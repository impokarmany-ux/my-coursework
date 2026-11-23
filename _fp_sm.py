from pathlib import Path
import re

dump = Path(r'E:\dump.cs').read_text(encoding='utf-8', errors='ignore')

# find classes with SM_ORGANIZATION / SM_APP_ID
for m in re.finditer(r'SM_ORGANIZATION', dump):
    start = dump.rfind('class ', 0, m.start())
    # get class block roughly
    chunk = dump[start:start+2500]
    print('=== near SM_ORGANIZATION ===')
    print(chunk[:2000])
    print('---')
    break

# search encode=2 compress related
for pat in [r'class .*Sm[A-Za-z]*', r'DeviceToken', r'deviceId', r'encode', r'CompressType', r'EncodeType']:
    pass

for pat in ['SmBackend', 'SMBackend', 'SmDevice', 'DeviceProfiler', 'FpSm', 'SecurityModule', 'shumei', 'ShuMei', 'FPX']:
    hits = list(re.finditer(pat, dump))
    print(f'{pat}: {len(hits)}')
    for h in hits[:2]:
        start=max(0,h.start()-60); end=min(len(dump),h.end()+100)
        print(' ', dump[start:end].replace('\n',' | ')[:180])
