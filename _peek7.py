import json,sys,re
sys.stdout.reconfigure(encoding="utf-8")
lines=open("logs/run_full_20261031_221306_resp.jsonl",encoding="utf-8").read().splitlines()
# dump upgrade responses for jobs
for line in lines:
    o=json.loads(line)
    if o.get("op")!="City:upgradeObject":
        continue
    resp=o.get("resp") or {}
    t=json.dumps(resp,ensure_ascii=False)
    # job fields
    jobs=re.findall(r'"job_id":\s*(\d+).*?"duration":\s*(\d+).*?"event_type":\s*(\d+).*?"device":\s*"([^"]*)"', t)
    # looser
    print("seq",o["seq"],"ok",resp.get("ok"))
    for m in re.finditer(r'\{[^{}]*"job_id"[^{}]*\}', t):
        frag=m.group(0)
        if "30" in frag or "duration" in frag or "building" in frag:
            print(" ",frag[:250])
    # level of building 1
    for m in re.finditer(r'\{[^{}]*"building_id":\s*1[^{}]*\}', t):
        print(" b1",m.group(0)[:200])
# also from first account how 4->5 was done - search agent notes / md
