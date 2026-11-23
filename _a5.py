import json,re
c=json.load(open("mitm/_castle5_cmds.json",encoding="utf-8"))
for i,x in enumerate(c[7:25],7):
    p=x.get("params",{}); print(i,x.get("time_hint"),x.get("class_method"),p.get("op") or x.get("method"),str(p.get("args"))[:100])
