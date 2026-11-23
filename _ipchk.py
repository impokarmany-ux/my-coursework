import requests,traceback
s=requests.Session();s.trust_env=False;s.proxies={'http':'http://127.0.0.1:18081','https':'http://127.0.0.1:18081'}
try:
  r=s.get('https://api.ipify.org?format=json',timeout=15);print('ok', r.json()['ip']!='203.0.113.10')
except Exception as e: traceback.print_exc()
