# -*- coding: utf-8 -*-
"""castle_relogin.py - fresh login into an archived castle from its saved data (castles/NNNN).
UNTESTED LIVE. Sequence copies the re-login that 15_new_account.py does after creation (step 5):
gateway hello+ping -> versionDiff2 -> manifest (ak) -> passport token_login(saved auth) -> call:init kingdom_id=0 (is_new=False).
Writes new session_key/token/seq_next=1 into the castle's working bundle (backup first).
Only via run_guarded.py. Without --live nothing is sent (bodies are built and signed offline)."""
import argparse, json, os, shutil, sys, time, importlib.util
from datetime import datetime
from pathlib import Path
import requests
sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parent
if getattr(requests.Session.request, "__name__", "") != "_forced": raise SystemExit("STOP: only via run_guarded.py")
ap = argparse.ArgumentParser(); ap.add_argument("--castle", type=int, required=True); ap.add_argument("--live", action="store_true")
a = ap.parse_args()
OFFLINE = os.environ.get("RG_OFFLINE") == "1"
LIVE = a.live and not OFFLINE
PROXY = os.environ.get("GOG_GUARDED") or ""
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, BASE / fn); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
na = _load("na15", "15_new_account.py"); lg = na.lg; sc = na.sc
FORBID_UID = (71206420, 98569572, 98570606, 98566384); FORBID_FPID = ("182070973",)

d = BASE / "castles" / f"{a.castle:04d}"
info = json.loads((d / "info.json").read_text(encoding="utf-8"))
acc = json.loads((d / "account.json").read_text(encoding="utf-8"))
bpath = Path(info.get("bundle_src") or d / "bundle.json")
if not bpath.exists(): bpath = d / "bundle.json"
bd = json.loads(bpath.read_text(encoding="utf-8"))
uid = int(bd["uid"]); fpid = str(acc["fpid"])
if uid in FORBID_UID or fpid in FORBID_FPID or str(bd.get("fpid")) != fpid: raise SystemExit("STOP: farm/old castle or mismatched data")
if bpath.name in ("session_bundle_farm.json", "session_bundle_new.json"): raise SystemExit("STOP: protected bundle")
devf = d / "device.json"
if not devf.exists() and acc.get("device_profile"): devf = BASE / "mitm" / Path(acc["device_profile"]).name
if not devf.exists(): raise SystemExit(f"STOP: castle #{a.castle}: no saved device profile - relogin with other ids is risky, not doing it")
device = json.loads(devf.read_text(encoding="utf-8")); device.pop("fpid", None); device.pop("uid", None)
device["guid"] = acc.get("guid") or device.get("guid")
auth = bd.get("session_key") or acc["auth_token"]
print(f"[relogin] castle #{a.castle} kingdom {info.get('kingdom')} status {info.get('status')} mode {'LIVE' if LIVE else 'DRY (nothing sent)'}")

def gateway_open():
    gw = _load("gw17", "17_gateway.py")
    from mitmproxy import io as mio, http as mhttp
    host = port = None
    def find_st(o):
        if isinstance(o, dict):
            if isinstance(o.get("stargate"), dict): return o["stargate"]
            w = o.get("watcher_gate")
            if isinstance(w, dict) and isinstance(w.get("stargate"), dict): return w["stargate"]
            for v in o.values():
                r = find_st(v)
                if r: return r
        elif isinstance(o, list):
            for v in o:
                r = find_st(v)
                if r: return r
    with open(BASE / "mitm" / "flows_newacct.mitm", "rb") as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.response or "gog-global" not in (fl.request.pretty_host or ""): continue
            try: st = find_st(json.loads(fl.response.content.decode("utf-8", "replace")))
            except Exception: continue
            if st and st.get("host") and st.get("port"): host, port = st["host"], int(st["port"]); break
    if not host: raise SystemExit("STOP: no gateway address in mitm")
    sess = gw.GatewaySession(gw.http_connect(PROXY, host, port, timeout=15)); fields = sess.handshake(); sess.start_ping(10.0)
    print("[relogin] gateway hello OK, ping 10s")
    return sess, {"gateway_name": fields["gateway_name"], "gateway_finger_print": str(fields["gateway_finger_print"]), "gateway_connid": str(fields["gateway_connid"])}

