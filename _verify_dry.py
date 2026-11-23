import json, re
from pathlib import Path

log = Path("logs/dryrun_ids_20261031b.txt").read_text(encoding="utf-8")
# ensure no full 32-hex device ids leaked as bare values in B lines after mask
# look for init-check lines
for line in log.splitlines():
    if any(x in line for x in ("[ids]", "[init-check]", "[sign]", "[order]", "DRY-RUN: bundle", "DRY-RUN: профиль", "=== ")):
        print(line)

# compare new profile vs farm template: all id fields different
farm = json.loads(Path("mitm/device_profile_98566384.json").read_text(encoding="utf-8"))
# newest device_*.json
devs = sorted(Path("mitm").glob("device_20*.json"), key=lambda p: p.stat().st_mtime)
print("device profiles:", [p.name for p in devs[-3:]])
new = json.loads(devs[-1].read_text(encoding="utf-8"))
for k in ("device_id","android_id","origin_guid","guid","gaid","appsflyer_id","anon_id","fp_device_id","fp_device_token"):
    same = farm.get(k) == new.get(k)
    print(f"  {k}: len_new={len(str(new.get(k,'')))} differs_from_farm={not same}")
pm = new.get("push_message") or {}
print("  push empty:", pm.get("device_token")=="")
print("  fp_registered:", new.get("fp_registered"))
print("  time_zone:", new.get("time_zone"))
print("  media_source set:", bool(new.get("media_source")))
# UA unchanged?
print("  UA same as template:", new.get("user_agent")==farm.get("user_agent"))
print("  app_id same:", new.get("app_id")==farm.get("app_id"))
# check masked output: B lines should not contain full unmasked 32hex after device_id
bad = 0
for line in log.splitlines():
    if line.strip().startswith("B "):
        # after mask, values look like abcd…(32)
        if re.search(r'"device_id":\s*"[0-9a-f]{32}"', line):
            bad += 1
print("unmasked device_id in B lines:", bad)
