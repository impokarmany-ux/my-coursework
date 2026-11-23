import json,glob,os
f=sorted(glob.glob("logs/run_full_*_resp.jsonl"),key=os.path.getmtime)[-1]; print(f)
for l in open(f,encoding="utf-8"):
    x=json.loads(l)
    if x["seq"] in (22,25,27,29,30):
        p=x["resp"]; t=p.get("time"); t=t/1000 if t and t>1e12 else t
        s=(p.get("data") or {}).get("set") or {}
        print(x["seq"],x["op"],"jobs",[(j.get("event_type"),j.get("time_end",0)-t, j.get("job_id")==None) for j in s.get("job",[])] if isinstance(s.get("job"),list) else s.get("job"),
              "cons",[(c.get("item_property_id"),c.get("quantity")) for c in s.get("user_consumable",[])] if isinstance(s.get("user_consumable"),list) else s.get("user_consumable"),"ud",str(s.get("user_data"))[:120])
