import re,sys,collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from mitmproxy import io as mio
from mitmproxy import http as mhttp

hosts=collections.Counter()
interesting=[]
for mf in Path("mitm").glob("*.mitm"):
    with open(mf,"rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.request: continue
            host=fl.request.pretty_host or ""
            path=fl.request.path or ""
            hosts[host]+=1
            hlow=host.lower()+path.lower()
            if any(x in hlow for x in ("device","funplus","fpid","fingerprint","account","passport","adjust","appsflyer","firebase","install")):
                hdr=dict(fl.request.headers)
                interesting.append((host, path[:80], fl.request.method, list(hdr.keys())[:12], "Fp-Device-Token" in hdr or "fp-device-token" in {k.lower() for k in hdr}))

print("all hosts:")
for h,c in hosts.most_common(30):
    print(f"  {c:4d} {h}")
print("interesting", len(interesting))
for x in interesting[:40]:
    print(x[2], x[0]+x[1], "has_fp_tok", x[4], "hdrs", x[3])
