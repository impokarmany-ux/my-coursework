import json,time
L=open("logs/run_full_20261031_231212_resp.jsonl",encoding="utf-8").read().splitlines()
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
for l in L:
    r=json.loads(l)
    if r["seq"] in (22,25,27):
        for d in walk(r["resp"]):
            if d.get("event_type")==30: print(r["seq"], {k:v for k,v in d.items() if not isinstance(v,(dict,list)) and k not in("uid","job_id")}, "now",int(time.time()))
