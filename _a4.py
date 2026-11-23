import json,re,glob
L={json.loads(l)["seq"]:json.loads(l) for l in open(glob.glob("logs/run_full_*_231212_resp.jsonl")[0],encoding="utf-8")}
j10=L[10]["resp"]["data"]["set"]["job"][0]; j13=[x for x in L[13]["resp"]["data"]["set"].get("job",[])]
print("idx10 dur",j10["time_end"]-j10["time_start"], "after13", [(x.get("time_end",0)-j10["time_end"]) for x in j13])
print("seq25 time-based remaining:", L[25]["resp"]["data"]["set"]["job"][0]["time_end"]-L[25]["resp"]["time"]//(1000 if L[25]["resp"]["time"]>1e12 else 1))
c=json.load(open("mitm/_castle5_cmds.json",encoding="utf-8"))
items=c if isinstance(c,list) else c.get("cmds") or c.get("steps") or list(c.values())[0]
for i,x in enumerate(items):
    s=json.dumps(x,ensure_ascii=False)
    if re.search(r'freeSecond|drawFree|Consumable|upgradeObject|speed|Helper|gold',s): print(i,re.sub(r'\d{8,}','#',s)[:260])
