import re,glob
from datetime import datetime as D
for f in ["logs/run_full_20261031_234926.log","logs/run_full_20261031_235426.log","logs/run_full_20261031_232746.log"]:
    try: L=open(f,encoding="utf-8").read().splitlines()
    except Exception: continue
    prev=None
    for l in L:
        m=re.match(r"(\d\d:\d\d:\d\d) (.*)",l)
        if not m: continue
        t=D.strptime(m.group(1),"%H:%M:%S")
        if prev and 0<(t-prev[0]).seconds>=12: print(f, (t-prev[0]).seconds,"s до:",re.sub(r"\d{7,}","#",m.group(2))[:70])
        prev=(t,m.group(2))
