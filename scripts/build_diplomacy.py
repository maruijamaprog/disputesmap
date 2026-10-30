# -*- coding: utf-8 -*-
"""
Дипломатические отношения → site/data/diplomacy.json.

Вход:
  data/diplomacy_curated.json — проверенные редакцией сведения со ссылками на источники:
      facts: {код: [{text: {ru, en}, src: [id источника]}]} — например, число государств, признающих сторону;
      none:  [{a, b, status: never|broken|suspended, since, note: {ru, en}, src: [...]}] — нет отношений или разрыв;
      sources: [{id, title, author, year, url, accessed}]
  raw/wikidata_states.csv     — только названия государств RU/EN (Wikidata, CC0)

Почему не используется свойство Wikidata P530 «дипломатические отношения»: проверка показала, что оно отмечает
двусторонние связи вообще, а не установленные дипломатические отношения (например, у Тайваня — более 170 «отношений»
при 12 государствах, признающих Китайскую Республику, есть пара Армения — Азербайджан, у которых отношений нет).
Поэтому на сайте показываются только проверенные сведения; полный перечень отношений не публикуется.
Запуск: python scripts/build_diplomacy.py --raw raw --out site/data
"""
import argparse, csv, json, os, datetime

SPECIAL = {"Q1246": "XKX", "Q159583": "VAT", "Q31354462": "X-ABK", "Q23334": "X-ABK", "Q23427": "X-SOS", "Q907112": "X-PMR",
           "Q23681": "X-TRNC", "Q40362": "X-SADR", "Q34754": "X-SOMALILAND"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw"); ap.add_argument("--out", default="site/data")
    ap.add_argument("--curated", default="data/diplomacy_curated.json")
    a = ap.parse_args()

    names = {}
    path = os.path.join(a.raw, "wikidata_states.csv")
    if os.path.exists(path):
        for r in csv.DictReader(open(path, encoding="utf-8")):
            q = r["item"].rsplit("/", 1)[-1]
            code = SPECIAL.get(q) or r["iso"]
            if not code or r["dissolved"] or code in names: continue
            if r["ru"] or r["en"]:
                names[code] = {"ru": r["ru"] or r["en"], "en": r["en"] or r["ru"]}

    cur = json.load(open(a.curated, encoding="utf-8")) if os.path.exists(a.curated) else {}
    ids = {s["id"] for s in cur.get("sources", [])}
    for x in cur.get("none", []):
        for s in x.get("src", []):
            if s not in ids: raise SystemExit(f"нет источника {s}")
    for code, fs in cur.get("facts", {}).items():
        for f in fs:
            for s in f.get("src", []):
                if s not in ids: raise SystemExit(f"нет источника {s}")

    today = datetime.date.today()
    months_ru = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    out = {
        "as_of": today.strftime("%Y-%m"),
        "as_of_label": {"ru": f"{months_ru[today.month - 1]} {today.year}", "en": today.strftime("%B %Y")},
        "names": names,
        "facts": cur.get("facts", {}),
        "none": cur.get("none", []),
        "sources": cur.get("sources", []),
    }
    dst = os.path.join(a.out, "diplomacy.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"diplomacy.json: сведений {sum(len(v) for v in out['facts'].values())}, пар без отношений {len(out['none'])}, источников {len(out['sources'])}")

if __name__ == "__main__":
    main()
