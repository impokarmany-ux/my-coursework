import json,re,glob
L={json.loads(l)["seq"]:json.loads(l) for l in open(glob.glob("logs/run_full_*_231212_resp.jsonl")[0],encoding="utf-8")}
j22=L[22]["resp"]["data"]["set"]["job"][0]; j25=L[25]["resp"]["data"]["set"]["job"][0]
print("job dur",j22["time_end"]-j22["time_start"],"after items end-start",j25["time_end"]-j25["time_start"],"remain at resp",j25["time_end"]-L[25]["resp"]["time"], "shift", j22["time_end"]-j25["time_end"])
st=sorted(glob.glob("logs/state_*.json"),key=lambda p:__import__("os").path.getmtime(p))[-1]
d=json.load(open(st,encoding="utf-8"))["data"]
print("state keys has user_consumable", "user_consumable" in d)
for it in d.get("user_consumable",[]):
    print(" item",it.get("item_property_id"),it.get("quantity"))
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
print("gold", {x.get("gold") for x in walk(d) if "gold" in x and isinstance(x.get("gold"),(int,float))})
