"""Генерирует inventory/embedded_icons.py из папки ico/.
Запускать перед сборкой:  python generate_icons.py
"""
import base64
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Умное определение путей (работает, даже если скрипт лежит внутри папки inventory)
if os.path.basename(SCRIPT_DIR) == "inventory":
    INV_DIR = SCRIPT_DIR
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
else:
    INV_DIR = os.path.join(SCRIPT_DIR, "inventory")
    PROJECT_ROOT = SCRIPT_DIR

ICO_DIR = os.path.join(PROJECT_ROOT, "ico")
OUT_FILE = os.path.join(INV_DIR, "embedded_icons.py")


def main():
    if not os.path.isdir(ICO_DIR):
        print(f"[!] Папка '{ICO_DIR}' не найдена. Генерация пропущена.")
        sys.exit(1)

    entries = {}
    for fname in sorted(os.listdir(ICO_DIR)):
        fpath = os.path.join(ICO_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "rb") as f:
            data = f.read()
        entries[fname] = base64.b64encode(data).decode("ascii")
        print(f"  + {fname}: {len(data)} байт")

    if not entries:
        print("[!] В папке ico/ нет файлов.")
        sys.exit(1)

    lines = [
        '"""Файл сгенерирован автоматически скриптом generate_icons.py.',
        'Не редактируйте вручную — запустите python generate_icons.py"',
        '"""',
        "",
        "ICONS_DATA = {",
    ]
    for name, b64 in entries.items():
        lines.append(f'    {name!r}: (')
        for i in range(0, len(b64), 76):
            lines.append(f'        {b64[i:i+76]!r}')
        lines.append("    ),")
    lines.append("}")
    lines.append("")

    try:
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except FileNotFoundError:
        print(f"[!] Не удалось найти папку для сохранения: {os.path.dirname(OUT_FILE)}")
        print("Убедитесь, что структура проекта не нарушена (папка inventory должна существовать).")
        sys.exit(1)

    total_kb = sum(len(v) for v in entries.values()) / 1024
    print(f"\n[OK] Записано: {OUT_FILE}")
    print(f"     Файлов: {len(entries)}, суммарно base64: {total_kb:.1f} КБ")


if __name__ == "__main__":
    main()