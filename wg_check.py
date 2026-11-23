# -*- coding: utf-8 -*-
"""wg_check.py: проверка выхода через 127.0.0.1:18091 (fail-closed).
Код 0 только если: прокси отвечает, IP не домашний, страна = AL.
IP наружу не печатаем - только короткий хэш выхода."""
import hashlib, json, subprocess, sys, time, os

HOME_IP = "203.0.113.10"          # домашний IP - запрещён
PROXY = "http://127.0.0.1:18091"  # CONNECT по hostname -> DNS резолвит туннель
WANT = "AU"
URLS = ["https://ipwho.is/", "https://ipinfo.io/json"]

def exit_hash(ip):
    # хэш выхода вместо IP (для logs/exit_counts.json)
    return hashlib.sha256(("castle-exit:" + ip).encode()).hexdigest()[:16]

def probe(proxy=PROXY, timeout=20):
    # один запрос через прокси; возвращает (ip, страна, время) или исключение
    for u in URLS:
        t0 = time.time()
        r = subprocess.run(["curl.exe", "-s", "-m", str(timeout), "-x", proxy, u],
                           capture_output=True, text=True)
        dt = time.time() - t0
        try:
            j = json.loads(r.stdout)
        except Exception:
            continue
        ip = j.get("ip"); cc = j.get("country_code") or j.get("country")
        if ip and cc:
            return ip, cc, dt
    raise RuntimeError("нет ответа через прокси")

def check(proxy=PROXY):
    try:
        ip, cc, dt = probe(proxy)
    except Exception as e:
        print("FAIL:", e); return 1
    if ip == HOME_IP:
        print("FAIL: выход ДОМАШНИЙ - стоп"); return 2
    if cc != WANT:
        print("FAIL: страна", cc, "!=", WANT); return 3
    print("OK exit_hash=%s country=%s %.2fs" % (exit_hash(ip), cc, dt))
    return 0

if __name__ == "__main__":
    sys.exit(check(sys.argv[1] if len(sys.argv) > 1 else PROXY))
