import re
# FunPlus encryption clues from metadata around session_login / MakeSign / AES
data=open(r"E:\Dump\global-metadata.dat",'rb').read()
needles=[b"session_login",b"MakeSignV3",b"_HmacSHA256ToBase64",b"get_dw_bind_list",b"fp-passport",b"AesUtil",b"AES/CBC",b"AES/ECB",b"encryptRequest",b"decryptResponse",b"4dOKPU",b"FunplusHttp",b"mGameKey"]
for p in needles:
  i=data.find(p)
  print(f"==== {p} @ {i} count={data.count(p)}")
  if i<0: continue
  s=data[max(0,i-200):i+250]
  toks=re.findall(rb"[ -~]{5,}",s)
  for t in toks[:25]:
    print(" ",t.decode())
