import os,re
# scan dex files for relevant strings
for n in sorted(os.listdir('.')):
  if not n.endswith('.dex'): continue
  data=open(n,'rb').read()
  for p in [b'Fp-Device-Token',b'fp_device_token',b'MakeSignV3',b'HmacSHA256',b'client_api.php',b'FunplusGameKey',b'device_token']:
    c=data.count(p)
    if c:
      i=data.find(p)
      ctx=data[max(0,i-60):i+80]
      toks=re.findall(rb"[ -~]{4,}",ctx)
      print(n,p,c,[t.decode() for t in toks[:8]])
