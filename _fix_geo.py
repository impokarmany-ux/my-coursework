from pathlib import Path
for fn in ("15_new_account.py",):
    p = Path(fn)
    src = p.read_text(encoding="utf-8")
    src2 = src.replace(
        'IP_CHECK_URL = "https://ipapi.co/json/"',
        'IP_CHECK_URL = "https://ipinfo.io/json"  # ip+country+timezone одним ответом через прокси',
        1,
    )
    # also accept country from ipinfo (field "country" is code like TR)
    # check_ip already does: country = js.get("country_code") or js.get("country")
    # timezone field exists on ipinfo
    if src2 == src:
        raise SystemExit("URL not replaced")
    p.write_text(src2, encoding="utf-8")
    print("updated", fn)

# harden check_ip: if error field or no ip, STOP clearly
src = Path("15_new_account.py").read_text(encoding="utf-8")
old = '''        ip = js.get("ip") or js.get("query") or ""
        if not ip:
            raise SystemExit("STOP: IP не определён — fail closed")
'''
new = '''        if js.get("error") or js.get("status") == "fail":
            raise SystemExit(f"STOP: geo API ошибка — fail closed ({js.get(\"reason\") or js.get(\"message\") or js.get(\"error\")})")
        ip = js.get("ip") or js.get("query") or ""
        if not ip:
            raise SystemExit("STOP: IP не определён — fail closed")
'''
if old not in src:
    raise SystemExit("ip parse block missing")
Path("15_new_account.py").write_text(src.replace(old, new, 1), encoding="utf-8")
import py_compile
py_compile.compile("15_new_account.py", doraise=True)
print("15 OK")
