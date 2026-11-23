# -*- coding: utf-8 -*-
"""batch_runner.py: several castles in parallel, each = its own new_castle_full.py process + its own tunnel lease.
  python batch_runner.py --world 837 --alliance 3cy --count 3 --parallel 3 --mode prep [--calm 1.5] [--live]
  python batch_runner.py --batches "837:3cy:15:15:prep,838:abc:15:15:full" [--live]   (world:alliance:count:parallel:mode)
Per castle: own tunnel/exit (never shared while active, lifetime limit via exit_counts.json - live only),
own device profile/session/seq/logs (logs/batch_<ts>/castle_<k>.log), random staggered start (30-120 s after the
previous start in the same batch), independent jitter, alliance joins spaced by alliance_gate (shared lock file).
Fail-closed: no tunnel -> castle not started; tunnel dies -> castle stopped (resume later), never rerouted.
Stop: logs/panel_stop.flag. Status: logs/batch_<ts>/status.json (castles shown only as 'castle #k')."""
import argparse, os, random, re, subprocess, sys, threading, time
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__)); os.chdir(BASE); sys.path.insert(0, BASE)
import tunnel_pool
from multilock import jsave
STOPF = os.path.join(BASE, "logs", "panel_stop.flag")
ap = argparse.ArgumentParser()
ap.add_argument("--world", type=int); ap.add_argument("--alliance"); ap.add_argument("--count", type=int, default=3)
ap.add_argument("--parallel", type=int, default=3); ap.add_argument("--mode", choices=["full", "prep"], default="prep")
ap.add_argument("--batches", default=None); ap.add_argument("--calm", type=float, default=1.0)
ap.add_argument("--live", action="store_true")
ap.add_argument("--stagger-min", type=float, default=30); ap.add_argument("--stagger-max", type=float, default=120)
ap.add_argument("--gate-min", type=float, default=60); ap.add_argument("--gate-max", type=float, default=90)
ap.add_argument("--dry-delay", type=float, default=0.05)
ap.add_argument("--max-parallel-total", type=int, default=30)
a = ap.parse_args()
if a.live and (a.gate_min < 30 or a.stagger_min < 10): raise SystemExit("STOP: live needs gate-min >= 30 and stagger-min >= 10")
specs = []
if a.batches:
    for part in a.batches.split(","):
        w, al, c, k, m = part.strip().split(":"); specs.append((int(w), al, int(c), int(k), m))
else:
    if a.world is None or not a.alliance: raise SystemExit("need --world/--alliance or --batches")
    specs.append((a.world, a.alliance, a.count, a.parallel, a.mode))
for w, al, c, k, m in specs:
    if not re.fullmatch(r"[A-Za-z0-9_]{2,8}", al) or m not in ("full", "prep") or not (1 <= c <= 1000 and 1 <= k <= 30): raise SystemExit(f"STOP: bad batch {w}:{al}")
TS = datetime.now().strftime("%Y%m%d_%H%M%S"); OUT = os.path.join(BASE, "logs", f"batch_{TS}_{os.getpid()}"); os.makedirs(OUT, exist_ok=True)
MLOG = os.path.join(OUT, "batch.log"); lk = threading.Lock(); TOTAL = threading.Semaphore(a.max_parallel_total)
status = {"live": a.live, "started": TS, "batches": [], "castles": {}}

def mask(t):
    t = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b", "<ip>", t); t = re.sub(r"\b\d{7,}\b", "#", t)
    t = re.sub(r"(?i)(token|key|fpid|uid|connid|finger\w*|auth\w*)([\"'=:\s]+)[^\s,\"'}]+", r"\1\2***", t)
    return re.sub(r"\b[A-Za-z0-9_\-]{24,}\b", "***", t)
def log(m):
    line = f"{datetime.now():%H:%M:%S.%f}"[:-3] + " " + mask(m)
    with lk: print(line, flush=True); open(MLOG, "a", encoding="utf-8").write(line + "\n")
def setst(tag, **kw):
    with lk: status["castles"].setdefault(tag, {}).update(kw); jsave(os.path.join(OUT, "status.json"), status)

