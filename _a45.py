import json,glob,re
plan=json.load(open("mitm/upgrade_plan.json",encoding="utf-8"))
for s in plan["steps"]:
    if 8<=s["idx"]<=24: print("PLAN",s["idx"],s["op"],json.dumps(s.get("args"),ensure_ascii=False)[:150],"lvl",s.get("level_reached"),"gap",s.get("gap_s") or (s.get("delay_s_min"),s.get("delay_s_max")),"after",[a["op"] for a in s.get("after",[])])
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
for f in sorted(glob.glob("logs/run_full_*_resp.jsonl")):
    print("==",f)
    for l in open(f,encoding="utf-8"):
        r=json.loads(l)
        if r["seq"]>45: continue
        info=[]
        for d in walk(r["resp"]):
            if d.get("event_type")==30: info.append(("job",d.get("time_end",0)-d.get("time_start",0)))
            if "gold" in d and isinstance(d["gold"],(int,float)): info.append(("gold",d["gold"]))
            if "item_id" in d: info.append(("item",d.get("item_id"),d.get("num",d.get("count"))))
        print(r["seq"],r["op"],info[:8])
