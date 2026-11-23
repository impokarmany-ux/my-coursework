import re
pats=[b"Fp-Device-Token",b"Authorization",b"FP ",b"HmacSHA256",b"client_api.php",b"fp_device_token",b"X-FP",b"app_secret",b"appSecret",b"signature",b"device_token",b"gog-passport",b"session_login",b"fp-passport"]
for path in [r"E:\Dump\global-metadata.dat",r"E:\Dump\libil2cpp.so"]:
    data=open(path,'rb').read()
    print("====",path,len(data))
    for p in pats:
        i=data.find(p); 
        if i>=0:
            print(p, "count", data.count(p), "first@",i)
