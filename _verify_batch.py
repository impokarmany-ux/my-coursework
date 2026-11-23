import glob, json, os, sys
d = sorted(glob.glob("logs/batch_*"), key=os.path.getmtime)[-1]
for f in sorted(glob.glob(d + "/*/*_seq.jsonl")):
    R = [json.loads(l) for l in open(f)]
    ok = all(r["seq"] == i + 1 for i, r in enumerate(R)) and all(r["t_send"] >= r["prev_ack"] for r in R) and len({r["tag"] for r in R}) == 1
    print(R[0]["tag"], "steps", len(R), "seq 1..%d" % R[-1]["seq"], "ordered+send-after-ack:", ok, "first send %.1f" % R[0]["t_send"])
G = [json.loads(l) for l in open("logs/alliance_gate_log.jsonl")][-int(sys.argv[1]):]
by = {}
for g in G: by.setdefault(g["key"], []).append(g)
for k, v in by.items():
    print(k, [g["who"] for g in v], "gaps s:", [round(b["t"] - a["t"], 1) for a, b in zip(v, v[1:])], "required:", [a["next_gap"] for a in v[:-1]])
print("own dirs:", sorted(os.listdir(d)))
