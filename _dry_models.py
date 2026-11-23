from pathlib import Path
import json, re
log = Path("logs/dryrun_models.txt").read_text(encoding="utf-8", errors="replace")
for line in log.splitlines():
    if any(x in line for x in ("[ids]", "[tz]", "[init-check]", "[sign]", "[order]", "DRY-RUN: bundle", "=== ", "model=")):
        # strip any accidental long hex
        print(re.sub(r'[0-9a-fA-F]{16,}', '…', line)[:200])

devs = sorted(Path("mitm").glob("device_20*.json"), key=lambda p: p.stat().st_mtime)
d = json.loads(devs[-1].read_text(encoding="utf-8"))
need = ["model","manufacturer","user_agent","fpx_user_agent","os_version","build_id","time_zone","api_level"]
print("profile", devs[-1].name)
for k in need:
    v = d.get(k)
    print(f"  {k}: present={v is not None} type={type(v).__name__} len={len(str(v)) if v is not None else 0}")
print("  UA contains model:", d.get("model","") in (d.get("user_agent") or ""))
print("  fpx contains api:", f"v{d.get('api_level')}" in (d.get("fpx_user_agent") or ""))
# pool coverage dry: generate all models once
import importlib.util
spec = importlib.util.spec_from_file_location("na", "15_new_account.py")
na = importlib.util.module_from_spec(spec); spec.loader.exec_module(na)
for m in na.DEVICE_MODEL_POOL:
    ids = na.generate_device_ids(time_zone="+00:00", model_name=m["model"])
    assert ids["model"] == m["model"]
    assert ids["user_agent"] == m["user_agent"]
    assert m["model"] in ids["user_agent"] or m["model"].split()[0] in ids["user_agent"]
print("all pool models generate OK, n=", len(na.DEVICE_MODEL_POOL))
