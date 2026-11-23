# -*- coding: utf-8 -*-
"""Обёртка: создание замка -> loadBaseData (мир?) -> полный круг 16_run_full --speedup-45.
--dry-run (по умолчанию): сеть не трогаем, только план + имитация этапов + офлайн-проверка ускорения.
--live: каждый этап отдельным процессом через run_guarded; RG_OFFLINE у детей удаляется явно.
Стоп панели: файл logs/panel_stop.flag - проверяется между этапами и перед каждой командой круга."""
import argparse, glob, os, re, subprocess, sys, time
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE)
STOPF = os.path.join(BASE, "logs", "panel_stop.flag")
ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group()
g.add_argument("--live", action="store_true"); g.add_argument("--dry-run", action="store_true")
ap.add_argument("--world", type=int, default=837); ap.add_argument("--alliance", default="3cy")
# TODO(wireproxy): для параллельных замков - свой порт прокси на замок (список портов wireproxy); пока один VPN 18081
ap.add_argument("--proxy", default="http://127.0.0.1:18081")
# split: full = как раньше; prep = заготовка до замка 9 без альянса (финиш - castle_finish.py)
ap.add_argument("--mode", choices=["full", "prep"], default="full")
ap.add_argument("--calm", type=float, default=1.0, help="prep: множитель пауз (>1 = спокойно, со случайным разбросом)")
ap.add_argument("--tag", default="", help="batch worker tag (logs/seq separate per castle)")
ap.add_argument("--dry-delay", type=float, default=0.15, help="пауза имитации шага в dry-run")
a = ap.parse_args(); PROXY = a.proxy
FINISH_FROM = 114.9   # первый шаг финиша: поиск альянса (115 вступление, 116 замок 9->10, 118 выход)
RUN_EXTRA = ["--to", str(FINISH_FROM), "--calm", str(a.calm)] if a.mode == "prep" else []
if not re.fullmatch(r"[A-Za-z0-9_]{2,8}|\d+", a.alliance): raise SystemExit("СТОП: странный тег альянса")
TAG = re.sub(r"[^A-Za-z0-9_]", "", a.tag) or "solo"
LOGDIR = os.environ.get("CASTLE_LOGDIR") or os.path.join(BASE, "logs"); os.makedirs(LOGDIR, exist_ok=True)
LOG = os.path.join(LOGDIR, f"new_castle_full_{datetime.now():%Y%m%d_%H%M%S}_{TAG}_{os.getpid()}.log")
mport = re.search(r":(\d+)$", PROXY); PORT = int(mport.group(1)) if mport else None
GATE_KEY = f"{a.world}:{a.alliance.lower()}"
def log(m):
    line = f"{datetime.now():%H:%M:%S} {m}"; print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")
def stopped(): return os.path.exists(STOPF)
def child_env(offline):
    # флаг офлайна задаётся только ребёнку и никогда не наследуется из оболочки
    e = {k: v for k, v in os.environ.items() if k != "RG_OFFLINE"}; e["PYTHONIOENCODING"] = "utf-8"; e["PYTHONUNBUFFERED"] = "1"
    if offline: e["RG_OFFLINE"] = "1"
    return e
