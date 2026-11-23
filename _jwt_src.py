import re,json,os
# Where does JWT token come from? Search decrypted for eyJ
d=r"E:\protocol_analysis\capture\mitm\decrypted_send"
hits=[]
for n in sorted(os.listdir(d)):
  p=os.path.join(d,n)
  if not n.endswith('.txt'): continue
  t=open(p,encoding='utf-8',errors='ignore').read()
  if 'eyJ' in t:
    # find context
    for m in re.finditer(r'"(token|session_key|chat_token|jwt)"\s*:\s*"(eyJ[^"]+)"', t):
      hits.append((n,m.group(1),len(m.group(2)),m.group(2)[:20]))
    if not any(h[0]==n for h in hits[-5:]):
      # maybe in non-json
      m=re.search(r'eyJ[A-Za-z0-9_\-]{10,}', t)
      if m: hits.append((n,'raw',len(m.group(0)),m.group(0)[:20]))
print("JWT hits in decrypted_send:", len(hits))
for h in hits[:20]: print(h)

# also check harvest scripts for how token is obtained
for script in ["_harvest_new.py","_harvest_session.py","_patch_bundle.py"]:
  p=rf"E:\protocol_analysis\capture\mitm\{script}"
  if os.path.exists(p):
    t=open(p,encoding='utf-8',errors='ignore').read()
    print("====",script)
    for m in re.finditer(r'.{0,40}(?:token|session_key|call:init|jwt).{0,60}', t):
      print(" ",m.group(0)[:120])
