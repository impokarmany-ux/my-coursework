import re
def patch(fn, pairs, enc="utf-8"):
    t = open(fn, encoding="utf-8-sig").read()
    bom = open(fn, "rb").read(3) == b"\xef\xbb\xbf"
    for old, new in pairs:
        assert t.count(old) == 1, (fn, old[:60], t.count(old))
        t = t.replace(old, new)
    open(fn, "w", encoding="utf-8-sig" if bom else "utf-8").write(t)
    print("patched", fn)

patch("16_run_full.py", [
('ap.add_argument("--speedup-45-maxwait", dest="sp45_wait", type=int, default=1200)\n',
 'ap.add_argument("--speedup-45-maxwait", dest="sp45_wait", type=int, default=1200)\n'
 '# split: --to = до какого idx (не включая) - режим заготовки; --calm = растянутые паузы с разбросом; --list-steps = офлайн показать шаги и выйти\n'
 'ap.add_argument("--to", dest="to", type=float, default=1e9)\n'
 'ap.add_argument("--calm", type=float, default=1.0)\n'
 'ap.add_argument("--list-steps", dest="list_steps", action="store_true")\n'),
('    rest = last_send[0] + g - time.time()\n    if rest > 0: time.sleep(rest)\n\nplan =',
 '    if a.calm > 1: g = g * random.uniform(a.calm * 0.8, a.calm * 1.25) + random.uniform(0, 2 * a.calm)\n'
 '    rest = last_send[0] + g - time.time()\n    if rest > 0: time.sleep(rest)\n\nplan ='),
('steps = [s for s in steps if s["idx"] >= a.frm]\n',
 'steps = [s for s in steps if a.frm <= s["idx"] < a.to]\n'),
('log(f"старт (новый замок), шагов {len(steps)}, seq {seq}, лог {LOG}")\n',
 'if a.list_steps:\n'
 '    def _g(s, k=1.0):\n'
 '        gs = s.get("gap_s")\n'
 '        g = gs["median"] if gs else ((s.get("delay_s_min") or 0.5) + ((s.get("delay_s_min") or 0.5) + (s.get("delay_s_max") or 1.0)) / 2) / 2\n'
 '        return g * k + (a.calm if a.calm > 1 else 0)\n'
 '    for s in steps: print(f"   idx {s[\'idx\']}: {s[\'op\']} (list)")\n'
 '    k = 1.0 if a.calm <= 1 else a.calm * 1.025\n'
 '    print(f"LIST: шагов {len(steps)}, idx {steps[0][\'idx\'] if steps else None}..{steps[-1][\'idx\'] if steps else None}, оценка пауз ~{sum(_g(s, k) for s in steps)/60:.1f} мин (calm {a.calm}), альянс-команд {sum(1 for s in steps if s[\'op\'].startswith(\'Alliance:\'))}")\n'
 '    sys.exit(0)\n'
 'log(f"старт (новый замок), шагов {len(steps)}, seq {seq}, лог {LOG}")\n'),
])

patch("new_castle_full.py", [
('ap.add_argument("--dry-delay"',
 '# split: full = как раньше; prep = заготовка до замка 9 без альянса (финиш - castle_finish.py)\n'
 'ap.add_argument("--mode", choices=["full", "prep"], default="full")\n'
 'ap.add_argument("--calm", type=float, default=1.0, help="prep: множитель пауз (>1 = спокойно, со случайным разбросом)")\n'
 'ap.add_argument("--dry-delay"'),
('a = ap.parse_args(); PROXY = a.proxy\n',
 'a = ap.parse_args(); PROXY = a.proxy\nFINISH_FROM = 114.9   # первый шаг финиша: поиск альянса (115 вступление, 116 замок 9->10, 118 выход)\n'
 'RUN_EXTRA = ["--to", str(FINISH_FROM), "--calm", str(a.calm)] if a.mode == "prep" else []\n'),
('    log(f"DRY-RUN: сеть не используется. мир {a.world}, альянс {a.alliance}")\n',
 '    log(f"DRY-RUN: сеть не используется. режим {a.mode}, мир {a.world}, альянс {a.alliance}" + (f", calm {a.calm}, до idx {FINISH_FROM}" if a.mode == "prep" else ""))\n'),
('    N = 123\n', '    N = 115 if a.mode == "prep" else 123\n'),
('    r = subprocess.run([sys.executable, "_dry45.py"]',
 '    if a.mode == "prep": log(f"[archive] был бы статус castle9_ready, finish_from {FINISH_FROM} (dry - не пишем)")\n'
 '    r = subprocess.run([sys.executable, "_dry45.py"]'),
('"--world", str(a.world), "--speedup-45"], False)\n',
 '"--world", str(a.world), "--speedup-45"] + RUN_EXTRA, False)\n'),
('castle_archive.save(bundle, a.world, a.alliance, "castle10" if rc == 0 else "unfinished", {"run_rc": rc, "total_s": round(time.time() - T0)})',
 'ok_status = "castle9_ready" if a.mode == "prep" else "castle10"\n'
 '    mfrom = re.search(r"--from ([\\d.]+)", out)\n'
 '    castle_archive.save(bundle, a.world, None if a.mode == "prep" else a.alliance, ok_status if rc == 0 else "unfinished",\n'
 '                        {"run_rc": rc, "total_s": round(time.time() - T0), "mode": a.mode, "calm": a.calm,\n'
 '                         "finish_from": FINISH_FROM if a.mode == "prep" else None, "resume_from": float(mfrom.group(1)) if (rc and mfrom) else None})'),
])

patch("castle_archive.py", [
('    if acc: shutil.copy2(acc, os.path.join(d, "account.json"))\n',
 '    if acc:\n        shutil.copy2(acc, os.path.join(d, "account.json"))\n'
 '        dp = json.load(open(acc, encoding="utf-8")).get("device_profile")\n'
 '        dpp = os.path.join(BASE, "mitm", os.path.basename(dp)) if dp else None\n'
 '        if dpp and os.path.exists(dpp): shutil.copy2(dpp, os.path.join(d, "device.json"))\n'),
('if __name__ == "__main__":',
 'def ready(kingdom, status="castle9_ready"):\n'
 '    """castles of this kingdom with given status, oldest first (only with login data)."""\n'
 '    return [r for r in _registry() if r.get("status") == status and int(r.get("kingdom") or 0) == int(kingdom) and r.get("has_account")]\n\n'
 'def counts(status="castle9_ready"):\n'
 '    c = {}\n'
 '    for r in _registry():\n'
 '        if r.get("status") == status: c[str(r.get("kingdom"))] = c.get(str(r.get("kingdom")), 0) + 1\n'
 '    return c\n\n'
 'if __name__ == "__main__":'),
('        for r in _registry(): print(',
 '        print("castle9_ready per kingdom:", counts())\n        for r in _registry(): print('),
])
