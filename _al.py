import json
W=json.load(open('mitm/_3r_all.json',encoding='utf-8'))
for r in W:
    if any(k in (r['op'] or '') for k in ('lliance','unSubTopics')) and r['cm']=='call:commit':
        print(r['uid'],r['op'],repr(r['rq']['params'].get('args'))[:120],(r.get('rs_s') or '')[:120])
