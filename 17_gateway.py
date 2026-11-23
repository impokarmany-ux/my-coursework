# -*- coding: utf-8 -*-
"""
17_gateway.py — клиент шлюза (stargate / WatcherSDK).

Получает gateway_name, gateway_finger_print, gateway_connid для init.

Режимы:
  --dry-run     офлайн: разбирает gog1.pcap, собирает HandshakeOut и сверяет байты с игрой
  --live        ЖИВОЕ подключение (запрещено без отдельного «да» пользователя)

Защита:
  * без --proxy в live — отказ
  * проверка выходного IP «не домашний» перед TCP (через run_guarded или сами)
  * DNS только через прокси (HTTP CONNECT), прямых сокетов к хосту шлюза нет
  * запуск через run_guarded.py предпочтителен

Пример dry-run:
  python 17_gateway.py --dry-run --pcap gog1.pcap
"""
from __future__ import annotations

# --- ЗАЩИТА ОТ ПРЯМОГО ЗАПУСКА (как в 10/11/12): live только через run_guarded ---
if __name__ == "__main__":
    import sys as _sys
    if "--live" in _sys.argv:
        import requests as _rq_guard
        if getattr(_rq_guard.Session.request, "__name__", "") != "_forced":
            raise SystemExit(
                "СТОП: --live только через run_guarded.py --proxy http://127.0.0.1:18081"
            )
# --- конец защиты ---

import argparse
import base64
import json
import os
import select
import socket
import struct
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    import xxhash
except ImportError:
    xxhash = None  # dry-run всё равно требует xxhash

BASE = Path(__file__).resolve().parent
HASH_SEED = 0x06B80873  # WatcherHeader.HashSeed из libil2cpp.so / dump.cs
WARDEN = 0xB873         # WatcherHeader.Warden (магия 73 b8)
SECRET_NUMBER = 888888
BAD_HOME_IP = "203.0.113.10"  # домашний — нельзя светить


def xxh32_payload(payload: bytes) -> int:
    """Контрольная сумма кадров: XXH32(тело, seed=HashSeed). Пустое тело → 0."""
    if not payload:
        return 0
    return xxhash.xxh32(payload, seed=HASH_SEED).intdigest()


def header_size(com_flags_and_msg_id: int) -> int:
    """GetHeaderSize: бит 0x20000000 → 18, иначе 32."""
    return 18 if (com_flags_and_msg_id & 0x20000000) else 32


def build_header(msg_id: int, payload: bytes, flags: int = 0, codec: int = 2) -> bytes:
    """
    Собирает заголовок управления (32 байта) для handshake/ping.
    Раскладка на проводе (из pcap + WatcherHeader.Serialize):
      [0..3]  ComFlagsAndMsgId (LE) — для handshake=3, ping=1; у ping ещё флаг в байте 3
      [4..6]  длина тела (3 байта LE)
      [7]     codec (2 = JSON)
      [8..25] нули (N64/N32/ReqId/Flags/Multicast не используются)
      [26..27] Warden 0xB873 LE → 73 b8
      [28..31] Chksum = XXH32(payload, HashSeed)
    """
    com = msg_id & 0xFF
    # ping в pcap: 01 00 00 04 — младший байт msg_id=1, байт 3 = 0x04 (флаг)
    if flags:
        com = (flags << 24) | (msg_id & 0xFFFFFF)
    ln = len(payload)
    hdr = bytearray(32)
    struct.pack_into("<I", hdr, 0, com)
    hdr[4] = ln & 0xFF
    hdr[5] = (ln >> 8) & 0xFF
    hdr[6] = (ln >> 16) & 0xFF
    hdr[7] = codec
    struct.pack_into("<H", hdr, 26, WARDEN)
    struct.pack_into("<I", hdr, 28, xxh32_payload(payload))
    return bytes(hdr)


def build_handshake_out(conn_id) -> bytes:
    """Тело + заголовок HandshakeOut (как у игры)."""
    body = {
        "ClientID": str(conn_id),
        "PreferredCodec": "JSON",
        "SecretNumber": SECRET_NUMBER,
        "Encrypt": True,
    }
    # компактный JSON без пробелов — как в pcap
    payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
    return build_header(3, payload) + payload


