# -*- coding: utf-8 -*-
import sys, struct, re
sys.stdout.reconfigure(encoding="utf-8")
from capstone import *
so = open(r"E:\Dump\libil2cpp.so", "rb").read()
# ELF PT_LOAD mapping
import io
e = so[:64]
assert e[:4] == b"\x7fELF"
phoff = struct.unpack_from("<Q", e, 32)[0]
phentsize, phnum = struct.unpack_from("<HH", e, 54)
print("phnum", phnum)
segs = []
for i in range(phnum):
    off = phoff + i * phentsize
    p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack_from("<IIQQQQQQ", so, off)
    if p_type == 1:
        segs.append((p_vaddr, p_offset, p_filesz, p_memsz))
        print(f"LOAD vaddr={p_vaddr:#x} off={p_offset:#x} filesz={p_filesz:#x}")

def va2off(va):
    for v, o, fs, ms in segs:
        if v <= va < v + ms:
            return o + (va - v)
    return None

addr = 0x3DC01B8
off = va2off(addr)
print(f"const @ {addr:#x} -> off {off:#x}" if off is not None else "no map")
if off is not None:
    raw = so[off : off + 8]
    print("bytes", raw.hex(), "as 2x u32", struct.unpack("<II", raw), "as u64", struct.unpack("<Q", raw)[0])

# поиск всех bl на XXH32 в диапазоне 0x14900000..0x14950000
xx = {0x14933080: "XXH32(buf)", 0x149330E8: "XXH32(buf,seed)", 0x149331B8: "XXH32(buf,off,len,seed)",
      0x149335FC: "XXH32(stream)", 0x14933664: "XXH32(stream,seed)", 0x149339FC: "DigestState32"}
code_start, code_end = 0x14900000, 0x14950000
code = so[va2off(code_start) : va2off(code_start) + (code_end - code_start)]
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
print("XXH calls:")
for i in md.disasm(code, code_start):
    if i.mnemonic != "bl":
        continue
    m = re.search(r"#(0x[0-9a-f]+)", i.op_str)
    if m:
        t = int(m.group(1), 16)
        if t in xx:
            print(f"  {i.address:08x} -> {xx[t]}")
