import os,re,json
# find init responses for uid 98566384
for root in [r"E:\protocol_analysis\capture\mitm\decrypted_send", r"E:\protocol_analysis\capture\mitm\decrypted"]:
  if not os.path.isdir(root): continue
  for n in sorted(os.listdir(root)):
    if "resp" not in n: continue
    p=os.path.join(root,n)
    try:
      t=open(p,encoding='utf-8',errors='ignore').read()
    except: continue
    if "98566384" not in t: continue
    if '"token":"eyJ' not in t and '"token": "eyJ' not in t: continue
    # likely init payload
    if '"chat_token"' not in t: continue
    print("FOUND",root,n,"len",len(t))
    j=json.loads(t)
    pay=j.get("payload") or {}
    print(" uid",pay.get("uid"),"ok",j.get("ok"))
    print(" token len",len(pay.get("token") or ""),"chat_token len",len(pay.get("chat_token") or ""))
    print(" city_ids",pay.get("city_ids"))
    # seq in data?
    print(" top keys",list(j.keys()))
    # look for seq field near start of commits after this - skip
    # decode jwt payload (no verify) redacted
    tok=pay.get("token") or ""
    if tok:
      import base64
      part=tok.split(".")[1]
      part += "="*((-len(part))%4)
      payload=json.loads(base64.urlsafe_b64decode(part))
      # redact
      safe={k:(str(v)[:20]+"..." if isinstance(v,str) and len(str(v))>20 else v) for k,v in payload.items()}
      print(" jwt claims",safe)
    break
