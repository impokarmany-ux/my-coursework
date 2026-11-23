import json,sys,re,collections,string
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from mitmproxy import io as mio
from mitmproxy import http as mhttp

toks=[]; fpids=[]
# from device profiles
for p in Path("mitm").glob("device_profile_*.json"):
    d=json.loads(p.read_text(encoding="utf-8"))
    toks.append(d.get("fp_device_token",""))
    fpids.append(d.get("fp_device_id",""))
# from decdevicetoken reqs
for mf in Path("mitm").glob("*.mitm"):
    with open(mf,"rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.request: continue
            if "decdevicetoken" not in (fl.request.path or ""): continue
            try:
                js=json.loads(fl.request.get_text(strict=False) or "")
                toks.append(js.get("fp_device_token",""))
            except: pass
            if fl.response:
                try:
                    r=json.loads(fl.response.get_text(strict=False) or "")
                    fpids.append(((r.get("data") or {}) or {}).get("fp_device_id",""))
                except: pass

print("tokens", len(toks), "uniq", len(set(toks)))
for t in list(dict.fromkeys(toks))[:8]:
    charset=sorted(set(t))
    print(" len",len(t),"start",t[:4],"alnum+/\-_", all(c.isalnum() or c in "+/-=_" for c in t), "has=", "=" in t, "has/", "/" in t)
print("fpids", len(fpids), "uniq", len(set([x for x in fpids if x])))
for f in list(dict.fromkeys([x for x in fpids if x]))[:6]:
    print(" len",len(f),"ts",f[:12],"rest_len",len(f)-12)

# empty push in any captured init (decrypted)?
# check 12 default and docs
# also check if new_account dry-run ever used empty successfully - from АНОНИМНОСТЬ yes

# user_agent samples
uas=set()
for mf in Path("mitm").glob("*.mitm"):
    with open(mf,"rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow): continue
            ua=fl.request.headers.get("User-Agent","")
            if "Dalvik" in ua or "FPX" in ua:
                uas.add(ua)
print("UA count", len(uas))
for u in sorted(uas)[:12]:
    print(" ", u[:100])
