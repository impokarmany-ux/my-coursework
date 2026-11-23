import re
data=open(r"E:\Dump\global-metadata.dat",'rb').read()
def ctx(off,back=400,fwd=120):
    s=data[off-back:off+fwd]
    toks=re.findall(rb"[ -~]{4,}",s)
    return [t.decode() for t in toks]
for lbl,p in [("FP ",b"FP "),("app_secret",b"app_secret"),("fp_device_token",b"fp_device_token"),("HmacSHA256",b"HmacSHA256"),("FpDeviceToken",b"Fp-Device-Token")]:
    i=data.find(p)
    print("####",lbl,i)
    for t in ctx(i): print("  ",t)
