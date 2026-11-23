from pathlib import Path
assert Path("15_new_account.py.bak_ids").exists()
assert Path("_once_castle_gw.py.bak_ids").exists()
src = Path("15_new_account.py").read_text(encoding="utf-8")
assert "generate_device_ids" in src and "ID_KEYS" in src
gw = Path("_once_castle_gw.py").read_text(encoding="utf-8")
assert "НЕ копируем" in gw
assert 'init_extra_game.json").read_text' not in gw
print("OK")
print("device template still passed to 15:", "device_profile_98566384" in gw)
for line in gw.splitlines():
    if "init_extra_game" in line:
        print("mention:", line.strip()[:100])
