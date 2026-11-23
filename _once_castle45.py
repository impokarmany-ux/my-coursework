# -*- coding: utf-8 -*-
# разовая попытка бесплатного 4->5 (instant true gold 0), затем при успехе можно --from 24
import sys, os, json, time, importlib.util
sys.stdout.reconfigure(encoding="utf-8")
if not getattr(__import__("requests").Session.request, "__name__", "") == "_forced":
    raise SystemExit("СТОП: только через run_guarded")
BAD = "203.0.113.10"
UID = 98570606
B = r"E:\protocol_analysis\capture"
MITM = os.path.join(B, "mitm")
s = importlib.util.spec_from_file_location("sc", os.path.join(B, "10_send_cmd.py"))
sc = importlib.util.module_from_spec(s); s.loader.exec_module(sc)
bd = json.load(open(os.path.join(MITM, f"session_bundle_{UID}.json"), encoding="utf-8"))
assert int(bd["uid"]) == UID
KEY = bytes.fromhex(bd["aes_key_hex"])
seq = int(bd.get("seq_next") or 1)
import requests
ip = requests.Session().get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
if not ip or ip == BAD:
    raise SystemExit("СТОП: домашний IP или пусто")
print("ip_ok seq", seq)

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)

def send(op, args):
    global seq
    if isinstance(args, dict) and args.get("gold", 0) != 0:
        raise SystemExit("СТОП: gold != 0")
    env = sc.build_commit_envelope(op, bd["session_key"], bd["token"], args, fpid=str(bd["fpid"]), seq=seq)
    used = seq; seq += 1; bd["seq_next"] = seq
    json.dump(bd, open(os.path.join(MITM, f"session_bundle_{UID}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    p, raw, meta = sc.send_command(KEY, env)
    open(os.path.join(B, "logs", "castle45_try.jsonl"), "a", encoding="utf-8").write(
        json.dumps({"seq": used, "op": op, "resp": p}, ensure_ascii=False) + "\n")
    if not p or p.get("ok") != 1:
        raise SystemExit(f"СТОП: {op} seq={used} http={meta.get('http_status')} ответ={json.dumps(p, ensure_ascii=False)[:600]}")
    golds = [d.get("gold") for d in walk(p) if isinstance(d.get("gold"), (int, float))]
    print("gold_seen", golds[:5])
    if golds and any(g < 0 for g in golds):
        raise SystemExit("СТОП: странное золото")
    # track building 1
    for d in walk(p):
        if d.get("building_id") == 1 and "level" in d:
            print("castle_level", d["level"])
    return p

# 1) instant true
print("try instant true 4->5")
p = send("City:upgradeObject", {"gold": 0, "city_id": UID, "instant": True, "auto": False, "building_id": 1})
print("done", json.dumps(p, ensure_ascii=False)[:400])
print("seq_next", seq)
