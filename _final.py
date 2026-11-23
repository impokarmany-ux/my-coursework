import json,sys
sys.stdout.reconfigure(encoding="utf-8")
b=json.load(open("mitm/session_bundle_98570606.json",encoding="utf-8"))
print("seq_next", b.get("seq_next"))
# aggregate both runs
ok1=ok2=sent1=sent2=0
# parse logs
for path, label in [("logs/run_full_20261031_221306.log","r1"),("logs/run_full_20261031_222030.log","r2")]:
    lines=open(path,encoding="utf-8").read().splitlines()
    print("---",label, path)
    for line in lines:
        if "отправлено" in line or "ГОТОВО" in line or "СТОП" in line or "замок" in line.lower() or "страж" in line or "золото" in line:
            print(line)
# count ok from resp jsonl
for path in ["logs/run_full_20261031_221306_resp.jsonl","logs/run_full_20261031_222030_resp.jsonl"]:
    n=ok=0
    for line in open(path,encoding="utf-8"):
        o=json.loads(line); n+=1
        if (o.get("resp") or {}).get("ok")==1: ok+=1
    print(path, "cmds", n, "ok1", ok)
# verify castle 10 + not in alliance via state if needed
print("exit_ip_check from logs:")
for path in ["logs/run_full_20261031_221306.log","logs/run_full_20261031_222030.log"]:
    for line in open(path,encoding="utf-8"):
        if "[ip]" in line:
            print(line.strip())
