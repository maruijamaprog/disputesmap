# -*- coding: utf-8 -*-
"""
Ставит новую версию сборки в site/index.html и site/methodology.html:
атрибут <html data-v="…"> и метки ?v=… у стилей, скриптов и карты модулей (importmap).
Браузер видит новые адреса и загружает свежие файлы, а не старые копии из кэша.

Запуск перед загрузкой изменений на GitHub:
  python scripts/set_version.py            — версия по текущему времени (ГГГГММДД-ЧЧММ)
  python scripts/set_version.py 2026-11-19 — своя метка
"""
import datetime, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = [os.path.join(ROOT, "site", "index.html"), os.path.join(ROOT, "site", "methodology.html")]


def main():
    v = sys.argv[1] if len(sys.argv) > 1 else datetime.datetime.now().strftime("%Y%m%d-%H%M")
    if not re.fullmatch(r"[0-9A-Za-z.\-]+", v):
        sys.exit("Версия может содержать только латиницу, цифры, точку и дефис")
    for path in FILES:
        with open(path, encoding="utf-8") as f:
            s = f.read()
        s2 = re.sub(r'(\?v=)[0-9A-Za-z.\-]+', r'\g<1>' + v, s)
        s2 = re.sub(r'(<html[^>]*\sdata-v=")[^"]*(")', r'\g<1>' + v + r'\g<2>', s2)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(s2)
        print(f"{os.path.relpath(path, ROOT)}: версия {v}")


if __name__ == "__main__":
    main()
