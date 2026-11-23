from pathlib import Path; import re, py_compile
p=Path("16_run_full.py"); s=p.read_text(encoding="utf-8")
s,n=re.subn(r'log\(f"\[ip\] \{phase\}: \{ip\}".*\n', 'log(f"[ip] {phase}: выход НЕ домашний" + ("" if ip == FIRST_IP[0] else " (сменился)"))\n', s, count=1)
p.write_text(s,encoding="utf-8"); py_compile.compile(str(p),doraise=True); print(n)
