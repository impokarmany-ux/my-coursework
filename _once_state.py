# loadBaseData через guarded — актуальный город
import sys, os, json, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
if not getattr(__import__("requests").Session.request, "__name__", "") == "_forced":
    raise SystemExit("СТОП: только через run_guarded")
import requests
BAD="203.0.113.10"; UID=98570606
B=r"E:\protocol_analysis\capture"; MITM=os.path.join(B,"mitm")
ip=requests.Session().get("https://api.ipify.org?format=json",timeout=15).json().get("ip")
if not ip or ip==BAD: raise SystemExit("СТОП: домашний IP")
s=importlib.util.spec_from_file_location("sc", os.path.join(B,"10_send_cmd.py"))
sc=importlib.util.module_from_spec(s); s.loader.exec_module(sc)
bd=json.load(open(os.path.join(MITM,f"session_bundle_{UID}.json"),encoding="utf-8"))
KEY=bytes.fromhex(bd["aes_key_hex"])
# loadBaseData обычно read - через build_envelope не commit?
# используем тот же send_command как 16_state
p, raw, meta = sc.send_command(KEY, sc.build_envelope("Player", "loadBaseData", bd["session_key"], bd["token"]))
open(os.path.join(B,"logs",f"state_{UID}.json"),"w",encoding="utf-8").write(json.dumps(p,ensure_ascii=False))
print("http",meta.get("http_status"),"ok",(p or {}).get("ok"),"seq NOT burned (read)")
# buildings for this city
def walk(o):
    if isinstance(o,dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o,list):
        for v in o: yield from walk(v)
city=[]
for d in walk(p):
    if d.get("building_id") is not None and d.get("level") is not None and d.get("type_id") is not None:
        if d.get("city_id") in (UID, None) or d.get("uid") in (UID, None):
            city.append((d.get("building_id"), d.get("type_id"), d.get("level"), d.get("slot_id"), d.get("city_id"), d.get("uid")))
# unique by building_id preferring our city
by={}
for b in city:
    bid=b[0]
    if bid not in by or b[4]==UID:
        by[bid]=b
print("buildings", len(by))
for bid in sorted(by, key=lambda x: int(x) if str(x).isdigit() else 0):
    print(by[bid])
golds=sorted({d.get("gold") for d in walk(p) if isinstance(d.get("gold"),(int,float))})
print("gold", golds[:10])
