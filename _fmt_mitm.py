import json,sys,re,collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
from mitmproxy import io as mio
from mitmproxy import http as mhttp

# Collect formats from mitm flows
gaids, afs, anons, fpids_dev, tokens, medias, tzs = [], [], [], [], [], [], []
empty_tok = 0; nonempty_tok = 0
passport_android = []
fp_hosts = collections.Counter()

mitm_files = list(Path("mitm").glob("*.mitm"))[:20]
print("mitm files", len(list(Path("mitm").glob("*.mitm"))))
for mf in Path("mitm").glob("*.mitm"):
    try:
        f=open(mf,"rb")
    except: continue
    try:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow) or not fl.request: continue
            host = fl.request.pretty_host or ""
            path = fl.request.path or ""
            # FunPlus device-ish hosts
            if any(x in host for x in ("funplus","fp-","device","passport","account")):
                if "device" in host.lower() or "device" in path.lower() or "Fp-Device" in str(fl.request.headers):
                    fp_hosts[host+path[:60]] += 1
            body = ""
            try:
                body = fl.request.get_text(strict=False) or ""
            except: pass
            # init JSON
            if "init" in body and "appsflyer" in body:
                try:
                    js=json.loads(body)
                    p=(js.get("params") or {})
                    if p.get("gaid"): gaids.append(p["gaid"])
                    if p.get("appsflyer_id"): afs.append(p["appsflyer_id"])
                    if p.get("anon_id"): anons.append(p["anon_id"])
                    if p.get("fp_device_id"): fpids_dev.append(p["fp_device_id"])
                    if p.get("media_source") is not None: medias.append(p.get("media_source"))
                    if p.get("time_zone"): tzs.append(p["time_zone"])
                    pm=p.get("push_message") or {}
                    tok=pm.get("device_token","") if isinstance(pm,dict) else ""
                    if tok=="": empty_tok+=1
                    else: nonempty_tok+=1; tokens.append(tok[:20]+f"(len={len(tok)})")
                except: pass
            # form body
            if "android_id=" in body and "device_id=" in body:
                m=re.search(r"android_id=([0-9a-fA-F]+)", body)
                if m: passport_android.append(len(m.group(1)))
    finally:
        f.close()

def shapes(xs, n=5):
    out=[]
    for x in xs[:n]:
        if isinstance(x,str) and "-" in x:
            out.append({"len":len(x),"parts":[len(p) for p in x.split("-")],"prefix":x[:4]})
        elif isinstance(x,str):
            out.append({"len":len(x),"prefix":x[:4], "hexish":all(c in "0123456789abcdef" for c in x.lower())})
        else:
            out.append(x)
    return out

print("gaid samples shapes", shapes(list(dict.fromkeys(gaids))))
print("gaid unique", len(set(gaids)), "total", len(gaids))
print("appsflyer shapes", shapes(list(dict.fromkeys(afs))))
for a in list(dict.fromkeys(afs))[:5]:
    left,right=a.split("-",1)
    print("  af parts", len(left), len(right), "left_digits", left.isdigit(), "right_digits", right.isdigit())
print("anon shapes", shapes(list(dict.fromkeys(anons))))
for a in list(dict.fromkeys(anons))[:5]:
    print("  anon", a[:2], "rest_len", len(a)-2, "uuid_like", bool(re.match(r"XZ[0-9a-f-]{36}$", a, re.I)))
print("fp_device_id shapes", shapes(list(dict.fromkeys(fpids_dev))))
for f in list(dict.fromkeys(fpids_dev))[:5]:
    print("  fp", "len", len(f), "ts_prefix", f[:12], "rest_len", len(f)-12, "rest_hex", all(c in "0123456789abcdef" for c in f[12:].lower()))
print("push empty", empty_tok, "nonempty", nonempty_tok, "tok_shapes", tokens[:3])
print("media", collections.Counter(medias).most_common(5))
print("tz", collections.Counter(tzs).most_common(8))
print("android_id lens", collections.Counter(passport_android).most_common())
print("fp host hits top", fp_hosts.most_common(15))
