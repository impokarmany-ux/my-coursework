# -*- coding: utf-8 -*-
"""Одна проба замка 837 со своим шлюзом. Только через run_guarded. Без повторов."""
from __future__ import annotations
import importlib.util, json, os, runpy, sys, threading, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
# proxy = the one run_guarded forces (per-castle tunnel); no default route
PROXY = os.environ.get("GOG_GUARDED") or sys.exit("STOP: no GOG_GUARDED proxy (run via run_guarded.py --proxy)")
BAD = "203.0.113.10"
TZ = ZoneInfo("Europe/Kiev")
KINGDOM = int(sys.argv[sys.argv.index("--kingdom") + 1]) if "--kingdom" in sys.argv else 837

import requests
if getattr(requests.Session.request, "__name__", "") != "_forced":
    raise SystemExit("СТОП: только через run_guarded.py")

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, BASE / fn)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

gw = _load("gw17", "17_gateway.py")
log_path = BASE / "logs" / f"castle_gw_{datetime.now(TZ):%Y%m%d_%H%M%S}_{os.getpid()}.log"
log_path.parent.mkdir(exist_ok=True)
logf = open(log_path, "w", encoding="utf-8")

def log(msg):
    line = f"[{datetime.now(TZ):%H:%M:%S}] {msg}"
    print(line); logf.write(line + "\n"); logf.flush()

# --- IP ---
try:
    s = requests.Session(); s.trust_env = False
    s.proxies = {"http": PROXY, "https": PROXY}
    ip = s.get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
except Exception as e:
    log(f"STOP IP: {type(e).__name__}"); logf.close(); sys.exit(2)
if not ip or ip == BAD:
    log("STOP: выход домашний или пустой"); logf.close(); sys.exit(2)
log("exit IP: NOT home (ok)")

# --- адрес шлюза из mitm (без versionDiff2) ---
host = port = None
from mitmproxy import io as mio
from mitmproxy import http as mhttp
with open(BASE / "mitm" / "flows_newacct.mitm", "rb") as f:
    for fl in mio.FlowReader(f).stream():
        if not isinstance(fl, mhttp.HTTPFlow) or not fl.response:
            continue
        if "gog-global" not in (fl.request.pretty_host or ""):
            continue
        try:
            js = json.loads(fl.response.content.decode("utf-8", "replace"))
        except Exception:
            continue
        def find_st(o):
            if isinstance(o, dict):
                if isinstance(o.get("stargate"), dict): return o["stargate"]
                wg = o.get("watcher_gate")
                if isinstance(wg, dict) and isinstance(wg.get("stargate"), dict):
                    return wg["stargate"]
                for v in o.values():
                    r = find_st(v)
                    if r: return r
            elif isinstance(o, list):
                for v in o:
                    r = find_st(v)
                    if r: return r
            return None
        st = find_st(js)
        if st and st.get("host") and st.get("port"):
            host, port = st["host"], int(st["port"]); break
if not host:
    log("STOP: нет адреса шлюза в mitm"); logf.close(); sys.exit(2)
log(f"stargate port={port} (host from mitm)")

# --- открыть шлюз и держать ping ---
sock = gw.http_connect(PROXY, host, port, timeout=15)
sess = gw.GatewaySession(sock)
fields = sess.handshake()
log(f"gateway hello OK name={fields['gateway_name']} (conn/fp received)")
sess.start_ping(10.0)
log("ping thread every 10s started; holding during 15_new_account")

# init_extra: ТОЛЬКО gateway_* из живого 17_gateway.
# gaid/appsflyer/anon/push НЕ копируем из init_extra_game.json — их генерит 15_new_account.
# media_source/time_zone — параметры 15 (CLI); здесь не подмешиваем фермовые.
extra = {
    "gateway_name": fields["gateway_name"],
    "gateway_finger_print": str(fields["gateway_finger_print"]),
    "gateway_connid": str(fields["gateway_connid"]),
}
extra_path = BASE / "mitm" / f"init_extra_live_{datetime.now(TZ):%Y%m%d_%H%M%S}_{os.getpid()}.json"
# в файл пишем полные поля (нужны скрипту); в лог — без conn/fp
extra_path.write_text(json.dumps(extra, ensure_ascii=False, indent=2), encoding="utf-8")
log(f"init_extra written {extra_path.name} gateway_name={extra['gateway_name']}")

# также сохранить сырые поля шлюза
(BASE / "mitm" / f"gateway_fields_{datetime.now(TZ):%Y%m%d_%H%M%S}_{os.getpid()}.json").write_text(
    json.dumps({
        "gateway_name": fields["gateway_name"],
        "gateway_finger_print": fields["gateway_finger_print"],
        "gateway_connid": fields["gateway_connid"],
        "ts_europe_kiev": datetime.now(TZ).isoformat(timespec="seconds"),
        "note": "live hold during castle create",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

device = BASE / "mitm" / "device_profile_98566384.json"
code = 1
try:
    argv_15 = [
        str(BASE / "15_new_account.py"),
        "--live",
        "--proxy", PROXY,
        "--kingdom", str(KINGDOM),
        "--device", str(device),
        "--init-extra", str(extra_path),
    ]
    log("starting 15_new_account.py once...")
    # сохранить/подменить argv и выполнить в этом процессе (прокси уже _forced)
    old_argv = sys.argv
    sys.argv = argv_15
    try:
        runpy.run_path(str(BASE / "15_new_account.py"), run_name="__main__")
        code = 0
        log("15_new_account finished OK")
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else (0 if e.code is None else 1)
        log(f"15_new_account SystemExit code={code}")
    finally:
        sys.argv = old_argv
except Exception as e:
    log(f"15 FAIL: {type(e).__name__}: {e}")
    code = 1
finally:
    log("closing gateway...")
    try:
        sess.close()
    except Exception as e:
        log(f"gateway close: {type(e).__name__}")
    log("gateway closed")
    logf.close()

sys.exit(code)
