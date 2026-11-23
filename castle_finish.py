# -*- coding: utf-8 -*-
"""castle_finish.py - finish archived castle9_ready castles: relogin -> loadBaseData (kingdom W, castle 9) ->
16_run_full --from finish_from (search alliance, join, castle 9->10, leave) -> archive castle10.
One castle at a time, random gap between castles (default 60-90 s). DRY-RUN by default, --live required for network.
Stop: logs/panel_stop.flag. Relogin is UNTESTED live."""
import argparse, json, os, random, re, subprocess, sys, time
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE); sys.path.insert(0, BASE)
import castle_archive
STOPF = os.path.join(BASE, "logs", "panel_stop.flag")
ap = argparse.ArgumentParser()
ap.add_argument("--kingdom", type=int, required=True); ap.add_argument("--alliance", required=True); ap.add_argument("--count", type=int, default=1)
ap.add_argument("--gap-min", type=float, default=60); ap.add_argument("--gap-max", type=float, default=90)
ap.add_argument("--proxy", default="http://127.0.0.1:18081"); ap.add_argument("--live", action="store_true")
ap.add_argument("--castle", type=int, default=None, help="only this archive number")
a = ap.parse_args()
if not re.fullmatch(r"[A-Za-z0-9_]{2,8}", a.alliance): raise SystemExit("STOP: odd alliance tag")
LOG = os.path.join(BASE, "logs", f"castle_finish_{datetime.now():%Y%m%d_%H%M%S}_{os.getpid()}.log")
def log(m):
    line = f"{datetime.now():%H:%M:%S} {m}"; print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")
def env(offline):
    e = {k: v for k, v in os.environ.items() if k != "RG_OFFLINE"}; e["PYTHONIOENCODING"] = "utf-8"; e["PYTHONUNBUFFERED"] = "1"
    if offline: e["RG_OFFLINE"] = "1"
    return e
def stage(name, script, args):
    cmd = [sys.executable, "run_guarded.py", "--proxy", a.proxy, script] + args
    log(f"[{name}] start {script}"); out = []
    p = subprocess.Popen(cmd, env=env(not a.live), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for line in p.stdout:
        out.append(line)
        if name == "run" or "STOP" in line or "СТОП" in line or "RESULT" in line or "Traceback" in line: print("   " + line.rstrip(), flush=True)
    rc = p.wait(); log(f"[{name}] code {rc}"); return rc, "".join(out)

pool = castle_archive.ready(a.kingdom)
if a.castle: pool = [r for r in pool if r["n"] == a.castle]
pick = pool[:a.count]
log(f"{'LIVE' if a.live else 'DRY-RUN (nothing sent)'}: kingdom {a.kingdom}, alliance {a.alliance}, ready {len(pool)}, taking {len(pick)}, gap {a.gap_min}-{a.gap_max} s")
if not pick: log("no castle9_ready castles in this kingdom"); sys.exit(4 if a.live else 0)
done = 0
for i, r in enumerate(pick):
    if os.path.exists(STOPF): log("STOP: panel stop"); sys.exit(3)
    if i:
        g = random.uniform(a.gap_min, a.gap_max); log(f"gap before next castle {g:.0f} s" + ("" if a.live else " (dry: not waiting)"))
        if a.live:
            t = time.time()
            while time.time() - t < g:
                if os.path.exists(STOPF): log("STOP: panel stop"); sys.exit(3)
                time.sleep(1)
    n = r["n"]; ff = r.get("finish_from") or 114.9; T0 = time.time()
    log(f"castle #{n}: finish from idx {ff}")
    rc, out = stage("relogin", "castle_relogin.py", ["--castle", str(n)] + (["--live"] if a.live else []))
    m = re.search(r"RELOGIN_RESULT OK BUNDLE (.+)", out)
    if rc != 0 or not m: log(f"STOP: castle #{n} relogin failed - status unchanged"); sys.exit(2)
    bundle = m.group(1).strip()
    if a.live:
        rc, out = stage("state", "16_state_new.py", [bundle, str(a.kingdom)])
        lvl = re.search(r"castle_level (\d+)", out)
        if rc != 0 or "RESULT_OK True" not in out: log(f"STOP: castle #{n} kingdom not {a.kingdom} or loadBaseData error"); sys.exit(2)
        if not lvl or int(lvl.group(1)) != 9: log(f"STOP: castle #{n} level {lvl.group(1) if lvl else '?'} != 9"); sys.exit(2)
        rc, out = stage("run", "16_run_full.py", ["--bundle", bundle, "--alliance", a.alliance, "--world", str(a.kingdom), "--from", str(ff)])
        mf = re.search(r"--from ([\d.]+)", out)
        castle_archive.save(bundle, a.kingdom, a.alliance, "castle10" if rc == 0 else "finish_failed",
                            {"finish_rc": rc, "finish_s": round(time.time() - T0), "finish_from": ff, "resume_from": float(mf.group(1)) if (rc and mf) else None})
        if rc != 0: log(f"STOP: castle #{n} finish code {rc}" + (f", resume --from {mf.group(1)}" if mf else "")); sys.exit(rc)
    else:
        log("[state] dry: skipped (needs network); live checks kingdom and castle_level == 9")
        rc, out = stage("run", "16_run_full.py", ["--bundle", bundle, "--alliance", a.alliance, "--world", str(a.kingdom), "--from", str(ff), "--list-steps"])
        if rc != 0: log(f"STOP: dry list failed {rc}"); sys.exit(rc)
        import alliance_gate; w = alliance_gate.acquire(f"{a.kingdom}:{a.alliance.lower()}", who=f"finish{n}", log=log)
        log(f"[gate] dry: join slot after {w:.1f} s (live: gate sits inside 16_run_full before joinAlliance)")
        log(f"[archive] dry: would set castle #{n} -> castle10")
    done += 1; log(f"castle #{n}: done in {time.time() - T0:.0f} s")
log(f"DONE: {done}/{len(pick)}")
