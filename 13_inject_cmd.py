# -*- coding: utf-8 -*-
"""
13_inject_cmd.py - положить команду в очередь inject.py (бот на живой игре).

Примеры:
  python 13_inject_cmd.py --uid 98566384 City:upgradeObject "{\"gold\":0,\"city_id\":98566384,\"instant\":true,\"auto\":false,\"building_id\":2}"
  python 13_inject_cmd.py --uid 98566384 Prophase:collectCityAllRewards "{\"type\":\"ruin\",\"uid\":98566384}"

Скрипт ждёт ответа (до --wait секунд) и печатает его. Сам он ничего в сеть не шлёт:
шлёт mitmdump с inject.py, через игру/VPN окна.
"""
import argparse, json, os, sys, time

BOX = r"E:\protocol_analysis\capture\mitm"
INBOX, OUTBOX = os.path.join(BOX, "inject_inbox"), os.path.join(BOX, "inject_outbox")
sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("op", help="например City:upgradeObject")
ap.add_argument("args", nargs="?", default="null", help="JSON-объект аргументов")
ap.add_argument("--uid", type=int, required=True, help="uid замка - защита от чужого аккаунта")
ap.add_argument("--wait", type=float, default=60)
a = ap.parse_args()

args = json.loads(a.args)
if args is not None and not isinstance(args, dict):
    sys.exit("args должен быть JSON-объектом (как в игре), не строкой")
os.makedirs(INBOX, exist_ok=True)
name = f"{int(time.time()*1000)}.json"
tmp = os.path.join(INBOX, name + ".tmp")
json.dump({"op": a.op, "args": args, "uid": a.uid}, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
os.replace(tmp, os.path.join(INBOX, name))   # атомарно, чтобы аддон не прочёл половину
print(f"в очереди: {a.op} {json.dumps(args, ensure_ascii=False)}")

res = os.path.join(OUTBOX, name)
t0 = time.time()
while time.time() - t0 < a.wait:
    if os.path.exists(res):
        print(json.dumps(json.load(open(res, encoding="utf-8")), ensure_ascii=False, indent=1)[:3000])
        sys.exit(0)
    time.sleep(0.3)
print("ответа нет: игра ещё не отправила ни одного commit (нечем взять seq) или mitmdump не запущен")
