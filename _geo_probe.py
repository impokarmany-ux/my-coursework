import os, json, requests
# force proxy like run_guarded
PROXY = "http://127.0.0.1:18081"
_orig = requests.Session.request
def _forced(self, method, url, **kw):
    self.trust_env = False
    kw["proxies"] = {"http": PROXY, "https": PROXY}
    return _orig(self, method, url, **kw)
_forced.__name__ = "_forced"
requests.Session.request = _forced

s = requests.Session()
for url in [
    "https://ipapi.co/json/",
    "https://ipinfo.io/json",
    "http://ip-api.com/json/",
    "https://api.ipify.org?format=json",
]:
    try:
        r = s.get(url, timeout=20)
        js = r.json() if "json" in (r.headers.get("content-type","")) or r.text.strip().startswith("{") else {"raw": r.text[:200]}
        keys = list(js.keys()) if isinstance(js, dict) else type(js)
        # redact ip-like values
        safe = {}
        for k,v in (js.items() if isinstance(js,dict) else []):
            if any(x in k.lower() for x in ("ip","query","loc")):
                safe[k] = f"len={len(str(v))}" if v else "EMPTY"
            else:
                safe[k] = v
        print(url, "status", r.status_code, "keys", keys, "safe", safe)
    except Exception as e:
        print(url, "ERR", type(e).__name__, e)
