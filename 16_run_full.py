# -*- coding: utf-8 -*-
"""
16_run_full.py — полный круг БЕЗ игры для uid 98570606 (upgrade_plan.json idx 0..119).
Запуск ТОЛЬКО так:  python run_guarded.py --proxy http://127.0.0.1:18081 16_run_full.py --alliance 3cy --world 837
Правила:
  * отправка через sc.send_command (requests), которую run_guarded принудительно пускает через прокси;
  * выходной IP проверяется перед стартом и перед каждой фазой (обучение / путь / альянс); 203.0.113.10 или неизвестен -> стоп;
  * шаг N -> ждём ok:1 -> пауза как в 14 (по медиане интервала от прошлой отправки) -> шаг N+1; без повторов;
  * только uid 98570606, ферма 71206420 запрещена; gold всегда 0, рост расхода золота -> стоп;
  * drawFreeLegend: в ответе должен быть легенд/страж, иначе стоп;
  * альянс: поиск по тегу, ровно одно совпадение, id 1035611 и world 837, иначе стоп.
"""
import argparse, json, os, random, re, sys, time, importlib.util
import requests
sys.stdout.reconfigure(encoding="utf-8")
BASE = r"E:\protocol_analysis\capture"; MITM = os.path.join(BASE, "mitm")
# uid берётся из указанного bundle (новый замок со своими данными)
FORBIDDEN = (71206420, "182070973"); OLD_CASTLES = (98569572, 98570606, 98566384); ALLY_EXPECT = 1035611; BAD_IP = "203.0.113.10"
ap = argparse.ArgumentParser(); ap.add_argument("--from", dest="frm", type=float, default=0)
ap.add_argument("--alliance", default="3cy"); ap.add_argument("--bundle", required=True); ap.add_argument("--world", type=int, required=True)
# ускорение 4->5: по умолчанию выключено
ap.add_argument("--speedup-45", dest="sp45", action="store_true")
ap.add_argument("--speedup-45-maxwait", dest="sp45_wait", type=int, default=1200)
# split: --to = до какого idx (не включая) - режим заготовки; --calm = растянутые паузы с разбросом; --list-steps = офлайн показать шаги и выйти
ap.add_argument("--to", dest="to", type=float, default=1e9)
ap.add_argument("--calm", type=float, default=1.0)
ap.add_argument("--list-steps", dest="list_steps", action="store_true")
a = ap.parse_args()
# --alliance можно задать id: ищем всё равно по тегу 3cy и сверяем id
if str(a.alliance).strip().isdigit():
    if int(a.alliance) != 1035611: raise SystemExit("СТОП: неизвестный id альянса")
    a.alliance = "3cy"
if not getattr(requests.Session.request, "__name__", "") == "_forced":
    raise SystemExit("СТОП: запускай только через run_guarded.py (иначе прямой выход)")
s_ = importlib.util.spec_from_file_location("sc", os.path.join(BASE, "10_send_cmd.py")); sc = importlib.util.module_from_spec(s_); s_.loader.exec_module(sc)
BP = a.bundle
bd = json.load(open(BP, encoding="utf-8"))
UID = int(bd["uid"])
if UID in OLD_CASTLES or UID in FORBIDDEN: raise SystemExit("СТОП: прежний замок/ферма")
if int(bd.get("kingdom") or 0) != a.world: raise SystemExit(f"СТОП: bundle не {a.world}")
if int(bd["uid"]) != UID or str(bd["fpid"]) in FORBIDDEN: raise SystemExit("СТОП: чужой bundle")
KEY = bytes.fromhex(bd["aes_key_hex"]); seq = int(bd.get("seq_next") or 1)
LOG = os.path.join(BASE, "logs", time.strftime("run_full_%Y%m%d_%H%M%S") + f"_{os.getpid()}.log")
RESP = LOG.replace(".log", "_resp.jsonl")
def log(m):
    line = time.strftime("%H:%M:%S ") + m
    print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")

FIRST_IP = [None]
def check_ip(phase):
    # проверка выхода через тот же (принудительный) прокси
    try: ip = requests.Session().get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
    except Exception as e: raise SystemExit(f"СТОП: IP не определён перед '{phase}' ({type(e).__name__})")
    if not ip or ip == BAD_IP: raise SystemExit(f"СТОП: IP {ip} перед '{phase}'")
    FIRST_IP[0] = FIRST_IP[0] or ip
    log(f"[ip] {phase}: выход НЕ домашний" + ("" if ip == FIRST_IP[0] else " (сменился)"))

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

