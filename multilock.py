# -*- coding: utf-8 -*-
"""multilock.py: cross-process file lock (Windows msvcrt / posix fcntl) + atomic JSON helpers."""
import json, os, time, contextlib
BASE = os.path.dirname(os.path.abspath(__file__)); LOCKDIR = os.path.join(BASE, "logs", "locks"); os.makedirs(LOCKDIR, exist_ok=True)

@contextlib.contextmanager
def locked(name, timeout=120):
    path = os.path.join(LOCKDIR, name + ".lock"); f = open(path, "a+b"); t0 = time.time()
    try:
        if os.name == "nt":
            import msvcrt
            while True:
                try: f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1); break
                except OSError:
                    if time.time() - t0 > timeout: raise TimeoutError("lock " + name)
                    time.sleep(0.05)
        else:
            import fcntl; fcntl.flock(f, fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt; f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError: pass
        f.close()

def jload(path, default):
    try: return json.load(open(path, encoding="utf-8-sig"))
    except Exception: return default

def jsave(path, obj):
    tmp = path + ".tmp%d" % os.getpid()
    json.dump(obj, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, path)
