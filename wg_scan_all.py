# wg_scan_all.py: check every Surfshark config via wireproxy on 127.0.0.1:18092 (no game traffic)
import os, re, glob, json, socket, subprocess, time, statistics, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import wg_check
EXE = os.path.join(BASE, "wg", "bin", "wireproxy.exe")
PORT = 18092
PROXY = "http://127.0.0.1:%d" % PORT
TMP = os.path.join(BASE, "wg", "_scan_wireproxy.conf")
OUT = os.path.join(BASE, "logs", "wg_scan.json")
FIX = {"UK": "GB"}
def listening():
    s = socket.socket(); s.settimeout(1)
    try: s.connect(("127.0.0.1", PORT)); return True
    except OSError: return False
    finally: s.close()
res = json.load(open(OUT)) if len(sys.argv) > 1 else {}
confs = sorted(f for f in glob.glob(os.path.join(BASE, "wg", "*.conf")) if not os.path.basename(f).startswith(("wireproxy", "_scan")))
if len(sys.argv) > 1: confs = [f for f in confs if res.get(os.path.basename(f)[:-5], {}).get('status') == 'FAIL']
for i, f in enumerate(confs, 1):
    name = os.path.basename(f)[:-5]
    want = FIX.get(name.split("-")[0].upper(), name.split("-")[0].upper())
    t = open(f, encoding="utf-8", errors="ignore").read()
    host = re.search(r"Endpoint\s*=\s*([^:\s]+)", t).group(1)
    try: eps = sorted({a[4][0] for a in socket.getaddrinfo(host, 51820, socket.AF_INET)})
    except Exception: eps = []
    r = {"want": want, "endpoints": eps, "n_endpoints": len(eps)}
    open(TMP, "w").write("WGConfig = %s\n\n[http]\nBindAddress = 127.0.0.1:%d\n" % (f, PORT))
    p = subprocess.Popen([EXE, "-c", TMP], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, creationflags=0x08000000)
    try:
        for _ in range(20):
            if listening(): break
            time.sleep(0.5)
        time.sleep(1.5)
        ts = []; ip = cc = None
        for k in range(3):
            try:
                ip, cc, dt = wg_check.probe(PROXY, timeout=12); ts.append(dt)
            except Exception:
                if k == 0: break
        if not ts:
            r["status"] = "FAIL"
        elif ip == wg_check.HOME_IP:
            r["status"] = "HOME"
        else:
            r.update(status="OK" if cc == want else "MISMATCH", cc=cc, exit_hash=wg_check.exit_hash(ip), t=round(statistics.median(ts), 2))
    finally:
        p.kill(); p.wait()
    res[name] = r
    print("%3d/%d %-8s %-8s %s %s" % (i, len(confs), name, r["status"], r.get("cc", ""), r.get("t", "")), flush=True)
    json.dump(res, open(OUT, "w"), indent=1)
try: os.remove(TMP)
except OSError: pass
ok = [v for v in res.values() if v["status"] == "OK"]
print("DONE total=%d ok=%d fail=%d mismatch=%d home=%d distinct_exits=%d endpoints_total=%d" % (
    len(res), len(ok), sum(v["status"] == "FAIL" for v in res.values()), sum(v["status"] == "MISMATCH" for v in res.values()),
    sum(v["status"] == "HOME" for v in res.values()), len({v["exit_hash"] for v in ok}), sum(v["n_endpoints"] for v in res.values())))
