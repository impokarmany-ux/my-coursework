# -*- coding: utf-8 -*-
"""tunnel_pool.py: pool of wireproxy tunnels, one per castle, ports 18100+ (fail-closed).
lease(owner, live) -> starts a wireproxy on a free port with its own Surfshark config, checks exit
(answers, not home, country known), guarantees: no two active leases on the same exit; exit lifetime
count < limit (logs/exit_counts.json, incremented ONLY when live=True). release(port) kills it.
Never prints IPs: only exit_hash. CLI: up N | list | release PORT | release-all"""
import glob, json, os, random, socket, subprocess, sys, time
from multilock import locked, jload, jsave, BASE
sys.path.insert(0, BASE); import wg_check
EXE = os.path.join(BASE, "wg", "bin", "wireproxy.exe"); RUN = os.path.join(BASE, "wg", "run"); os.makedirs(RUN, exist_ok=True)
LEASES = os.path.join(BASE, "logs", "tunnel_leases.json"); COUNTS = os.path.join(BASE, "logs", "exit_counts.json")
SCAN = os.path.join(BASE, "logs", "wg_scan.json"); PORT0, PORTN = 18100, 18299
URLS = ["https://ipwho.is/", "https://ipinfo.io/json"]

def listening(port):
    s = socket.socket(); s.settimeout(1)
    try: s.connect(("127.0.0.1", port)); return True
    except OSError: return False
    finally: s.close()

def pid_alive(pid):
    if not pid: return False
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
    return str(pid) in r.stdout and "wireproxy" in r.stdout.lower()

def kill(pid):
    if pid: subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)

def probe(proxy, timeout=20):
    """-> (ip, cc, iana_tz, seconds). ip stays in memory only."""
    for u in URLS:
        t0 = time.time()
        r = subprocess.run(["curl.exe", "-s", "-m", str(timeout), "-x", proxy, u], capture_output=True, text=True)
        try: j = json.loads(r.stdout)
        except Exception: continue
        ip = j.get("ip"); cc = j.get("country_code") or j.get("country")
        tz = (j.get("timezone") or {}).get("id") if isinstance(j.get("timezone"), dict) else j.get("timezone")
        if ip and cc: return ip, cc, tz, time.time() - t0
    raise RuntimeError("no answer through tunnel")

def _counts():
    c = jload(COUNTS, {}); c.setdefault("limit_per_exit", 8); c.setdefault("exits", {}); return c

def candidates(max_t=1.0):
    scan = jload(SCAN, {})
    ok = [(v.get("t") or 9, k) for k, v in scan.items() if str(v.get("status")).upper() in ("OK", "MISMATCH") and os.path.exists(os.path.join(BASE, "wg", k + ".conf"))]
    fast = [k for t, k in sorted(ok) if t < max_t]; slow = [k for t, k in sorted(ok) if t >= max_t]
    random.shuffle(fast); random.shuffle(slow)   # not always the same order/countries
    return fast + slow, scan