# стартовое состояние города — из чтения loadBaseData (16_state.py)
st0 = json.load(open(os.path.join(BASE, "logs", f"state_{UID}.json"), encoding="utf-8"))
city = {str(c["building_id"]): {"type_id": c["type_id"], "level": c["level"], "slot_id": c.get("slot_id")}
        for c in st0["data"]["city_map"]}
gold_last = [None]; stats = {"sent": 0, "ok": 0, "skip": 0}; slot_ids = {}; job = {}; legend_got = []
# сведения для --speedup-45: последний job замка, его конец (серверное время), сдвиг часов, инвентарь из ответов
sp = {"job": None, "end": None, "dt": 0.0, "inv": {}}
ALLY = None
for d in walk(st0["data"].get("user_info")):
    if isinstance(d.get("gold"), (int, float)): gold_last[0] = d["gold"]; break

FILL = {"City:upgradeObject": {"city_id": UID}, "City:addObject": {"c_job_id": 0, "city_id": UID},
        "Hero:notifyLastLevel": {"uid": UID}, "Prophase:clearCityRuin": {"uid": UID},
        "Prophase:collectCityAllRewards": {"uid": UID}}
ORDER = {"City:upgradeObject": ["gold", "city_id", "instant", "auto", "building_id"],
         "City:addObject": ["slot_id", "gold", "type", "c_job_id", "building_id", "city_id", "instant"]}
last_send = [0.0]

