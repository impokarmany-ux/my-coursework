from pathlib import Path
apk = Path('apk/base')
# list interesting libs and sm-related
libs = list(apk.rglob('*.so')) if apk.exists() else []
print('so count', len(libs))
for p in libs:
    n=p.name.lower()
    if any(x in n for x in ('sm','fp','guard','device','sec','encrypt','fpx')):
        print(p)

# strings in classes related to encode compress tn ep
import subprocess, re
dex = Path('apk/base/classes4.dex')
# use strings via python
data = dex.read_bytes()
for s in [b'encode', b'compress', b'deviceprofile', b'/deviceprofile', b'tn', b'organization']:
    print(s, data.count(s))

# extract readable strings containing deviceprofile or encode=
strings = set()
cur=bytearray()
for b in data:
    if 32 <= b < 127:
        cur.append(b)
    else:
        if len(cur) >= 8:
            strings.add(cur.decode('ascii', errors='ignore'))
        cur=bytearray()
interesting=[s for s in strings if any(x in s.lower() for x in ('deviceprofile','decdevice','organization','encode','compress','shumei','sm_app','fp_device'))]
print('interesting', len(interesting))
for s in sorted(interesting)[:60]:
    print(repr(s)[:120])
