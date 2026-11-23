P="16_run_full.py"; s=open(P,encoding="utf-8").read()
old='''        if d.get("event_type") == 30 and d.get("job_id") and d.get("time_end"): sp["job"], sp["end"] = d["job_id"], d["time_end"]'''
new='''        # ответ ускорения приходит без event_type - сверяем по job_id
        if d.get("job_id") and d.get("time_end") and (d.get("event_type") == 30 or (op == "Item:useConsumableItem" and d.get("job_id") == sp["job"])): sp["job"], sp["end"] = d["job_id"], d["time_end"]
    # ускорение вернуло ok, а нашего job в ответе нет - стройка завершена
    if op == "Item:useConsumableItem" and isinstance(args, dict) and args.get("job_id") == sp["job"] and not any(d.get("job_id") == sp["job"] for d in walk(((p.get("data") or {}).get("set") or {}).get("job"))): sp["end"] = time.time() + sp["dt"]'''
assert old in s; s=s.replace(old,new,1); open(P,"w",encoding="utf-8").write(s)
