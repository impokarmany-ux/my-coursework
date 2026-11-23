from pathlib import Path
import re

# search capture tree for organization string and encode/compress constants
org = b'xNxMh079HgFDeRkJE1qN'
hits = []
for p in Path(r'E:\protocol_analysis').rglob('*'):
    if not p.is_file(): continue
    if p.stat().st_size > 80_000_000: continue
    if p.suffix.lower() in ('.png','.jpg','.mp4','.zip','.7z','.rar'): continue
    try:
        data = p.read_bytes()
    except Exception:
        continue
    if org in data or b'deviceprofile/v4' in data or b'SM_ORGANIZATION' in data:
        hits.append((str(p), p.stat().st_size))
print('hits', len(hits))
for h in hits[:30]:
    print(h)

# also check IP check - does ipify return country? Currently only IP.
# options: ipapi.co, ip-api.com via same proxy - user said "geo из того же ответа" for the IP check already done.
# Current check uses api.ipify.org?format=json which ONLY returns IP - no country!
# Need to switch IP check to a service that returns country in same response, via proxy.
print('---')
# what does 15 use
print('IP_CHECK', 'api.ipify.org' )
