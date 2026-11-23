import json,sys
sys.stdout.reconfigure(encoding="utf-8")
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
for line in open("logs/run_full_20261031_221306_resp.jsonl",encoding="utf-8"):
    o=json.loads(line)
    if o["seq"] not in (10,13,22,25,28,29): continue
    print("==== seq",o["seq"],o["op"],"====")
    for d in walk(o.get("resp")):
        if d.get("building_id")==1 and ("level" in d or "job_id" in d):
            print(json.dumps({k:d[k] for k in d if k in ("building_id","level","type_id","job_id","city_id","uid","status","trace")},ensure_ascii=False))
        if d.get("event_type")==30:
            print("JOB30",json.dumps(d,ensure_ascii=False)[:400])
print("bundle seq", json.load(open("mitm/session_bundle_98570606.json",encoding="utf-8")).get("seq_next"))
