# -*- coding: utf-8 -*-
from pathlib import Path
import re
p = Path("15_new_account.py")
src = p.read_text(encoding="utf-8")
# insert ID_KEYS after SECRET_KEYS line
if "ID_KEYS" in src:
    print("already has ID_KEYS")
else:
    src = src.replace(
        'SECRET_KEYS = ("auth_token", "session_key", "token", "session_id", "Authorization", "Fp-Device-Token", "ak", "chat_token")\n',
        'SECRET_KEYS = ("auth_token", "session_key", "token", "session_id", "Authorization", "Fp-Device-Token", "ak", "chat_token")\n'
        'ID_KEYS = (\n'
        '    "device_id", "device", "android_id", "origin_guid", "guid", "gaid",\n'
        '    "appsflyer_id", "anon_id", "fp_device_id", "fp_device_token", "gateway_connid",\n'
        '    "gateway_finger_print", "fpid", "uid",\n'
        ')\n',
        1,
    )
# replace mask_obj
pat = re.compile(r"def mask_obj\(o\):\n(?:.*\n)*?    return o\n\ndef farm_guard", re.M)
repl = '''def mask_obj(o):
    # маскируем токены и идентификаторы в выводе
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k in SECRET_KEYS and v:
                out[k] = mask(v)
            elif k in ID_KEYS and v not in ("", None):
                out[k] = mask(v)
            else:
                out[k] = mask_obj(v)
        return out
    if isinstance(o, list):
        return [mask_obj(x) for x in o]
    return o

def farm_guard'''
src2, n = pat.subn(repl, src, count=1)
if n != 1:
    raise SystemExit(f"mask_obj replace failed n={n}")
p.write_text(src2, encoding="utf-8")
import py_compile
py_compile.compile(str(p), doraise=True)
print("OK")
