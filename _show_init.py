import re,json
def redact(t):
  t=re.sub(r'"(session_key|token|chat_token|auth_token|push_token)"\s*:\s*"[^"]*"', lambda m: f'"{m.group(1)}":"<R:{len(m.group(0))-len(m.group(1))-4}>"', t)
  return t
# full init req
for p in [
 r"E:\protocol_analysis\capture\mitm\decrypted_send\0038_req.bin.txt",
 r"E:\protocol_analysis\capture\mitm\decrypted\0094_req.json.txt",
]:
  t=open(p,encoding='utf-8',errors='ignore').read()
  print("====REQ",p)
  print(redact(t)[:2500])
  print()
# find matching resp for 0094
import os
d=r"E:\protocol_analysis\capture\mitm\decrypted"
cands=[n for n in os.listdir(d) if n.startswith("009") and "resp" in n]
print("nearby resp",cands)
for n in ["0095_resp.json.txt","0096_resp.json.txt","0097_resp.json.txt","0095_resp.txt"]:
  p=os.path.join(d,n)
  if os.path.exists(p):
    t=open(p,encoding='utf-8',errors='ignore').read()
    print("====RESP",n,"len",len(t))
    # show top keys and long string fields redacted
    try:
      j=json.loads(t)
      print("top",list(j.keys()))
      pay=j.get("payload") or j.get("data") or {}
      if isinstance(pay,dict):
        print("payload keys",list(pay.keys())[:50])
        for k,v in pay.items():
          if isinstance(v,str) and len(v)>20:
            print(f"  long {k} len={len(v)} prefix={v[:8]}")
          elif isinstance(v,(int,float,bool)) or v is None:
            print(f"  {k}={v}")
          elif isinstance(v,dict):
            print(f"  {k}=dict keys={list(v.keys())[:20]}")
          elif isinstance(v,list):
            print(f"  {k}=list len={len(v)}")
      # also seq
      print("ok",j.get("ok"),"seq",j.get("seq"),"time",j.get("time"))
      # search session_key in whole
      for kn in ["session_key","token","chat_token","seq","uid","fpid","kingdom_id","world_id"]:
        if kn in t:
          print("contains",kn)
    except Exception as e:
      print("parse err",e)
      print(redact(t)[:800])
