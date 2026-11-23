import json
p="castles/registry.jsonl"; r=[json.loads(l) for l in open(p,encoding="utf-8")]
for x in r:
    if x["n"] in (3,4): x["status"]="castle9_ready"; x["finish_from"]=114.9
open(p,"w",encoding="utf-8").write("".join(json.dumps(x,ensure_ascii=False)+"\n" for x in r))
