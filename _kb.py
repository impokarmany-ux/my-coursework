import json
from pathlib import Path
b=sorted(Path("mitm").glob("session_bundle_*.json"),key=lambda p:p.stat().st_mtime)[-1]
d=json.loads(b.read_text(encoding="utf-8"))
def walk(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items():
            if any(s in k.lower() for s in ("kingdom","world","server","model","time_zone","fp_registered")) and not isinstance(v,(dict,list)): print(p+k,"=",v)
            walk(v,p+k+".")
walk(d); print(sorted(d.keys()))
print(json.loads(sorted(Path("logs").glob("init_resp_k837_*.json"))[-1].read_text(encoding="utf-8"))["payload_keys"])
