from pathlib import Path
import json,re

# device profile sample UA
d=json.loads(Path('mitm/device_profile_98566384.json').read_text(encoding='utf-8'))
print('UA:', d.get('user_agent'))
print('keys', list(d.keys()))

# 12_login passport_headers UA
src=Path('12_login.py').read_text(encoding='utf-8')
i=src.find('def passport_headers')
print(src[i:i+800])

# real Dalvik UAs and any Build props from mitm bodies
from mitmproxy import io as mio
from mitmproxy import http as mhttp
uas=set(); fpx=set()
for mf in Path('mitm').glob('*.mitm'):
    with open(mf,'rb') as f:
        for fl in mio.FlowReader(f).stream():
            if not isinstance(fl, mhttp.HTTPFlow): continue
            ua=fl.request.headers.get('User-Agent','')
            if ua.startswith('Dalvik'): uas.add(ua)
            if ua.startswith('FPX'): fpx.add(ua)
print('Dalvik UAs:')
for u in sorted(uas): print(' ',u)
print('FPX UAs:')
for u in sorted(fpx): print(' ',u)

# how does run_guarded work for a one-shot script
print('==== run_guarded head ====')
print(Path('run_guarded.py').read_text(encoding='utf-8')[:1500])
