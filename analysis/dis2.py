# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
from capstone import *
so = open(r"E:\Dump\libil2cpp.so", "rb").read()

def dis(rva, n=400, label=""):
    code = so[rva - 0x4000 : rva - 0x4000 + n]
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    print(f"=== {label} {rva:#x}")
    for i in md.disasm(code, rva):
        print(f"  {i.address:08x}: {i.mnemonic:8} {i.op_str}")
        if i.mnemonic == "ret" and i.address > rva + 16:
            break

dis(0x149405AC, 200, "WatcherHeader.cctor")
dis(0x1493BBDC, 120, "GetHeaderSize")
dis(0x14939CA4, 200, "WatcherHeader.ctor")
# найти вызовы XXH32 из области Watcher (0x14939000-0x14941000)
print("=== BL to XXH32 from Watcher region")
code = so[0x14939000 - 0x4000 : 0x14941000 - 0x4000]
md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
xx_targets = {0x14933080, 0x149330E8, 0x149331B8, 0x149335FC, 0x14933664, 0x149339FC, 0x14934D24, 0x14933804}
for i in md.disasm(code, 0x14939000):
    if i.mnemonic == "bl":
        m = re.search(r"#(0x[0-9a-f]+)", i.op_str)
        if m and int(m.group(1), 16) in xx_targets:
            print(f"  {i.address:08x} -> {m.group(1)}")