def build_ping() -> bytes:
    return build_header(1, b"", flags=0x04)


def parse_frame(buf: bytes, offset: int = 0):
    """Вернуть (header_len, payload, next_offset) или None."""
    if len(buf) - offset < 18:
        return None
    com = struct.unpack_from("<I", buf, offset)[0]
    hl = header_size(com)
    if len(buf) - offset < hl:
        return None
    ln = int.from_bytes(buf[offset + 4 : offset + 7], "little")
    if len(buf) - offset < hl + ln:
        return None
    hdr = buf[offset : offset + hl]
    pay = buf[offset + hl : offset + hl + ln]
    return hl, hdr, pay, offset + hl + ln


def parse_greeting(payload: bytes) -> dict:
    js = json.loads(payload.decode("utf-8"))
    return {
        "gateway_connid": js["ConnID"],
        "gateway_finger_print": js["Fingerprint"],
        "gateway_name": js["ServerID"],
        "cipher_b64": js.get("Cipher", ""),
        "codecs": js.get("Codecs", []),
    }


# -------------------- dry-run по pcap --------------------

def extract_gateway_streams(pcap_path: Path):
    """Достаёт клиентские/серверные байты TCP :17681 из pcap (SLL или Ethernet)."""
    data = pcap_path.read_bytes()
    lt = struct.unpack("<I", data[20:24])[0]
    off = 24
    streams = {}
    PORT = 17681
    while off + 16 <= len(data):
        ts, us, cl, ol = struct.unpack("<IIII", data[off : off + 16])
        d = data[off + 16 : off + 16 + cl]
        off += 16 + cl
        ip = d[16:] if lt == 113 else d[14:]
        if len(ip) < 20 or (ip[0] >> 4) != 4 or ip[9] != 6:
            continue
        ihl = (ip[0] & 15) * 4
        t = ip[ihl:]
        sp, dp = struct.unpack(">HH", t[:4])
        if PORT not in (sp, dp):
            continue
        plen = struct.unpack(">H", ip[2:4])[0]
        pl = ip[ihl + (t[12] >> 4) * 4 : plen]
        cport = sp if dp == PORT else dp
        s = streams.setdefault(cport, {"C": b"", "S": b""})
        s["C" if dp == PORT else "S"] += pl
    return streams


def dry_run(pcap_path: Path) -> int:
    if xxhash is None:
        print("СТОП: нужен пакет xxhash (pip install xxhash)")
        return 2
    streams = extract_gateway_streams(pcap_path)
    if not streams:
        print("нет потоков :17681 в", pcap_path)
        return 1
    ok_all = True
    for cport, s in streams.items():
        if not s["S"]:
            continue
        print(f"=== поток клиентского порта {cport}")
        # серверное приветствие
        fr = parse_frame(s["S"], 0)
        if not fr:
            print("  нет кадра сервера"); ok_all = False; continue
        hl, hdr, pay, _ = fr
        fields = parse_greeting(pay)
        print(f"  greeting ServerID={fields['gateway_name']} "
              f"ConnID=<скрыт> Fingerprint=<скрыт> cipher_len="
              f"{len(base64.b64decode(fields['cipher_b64'])) if fields['cipher_b64'] else 0}")
        # наш HandshakeOut
        ours = build_handshake_out(fields["gateway_connid"])
        # игровой ответ клиента
        fr_c = parse_frame(s["C"], 0)
        if not fr_c:
            print("  нет ответа клиента в pcap (короткое соединение?)")
            continue
        _, chdr, cpay, _ = fr_c
        game = chdr + cpay
        match = ours == game
        print(f"  HandshakeOut совпал с игрой: {match} (наш {len(ours)} B, игра {len(game)} B)")
        if not match:
            ok_all = False
            print("  наш :", ours[:32].hex(), ours[32:60])
            print("  игра:", game[:32].hex(), game[32:60])
        # ping
        ping = build_ping()
        # найдём первый ping клиента
        o = fr_c[3]
        found_ping = False
        while True:
            frp = parse_frame(s["C"], o)
            if not frp:
                break
            hl2, h2, p2, nxt = frp
            if h2[0] == 1:
                found_ping = True
                pm = ping == (h2 + p2)
                print(f"  Ping совпал с игрой: {pm}")
                if not pm:
                    ok_all = False
                    print("  наш ping:", ping.hex())
                    print("  игра ping:", (h2 + p2).hex())
                break
            o = nxt
        if not found_ping:
            print("  ping в pcap не найден (норм для короткого коннекта)")
        # сверка контрольных сумм всех кадров потока
        for side, buf in (("S", s["S"]), ("C", s["C"])):
            o = 0
            while True:
                frx = parse_frame(buf, o)
                if not frx:
                    break
                hlx, hx, px, nxt = frx
                want = struct.unpack_from("<I", hx, hlx - 4)[0]
                got = xxh32_payload(px)
                if want != got:
                    print(f"  CHK FAIL {side} off={o} want={want:#x} got={got:#x}")
                    ok_all = False
                o = nxt
    print("DRY-RUN", "OK" if ok_all else "FAIL")
    return 0 if ok_all else 1


