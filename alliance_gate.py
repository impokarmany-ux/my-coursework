# -*- coding: utf-8 -*-
"""alliance_gate.py: shared spacing of alliance joins across all workers/processes.
No two joins into the same kingdom:alliance closer than a random gap in [gap_min, gap_max] (default 60-90 s).
Env override: GATE_GAP_MIN / GATE_GAP_MAX (dry-run tests use short gaps). State: logs/alliance_gate.json."""
import json, os, random, time
from multilock import locked, jload, jsave, BASE
STATE = os.path.join(BASE, "logs", "alliance_gate.json"); GLOG = os.path.join(BASE, "logs", "alliance_gate_log.jsonl")
STOPF = os.path.join(BASE, "logs", "panel_stop.flag")

def gaps():
    return float(os.environ.get("GATE_GAP_MIN", 60)), float(os.environ.get("GATE_GAP_MAX", 90))

def acquire(key, gap_min=None, gap_max=None, who="", stopf=STOPF, log=print):
    """Blocks until this worker may join. Returns seconds waited. Raises SystemExit(3) on panel stop."""
    gmin, gmax = gaps()
    gmin = gap_min if gap_min is not None else gmin; gmax = gap_max if gap_max is not None else gmax
    t0 = time.time(); said = False
    while True:
        if stopf and os.path.exists(stopf): raise SystemExit(3)
        with locked("alliance_gate"):
            st = jload(STATE, {}); e = st.get(key) or {}
            ready_at = e.get("last", 0) + e.get("gap", 0); now = time.time()
            if now >= ready_at:
                g = random.uniform(gmin, gmax); st[key] = {"last": now, "gap": g}; jsave(STATE, st)
                open(GLOG, "a", encoding="utf-8").write(json.dumps({"key": key, "who": who, "t": round(now, 3), "next_gap": round(g, 1), "waited": round(now - t0, 1)}) + "\n")
                return now - t0
        if not said: log(f"[gate] {key}: waiting {ready_at - now:.0f} s for alliance-join slot"); said = True
        time.sleep(min(1.0, max(0.05, ready_at - now)))
