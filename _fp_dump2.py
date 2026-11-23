from pathlib import Path
import re

# existing research
for p in Path('.').glob('_fp*'):
    print('file', p.name, p.stat().st_size)
for p in Path('.').glob('_devproxy*'):
    print('file', p.name, p.stat().st_size)
for p in Path('mitm').glob('*device*'):
    print('mitm', p.name)

# dump.cs search for encode/compress deviceprofile
dump = Path(r'E:\dump.cs')
if dump.exists():
    text = dump.read_text(encoding='utf-8', errors='ignore')
    for pat in ['deviceprofile', 'DeviceProfile', 'decdevicetoken', 'DecDeviceToken',
                'encode.*compress', 'FpDevice', 'organization', 'xNxMh079']:
        hits = list(re.finditer(pat, text, re.I))
        print(f'pat {pat!r}: {len(hits)} hits')
        for h in hits[:3]:
            start=max(0,h.start()-80); end=min(len(text), h.end()+120)
            snippet=text[start:end].replace('\n',' | ')
            print(' ', snippet[:200])
else:
    print('NO dump.cs')
