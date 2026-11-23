import json,sys
sys.stdout.reconfigure(encoding="utf-8")
# где в плане апгрейд замка 4->5?
plan=json.load(open("mitm/upgrade_plan.json",encoding="utf-8"))
for s in plan["steps"]:
    a=s.get("args") or {}
    if a.get("building_id")==1 or s["op"]=="Legend2:drawFreeLegend":
        print("idx",s["idx"],s["op"],"gold",a.get("gold"),"instant",a.get("instant"),"lvl",s.get("level_reached"),"job",a.get("job_id"))
# seq_next now
b=json.load(open("mitm/session_bundle_98570606.json",encoding="utf-8"))
print("seq_next",b.get("seq_next"),"plan_start",b.get("plan_start_idx"))
