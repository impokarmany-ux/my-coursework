from pathlib import Path
p = Path("15_new_account.py")
src = p.read_text(encoding="utf-8")

# argparse --time-zone default None + --model
old = '''    ap.add_argument("--media-source", default=DEFAULT_MEDIA_SOURCE,
                    help="params.media_source (атрибуция; не идентификатор устройства)")
    ap.add_argument("--time-zone", default=DEFAULT_TIME_ZONE,
                    help="params.time_zone; можно согласовать со страной VPN (+02:00 по умолчанию Europe/Kiev)")
    ap.add_argument("--keep-device-ids", action="store_true",
                    help="НЕ генерировать свежие id — взять как в --device (опасно: связка с шаблоном/фермой)")
'''
new = '''    ap.add_argument("--media-source", default=DEFAULT_MEDIA_SOURCE,
                    help="params.media_source (атрибуция; не идентификатор устройства)")
    ap.add_argument("--time-zone", default=None,
                    help="params.time_zone (+02:00 …). Если не задан: при live — из geo VPN; "
                         "при dry-run — +02:00; если live и страну не узнать — STOP")
    ap.add_argument("--model", default=None,
                    help="модель из пула (SM-G975N, SM-G991B, SM-A525F, V2338A, 'Pixel 6', 'Redmi Note 11'); иначе случайная")
    ap.add_argument("--keep-device-ids", action="store_true",
                    help="НЕ генерировать свежие id — взять как в --device (опасно: связка с шаблоном/фермой)")
'''
if old not in src:
    raise SystemExit("argparse block not found")
src = src.replace(old, new, 1)

# replace device generation block
old2 = '''    # устройство: шаблон констант + свежие id на замок (если не --keep-device-ids / reuse с профилем)
    device = json.loads(a.device.read_text(encoding="utf-8"))
    device.pop("fpid", None); device.pop("uid", None)

    device_path = None
    if a.reuse_fpid:
        # при reuse: если в new_account_*.json есть device_profile — грузим его (те же id)
        pass  # ids подставим ниже после чтения saved
    elif a.keep_device_ids:
        print("[ids] --keep-device-ids: свежие id НЕ генерируем (риск связки)")
        if "guid" not in device or not device["guid"]:
            device["guid"] = uuid.uuid4().hex
    else:
        ids = generate_device_ids(time_zone=a.time_zone, media_source=a.media_source, empty_push=True)
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
        print(f"[ids] свежий профиль: {device_path.name} (fp_registered=false, push пустой)")
        print("[ids] User-Agent/модель из шаблона НЕ меняли (пул предложен в отчёте; смена — по согласованию)")
'''

new2 = '''    # устройство: шаблон констант + свежие id/модель на замок
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
'''

if old2 not in src:
    raise SystemExit("device gen block not found")
src = src.replace(old2, new2, 1)

p.write_text(src, encoding="utf-8")
import py_compile
py_compile.compile(str(p), doraise=True)
print("compile OK")
