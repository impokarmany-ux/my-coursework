# -*- coding: utf-8 -*-
"""
08_timeline.py — разбор полного MITM-цикла из папки bodies/.

Запуск (PowerShell):
  $env:PYTHONIOENCODING='utf-8'
  python E:\\protocol_analysis\\capture\\08_timeline.py

Что делает:
1) Читает все *.txt в mitm/bodies/
2) Строит таймлайн ключевых хостов (passport / FunPlus / gog-global)
3) Достаёт clear-JSON method/class/cmd
4) Находит все ak/ai
5) Отмечает переход JSON → octet-stream
6) Пишет краткий отчёт в stdout и сохраняет
   E:\\protocol_analysis\\capture\\mitm\\timeline_fullcycle.txt
"""
from __future__ import annotations

import json
import re
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

BODIES = Path(r"E:\protocol_analysis\capture\mitm\bodies")
OUT = Path(r"E:\protocol_analysis\capture\mitm\timeline_fullcycle.txt")

REDACT_KEYS = {
    "password", "passwd", "pwd", "token", "access_token", "refresh_token",
    "session_key", "session_token", "auth_token", "authorization",
    "sig", "sign", "signature", "secret", "client_secret",
    "id_token", "fp_token", "ticket", "sessionid", "session_id",
}

INTERESTING_HOSTS = (
    "gog-passport",
    "fp-passport",
    "fpcs-web",
    "popups-api",
    "dw-fpcs",
    "gog-global",
    "gog-news",
    "gog-store",
    "gog-community",
    "gog-achievement",
    "user-privacy",
    "devproxy",
)