def lease(owner="?", live=False, exclude_cc=(), max_tries=8, log=print):
    names, scan = candidates()
    tried = 0
    for name in names:
        if tried >= max_tries: break
        with locked("tunnels"):
            L = jload(LEASES, {}); C = _counts(); lim = C["limit_per_exit"]
            used_conf = {v["conf"] for v in L.values()}; used_hash = {v.get("exit_hash") for v in L.values()}
            sh = (scan.get(name) or {}).get("exit_hash")
            if name in used_conf or (sh and (sh in used_hash or C["exits"].get(sh, 0) >= lim)): continue
            if (scan.get(name) or {}).get("cc") in exclude_cc: continue
            port = next((p for p in range(PORT0, PORTN) if str(p) not in L and not listening(p)), None)
            if port is None: raise RuntimeError("no free port")
            L[str(port)] = {"conf": name, "pid": None, "owner": owner, "t": time.time(), "state": "starting"}; jsave(LEASES, L)
        tried += 1
        cfg = os.path.join(RUN, f"wp_{port}.conf")
        open(cfg, "w", encoding="utf-8").write(f"WGConfig = {os.path.join(BASE, 'wg', name + '.conf')}\n\n[http]\nBindAddress = 127.0.0.1:{port}\n")
        lg = open(os.path.join(RUN, f"wp_{port}.log"), "ab")
        p = subprocess.Popen([EXE, "-c", cfg], stdout=lg, stderr=lg, stdin=subprocess.DEVNULL,
                             creationflags=0x00000008 | 0x00000200 | 0x08000000, close_fds=True)
        ok, why = False, ""
        for _ in range(30):
            if listening(port): break
            time.sleep(0.3)
        time.sleep(1.5)
        try:
            ip, cc, tz, dt = probe(f"http://127.0.0.1:{port}")
            if ip == wg_check.HOME_IP: why = "HOME exit"
            else: ok = True
        except Exception as e: why = type(e).__name__
        if ok:
            h = wg_check.exit_hash(ip); del ip
            with locked("tunnels"):
                L = jload(LEASES, {}); C = _counts()
                if any(v.get("exit_hash") == h for k, v in L.items() if k != str(port)): ok, why = False, "exit already in use"
                elif C["exits"].get(h, 0) >= C["limit_per_exit"]: ok, why = False, "exit at limit"
                else:
                    if live: C["exits"][h] = C["exits"].get(h, 0) + 1; jsave(COUNTS, C)
                    L[str(port)] = {"conf": name, "pid": p.pid, "owner": owner, "t": time.time(), "state": "up", "exit_hash": h, "cc": cc, "tz": tz, "lat": round(dt, 2), "live": live}
                    jsave(LEASES, L)
                    log(f"[pool] lease port {port} {name} cc={cc} tz={tz} exit={h} {dt:.2f}s{' count+1' if live else ' (dry: count unchanged)'}")
                    return dict(L[str(port)], port=port, proxy=f"http://127.0.0.1:{port}")
        kill(p.pid)
        with locked("tunnels"):
            L = jload(LEASES, {}); L.pop(str(port), None); jsave(LEASES, L)
        log(f"[pool] {name}: rejected ({why}) - next config")
    raise RuntimeError("no usable tunnel (fail-closed)")

def alive(port):
    e = jload(LEASES, {}).get(str(port))
    return bool(e) and pid_alive(e.get("pid")) and listening(int(port))

def recheck(port):
    """full exit re-check: same exit_hash, not home. False -> caller must stop."""
    e = jload(LEASES, {}).get(str(port))
    if not e: return False
    try: ip, cc, tz, dt = probe(f"http://127.0.0.1:{port}")
    except Exception: return False
    return ip != wg_check.HOME_IP and wg_check.exit_hash(ip) == e.get("exit_hash")

def release(port, log=print):
    with locked("tunnels"):
        L = jload(LEASES, {}); e = L.pop(str(port), None); jsave(LEASES, L)
    if e: kill(e.get("pid")); log(f"[pool] released port {port}")
    for ext in (".conf",):
        try: os.remove(os.path.join(RUN, f"wp_{port}{ext}"))
        except OSError: pass

def release_all(log=print):
    for p in list(jload(LEASES, {})): release(p, log)

if __name__ == "__main__":
    cmd = sys.argv[1:2]
    if cmd == ["up"]:
        got = []
        for i in range(int(sys.argv[2])):
            got.append(lease("cli", live=False, exclude_cc=[g["cc"] for g in got]))
        print("UP", [(g["port"], g["cc"], g["exit_hash"]) for g in got])
    elif cmd == ["list"]:
        for k, v in jload(LEASES, {}).items(): print(k, v.get("conf"), v.get("cc"), v.get("tz"), v.get("exit_hash"), v.get("state"), "alive" if alive(k) else "DEAD")
    elif cmd == ["release"]: release(sys.argv[2])
    elif cmd == ["release-all"]: release_all()
    else: print(__doc__)
