import json,base64,re
from pathlib import Path
data=json.load(open(r"E:\protocol_analysis\capture\mitm\_pp_all.json",encoding='utf-8'))
# collect unique Fp-Device-Token values (redacted)
seen=set()
for r in data:
    rqh=r.get('rqh') or {}
    for k,v in rqh.items():
        if k.lower()=='fp-device-token':
            if v not in seen:
                seen.add(v)
                print(r.get('file'), r.get('host'), "fdt_len",len(v), "prefix",v[:8], "suffix",v[-8:])
                # try decode
                for pad in ('', '=', '==', '==='):
                    try:
                        raw=base64.b64decode(v+pad)
                        print("  b64decode len",len(raw),"hex",raw[:16].hex())
                        break
                    except: pass
                try:
                    raw=base64.urlsafe_b64decode(v+'==')
                    print("  urlsafe len",len(raw),"hex",raw[:16].hex())
                except: pass
print("unique fdt",len(seen))
# also look for device token generation strings in metadata
data2=open(r"E:\Dump\global-metadata.dat",'rb').read()
for p in [b"Fp-Device-Token",b"fp_device_token",b"DeviceToken",b"device_token",b"MakeDeviceToken",b"getDeviceToken",b"FpDevice"]:
    i=0; c=0
    while True:
        j=data2.find(p,i)
        if j<0: break
        c+=1; i=j+1
        if c<=3:
            s=data2[max(0,j-80):j+120]
            toks=re.findall(rb"[ -~]{4,}",s)
            print(p, [t.decode() for t in toks])
