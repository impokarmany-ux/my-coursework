import json
for f in ['FPSDKConfigAndroid.json','fpx_config.json']:
    d=json.load(open(f,encoding='utf-8-sig'))
    def w(d,p=''):
        for k,v in (d.items() if isinstance(d,dict) else enumerate(d)):
            if isinstance(v,(dict,list)): w(v,p+str(k)+'.')
            else:
                s=str(v); print(f,p+str(k), s if len(s)<10 or 'url' in str(k).lower() else s[:3]+'...('+str(len(s))+')')
    w(d)
