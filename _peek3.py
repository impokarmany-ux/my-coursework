import json,sys
sys.stdout.reconfigure(encoding="utf-8")
plan=json.load(open("mitm/upgrade_plan.json",encoding="utf-8"))
for s in plan["steps"]:
    if s["idx"] in (9,10,19,20,24) or (s.get("args") or {}).get("building_id")==1:
        print(json.dumps(s, ensure_ascii=False, indent=2)[:800])
        print("---")
# look for 4->5 in commits / recorded
for name in ["mitm/all_commits.json","logs/all_commits.json"]:
    try:
        data=json.load(open(name,encoding="utf-8"))
        print(name,"type",type(data).__name__,"len",len(data) if hasattr(data,"__len__") else "")
    except Exception as e:
        print(name,e)
