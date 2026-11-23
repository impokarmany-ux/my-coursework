import json,re
# GameSetting.json
p=r"E:\protocol_analysis\apk\base\assets"
import os
for root,_,files in os.walk(p):
  for f in files:
    if f=="GameSetting.json":
      path=os.path.join(root,f)
      print("FOUND",path,os.path.getsize(path))
      text=open(path,encoding='utf-8',errors='ignore').read()
      # find keys containing secret/key/game
      for m in re.finditer(r'"(?P<k>[^"]*(?:secret|Secret|game_key|gameKey|appKey|app_key|mGameKey|auth)[^"]*)"\s*:\s*"(?P<v>[^"]*)"',text):
        k,v=m.group('k'),m.group('v')
        print(f"  {k} = {v[:4]}...({len(v)})" if len(v)>8 else f"  {k} = {v}")
      # also print nearby 2064
      for m in re.finditer(r'.{0,60}2064.{0,80}',text):
        print("CTX2064:",m.group(0)[:200])
