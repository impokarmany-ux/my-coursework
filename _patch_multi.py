import re
def rd(f): return open(f, encoding="utf-8").read()
def wr(f, s): open(f, "w", encoding="utf-8").write(s)
def sub1(s, a, b, f):
    assert s.count(a) >= 1, (f, a[:60]); return s.replace(a, b)

# ---- new_castle_full.py
f = "new_castle_full.py"; s = rd(f)
s = sub1(s, 'ap.add_argument("--dry-delay"', 'ap.add_argument("--tag", default="", help="batch worker tag (logs/seq separate per castle)")\nap.add_argument("--dry-delay"', f)
s = sub1(s, 'LOG = os.path.join(BASE, "logs", f"new_castle_full_{datetime.now():%Y%m%d_%H%M%S}.log")',
 'TAG = re.sub(r"[^A-Za-z0-9_]", "", a.tag) or "solo"\nLOGDIR = os.environ.get("CASTLE_LOGDIR") or os.path.join(BASE, "logs"); os.makedirs(LOGDIR, exist_ok=True)\nLOG = os.path.join(LOGDIR, f"new_castle_full_{datetime.now():%Y%m%d_%H%M%S}_{TAG}_{os.getpid()}.log")\nmport = re.search(r":(\\d+)$", PROXY); PORT = int(mport.group(1)) if mport else None\nGATE_KEY = f"{a.world}:{a.alliance.lower()}"', f)
i = s.index("if not a.live:\n"); j = s.index("sys.exit(r.returncode)", i) + len("sys.exit(r.returncode)")
dry = '''if not a.live:
    import json as _j, random as _r, socket as _s
    rnd = _r.Random(); SEQ = LOG.replace(".log", "_seq.jsonl")
    def tun_ok():
        if not PORT: return True
        k = _s.socket(); k.settimeout(1)
        try: k.connect(("127.0.0.1", PORT)); return True
        except OSError: return False
        finally: k.close()
    log(f"DRY-RUN: nothing is sent. tag {TAG}, mode {a.mode}, world {a.world}, alliance {a.alliance}, tunnel port {PORT}" + (f", calm {a.calm}, to idx {FINISH_FROM}" if a.mode == "prep" else ""))
    for n, s_ in STAGES: log(f"   [{n}] run_guarded.py --proxy <tunnel> " + s_.replace(" W", f" {a.world}").replace(" A ", f" {a.alliance} "))
    if not tun_ok(): log("STOP: tunnel not listening (fail-closed) - castle not started"); sys.exit(2)
    log("[create] dry ok"); time.sleep(a.dry_delay * 3)
    log("[state] dry: RESULT_OK True")
    N = 115 if a.mode == "prep" else 123; seq = 1; last_ack = 0.0
    with open(SEQ, "w", encoding="utf-8") as sf:
        for i in range(N):
            if stopped(): log(f"STOP: panel stop - resume --from {i}"); sys.exit(3)
            if i % 20 == 0 and not tun_ok(): log(f"STOP: tunnel died - resume --from {i} (no other route)"); sys.exit(2)
            if a.mode == "full" and i == 115:
                import alliance_gate; w = alliance_gate.acquire(GATE_KEY, who=TAG, log=log); log(f"[gate] {GATE_KEY}: join slot after {w:.1f} s")
            time.sleep(a.dry_delay * rnd.uniform(0.5, 1.6))            # independent jitter per castle
            t_send = time.time(); time.sleep(rnd.uniform(0.01, 0.04)); t_ack = time.time()   # simulated server answer
            sf.write(_j.dumps({"tag": TAG, "seq": seq, "idx": i, "t_send": t_send, "t_ack": t_ack, "prev_ack": last_ack}) + "\\n"); sf.flush()
            print(f"   idx {i}: (dry) ok:1 seq={seq}", flush=True); seq += 1; last_ack = t_ack
    if a.mode == "prep": log(f"[archive] would mark castle9_ready, finish_from {FINISH_FROM} (dry - not written)")
    r = subprocess.run([sys.executable, "_dry45.py"], env=child_env(True), capture_output=True, text=True, encoding="utf-8")
    for l in r.stdout.splitlines(): log("   " + l)
    log("DONE (dry)"); sys.exit(r.returncode)'''
