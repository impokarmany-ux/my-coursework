import json
p=r"E:\protocol_analysis\capture\mitm\session_bundle_new.json"
d=json.load(open(p,encoding="utf-8"))
def show(o,prefix=""):
  if isinstance(o,dict):
    for k,v in o.items():
      if isinstance(v,(dict,list)):
        print(f"{prefix}{k}: {type(v).__name__} len={len(v)}")
        if isinstance(v,dict) and len(v)<20: show(v,prefix+"  ")
        elif isinstance(v,list) and v and isinstance(v[0],dict) and len(v)<=3:
          show(v[0],prefix+"  [0].")
      else:
        s=str(v)
        sens=any(x in k.lower() for x in ("token","key","secret","jwt","pass","auth","session"))
        if sens and isinstance(v,str) and len(s)>8:
          print(f"{prefix}{k}: {s[:4]}...({len(s)})")
        else:
          print(f"{prefix}{k}: {s[:80]}")
  else:
    print(prefix,type(o),str(o)[:60])
show(d)
