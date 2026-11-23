import json
W=json.load(open('mitm/_3r_all.json',encoding='utf-8'))
bl=[r['rq']['params']['args']['tutorial'] for r in W if r['op']=='Player:setTutorial' and r['uid']==98566768]
p=json.load(open('mitm/upgrade_plan.json',encoding='utf-8'))
ix=[s for s in p['steps'] if s['op']=='Player:setTutorial']
print([s['idx'] for s in ix])
for s,b in zip(ix,bl): s['args']={'tutorial':b,'city_id':{'const':'uid'}}
json.dump(p,open('mitm/upgrade_plan.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
