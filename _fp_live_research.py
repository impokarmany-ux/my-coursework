from pathlib import Path
from mitmproxy import io as mio
from mitmproxy import http as mhttp
import json, re

# 1) deviceprofile/v4 requests: method, headers, body shape
print("=== deviceprofile/v4 & decdevicetoken ===")
for mf in sorted(Path("mitm").glob("*.mitm")):
    with open(mf, "rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.request:
                continue
            path = fl.request.path or ""
            host = fl.request.pretty_host or ""
            if "deviceprofile" not in path and "decdevicetoken" not in path:
                continue
            req = fl.request
            print(f"\nFILE {mf.name}")
            print(f"  {req.method} https://{host}{path}")
            print("  headers:")
            for k,v in req.headers.items():
                vv = v if k.lower() not in ("authorization","fp-device-token","cookie") else f"{v[:4]}…({len(v)})"
                print(f"    {k}: {vv[:120]}")
            body = req.get_text(strict=False) or ""
            print(f"  body_len={len(body)} content-type={req.headers.get('Content-Type','')}")
            print(f"  body_prefix={body[:200]!r}")
            if body.startswith("{"):
                try:
                    js=json.loads(body)
                    print("  json_keys", list(js.keys()))
                    for k,v in js.items():
                        if isinstance(v,str):
                            print(f"    {k}: len={len(v)} prefix={v[:40]!r}")
                        else:
                            print(f"    {k}: {type(v).__name__}={v!r}"[:120])
                except Exception as e:
                    print("  json err", e)
            if fl.response:
                rt = fl.response.get_text(strict=False) or ""
                print(f"  resp {fl.response.status_code} len={len(rt)} prefix={rt[:180]!r}")
