# -*- coding: utf-8 -*-
"""
14_run_plan_inject.py - прогон upgrade_plan.json v2 через ЖИВУЮ игру (inject.py, VPN).
Правила:
  * шаг N -> ждём ответ сервера (ok:1) -> пауза из записи пользователя (от момента ОТВЕТА) -> шаг N+1;
  * никакой очереди наперёд; таймаут/ошибка/ok!=1/списание ресурсов/золота -> СТОП;
  * uid берётся из живой сессии (inject_state.json), никогда 71206420; gold 0; instant только до ур.10;
  * альянс ищется по тегу/имени (--alliance) перед вступлением; join/leave только найденный id;
  * шаг пропускается, если результат уже есть (уровень достигнут).
Запуск: python 14_run_plan_inject.py --from 25 --alliance 3cy --world 837
"""
import argparse, json, os, random, re, sys, time
sys.stdout.reconfigure(encoding="utf-8")
BASE = r"E:\protocol_analysis\capture"
MITM = os.path.join(BASE, "mitm")
INBOX, OUTBOX = os.path.join(MITM, "inject_inbox"), os.path.join(MITM, "inject_outbox")
FORBIDDEN = 71206420
TIMEOUT = 30
ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="frm", type=float, default=26)
ap.add_argument("--alliance", required=True, help="тег или имя альянса, напр. 3cy")
ap.add_argument("--world", type=int, required=True, help="королевство (world_id), напр. 837")
a = ap.parse_args()
# uid - только из живой сессии
_st = json.load(open(os.path.join(MITM, "inject_state.json"), encoding="utf-8"))
UID = _st.get("uid")
if not UID: raise SystemExit("СТОП: в inject_state.json нет uid - игра ещё не сделала ни одного commit")
UID = int(UID)
if UID == FORBIDDEN: raise SystemExit("СТОП: сессия фермы 71206420 - запрещено")
if time.time() - (_st.get("last_game") or 0) > 600: raise SystemExit("СТОП: сессия не свежая (>600 c)")
ALLY = None          # id альянса появится после поиска
ALLY_FILE = os.path.join(MITM, "alliance_allow.json")
if os.path.exists(ALLY_FILE): os.remove(ALLY_FILE)   # старый разрешённый альянс - убрать
LOG = os.path.join(BASE, "logs", time.strftime("run_plan_%Y%m%d_%H%M%S.log"))
def log(m):
    line = time.strftime("%H:%M:%S ") + m
    print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")

_cf = os.path.join(MITM, f"city_live_{UID}.json")   # пишет inject.py из данных входа этого замка
if not os.path.exists(_cf): raise SystemExit(f"СТОП: нет {_cf} - перезайдите в игру при запущенном mitmdump")
city = json.load(open(_cf, encoding="utf-8"))           # building_id -> {type_id, level, slot_id}
if "1" not in city: raise SystemExit("СТОП: в данных города нет замка (building 1)")
slot_ids = {}            # slot -> building_id, выданный при addObject
res_last = {}            # последние известные ресурсы/золото
stats = {"sent": 0, "ok": 0, "skip": 0}

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

def check_spend(resp):
    """Сравниваем только реальные запасы: user_city[].resource.resource и gold игрока (не награды в payload)."""
    sets = ((resp or {}).get("data") or {}).get("set") or {}
    cur = {}
    for uc in sets.get("user_city") or []:
        rr = ((uc.get("resource") or {}).get("resource")) or {}
        cur.update({k: v for k, v in rr.items() if isinstance(v, (int, float))})
    for up in sets.get("user_info") or sets.get("user") or []:
        if isinstance(up, dict) and isinstance(up.get("gold"), (int, float)): cur["gold"] = up["gold"]
    for k, v in cur.items():
        old = res_last.get(k)
        res_last[k] = v
        if old is not None and v < old and (k == "gold" or old - v > 0):
            return f"{k}: {old} -> {v}"
    return None

FILL = {   # поля, которые клиент шлёт, а план вырезал (по записям кругов _3r_all.json)
    "City:upgradeObject": {"city_id": UID},
    "City:addObject": {"c_job_id": 0, "city_id": UID},
    "Hero:notifyLastLevel": {"uid": UID},
    "Prophase:clearCityRuin": {"uid": UID},
    "Prophase:collectCityAllRewards": {"uid": UID},
}
ORDER = {  # порядок ключей как у клиента
    "City:upgradeObject": ["gold", "city_id", "instant", "auto", "building_id"],
    "City:addObject": ["slot_id", "gold", "type", "c_job_id", "building_id", "city_id", "instant"],
}

