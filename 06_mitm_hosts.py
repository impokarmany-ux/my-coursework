# 06_mitm_hosts.py — посмотреть какие HTTPS-хосты поймал MITM
# Запуск: $env:PYTHONIOENCODING='utf-8'; python 06_mitm_hosts.py
from pathlib import Path
p = Path(r"E:\protocol_analysis\capture\mitm\hosts_seen.txt")
if not p.exists():
    print("Нет hosts_seen.txt — mitmdump ещё не ловил трафик")
else:
    hosts = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if " HOST " in line:
            hosts.append(line.split(" HOST ", 1)[1].strip())
    uniq = sorted(set(hosts))
    print(f"Всего уникальных хостов: {len(uniq)}")
    for h in uniq:
        mark = " <== GOG" if any(x in h for x in ("kingsgroup", "funplus", "gog")) else ""
        print(f"  {h}{mark}")
