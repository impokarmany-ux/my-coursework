from pathlib import Path
src = Path("15_new_account.py").read_text(encoding="utf-8")
# show UA_MODEL_POOL through generate_device_ids start
i = src.find("UA_MODEL_POOL")
j = src.find("def mask(")
print(src[i:j])
print("==== check_ip ====")
i = src.find("def check_ip")
print(src[i:i+900])
print("==== generate ====")
i = src.find("def generate_device_ids")
print(src[i:i+1200])
