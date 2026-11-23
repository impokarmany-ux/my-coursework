# -*- coding: utf-8 -*-
# Офлайн-разбор кадров шлюза (stargate, порт 17681) из pcap. В сеть ничего не шлёт.
# Запуск: python analysis\gateway_pcap_parse.py gog1.pcap
import struct, sys, json, base64
sys.stdout.reconfigure(encoding="utf-8")
PORT = 17681
b = open(sys.argv[1] if len(sys.argv) > 1 else "gog1.pcap", "rb").read()
lt = struct.unpack("<I", b[20:24])[0]
off = 24; streams = {}
while off + 16 <= len(b):
    ts, us, cl, ol = struct.unpack("<IIII", b[off:off+16]); d = b[off+16:off+16+cl]; off += 16 + cl
    ip = d[16:] if lt == 113 else d[14:]          # SLL или Ethernet
    if len(ip) < 20 or ip[0] >> 4 != 4 or ip[9] != 6: continue
    ihl = (ip[0] & 15) * 4; t = ip[ihl:]; sp, dp = struct.unpack(">HH", t[:4])
    if PORT not in (sp, dp): continue
    pl = ip[ihl + (t[12] >> 4) * 4: struct.unpack(">H", ip[2:4])[0]]
    cport = sp if dp == PORT else dp
    s = streams.setdefault(cport, {"C": b"", "S": b""})
    s["C" if dp == PORT else "S"] += pl
for cport, s in streams.items():
    print(f"=== соединение клиентского порта {cport}")
    for side in "SC":
        buf = s[side]; o = 0
        while o + 18 <= len(buf):
            h = buf[o:o+32]; ln = int.from_bytes(h[4:7], "little")
            hl = 32 if h[0] < 0x10 else 18          # управляющие кадры: 32 байта, данные (0x71): 18
            kind = {1: "ping", 2: "pong", 3: "handshake", 5: "handshake-ack", 0x71: "data(шифр)"}.get(h[0], hex(h[0]))
            line = f"{side} off={o} {kind} len={ln}"
            if h[0] == 3:
                js = json.loads(buf[o+hl:o+hl+ln])
                if "Cipher" in js: js["Cipher"] = f"<{len(base64.b64decode(js['Cipher']))} байт>"
                line += " " + json.dumps(js, ensure_ascii=False)
            print(line); o += hl + ln
