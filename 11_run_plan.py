# -*- coding: utf-8 -*-
"""
11_run_plan.py — пошаговое выполнение mitm/upgrade_plan.json (v2) для uid 98566384.

Использование:
  python 11_run_plan.py --from 26 --to 27            # сухой прогон (по умолчанию), ничего не шлёт
  python 11_run_plan.py --from 26 --to 27 --live     # реальная отправка
  python 11_run_plan.py --state                       # только чтение состояния города
Опции: --seq N (начальный seq; иначе seq_next из сессии), --session путь.
Лог: logs/run_plan_ГГГГММДД_ЧЧММСС.log (всё, что выводится на экран).
Защиты: только uid 98566384; gold всегда 0; instant:true только для upgradeObject, где он в плане;
стоп при любом ok!=1 (ok:98 — один повтор с seq от сервера).
"""
import argparse, importlib.util, json, random, sys, time, os

# --- ЗАЩИТА ОТ ПРЯМОГО ЗАПУСКА (добавлено 31.10): только через run_guarded.py ---
if __name__ == "__main__":
    import requests as _rq_guard
    if getattr(_rq_guard.Session.request, "__name__", "") != "_forced":
        raise SystemExit("СТОП: запускай только через run_guarded.py --proxy http://127.0.0.1:18081 (прямой выход запрещён)")
# --- конец защиты ---
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
BASE = Path(r"E:\protocol_analysis\capture")
spec = importlib.util.spec_from_file_location("sc", BASE / "10_send_cmd.py")
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)

ALLOWED_UID = 98566384
LOG = None

def log(msg=""):
    # печать на экран + в лог-файл
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if LOG: LOG.write(line + "\n"); LOG.flush()

def countdown(sec, live):
    # ожидание с обратным отсчётом (в сухом прогоне только пишем)
    if not live:
        log(f"   пауза {sec:.2f} с (сухой прогон — не ждём)"); return
    end = time.time() + sec
    while True:
        left = end - time.time()
        if left <= 0: break
        print(f"\r   ожидание {left:5.2f} с ...", end="", flush=True)
        time.sleep(min(0.25, left))
    print("\r" + " " * 30 + "\r", end="")
    log(f"   пауза {sec:.2f} с выдержана")

