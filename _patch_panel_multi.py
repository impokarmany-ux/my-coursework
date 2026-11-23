f = "panel.py"; s = open(f, encoding="utf-8").read()
fn = '''
BATCHES = []   # panel-launched batch_runner runs: {"p": Popen, "dir": path or None, "t": start}
def run_batches(rows, live, calm):
    spec = ",".join(f"{w}:{al}:{c}:{k}:{m}" for w, al, c, k, m in rows)
    cmd = [sys.executable, "batch_runner.py", "--batches", spec, "--calm", str(calm)] + (["--live"] if live else [])
    env = {k: v for k, v in os.environ.items() if k != "RG_OFFLINE"}; env["PYTHONIOENCODING"] = "utf-8"; env["PYTHONUNBUFFERED"] = "1"
    if not live: env["RG_OFFLINE"] = "1"
    before = set(os.listdir(LOGS)); p = subprocess.Popen(cmd, cwd=BASE, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec = {"p": p, "dir": None, "t": time.time(), "spec": [(w, al, c, k, m) for w, al, c, k, m in rows], "live": live}; BATCHES.append(rec)
    plog(f"batch start: {spec} {'live' if live else 'dry'}")
    for _ in range(50):
        new = [d for d in set(os.listdir(LOGS)) - before if d.startswith("batch_")]
        if new: rec["dir"] = os.path.join(LOGS, sorted(new)[-1]); break
        time.sleep(0.2)
def batch_status():
    out = []
    for r in BATCHES[-6:]:
        st = {}
        try: st = json.load(open(os.path.join(r["dir"], "status.json"), encoding="utf-8")) if r["dir"] else {}
        except Exception: pass
        rows = []
        for tag, c in sorted((st.get("castles") or {}).items(), key=lambda x: (x[1].get("batch", 0), x[1].get("n", 0))):
            rows.append({"name": f"пачка {c.get('batch')} · замок №{c.get('n')}", "kingdom": c.get("kingdom"), "alliance": c.get("alliance"),
                         "stage": c.get("stage"), "idx": c.get("idx"), "cc": c.get("cc", ""), "t": c.get("t", round(time.time() - c["t0"]) if c.get("t0") else 0)})
        out.append({"running": r["p"].poll() is None, "live": r["live"], "spec": r["spec"], "castles": rows})
    return out
'''
s = s.replace('\nPAGE = """', fn + '\nPAGE = """', 1)
html = '''<form id="fb"><fieldset><legend>Пачки (параллельно): строка = королевство альянс замков параллельно режим(full/prep)</legend>
<textarea name="rows" rows="3" cols="50">837 3cy 15 15 prep
838 abc 15 15 prep</textarea><br>
<label><input type="radio" name="mode" value="dry" checked> проверка (dry-run)</label> <label><input type="radio" name="mode" value="live"> живой</label>
&nbsp; <label><input type="checkbox" name="confirm" value="1"> подтверждаю живой запуск</label> &nbsp; спокойно x<input name="calm" value="1.0" size="3">
<button type="button" onclick="gb('/batch')">Запустить пачки</button> <button type="button" onclick="go('/stop')">Стоп всё</button> <span id="mb"></span>
</fieldset></form><div id="sb"></div>
<div id="s">'''
s = s.replace('<div id="s">', html, 1)
js = '''function gb(u){fetch(u,{method:'POST',body:new URLSearchParams(new FormData(document.getElementById('fb')))}).then(r=>r.json()).then(j=>{document.getElementById('mb').textContent=j.msg;updb()})}
function updb(){fetch('/batch_status').then(r=>r.json()).then(L=>{let h='';for(const b of L){h+='<p>'+(b.live?'ЖИВОЙ':'dry')+' | '+(b.running?'идёт':'закончено')+' | '+esc(JSON.stringify(b.spec))+'</p><table><tr><th>замок</th><th>королевство</th><th>альянс</th><th>страна туннеля</th><th>этап</th><th>idx</th><th>с</th></tr>';
for(const c of b.castles){h+='<tr><td>'+esc(c.name)+'</td><td>'+c.kingdom+'</td><td>'+esc(c.alliance)+'</td><td>'+esc(c.cc)+'</td><td>'+esc(c.stage)+'</td><td>'+esc(c.idx)+'</td><td>'+c.t+'</td></tr>'}h+='</table>'}document.getElementById('sb').innerHTML=h})}
setInterval(updb,3000);updb();
setInterval(upd,3000);upd();'''
s = s.replace("setInterval(upd,3000);upd();", js, 1)
s = s.replace('''        if self.path == "/status":''', '''        if self.path == "/batch_status": return self._j(batch_status())
        if self.path == "/status":''', 1)
s = s.replace('''        if self.path not in ("/start", "/prep", "/finish"): return self._j({"msg": "?"}, 404)''', '''        if self.path == "/batch":
            rows = []
            for ln in q.get("rows", "").splitlines():
                p_ = ln.split()
                if not p_: continue
                try: w, al, c, k, m = int(p_[0]), p_[1], int(p_[2]), int(p_[3]), (p_[4] if len(p_) > 4 else "prep")
                except (ValueError, IndexError): return self._j({"msg": f"плохая строка: {ln[:40]}"})
                if not (1 <= w <= 5000 and re.fullmatch(r"[A-Za-z0-9_]{2,8}", al) and 1 <= c <= 1000 and 1 <= k <= 30 and m in ("full", "prep")): return self._j({"msg": f"плохие параметры: {ln[:40]}"})
                rows.append((w, al, c, k, m))
            if not rows or len(rows) > 4: return self._j({"msg": "нужно 1-4 строки"})
            live = q.get("mode") == "live"
            if live and q.get("confirm") != "1": return self._j({"msg": "для живого режима поставь галочку подтверждения"})
            if any(r["p"].poll() is None for r in BATCHES): return self._j({"msg": "пачки уже идут"})
            if os.path.exists(STOPF): os.remove(STOPF)
            try: calm = max(1.0, min(5.0, float(q.get("calm", "1.0"))))
            except ValueError: calm = 1.0
            threading.Thread(target=run_batches, args=(rows, live, calm), daemon=True).start()
            return self._j({"msg": f"запущено пачек: {len(rows)}, {'живой' if live else 'dry-run'}"})
        if self.path not in ("/start", "/prep", "/finish"): return self._j({"msg": "?"}, 404)''', 1)
assert s.count("batch_status") >= 3
open(f, "w", encoding="utf-8").write(s); print("panel patched")
