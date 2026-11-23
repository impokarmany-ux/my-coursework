# -*- coding: utf-8 -*-
"""Локальная панель замков. Только 127.0.0.1, только stdlib, без внешних ресурсов.
Замки идут строго по очереди (один VPN 18081). Без uid/fpid/IP/токенов в интерфейсе и логах."""
import html, json, os, re, subprocess, sys, threading, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
BASE = os.path.dirname(os.path.abspath(__file__)); LOGS = os.path.join(BASE, "logs"); os.makedirs(LOGS, exist_ok=True)
STOPF = os.path.join(LOGS, "panel_stop.flag"); HOST, PORT = "127.0.0.1", 8765
# TODO(wireproxy): список портов прокси на замок для будущей параллельности; пока один, очередь строго последовательная
PROXIES = ["http://127.0.0.1:18081"]
STEPS_N = 123
lock = threading.Lock(); state = {"running": False, "mode": "", "castles": [], "msg": ""}
PLOG = os.path.join(LOGS, f"panel_{datetime.now():%Y%m%d_%H%M%S}.log")

def mask(t):
    # скрываем IP, длинные числа (uid/fpid/id), токены/ключи
    t = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?\b", "<ip>", t)
    t = re.sub(r"\b\d{7,}\b", "#", t)
    t = re.sub(r"(?i)(token|key|fpid|uid|connid|finger\w*|auth\w*)([\"'=:\s]+)[^\s,\"'}]+", r"\1\2***", t)
    t = re.sub(r"\b[A-Za-z0-9_\-]{24,}\b", "***", t)
    return t
def plog(m):
    open(PLOG, "a", encoding="utf-8").write(f"{datetime.now():%H:%M:%S} {mask(m)}\n")

def ready_counts():
    try:
        sys.path.insert(0, BASE); import castle_archive; return castle_archive.counts()
    except Exception as e: return {"err": type(e).__name__}