net = na.Net(LIVE, PROXY if LIVE else None)
gsess = None; code = 1
try:
    if LIVE:
        if not PROXY: raise SystemExit("STOP: no proxy")
        net.check_ip("before relogin")
        gsess, extra = gateway_open()
    else:
        extra = {"gateway_name": "<dry>", "gateway_finger_print": "0", "gateway_connid": "0"}
    extra.setdefault("time_zone", device.get("time_zone", "+02:00")); extra.setdefault("media_source", device.get("media_source", na.DEFAULT_MEDIA_SOURCE))
    extra.setdefault("push_message", device.get("push_message"))
    for fld in ("gaid", "appsflyer_id", "anon_id"):
        if device.get(fld): extra.setdefault(fld, device[fld])
    device["_init_extra"] = extra
    na.human_sleep(2.0, 4.0, LIVE, "gateway -> versionDiff2")
    na.api_plain(net, {"class": "call", "method": "versionDiff2", "params": {"os": "android", "channel": "google_gog", "version": "14.2.0"}}, "api versionDiff2")
    mj = na.api_plain(net, {"class": "call", "method": "manifest", "req_id": sc.make_req_id(), "params": {
        "client_version": "14.2.0", "client_lang": "ru", "os": "android", "client_full_version": "14.2.0.8514.0",
        "channel": "google_gog", "sys_lang": "ru-RU"}}, "api manifest")
    if LIVE:
        import re
        m = re.search(r'"ak"\s*:\s*"([^"]+)"', json.dumps(mj))
        if not m: raise SystemExit("STOP: no ak in manifest")
        key = sc.unwrap_ak(m.group(1))
    else:
        key = bytes.fromhex(bd["aes_key_hex"])
    print(f"[relogin] ak same as saved: {key.hex() == str(bd['aes_key_hex']).lower()}")
    na.human_sleep(1.0, 2.0, LIVE, "manifest -> token_login")
    tj = na.passport_call(net, device, "token_login", auth_token=auth)
    if LIVE and str(tj["data"].get("fpid")) != fpid: raise SystemExit("STOP: passport returned other fpid")
    auth2 = tj["data"].get("auth_token") or auth
    na.human_sleep(1.0, 2.0, LIVE, "token_login -> init")
    ij = na.api_init(net, key, auth2 if LIVE else auth, fpid, device, 0, is_new=False)
    pay = ij.get("payload") or {}
    if not LIVE:
        print("[relogin] DRY: bundle NOT written; would update session_key, token, seq_next=1, aes_key_hex"); code = 0
    else:
        if int(pay.get("uid") or 0) != uid: raise SystemExit("STOP: uid after relogin differs")
        if not pay.get("token"): raise SystemExit("STOP: no token in init")
        shutil.copy2(bpath, str(bpath) + f".bak_relogin_{int(time.time())}")
        bd.update({"session_key": auth2, "token": pay["token"], "seq_next": 1, "aes_key_hex": key.hex(),
                   "relogin_meta": {"ts": datetime.now().isoformat(timespec="seconds"), "castle": a.castle}})
        bpath.write_text(json.dumps(bd, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[relogin] RELOGIN_OK bundle updated"); code = 0
finally:
    if gsess:
        try: gsess.close(); print("[relogin] gateway closed")
        except Exception as e: print(f"[relogin] gateway close: {type(e).__name__}")
print(f"RELOGIN_RESULT {'OK' if code == 0 else 'FAIL'} BUNDLE {bpath}")
sys.exit(code)
