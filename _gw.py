import os,re
# gateway hosts in bodies filenames / pp
base=r"E:\protocol_analysis\capture\mitm\bodies"
names=[n for n in os.listdir(base) if 'gateway' in n.lower() or 'g19' in n.lower()][:20]
print("gateway body files",names)
# search pp and catalogs
for p in [r"E:\protocol_analysis\capture\mitm\cmd_catalog.txt",
          r"E:\protocol_analysis\capture\mitm\READY_SWITCH.txt"]:
  if os.path.exists(p):
    t=open(p,encoding='utf-8',errors='ignore').read()
    for m in re.finditer(r'.{0,40}gateway.{0,60}', t, re.I):
      print(os.path.basename(p), m.group(0)[:100])
# list unique hosts from body filenames
hosts=set()
for n in os.listdir(base):
  # pattern NNN_req_HOST__path
  m=re.match(r'\d+_(?:req|resp)_(.+?)__', n)
  if m: hosts.add(m.group(1))
print("hosts sample:")
for h in sorted(hosts):
  if any(x in h for x in ('gateway','ws','socket','kg','gog','funplus','passport')):
    print(" ",h)
