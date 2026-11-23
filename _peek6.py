import json,sys
sys.stdout.reconfigure(encoding="utf-8")
commits=json.load(open("logs/all_commits.json",encoding="utf-8"))
print("elem0",commits[0][:3] if isinstance(commits[0],list) else commits[0])
# find format
for i,c in enumerate(commits[:5]):
    print(i, type(c), str(c)[:200])
# search string
raw=json.dumps(commits,ensure_ascii=False)
print("drawFree count", raw.count("drawFreeLegend"))
# find upgrade building 1 near draw
for i,c in enumerate(commits):
    s=json.dumps(c,ensure_ascii=False)
    if "drawFreeLegend" in s:
        print("=== at",i,"===")
        for j in range(max(0,i-5), min(len(commits),i+3)):
            print(j, json.dumps(commits[j],ensure_ascii=False)[:300])