def worker(bi, k, tag, w, al, mode, start_at, sem):
    setst(tag, batch=bi, n=k, kingdom=w, alliance=al, stage="queued", idx="", t0=None)
    while time.time() < start_at:
        if os.path.exists(STOPF): setst(tag, stage="cancelled (stop)"); return
        time.sleep(0.2)
    with sem, TOTAL:
        if os.path.exists(STOPF): setst(tag, stage="cancelled (stop)"); return
        setst(tag, stage="tunnel")
        try: L = tunnel_pool.lease(owner=tag, live=a.live, log=lambda m: log(f"{tag} {m}"))
        except Exception as e: log(f"{tag}: STOP no tunnel ({e}) - castle not started"); setst(tag, stage="no tunnel"); return
        setst(tag, stage="running", cc=L["cc"], t0=time.time())
        cmd = [sys.executable, "new_castle_full.py", "--live" if a.live else "--dry-run", "--world", str(w), "--alliance", al,
               "--proxy", L["proxy"], "--mode", mode, "--calm", str(a.calm), "--tag", tag, "--dry-delay", str(a.dry_delay)]
        env = {k_: v for k_, v in os.environ.items() if k_ != "RG_OFFLINE"}
        env.update(PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", CASTLE_TAG=tag, CASTLE_LOGDIR=os.path.join(OUT, tag),
                   GATE_GAP_MIN=str(a.gate_min), GATE_GAP_MAX=str(a.gate_max))
        if not a.live: env["RG_OFFLINE"] = "1"
        log(f"{tag}: start kingdom {w} alliance {al} mode {mode} via tunnel cc={L['cc']} exit={L['exit_hash']}")
        p = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        dead = [False]
        def watch():                       # tunnel died -> stop this castle, no reroute
            while p.poll() is None:
                time.sleep(3)
                if p.poll() is None and not tunnel_pool.alive(L["port"]):
                    dead[0] = True; log(f"{tag}: TUNNEL DIED - stopping castle (resume later)")
                    subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True); return
        threading.Thread(target=watch, daemon=True).start()
        with open(os.path.join(OUT, f"castle_{tag}.log"), "w", encoding="utf-8") as cf:
            for line in p.stdout:
                line = mask(line.rstrip()); cf.write(f"{time.time():.3f} {line}\n"); cf.flush()
                m = re.search(r"idx ([\d.]+):.*ok:1", line)
                if m: setst(tag, idx=m.group(1))
                if "[gate]" in line: log(f"{tag} {line.strip()}")
        rc = p.wait(); tunnel_pool.release(L["port"], log=lambda m: log(f"{tag} {m}"))
        st = "done" if rc == 0 else ("tunnel died - stopped" if dead[0] else ("stopped (panel)" if rc == 3 else f"stop (code {rc})"))
        setst(tag, stage=st, rc=rc, t=round(time.time() - status["castles"][tag]["t0"])); log(f"{tag}: {st}")

threads = []; T0 = time.time()
log(f"{'LIVE' if a.live else 'DRY-RUN'} batches: " + "; ".join(f"#{i+1} kingdom {w} alliance {al} x{c} parallel {k} {m}" for i, (w, al, c, k, m) in enumerate(specs)))
log(f"stagger {a.stagger_min}-{a.stagger_max} s, alliance gate {a.gate_min}-{a.gate_max} s, calm {a.calm}")
for bi, (w, al, c, k, m) in enumerate(specs, 1):
    status["batches"].append({"b": bi, "kingdom": w, "alliance": al, "count": c, "parallel": k, "mode": m})
    sem = threading.Semaphore(k); t = T0 + random.uniform(0, a.stagger_min)   # batches start offset too
    for n in range(1, c + 1):
        tag = f"b{bi}c{n}"
        th = threading.Thread(target=worker, args=(bi, n, tag, w, al, m, t, sem), daemon=True); th.start(); threads.append(th)
        t += random.uniform(a.stagger_min, a.stagger_max)
try:
    for th in threads:
        while th.is_alive(): th.join(1)
except KeyboardInterrupt:
    open(STOPF, "w").write("stop"); log("Ctrl+C -> stop flag")
    for th in threads: th.join(30)
res = {}
for v in status["castles"].values(): res[v["stage"]] = res.get(v["stage"], 0) + 1
log(f"BATCH END {time.time() - T0:.0f} s: {res}  logs: {os.path.relpath(OUT, BASE)}")
sys.exit(0 if set(res) == {"done"} else 1)
