# -*- coding: utf-8 -*-
# ШАГ 2. Для HTTPS (порт 443) трафик зашифрован TLS, но имя сайта (SNI)
# передаётся открытым текстом в первом пакете (ClientHello). Так узнаём, куда ходит игра.
import re
from common import load_flows
fl = load_flows(); names = {}
for k, v in fl.items():
    if k[1][1] == 443 and v['seg'][0]:
        first = sorted(v['seg'][0].items())[0][1][1]
        for n in re.findall(rb'[a-z0-9\-]+(?:\.[a-z0-9\-]+)+\.(?:com|net|io|org)', first):
            d = names.setdefault(k[1][0], [set(), 0]); d[0].add(n.decode()); d[1] += sum(v['bytes'])
for ip, (n, b) in sorted(names.items(), key=lambda x: -x[1][1]):
    print('%-16s %8d байт  %s' % (ip, b, ', '.join(sorted(n))))
