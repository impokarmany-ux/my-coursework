# офлайн-проверка --speedup-45: сеть не используется, ответы сервера имитируются
import json,re,time,types
src=open("16_run_full.py",encoding="utf-8").read()
SEC={6000029:300,6002580:60}
def run(left0):
    st={"end":time.time()+left0,"inv":{6000029:10,6002580:55}}; sent=[]
    class SC:
        def build_commit_envelope(self,op,k,t,args,**kw): return {"op":op,"args":args}
        def send_command(self,key,env):
            a=env["args"]; sent.append((a["item_id"],a["amount"]))
            st["inv"][a["item_id"]]-=a["amount"]; st["end"]-=SEC[a["item_id"]]*a["amount"]
            now=time.time(); jobs=[{"job_id":7,"time_end":st["end"]}] if st["end"]>now else []
            return {"ok":1,"time":now*1000,"data":{"set":{"job":jobs,"user_consumable":[{"item_property_id":i,"quantity":q} for i,q in st["inv"].items()]}}},b"",{}
    g=dict(json=json,time=types.SimpleNamespace(time=time.time,sleep=lambda x:g.__setitem__("slept",round(x))),re=re,sc=SC(),
           bd={"session_key":0,"token":0,"fpid":0,"seq_next":0},seq=1,KEY=0,BP="NUL",RESP="NUL",UID=1,FORBIDDEN=set(),ALLY=0,FILL={},ORDER={},
           stats={"sent":0,"ok":0},city={"1":{"level":4}},gold_last=[None],last_send=[0.0],a=types.SimpleNamespace(sp45_wait=1200),log=lambda m:None,
           sp={"job":7,"end":st["end"] if left0>0 else time.time()-1,"dt":0.0,"inv":dict(st["inv"])})
    w=src[src.index("def walk"):]; exec(w[:w.index("\n\n")],g)
    exec(src[src.index("def send(op, args):"):src.index("def wait_gap")],g); exec("def wait_gap(s): pass",g)
    g["speedup_45"](24)
    print(f"остаток {left0:>4} с -> ушло {sent or 'ничего'}, ждали {g.get('slept',0)} с, замок {g['city']['1']['level']}")
for L in (77,300,0,1000): run(L)
