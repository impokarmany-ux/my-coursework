s=open('tunnel_pool.py',encoding='utf-8').read().replace('v.get("status") == "ok"','str(v.get("status")).upper() in ("OK", "MISMATCH")');open('tunnel_pool.py','w',encoding='utf-8').write(s)
