# -*- coding: utf-8 -*-
"""
15_new_account.py — создание НОВОГО замка без игры (passport new_account + init с kingdom_id).
По умолчанию DRY-RUN: в сеть НЕ уходит ни один байт (ни passport, ни игра, ни проверка IP).
12_login.py не меняется — берём из него функции (подпись, тело passport, конверт init).

Цепочка (как в записях flows_3rounds / flows_inject5):
  0) [только live] проверка выходного IP через ту же цепочку прокси (Surfshark), иначе стоп
  1) passport new_account  (подпись FP 2064:HMAC, НОВЫЙ guid, поля в порядке клиента)
     -> новый fpid + auth_token
  2) пауза 4-5 с, game: versionDiff2 + manifest (из manifest берём ak -> AES ключ)
  3) пауза до 8-9 с от new_account: init {kingdom_id:837, is_old_account:1, fpid:новый}
     -> новый uid
  4) пауза ~28-30 с (в записи игра перелогинивается): token_login + init {kingdom_id:0}
  5) сохранить mitm/session_bundle_<uid>.json (seq_next=1) для плановика с idx 0

Идентификаторы устройства (АНОНИМНОСТЬ.md):
  на каждый новый замок генерируются свежие device_id / android_id / origin_guid / guid /
  gaid / appsflyer_id / anon_id; push.device_token пустой; fp_* — офлайн-заглушки формата
  (живую регистрацию FunPlus deviceprofile/v4 + decdevicetoken не делаем без отдельного «да»).
  Профиль пишется в mitm/device_<время>.json и ссылка кладётся в bundle.

getServersState НЕ шлём: в записи игра шлёт его из сессии ФЕРМЫ (до new_account
своей сессии ещё нет), а ферме команды слать запрещено.

Сеть (требование: не светить IP ноутбука):
  * только requests.Session(trust_env=False) + обязательный --proxy (HTTP CONNECT по имени
    хоста -> DNS резолвит прокси, не ноутбук). Без --proxy в live — отказ.
  * перед каждой live-фазой проверка IP; 203.0.113.10 или ошибка -> стоп (fail closed).
  * ферма: fpid 182070973 / uid 71206420 — немедленный стоп при любом совпадении.
"""
import os
import argparse, importlib.util, json, re, secrets, sys, time, uuid, random
from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import parse_qsl

ROOT = Path(__file__).resolve().parent
MITM = ROOT / "mitm"

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, ROOT / fn)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

lg = _load("login12", "12_login.py")   # подпись, тело passport, конверт init
sc = lg.sc                              # AES/ak из 10_send_cmd.py

FARM_FPID = "182070973"
FARM_UID = 71206420
BAD_IP = "203.0.113.10"
SURFSHARK_IP = "203.0.113.20"
KINGDOM = 837
SECRET_KEYS = ("auth_token", "session_key", "token", "session_id", "Authorization", "Fp-Device-Token", "ak", "chat_token")
ID_KEYS = (
    "device_id", "device", "android_id", "origin_guid", "guid", "gaid",
    "appsflyer_id", "anon_id", "fp_device_id", "fp_device_token", "gateway_connid",
    "gateway_finger_print", "fpid", "uid",
)

# дефолты атрибуции (не идентификаторы устройства; вынесены в CLI)
DEFAULT_MEDIA_SOURCE = "googleadwords_int"
DEFAULT_TIME_ZONE = "+02:00"  # Europe/Kiev; опция: согласовать со страной VPN (см. --time-zone)

# правдоподобный пул моделей — только предложение; User-Agent профиля НЕ меняем без согласования
# один HTTPS-запрос через прокси: IP + страна + IANA timezone (не ipify — там нет geo)
IP_CHECK_URL = "https://ipinfo.io/json"  # ip+country+timezone одним ответом через прокси

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

def mask(v):
    s = str(v)
    return s if len(s) < 10 else f"{s[:4]}…({len(s)})"

def mask_obj(o):
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