def redact_obj(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            lk = str(k).lower()
            if any(r in lk for r in REDACT_KEYS):
                out[k] = "<REDACTED>"
            else:
                out[k] = redact_obj(v)
        return out
    if isinstance(o, list):
        return [redact_obj(x) for x in o]
    if isinstance(o, str) and len(o) > 80 and re.fullmatch(r"[A-Za-z0-9_\-\./=+]{40,}", o):
        return o[:8] + "…<REDACTED>"
    return o


def split_dump(text: str):
    sep = "--- body ---\n"
    if sep not in text:
        sep = "--- body ---\r\n"
    if sep in text:
        meta, body = text.split(sep, 1)
    else:
        meta, body = text, ""
    return meta, body.strip("\r\n")


def parse_meta(meta: str):
    info = {"method": None, "status": None, "url": None, "date": None, "ctype": None, "gdataver": None}
    for line in meta.splitlines():
        if line.startswith("METHOD "):
            info["method"] = line[7:].strip()
        elif line.startswith("STATUS "):
            info["status"] = line[7:].strip()
        elif line.startswith("URL "):
            info["url"] = line[4:].strip()
        elif line.lower().startswith("date:"):
            info["date"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("content-type:"):
            info["ctype"] = line.split(":", 1)[1].strip().lower()
        elif line.lower().startswith("gdataver:"):
            info["gdataver"] = line.split(":", 1)[1].strip()
    return info


def host_of(url: str | None, filename: str) -> str:
    if url:
        try:
            return urllib.parse.urlparse(url).hostname or ""
        except Exception:
            pass
    # fallback from filename: NNN_req_HOST__path.txt
    m = re.match(r"\d+_(?:req|resp)_([^_]+(?:\.[^_]+)*)__", filename)
    if m:
        return m.group(1)
    return ""


def extract_form_params(body: str) -> dict:
    if not body or body.startswith("{") or body.startswith("["):
        return {}
    # application/x-www-form-urlencoded or query-like
    try:
        qs = urllib.parse.parse_qs(body, keep_blank_values=True)
        return {k: (v[0] if len(v) == 1 else v) for k, v in qs.items()}
    except Exception:
        return {}


def try_json(body: str):
    if not body:
        return None
    s = body.strip()
    if not (s.startswith("{") or s.startswith("[")):
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


def walk_find(obj, keys=("ak", "ai", "uid", "kid", "fpid", "world_id", "server_id", "sid", "kingdom_id")):
    hits = []

    def walk(o, path=""):
        if isinstance(o, dict):
            present = {k: o[k] for k in keys if k in o}
            if present:
                hits.append((path or "/", present))
            for k, v in o.items():
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o[:50]):  # cap
                walk(v, f"{path}[{i}]")

    walk(obj)
    return hits


def api_methods_from_json(obj):
    """Collect class/method/cmd-like fields from clear JSON."""
    found = []

    def walk(o):
        if isinstance(o, dict):
            cls = o.get("class")
            meth = o.get("method")
            cmd = o.get("cmd") or o.get("command") or o.get("op")
            if meth or cmd:
                found.append({
                    "class": cls,
                    "method": meth,
                    "cmd": cmd,
                    "params_keys": sorted(list((o.get("params") or {}).keys()))[:30]
                    if isinstance(o.get("params"), dict) else None,
                })
            # sometimes batch: list under "requests" / "list"
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(obj)
    return found


def interesting(host: str) -> bool:
    h = host.lower()
    return any(x in h for x in INTERESTING_HOSTS)


def main():
    files = sorted(BODIES.glob("*.txt"))
    rows = []
    methods_counter = Counter()
    passport_events = []
    ak_events = []
    octet_first = None
    json_gog_req = 0
    octet_gog_req = 0
    clear_api_samples = []  # first N unique methods with file ref

    for p in files:
        kind = "req" if "_req_" in p.name else "resp"
        text = p.read_text(encoding="utf-8", errors="replace")
        meta, body = split_dump(text)
        info = parse_meta(meta)
        host = host_of(info["url"], p.name)
        idx = int(p.name.split("_", 1)[0])

        ctype = info["ctype"] or ""
        is_octet = "octet-stream" in ctype
        is_json_ct = "json" in ctype

        j = try_json(body) if not is_octet else None
        form = extract_form_params(body) if kind == "req" and j is None else {}

        # gog-global counters
        if kind == "req" and "gog-global" in host:
            if is_octet:
                octet_gog_req += 1
                if octet_first is None:
                    octet_first = (idx, p.name, info["date"])
            elif is_json_ct or (j is not None):
                json_gog_req += 1

        # methods
        meth_name = None
        if form.get("method"):
            meth_name = str(form.get("method"))
        if j is not None:
            for m in api_methods_from_json(j):
                label = None
                if m["method"]:
                    label = f'{m.get("class") or "-"}::{m["method"]}'
                elif m["cmd"]:
                    label = f'cmd={m["cmd"]}'
                if label:
                    methods_counter[label] += 1
                    if len(clear_api_samples) < 200 and label not in {s[0] for s in clear_api_samples}:
                        clear_api_samples.append((label, p.name, m))
                    if meth_name is None and m["method"]:
                        meth_name = m["method"]

        # ak/ai
        if j is not None:
            for path, present in walk_find(j):
                if "ak" in present and "ai" in present:
                    ak_events.append({
                        "idx": idx,
                        "file": p.name,
                        "date": info["date"],
                        "host": host,
                        "path": path,
                        "ai": present.get("ai"),
                        "ak": present.get("ak"),
                        "ids": {k: present[k] for k in present if k not in ("ak", "ai")},
                    })

        # passport / funplus timeline rows
        if interesting(host):
            # pull identity hints (redacted)
            ids = {}
            src = j if j is not None else form
            if isinstance(src, dict):
                for k in ("uid", "fpid", "kid", "world_id", "server_id", "sid", "kingdom_id",
                          "account_id", "role_id", "package_id", "game_id", "app_id",
                          "social_type", "login_type", "channel", "device_id"):
                    if k in src:
                        ids[k] = src[k]
                # nested payload
                if isinstance(src.get("payload"), dict):
                    for k in ("uid", "fpid", "kid", "world_id", "server_id", "sid"):
                        if k in src["payload"]:
                            ids[f"payload.{k}"] = src["payload"][k]
                params = src.get("params")
                if isinstance(params, dict):
                    for k in ("uid", "fpid", "kid", "world_id", "server_id"):
                        if k in params:
                            ids[f"params.{k}"] = params[k]

            # form method for passport
            if not meth_name and form.get("method"):
                meth_name = form["method"]

            row = {
                "idx": idx,
                "kind": kind,
                "host": host,
                "url": info["url"],
                "http": info["method"] or info["status"],
                "date": info["date"],
                "ctype": ctype[:40] if ctype else "",
                "method": meth_name,
                "octet": is_octet,
                "ids": ids,
                "file": p.name,
            }
            rows.append(row)

            if "passport" in host or "fp-passport" in host or "fpcs" in host:
                passport_events.append(row)

    # Build report
    lines = []
    def w(s=""):
        lines.append(s)

    w("# TIMELINE full-cycle MITM")
    w(f"bodies: {len(files)} files in {BODIES}")
    w(f"gog-global clear-JSON requests: {json_gog_req}")
    w(f"gog-global octet-stream requests: {octet_gog_req}")
    if octet_first:
        w(f"first octet-stream gog-global req: #{octet_first[0]} {octet_first[1]} date={octet_first[2]}")
    w()
    w("## ak/ai appearances (clear JSON responses)")
    for e in ak_events:
        ak = e["ak"]
        ak_show = ak if isinstance(ak, str) else repr(ak)
        w(f"- #{e['idx']:04d} ai={e['ai']} ak={ak_show} date={e['date']} file={e['file']}")
        if e["ids"]:
            w(f"    ids={e['ids']}")
    w(f"TOTAL ak/ai: {len(ak_events)}")
    uniq_ak = {e["ak"] for e in ak_events}
    w(f"UNIQUE ak values: {len(uniq_ak)}")
    w()

    w("## Passport / FunPlus key events (req only, methods)")
    for r in passport_events:
        if r["kind"] != "req":
            continue
        if not r["method"] and "gog-global" in r["host"]:
            continue
        w(f"- #{r['idx']:04d} {r['host']} method={r['method']} date={r['date']} ids={r['ids']} file={r['file']}")
    w()

    w("## Full interesting-host timeline (compact)")
    for r in rows:
        # skip pure octet spam after first few: show first octet + every 100th + non-octet
        if r["octet"] and "gog-global" in r["host"]:
            # show boundaries only: first 3 octet, and any with method
            pass
        flag = "OCTET" if r["octet"] else ("JSON" if "json" in (r["ctype"] or "") else r["ctype"] or "-")
        meth = r["method"] or "-"
        # shorten
        host_short = r["host"].replace(".kingsgroupgames.com", "").replace(".funplus.com", "")
        id_bits = ""
        if r["ids"]:
            # redact token-like
            safe = {k: ("<R>" if isinstance(v, str) and len(v) > 40 else v) for k, v in r["ids"].items()}
            id_bits = " " + str(safe)
        # Only print: passport/fp events always; gog-global only if JSON or has method or around ak
        if "gog-global" in r["host"]:
            if r["octet"]:
                continue  # too noisy; counted above
            if r["kind"] == "resp" and r["idx"] not in {e["idx"] for e in ak_events}:
                # print short resp only if method-ish body already counted via samples
                if not r["method"]:
                    continue
        w(f"{r['idx']:04d} {r['kind']:4s} {flag:12s} {host_short:28s} {meth:20s} {r['date'] or ''}{id_bits}")

    w()
    w("## Clear API method dictionary (class::method counts)")
    for label, cnt in methods_counter.most_common():
        w(f"  {cnt:4d}  {label}")
    w(f"UNIQUE labels: {len(methods_counter)}")
    w()

    # Compare two social_login / session_login blocks
    w("## Two FunPlus farm-entry candidates (fp-passport session_login)")
    fp_logins = [r for r in passport_events if r["kind"] == "req" and "fp-passport" in r["host"] and "session_login" in (r["url"] or r["file"])]
    for r in fp_logins:
        w(f"- #{r['idx']:04d} {r['url']} date={r['date']} file={r['file']}")
    social = [r for r in passport_events if r["kind"] == "req" and r["method"] == "social_login"]
    w("social_login on gog-passport:")
    for r in social:
        w(f"- #{r['idx']:04d} date={r['date']} ids={r['ids']} file={r['file']}")
    new_acc = [r for r in passport_events if r["kind"] == "req" and r["method"] == "new_account"]
    w("new_account:")
    for r in new_acc:
        w(f"- #{r['idx']:04d} date={r['date']} ids={r['ids']} file={r['file']}")
    tokens = [r for r in passport_events if r["kind"] == "req" and r["method"] == "token_login"]
    w("token_login:")
    for r in tokens:
        w(f"- #{r['idx']:04d} date={r['date']} ids={r['ids']} file={r['file']}")

    report = "\n".join(lines) + "\n"
    OUT.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
