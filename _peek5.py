import json,sys
sys.stdout.reconfigure(encoding="utf-8")
# из ответа idx19/20 текущего замка — что в item/job
lines=open("logs/run_full_20261031_221306_resp.jsonl",encoding="utf-8").read().splitlines()
print("resp lines",len(lines))
# найти useConsumable и последний upgrade, плюс item counts
for line in lines:
    o=json.loads(line)
    if o.get("op") in ("Item:useConsumableItem","City:upgradeObject","Legend2:drawFreeLegend"):
        print("seq",o["seq"],o["op"],"ok", (o.get("resp") or {}).get("ok"))
# walk items for speedup ids
last=json.loads(lines[-2] if len(lines)>1 else lines[-1])  # before fail maybe
# better: parse all set.item from responses
items={}
for line in lines:
    o=json.loads(line)
    resp=o.get("resp") or {}
    data=resp.get("data") or {}
    sett=data.get("set") or {}
    it=sett.get("item") or {}
    if isinstance(it,dict):
        for k,v in it.items():
            if isinstance(v,dict):
                items[str(v.get("item_property_id") or v.get("item_id") or k)]=v
print("item sample keys",list(items)[:20])
for k,v in items.items():
    ip=str(v.get("item_property_id") or "")
    if ip.startswith("600") or "speed" in str(v).lower() or ip in ("6002580","6000029","6000030"):
        print("ITEM",k,json.dumps(v,ensure_ascii=False)[:180])
