# -*- coding: utf-8 -*-
"""Патч 15: пул моделей + time_zone из VPN geo."""
from pathlib import Path
import re

p = Path("15_new_account.py")
src = p.read_text(encoding="utf-8")

# 1) imports: add zoneinfo
if "from zoneinfo import ZoneInfo" not in src:
    src = src.replace(
        "from datetime import datetime\n",
        "from datetime import datetime, timezone as dt_timezone\nfrom zoneinfo import ZoneInfo\n",
        1,
    )

# 2) IP_CHECK_URL + helpers after DEFAULT_TIME_ZONE / replace UA pool
old_pool = '''UA_MODEL_POOL = [
    ("SM-G975N", "Samsung Galaxy S10+"),
    ("SM-G991B", "Samsung Galaxy S21"),
    ("SM-A525F", "Samsung Galaxy A52"),
    ("V2338A", "vivo (эмуляторный UA из mitm)"),
    ("Pixel 6", "Google Pixel 6"),
    ("Redmi Note 11", "Xiaomi Redmi Note 11"),
]
'''

new_pool = r'''# один HTTPS-запрос через прокси: IP + страна + IANA timezone (не ipify — там нет geo)
IP_CHECK_URL = "https://ipapi.co/json/"

# пул правдоподобных моделей; UA/FPX согласованы с форматом реальных запросов игры
DEVICE_MODEL_POOL = [
    {
        "model": "SM-G975N",
        "manufacturer": "samsung",
        "marketing_name": "Galaxy S10+",
        "os_version": "9",
        "api_level": 28,
        "build_id": "PQ3B.190801.07081204",
        "board": "beyond2qlte",
        "device_codename": "beyond2",
        "incremental": "G975NKSU5FVF1",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G975N Build/PQ3B.190801.07081204)",
        "fpx_user_agent": "FPX/Android(v28/Android/beyond2qlte/beyond2:9/PQ3B.190801.07081204/G975NKSU5FVF1:user/release-keys)",
    },
    {
        "model": "SM-G991B",
        "manufacturer": "samsung",
        "marketing_name": "Galaxy S21",
        "os_version": "12",
        "api_level": 31,
        "build_id": "SP1A.210812.016",
        "board": "o1s",
        "device_codename": "o1s",
        "incremental": "G991BXXU5CVH7",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 12; SM-G991B Build/SP1A.210812.016)",
        "fpx_user_agent": "FPX/Android(v31/Android/o1s/o1s:12/SP1A.210812.016/G991BXXU5CVH7:user/release-keys)",
    },
    {
        "model": "SM-A525F",
        "manufacturer": "samsung",
        "marketing_name": "Galaxy A52",
        "os_version": "11",
        "api_level": 30,
        "build_id": "RP1A.200720.012",
        "board": "a52q",
        "device_codename": "a52q",
        "incremental": "A525FXXU4BVA2",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A525F Build/RP1A.200720.012)",
        "fpx_user_agent": "FPX/Android(v30/Android/a52q/a52q:11/RP1A.200720.012/A525FXXU4BVA2:user/release-keys)",
    },
    {
        "model": "V2338A",
        "manufacturer": "vivo",
        "marketing_name": "vivo (как в mitm)",
        "os_version": "9",
        "api_level": 28,
        "build_id": "PQ3A.190705.09211140",
        "board": "graceltexx",
        "device_codename": "gracelte",
        "incremental": "G9700FXXU1APFO",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 9; V2338A Build/PQ3A.190705.09211140)",
        "fpx_user_agent": "FPX/Android(v28/Android/graceltexx/gracelte:9/PQ3A.190705.09211140/G9700FXXU1APFO:user/release-keys)",
    },
    {
        "model": "Pixel 6",
        "manufacturer": "Google",
        "marketing_name": "Pixel 6",
        "os_version": "13",
        "api_level": 33,
        "build_id": "TQ3A.230805.001",
        "board": "oriole",
        "device_codename": "oriole",
        "incremental": "10161073",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 6 Build/TQ3A.230805.001)",
        "fpx_user_agent": "FPX/Android(v33/Android/oriole/oriole:13/TQ3A.230805.001/10161073:user/release-keys)",
    },
    {
        "model": "Redmi Note 11",
        "manufacturer": "Xiaomi",
        "marketing_name": "Redmi Note 11",
        "os_version": "11",
        "api_level": 30,
        "build_id": "RKQ1.211001.001",
        "board": "spes",
        "device_codename": "spes",
        "incremental": "V13.0.5.0.RGCMIXM",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 11; Redmi Note 11 Build/RKQ1.211001.001)",
        "fpx_user_agent": "FPX/Android(v30/Android/spes/spes:11/RKQ1.211001.001/V13.0.5.0.RGCMIXM:user/release-keys)",
    },
]

def iana_to_offset(iana: str) -> str:
    """Europe/Amsterdam -> +01:00 (с учётом DST на сейчас)."""
    dt = datetime.now(ZoneInfo(iana))
    off = dt.utcoffset()
    if off is None:
        raise ValueError(f"нет смещения для {iana}")
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 3600:02d}:{(total % 3600) // 60:02d}"

def pick_model(name: str | None = None) -> dict:
    if name:
        for m in DEVICE_MODEL_POOL:
            if m["model"].lower() == name.lower() or m["marketing_name"].lower() == name.lower():
                return dict(m)
        raise SystemExit(f"STOP: модель {name!r} не в пуле")
    return dict(random.choice(DEVICE_MODEL_POOL))
'''

