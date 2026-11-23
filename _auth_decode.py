import json,base64,hmac,hashlib,urllib.parse
from pathlib import Path
pp=Path(r"E:\protocol_analysis\capture\mitm\_pp_all.json")
data=json.load(open(pp,encoding='utf-8'))
print("total rows",len(data),"keys",list(data[0].keys()) if data else None)
rows=[r for r in data if 'gog-passport' in r.get('host','') and 'token_login' in (r.get('rqb') or '')]
print("token_login rows",len(rows))
for r in rows[:2]:
    print("---",r.get('file'),r.get('t'))
    rqh=r.get('rqh') or {}
    # normalize
    auth=None; fdt=None
    for k,v in rqh.items():
        lk=k.lower()
        if lk=='authorization': auth=v
        if lk=='fp-device-token': fdt=v
    body=r.get('rqb') or ''
    print("auth", (auth or '')[:20]+"...", "fdt",(fdt or '')[:10]+"...")
    if auth and ':' in auth:
        b64=auth.split(':',1)[-1].strip()
        raw=base64.b64decode(b64)
        print("decoded len",len(raw),"hex",raw.hex()[:64],"ascii?",all(32<=c<127 for c in raw))
        try: print("text",raw.decode()[:90])
        except: pass
    qs=urllib.parse.parse_qs(body,keep_blank_values=True)
    for k,v in qs.items():
        vv=v[0]
        if any(x in k for x in ('token','guid','device','android','session','imei')):
            print(f"  {k}={vv[:6]}...({len(vv)})")
        else:
            print(f"  {k}={vv}")
