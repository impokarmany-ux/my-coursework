from pathlib import Path
p = Path("16_run_full.py")
t = p.read_text(encoding="utf-8-sig")
needle = '        if op == "Legend2:drawFreeLegend":'
insert = '''        if op == "Legend2:drawFreeLegend":
            cur_c = city.get("1", {}).get("level")
            if cur_c is None or cur_c < 5:
                raise SystemExit(f"СТОП: drawFreeLegend только при замке 5 (сейчас {cur_c}) — дождись таймера 4→5 и --from {s['idx']}")
'''
# avoid double-patch
if "drawFreeLegend только при замке 5" in t:
    print("already patched")
else:
    if needle not in t:
        raise SystemExit("needle missing")
    # replace first occurrence of the drawFree block header with guarded version
    # the old block starts with the needle then ls = sorted...
    old = '''        if op == "Legend2:drawFreeLegend":
            ls = sorted({d.get("legend_id") for d in walk(p.get("data")) if d.get("legend_id")})'''
    new = '''        if op == "Legend2:drawFreeLegend":
            cur_c = city.get("1", {}).get("level")
            if cur_c is None or cur_c < 5:
                raise SystemExit(f"СТОП: drawFreeLegend только при замке 5 (сейчас {cur_c}) — дождись таймера 4→5 и --from {s['idx']}")
            ls = sorted({d.get("legend_id") for d in walk(p.get("data")) if d.get("legend_id")})'''
    if old not in t:
        raise SystemExit("old block missing")
    t = t.replace(old, new, 1)
    # also: after non-instant upgrade, don't trust stale level; set from job next_level-1 still building
    # better: before drawFree, if level from city is 4 but we have no active job, refresh is hard;
    # For resume --from 24, city is empty until first response. Need to seed city from a load or first ops.
    p.write_text(t, encoding="utf-8")
    print("patched guard")

# CRITICAL: --from 24 starts with empty city{} — drawFree guard would see None.
# Seed city from loadBaseData at start, or skip guard when city unknown and let server answer.
# Better: at start after loading bundle, if frm>=24, require optional --assume-castle or do loadBaseData seed.
