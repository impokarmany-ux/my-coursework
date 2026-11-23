# -*- coding: utf-8 -*-
"""wg_up.py: поднять wireproxy (127.0.0.1:18091) и проверить выход (fail-closed).
Без админа, без адаптеров/маршрутов: wireproxy - userspace WireGuard.
Если проверка не прошла - процесс убиваем, код != 0."""
import os, socket, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(BASE, "wg", "bin", "wireproxy.exe")
CONF = os.path.join(BASE, "wg", "wireproxy.conf")
LOG = os.path.join(BASE, "logs", "wireproxy.log")
PORT = 18091
sys.path.insert(0, BASE)
import wg_check

def listening():
    # слушает ли кто-то 127.0.0.1:18091
    s = socket.socket(); s.settimeout(1)
    try:
        s.connect(("127.0.0.1", PORT)); return True
    except OSError:
        return False
    finally:
        s.close()

def main():
    if listening():
        print("18091 уже слушает - только проверка")
        return wg_check.check()
    flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
    log = open(LOG, "ab")
    p = subprocess.Popen([EXE, "-c", CONF], stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    for _ in range(30):
        if listening(): break
        time.sleep(0.5)
    time.sleep(2)  # время на handshake
    rc = wg_check.check() if listening() else 1
    if rc != 0:
        print("FAIL - убиваю wireproxy (fail-closed)"); p.kill(); return rc
    print("wireproxy pid", p.pid, "работает")
    return 0

if __name__ == "__main__":
    sys.exit(main())
