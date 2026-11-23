import json,sys,time
sys.stdout.reconfigure(encoding="utf-8")
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
for line in open("logs/run_full_20261031_221306_resp.jsonl",encoding="utf-8"):
    o=json.loads(line)
    if o["seq"]!=25: continue
    p=o["resp"]
    print("ok",p.get("ok"),"keys",list(p)[:20])
    print(json.dumps(p,ensure_ascii=False)[:2000])
    for d in walk(p):
        if d.get("job_id") or d.get("item_property_id") or d.get("building_id")==1:
            print(">",json.dumps(d,ensure_ascii=False)[:300])
print("local now", time.time())
# server time from last state
st=json.load(open("logs/state_98570606.json",encoding="utf-8"))
print("state time", st.get("time"), "server_s", (st.get("time") or 0)//1000 if st.get("time") else None)
