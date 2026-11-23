# -*- coding: utf-8 -*-
import sys, struct, xxhash, zlib
sys.stdout.reconfigure(encoding="utf-8")
b = open(r"E:\protocol_analysis\capture\gog1.pcap", "rb").read()
lt = struct.unpack("<I", b[20:24])[0]
off = 24
sc = ss = b""
PORT = 17681
while off + 16 <= len(b):
    ts, us, cl, ol = struct.unpack("<IIII", b[off : off + 16])
    d = b[off + 16 : off + 16 + cl]
    off += 16 + cl
    ip = d[16:] if lt == 113 else d[14:]
    if len(ip) < 20 or ip[0] >> 4 != 4 or ip[9] != 6:
        continue
    ihl = (ip[0] & 15) * 4
    t = ip[ihl:]
    sp, dp = struct.unpack(">HH", t[:4])
    if PORT not in (sp, dp):
        continue
    pl = ip[ihl + (t[12] >> 4) * 4 : struct.unpack(">H", ip[2:4])[0]]
    if dp == PORT:
        sc += pl
    else:
        ss += pl
shdr, spay = ss[:32], ss[32 : 32 + 211]
chdr, cpay = sc[:32], sc[32 : 32 + 84]
st = struct.unpack("<I", shdr[28:32])[0]
ct = struct.unpack("<I", chdr[28:32])[0]
print("S", shdr.hex(), hex(st), "pay", len(spay))
print("C", chdr.hex(), hex(ct), "pay", cpay[:50])

def xx(data, seed):
    return xxhash.xxh32(data, seed=seed).intdigest()

warden = 0xB873
hits = []
seeds = [0, 1, warden, 0x73B8, 0xCBF29CE4, 0x811C9DC5, 0xDEADBEEF, 0x9747B28C, 0x242070DB, 0x85EBCA77, 0xC2B2AE3D, 0x27D4EB2F, 0x165667B1]
for seed in seeds:
    pairs = [
        ("pay", cpay, spay),
        ("h28+pay", chdr[:28] + cpay, shdr[:28] + spay),
        ("hz+pay", chdr[:28] + b"\x00" * 4 + cpay, shdr[:28] + b"\x00" * 4 + spay),
        ("from4+pay", chdr[4:28] + cpay, shdr[4:28] + spay),
        ("type+pay", bytes([chdr[0]]) + cpay, bytes([shdr[0]]) + spay),
        ("size3+pay", chdr[4:7] + cpay, shdr[4:7] + spay),
        ("codec+pay", bytes([chdr[7]]) + cpay, bytes([shdr[7]]) + spay),
        ("warden+pay", chdr[26:28] + cpay, shdr[26:28] + spay),
        ("h0_26+pay", chdr[:26] + cpay, shdr[:26] + spay),
        ("utf16", cpay.decode().encode("utf-16le"), spay.decode().encode("utf-16le")),
    ]
    for label, cd, sd in pairs:
        if xx(cd, seed) == ct:
            hits.append(("C", label, hex(seed)))
        if xx(sd, seed) == st:
            hits.append(("S", label, hex(seed)))
print("xx hits", hits)
print("crc32 c", hex(zlib.crc32(cpay) & 0xFFFFFFFF), "s", hex(zlib.crc32(spay) & 0xFFFFFFFF))
print("xx0 c", hex(xx(cpay, 0)), "xor target", hex(xx(cpay, 0) ^ ct))
# широкий перебор seed для h28+pay и pay
print("bruteforce seed 24bit on pay...")
for seed in range(0, 1 << 24, 1):
    if xx(cpay, seed) == ct:
        print("FOUND pay seed", hex(seed))
        break
    if xx(chdr[:28] + cpay, seed) == ct:
        print("FOUND h28+pay seed", hex(seed))
        break
    if seed & 0xFFFFF == 0 and seed:
        pass
else:
    print("no 24bit seed for pay/h28+pay")
