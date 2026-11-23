import re,json,os
d=r"E:\protocol_analysis\capture\mitm\decrypted_send"
# list around init
files=sorted(os.listdir(d))
print([f for f in files if f.startswith(("003","004","005","006","007"))][:40])
# show 0038 resp if any, and first file that contains token JWT
for n in files:
  if not n.endswith('.txt'): continue
  t=open(os.path.join(d,n),encoding='utf-8',errors='ignore').read()
  if '"token":"eyJ' in t or '"token": "eyJ' in t:
    # classify
    m=re.search(r'"class"\s*:\s*"([^"]+)".*?"method"\s*:\s*"([^"]+)"', t)
    # for resp look at ok and if token in payload or params
    has_params='"params"' in t[:200]
    print("FIRST JWT FILE",n,"len",len(t),"has_params",has_params)
    # show surrounding of token field name contexts
    for m2 in re.finditer(r'.{0,80}"token"\s*:\s*"eyJ[^"]{0,30}', t):
      print(" CTX",m2.group(0)[-100:])
      break
    # if request, show class/method
    cm=re.search(r'"class"\s*:\s*"([^"]+)".{0,40}"method"\s*:\s*"([^"]+)"', t)
    if cm: print(" class/method",cm.group(1),cm.group(2))
    # top keys
    try:
      j=json.loads(t)
      print(" top",list(j.keys())[:15])
      if "payload" in j and isinstance(j["payload"],dict):
        print(" payload keys",list(j["payload"].keys())[:20])
        if "token" in j["payload"]:
          print(" token IN PAYLOAD len",len(j["payload"]["token"]))
      if "params" in j and isinstance(j["params"],dict) and "token" in j["params"]:
        print(" token IN PARAMS (client->server)")
    except Exception as e:
      print(" json err",e)
    break
# also show call:init response - find resp right after 0038_req
for n in ["0039_resp.bin.txt","0043_resp.bin.txt","0044_resp.bin.txt","0045_resp.bin.txt","0046_resp.bin.txt"]:
  p=os.path.join(d,n)
  if os.path.exists(p):
    t=open(p,encoding='utf-8').read()
    print("====",n,"len",len(t),"has token", "eyJ" in t, "has session_key", "session_key" in t)
    try:
      j=json.loads(t)
      print(" ok",j.get("ok"),"payload keys", list((j.get("payload") or {}).keys())[:25] if isinstance(j.get("payload"),dict) else type(j.get("payload")).__name__)
    except Exception as e: print(" err",e)