if old_pool not in src:
    raise SystemExit("UA_MODEL_POOL block not found")
src = src.replace(old_pool, new_pool, 1)

# remove old IP_CHECK_URL if still near top (duplicate after new)
# old line: IP_CHECK_URL = "https://api.ipify.org?format=json"
src = src.replace('IP_CHECK_URL = "https://api.ipify.org?format=json"\n', "", 1)

# 3) replace generate_device_ids signature and body start to include model
old_gen = '''def generate_device_ids(*, time_zone: str = DEFAULT_TIME_ZONE, media_source: str = DEFAULT_MEDIA_SOURCE,
                       empty_push: bool = True) -> dict:
    """Свежие идентификаторы на один замок. Форматы сверены с mitm / АНОНИМНОСТЬ.md.
    Значения сюда не логируем — только длины/формы при проверке."""
    now = datetime.now()
    ms = int(time.time() * 1000)  # 13 цифр до ~2286 г.
    right19 = secrets.randbelow(10**19 - 10**18) + 10**18  # ровно 19 цифр
    gaid = str(uuid.uuid4())  # UUID с дефисами, как GAID
    ids = {
        "device_id": uuid.uuid4().hex,                 # 32 hex
        "android_id": secrets.token_hex(8),            # 16 hex
        "origin_guid": uuid.uuid4().hex,               # 32 hex
        "guid": uuid.uuid4().hex,                      # 32 hex
        "gaid": gaid,                                  # UUID v4
        "appsflyer_id": f"{ms}-{right19}",             # <13мс>-<19цифр>
        "anon_id": "XZ" + str(uuid.uuid4()),           # XZ + UUID = 38
        "time_zone": time_zone,
        "media_source": media_source,
'''

new_gen = '''def generate_device_ids(*, time_zone: str = DEFAULT_TIME_ZONE, media_source: str = DEFAULT_MEDIA_SOURCE,
                       empty_push: bool = True, model_name: str | None = None) -> dict:
    """Свежие идентификаторы + модель на один замок. Форматы сверены с mitm / АНОНИМНОСТЬ.md.
    Значения сюда не логируем — только длины/формы при проверке."""
    now = datetime.now()
    ms = int(time.time() * 1000)  # 13 цифр до ~2286 г.
    right19 = secrets.randbelow(10**19 - 10**18) + 10**18  # ровно 19 цифр
    gaid = str(uuid.uuid4())  # UUID с дефисами, как GAID
    model = pick_model(model_name)
    ids = {
        "device_id": uuid.uuid4().hex,                 # 32 hex
        "android_id": secrets.token_hex(8),            # 16 hex
        "origin_guid": uuid.uuid4().hex,               # 32 hex
        "guid": uuid.uuid4().hex,                      # 32 hex
        "gaid": gaid,                                  # UUID v4
        "appsflyer_id": f"{ms}-{right19}",             # <13мс>-<19цифр>
        "anon_id": "XZ" + str(uuid.uuid4()),           # XZ + UUID = 38
        "time_zone": time_zone,
        "media_source": media_source,
        # модель / UA (согласованный комплект)
        "model": model["model"],
        "manufacturer": model["manufacturer"],
        "marketing_name": model["marketing_name"],
        "os_version": model["os_version"],
        "api_level": model["api_level"],
        "build_id": model["build_id"],
        "board": model["board"],
        "device_codename": model["device_codename"],
        "incremental": model["incremental"],
        "user_agent": model["user_agent"],
        "fpx_user_agent": model["fpx_user_agent"],
'''

