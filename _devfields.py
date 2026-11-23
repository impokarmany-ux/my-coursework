import json,urllib.parse
data=json.load(open(r"E:\protocol_analysis\capture\mitm\_pp_all.json",encoding='utf-8'))
for r in data:
  body=r.get('rqb') or ''
  if 'method=token_login' not in body or 'L4hx' not in body: continue
  qs={k:v[0] for k,v in urllib.parse.parse_qs(body,keep_blank_values=True).items()}
  for k in sorted(qs):
    v=qs[k]
    if k=='auth_token': print(f"{k}=<R:{len(v)}>")
    else: print(f"{k}={v}")
  rqh=r.get('rqh') or {}
  for k,v in rqh.items():
    if k.lower() in ('authorization','fp-device-token','user-agent'):
      print(f"HDR {k}=<R:{len(v)} prefix={v[:6]}>")
  break
# FDT from same request - save length/structure only
