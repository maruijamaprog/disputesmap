# -*- coding: utf-8 -*-
"""Копирует проверенные записи в site/data и собирает справочник сторон для сайта.
Запуск: python scripts/build_site_data.py  (из корня проекта)"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*x): return os.path.join(ROOT, *x)

disputes = json.load(open(p("data", "disputes.json"), encoding="utf-8"))
actors = json.load(open(p("data", "actors.skeleton.json"), encoding="utf-8"))["actors"]
by_code = {a["code"]: a for a in actors}

used = set()
for d in disputes["disputes"]:
    for c in d["claimants"]: used.add(c["actor"])
    for c in d["de_facto_controller"]: used.add(c["state"])
    for e in d.get("external_control", []): used.add(e["state"])
    for ar in d["areas"]:
        for c in ar["de_facto_controller"]: used.add(c["state"])
        for c in ar.get("claimants", []): used.add(c["actor"])
        for e in ar.get("external_control", []): used.add(e["state"])
    for pos in d["positions"]: used.add(pos["actor"])

missing = sorted(used - set(by_code))
if missing:
    raise SystemExit("Нет в справочнике сторон: " + ", ".join(missing))

out_actors = {c: {"type": by_code[c]["type"], "ru": by_code[c]["names"]["ru"], "en": by_code[c]["names"]["en"]} for c in sorted(used)}
os.makedirs(p("site", "data"), exist_ok=True)
json.dump(disputes, open(p("site", "data", "disputes.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(out_actors, open(p("site", "data", "actors.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"споров: {len(disputes['disputes'])}, сторон: {len(out_actors)}")
