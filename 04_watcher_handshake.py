# -*- coding: utf-8 -*-
# ШАГ 4. Порт 17681 — «Watcher» (push-канал игры). Разбираем заголовки кадров
# и печатаем рукопожатие (handshake) — оно открытым JSON, там ключ "Cipher".
import json, base64
from common import load_flows, stream
k, (c2s, s2c), ev = stream(load_flows(), 17681)

def parse(buf):
    """Кадр: байт0=тип, байты4..6=длина данных (little-endian), байт7=версия(2).
    Тип 3 (handshake), 1/2 (ping/pong), 5 (ack): заголовок 32 байта.
    Тип 0x71 (данные): заголовок 18 байт: ...'73 b8' + 4 байта (меняются, назначение не ясно)."""
    i, out = 0, []
    while i < len(buf):
        t = buf[i]; L = int.from_bytes(buf[i+4:i+7], 'little')
        hl = 18 if t == 0x71 else 32
        if t in (1, 2, 5): L = 0
        out.append((t, buf[i:i+hl], buf[i+hl:i+hl+L])); i += hl + L
    return out
if __name__ == '__main__':
    for name, buf in (('клиент->сервер', c2s), ('сервер->клиент', s2c)):
        print('==', name)
        for t, h, p in parse(buf):
            if t == 3:
                print(' HANDSHAKE:', p.decode())
            elif t == 0x71:
                print(' ДАННЫЕ флаги=%s длина=%4d хвост_заголовка=%s  данные: %s...' % (h[1:4].hex(), len(p), h[14:18].hex(), p[:24].hex()))
    hs = json.loads(parse(s2c)[0][2])
    key = base64.b64decode(hs['Cipher'])
    print('\nCipher (base64 -> %d байт): %s' % (len(key), key.hex()))
