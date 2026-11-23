exec(open("_split_patch.py", encoding="utf-8-sig").read().split("patch(\"16_run_full.py\"")[0])
patch("panel.py", [
('def run_queue(world, ally, count, live):\n',
 'def ready_counts():\n'
 '    try:\n        sys.path.insert(0, BASE); import castle_archive; return castle_archive.counts()\n'
 '    except Exception as e: return {"err": type(e).__name__}\n\n'
 'def run_finish(world, ally, count, live):\n'
 '    # Добить: один процесс castle_finish.py, он сам идёт по замкам с паузой 60-90 с\n'
 '    with lock: state.update(running=True, mode=("живой" if live else "проверка (dry-run)") + " / добить", castles=[{"n": 1, "stage": f"добить {count} шт.", "t0": time.time(), "t": 0, "ok": 0, "idx": "", "err": "", "tail": []}], msg="")\n'
 '    c = state["castles"][0]; plog(f"добить: {count}, мир {world}, альянс {ally}, {\'live\' if live else \'dry\'}")\n'
 '    cmd = [sys.executable, "castle_finish.py", "--kingdom", str(world), "--alliance", ally, "--count", str(count), "--proxy", PROXIES[0]] + (["--live"] if live else [])\n'
 '    env = {k: v for k, v in os.environ.items() if k != "RG_OFFLINE"}; env["PYTHONIOENCODING"] = "utf-8"; env["PYTHONUNBUFFERED"] = "1"\n'
 '    p = subprocess.Popen(cmd, cwd=BASE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")\n'
 '    for line in p.stdout:\n'
 '        line = mask(line.rstrip())\n'
 '        with lock:\n'
 '            c["tail"] = (c["tail"] + [line])[-12:]; c["t"] = round(time.time() - c["t0"])\n'
 '            m = re.search(r"castle #(\\d+): (finish from|done)", line)\n'
 '            if m: c["stage"] = f"замок архива №{m.group(1)}: " + ("идёт" if m.group(2) != "done" else "готов")\n'
 '            if ": done in" in line: c["ok"] += 1\n'
 '            if "STOP" in line or "СТОП" in line or "Traceback" in line: c["err"] = line[-200:]\n'
 '    rc = p.wait()\n'
 '    with lock: c["stage"] = "готово" if rc == 0 else ("остановлен (Стоп)" if rc == 3 else f"стоп (код {rc})"); state["running"] = False; state["msg"] = "добить: завершено"\n'
 '    plog(f"добить: код {rc}")\n\n'
 'def run_queue(world, ally, count, live, kind="full", calm=1.0):\n'),
('        cmd = [sys.executable, "new_castle_full.py", "--live" if live else "--dry-run", "--world", str(world), "--alliance", ally, "--proxy", proxy]\n',
 '        cmd = [sys.executable, "new_castle_full.py", "--live" if live else "--dry-run", "--world", str(world), "--alliance", ally, "--proxy", proxy]\n'
 '        if kind == "prep": cmd += ["--mode", "prep", "--calm", str(calm)]\n'),
('c["idx"] = f"{m.group(1)}/{STEPS_N}"', 'c["idx"] = f"{m.group(1)}/{115 if kind == \'prep\' else STEPS_N}"'),
('<button type="button" onclick="go(\'/start\')">Старт</button>',
 '<button type="button" onclick="go(\'/start\')">Старт (полный круг)</button> <button type="button" onclick="go(\'/prep\')">Заготовки (до 9, без альянса)</button> спокойно x<input name="calm" value="1.5" size="3"> <button type="button" onclick="go(\'/finish\')">Добить (9→10 в альянсе)</button>'),
("let h='<p>Режим: '+esc(j.mode)", "let h='<p>Заготовок 9 ур. по королевствам: '+esc(JSON.stringify(j.ready||{}))+'</p><p>Режим: '+esc(j.mode)"),
('            with lock: return self._j({k: (v if k != "castles" else [{x: y for x, y in c.items() if x != "t0"} for c in v]) for k, v in state.items()})',
 '            with lock: o = {k: (v if k != "castles" else [{x: y for x, y in c.items() if x != "t0"} for c in v]) for k, v in state.items()}\n'
 '            o["ready"] = ready_counts(); return self._j(o)'),
('        if self.path != "/start": return', '        if self.path not in ("/start", "/prep", "/finish"): return'),
('        threading.Thread(target=run_queue, args=(world, ally, count, live), daemon=True).start()\n        return self._j({"msg": f"запущено: {count} замк., {\'живой\' if live else \'dry-run\'}"})',
 '        try: calm = max(1.0, min(5.0, float(q.get("calm", "1.5"))))\n        except ValueError: calm = 1.5\n'
 '        if self.path == "/finish": threading.Thread(target=run_finish, args=(world, ally, count, live), daemon=True).start()\n'
 '        else: threading.Thread(target=run_queue, args=(world, ally, count, live, "prep" if self.path == "/prep" else "full", calm), daemon=True).start()\n'
 '        what = {"/start": "полный круг", "/prep": f"заготовки (спокойно x{calm})", "/finish": "добить"}[self.path]\n'
 '        return self._j({"msg": f"запущено: {what}, {count} шт., {\'живой\' if live else \'dry-run\'}"})'),
])
