# -*- coding: utf-8 -*-
import sys, struct, xxhash, zlib
sys.stdout.reconfigure(encoding="utf-8")
SEED = 0x06B80873
print("seed", hex(SEED))
b = open(r"E:\protocol_analysis\capture\gog1.pcap", "rb").read()
lt = struct.unpack("<I", b[20:24])[0]; off = 24; sc = ss = b""; PORT = 17681
while off + 16 <= len(b):
    ts, us, cl, ol = struct.unpack("<IIII", b[off:off+16]); d = b[off+16:off+16+cl]; off += 16+cl
    ip = d[16:] if lt == 113 else d[14:]
    if len(ip) < 20 or ip[0]>>4 != 4 or ip[9] != 6: continue
    ihl = (ip[0]&15)*4; t = ip[ihl:]; sp, dp = struct.unpack(">HH", t[:4])
    if PORT not in (sp, dp): continue
    pl = ip[ihl+(t[12]>>4)*4 : struct.unpack(">H", ip[2:4])[0]]
    (sc if dp == PORT else ss).__class__  # noqa
    if dp == PORT: sc += pl
    else: ss += pl

def frames(buf, side):
    o = 0
    while o + 18 <= len(buf):
        h0 = buf[o]
        # GetHeaderSize: if (comFlagsAndMsgId & 0x20000000)==0 -> 32 else 18
        # На проводе байты 0..3 = ComFlagsAndMsgId LE?
        com = struct.unpack_from("<I", buf, o)[0]
        hl = 32 if (com & 0x20000000) == 0 else 18
        # но data frame начинается с 71 17 00 25 — com=0x25001771, bit 0x20000000 set? 0x25001771 & 0x20000000 = 0
        # hmm bit29 = 0x20000000. 0x25001771 = 0010 0101 ... bit29 is bit of 0x20000000 = bit 29.
        # 0x25001771 >> 29 = 1? 0x25001771 = 622986097, >>29 = 1. Yes bit29 set -> size 18.
        # handshake 03 00 00 00 -> com=3, bit29 clear -> 32. Good!
        ln = int.from_bytes(buf[o+4:o+7], "little")
        if o + hl + ln > len(buf): break
        yield side, hl, buf[o:o+hl], buf[o+hl:o+hl+ln]
        o += hl + ln

def xx(data, seed=SEED):
    return xxhash.xxh32(data, seed=seed).intdigest()

hits = 0; total = 0
for side, hl, hdr, pay in list(frames(ss,"S"))+list(frames(sc,"C")):
    chk = struct.unpack_from("<I", hdr, hl-4)[0]
    total += 1
    cands = {
        "pay": xx(pay) if pay else 0,
        "h_nocheck+pay": xx(hdr[:hl-4] + pay),
        "h_zerocheck+pay": xx(hdr[:hl-4] + b"\x00"*4 + pay),
        "h_nocheck": xx(hdr[:hl-4]),
        "from1+pay": xx(hdr[1:hl-4]+pay) if hl>5 else None,
        "skip0_3+pay": xx(hdr[4:hl-4]+pay),
    }
    ok = [k for k,v in cands.items() if v == chk]
    # empty special
    if not pay and chk == 0:
        ok.append("empty->0")
    mark = "OK "+str(ok) if ok else "MISS"
    if ok: hits += 1
    print(f"{side} hl={hl} len={len(pay)} chk={chk:#010x} {mark} cands={{"+", ".join(f'{k}:{v:#x}' for k,v in cands.items() if v is not None)+"}")
print(f"hits {hits}/{total}")