def send(op, args):
    if isinstance(args, dict) and op in FILL:
        for k, v in FILL[op].items():
            if k not in args or isinstance(args[k], dict): args[k] = v
        if op in ORDER:
            args = {k: args[k] for k in ORDER[op] if k in args} | {k: v for k, v in args.items() if k not in ORDER[op]}
    if isinstance(args, dict):
        if args.get("gold", 0) != 0: raise SystemExit("СТОП: gold != 0")
        if op in ("Alliance:joinAlliance", "Alliance:leaveAlliance") and (not ALLY or args.get("alliance_id") != ALLY): raise SystemExit(f"СТОП: альянс {args.get('alliance_id')} не найденный {ALLY}")
    name = f"{int(time.time()*1000)}.json"
    tmp = os.path.join(INBOX, name + ".tmp")
    json.dump({"op": op, "args": args, "uid": UID}, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, os.path.join(INBOX, name))
    stats["sent"] += 1
    last_send[0] = time.time()
    path, t0 = os.path.join(OUTBOX, name), time.time()
    while time.time() - t0 < TIMEOUT:
        if os.path.exists(path):
            time.sleep(0.05)
            r = json.load(open(path, encoding="utf-8"))
            break
        time.sleep(0.02)   # быстрый опрос outbox
    else:
        raise SystemExit(f"СТОП: нет ответа {TIMEOUT} c на {op}")
    if r.get("error") or r.get("ok") != 1:
        raise SystemExit(f"СТОП: {op} -> ok={r.get('ok')} error={r.get('error')} {json.dumps(r.get('resp'), ensure_ascii=False)[:300]}")
    stats["ok"] += 1
    resp = r.get("resp") or {}
    for d in walk(resp):
        if "building_id" in d and "level" in d and "type_id" in d and d.get("uid", UID) == UID:
            city[str(d["building_id"])] = {"type_id": d["type_id"], "level": d["level"], "slot_id": d.get("slot_id")}
    sp = check_spend(resp)
    if sp: raise SystemExit(f"СТОП: неожиданное списание после {op}: {sp}")
    return r, resp

def pause(lo, hi, why=""):
    d = random.uniform(lo, hi)
    time.sleep(d)

# --- тайминг по записи: интервал считается от ОТПРАВКИ прошлой команды (send-to-send, как у игрока),
# а не после ответа. Ответ всё равно ждём перед следующей отправкой (без конвейера).
last_send = [0.0]
def wait_until_gap(gap_target, gap_floor):
    """ждём, чтобы от прошлой отправки прошло gap_target (не меньше gap_floor - минимум у человека)"""
    g = max(gap_target, gap_floor)
    rest = last_send[0] + g - time.time()
    if rest > 0: time.sleep(rest)

def main_gap(s):
    gs = s.get("gap_s")
    if gs:   # медиана трёх кругов, джиттер -2..+4 %, но не быстрее минимального круга
        return gs["median"] * random.uniform(0.98, 1.04), gs["min"]
    lo, hi = s.get("delay_s_min") or 0.5, s.get("delay_s_max") or 1.0
    return random.uniform(lo, (lo + hi) / 2), lo

plan = json.load(open(os.path.join(MITM, "upgrade_plan.json"), encoding="utf-8"))
RG = json.load(open(os.path.join(MITM, "record_group_progress.json"), encoding="utf-8"))
allsteps = []
for s in plan["steps"]:
    allsteps.append(s)
    if s["idx"] == 117:   # после notifyLastLevel 6: в кругах +2.35 c
        allsteps.append({"idx": 117.5, "op": "Prophase:recordGroupProgress", "args": RG[0], "delay_s_min": 1.7, "delay_s_max": 2.86})
    if s["idx"] == 118:   # после leaveAlliance: в кругах +3.5 c
        allsteps.append({"idx": 118.5, "op": "Prophase:recordGroupProgress", "args": RG[1], "delay_s_min": 3.23, "delay_s_max": 4.7})
_n = []
for s in allsteps:
    if s["idx"] == 115:   # Alliance:searchAllianceByUser там же, где был поиск "591"
        _n.append({"idx": 114.9, "op": "Alliance:searchAllianceByUser", "args": {"context": a.alliance, "page": 1},
                   "gap_s": {"min": 5.4, "median": 8.2, "max": 8.9}})
        s["gap_s"] = {"min": 1.8, "median": 1.9, "max": 3.8}     # вступление через ~1.9 c после поиска
    _n.append(s)
allsteps = _n
for s in allsteps:
    if s["idx"] == 118: s["delay_s_min"], s["delay_s_max"] = 7.8, 9.0; s["gap_s"] = None     # leave через ~7.8 c после recordGroupProgress
    if s["idx"] == 119: s["delay_s_min"], s["delay_s_max"] = 12.1, 14.0; s["gap_s"] = None   # unSubTopics через ~12 c
