import json,re,glob
L=[json.loads(l) for l in open(glob.glob("logs/run_full_*_231212_resp.jsonl")[0],encoding="utf-8")]
def red(s): return re.sub(r'\d{8,}','#',s)
for r in L:
    if r["seq"] in (22,25,26,27,13): print(r["seq"],r["op"],red(json.dumps(r["resp"],ensure_ascii=False))[:1500]); print()
