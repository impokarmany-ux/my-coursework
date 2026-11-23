# -*- coding: utf-8 -*-
# ШАГ 5. Пробуем расшифровать данные Watcher.
# Наблюдение 1: у разных сообщений ОДИНАКОВЫЕ начала шифротекста => гамма (keystream)
#   одна и та же для каждого сообщения (сбрасывается на каждом кадре), не «катится» по потоку.
# Проверка 2: простой XOR с ключом Cipher (повтор 70 байт) — даёт мусор.
# Проверка 3: если открытый текст — JSON (ASCII), для каждой позиции должен найтись байт гаммы,
#   делающий ВСЕ сообщения печатными. Почти везде таких нет => внутри не ASCII
#   (скорее protobuf или сжатие), либо шифр сложнее XOR (RC4/AES-CTR и т.п.).
import json, base64
from common import load_flows, stream
from importlib import import_module
w = import_module('04_watcher_handshake')
fr = [f for f in w.parse(w.s2c) if f[0] == 0x71]
key = base64.b64decode(json.loads(w.parse(w.s2c)[0][2])['Cipher'])
a, b = fr[0][2], fr[3][2]
same = next(i for i in range(min(len(a), len(b))) if a[i] != b[i])
print('Сообщения 1 и 4 совпадают в первых %d байтах шифротекста' % same)
x = bytes(c ^ key[i % len(key)] for i, c in enumerate(a))
print('XOR с Cipher, сообщение 1:', x[:60])
small = [f[2] for f in fr if f[1][3] == 0x25]
n = min(map(len, small))
ok = [sum(1 for k in range(256) if all(32 <= (m[j] ^ k) < 127 for m in small)) for j in range(n)]
print('Позиций, где возможен ASCII: %d из %d' % (sum(1 for c in ok if c), n))
