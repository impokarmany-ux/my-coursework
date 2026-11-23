from pathlib import Path
p = Path("16_run_full.py")
t = p.read_text(encoding="utf-8-sig")

# 1) seed from current UID state
old_seed = 'st0 = json.load(open(os.path.join(BASE, "logs", "state_98569572.json"), encoding="utf-8"))'
new_seed = 'st0 = json.load(open(os.path.join(BASE, "logs", f"state_{UID}.json"), encoding="utf-8"))'
if old_seed in t:
    t = t.replace(old_seed, new_seed, 1)
    print("seed -> state_UID")
elif f"state_{{UID}}.json" in t or 'f"state_{UID}.json"' in t:
    print("seed already UID")
else:
    raise SystemExit("seed line not found")

# 2) move drawFree level check BEFORE send — insert before wait_gap/send for that op
# Remove post-send guard (keep legend validation)
old_post = '''        if op == "Legend2:drawFreeLegend":
            cur_c = city.get("1", {}).get("level")
            if cur_c is None or cur_c < 5:
                raise SystemExit(f"СТОП: drawFreeLegend только при замке 5 (сейчас {cur_c}) — дождись таймера 4→5 и --from {s['idx']}")
            ls = sorted({d.get("legend_id") for d in walk(p.get("data")) if d.get("legend_id")})'''
new_post = '''        if op == "Legend2:drawFreeLegend":
            ls = sorted({d.get("legend_id") for d in walk(p.get("data")) if d.get("legend_id")})'''
if old_post in t:
    t = t.replace(old_post, new_post, 1)
    print("removed post-send guard")
else:
    print("post-send guard already clean or missing")

# Insert pre-send check just before wait_gap(s)
anchor = "        wait_gap(s)\n        if op == \"City:addObject\": args[\"building_id\"] = int(time.time())"
pre = '''        if op == "Legend2:drawFreeLegend":
            cur_c = city.get("1", {}).get("level")
            if cur_c is None or int(cur_c) < 5:
                raise SystemExit(f"СТОП: drawFreeLegend только при замке 5 (сейчас {cur_c}) — дождись таймера 4→5 и --from {s['idx']}")
        wait_gap(s)
        if op == "City:addObject": args["building_id"] = int(time.time())'''
if "drawFreeLegend только при замке 5" in t and "wait_gap(s)" in t[t.find("Legend2:drawFreeLegend"):t.find("Legend2:drawFreeLegend")+200]:
    # check if pre already exists
    pass
if pre.split("wait_gap")[0] in t:
    print("pre-send already present")
elif anchor in t:
    t = t.replace(anchor, pre, 1)
    print("inserted pre-send guard")
else:
    raise SystemExit("anchor missing")

p.write_text(t, encoding="utf-8")
print("ok city seed level", end=" ")
import json
st=json.load(open("logs/state_98570606.json",encoding="utf-8"))
for c in st["data"]["city_map"]:
    if c["building_id"]==1:
        print(c["level"])