def run_finish(world, ally, count, live):
    # Добить: один процесс castle_finish.py, он сам идёт по замкам с паузой 60-90 с
    with lock: state.update(running=True, mode=("живой" if live else "проверка (dry-run)") + " / добить", castles=[{"n": 1, "stage": f"добить {count} шт.", "t0": time.time(), "t": 0, "ok": 0, "idx": "", "err": "", "tail": []}], msg="")
    c = state["castles"][0]; plog(f"добить: {count}, мир {world}, альянс {ally}, {'live' if live else 'dry'}")
    cmd = [sys.executable, "castle_finish.py", "--kingdom", str(world), "--alliance", ally, "--count", str(count), "--proxy", PROXIES[0]] + (["--live"] if live else [])
    env = {k: v for k, v in os.environ.items() if k != "RG_OFFLINE"}; env["PYTHONIOENCODING"] = "utf-8"; env["PYTHONUNBUFFERED"] = "1"
    p = subprocess.Popen(cmd, cwd=BASE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for line in p.stdout:
        line = mask(line.rstrip())
        with lock:
            c["tail"] = (c["tail"] + [line])[-12:]; c["t"] = round(time.time() - c["t0"])
            m = re.search(r"castle #(\d+): (finish from|done)", line)
            if m: c["stage"] = f"замок архива №{m.group(1)}: " + ("идёт" if m.group(2) != "done" else "готов")
            if ": done in" in line: c["ok"] += 1
            if "STOP" in line or "СТОП" in line or "Traceback" in line: c["err"] = line[-200:]
    rc = p.wait()
    with lock: c["stage"] = "готово" if rc == 0 else ("остановлен (Стоп)" if rc == 3 else f"стоп (код {rc})"); state["running"] = False; state["msg"] = "добить: завершено"
    plog(f"добить: код {rc}")

def run_queue(world, ally, count, live, kind="full", calm=1.0):
    with lock: state.update(running=True, mode="живой" if live else "проверка (dry-run)", castles=[{"n": i + 1, "stage": "в очереди", "t0": None, "t": 0, "ok": 0, "idx": "", "err": "", "tail": []} for i in range(count)], msg="")
    plog(f"старт очереди: {count} замк., мир {world}, альянс {ally}, режим {'live' if live else 'dry'}")
    for c in state["castles"]:
        if os.path.exists(STOPF): c["stage"] = "отменён (Стоп)"; continue
        proxy = PROXIES[0]   # TODO(wireproxy): PROXIES[(c["n"]-1) % len(PROXIES)] при параллельном запуске
        cmd = [sys.executable, "new_castle_full.py", "--live" if live else "--dry-run", "--world", str(world), "--alliance", ally, "--proxy", proxy]
        if kind == "prep": cmd += ["--mode", "prep", "--calm", str(calm)]
        env = {k: v for k, v in os.environ.items() if k != "RG_OFFLINE"}; env["PYTHONIOENCODING"] = "utf-8"; env["PYTHONUNBUFFERED"] = "1"
        if not live: env["RG_OFFLINE"] = "1"   # dry: ребёнку явно запрещена сеть
        c["t0"] = time.time(); c["stage"] = "создание"; plog(f"замок №{c['n']}: запуск {'live' if live else 'dry'}")
        p = subprocess.Popen(cmd, cwd=BASE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        for line in p.stdout:
            line = mask(line.rstrip())
            with lock:
                c["tail"] = (c["tail"] + [line])[-12:]; c["t"] = round(time.time() - c["t0"])
                if "[state]" in line: c["stage"] = "проверка королевства"
                m = re.search(r"idx ([\d.]+):.*ok:1", line)
                if m: c["stage"] = "круг"; c["idx"] = f"{m.group(1)}/{115 if kind == 'prep' else STEPS_N}"; c["ok"] += 1
                if "СТОП" in line or "Traceback" in line or "Error" in line: c["err"] = line[-200:]
        rc = p.wait()
        with lock:
            c["t"] = round(time.time() - c["t0"])
            c["stage"] = "готово" if rc == 0 else ("остановлен (Стоп)" if rc == 3 else f"стоп (код {rc})")
        plog(f"замок №{c['n']}: {c['stage']}, {c['t']} с, ok {c['ok']}")
        if rc != 0: 
            for r in state["castles"]:
                if r["stage"] == "в очереди": r["stage"] = "отменён"
            break
    with lock: state["running"] = False; state["msg"] = "очередь завершена"
    plog("очередь завершена")

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

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Панель замков</title>
<style>body{font-family:sans-serif;margin:20px;max-width:1000px}fieldset{margin-bottom:12px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:4px;vertical-align:top}pre{margin:0;font-size:11px;white-space:pre-wrap;max-height:160px;overflow:auto}.err{color:#b00}</style></head><body>
<h2>Панель замков</h2>
<form id="f"><fieldset><legend>Параметры</legend>
Королевство <input name="world" value="837" size="5"> &nbsp; Тег альянса <input name="alliance" value="3cy" size="6"> &nbsp; Замков <input name="count" value="1" size="3"><br><br>
<label><input type="radio" name="mode" value="dry" checked> проверка (dry-run)</label>
<label><input type="radio" name="mode" value="live"> живой</label>
&nbsp; <label><input type="checkbox" name="confirm" value="1"> подтверждаю живой запуск</label><br><br>
<button type="button" onclick="go('/start')">Старт (полный круг)</button> <button type="button" onclick="go('/prep')">Заготовки (до 9, без альянса)</button> спокойно x<input name="calm" value="1.5" size="3"> <button type="button" onclick="go('/finish')">Добить (9→10 в альянсе)</button> <button type="button" onclick="go('/stop')">Стоп</button> <span id="m"></span>
</fieldset></form>
<form id="fb"><fieldset><legend>Пачки (параллельно): строка = королевство альянс замков параллельно режим(full/prep)</legend>
<textarea name="rows" rows="3" cols="50">837 3cy 15 15 prep
838 abc 15 15 prep</textarea><br>
<label><input type="radio" name="mode" value="dry" checked> проверка (dry-run)</label> <label><input type="radio" name="mode" value="live"> живой</label>
&nbsp; <label><input type="checkbox" name="confirm" value="1"> подтверждаю живой запуск</label> &nbsp; спокойно x<input name="calm" value="1.0" size="3">
<button type="button" onclick="gb('/batch')">Запустить пачки</button> <button type="button" onclick="go('/stop')">Стоп всё</button> <span id="mb"></span>
</fieldset></form><div id="sb"></div>
<div id="s"></div>
<script>
function go(u){fetch(u,{method:'POST',body:new URLSearchParams(new FormData(document.getElementById('f')))}).then(r=>r.json()).then(j=>{document.getElementById('m').textContent=j.msg;upd()})}
function esc(t){return String(t).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function upd(){fetch('/status').then(r=>r.json()).then(j=>{let h='<p>Заготовок 9 ур. по королевствам: '+esc(JSON.stringify(j.ready||{}))+'</p><p>Режим: '+esc(j.mode)+' | '+(j.running?'идёт':'не идёт')+' '+esc(j.msg)+'</p><table><tr><th>Замок</th><th>Этап</th><th>idx</th><th>Время, с</th><th>ok</th><th>Ошибка</th><th>Хвост лога</th></tr>';
for(const c of j.castles){h+='<tr><td>№'+c.n+'</td><td>'+esc(c.stage)+'</td><td>'+esc(c.idx)+'</td><td>'+c.t+'</td><td>'+c.ok+'</td><td class="err">'+esc(c.err)+'</td><td><pre>'+esc(c.tail.join('\\n'))+'</pre></td></tr>'}
document.getElementById('s').innerHTML=h+'</table>'})}
function gb(u){fetch(u,{method:'POST',body:new URLSearchParams(new FormData(document.getElementById('fb')))}).then(r=>r.json()).then(j=>{document.getElementById('mb').textContent=j.msg;updb()})}
function updb(){fetch('/batch_status').then(r=>r.json()).then(L=>{let h='';for(const b of L){h+='<p>'+(b.live?'ЖИВОЙ':'dry')+' | '+(b.running?'идёт':'закончено')+' | '+esc(JSON.stringify(b.spec))+'</p><table><tr><th>замок</th><th>королевство</th><th>альянс</th><th>страна туннеля</th><th>этап</th><th>idx</th><th>с</th></tr>';
for(const c of b.castles){h+='<tr><td>'+esc(c.name)+'</td><td>'+c.kingdom+'</td><td>'+esc(c.alliance)+'</td><td>'+esc(c.cc)+'</td><td>'+esc(c.stage)+'</td><td>'+esc(c.idx)+'</td><td>'+c.t+'</td></tr>'}h+='</table>'}document.getElementById('sb').innerHTML=h})}
setInterval(updb,3000);updb();
setInterval(upd,3000);upd();
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _j(self, o, code=200):
        b = json.dumps(o, ensure_ascii=False).encode("utf-8"); self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if self.path == "/batch_status": return self._j(batch_status())
        if self.path == "/status":
            with lock: o = {k: (v if k != "castles" else [{x: y for x, y in c.items() if x != "t0"} for c in v]) for k, v in state.items()}
            o["ready"] = ready_counts(); return self._j(o)
        b = PAGE.encode("utf-8"); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        q = {k: v[0] for k, v in parse_qs(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()).items()}
        if self.path == "/stop":
            open(STOPF, "w").write("stop"); plog("Стоп нажат"); return self._j({"msg": "Стоп: остановка после текущей команды"})
        if self.path == "/batch":
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
        if self.path not in ("/start", "/prep", "/finish"): return self._j({"msg": "?"}, 404)
        with lock:
            if state["running"]: return self._j({"msg": "уже идёт"})
        try:
            world = int(q.get("world", "837")); count = int(q.get("count", "1")); ally = q.get("alliance", "3cy").strip()
        except ValueError: return self._j({"msg": "неверные числа"})
        if not (1 <= world <= 5000 and 1 <= count <= 20 and re.fullmatch(r"[A-Za-z0-9_]{2,8}", ally)): return self._j({"msg": "неверные параметры"})
        live = q.get("mode") == "live"
        if live and q.get("confirm") != "1": return self._j({"msg": "для живого режима поставь галочку подтверждения"})
        if os.path.exists(STOPF): os.remove(STOPF)
        try: calm = max(1.0, min(5.0, float(q.get("calm", "1.5"))))
        except ValueError: calm = 1.5
        if self.path == "/finish": threading.Thread(target=run_finish, args=(world, ally, count, live), daemon=True).start()
        else: threading.Thread(target=run_queue, args=(world, ally, count, live, "prep" if self.path == "/prep" else "full", calm), daemon=True).start()
        what = {"/start": "полный круг", "/prep": f"заготовки (спокойно x{calm})", "/finish": "добить"}[self.path]
        return self._j({"msg": f"запущено: {what}, {count} шт., {'живой' if live else 'dry-run'}"})

if __name__ == "__main__":
    if os.path.exists(STOPF): os.remove(STOPF)
    print(f"Панель: http://{HOST}:{PORT}/  (только локально)")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
