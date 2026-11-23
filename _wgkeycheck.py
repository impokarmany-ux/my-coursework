import re,glob
for f in glob.glob('*.conf'):
    if f=='wireproxy.conf': continue
    t=open(f,encoding='utf-8',errors='ignore').read()
    m=re.search(r'PrivateKey\s*=\s*(\S+)',t)
    k=m.group(1) if m else ''
    ok=bool(re.fullmatch(r'[A-Za-z0-9+/]{43}=',k))
    st='OK' if ok else ('PLACEHOLDER' if 'insert' in k else 'BAD len=%d'%len(k))
    print(f,'| PrivateKey:',st,'| Peer:', '[Peer]' in t,'| Endpoint:', 'Endpoint' in t,'| AllowedIPs 0/0:', '0.0.0.0/0' in t)