def send(op, args):
    global seq
    if isinstance(args, dict) and op in FILL:
        for k, v in FILL[op].items():
            if k not in args or isinstance(args[k], dict): args[k] = v
        if op in ORDER: args = {k: args[k] for k in ORDER[op] if k in args} | {k: v for k, v in args.items() if k not in ORDER[op]}
    if isinstance(args, dict):
        if args.get("gold", 0) != 0: raise SystemExit("СТОП: gold != 0")
        for k in ("uid", "city_id"):
            if k in args and args[k] != UID: raise SystemExit(f"СТОП: {k}={args[k]} не наш")
        if op.startswith("Alliance:") and op != "Alliance:searchAllianceByUser" and args.get("alliance_id") != ALLY: raise SystemExit("СТОП: альянс не разрешён")
    env = sc.build_commit_envelope(op, bd["session_key"], bd["token"], args, fpid=str(bd["fpid"]), seq=seq)
    stats["sent"] += 1; last_send[0] = time.time()
    # номер seq сжигается при любой отправке (ответ, errno, пусто, обрыв) — никогда не повторяется
    used = seq; seq += 1; bd["seq_next"] = seq
    json.dump(bd, open(BP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    try: p, raw, meta = sc.send_command(KEY, env)
    except Exception as e: raise SystemExit(f"СТОП: нет ответа на {op}: {type(e).__name__} {e}")
    open(RESP, "a", encoding="utf-8").write(json.dumps({"seq": used, "op": op, "resp": p}, ensure_ascii=False) + "\n")
    if not isinstance(p, dict) or p.get("ok") != 1:
        raise SystemExit(f"СТОП: {op} seq={used} http={meta.get('http_status')} ответ={json.dumps(p, ensure_ascii=False)[:600]}")
    stats["ok"] += 1
    for d in walk(p):
        if "building_id" in d and "level" in d and "type_id" in d and d.get("uid", UID) == UID:
            city[str(d["building_id"])] = {"type_id": d["type_id"], "level": d["level"], "slot_id": d.get("slot_id")}
        if d.get("uid") not in (None, UID) and isinstance(d.get("uid"), int) and d.get("uid") in FORBIDDEN: raise SystemExit("СТОП: ферма в ответе")
    for d in walk(((p.get("data") or {}).get("set") or {}).get("user_info")):
        if isinstance(d.get("gold"), (int, float)):
            if gold_last[0] is not None and d["gold"] < gold_last[0]: raise SystemExit(f"СТОП: потрачено золото {gold_last[0]} -> {d['gold']} после {op}")
            gold_last[0] = d["gold"]
    # запоминаем job стройки (event 30), серверное время и количество предметов из последнего ответа
    if isinstance(p.get("time"), (int, float)): sp["dt"] = (p["time"] / (1000 if p["time"] > 1e12 else 1)) - time.time()
    for d in walk(((p.get("data") or {}).get("set") or {}).get("job")):
        # ответ ускорения приходит без event_type - сверяем по job_id
        if d.get("job_id") and d.get("time_end") and (d.get("event_type") == 30 or (op == "Item:useConsumableItem" and d.get("job_id") == sp["job"])): sp["job"], sp["end"] = d["job_id"], d["time_end"]
    # ускорение вернуло ok, а нашего job в ответе нет - стройка завершена
    if op == "Item:useConsumableItem" and isinstance(args, dict) and args.get("job_id") == sp["job"] and not any(d.get("job_id") == sp["job"] for d in walk(((p.get("data") or {}).get("set") or {}).get("job"))): sp["end"] = time.time() + sp["dt"]
    for d in walk(((p.get("data") or {}).get("set") or {}).get("user_consumable")):
        if d.get("item_property_id") and isinstance(d.get("quantity"), int): sp["inv"][int(d["item_property_id"])] = d["quantity"]
    return p

def sp_left():
    # сколько секунд осталось до конца стройки замка по серверным часам
    return None if sp["end"] is None else sp["end"] - (time.time() + sp["dt"])

SP_ITEMS = ((6000029, 300), (6002580, 60))   # предмет, секунд за штуку (6002580 ~60 с - не подтверждено)

def speedup_45(idx):
    # закрываем остаток 4->5 ускорителями сразу и полностью (с запасом), они дальше в круге не нужны
    # перед каждым предметом: по последнему ответу стройка ещё идёт и предмет есть в запасе
    # золото не трогаем (у новых замков 0); если предметов не хватило - ждём остаток
    left = sp_left()
    log(f"[sp45] idx {idx}: осталось {left if left is None else round(left)} с, предметы { {i: sp['inv'].get(i) for i, _ in SP_ITEMS} }")
    if left is None: raise SystemExit(f"СТОП: [sp45] нет данных о job замка - жди таймер и --from {idx}")
    for _ in range(6):
        left = sp_left()
        if left is None or left <= 0: break
        pick = [(i, sec) for i, sec in SP_ITEMS if sp["inv"].get(i, 0) > 0]
        if not pick: log("[sp45] ускорителей нет"); break
        item, sec = pick[0]
        n = min(sp["inv"][item], -(-int(left + 1) // sec))   # округление вверх - закрыть остаток целиком
        wait_gap({"delay_s_min": 2.5, "delay_s_max": 4.0})
        send("Item:useConsumableItem", {"job_id": sp["job"], "amount": n, "legend_id": "", "item_id": item, "type": "speedup", "extra_content": ""})
        stats.setdefault("sp45_items", []).append((item, n))
        log(f"[sp45] предмет {item} x{n}, осталось {round(max(0, sp_left() or 0))} с")
    left = max(0.0, sp_left() or 0)
    if left > 0:
        if left > a.sp45_wait: raise SystemExit(f"СТОП: [sp45] осталось {round(left)} с > лимита - --from {idx}")
        log(f"[sp45] жду таймер {round(left)+5} с"); stats["sp45_wait"] = round(left) + 5; time.sleep(left + 5)
    city.setdefault("1", {})["level"] = 5
    log("[sp45] 4->5 готово, замок считаем 5")

def wait_gap(s):
    gs = s.get("gap_s")
    if gs: g = max(gs["median"] * random.uniform(0.98, 1.04), gs["min"])
    else:
        lo, hi = s.get("delay_s_min") or 0.5, s.get("delay_s_max") or 1.0; g = random.uniform(lo, (lo + hi) / 2)
    if a.calm > 1: g = g * random.uniform(a.calm * 0.8, a.calm * 1.25) + random.uniform(0, 2 * a.calm)
    rest = last_send[0] + g - time.time()
    if rest > 0: time.sleep(rest)

plan = json.load(open(os.path.join(MITM, "upgrade_plan.json"), encoding="utf-8"))
RG = json.load(open(os.path.join(MITM, "record_group_progress.json"), encoding="utf-8"))
steps = []
for s in plan["steps"]:
    if s["idx"] == 115:
        steps.append({"idx": 114.9, "op": "Alliance:searchAllianceByUser", "args": {"context": a.alliance, "page": 1}, "gap_s": {"min": 5.4, "median": 8.2, "max": 8.9}})
        s["gap_s"] = {"min": 1.8, "median": 1.9, "max": 3.8}
    if s["idx"] == 118: s["delay_s_min"], s["delay_s_max"], s["gap_s"] = 7.8, 9.0, None
    if s["idx"] == 119: s["delay_s_min"], s["delay_s_max"], s["gap_s"] = 12.1, 14.0, None
    steps.append(s)
    if s["idx"] == 117: steps.append({"idx": 117.5, "op": "Prophase:recordGroupProgress", "args": RG[0], "delay_s_min": 1.7, "delay_s_max": 2.86})
    if s["idx"] == 118: steps.append({"idx": 118.5, "op": "Prophase:recordGroupProgress", "args": RG[1], "delay_s_min": 3.23, "delay_s_max": 4.7})
steps = [s for s in steps if a.frm <= s["idx"] < a.to]
PHASES = {0: "обучение", 24: "страж", 25: "путь к замку 10", 114.9: "альянс"}
if a.list_steps:
    def _g(s, k=1.0):
        gs = s.get("gap_s")
        g = gs["median"] if gs else ((s.get("delay_s_min") or 0.5) + ((s.get("delay_s_min") or 0.5) + (s.get("delay_s_max") or 1.0)) / 2) / 2
        return g * k + (a.calm if a.calm > 1 else 0)
    for s in steps: print(f"   idx {s['idx']}: {s['op']} (list)")
    k = 1.0 if a.calm <= 1 else a.calm * 1.025
    print(f"LIST: шагов {len(steps)}, idx {steps[0]['idx'] if steps else None}..{steps[-1]['idx'] if steps else None}, оценка пауз ~{sum(_g(s, k) for s in steps)/60:.1f} мин (calm {a.calm}), альянс-команд {sum(1 for s in steps if s['op'].startswith('Alliance:'))}")
    sys.exit(0)
log(f"старт (новый замок), шагов {len(steps)}, seq {seq}, лог {LOG}")
t0 = time.time()
try:
    for s in steps:
        # панель: файл-стоп - аккуратно выходим перед следующей командой
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "panel_stop.flag")): raise SystemExit(f"СТОП: остановлено панелью - продолжать --from {s['idx']}")
        if s["idx"] in PHASES or s is steps[0]: check_ip(PHASES.get(s["idx"], "старт"))
        op, args = s["op"], json.loads(json.dumps(s.get("args")))
        lvl = s.get("level_reached")
        if isinstance(args, dict):
            if isinstance(args.get("city_id"), dict): args["city_id"] = UID
            bid = args.get("building_id")
            if isinstance(bid, dict) and "from_response" in bid:
                args["building_id"] = slot_ids[int(re.search(r"slot(\d+)", bid["from_response"]).group(1))]
            if isinstance(args.get("job_id"), dict):
                if "b1" not in job: raise SystemExit("СТОП: нет job_id стройки замка для ускорения")
                args["job_id"] = job.pop("b1")
        if op == "City:upgradeObject":
            cur = city.get(str(args["building_id"]), {}).get("level")
            if cur is None: raise SystemExit(f"СТОП: здания {args['building_id']} нет")
            if args.get("instant") and (lvl or 99) > 10: raise SystemExit("СТОП: instant выше 10")
            if lvl and cur >= lvl: log(f"idx {s['idx']}: здание {args['building_id']} уже ур.{cur} - пропуск"); stats["skip"] += 1; continue
        if op == "City:addObject":
            used = [k for k, v in city.items() if v.get("slot_id") == args["slot_id"]]
            if used: slot_ids[args["slot_id"]] = int(used[0]); log(f"idx {s['idx']}: слот занят {used[0]} - пропуск"); stats["skip"] += 1; continue
        if op == "Legend2:drawFreeLegend":
            cur_c = city.get("1", {}).get("level")
            if (cur_c is None or int(cur_c) < 5) and a.sp45: speedup_45(s["idx"]); cur_c = 5
            if cur_c is None or int(cur_c) < 5:
                raise SystemExit(f"СТОП: drawFreeLegend только при замке 5 (сейчас {cur_c}) — дождись таймера 4→5 и --from {s['idx']}")
        if op == "Alliance:joinAlliance":
            # shared gate: no two joins into this alliance closer than the random min gap (all workers/processes)
            import alliance_gate; w = alliance_gate.acquire(f"{a.world}:{a.alliance.lower()}", who=os.environ.get("CASTLE_TAG", ""), log=log)
            log(f"[gate] join slot after {w:.0f} s")
        wait_gap(s)
        if op == "City:addObject": args["building_id"] = int(time.time())
        if op in ("Alliance:joinAlliance", "Alliance:leaveAlliance"): args["alliance_id"] = ALLY
        p = send(op, args); extra = ""
        if op == "City:upgradeObject" and not args.get("instant"):
            js = [d for d in walk(((p.get("data") or {}).get("set") or {}).get("job")) if d.get("event_type") == 30 and d.get("job_id")]
            if len(js) != 1: raise SystemExit(f"СТОП: не нашёл job стройки (найдено {len(js)})")
            job["b1"] = js[0]["job_id"]; extra = f" -> job {job['b1']}"
        if op == "Legend2:drawFreeLegend":
            ls = sorted({d.get("legend_id") for d in walk(p.get("data")) if d.get("legend_id")})
            if not ls: raise SystemExit(f"СТОП: страж не взят, ответ {json.dumps(p, ensure_ascii=False)[:600]}")
            legend_got.extend(ls); extra = f" -> легенды {ls}"
            if 107100155 not in ls: raise SystemExit(f"СТОП: нет стража 107100155, легенды {ls}")
            u128 = [d for d in walk(p.get("data")) if str(d.get("type", d.get("key", ""))) == "128"]
            extra += f" user_data128={json.dumps(u128, ensure_ascii=False)[:120]}"
        if op == "Alliance:searchAllianceByUser":
            lst = p.get("payload") or []
            if isinstance(lst, dict): lst = lst.get("list") or []
            want = a.alliance.lower()
            hit = [x for x in lst if isinstance(x, dict) and (str(x.get("acronym", "")).lower() == want or str(x.get("name", "")).lower() == want)]
            log("поиск: " + "; ".join(f"{x.get('alliance_id')} [{x.get('acronym')}] {x.get('name')} world={x.get('world_id')}" for x in lst[:10]))
            if len(hit) != 1: raise SystemExit(f"СТОП: совпадений {len(hit)}")
            if int(hit[0].get("world_id") or 0) != a.world or (want == "3cy" and int(hit[0]["alliance_id"]) != ALLY_EXPECT) or hit[0].get("alliance_id") is None: raise SystemExit(f"СТОП: альянс {hit[0].get('alliance_id')} world {hit[0].get('world_id')}")
            ALLY = int(hit[0]["alliance_id"]); extra = f" -> альянс {ALLY}"
        if op == "City:addObject":
            new = [d for d in walk(p) if "building_id" in d and d.get("slot_id") == args["slot_id"]]
            slot_ids[args["slot_id"]] = int(new[0]["building_id"]) if new else args["building_id"]
        if op == "City:upgradeObject":
            nl = city[str(args["building_id"])]["level"]; extra += f" -> ур.{nl}"
            if lvl and nl < lvl: raise SystemExit(f"СТОП: уровень не вырос{extra}")
        log(f"idx {s['idx']}: {op} ok:1 seq={seq-1}{extra}")
        for sub in s.get("after", []):
            lo2, hi2 = sub["delay_s"]; rest = last_send[0] + random.uniform(lo2, (lo2 + hi2) / 2) - time.time()
            if rest > 0: time.sleep(rest)
            send(sub["op"], sub["args"]); log(f"   + {sub['op']} {sub['args'].get('path')} ok:1")
    log(f"ГОТОВО за {time.time()-t0:.0f} c. отправлено {stats['sent']}, ok:1 {stats['ok']}, пропущено {stats['skip']}")
except SystemExit as e:
    log(f"{e} | отправлено {stats['sent']}, ok:1 {stats['ok']}, пропущено {stats['skip']}, за {time.time()-t0:.0f} c")
finally:
    log(f"замок ур.{city.get('1',{}).get('level')} | стражи {legend_got} | золото {gold_last[0]} | город: " + ", ".join(f"{k}:{v['level']}" for k, v in sorted(city.items(), key=lambda x: int(x[0]))))
