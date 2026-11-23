import json
p=json.load(open(r"mitm\upgrade_plan.json",encoding="utf-8"))
print(p.keys() if isinstance(p,dict) else type(p), len(p["steps"]))
for s in p["steps"]:
    a=s.get("args") or {}
    op=s["op"]
    if op.startswith("Alliance") or "elp" in op or s["idx"]>=105 or (op=="City:upgradeObject" and str(a.get("building_id"))=="1"):
        print(s["idx"], op, json.dumps({k:v for k,v in a.items() if k not in("uid","city_id")},ensure_ascii=False)[:120], s.get("target_level", s.get("level")), [x["op"] for x in s.get("after",[])])