s = s[:i] + dry + s[j:]
s = sub1(s, '''new = sorted(set(glob.glob("mitm/session_bundle_*.json")) - before, key=os.path.getmtime)
if rc != 0 or len(new) != 1:''', '''# parallel-safe: bundle name comes from THIS castle's create output, not from a folder diff
mb = re.findall(r"session_bundle_\\d+\\.json", out)
new = [os.path.join("mitm", mb[-1])] if mb and os.path.exists(os.path.join("mitm", mb[-1])) else []
if rc != 0 or len(new) != 1:''', f)
s = sub1(s, 'bundle = new[0]; open("_newbundle.txt", "w").write(os.path.abspath(bundle) + "\\n")',
 'bundle = new[0]\nif TAG == "solo": open("_newbundle.txt", "w").write(os.path.abspath(bundle) + "\\n")\nprint("CASTLE_BUNDLE_OK", flush=True)', f)
s = sub1(s, 'with open(LOG.replace(".log", f"_{name}.txt"), "w", encoding="utf-8") as f:', 'with open(LOG.replace(".log", f"_{name}.txt"), "w", encoding="utf-8") as f:', f)
wr(f, s)

# ---- _once_castle_gw.py
f = "_once_castle_gw.py"; s = rd(f)
s = sub1(s, 'import importlib.util, json, runpy, sys, threading, time', 'import importlib.util, json, os, runpy, sys, threading, time', f)
s = sub1(s, 'PROXY = "http://127.0.0.1:18081"', '# proxy = the one run_guarded forces (per-castle tunnel); no default route\nPROXY = os.environ.get("GOG_GUARDED") or sys.exit("STOP: no GOG_GUARDED proxy (run via run_guarded.py --proxy)")', f)
s = s.replace('%H%M%S}.log"', '%H%M%S}_{os.getpid()}.log"').replace('%H%M%S}.json"', '%H%M%S}_{os.getpid()}.json"')
wr(f, s)

# ---- 16_run_full.py
f = "16_run_full.py"; s = rd(f)
s = sub1(s, 'time.strftime("run_full_%Y%m%d_%H%M%S.log")', 'time.strftime("run_full_%Y%m%d_%H%M%S") + f"_{os.getpid()}.log"', f)
s = sub1(s, '''        wait_gap(s)
        if op == "City:addObject": args["building_id"] = int(time.time())''', '''        if op == "Alliance:joinAlliance":
            # shared gate: no two joins into this alliance closer than the random min gap (all workers/processes)
            import alliance_gate; w = alliance_gate.acquire(f"{a.world}:{a.alliance.lower()}", who=os.environ.get("CASTLE_TAG", ""), log=log)
            log(f"[gate] join slot after {w:.0f} s")
        wait_gap(s)
        if op == "City:addObject": args["building_id"] = int(time.time())''', f)
wr(f, s)

# ---- 15_new_account.py
f = "15_new_account.py"; s = rd(f)
s = sub1(s, 'path = MITM / f"device_{ts}.json"', 'path = MITM / f"device_{ts}_{os.getpid()}.json"  # unique per parallel castle', f)
if not re.search(r"^import .*\bos\b", s, re.M) and "\nimport os" not in s: s = s.replace("\nimport ", "\nimport os\nimport ", 1)
wr(f, s)

# ---- castle_archive.py
f = "castle_archive.py"; s = rd(f)
s = sub1(s, 'def save(bundle, world=None, alliance=None, status="castle10", extra=None):', '''def save(bundle, world=None, alliance=None, status="castle10", extra=None):
    # parallel workers: registry numbering/writes under a cross-process lock
    from multilock import locked
    with locked("archive"): return _save(bundle, world, alliance, status, extra)

def _save(bundle, world=None, alliance=None, status="castle10", extra=None):''', f)
wr(f, s)

# ---- castle_finish.py
f = "castle_finish.py"; s = rd(f)
s = sub1(s, 'f"castle_finish_{datetime.now():%Y%m%d_%H%M%S}.log"', 'f"castle_finish_{datetime.now():%Y%m%d_%H%M%S}_{os.getpid()}.log"', f)
s = sub1(s, '''        log(f"[archive] dry: would set castle #{n} -> castle10")''', '''        import alliance_gate; w = alliance_gate.acquire(f"{a.kingdom}:{a.alliance.lower()}", who=f"finish{n}", log=log)
        log(f"[gate] dry: join slot after {w:.1f} s (live: gate sits inside 16_run_full before joinAlliance)")
        log(f"[archive] dry: would set castle #{n} -> castle10")''', f)
wr(f, s)
print("patched")
