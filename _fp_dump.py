import re,sys
sys.stdout.reconfigure(encoding="utf-8")
# search dump.cs for FunPlus device registration clues
path=r"E:\dump.cs"
keys=["FpDevice","DeviceToken","fp_device","RegisterDevice","DeviceService","Fp-Device","GetDeviceToken","device_token","FunPlusSdk","IDevice"]
# stream file for matches with context
pat=re.compile("|".join(re.escape(k) for k in keys), re.I)
count=0
with open(path,"r",encoding="utf-8",errors="replace") as f:
    lines=f.readlines()
print("lines",len(lines))
hits=[]
for i,l in enumerate(lines):
    if pat.search(l):
        hits.append(i)
print("hit lines",len(hits))
# show unique interesting class/method blocks
shown=0
for i in hits:
    if shown>40: break
    # skip noise
    l=lines[i].strip()
    if "private" in l and "Field" in lines[max(0,i-2)]: 
        continue
    ctx="".join(lines[max(0,i-2):i+3])
    if any(x in ctx for x in ("Register","Request","Http","Url","Token","fp_device_id","DeviceId")):
        print(f"--- L{i+1} ---")
        print(ctx[:400])
        shown+=1
