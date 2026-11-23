# -*- coding: utf-8 -*-
# Общие функции: чтение pcap и сборка TCP-потоков.
import dpkt, socket, collections, os
PCAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gog1.pcap')

def load_flows():
    """Читает pcap и группирует пакеты в «потоки» (соединения).
    Ключ: (протокол, сервер(ip,порт), клиент(ip,порт)). Сервер = сторона с меньшим портом."""
    flows = collections.defaultdict(lambda: {'bytes': [0, 0], 't0': None, 't1': None, 'seg': [{}, {}]})
    with open(PCAP, 'rb') as f:
        r = dpkt.pcap.Reader(f)
        for ts, buf in r:
            try:
                ip = dpkt.sll.SLL(buf).data   # tcpdump -i any => заголовок Linux SLL
            except Exception:
                continue
            if not isinstance(ip, dpkt.ip.IP):
                continue
            t = ip.data
            proto = 'tcp' if isinstance(t, dpkt.tcp.TCP) else 'udp' if isinstance(t, dpkt.udp.UDP) else None
            if not proto or 53 in (t.sport, t.dport):   # DNS пропускаем
                continue
            a = (socket.inet_ntoa(ip.src), t.sport); b = (socket.inet_ntoa(ip.dst), t.dport)
            srv, cli = (a, b) if a[1] < b[1] else (b, a)
            fl = flows[(proto, srv, cli)]
            d = 0 if a == cli else 1          # 0 = клиент->сервер, 1 = сервер->клиент
            fl['bytes'][d] += len(t.data)
            fl['t0'] = fl['t0'] or ts; fl['t1'] = ts
            if proto == 'tcp' and t.data:
                fl['seg'][d].setdefault(t.seq, (ts, bytes(t.data)))  # повторы (ретрансмиты) отбрасываем
    return flows

def stream(flows, port, min_bytes=200):
    """Возвращает склеенные байты обоих направлений для соединения с данным серверным портом."""
    for k, v in flows.items():
        if k[0] == 'tcp' and k[1][1] == port and sum(v['bytes']) > min_bytes:
            out = [b''.join(d for _, (ts, d) in sorted(v['seg'][i].items())) for i in (0, 1)]
            events = sorted((ts, i, d) for i in (0, 1) for _, (ts, d) in v['seg'][i].items())
            return k, out, events
