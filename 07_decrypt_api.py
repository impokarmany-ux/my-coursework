# -*- coding: utf-8 -*-
"""
07_decrypt_api.py — разбор «второго слоя» шифрования HTTP API Guns of Glory.

Что делает:
1) Считает статистику сохранённых тел запросов/ответов (размер, выравнивание 16,
   энтропия, общие префиксы).
2) Пробует наивные ключи (KOA и производные) — ожидаемо НЕ сработает на боевых
   телах: ключ сессии (ak/ai) приходит с сервера и живёт в памяти.
3) Печатает, куда смотреть дальше (Frida / Ghidra).

Запуск (PowerShell):
  $env:PYTHONIOENCODING='utf-8'
  python E:\\protocol_analysis\\capture\\07_decrypt_api.py
"""
from __future__ import annotations
import glob, hashlib, json, math, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
BODIES = os.path.join(ROOT, "mitm", "raw_bodies")

def entropy(b: bytes) -> float:
    if not b:
        return 0.0
    c = Counter(b)
    n = len(b)
    return -sum((v/n) * math.log2(v/n) for v in c.values())

def looks_json(b: bytes) -> bool:
    s = b.lstrip()[:1]
    return s in (b"{", b"[")

def summarize():
    files = sorted(glob.glob(os.path.join(BODIES, "*.bin")))
    if not files:
        print("Нет файлов в", BODIES)
        print("Сначала извлеки сырые тела из flows.mitm (см. СЛОЙ2.md).")
        return []
    rows = []
    print("=== Сырые тела ===")
    print(f"{'file':28} {'n':>6} {'%16':>4} {'H':>5} {'head hex'}")
    for p in files:
        b = open(p, "rb").read()
        name = os.path.basename(p)
        aligned = "yes" if len(b) % 16 == 0 and len(b) >= 16 and not looks_json(b) else ("json" if looks_json(b) else "no")
        h = entropy(b)
        print(f"{name:28} {len(b):6d} {aligned:>4} {h:5.2f} {b[:16].hex()}")
        rows.append((name, b))
    # shared first blocks
    for kind in ("_req.bin", "_resp.bin"):
        blocks = Counter()
        for name, b in rows:
            if name.endswith(kind) and len(b) >= 16 and not looks_json(b):
                blocks[b[:16]] += 1
        print(f"\nОбщие первые 16 байт ({kind}):")
        for blk, c in blocks.most_common(5):
            print(f"  {c:3d}x  {blk.hex()}")
    return rows

def try_naive_aes(rows):
    try:
        from Crypto.Cipher import AES
    except ImportError:
        print("\n[!] Нет pycryptodome: pip install pycryptodome")
        return
    # берём короткий encrypted resp
    sample = None
    for name, b in rows:
        if name.endswith("_resp.bin") and len(b) >= 32 and len(b) % 16 == 0 and not looks_json(b):
            if sample is None or len(b) < len(sample[1]):
                sample = (name, b)
    if not sample:
        print("Нет бинарного ответа для пробы")
        return
    name, body = sample
    print(f"\n=== Наивные AES-попытки на {name} ({len(body)} байт) ===")
    print("Цель — убедиться, что статический KOA / нули / md5(KOA) НЕ открывают тело.")
    seeds = [
        b"KOA",
        b"KOA\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        b"1234567890abcdef",  # api_iv из manifest — чужой контекст
        b"GunsOfGlory!!!!!",
        b"funplus",
        b"gog.global.prod!",
    ]
    keys = []
    for s in seeds:
        raw = (s * 16)[:16]
        keys.append((f"pad16({s[:12]!r})", raw))
        keys.append((f"md5({s[:12]!r})", hashlib.md5(s).digest()))
        keys.append((f"sha256[:16]({s[:12]!r})", hashlib.sha256(s).digest()[:16]))
    hits = 0
    for kname, key in keys:
        # ECB
        try:
            pt = AES.new(key, AES.MODE_ECB).decrypt(body)
            if looks_json(pt) or b"payload" in pt[:64] or b'"ok"' in pt[:64]:
                print("HIT ECB", kname, pt[:80])
                hits += 1
        except Exception:
            pass
        # CBC IV=0
        try:
            pt = AES.new(key, AES.MODE_CBC, b"\x00" * 16).decrypt(body)
            if looks_json(pt) or b"payload" in pt[:64] or b'"ok"' in pt[:64]:
                print("HIT CBC-zero", kname, pt[:80])
                hits += 1
        except Exception:
            pass
        # CBC IV=first block (остальное — ciphertext)
        if len(body) > 16:
            try:
                pt = AES.new(key, AES.MODE_CBC, body[:16]).decrypt(body[16:])
                if looks_json(pt) or b"payload" in pt[:64] or b'"ok"' in pt[:64]:
                    print("HIT CBC-headIV", kname, pt[:80])
                    hits += 1
            except Exception:
                pass
    if hits == 0:
        print("Попаданий нет (ожидаемо). Ключ сессии ak/ai нужен из EncryptorWithRandomKey.Open.")
    else:
        print("Неожиданные попадания:", hits)

def main():
    print("Bodies dir:", BODIES)
    rows = summarize()
    if rows:
        try_naive_aes(rows)
    print("""
=== Что это значит ===
- Выравнивание кратно 16 + высокая энтропия ≈ AES (блочный шифр).
- Одинаковый первый блок у многих ответов ≈ общий префикс plaintext
  (например начало JSON) + фиксированный IV, либо ECB на одинаковом блоке.
- Ключ не «KOA» напрямую для HTTP: KOA — default у AesKeyCoderMethod1..5,
  которые, судя по сигнатурам, больше похожи на обёртки/деривацию строки ключа.
- Боевой путь: EncryptorWithRandomKey.Open(ak, ai) → AesCoderWithRandomKey.Initialize
  → Encode/Decode. ak/ai в release, похоже, не пишутся на диск (/aes_key пусто).

Следующий шаг: Frida-хук Open(ak,ai) / Encode на окне netbot_test, либо
разбор Initialize в Ghidra по RVA из dump.cs.
""")

if __name__ == "__main__":
    main()
