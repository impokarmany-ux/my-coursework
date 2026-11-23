# -*- coding: utf-8 -*-
# 16_state_new.py — только чтение Player:loadBaseData для нового замка (bundle передаётся аргументом), строго через run_guarded
import sys, json, importlib.util, re, requests
sys.stdout.reconfigure(encoding="utf-8")
B = r"E:\protocol_analysis\capture"
if getattr(requests.Session.request, "__name__", "") != "_forced": raise SystemExit("СТОП: только через run_guarded")
ip = requests.Session().get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
if not ip or ip == "203.0.113.10": raise SystemExit("СТОП: выход домашний/неизвестен")
print("[ip] выход НЕ домашний")
s = importlib.util.spec_from_file_location("sc", B + r"\10_send_cmd.py"); sc = importlib.util.module_from_spec(s); s.loader.exec_module(sc)
bp = sys.argv[1]; bd = json.load(open(bp, encoding="utf-8")); uid = int(bd["uid"])
if uid in (98569572, 98570606, 98566384, 71206420): raise SystemExit("СТОП: прежний замок/ферма")
key = bytes.fromhex(bd["aes_key_hex"])
p, raw, meta = sc.send_command(key, sc.build_envelope("Player", "loadBaseData", bd["session_key"], bd["token"]))
open(B + rf"\logs\state_{uid}.json", "w", encoding="utf-8").write(json.dumps(p, ensure_ascii=False))
print("http", meta.get("http_status"), "ok", (p or {}).get("ok"))
t = json.dumps(p, ensure_ascii=False)
w = sorted(set(re.findall(r'"world_id":\s*"?(\d+)', t)))
print("world_id", w, "gold", sorted(set(re.findall(r'"gold":\s*(\d+)', t)))[:5])
c1 = [c for c in (p.get("data") or {}).get("city_map", []) if str(c.get("building_id")) == "1"]
print("castle_level", c1[0]["level"] if c1 else None)
WANT = sys.argv[2] if len(sys.argv) > 2 else "837"
print("RESULT_837", w == ["837"])
print("RESULT_OK", w == [str(WANT)])
