# -*- coding: utf-8 -*-
# 16_state.py — только чтение Player:loadBaseData для uid 98569572 (запуск строго через run_guarded.py)
import sys, json, importlib.util, re
sys.stdout.reconfigure(encoding="utf-8")
B = r"E:\protocol_analysis\capture"
s = importlib.util.spec_from_file_location("sc", B + r"\10_send_cmd.py"); sc = importlib.util.module_from_spec(s); s.loader.exec_module(sc)
bd = json.load(open(B + r"\mitm\session_bundle_98569572.json", encoding="utf-8"))
assert int(bd["uid"]) == 98569572
key = bytes.fromhex(bd["aes_key_hex"])
p, raw, meta = sc.send_command(key, sc.build_envelope("Player", "loadBaseData", bd["session_key"], bd["token"]))
open(B + r"\logs\state_98569572.json", "w", encoding="utf-8").write(json.dumps(p, ensure_ascii=False))
print("http", meta.get("http_status"), "ok", (p or {}).get("ok"))
t = json.dumps(p, ensure_ascii=False)
for k in ("world_id", "kingdom_id", "server_id", "kingdom", "gold", "level"):
    print(k, sorted(set(re.findall(r'"%s":\s*("?[\w.-]+"?)' % k, t)))[:10])
