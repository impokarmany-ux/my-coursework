from pathlib import Path
p=Path("15_new_account.py"); s=p.read_text(encoding="utf-8")
old='''    if str(j.get("status")) not in ("1", "1.0"):
        raise SystemExit'''
new='''    if str(j.get("status")) not in ("1", "1.0"):
        (ROOT / "logs" / f"passport_fail_{method}_{int(time.time())}.json").write_text(
            json.dumps(mask_obj(j), ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit'''
assert old in s; s=s.replace(old,new,1)
old2='''    print("   -> ok", j.get("ok"), "uid", pay.get("uid"), "city_ids", pay.get("city_ids"))'''
new2='''    kd = {k: pay.get(k) for k in ("kingdom_id", "kingdom", "world_id", "server_id") if k in pay}
    print("   -> ok", j.get("ok"), "kingdom_fields", kd)
    (ROOT / "logs" / f"init_resp_k{kingdom_id}_{int(time.time())}.json").write_text(
        json.dumps({"ok": j.get("ok"), "kingdom_fields": kd, "payload_keys": sorted(pay.keys())}, ensure_ascii=False, indent=2), encoding="utf-8")'''
assert old2 in s; s=s.replace(old2,new2,1)
p.write_text(s,encoding="utf-8")
import py_compile; py_compile.compile(str(p),doraise=True); print("ok")
