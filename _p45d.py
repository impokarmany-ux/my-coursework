P="16_run_full.py"; s=open(P,encoding="utf-8").read()
a=s.index("SP_WAIT_MAX = 90"); b=s.index("def wait_gap")
NEW='''SP_ITEMS = ((6000029, 300), (6002580, 60))   # предмет, секунд за штуку (6002580 ~60 с - не подтверждено)

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

'''
s=s[:a]+NEW+s[b:]; open(P,"w",encoding="utf-8").write(s)
