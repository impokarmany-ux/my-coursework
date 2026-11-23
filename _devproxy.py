import json,sys,re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from mitmproxy import io as mio
from mitmproxy import http as mhttp

def redact(s, n=6):
    s=str(s)
    if len(s)<=n*2: return f"len={len(s)}"
    return f"{s[:n]}…({len(s)})"

for mf in Path("mitm").glob("*.mitm"):
    with open(mf,"rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.request: continue
            host=fl.request.pretty_host or ""
            path=fl.request.path or ""
            if "devproxy" not in host: continue
            print("="*60)
            print(mf.name, fl.request.method, host+path)
            print("req headers:", {k: (redact(v) if "token" in k.lower() or "auth" in k.lower() else v) for k,v in fl.request.headers.items()})
            try:
                body=fl.request.get_text(strict=False) or ""
            except: body=""
            print("req body len", len(body))
            # try parse json
            try:
                js=json.loads(body)
                print("req json keys", list(js.keys()) if isinstance(js,dict) else type(js))
                def show(o, indent=0):
                    if isinstance(o, dict):
                        for k,v in o.items():
                            if isinstance(v,(dict,list)):
                                print(" "*indent+k+":")
                                show(v, indent+2)
                            else:
                                vs=str(v)
                                sens=any(x in k.lower() for x in ("token","id","guid","android","device","fp"))
                                print(" "*indent+f"{k}: len={len(vs)} shape={vs[:4]}…" if sens and len(vs)>8 else " "*indent+f"{k}: {v}")
                    elif isinstance(o, list):
                        print(" "*indent+f"list[{len(o)}]")
                        if o: show(o[0], indent+2)
                show(js)
            except Exception as e:
                print("req not json", body[:200].replace("\n"," "))
            if fl.response:
                print("status", fl.response.status_code)
                try:
                    rb=fl.response.get_text(strict=False) or ""
                except: rb=""
                print("resp len", len(rb))
                try:
                    rjs=json.loads(rb)
                    print("resp keys", list(rjs.keys()) if isinstance(rjs,dict) else type(rjs))
                    # mask values
                    def showr(o, indent=0, depth=0):
                        if depth>4: return
                        if isinstance(o, dict):
                            for k,v in list(o.items())[:30]:
                                if isinstance(v,(dict,list)):
                                    print(" "*indent+k+":")
                                    showr(v, indent+2, depth+1)
                                else:
                                    vs=str(v)
                                    if any(x in k.lower() for x in ("token","id","guid","key","secret","fp")) and len(vs)>10:
                                        print(" "*indent+f"{k}: len={len(vs)} prefix={vs[:4]}")
                                    else:
                                        print(" "*indent+f"{k}: {v}")
                        elif isinstance(o, list):
                            print(" "*indent+f"list[{len(o)}]")
                            if o: showr(o[0], indent+2, depth+1)
                    showr(rjs)
                except:
                    print("resp text", rb[:300])
