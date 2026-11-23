import json,urllib.parse
data=json.load(open(r"E:\protocol_analysis\capture\mitm\_pp_all.json",encoding='utf-8'))
# timeline of passport+funplus around newacct token_login for teaching acct
rows=[r for r in data if r.get('file')=='flows_newacct.mitm']
rows=sorted(rows,key=lambda r:r.get('t') or 0)
# show sequence around second token_login (L4hx)
for r in rows:
  body=r.get('rqb') or ''
  qs=urllib.parse.parse_qs(body,keep_blank_values=True)
  method=(qs.get('method') or [''])[0]
  host=r.get('host','')
  path=r.get('path','')
  if 'passport' in host or 'funplus' in host or 'gog-global' in host:
    auth_tok=(qs.get('auth_token') or [''])[0]
    flag='L4' if auth_tok.startswith('L4') else ('QO' if auth_tok.startswith('QO') else '')
    print(f"{r['t']:.1f} {host}{path} method={method or '-'} {flag}")
