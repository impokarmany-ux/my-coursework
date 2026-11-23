# -*- coding: utf-8 -*-
"""
18_fp_device_register.py — РОВНО ОДНА пробная регистрация устройства FunPlus
(deviceprofile/v4 → decdevicetoken). Только через run_guarded + vpnproxy.
БЕЗ passport / init / замка / игровых команд. Без повторов.

Если шифрование fingerprint (ShuMei encode/compress/tn/ep) недоступно —
НЕ угадываем, СТОП до POST, fp_registered остаётся false.
"""
from __future__ import annotations
import importlib.util, json, sys, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
MITM = BASE / "mitm"
LOGS = BASE / "logs"
PROXY_EXPECT = "http://127.0.0.1:18081"
BAD = "203.0.113.10"
TZ = ZoneInfo("Europe/Kiev")
DEVPROXY = "https://devproxy.kingsgroupgames.com"
ORG = "xNxMh079HgFDeRkJE1qN"
SM_APP = "gog.funplus.sdk"

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, BASE / fn)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

    import os, requests
    proxy = os.environ.get("GOG_GUARDED")
    if not proxy:
        raise SystemExit("STOP: только через run_guarded.py --proxy …")
    if getattr(requests.Session.request, "__name__", "") != "_forced":
        raise SystemExit("STOP: Session.request не принудительный — нужен run_guarded")
    if proxy.startswith("socks5://") and not proxy.startswith("socks5h://"):
        raise SystemExit("STOP: нужен socks5h:// (DNS через прокси)")

    LOGS.mkdir(exist_ok=True)
    MITM.mkdir(exist_ok=True)
    stamp = datetime.now(TZ).strftime("%Y%m%d_%H%M%S")
    log_path = LOGS / f"fp_register_{stamp}.log"
    logf = open(log_path, "w", encoding="utf-8")

    def log(msg):
        line = f"[{datetime.now(TZ):%H:%M:%S}] {msg}"
        print(line); logf.write(line + "\n"); logf.flush()

    # --- 15 helpers: модель + id + geo ---
    na = _load("na15", "15_new_account.py")

    s = requests.Session()
    s.trust_env = False
    s.proxies = {"http": proxy, "https": proxy}

    # IP+geo одним запросом (тот же URL, что в 15)
    log("IP/geo check via proxy…")
    try:
        r = s.get(na.IP_CHECK_URL, timeout=20)
        js = r.json()
    except Exception as e:
        log(f"STOP: geo fail {type(e).__name__}")
        logf.close(); raise SystemExit(2)
    ip = js.get("ip") or js.get("query") or ""
    if not ip or ip == BAD:
        log("STOP: выход домашний или IP пуст")
        logf.close(); raise SystemExit(2)
    country = js.get("country_code") or js.get("country") or ""
    iana = js.get("timezone") or ""
    try:
        tz_off = na.iana_to_offset(iana) if iana else None
    except Exception:
        tz_off = None
    if not tz_off:
        log("STOP: пояс VPN не определён — нужен явный --time-zone (здесь не задан)")
        logf.close(); raise SystemExit(2)
    log(f"exit NOT home; country={country or '?'}; tz={tz_off}")

    # свежий профиль (офлайн-генерация id+модель)
    model = na.pick_model(None)
    ids = na.generate_device_ids(time_zone=tz_off, empty_push=True)
    # шаблон констант
    device = json.loads(na.lg.DEFAULT_DEVICE.read_text(encoding="utf-8"))
    device.pop("fpid", None); device.pop("uid", None)
    na.apply_fresh_ids(device, ids)
    device_path = MITM / f"device_{stamp}.json"
    dump = {k: v for k, v in device.items() if not k.startswith("_")}
    dump["fp_registered"] = False
    dump["fp_register_note"] = "ожидание deviceprofile/v4 — см. лог"
    device_path.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"profile written {device_path.name} model={device.get('model')} tz={tz_off}")

    # --- анализ шифрования fingerprint (офлайн по mitm) ---
    log("проверяю возможность собрать deviceprofile/v4…")
    # тело: organization, os, appId, encode=2, compress=3, data(base64), tn(344), ep(344)
    # data/tn/ep выдаёт нативный ShuMei SmAntiFraud SDK (com.ishumei… / SMSDK).
    # В dump.cs/apk нет открытого ключа и схемы plaintext — подобрать нельзя.
    can_encrypt = False
    reason = (
        "deviceprofile/v4 требует encode=2 compress=3 + поля data/tn/ep от ShuMei SDK; "
        "алгоритм/ключ офлайн не восстановлены — POST не отправляем (не угадываем)"
    )
    log(f"can_encrypt={can_encrypt}: {reason}")

    result = {
        "ts": datetime.now(TZ).isoformat(timespec="seconds"),
        "profile": device_path.name,
        "model": device.get("model"),
        "time_zone": tz_off,
        "country": country,
        "exit_not_home": True,
        "registration_attempted": False,
        "registration_ok": False,
        "http_status_deviceprofile": None,
        "http_status_decdevicetoken": None,
        "fp_registered": False,
        "stop_reason": reason,
        "log": log_path.name,
    }
    (LOGS / f"fp_register_{stamp}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if not can_encrypt:
        log("СТОП до POST: регистрация НЕ выполнена (нет шифрования fingerprint)")
        logf.close()
        raise SystemExit(3)

    # --- ниже живой путь (недостижим, пока can_encrypt=False) ---
    # ровно один POST deviceprofile/v4, затем один decdevicetoken; без повторов
    raise SystemExit("unreachable")

if __name__ == "__main__":
    raise SystemExit(main() or 0)
'''
Path('18_fp_device_register.py').write_text('''# -*- coding: utf-8 -*-
"""
18_fp_device_register.py — РОВНО ОДНА пробная регистрация устройства FunPlus
(deviceprofile/v4 → decdevicetoken). Только через run_guarded + vpnproxy.
БЕЗ passport / init / замка / игровых команд. Без повторов.

Если шифрование fingerprint (ShuMei encode/compress/tn/ep) недоступно —
НЕ угадываем, СТОП до POST, fp_registered остаётся false.
"""
from __future__ import annotations
import importlib.util, json, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
MITM = BASE / "mitm"
LOGS = BASE / "logs"
BAD = "203.0.113.10"
TZ = ZoneInfo("Europe/Kiev")

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, BASE / fn)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

    import os, requests
    proxy = os.environ.get("GOG_GUARDED")
    if not proxy:
        raise SystemExit("STOP: только через run_guarded.py --proxy …")
    if getattr(requests.Session.request, "__name__", "") != "_forced":
        raise SystemExit("STOP: Session.request не принудительный — нужен run_guarded")
    if proxy.startswith("socks5://") and not proxy.startswith("socks5h://"):
        raise SystemExit("STOP: нужен socks5h:// (DNS через прокси)")

    LOGS.mkdir(exist_ok=True)
    MITM.mkdir(exist_ok=True)
    stamp = datetime.now(TZ).strftime("%Y%m%d_%H%M%S")
    log_path = LOGS / f"fp_register_{stamp}.log"
    logf = open(log_path, "w", encoding="utf-8")

    def log(msg):
        line = f"[{datetime.now(TZ):%H:%M:%S}] {msg}"
        print(line); logf.write(line + "\n"); logf.flush()

    na = _load("na15", "15_new_account.py")

    s = requests.Session()
    s.trust_env = False
    s.proxies = {"http": proxy, "https": proxy}

    log("IP/geo check via proxy…")
    try:
        r = s.get(na.IP_CHECK_URL, timeout=20)
        js = r.json()
    except Exception as e:
        log(f"STOP: geo fail {type(e).__name__}")
        logf.close(); raise SystemExit(2)
    ip = js.get("ip") or js.get("query") or ""
    if not ip or ip == BAD:
        log("STOP: выход домашний или IP пуст")
        logf.close(); raise SystemExit(2)
    country = js.get("country_code") or js.get("country") or ""
    iana = js.get("timezone") or ""
    try:
        tz_off = na.iana_to_offset(iana) if iana else None
    except Exception:
        tz_off = None
    if not tz_off:
        log("STOP: пояс VPN не определён")
        logf.close(); raise SystemExit(2)
    log(f"exit NOT home; country={country or '?'}; tz={tz_off}")

    ids = na.generate_device_ids(time_zone=tz_off, empty_push=True)
    device = json.loads(na.lg.DEFAULT_DEVICE.read_text(encoding="utf-8"))
    device.pop("fpid", None); device.pop("uid", None)
    na.apply_fresh_ids(device, ids)
    device_path = MITM / f"device_{stamp}.json"
    dump = {k: v for k, v in device.items() if not k.startswith("_")}
    dump["fp_registered"] = False
    dump["fp_register_note"] = (
        "deviceprofile/v4 не отправлен: нет ShuMei encrypt (encode=2/compress=3/data/tn/ep)"
    )
    device_path.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"profile written {device_path.name} model={device.get('model')} tz={tz_off}")

    reason = (
        "deviceprofile/v4 требует тело ShuMei SDK (encode=2, compress=3, data, tn, ep); "
        "ключ/алгоритм офлайн не восстановлены — POST не шлём"
    )
    log(f"can_encrypt=False: {reason}")

    result = {
        "ts": datetime.now(TZ).isoformat(timespec="seconds"),
        "profile": device_path.name,
        "model": device.get("model"),
        "time_zone": tz_off,
        "country": country,
        "exit_not_home": True,
        "registration_attempted": False,
        "registration_ok": False,
        "http_status_deviceprofile": None,
        "http_status_decdevicetoken": None,
        "fp_registered": False,
        "stop_reason": reason,
        "log": log_path.name,
    }
    out_json = LOGS / f"fp_register_{stamp}.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"result {out_json.name}")
    log("СТОП до POST: регистрация НЕ выполнена")
    logf.close()
    raise SystemExit(3)

if __name__ == "__main__":
    raise SystemExit(main() or 0)
''', encoding='utf-8')
print('wrote 18')
import py_compile
py_compile.compile('18_fp_device_register.py', doraise=True)
print('18 compile OK')
