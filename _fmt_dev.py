import json,sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
# load one device profile - show KEYS and format shapes only (no full values)
for p in sorted(Path("mitm").glob("device_profile_*.json"))[:2]:
    d=json.loads(p.read_text(encoding="utf-8"))
    print("FILE", p.name, "keys", sorted(d.keys()))
    for k in sorted(d.keys()):
        v=d[k]
        if isinstance(v,str):
            print(f"  {k}: len={len(v)} sample_shape={v[:4]}... type_hint=", end="")
            if all(c in "0123456789abcdef" for c in v.lower()) and len(v) in (16,32,40,64):
                print(f"hex{len(v)}")
            elif "-" in v and len(v)>20:
                print("dashed", v.count("-"), "parts", [len(x) for x in v.split("-")])
            elif v.startswith("XZ"):
                print("XZ+rest", len(v)-2)
            else:
                print("other")
        else:
            print(f"  {k}: {type(v).__name__}={v if not isinstance(v,(dict,list)) else '...'}")
