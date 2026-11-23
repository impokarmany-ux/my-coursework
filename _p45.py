import re
P="16_run_full.py"; s=open(P,encoding="utf-8").read()
s=s.replace('ap.add_argument("--world", type=int, required=True)',
 'ap.add_argument("--world", type=int, required=True)\n# ускорение 4->5: по умолчанию выключено\nap.add_argument("--speedup-45", dest="sp45", action="store_true")\nap.add_argument("--speedup-45-maxwait", dest="sp45_wait", type=int, default=1200)',1)
s=s.replace('job = {}; legend_got = []','job = {}; legend_got = []\n# сведения для --speedup-45: последний job замка, его конец (серверное время), сдвиг часов, инвентарь из ответов\nsp = {"job": None, "end": None, "dt": 0.0, "inv": {}}',1)
s=s.replace('    return p\n\ndef wait_gap','''    # запоминаем job стройки (event 30), серверное время и количество предметов из последнего ответа
    if isinstance(p.get("time"), (int, float)): sp["dt"] = (p["time"] / (1000 if p["time"] > 1e12 else 1)) - time.time()
    for d in walk(((p.get("data") or {}).get("set") or {}).get("job")):
        if d.get("event_type") == 30 and d.get("job_id") and d.get("time_end"): sp["job"], sp["end"] = d["job_id"], d["time_end"]
    for d in walk(((p.get("data") or {}).get("set") or {}).get("user_consumable")):
        if d.get("item_property_id") and isinstance(d.get("quantity"), int): sp["inv"][int(d["item_property_id"])] = d["quantity"]
    return p

def sp_left():
    # сколько секунд осталось до конца стройки замка по серверным часам
    return None if sp["end"] is None else sp["end"] - (time.time() + sp["dt"])

def speedup_45(idx):
    # 1) бесплатно: предметы ускорения, только если последний ответ показал количество > 0
    # 2) золото НЕ используем: протокол ускорения за золото не записан
    # 3) иначе ждём остаток таймера (не дольше --speedup-45-maxwait), сервер сам завершает стройку
    left = sp_left()
    log(f"[sp45] idx {idx}: осталось {left if left is None else round(left)} с, предметы {{6002580: {sp['inv'].get(6002580)}, 6000029: {sp['inv'].get(6000029)}}}")
    if left is None: raise SystemExit(f"СТОП: [sp45] нет данных о job замка - жди таймер и --from {idx}")
    for item, sec in ((6000029, 300), (6002580, 60)):
        if left <= 15: break
        q = sp["inv"].get(item, 0)
        if q <= 0 or (item == 6000029 and left < 240): continue
        n = min(q, max(1, int(left // sec)))
        wait_gap({"delay_s_min": 2.5, "delay_s_max": 4.0})
        send("Item:useConsumableItem", {"job_id": sp["job"], "amount": n, "legend_id": "", "item_id": item, "type": "speedup", "extra_content": ""})
        log(f"[sp45] предмет {item} x{n}, осталось {round(sp_left() or 0)} с, на складе {sp['inv'].get(item)}")
        left = sp_left() or 0
    if left > 0:
        if left > a.sp45_wait: raise SystemExit(f"СТОП: [sp45] осталось {round(left)} с > лимита - --from {idx}")
        log(f"[sp45] жду таймер {round(left)+5} с"); time.sleep(left + 5)
    city.setdefault("1", {})["level"] = 5
    log("[sp45] таймер 4->5 истёк, замок считаем 5")

def wait_gap''',1)
s=s.replace('            if cur_c is None or int(cur_c) < 5:\n','            if (cur_c is None or int(cur_c) < 5) and a.sp45: speedup_45(s["idx"]); cur_c = 5\n            if cur_c is None or int(cur_c) < 5:\n',1)
open(P,"w",encoding="utf-8").write(s)