def farm_guard(*vals):
    # любая встреча фермы -> аварийный стоп
    for v in vals:
        if str(v) in (FARM_FPID, str(FARM_UID)):
            raise SystemExit(f"STOP: обнаружена ферма ({v}) — запрещено")

def human_sleep(lo, hi, live, what):
    d = random.uniform(lo, hi)
    print(f"  пауза {d:.1f} с ({what})" + ("" if live else " — dry-run, не ждём"))
    if live:
        time.sleep(d)

def _placeholder_fp_token() -> str:
    """Офлайн-заглушка формата Fp-Device-Token (~89, base64-алфавит, старт 'B').
    НЕ валидный FunPlus-токен — живая регистрация: deviceprofile/v4 → decdevicetoken."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    # 1 + 86 + 2 = 89
    return "B" + "".join(secrets.choice(alphabet) for _ in range(86)) + "=="

def generate_device_ids(*, time_zone: str = DEFAULT_TIME_ZONE, media_source: str = DEFAULT_MEDIA_SOURCE,
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
        # FunPlus: формат как в записях, но fp_registered=false — сервер их не выдавал
        "fp_device_id": now.strftime("%Y%m%d%H%M") + secrets.token_hex(25),  # 12+50=62
        "fp_device_token": _placeholder_fp_token(),    # ~89
        "fp_registered": False,
        "push_message": {
            "device_type": "phone",
            "channel_type": "aws",
            "device_token": "" if empty_push else "",
            "platform_type": "gcm",
        },
        "generated_at": now.isoformat(timespec="seconds"),
        "note": "офлайн-генерация 15_new_account; fp_* не зарегистрированы у FunPlus; push пустой",
    }
    return ids

def apply_fresh_ids(device: dict, ids: dict) -> dict:
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

def save_device_profile(device: dict) -> Path:
    """mitm/device_<YYYYMMDD_HHMMSS>.json — постоянные id этого замка."""
    MITM.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = MITM / f"device_{ts}_{os.getpid()}.json"  # unique per parallel castle
    # не тащим служебное _init_extra в файл профиля
    dump = {k: v for k, v in device.items() if not k.startswith("_")}
    path.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def validate_id_formats(device: dict) -> list[str]:
    """Офлайн-проверка форматов. Возвращает список ошибок (пустой = ок)."""
    errs = []
    checks = [
        ("device_id", r"^[0-9a-f]{32}$", device.get("device_id", "")),
        ("android_id", r"^[0-9a-f]{16}$", device.get("android_id", "")),
        ("origin_guid", r"^[0-9a-f]{32}$", device.get("origin_guid", "")),
        ("guid", r"^[0-9a-f]{32}$", device.get("guid", "")),
        ("gaid", r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
         str(device.get("gaid", "")).lower()),
        ("appsflyer_id", r"^\d{13}-\d{19}$", device.get("appsflyer_id", "")),
        ("anon_id", r"^XZ[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
         device.get("anon_id", "")),
        ("fp_device_id", r"^\d{12}[0-9a-f]{50}$", device.get("fp_device_id", "")),
    ]
    for name, pat, val in checks:
        if not re.fullmatch(pat, str(val)):
            errs.append(f"{name}: формат не совпал (len={len(str(val))})")
    tok = device.get("fp_device_token", "")
    if not (isinstance(tok, str) and len(tok) == 89 and tok.startswith("B")):
        errs.append(f"fp_device_token: ожидали len=89 старт B, got len={len(tok)}")
    pm = device.get("push_message") or {}
    if pm.get("device_token") not in ("", None):
        errs.append("push_message.device_token: должен быть пустым (не чужой FCM)")
    return errs

def compare_init_keys(params: dict) -> tuple[bool, list, list]:
    """Сверка ключей init с реальным снимком mitm/_3r_all.json (если есть)."""
    ref_path = MITM / "_3r_all.json"
    if not ref_path.exists():
        return True, [], ["нет mitm/_3r_all.json — сверка ключей пропущена"]
    raw = json.loads(ref_path.read_text(encoding="utf-8"))

    def find_params(o):
        if isinstance(o, dict):
            if "appsflyer_id" in o and "fp_device_id" in o:
                return o
            for v in o.values():
                r = find_params(v)
                if r:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = find_params(v)
                if r:
                    return r
        return None

    ref = find_params(raw) or {}
    ours = set(params.keys())
    theirs = set(ref.keys())
    missing = sorted(theirs - ours)
    extra = sorted(ours - theirs)
    # is_old_account появляется только на первом init — допустимо как extra
    extra = [k for k in extra if k != "is_old_account"]
    return (not missing and not extra), missing, extra

class Net:
    """Единственный путь в сеть. Только через прокси, без env, без fallback."""
    def __init__(self, live, proxy):
        self.live = live
        self.s = None
        if live:
            if not proxy:
                raise SystemExit("STOP: --live без --proxy запрещён (прямой выход = IP ноутбука)")
            import requests
            self.s = requests.Session()
            self.s.trust_env = False                      # игнор HTTP(S)_PROXY/NO_PROXY из окружения
            self.s.proxies = {"http": proxy, "https": proxy}  # https -> CONNECT host:443, DNS на прокси
            if proxy.startswith("socks5://"):
                raise SystemExit("STOP: используй socks5h:// (DNS через прокси), не socks5://")

    def check_ip(self, phase):
        """Один запрос через прокси: IP + страна/timezone. Не логируем IP в вызывающем отчёте."""
        if not self.live:
            print(f"[ip] {phase}: dry-run — проверка не выполняется (сеть не трогаем)")
            return None
        try:
            r = self.s.get(IP_CHECK_URL, timeout=15)
            js = r.json()
        except Exception as e:
            raise SystemExit(f"STOP: проверка IP/geo не удалась ({type(e).__name__}) — fail closed")
        if js.get("error") or js.get("status") == "fail":
            raise SystemExit(f"STOP: geo API ошибка — fail closed ({js.get("reason") or js.get("message") or js.get("error")})")
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

    def post(self, url, data, headers, timeout=30):
        if not self.live:
            raise RuntimeError("dry-run: сеть запрещена")
        return self.s.post(url, data=data, headers=headers, timeout=timeout)

def show_req(name, url, headers, body_text):
    print(f"[{name}] POST {url}")
    for k, v in headers.items():
        print(f"   H {k}: {mask(v) if k in SECRET_KEYS else v}")
    print("   B", body_text)

def captured_new_accounts():
    # 4 захваченных new_account: тело + заголовок Authorization (для сверки подписи и порядка полей)
    from mitmproxy import io
    out = []
    for fn in ("flows_3rounds.mitm", "flows_inject5.mitm"):
        p = MITM / fn
        if not p.exists():
            continue
        with open(p, "rb") as f:
            for fl in io.FlowReader(f).stream():
                if not hasattr(fl, "request"):
                    continue
                b = (fl.request.raw_content or b"").decode("utf-8", "replace")
                if "gog-passport" in fl.request.pretty_host and b.startswith("method=new_account"):
                    out.append((fn, b, fl.request.headers.get("Authorization", "")))
    return out

def passport_call(net, device, method, auth_token=None):
    body = lg.build_passport_body(method, device, auth_token=auth_token, session_id="")
    headers = lg.passport_headers(device, body)
    shown = dict(parse_qsl(body, keep_blank_values=True))
    show_req(f"passport {method}", lg.PASSPORT_URL, headers, json.dumps(mask_obj(shown), ensure_ascii=False))
    assert headers["Authorization"] == lg.passport_sign(body)
    if not net.live:
        print("   DRY-RUN: подпись посчитана, НЕ отправлено")
        return {"status": 1, "data": {"fpid": "DRYFPID", "auth_token": "DRY_AUTH_TOKEN_XXXX", "is_new": method == "new_account"}}
    r = net.post(lg.PASSPORT_URL, body.encode("utf-8"), headers)
    j = r.json()
    d = j.get("data") or {}
    print("   ->", r.status_code, json.dumps(mask_obj(j), ensure_ascii=False)[:300])
    if str(j.get("status")) not in ("1", "1.0"):
        (ROOT / "logs" / f"passport_fail_{method}_{int(time.time())}.json").write_text(
            json.dumps(mask_obj(j), ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"STOP: passport {method} status={j.get('status')}")
    farm_guard(d.get("fpid"))
    return j

def api_plain(net, env, name):
    # versionDiff2/manifest идут открытым JSON (как у клиента)
    body = json.dumps(env, separators=(",", ":"))
    hdr = {"Content-Type": "application/json", "User-Agent": "UnityPlayer/2022.3.27f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
           "Accept": "*/*", "Accept-Encoding": "gzip", "X-Unity-Version": "2022.3.27f1"}
    show_req(name, sc.API_URL, hdr, body)
    if not net.live:
        print("   DRY-RUN: НЕ отправлено")
        return None
    r = net.post(sc.API_URL, body.encode(), hdr)
    j = r.json()
    if j.get("ok") != 1:
        raise SystemExit(f"STOP: {name} ok={j.get('ok')}")
    return j

def api_init(net, aes_key, session_key, fpid, device, kingdom_id, is_new):
    env = lg.build_init_envelope(session_key, fpid, device, kingdom_id=kingdom_id)
    if is_new:
        env["params"]["is_old_account"] = 1   # как в первом init после new_account в записи
    env["params"].update(device.get("_init_extra") or {})  # поля, как их шлёт игра (gateway_* и т.п.)
    show_req(f"api init kingdom_id={kingdom_id}", sc.API_URL, {"Content-Type": "AES-ECB(ak)"},
             json.dumps(mask_obj(env["params"]), ensure_ascii=False)[:700])
    farm_guard(fpid)
    plain = json.dumps(env, separators=(",", ":"), ensure_ascii=False).encode()
    cipher = sc.encrypt_api_body(plain, aes_key)
    if not net.live:
        print(f"   DRY-RUN: plain {len(plain)} B -> cipher {len(cipher)} B, НЕ отправлено")
        return {"ok": 1, "payload": {"uid": 0, "token": ""}, "_params": env["params"]}
    r = net.post(sc.API_URL, cipher, sc.HEADERS, timeout=45)
    raw = r.content
    j = json.loads(raw if raw[:1] == b"{" else sc.decrypt_api_body(raw, aes_key))
    pay = j.get("payload") or {}
    kd = {k: pay.get(k) for k in ("kingdom_id", "kingdom", "world_id", "server_id") if k in pay}
    print("   -> ok", j.get("ok"), "kingdom_fields", kd)
    (ROOT / "logs" / f"init_resp_k{kingdom_id}_{int(time.time())}.json").write_text(
        json.dumps({"ok": j.get("ok"), "kingdom_fields": kd, "payload_keys": sorted(pay.keys())}, ensure_ascii=False, indent=2), encoding="utf-8")
    if j.get("ok") != 1:
        # сохраняем полный ответ сервера (токены замаскированы) для разбора
        (ROOT / "logs" / f"init_fail_{int(time.time())}.json").write_text(
            json.dumps(mask_obj(j), ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"STOP: init ok={j.get('ok')} msg={json.dumps(mask_obj(j), ensure_ascii=False)[:400]}")
    farm_guard(pay.get("uid"))
    return j

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser(description="новый замок без игры (по умолчанию dry-run)")
    ap.add_argument("--device", type=Path, default=lg.DEFAULT_DEVICE,
                    help="шаблон device_profile_*.json (константы app_id/key/UA); id перегенерируются")
    ap.add_argument("--kingdom", type=int, default=KINGDOM)
    ap.add_argument("--live", action="store_true", help="РЕАЛЬНЫЕ запросы — только после «да» пользователя")
    ap.add_argument("--proxy", default=None, help="http://127.0.0.1:18081 (vpnproxy -> Surfshark)")
    ap.add_argument("--reuse-fpid", default=None, help="не делать new_account; взять fpid+auth_token из mitm/new_account_<fpid>.json")
    ap.add_argument("--init-extra", type=Path, default=None,
                    help="JSON с полями init (только gateway_* и пр.; НЕ копировать фермовые gaid/appsflyer/anon/push)")
    ap.add_argument("--media-source", default=DEFAULT_MEDIA_SOURCE,
                    help="params.media_source (атрибуция; не идентификатор устройства)")
    ap.add_argument("--time-zone", default=None,
                    help="params.time_zone (+02:00 …). Если не задан: при live — из geo VPN; "
                         "при dry-run — +02:00; если live и страну не узнать — STOP")
    ap.add_argument("--model", default=None,
                    help="модель из пула (SM-G975N, SM-G991B, SM-A525F, V2338A, 'Pixel 6', 'Redmi Note 11'); иначе случайная")
    ap.add_argument("--keep-device-ids", action="store_true",
                    help="НЕ генерировать свежие id — взять как в --device (опасно: связка с шаблоном/фермой)")
    ap.add_argument("--device-out", type=Path, default=None,
                    help="куда сохранить профиль (по умолчанию mitm/device_<время>.json)")
    a = ap.parse_args()
    net = Net(a.live, a.proxy)
    print("=== LIVE ===" if a.live else "=== DRY-RUN: сеть не используется ===")

    # устройство: шаблон констант + свежие id/модель на замок
    device = json.loads(a.device.read_text(encoding="utf-8"))
    device.pop("fpid", None); device.pop("uid", None)

    # time_zone: явный CLI > geo VPN (live) > дефолт dry-run; иначе STOP
    tz = a.time_zone
    if tz is None and a.live and not a.keep_device_ids and not a.reuse_fpid:
        geo0 = net.check_ip("geo/timezone до генерации профиля")
        if geo0 and geo0.get("time_zone"):
            tz = geo0["time_zone"]
            print(f"[tz] из VPN geo: {tz} (country={geo0.get('country') or '?'})")
        else:
            raise SystemExit("STOP: страну/пояс VPN не узнать — укажите --time-zone явно")
    if tz is None:
        tz = DEFAULT_TIME_ZONE
        if not a.live:
            print(f"[tz] dry-run: {tz} (VPN geo недоступен офлайн; задайте --time-zone при необходимости)")

    device_path = None
    if a.reuse_fpid:
        pass  # ids подставим ниже после чтения saved
    elif a.keep_device_ids:
        print("[ids] --keep-device-ids: свежие id НЕ генерируем (риск связки)")
        if "guid" not in device or not device["guid"]:
            device["guid"] = uuid.uuid4().hex
        if a.time_zone:
            device["time_zone"] = a.time_zone
    else:
        ids = generate_device_ids(time_zone=tz, media_source=a.media_source,
                                  empty_push=True, model_name=a.model)
        apply_fresh_ids(device, ids)
        ferrs = validate_id_formats(device)
        if ferrs:
            raise SystemExit("STOP: форматы id: " + "; ".join(ferrs))
        device_path = a.device_out or save_device_profile(device)
        if a.device_out:
            dump = {k: v for k, v in device.items() if not k.startswith("_")}
            a.device_out.parent.mkdir(parents=True, exist_ok=True)
            a.device_out.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding="utf-8")
            device_path = a.device_out
        print(f"[ids] свежий профиль: {device_path.name} model={device.get('model')} "
              f"os={device.get('os_version')} tz={device.get('time_zone')} "
              f"(fp_registered=false, push пустой)")

    for k in ("gateway_name", "gateway_finger_print", "gateway_connid"):
        print(f"[!] {k}: {'есть в профиле' if device.get(k) else 'НЕТ (уйдёт пустым) — источник: 17_gateway / --init-extra'}")

    # 1. сверка подписи на 4 захваченных new_account + порядок полей
    caps = captured_new_accounts()
    ok = sum(1 for _, b, h in caps if lg.passport_sign(b) == h)
    print(f"[sign] захваченные new_account: {ok}/{len(caps)} совпали")
    mine = [k for k, _ in parse_qsl(lg.build_passport_body("new_account", device), keep_blank_values=True)]
    if caps:
        theirs = [k for k, _ in parse_qsl(caps[0][1], keep_blank_values=True)]
        print("[order] порядок полей как в записи:", mine == theirs)
        if mine != theirs:
            raise SystemExit("STOP: порядок полей отличается")
    if caps and ok != len(caps):
        raise SystemExit("STOP: подпись не совпала")

    # 2. new_account
    extra = json.loads(a.init_extra.read_text(encoding="utf-8")) if a.init_extra else {}
    # защита: init-extra не должен затирать свежие id фермовыми
    for banned in ("gaid", "appsflyer_id", "anon_id", "push_message", "device", "android_id",
                   "fp_device_id", "origin_guid", "guid"):
        if banned in extra and not a.keep_device_ids:
            print(f"[ids] убран {banned} из --init-extra (не копируем чужие/фермовые)")
            extra.pop(banned, None)
    # time_zone / media_source: CLI главнее, если не keep
    if not a.keep_device_ids:
        extra.setdefault("time_zone", device.get("time_zone", a.time_zone))
        extra.setdefault("media_source", device.get("media_source", a.media_source))
        # гарантируем, что push из профиля (пустой) попадёт в params, если extra его убрал
        if "push_message" not in extra:
            extra["push_message"] = device.get("push_message")
        for fld in ("gaid", "appsflyer_id", "anon_id"):
            if fld not in extra and device.get(fld):
                extra[fld] = device[fld]
    device["_init_extra"] = extra

    if a.reuse_fpid:
        # режим повторного init: аккаунт уже есть, new_account НЕ шлём
        farm_guard(a.reuse_fpid)
        f = MITM / f"new_account_{a.reuse_fpid}.json"
        if not f.exists():
            raise SystemExit(f"STOP: нет сохранённого auth_token для fpid {a.reuse_fpid} ({f.name}) — новый аккаунт не создаём")
        saved = json.loads(f.read_text(encoding="utf-8"))
        fpid, auth = str(saved["fpid"]), saved["auth_token"]
        # если при создании сохранили device_profile — используем те же id
        dp = saved.get("device_profile")
        if dp:
            dpp = MITM / Path(dp).name if not Path(dp).is_file() else Path(dp)
            if dpp.exists():
                device = json.loads(dpp.read_text(encoding="utf-8"))
                device.pop("fpid", None); device.pop("uid", None)
                device_path = dpp
                device["_init_extra"] = extra
                print(f"[ids] reuse: загружен профиль {dpp.name}")
            else:
                device["guid"] = saved.get("guid", device.get("guid") or uuid.uuid4().hex)
        else:
            device["guid"] = saved.get("guid", device.get("guid") or uuid.uuid4().hex)
        pj = None
    else:
        net.check_ip("перед new_account")
        pj = passport_call(net, device, "new_account")
        fpid = str(pj["data"]["fpid"]); auth = pj["data"]["auth_token"]
        if net.live:
            # сохраняем локально (только на ноутбуке), чтобы можно было повторить init без нового аккаунта
            (MITM / f"new_account_{fpid}.json").write_text(json.dumps({
                "fpid": fpid, "auth_token": auth, "guid": device["guid"],
                "device_profile": device_path.name if device_path else None,
            }), encoding="utf-8")
    t_acc = time.time()

    # 3. versionDiff2 + manifest -> ak
    human_sleep(4.0, 5.0, a.live, "new_account -> versionDiff2 (в записи ~5 с)")
    api_plain(net, {"class": "call", "method": "versionDiff2", "params": {"os": "android", "channel": "google_gog", "version": "14.2.0"}}, "api versionDiff2")
    mj = api_plain(net, {"class": "call", "method": "manifest", "req_id": sc.make_req_id(), "params": {
        "client_version": "14.2.0", "client_lang": "ru", "os": "android", "client_full_version": "14.2.0.8514.0",
        "channel": "google_gog", "sys_lang": "ru-RU"}}, "api manifest")
    if a.live:
        m = re.search(r'"ak"\s*:\s*"([^"]+)"', json.dumps(mj))
        if not m: raise SystemExit("STOP: нет ak в manifest")
        key = sc.unwrap_ak(m.group(1))
    else:
        key = bytes.fromhex("00" * 16)  # фиктивный ключ для dry-run шифрования

    # 4. init с королевством
    if a.live:
        rest = 8.0 + random.uniform(0, 1.0) - (time.time() - t_acc)
        if rest > 0: time.sleep(rest)
    else:
        print("  пауза до 8-9 с от new_account — dry-run, не ждём")
    net.check_ip("перед init(создание)")
    ij = api_init(net, key, auth, fpid, device, a.kingdom, is_new=True)
    uid = int((ij.get("payload") or {}).get("uid") or 0)

    # офлайн-сверка структуры init
    if not a.live:
        params = ij.get("_params") or {}
        ok_keys, missing, extran = compare_init_keys(params)
        print(f"[init-check] ключи vs реальный init: ok={ok_keys} missing={missing} extra={extran}")
        ferrs = validate_id_formats({
            "device_id": params.get("device"),
            "android_id": params.get("android_id"),
            "origin_guid": device.get("origin_guid"),
            "guid": device.get("guid"),
            "gaid": params.get("gaid"),
            "appsflyer_id": params.get("appsflyer_id"),
            "anon_id": params.get("anon_id"),
            "fp_device_id": params.get("fp_device_id"),
            "fp_device_token": device.get("fp_device_token"),
            "push_message": params.get("push_message"),
        })
        if ferrs:
            print("[init-check] ФОРМАТЫ:", "; ".join(ferrs))
        else:
            print("[init-check] форматы device/android/gaid/appsflyer/anon/fp_device_id/push — ок")
        pm = params.get("push_message") or {}
        print(f"[init-check] push.device_token пустой={pm.get('device_token','')==''} "
              f"(в реальных mitm всегда был FCM ~142 — риск, см. отчёт)")

    # 5. перелогин как у игры
    human_sleep(28.0, 31.0, a.live, "перезапуск сессии (в записи ~28-30 с)")
    net.check_ip("перед перелогином")
    tj = passport_call(net, device, "token_login", auth_token=auth)
    auth2 = tj["data"].get("auth_token") or auth
    human_sleep(1.0, 2.0, a.live, "token_login -> init")
    ij2 = api_init(net, key, auth2, fpid, device, 0, is_new=False)
    pay = ij2.get("payload") or {}
    if a.live and int(pay.get("uid") or 0) != uid:
        raise SystemExit("STOP: uid после перелогина другой")

    # 6. bundle
    bundle = {"uid": uid, "fpid": fpid, "session_key": auth2, "token": pay.get("token"),
              "aes_key_hex": key.hex(), "client_version": "14.2.0", "seq_next": 1, "kingdom": a.kingdom,
              "guid": device["guid"], "plan_start_idx": 0, "note": "создано 15_new_account.py",
              "device_profile": device_path.name if device_path else None,
              "fp_registered": bool(device.get("fp_registered")),
              }
    out = MITM / f"session_bundle_{uid}.json"
    if not a.live:
        print(f"DRY-RUN: bundle НЕ записан (был бы mitm/session_bundle_<uid>.json), ключи: {list(bundle)}")
        if device_path:
            print(f"DRY-RUN: профиль устройства записан: {device_path.name}")
        return 0
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print("записан", out.name, "uid", uid, "королевство", a.kingdom,
          "device_profile", bundle.get("device_profile"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