if old_gen not in src:
    raise SystemExit("generate_device_ids block not found")
src = src.replace(old_gen, new_gen, 1)

# 4) apply_fresh_ids — добавить поля модели
old_apply = '''def apply_fresh_ids(device: dict, ids: dict) -> dict:
    """Накладывает сгенерированные id на шаблон профиля (константы app_id/key/UA остаются)."""
    for k in ("device_id", "android_id", "origin_guid", "guid", "gaid",
              "appsflyer_id", "anon_id", "time_zone", "media_source",
              "fp_device_id", "fp_device_token", "push_message", "fp_registered"):
        if k in ids:
            device[k] = ids[k]
    return device
'''

new_apply = '''def apply_fresh_ids(device: dict, ids: dict) -> dict:
    """Накладывает сгенерированные id + модель/UA на шаблон (app_id/key остаются)."""
    for k in ("device_id", "android_id", "origin_guid", "guid", "gaid",
              "appsflyer_id", "anon_id", "time_zone", "media_source",
              "fp_device_id", "fp_device_token", "push_message", "fp_registered",
              "model", "manufacturer", "marketing_name", "os_version", "api_level",
              "build_id", "board", "device_codename", "incremental",
              "user_agent", "fpx_user_agent"):
        if k in ids:
            device[k] = ids[k]
    return device
'''

if old_apply not in src:
    raise SystemExit("apply_fresh_ids not found")
src = src.replace(old_apply, new_apply, 1)

# 5) check_ip with geo
old_check = '''def check_ip(self, phase):
        if not self.live:
            print(f"[ip] {phase}: dry-run — проверка не выполняется (сеть не трогаем)")
            return
        try:
            r = self.s.get(IP_CHECK_URL, timeout=15)
            ip = r.json().get("ip", "")
        except Exception as e:
            raise SystemExit(f"STOP: проверка IP не удалась ({type(e).__name__}) — fail closed")
        if not ip:
            raise SystemExit("STOP: IP не определён — fail closed")
        if ip == BAD_IP:
            raise SystemExit(f"STOP: домашний IP {BAD_IP} ({phase})")
        # фиксируем IP первой фазы; смена (не на домашний) только логируется
        if getattr(self, "first_ip", None) is None:
            self.first_ip = ip
        note = "" if ip == self.first_ip else f" (сменился, первый был {self.first_ip})"
        print(f"[ip] {phase}: выход {ip}{note}")
'''

new_check = '''def check_ip(self, phase):
        """Один запрос через прокси: IP + страна/timezone. Не логируем IP в вызывающем отчёте."""
        if not self.live:
            print(f"[ip] {phase}: dry-run — проверка не выполняется (сеть не трогаем)")
            return None
        try:
            r = self.s.get(IP_CHECK_URL, timeout=15)
            js = r.json()
        except Exception as e:
            raise SystemExit(f"STOP: проверка IP/geo не удалась ({type(e).__name__}) — fail closed")
        ip = js.get("ip") or js.get("query") or ""
        if not ip:
            raise SystemExit("STOP: IP не определён — fail closed")
        if ip == BAD_IP:
            raise SystemExit(f"STOP: домашний IP ({phase})")
        country = js.get("country_code") or js.get("country") or ""
        iana = js.get("timezone") or js.get("time_zone") or ""
        tz_off = None
        if iana:
            try:
                tz_off = iana_to_offset(iana)
            except Exception as e:
                print(f"[ip] {phase}: timezone IANA есть, offset не посчитан ({type(e).__name__})")
        geo = {"country": country, "iana": iana, "time_zone": tz_off, "ok_not_home": True}
        self.last_geo = geo
        if getattr(self, "first_ip", None) is None:
            self.first_ip = ip
        changed = "" if ip == self.first_ip else " (сменился)"
        # в консоль — только факт и страна/пояс, без значения IP
        print(f"[ip] {phase}: выход НЕ домашний{changed}; country={country or '?'}; "
              f"tz={tz_off or iana or '?'}")
        return geo
'''

if old_check not in src:
    raise SystemExit("check_ip not found")
src = src.replace(old_check, new_check, 1)

p.write_text(src, encoding="utf-8")
print("partial patch ok, len", len(src))
