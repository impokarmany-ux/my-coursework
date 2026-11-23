# -*- coding: utf-8 -*-
import sys, os, json, time, importlib.util, re
sys.stdout.reconfigure(encoding="utf-8")
if not getattr(__import__("requests").Session.request, "__name__", "") == "_forced":
    raise SystemExit("СТОП: только через run_guarded")
BAD = "203.0.113.10"; UID = 98570606
B = r"E:\protocol_analysis\capture"; MITM = os.path.join(B, "mitm")
s = importlib.util.spec_from_file_location("sc", os.path.join(B, "10_send_cmd.py"))
sc = importlib.util.module_from_spec(s); s.loader.exec_module(sc)
bd = json.load(open(os.path.join(MITM, f"session_bundle_{UID}.json"), encoding="utf-8"))
assert int(bd["uid"]) == UID
KEY = bytes.fromhex(bd["aes_key_hex"]); seq = int(bd.get("seq_next") or 1)
import requests
ip = requests.Session().get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
if not ip or ip == BAD: raise SystemExit("СТОП: домашний IP")
print("ip_ok seq", seq)

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

gold0 = None
def send(op, args):
    global seq, gold0
    if isinstance(args, dict) and args.get("gold", 0) != 0:
        raise SystemExit("СТОП: gold != 0")
    env = sc.build_commit_envelope(op, bd["session_key"], bd["token"], args, fpid=str(bd["fpid"]), seq=seq)
    used = seq; seq += 1; bd["seq_next"] = seq
    json.dump(bd, open(os.path.join(MITM, f"session_bundle_{UID}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    p, raw, meta = sc.send_command(KEY, env)
    open(os.path.join(B, "logs", "castle45_try.jsonl"), "a", encoding="utf-8").write(
        json.dumps({"seq": used, "op": op, "args": args, "resp": p}, ensure_ascii=False) + "\n")
    print(f"seq={used} {op} http={meta.get('http_status')} ok={(p or {}).get('ok')}")
    if not p or p.get("ok") != 1:
        raise SystemExit(f"СТОП: {op} seq={used} ответ={json.dumps(p, ensure_ascii=False)[:700]}")
    for d in walk(p):
        if isinstance(d.get("gold"), (int, float)):
            if gold0 is None: gold0 = d["gold"]
            elif d["gold"] < gold0:
                raise SystemExit(f"СТОП: золото {gold0}->{d['gold']}")
            gold0 = d["gold"]
        if d.get("building_id") == 1 and "level" in d and d.get("city_id") in (None, UID, str(UID)):
            print("  b1 level", d["level"], "city", d.get("city_id"))
    return p

p = send("City:upgradeObject", {"gold": 0, "city_id": UID, "instant": False, "auto": False, "building_id": 1})
# dump jobs
t = json.dumps(p, ensure_ascii=False)
open(os.path.join(B, "logs", "castle45_upgrade_resp.json"), "w", encoding="utf-8").write(t)
jobs = [d for d in walk(p) if d.get("event_type") == 30 and d.get("job_id")]
print("jobs30", json.dumps(jobs, ensure_ascii=False)[:800])
# any job with building 1
jobs2 = [d for d in walk(p) if d.get("job_id") and d.get("building_id") == 1]
print("jobs_b1", json.dumps(jobs2, ensure_ascii=False)[:800])
print("gold", gold0, "seq_next", seq)
