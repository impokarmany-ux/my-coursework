import json
from pathlib import Path

hits = []
for p in Path(".").rglob("*.json"):
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    if '"appsflyer_id"' in t and '"fp_device_id"' in t and '"device"' in t:
        hits.append(p)

print("hits", len(hits))
for h in hits[:8]:
    d = json.loads(h.read_text(encoding="utf-8"))
    def find_params(o):
        if isinstance(o, dict):
            if "appsflyer_id" in o and "fp_device_id" in o:
                return o
            for v in o.values():
                r = find_params(v)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = find_params(v)
                if r:
                    return r
        return None
    params = find_params(d)
    if params:
        print(h, "nkeys", len(params), "keys", sorted(params.keys()))
