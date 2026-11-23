# -*- coding: utf-8 -*-
"""Патч _once_castle_gw.py: init_extra только gateway_* (+ опц. time_zone/media_source), без фермовых id."""
from pathlib import Path

p = Path("_once_castle_gw.py")
src = p.read_text(encoding="utf-8")

old = '''# init_extra: всё из init_extra_game.json, gateway_* — наши свежие
extra = json.loads((BASE / "mitm" / "init_extra_game.json").read_text(encoding="utf-8"))
extra["gateway_name"] = fields["gateway_name"]
extra["gateway_finger_print"] = str(fields["gateway_finger_print"])
extra["gateway_connid"] = str(fields["gateway_connid"])
'''

new = '''# init_extra: ТОЛЬКО gateway_* из живого 17_gateway.
# gaid/appsflyer/anon/push НЕ копируем из init_extra_game.json — их генерит 15_new_account.
# media_source/time_zone — параметры 15 (CLI); здесь не подмешиваем фермовые.
extra = {
    "gateway_name": fields["gateway_name"],
    "gateway_finger_print": str(fields["gateway_finger_print"]),
    "gateway_connid": str(fields["gateway_connid"]),
}
'''

if old not in src:
    raise SystemExit("STOP: блок init_extra не найден — проверь файл")
p.write_text(src.replace(old, new, 1), encoding="utf-8")
print("patched _once_castle_gw.py")
# verify
src2 = p.read_text(encoding="utf-8")
assert "init_extra_game.json" not in src2 or "НЕ копируем" in src2
assert "gaid" not in src2.split("extra = {")[1].split("}")[0]
print("verify ok")