def stage(name, script, args, offline):
    cmd = [sys.executable, "run_guarded.py", "--proxy", PROXY, script] + args
    log(f"[{name}] старт {script}")
    t = time.time(); out = []
    p = subprocess.Popen(cmd, env=child_env(offline), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    with open(LOG.replace(".log", f"_{name}.txt"), "w", encoding="utf-8") as f:
        for line in p.stdout:      # поток построчно - панель видит прогресс
            out.append(line); f.write(line); f.flush()
            if name == "run": print("   " + line.rstrip(), flush=True)
    rc = p.wait(); log(f"[{name}] код {rc}, {time.time() - t:.0f} с")
    return rc, "".join(out)
STAGES = [("create", "_once_castle_gw.py --kingdom W"), ("state", "16_state_new.py <bundle> W"), ("run", "16_run_full.py --bundle <bundle> --alliance A --world W --speedup-45")]
if not a.live:
    import json as _j, random as _r, socket as _s
    rnd = _r.Random(); SEQ = LOG.replace(".log", "_seq.jsonl")
    def tun_ok():
        if not PORT: return True
        k = _s.socket(); k.settimeout(1)
        try: k.connect(("127.0.0.1", PORT)); return True
        except OSError: return False
        finally: k.close()
    log(f"DRY-RUN: nothing is sent. tag {TAG}, mode {a.mode}, world {a.world}, alliance {a.alliance}, tunnel port {PORT}" + (f", calm {a.calm}, to idx {FINISH_FROM}" if a.mode == "prep" else ""))
    for n, s_ in STAGES: log(f"   [{n}] run_guarded.py --proxy <tunnel> " + s_.replace(" W", f" {a.world}").replace(" A ", f" {a.alliance} "))
    if not tun_ok(): log("STOP: tunnel not listening (fail-closed) - castle not started"); sys.exit(2)
    log("[create] dry ok"); time.sleep(a.dry_delay * 3)
    log("[state] dry: RESULT_OK True")
    N = 115 if a.mode == "prep" else 123; seq = 1; last_ack = 0.0
    with open(SEQ, "w", encoding="utf-8") as sf:
        for i in range(N):
            if stopped(): log(f"STOP: panel stop - resume --from {i}"); sys.exit(3)
            if i % 20 == 0 and not tun_ok(): log(f"STOP: tunnel died - resume --from {i} (no other route)"); sys.exit(2)
            if a.mode == "full" and i == 115:
                import alliance_gate; w = alliance_gate.acquire(GATE_KEY, who=TAG, log=log); log(f"[gate] {GATE_KEY}: join slot after {w:.1f} s")
            time.sleep(a.dry_delay * rnd.uniform(0.5, 1.6))            # independent jitter per castle
            t_send = time.time(); time.sleep(rnd.uniform(0.01, 0.04)); t_ack = time.time()   # simulated server answer
            sf.write(_j.dumps({"tag": TAG, "seq": seq, "idx": i, "t_send": t_send, "t_ack": t_ack, "prev_ack": last_ack}) + "\n"); sf.flush()
            print(f"   idx {i}: (dry) ok:1 seq={seq}", flush=True); seq += 1; last_ack = t_ack
    if a.mode == "prep": log(f"[archive] would mark castle9_ready, finish_from {FINISH_FROM} (dry - not written)")
    r = subprocess.run([sys.executable, "_dry45.py"], env=child_env(True), capture_output=True, text=True, encoding="utf-8")
    for l in r.stdout.splitlines(): log("   " + l)
    log("DONE (dry)"); sys.exit(r.returncode)
T0 = time.time(); before = set(glob.glob("mitm/session_bundle_*.json"))
if stopped(): log("СТОП: остановлено панелью до создания"); sys.exit(3)
rc, out = stage("create", "_once_castle_gw.py", ["--kingdom", str(a.world)], False); t_create = time.time() - T0
# parallel-safe: bundle name comes from THIS castle's create output, not from a folder diff
mb = re.findall(r"session_bundle_\d+\.json", out)
new = [os.path.join("mitm", mb[-1])] if mb and os.path.exists(os.path.join("mitm", mb[-1])) else []
if rc != 0 or len(new) != 1: log(f"СТОП: создание код {rc}, новых bundle {len(new)} - без повторов"); sys.exit(2)
bundle = new[0]
if TAG == "solo": open("_newbundle.txt", "w").write(os.path.abspath(bundle) + "\n")
print("CASTLE_BUNDLE_OK", flush=True)
if stopped(): log("СТОП: остановлено панелью после создания - продолжать с проверки мира"); sys.exit(3)
rc, out = stage("state", "16_state_new.py", [bundle, str(a.world)], False)
if rc != 0 or "RESULT_OK True" not in out: log(f"СТОП: мир не {a.world} или ошибка loadBaseData"); sys.exit(2)
rc, out = stage("run", "16_run_full.py", ["--bundle", bundle, "--alliance", a.alliance, "--world", str(a.world), "--speedup-45"] + RUN_EXTRA, False)
try:
    import castle_archive; ok_status = "castle9_ready" if a.mode == "prep" else "castle10"
    mfrom = re.search(r"--from ([\d.]+)", out)
    castle_archive.save(bundle, a.world, None if a.mode == "prep" else a.alliance, ok_status if rc == 0 else "unfinished",
                        {"run_rc": rc, "total_s": round(time.time() - T0), "mode": a.mode, "calm": a.calm,
                         "finish_from": FINISH_FROM if a.mode == "prep" else None, "resume_from": float(mfrom.group(1)) if (rc and mfrom) else None})
except Exception as e: log(f"ARCHIVE ERROR: {e}")
m = re.search(r"--from ([\d.]+)", out)
log(f"итог: код {rc}, создание {t_create:.0f} с, всего {time.time() - T0:.0f} с" + (f", продолжать --from {m.group(1)}" if rc and m else ""))
sys.exit(rc)
