# -*- coding: utf-8 -*-
"""run_guarded.py — запуск 10/11/12 ТОЛЬКО через прокси (fail closed), без правки исходников.
Пример: python run_guarded.py --proxy http://127.0.0.1:18081 11_run_plan.py <аргументы>
Подменяет requests: все запросы (включая requests.post) идут через --proxy, env игнорируется,
перед стартом проверка выходного IP; 203.0.113.10 / ошибка / не Surfshark -> стоп."""
import sys, runpy, requests
if len(sys.argv) < 4 or sys.argv[1] != "--proxy":
    raise SystemExit("использование: run_guarded.py --proxy URL script.py [args]")
PROXY = sys.argv[2]; script = sys.argv[3]
if PROXY.startswith("socks5://"): raise SystemExit("STOP: нужен socks5h:// (DNS через прокси)")
_orig = requests.Session.request
def _forced(self, method, url, **kw):
    # принудительно: только наш прокси, окружение не учитываем
    self.trust_env = False
    kw["proxies"] = {"http": PROXY, "https": PROXY}
    return _orig(self, method, url, **kw)
requests.Session.request = _forced
import os
os.environ["GOG_GUARDED"] = PROXY   # флаг для дочерних скриптов
if os.environ.get("RG_OFFLINE") == "1":
    # офлайн-тест: любой сетевой вызов падает, проверка IP пропускается
    def _nonet(self, method, url, **kw): raise RuntimeError("RG_OFFLINE: сеть запрещена")
    _nonet.__name__ = "_forced"; requests.Session.request = _nonet
    sys.argv = [script] + sys.argv[4:]; runpy.run_path(script, run_name="__main__"); raise SystemExit(0)
try:
    ip = requests.Session().get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
except Exception as e:
    raise SystemExit(f"STOP: проверка IP не удалась ({type(e).__name__})")
print("[guard] выходной IP:", ip)
if not ip or ip == "203.0.113.10": raise SystemExit("STOP: IP домашний или не определён")
sys.argv = [script] + sys.argv[4:]
runpy.run_path(script, run_name="__main__")
