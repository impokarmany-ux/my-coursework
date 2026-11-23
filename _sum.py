import re,json
from pathlib import Path
t=Path("logs/castle_own_ids_console.txt").read_text(encoding="utf-8",errors="replace")
for l in t.splitlines():
    if re.search(r'STOP|\[ids\]|\[tz\]|\[ip\]|   -> |записан|hello|closed|15_new_account|FAIL|exit IP',l):
        l=re.sub(r'[0-9a-fA-F]{12,}','…',l); l=re.sub(r'\d{6,}','#',l); print(l[:220])
for pat in ["mitm/session_bundle_*.json","logs/init_resp_*.json","logs/castle_gw_*.log","mitm/device_2026*.json"]:
    fs=sorted(Path().glob(pat),key=lambda p:p.stat().st_mtime)[-2:]
    print(pat,[f.name if not f.name.startswith("session_bundle") else "session_bundle_<uid>.json" for f in fs])
for f in sorted(Path("logs").glob("init_resp_*.json"))[-2:]:
    print(f.name, json.loads(f.read_text(encoding="utf-8"))["kingdom_fields"], json.loads(f.read_text(encoding="utf-8"))["ok"])
