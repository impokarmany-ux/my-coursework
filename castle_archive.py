# -*- coding: utf-8 -*-
"""castle_archive.py: archive of bot-made castles (login data + kingdom) so we can return to them later.
castles/NNNN/ : bundle.json (session), account.json (fpid/auth_token/guid/device), info.json
castles/registry.jsonl : one line per castle. Nothing is sent to the network."""
import glob, json, os, shutil, sys
from datetime import datetime
BASE = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.join(BASE, "castles"); REG = os.path.join(ARCH, "registry.jsonl")

def _account_for(fpid):
    for f in glob.glob(os.path.join(BASE, "mitm", "new_account_*.json")):
        try:
            if str(json.load(open(f, encoding="utf-8")).get("fpid")) == str(fpid): return f
        except Exception: pass
    return None

def _registry():
    if not os.path.exists(REG): return []
    return [json.loads(l) for l in open(REG, encoding="utf-8") if l.strip()]

def save(bundle, world=None, alliance=None, status="castle10", extra=None):
    # parallel workers: registry numbering/writes under a cross-process lock
    from multilock import locked
    with locked("archive"): return _save(bundle, world, alliance, status, extra)

def _save(bundle, world=None, alliance=None, status="castle10", extra=None):
    os.makedirs(ARCH, exist_ok=True)
    b = json.load(open(bundle, encoding="utf-8"))
    reg = _registry()
    src = os.path.abspath(bundle)
    for r in reg:                       # same castle again -> update, keep number
        if r.get("bundle_src") == src:
            n = r["n"]; break
    else:
        n = max([r["n"] for r in reg] or [0]) + 1
    d = os.path.join(ARCH, "%04d" % n); os.makedirs(d, exist_ok=True)
    shutil.copy2(bundle, os.path.join(d, "bundle.json"))
    acc = _account_for(b.get("fpid"))
    if acc:
        shutil.copy2(acc, os.path.join(d, "account.json"))
        dp = json.load(open(acc, encoding="utf-8")).get("device_profile")
        dpp = os.path.join(BASE, "mitm", os.path.basename(dp)) if dp else None
        if dpp and os.path.exists(dpp): shutil.copy2(dpp, os.path.join(d, "device.json"))
    info = {"n": n, "saved": datetime.now().isoformat(timespec="seconds"),
            "kingdom": world if world is not None else b.get("kingdom"), "alliance": alliance,
            "status": status, "has_account": bool(acc), "bundle_src": src,
            "account_src": os.path.abspath(acc) if acc else None}
    if extra: info.update(extra)
    json.dump(info, open(os.path.join(d, "info.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    reg = [r for r in reg if r["n"] != n] + [info]
    with open(REG, "w", encoding="utf-8") as f:
        for r in sorted(reg, key=lambda r: r["n"]): f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("ARCHIVE: castle #%d saved (kingdom %s, status %s, login data %s)" % (n, info["kingdom"], status, "yes" if acc else "NO"), flush=True)
    return n

def ready(kingdom, status="castle9_ready"):
    """castles of this kingdom with given status, oldest first (only with login data)."""
    return [r for r in _registry() if r.get("status") == status and int(r.get("kingdom") or 0) == int(kingdom) and r.get("has_account")]

def counts(status="castle9_ready"):
    c = {}
    for r in _registry():
        if r.get("status") == status: c[str(r.get("kingdom"))] = c.get(str(r.get("kingdom")), 0) + 1
    return c

if __name__ == "__main__":
    if sys.argv[1:2] == ["backfill"]:      # bot castles made so far (not farm)
        for f in sorted(glob.glob(os.path.join(BASE, "mitm", "session_bundle_*.json")), key=os.path.getmtime):
            b = json.load(open(f, encoding="utf-8"))
            if "kingdom" in b and _account_for(b.get("fpid")):
                save(f, status="backfill")
    elif sys.argv[1:2] == ["list"]:
        print("castle9_ready per kingdom:", counts())
        for r in _registry(): print("#%d kingdom %s alliance %s status %s %s" % (r["n"], r["kingdom"], r["alliance"], r["status"], r["saved"]))