class Runner:
    def __init__(self, sess_path, live, seq):
        self.sp = sess_path; self.live = live
        self.s = json.load(open(sess_path, encoding="utf-8"))
        self.uid = int(self.s["uid"])
        if self.uid != ALLOWED_UID: sys.exit(f"СТОП: uid {self.uid} не разрешён")
        self.key = bytes.fromhex(self.s["aes_key_hex"]) if self.s.get("aes_key_hex") else sc.unwrap_ak(self.s["ak"])
        self.seq = seq if seq is not None else int(self.s.get("seq_next") or 1)
        self.refs = self.s.get("plan_refs", {})  # building_id новых зданий: "addObject@slotN" -> id

    def save(self):
        self.s["seq_next"] = self.seq; self.s["plan_refs"] = self.refs
        json.dump(self.s, open(self.sp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def read(self, cls, method):
        env = sc.build_envelope(cls, method, self.s["session_key"], self.s["token"])
        p, raw, meta = sc.send_command(self.key, env)
        return p

    def commit(self, op, args):
        # отправка одной записи; ok:98 -> один повтор с seq сервера
        for attempt in (1, 2):
            env = sc.build_commit_envelope(op, self.s["session_key"], self.s["token"],
                                           args,  # клиент шлёт args объектом, не строкой
                                           fpid=str(self.s["fpid"]), seq=self.seq)
            if not self.live:
                log(f"   [СУХО] seq={self.seq} {op} {json.dumps(args, ensure_ascii=False)}")
                self.seq += 1; return {"ok": 1, "dry": True}
            p, raw, meta = sc.send_command(self.key, env)
            ok = p.get("ok") if isinstance(p, dict) else None
            log(f"   → отправлено seq={self.seq} {op} | ответ ok={ok} http={meta.get('http_status')}")
            if ok == 1:
                self.seq += 1; self.save(); return p
            if ok == 98 and attempt == 1 and isinstance(p, dict) and "seq" in p:
                log(f"   ok:98 — сервер ждёт seq={p['seq']}, повтор"); self.seq = int(p["seq"]); continue
            log(f"   СТОП: ответ {json.dumps(p, ensure_ascii=False)[:400]}"); self.save(); sys.exit(3)

def describe(st):
    a = st.get("args") or {}
    if st["op"] == "City:upgradeObject": return f"улучшение здания {a.get('building_id')} → ур.{st.get('level_reached')}"
    if st["op"] == "City:addObject": return f"постройка type {a.get('type')} в слот {a.get('slot_id')}"
    return f"{st['op']} {json.dumps(a, ensure_ascii=False)[:80]}"

def resolve(r, st):
    # подстановка констант / ссылок из ответов / гарантии безопасности
    a = json.loads(json.dumps(st.get("args")))
    op = st["op"]
    # альянс: только 1129544 (разрешено владельцем)
    if op.startswith("Alliance:") and (not isinstance(a, dict) or a.get("alliance_id") != 1129544 or op not in ("Alliance:joinAlliance", "Alliance:leaveAlliance")): sys.exit(f"СТОП: {op} {a} запрещён")
    if isinstance(a, dict):
        if "gold" in a and a["gold"] != 0: sys.exit("СТОП: gold>0 запрещён")
        if a.get("instant") and op != "City:upgradeObject": sys.exit(f"СТОП: instant в {op} запрещён")
        if op == "City:upgradeObject" and a.get("instant") and (st.get("level_reached") or 99) > 10: sys.exit("СТОП: instant выше ур.10")
        b = a.get("building_id")
        if isinstance(b, dict):
            if b.get("gen") == "unix_time_now": a["building_id"] = int(time.time())
            elif "from_response" in b:
                ref = b["from_response"]
                if ref not in r.refs: sys.exit(f"СТОП: нет id для {ref}")
                a["building_id"] = r.refs[ref]
        if a.get("city_id") == {"const": "uid"}: a["city_id"] = r.uid  # city_id = uid аккаунта
        if isinstance(a.get("job_id"), dict): sys.exit("СТОП: шаг с job_id (ускорение) не поддержан")
        if op in ("City:upgradeObject", "City:addObject"):
            # порядок ключей как у клиента: gold, city_id, ...
            a = {"gold": 0, "city_id": r.uid, **{k: v for k, v in a.items() if k != "gold"}}
    return a

def summarize(p, op):
    try:
        s = p["data"]["set"]; out = []
        for c in s.get("city_map") or []: out.append(f"здание {c.get('building_id')} type {c.get('type_id')} ур.{c.get('level')}")
        uc = (s.get("user_city") or [{}])[0]
        res = (uc.get("resource") or {}).get("resource")
        if res: out.append(f"ресурсы {res}")
        return "; ".join(out) or "—"
    except Exception: return "—"

def state(r):
    p = r.read("Player", "loadBaseData")
    if not isinstance(p, dict): log("чтение: нет ответа"); return None
    log(f"чтение Player:loadBaseData ok={p.get('ok')}")
    d = p.get("data") or {}
    txt = json.dumps(d, ensure_ascii=False)
    cm = d.get("city_map") or (d.get("set") or {}).get("city_map") or []
    for c in cm:
        if c.get("building_id") in (1, 2): log(f"   здание {c['building_id']}: type {c.get('type_id')} ур.{c.get('level')} статус {c.get('status')} job {c.get('job_id')}")
    uc = d.get("user_city") or (d.get("set") or {}).get("user_city") or []
    if uc:
        u = uc[0] if isinstance(uc, list) else uc
        log(f"   ресурсы: {(u.get('resource') or {}).get('resource')}")
        log(f"   очередь: free_job={u.get('free_queue_job_id')} pay_job={u.get('pay_queue_job_id')} pay_status={u.get('pay_queue_status')}")
    Path(BASE / "logs").mkdir(exist_ok=True)
    (BASE / "logs" / f"state_{datetime.now():%H%M%S}.json").write_text(txt, encoding="utf-8")
    return p

def main():
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="f", type=int); ap.add_argument("--to", dest="t", type=int)
    ap.add_argument("--live", action="store_true"); ap.add_argument("--seq", type=int)
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--session", default=str(BASE / "mitm" / "session_bundle_new.json"))
    ap.add_argument("--plan", default=str(BASE / "mitm" / "upgrade_plan.json"))
    a = ap.parse_args()
    (BASE / "logs").mkdir(exist_ok=True)
    LOG = open(BASE / "logs" / f"run_plan_{datetime.now():%Y%m%d_%H%M%S}{'_live' if a.live else '_dry'}.log", "w", encoding="utf-8")
    r = Runner(a.session, a.live, a.seq)
    log(f"=== uid {r.uid} | режим: {'БОЕВОЙ' if a.live else 'СУХОЙ (ничего не шлём)'} | стартовый seq {r.seq} ===")
    if a.state: state(r); return
    steps = json.load(open(a.plan, encoding="utf-8"))["steps"]
    for st in steps[a.f:a.t + 1]:
        log(f"--- шаг {st['idx']}: {describe(st)}")
        d = random.uniform(st.get("delay_s_min") or 0.5, st.get("delay_s_max") or 1.0)
        countdown(d, a.live)
        args = resolve(r, st)
        p = r.commit(st["op"], args)
        if a.live: log(f"   итог: {summarize(p, st['op'])}")
        if st["op"] == "City:addObject":
            bid = args["building_id"]
            try: bid = p["data"]["set"]["city_map"][0]["building_id"]
            except Exception: pass
            r.refs[f"addObject@slot{args['slot_id']}"] = bid; r.save() if a.live else None
        for ex in st.get("after") or []:
            lo, hi = ex["delay_s"]; countdown(random.uniform(lo, hi), a.live)
            r.commit(ex["op"], ex["args"])
    log(f"=== готово. следующий seq {r.seq} ===")

if __name__ == "__main__":
    main()




