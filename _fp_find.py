from pathlib import Path
import re, json

# docs
for name in ['АНОНИМНОСТЬ.md','ШЛЮЗ.md']:
    t=Path(name).read_text(encoding='utf-8', errors='ignore')
    for kw in ['deviceprofile','decdevice','fp_device','ShuMei','shumei','encode','fingerprint','KGGuard']:
        if kw.lower() in t.lower():
            print(name, 'has', kw)

# _devproxy.py content
print('==== _devproxy.py ====')
print(Path('_devproxy.py').read_text(encoding='utf-8')[:2500])

# look for sm / fingerprint libs
for p in Path(r'E:\\').glob('**/libsm*.so'):
    print('lib', p)
# too slow maybe - search capture and common paths
for root in [Path('.'), Path(r'E:\protocol_analysis')]:
    if not root.exists(): continue
    for p in root.rglob('*'):
        n=p.name.lower()
        if any(x in n for x in ('shumei','libsm','sm-core','deviceprofile','kgguard')):
            print('found', p)
