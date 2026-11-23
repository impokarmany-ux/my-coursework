P="16_run_full.py"; s=open(P,encoding="utf-8").read()
a=s.index("def speedup_45(idx):"); b=s.index("def wait_gap")
NEW='''SP_WAIT_MAX = 90   # остаток <= 90 с - ускорители не тратим, ждём остаток+5 с
SP_ITEMS = ((6000029, 300), (6002580, 60))   # предмет, секунд за штуку (6002580 ~60 с - оценка)

def sp_plan(left, inv):
    # сколько штук нужно, чтобы остаток стал <= SP_WAIT_MAX; крупные сначала, без перерасхода
    plan, need = [], left - SP_WAIT_MAX
    for item, sec in SP_ITEMS:
        if need <= 0: break
        q = inv.get(item, 0)
        if q <= 0: continue
        n = min(q, int(need // sec))          # только целые, не перекрывающие остаток
        if n > 0: plan.append((item, n)); need -= n * sec
    if need > 0:                                   # добиваем самым мелким, одной штукой сверху
        for item, sec in reversed(SP_ITEMS):
            used = dict(plan).get(item, 0)
            if inv.get(item, 0) - used > 0:
                k = min(inv[item] - used, -(-int(need) // sec))
                plan = [(i, n + k) if i == item else (i, n) for i, n in plan] if used else plan + [(item, k)]
                break
    return plan

def speedup_45(idx):
    # 1) остаток <= 90 с - просто ждём (не дольше остатка+5 с)
    # 2) иначе предметы из инвентаря последнего ответа, ровно на (остаток-90) с; золото не тратим
    # 3) перед каждым useConsumableItem проверяем по последнему ответу, что стройка ещё идёт
    left = sp_left()
    log(f"[sp45] idx {idx}: осталось {left if left is None else round(left)} с, предметы { {i: sp['inv'].get(i) for i, _ in SP_ITEMS} }")
    if left is None: raise SystemExit(f"СТОП: [sp45] нет данных о job замка - жди таймер и --from {idx}")
    for item, n in sp_plan(left, sp["inv"]):
        left = sp_left()
        if left is None or left <= SP_WAIT_MAX: log("[sp45] стройка завершена/почти - ускорители больше не шлём"); break
        if sp["inv"].get(item, 0) < n: n = sp["inv"].get(item, 0)
        if n <= 0: continue
        wait_gap({"delay_s_min": 2.5, "delay_s_max": 4.0})
        send("Item:useConsumableItem", {"job_id": sp["job"], "amount": n, "legend_id": "", "item_id": item, "type": "speedup", "extra_content": ""})
        stats.setdefault("sp45_items", []).append((item, n))
        log(f"[sp45] предмет {item} x{n}, осталось {round(max(0, sp_left() or 0))} с")
    left = max(0.0, sp_left() or 0)
    if left > 0:
        if left > a.sp45_wait: raise SystemExit(f"СТОП: [sp45] осталось {round(left)} с > лимита - --from {idx}")
        log(f"[sp45] жду таймер {round(left)+5} с"); stats["sp45_wait"] = round(left) + 5; time.sleep(left + 5)
    city.setdefault("1", {})["level"] = 5
    log("[sp45] таймер 4->5 истёк, замок считаем 5")

'''
s=s[:a]+NEW+s[b:]
# альянс: тег или id; по умолчанию 3cy
s=s.replace('ap.add_argument("--alliance", required=True);','ap.add_argument("--alliance", default="3cy");',1)
s=s.replace('a = ap.parse_args()','a = ap.parse_args()\n# --alliance можно задать id: ищем всё равно по тегу 3cy и сверяем id\nif str(a.alliance).strip().isdigit():\n    if int(a.alliance) != 1035611: raise SystemExit("СТОП: неизвестный id альянса")\n    a.alliance = "3cy"',1)
open(P,"w",encoding="utf-8").write(s)
print("parse_args patched", "isdigit()" in s)
