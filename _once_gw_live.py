# -*- coding: utf-8 -*-
"""Один тестовый коннект к шлюзу. Запуск только через run_guarded. Не повторять."""
from __future__ import annotations
import importlib.util, json, sys, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
PROXY = "http://127.0.0.1:18081"
BAD = "203.0.113.10"
TZ = ZoneInfo("Europe/Kiev")

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, BASE / fn)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

# только через run_guarded
import requests
if getattr(requests.Session.request, "__name__", "") != "_forced":
    raise SystemExit("СТОП: только через run_guarded.py")

gw = _load("gw17", "17_gateway.py")
log_path = BASE / "logs" / f"gateway_live_{datetime.now(TZ):%Y%m%d_%H%M%S}.log"
log_path.parent.mkdir(exist_ok=True)
logf = open(log_path, "w", encoding="utf-8")

def log(msg):
    line = f"[{datetime.now(TZ):%H:%M:%S}] {msg}"
    print(line); logf.write(line + "\n"); logf.flush()

# 1) IP
try:
    s = requests.Session(); s.trust_env = False
    s.proxies = {"http": PROXY, "https": PROXY}
    ip = s.get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
except Exception as e:
    log(f"STOP IP check fail: {type(e).__name__}"); logf.close(); sys.exit(2)
if not ip or ip == BAD:
    log("STOP: выходной IP домашний или пустой"); logf.close(); sys.exit(2)
log("exit IP: NOT home (ok)")

# 2) host/port из mitm (без versionDiff2)
host, port = None, None
try:
    from mitmproxy import io as mio
    from mitmproxy import http as mhttp
    flows_path = BASE / "mitm" / "flows_newacct.mitm"
    with open(flows_path, "rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.response:
                continue
            if "gog-global" not in (fl.request.pretty_host or ""):
                continue
            try:
                body = fl.response.content.decode("utf-8", "replace")
                if "watcher_gate" not in body and "stargate" not in body:
                    continue
                js = json.loads(body)
            except Exception:
                continue
            # ответ может быть обёрткой
            def find_stargate(obj):
                if isinstance(obj, dict):
                    if "stargate" in obj and isinstance(obj["stargate"], dict):
                        return obj["stargate"]
                    wg = obj.get("watcher_gate")
                    if isinstance(wg, dict) and "stargate" in wg:
                        return wg["stargate"]
                    for v in obj.values():
                        r = find_stargate(v)
                        if r: return r
                elif isinstance(obj, list):
                    for v in obj:
                        r = find_stargate(v)
                        if r: return r
                return None
            st = find_stargate(js)
            if st and st.get("host") and st.get("port"):
                host, port = st["host"], int(st["port"])
                break
except Exception as e:
    log(f"mitm parse warn: {type(e).__name__}: {e}")

if not host:
    log("STOP: адрес шлюза в mitm не найден, versionDiff2 не делаем в этом прогоне")
    logf.close(); sys.exit(2)
log(f"stargate host from mitm, port={port} (hostname hidden in report)")

# 3) один CONNECT + handshake + 2 ping
sock = None
sess = None
try:
    log("CONNECT via proxy...")
    sock = gw.http_connect(PROXY, host, port, timeout=15)
    sess = gw.GatewaySession(sock)
    log("waiting hello...")
    fields = sess.handshake()
    log(f"hello OK ServerID={fields['gateway_name']} (ConnID/Fingerprint received, not logged)")
    log("HandshakeOut sent, ack received")
    # 1–2 ping/pong вручную (не фоновый поток надолго)
    for i in range(2):
        sock.sendall(gw.build_ping())
        log(f"ping {i+1} sent")
        try:
            hdr, pay = sess._recv_frame(timeout=8)
            typ = hdr[0]
            log(f"recv type={typ} (2=pong ok)" if typ == 2 else f"recv type={typ} len_pay={len(pay)}")
        except Exception as e:
            log(f"recv after ping failed: {type(e).__name__}")
            break
        time.sleep(1)
    # сохранить поля
    out = {
        "gateway_name": fields["gateway_name"],
        "gateway_finger_print": fields["gateway_finger_print"],
        "gateway_connid": fields["gateway_connid"],
        "ts_europe_kiev": datetime.now(TZ).isoformat(timespec="seconds"),
        "note": "one-shot live test; no init",
    }
    out_path = BASE / "mitm" / f"gateway_fields_{datetime.now(TZ):%Y%m%d_%H%M%S}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"fields saved: {out_path.name}")
    log("PASS")
    code = 0
except Exception as e:
    log(f"FAIL: {type(e).__name__}: {e}")
    code = 1
finally:
    if sess:
        try: sess.close()
        except Exception: pass
    elif sock:
        try: sock.close()
        except Exception: pass
    log("closed")
    logf.close()
sys.exit(code)
