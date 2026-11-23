from pathlib import Path
p = Path("18_fp_device_register.py")
src = p.read_text(encoding="utf-8")
old = '''    ip = js.get("ip") or js.get("query") or ""
    if not ip or ip == BAD:
        log("STOP: выход домашний или IP пуст")
        logf.close(); raise SystemExit(2)
'''
new = '''    if js.get("error") or js.get("status") == "fail":
        log(f"STOP: geo API ошибка ({js.get('reason') or js.get('message') or js.get('error')})")
        logf.close(); raise SystemExit(2)
    ip = js.get("ip") or js.get("query") or ""
    if not ip or ip == BAD:
        log("STOP: выход домашний или IP пуст")
        logf.close(); raise SystemExit(2)
'''
if old not in src:
    raise SystemExit("block missing")
p.write_text(src.replace(old, new, 1), encoding="utf-8")
print("18 patched")
