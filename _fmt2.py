import json,sys,re,collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

# from all_commits and any json with init params
gaids,afs,anons,fpds,toks,medias,tzs=[],[],[],[],[],[],[]
empty_tok=nonempty=0

def harvest(obj, path=""):
    global empty_tok,nonempty
    if isinstance(obj, dict):
        # init-like
        if "appsflyer_id" in obj or "gaid" in obj or "anon_id" in obj:
            if obj.get("gaid"): gaids.append(obj["gaid"])
            if obj.get("appsflyer_id"): afs.append(obj["appsflyer_id"])
            if obj.get("anon_id"): anons.append(obj["anon_id"])
            if obj.get("fp_device_id"): fpds.append(obj["fp_device_id"])
            if obj.get("media_source") is not None: medias.append(obj.get("media_source"))
            if obj.get("time_zone"): tzs.append(obj["time_zone"])
            pm=obj.get("push_message")
            if isinstance(pm,dict) and "device_token" in pm:
                if pm["device_token"]=="": empty_tok+=1
                else: nonempty+=1; toks.append(len(pm["device_token"]))
        for k,v in obj.items():
            harvest(v, path+"/"+str(k))
    elif isinstance(obj, list):
        for i,v in enumerate(obj): harvest(v, path+f"[{i}]")
    elif isinstance(obj, str) and obj.startswith("{") and "appsflyer" in obj:
        try: harvest(json.loads(obj), path+"(json)")
        except: pass

# commits format: list of lists
commits=json.load(open("logs/all_commits.json",encoding="utf-8"))
for c in commits:
    # c[5] is args string often
    for part in c:
        if isinstance(part,str) and ("gaid" in part or "appsflyer" in part or "anon_id" in part or "fp_device" in part):
            try: harvest(json.loads(part))
            except:
                # maybe nested
                for m in re.finditer(r'\{[^{}]*appsflyer_id[^{}]*\}', part):
                    try: harvest(json.loads(m.group(0)))
                    except: pass
                # broader extract
                for key,lst,pat in [
                    ("gaid",gaids,r'"gaid"\s*:\s*"([^"]*)"'),
                    ("af",afs,r'"appsflyer_id"\s*:\s*"([^"]*)"'),
                    ("anon",anons,r'"anon_id"\s*:\s*"([^"]*)"'),
                    ("fpd",fpds,r'"fp_device_id"\s*:\s*"([^"]*)"'),
                    ("ms",medias,r'"media_source"\s*:\s*"([^"]*)"'),
                    ("tz",tzs,r'"time_zone"\s*:\s*"([^"]*)"'),
                ]:
                    for m in re.finditer(pat, part):
                        lst.append(m.group(1))
                for m in re.finditer(r'"device_token"\s*:\s*"([^"]*)"', part):
                    if m.group(1)=="": empty_tok+=1
                    else: nonempty+=1; toks.append(len(m.group(1)))

# also scan init_extra and new_account json and any captured inits
for p in Path("mitm").rglob("*.json"):
    try: harvest(json.loads(p.read_text(encoding="utf-8")))
    except: pass
for p in Path("logs").glob("*.json"):
    try:
        t=p.read_text(encoding="utf-8")
        if "appsflyer" in t or "gaid" in t: harvest(json.loads(t))
    except: pass

print("gaid n",len(gaids),"uniq",len(set(gaids)))
for g in list(dict.fromkeys(gaids))[:6]:
    print(" ",g, "uuid_ok", bool(re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",g,re.I)))
print("af n",len(afs),"uniq",len(set(afs)))
for a in list(dict.fromkeys(afs))[:8]:
    left,right=a.split("-",1) if "-" in a else (a,"")
    print(" ", "L",len(left),"R",len(right),"Ldig",left.isdigit(),"Rdig",right.isdigit(), "sample_L_prefix",left[:4] if left else "")
print("anon n",len(anons),"uniq",len(set(anons)))
for a in list(dict.fromkeys(anons))[:6]:
    print(" ", a[:4], "len",len(a), "match", bool(re.match(r"^XZ[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", a)))
print("fpd n",len(fpds),"uniq",len(set(fpds)))
for f in list(dict.fromkeys(fpds))[:6]:
    print(" ", "len",len(f),"prefix",f[:12],"rest",len(f)-12,"hexrest",all(c in "0123456789abcdef" for c in f[12:].lower()))
print("push empty",empty_tok,"nonempty",nonempty,"tok lens",collections.Counter(toks).most_common(5))
print("media",collections.Counter(medias).most_common(6))
print("tz",collections.Counter(tzs).most_common(10))