# -------------------- сеть через HTTP CONNECT --------------------

def http_connect(proxy_url: str, host: str, port: int, timeout: float = 15.0) -> socket.socket:
    """
    TCP к host:port через HTTP CONNECT прокси.
    DNS резолвит прокси (vpnproxy сам резолвит имя) — мы передаём hostname, не IP.
    Прямого сокета к host нет.
    """
    u = urlparse(proxy_url)
    if u.scheme not in ("http", "https"):
        raise SystemExit(f"СТОП: нужен http:// прокси для CONNECT, сейчас {u.scheme}")
    ph, pp = u.hostname, u.port or 80
    # сокет только к локальному/доверенному прокси
    s = socket.create_connection((ph, pp), timeout=timeout)
    req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
    s.sendall(req.encode("ascii"))
    # читаем ответ до пустой строки
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = s.recv(4096)
        if not chunk:
            s.close()
            raise RuntimeError("прокси закрыл соединение до ответа CONNECT")
        buf += chunk
        if len(buf) > 65536:
            s.close()
            raise RuntimeError("слишком длинный ответ прокси")
    status_line = buf.split(b"\r\n", 1)[0].decode("ascii", "replace")
    if " 200 " not in status_line:
        s.close()
        raise RuntimeError(f"CONNECT отклонён: {status_line}")
    return s


def check_exit_ip(proxy_url: str) -> str:
    """Проверка выходного IP через тот же прокси (requests)."""
    import requests
    s = requests.Session()
    s.trust_env = False
    s.proxies = {"http": proxy_url, "https": proxy_url}
    ip = s.get("https://api.ipify.org?format=json", timeout=15).json().get("ip")
    if not ip or ip == BAD_HOME_IP:
        raise SystemExit(f"СТОП: выходной IP домашний или пустой")
    return ip


def version_diff2(proxy_url: str) -> tuple[str, int]:
    """versionDiff2 → (host, port) шлюза."""
    import requests
    s = requests.Session()
    s.trust_env = False
    s.proxies = {"http": proxy_url, "https": proxy_url}
    body = {"class": "call", "method": "versionDiff2",
            "params": {"os": "android", "channel": "google_gog", "version": "14.2.0"}}
    r = s.post("https://gog-global.kingsgroupgames.com/api/", json=body, timeout=20)
    r.raise_for_status()
    js = r.json()
    st = js.get("watcher_gate", {}).get("stargate") or {}
    host, port = st.get("host"), st.get("port")
    if not host or not port:
        raise RuntimeError("в ответе versionDiff2 нет watcher_gate.stargate")
    return host, int(port)


