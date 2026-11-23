import re,json,os
def redact_obj(o):
  if isinstance(o,dict):
    out={}
    for k,v in o.items():
      if isinstance(v,str) and (any(x in k.lower() for x in ("token","key","secret","jwt","auth","session")) or len(v)>80):
        out[k]=f"<R:{len(v)} {v[:4]}…>"
      else:
        out[k]=redact_obj(v)
    return out
  if isinstance(o,list):
    if len(o)>3: return [redact_obj(o[0]), f"...({len(o)} items)"]
    return [redact_obj(x) for x in o]
  return o

# 0094_resp should be init response (paired with 0094_req)
for n in ["0094_resp.json.txt","0094_resp.txt"]:
  p=rf"E:\protocol_analysis\capture\mitm\decrypted\{n}"
  if not os.path.exists(p): continue
  t=open(p,encoding='utf-8').read()
  print("====",n,"len",len(t))
  j=json.loads(t)
  print("top",list(j.keys()),"ok",j.get("ok"),"time",j.get("time"))
  pay=j.get("payload")
  print("payload type",type(pay).__name__, "keys" if isinstance(pay,dict) else "", list(pay.keys())[:30] if isinstance(pay,dict) else str(pay)[:80])
  data=j.get("data")
  if isinstance(data,dict):
    print("data keys",list(data.keys())[:20])
    # set/del often
    for sec in ("set","del","update"):
      if sec in data and isinstance(data[sec],dict):
        print(f" data.{sec} tables:",list(data[sec].keys())[:40])
  # find token-like
  for m in re.finditer(r'"(session_key|token|chat_token|seq|uid|fpid|world_id|kingdom_id)"\s*:\s*("[^"]*"|\d+)', t):
    k=m.group(1); v=m.group(2)
    if v.startswith('"') and len(v)>20:
      print(f"  field {k} len={len(v)-2} prefix={v[1:5]}")
    else:
      print(f"  field {k}={v}")
  # print first 500 of redacted payload if dict with interesting keys
  if isinstance(pay,dict):
    print("payload redacted sample:", json.dumps(redact_obj(pay),ensure_ascii=False)[:1200])
