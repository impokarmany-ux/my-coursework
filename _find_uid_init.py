import os,re,json
# any file mentioning both 98566384 and chat_token or method init
hits=[]
for root,dirs,files in os.walk(r"E:\protocol_analysis\capture\mitm"):
  # skip huge
  dirs[:] = [d for d in dirs if d not in ('bodies','raw_api','raw_api_send','flows')]
  for f in files:
    if not f.endswith(('.txt','.json','.log')): continue
    p=os.path.join(root,f)
    try:
      sz=os.path.getsize(p)
      if sz>20_000_000: continue
      t=open(p,encoding='utf-8',errors='ignore').read()
    except: continue
    if '98566384' in t and ('chat_token' in t or '"method":"init"' in t):
      hits.append((sz,p))
print("hits",len(hits))
for sz,p in sorted(hits)[:15]:
  print(sz, p)