class GatewaySession:
    """Держит TCP-сессию шлюза: greeting → handshake → ping каждые 10 с."""

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.fields = None
        self._stop = threading.Event()
        self._pinger = None
        self._buf = b""

    def _recv_frame(self, timeout=10.0):
        self.sock.settimeout(timeout)
        while True:
            fr = parse_frame(self._buf, 0)
            if fr:
                hl, hdr, pay, nxt = fr
                self._buf = self._buf[nxt:]
                return hdr, pay
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("шлюз закрыл соединение")
            self._buf += chunk

    def handshake(self):
        hdr, pay = self._recv_frame(timeout=10)
        if hdr[0] != 3:
            raise RuntimeError(f"ожидали handshake type=3, получили {hdr[0]}")
        self.fields = parse_greeting(pay)
        out = build_handshake_out(self.fields["gateway_connid"])
        self.sock.sendall(out)
        # ack type 5
        hdr2, pay2 = self._recv_frame(timeout=10)
        if hdr2[0] != 5:
            raise RuntimeError(f"ожидали ack type=5, получили {hdr2[0]}")
        return self.fields

    def start_ping(self, interval=10.0):
        def loop():
            while not self._stop.wait(interval):
                try:
                    self.sock.sendall(build_ping())
                except OSError:
                    break
        self._pinger = threading.Thread(target=loop, name="gw-ping", daemon=True)
        self._pinger.start()

    def close(self):
        self._stop.set()
        try:
            self.sock.close()
        except OSError:
            pass


def live_session(proxy_url: str, hold_seconds: float = 0) -> dict:
    """
    Полный цикл: IP-check → versionDiff2 → CONNECT → handshake → ping.
    Не вызывать без явного разрешения пользователя.
    """
    ip = check_exit_ip(proxy_url)
    print("[guard] выходной IP:", ip)
    host, port = version_diff2(proxy_url)
    print(f"[gw] stargate {host}:{port} (через CONNECT {proxy_url})")
    sock = http_connect(proxy_url, host, port)
    sess = GatewaySession(sock)
    fields = sess.handshake()
    sess.start_ping(10)
    print("[gw] handshake ok, поля получены; ping каждые 10 с")
    if hold_seconds > 0:
        time.sleep(hold_seconds)
        sess.close()
    # если hold_seconds==0 — вызывающий держит sess сам
    return {"fields": fields, "session": sess}


def fields_for_init(fields: dict) -> dict:
    """Три ключа для 15_new_account.py / init."""
    return {
        "gateway_name": fields["gateway_name"],
        "gateway_finger_print": fields["gateway_finger_print"],
        "gateway_connid": fields["gateway_connid"],
    }


def main():
    ap = argparse.ArgumentParser(description="Клиент шлюза Watcher/stargate")
    ap.add_argument("--dry-run", action="store_true", help="сверка с pcap, без сети")
    ap.add_argument("--pcap", type=Path, default=BASE / "gog1.pcap")
    ap.add_argument("--live", action="store_true", help="ЖИВОЕ подключение (нужно отдельное «да»)")
    ap.add_argument("--proxy", default=None, help="http://127.0.0.1:18081")
    ap.add_argument("--hold", type=float, default=30.0, help="сколько секунд держать ping в --live")
    ap.add_argument("--out", type=Path, default=None, help="записать три поля JSON")
    ap.add_argument("--i-have-user-ok-for-live", action="store_true",
                    help="явный флаг: пользователь разрешил live к шлюзу игры")
    args = ap.parse_args()

    if args.dry_run or not args.live:
        if not args.live:
            # по умолчанию dry-run
            return dry_run(args.pcap)
        return dry_run(args.pcap)

    # live
    if not args.i_have_user_ok_for_live:
        print("СТОП: живое соединение со шлюзом игры запрещено, пока нет отдельного «да».")
        print("      Когда будет разрешение: --live --i-have-user-ok-for-live --proxy http://127.0.0.1:18081")
        print("      vpnproxy (исходник) CONNECT на любой host:port умеет — проверено по vpnproxy.go.")
        return 3
    if not args.proxy:
        print("СТОП: --live без --proxy запрещён")
        return 3
    if xxhash is None:
        print("СТОП: нужен xxhash"); return 2
    result = live_session(args.proxy, hold_seconds=args.hold)
    fields = fields_for_init(result["fields"])
    # не печатаем сырые значения целиком — только факт и ServerID
    print("[gw] поля для init: gateway_name=", fields["gateway_name"],
          "connid/fingerprint получены")
    if args.out:
        args.out.write_text(json.dumps(fields), encoding="utf-8")
        print("[gw] записано в", args.out)
    result["session"].close()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
