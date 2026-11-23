import os,re,json,gzip
from pathlib import Path
# search decrypted_send and logs for call init / kingdom_id
roots=[
 r"E:\protocol_analysis\capture\mitm\decrypted_send",
 r"E:\protocol_analysis\capture\logs",
 r"E:\protocol_analysis\capture\mitm",
]
for root in roots:
  if not os.path.isdir(root):
    print("missing",root); continue
  print("===",root)
  for n in sorted(os.listdir(root))[:5]:
    print(" ",n)
  # only scan text files under 5MB for kingdom_id / "method\":\"init\"
  hits=0
  for dirpath,_,files in os.walk(root):
    for f in files:
      if not f.endswith(('.txt','.json','.log','.py')): continue
      p=os.path.join(dirpath,f)
      try:
        sz=os.path.getsize(p)
        if sz>5_000_000: continue
        t=open(p,encoding='utf-8',errors='ignore').read()
      except: continue
      if 'kingdom_id' in t or '"method":"init"' in t or '"method": "init"' in t or 'call:init' in t:
        # show context
        for m in re.finditer(r'.{0,40}(?:kingdom_id|"method"\s*:\s*"init"|call:init).{0,80}', t):
          s=m.group(0)
          s=re.sub(r'"(session_key|token|auth_token)"\s*:\s*"[^"]+"', r'"\1":"<R>"', s)
          print(f"HIT {os.path.relpath(p,root)} :: {s[:200]}")
          hits+=1
          if hits>25: break
      if hits>25: break
    if hits>25: break
  print("hits",hits)
