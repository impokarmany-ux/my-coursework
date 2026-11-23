import json,sys
sys.stdout.reconfigure(encoding="utf-8")
# ищем в commits апгрейд замка около стража / 4->5
commits=json.load(open("logs/all_commits.json",encoding="utf-8"))
print("n",len(commits))
# структура
c0=commits[0]
print("keys",c0.keys() if isinstance(c0,dict) else type(c0))
# найти drawFree и соседние upgradeObject building 1
hits=[]
for i,c in enumerate(commits):
    op=c.get("op") or c.get("cmd") or ""
    if "drawFree" in str(op) or ("upgradeObject" in str(op) and ("building_id" in str(c.get("args") or c.get("params") or {}) and (c.get("args") or c.get("params") or {}).get("building_id")==1)):
        hits.append(i)
print("hit idxs sample",hits[:30],"... total",len(hits))
for i in hits[:15]:
    c=commits[i]
    print(i, c.get("op") or c.get("cmd"), json.dumps(c.get("args") or c.get("params") or {},ensure_ascii=False)[:200])
# поиск free instant / 4-5 в тексте файлов
