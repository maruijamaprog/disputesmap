# -*- coding: utf-8 -*-
"""Партия 3 (15 споров) → data/disputes.json: записи с теми же id заменяются, новые добавляются.
Запуск: python scripts/data/batch3.py data/disputes.json"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch3a, batch3b  # noqa: E402

def refs(d):
    out = []
    for c in d["claimants"]: out += c.get("source_ids", [])
    for c in d["de_facto_controller"]: out += c.get("source_ids", [])
    for e in d.get("external_control", []): out += e["source_ids"]
    for a in d["areas"]:
        for c in a["de_facto_controller"]: out += c.get("source_ids", [])
        for c in a.get("claimants", []): out += c.get("source_ids", [])
        for e in a.get("external_control", []): out += e["source_ids"]
    for p in d["positions"]: out += p["source_ids"]
    if d.get("international_position"): out += d["international_position"]["source_ids"]
    for t in d["secondary_types"]: out += t["qualified_by"]
    for h in d.get("history", []): out += h["source_ids"]
    return out

def main(path):
    data = json.load(open(path, encoding="utf-8"))
    new = batch3a.R + batch3b.R
    for d in new:
        ids = [s["id"] for s in d["sources"]]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup: raise SystemExit(f"{d['id']}: повтор id источников {dup}")
        miss = sorted(set(refs(d)) - set(ids))
        if miss: raise SystemExit(f"{d['id']}: ссылки на несуществующие источники {miss}")
        unused = sorted(set(ids) - set(refs(d)))
        if unused: print(f"  {d['id']}: источники без ссылок в полях (только список): {unused}")
    by = {d["id"]: i for i, d in enumerate(data["disputes"])}
    for d in new:
        if d["id"] in by: data["disputes"][by[d["id"]]] = d
        else: data["disputes"].append(d)
    data["meta"]["batch"] = 3
    data["meta"]["generated"] = batch3a.ACC
    data["meta"]["note_ru"] = "Партии 1–3. Записи со статусом draft прошли проверку источников; спорные места перечислены в review. Отображение не выражает позиции авторов."
    data["meta"]["note_en"] = "Batches 1–3. Draft records have been source-checked; open issues are listed in review. Depiction does not imply any position of the authors."
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("записей:", len(data["disputes"]), "добавлено/обновлено:", ", ".join(d["id"] for d in new))

if __name__ == "__main__":
    main(sys.argv[1])
