import re,glob,os,collections
fs=[f for f in glob.glob('wg/*.conf') if not f.endswith('wireproxy.conf')]
other=[f for f in os.listdir('wg') if not f.endswith('.conf') and f!='bin' and not f.startswith('wireproxy.conf')]
keys=collections.Counter(); bad=[]; ccs=collections.Counter()
for f in fs:
    t=open(f,encoding='utf-8',errors='ignore').read()
    m=re.search(r'PrivateKey\s*=\s*(\S+)',t); k=m.group(1) if m else ''
    if not re.fullmatch(r'[A-Za-z0-9+/]{43}=',k) or '[Peer]' not in t or 'Endpoint' not in t or '0.0.0.0/0' not in t: bad.append(os.path.basename(f))
    keys[hash(k)]+=1
    ccs[os.path.basename(f).split('-')[0]]+=1
print('configs:',len(fs),'| bad:',bad,'| distinct keys:',len(keys),'| countries:',len(ccs))
print('other files:',other)
print('dups like (1):',[os.path.basename(f) for f in fs if '(' in f])