steps = [s for s in allsteps if s["idx"] >= a.frm]
log(f"старт: шагов {len(steps)} (idx {steps[0]['idx']}..{steps[-1]['idx']}), лог {LOG}")
t_start = time.time()
try:
    for s in steps:
        op, args = s["op"], json.loads(json.dumps(s["args"]))
        lo, hi = s.get("delay_s_min") or 0.5, s.get("delay_s_max") or 1.0
        lvl = s.get("level_reached")
        if isinstance(args, dict):
            if isinstance(args.get("city_id"), dict): args["city_id"] = UID
            bid = args.get("building_id")
            if isinstance(bid, dict) and "from_response" in bid:
                slot = int(re.search(r"slot(\d+)", bid["from_response"]).group(1))
                args["building_id"] = slot_ids[slot]
            elif isinstance(bid, dict) and bid.get("gen") == "unix_time_now":
                bid = None
        # пропуск, если результат уже есть
        if op == "City:upgradeObject":
            cur = city.get(str(args["building_id"]), {}).get("level")
            if cur is None: raise SystemExit(f"СТОП: здание {args['building_id']} не найдено в городе")
            if args.get("instant") and (lvl or 99) > 10: raise SystemExit("СТОП: instant выше ур.10")
            if cur >= lvl:
                log(f"idx {s['idx']}: здание {args['building_id']} уже ур.{cur} >= {lvl} - пропуск"); stats["skip"] += 1; continue
        if op == "City:addObject":
            used = [k for k, v in city.items() if v.get("slot_id") == args["slot_id"]]
            if used:
                slot_ids[args["slot_id"]] = int(used[0]); log(f"idx {s['idx']}: слот {args['slot_id']} уже занят зданием {used[0]} - пропуск"); stats["skip"] += 1; continue
        wait_until_gap(*main_gap(s))                    # пауза от ОТПРАВКИ прошлой команды (как у игрока)
        if op == "City:addObject":
            args["building_id"] = int(time.time())       # id как у клиента: текущее unix-время
        if op in ("Alliance:joinAlliance", "Alliance:leaveAlliance"):
            args["alliance_id"] = ALLY
        r, resp = send(op, args)
        extra = ""
        if op == "Alliance:searchAllianceByUser":
            lst = resp.get("payload") or []
            if isinstance(lst, dict): lst = lst.get("list") or []
            want = a.alliance.strip().lower()
            hit = [x for x in lst if isinstance(x, dict) and (str(x.get("acronym", "")).lower() == want or str(x.get("name", "")).lower() == want)]
            log("поиск '" + a.alliance + "': " + "; ".join(f"{x.get('alliance_id')} [{x.get('acronym')}] {x.get('name')} world={x.get('world_id')}" for x in lst[:10]))
            if len(hit) != 1: raise SystemExit(f"СТОП: точных совпадений '{a.alliance}': {len(hit)} - не вступаю")
            if int(hit[0].get("world_id") or 0) != a.world: raise SystemExit(f"СТОП: альянс в королевстве {hit[0].get('world_id')}, не {a.world}")
            ALLY = int(hit[0]["alliance_id"])
            json.dump({"alliance_id": ALLY, "tag": hit[0].get("acronym"), "name": hit[0].get("name")}, open(ALLY_FILE, "w", encoding="utf-8"), ensure_ascii=False)
            extra = f" -> альянс {ALLY} [{hit[0].get('acronym')}] {hit[0].get('name')}"
        if op == "City:addObject":
            new = [d for d in walk(resp) if "building_id" in d and d.get("slot_id") == args["slot_id"]]
            slot_ids[args["slot_id"]] = int(new[0]["building_id"]) if new else args["building_id"]
            extra = f" -> новое здание {slot_ids[args['slot_id']]}"
        if op == "City:upgradeObject":
            extra = f" -> здание {args['building_id']} ур.{city[str(args['building_id'])]['level']}"
            if city[str(args['building_id'])]['level'] < lvl: raise SystemExit(f"СТОП: уровень не вырос{extra}")
        log(f"idx {s['idx']}: {op} {json.dumps(args, ensure_ascii=False)[:120]} ok:1 seq={r.get('seq')}{extra}")
        for sub in s.get("after", []):
            lo2, hi2 = sub["delay_s"]
            wait_until_gap(random.uniform(lo2, (lo2 + hi2) / 2), lo2)
            r2, _ = send(sub["op"], sub["args"])
            log(f"   + {sub['op']} {sub['args'].get('path')} ok:1")
    log(f"ГОТОВО за {time.time()-t_start:.0f} c. отправлено {stats['sent']}, ok:1 {stats['ok']}, пропущено {stats['skip']}")
except SystemExit as e:
    log(f"{e} | отправлено {stats['sent']}, ok:1 {stats['ok']}, пропущено {stats['skip']}, за {time.time()-t_start:.0f} c")
finally:
    json.dump(city, open(os.path.join(MITM, f"city_{UID}_after.json"), "w"), indent=0)
    log("город после: " + ", ".join(f"{k}:ур{v['level']}" for k, v in sorted(city.items(), key=lambda x: int(x[0]))))
