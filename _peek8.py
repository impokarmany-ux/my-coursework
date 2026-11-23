import json,sys,os
sys.stdout.reconfigure(encoding="utf-8")
# между 20:04 и 20:34 что писали в resp / inject
for root,dirs,files in os.walk("."):
    for f in files:
        path=os.path.join(root,f)
        try:
            mt=os.path.getmtime(path)
        except: continue
        # 20:04 = ~1793469867 server? use file mtime local
        import datetime
        dt=datetime.datetime.fromtimestamp(mt)
        if dt.hour==20 and 4 <= dt.minute <= 40:
            if any(x in f for x in (".log",".jsonl",".json",".py",".txt")):
                print(dt.strftime("%H:%M:%S"), path, os.path.getsize(path))
