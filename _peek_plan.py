import json,sys
sys.stdout.reconfigure(encoding="utf-8")
plan=json.load(open("mitm/upgrade_plan.json",encoding="utf-8"))
for s in plan["steps"]:
    if s["idx"] > 40: break
    a=s.get("args") or {}
    print("idx",s["idx"],s["op"],"bid",a.get("building_id"),"gold",a.get("gold"),"instant",a.get("instant"),"lvl",s.get("level_reached"))
print("--- prev log ---")
for line in open("logs/run_full_20261031_205143.log",encoding="utf-8"):
    if any(x in line for x in ("drawFree","idx 1","idx 2","idx 3","ур.","замок","СТОП","Страж")):
        if "idx 1" in line and "idx 1" != line[line.find("idx"):line.find("idx")+5]:
            pass
        print(line.rstrip())
