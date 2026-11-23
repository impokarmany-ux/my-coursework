# -*- coding: utf-8 -*-
# ШАГ 3. Порт 13021 — чат FunPlus RTM. Формат Thrift (бинарный), НЕ шифрован:
# [4 байта длина][0f ff 00 01][номер запроса][... имя метода, напр. "auth", "get_history_msg_new" ...]
from common import load_flows, stream
k, (c2s, s2c), ev = stream(load_flows(), 13021, 1000)
print('Соединение:', k)
def frames(buf):
    i = 0
    while i + 4 <= len(buf):
        n = int.from_bytes(buf[i:i+4], 'big'); yield buf[i+4:i+4+n]; i += 4 + n
for name, buf in (('клиент->сервер', c2s), ('сервер->клиент', s2c)):
    print('==', name)
    for f in list(frames(buf))[:6]:
        m = f[22:22+int.from_bytes(f[18:22],'big')] if len(f) > 22 else b''
        print(' длина %6d  метод=%r  текст=%r' % (len(f), m, f[22:100]))
