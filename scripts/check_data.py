# -*- coding: utf-8 -*-
"""Проверка данных: JSON Schema + правила фактчекинга + проверка нейтральности.
Запуск: python scripts/check_data.py . отчёт.json  (из корня проекта)"""
import json, re, sys
from jsonschema import Draft202012Validator

root = sys.argv[1]
schema = json.load(open(f"{root}/schema/disputes.schema.json", encoding="utf-8"))
data = json.load(open(f"{root}/data/disputes.json", encoding="utf-8"))
actors = {a["code"] for a in json.load(open(f"{root}/data/actors.skeleton.json", encoding="utf-8"))["actors"]}

errs = list(Draft202012Validator(schema).iter_errors(data))
print(f"JSON Schema: {len(errs)} ошибок")
for e in errs[:20]: print("  ", list(e.absolute_path), e.message[:160])

def org(author):  # «независимость» источников: по организации/автору до скобки
    a = author.split(" (")[0].strip()
    return a

KEY = ["period.start", "claimants", "de_facto_controller", "legal_status"]
LOADED = r"(незаконн|так называем|оккупант|марионет|агресс|террор|героич|освобожд|освобож|режим\b|illegal|so-called|puppet|aggress|terror|heroic|liberat|regime\b|occupied|оккупир)"

summary = []
for r in data["disputes"]:
    rid = r["id"]; ids = {s["id"]: s for s in r["sources"]}
    probs, warns = [], []
    # ссылки на источники
    refs = []
    for c in r["claimants"]: refs += c.get("source_ids", [])
    for c in r["de_facto_controller"]: refs += c.get("source_ids", [])
    for a in r["areas"]:
        for c in a["de_facto_controller"]: refs += c.get("source_ids", [])
        for c in a.get("claimants", []): refs += c.get("source_ids", [])
        for e in a.get("external_control", []): refs += e.get("source_ids", [])
    for e in r.get("external_control", []): refs += e.get("source_ids", [])
    for h in r.get("history", []): refs += h["source_ids"]
    for p in r["positions"]: refs += p["source_ids"]
    if r["international_position"]: refs += r["international_position"]["source_ids"]
    for t in r["secondary_types"]: refs += t["qualified_by"]
    for x in refs:
        if x not in ids: probs.append(f"ссылка на несуществующий источник {x}")
    # акторы
    for c in r["claimants"] + [c for a in r["areas"] for c in a.get("claimants", [])]:
        if c["actor"] not in actors: probs.append(f"неизвестный актор {c['actor']}")
    for c in r["de_facto_controller"] + [c for a in r["areas"] for c in a["de_facto_controller"]]:
        if c["state"] not in actors: probs.append(f"неизвестный контролёр {c['state']}")
    # ≥2 независимых источника на ключевое утверждение
    keys = KEY + (["period.end"] if r["period"]["end"] is not None else [])
    cov = {}
    for k in keys:
        srcs = [s for s in r["sources"] if k in s["supports"]]
        orgs = {org(s["author"]) for s in srcs}
        full = [s for s in srcs if s["verified_fulltext"]]
        cov[k] = (len(orgs), len(full))
        if len(orgs) < 2: probs.append(f"«{k}»: независимых источников {len(orgs)} (<2)")
        elif len({org(s['author']) for s in full}) < 2: warns.append(f"«{k}»: только {len(full)} с проверенным текстом")
    # позиции: источник своей стороны
    pos_actors = set()
    for p in r["positions"]:
        persp = [ids[x]["perspective"].split(",") for x in p["source_ids"] if x in ids]
        if not any(p["actor"] in pp for pp in persp): probs.append(f"позиция {p['actor']}: нет источника этой стороны")
        pos_actors.add(p["actor"])
    claim_actors = {c["actor"] for c in r["claimants"] + [c for a in r["areas"] for c in a.get("claimants", [])]}
    if not r.get("history"): warns.append("нет истории")
    missing_pos = sorted(claim_actors - pos_actors)
    if missing_pos: warns.append("нет позиции: " + ", ".join(missing_pos))
    # оккупация
    for t in r["secondary_types"]:
        if t["type"] == "occupation":
            q = [ids[x] for x in t["qualified_by"] if x in ids]
            if not q: probs.append("occupation без qualified_by")
            elif not all(s["perspective"] == "international" for s in q): probs.append("qualified_by: не международный источник")
    # страницы
    for s in r["sources"]:
        if s["page_or_article"] and not s["verified_fulltext"]: probs.append(f"{s['id']}: страница без проверки текста")
    # нейтральность (тексты не-позиций)
    for fld in ("summary", "legal_status"):
        for lang in ("ru", "en"):
            for m in re.finditer(LOADED, r[fld][lang], flags=re.I):
                warns.append(f"лексика [{fld}.{lang}]: «{r[fld][lang][max(0,m.start()-30):m.end()+25]}»")
    conflicts = len(r["review"]["conflicts"])
    sugg_conf = "high" if not probs and not missing_pos and all(v[1] >= 2 for v in cov.values()) else ("medium" if not probs else "low")
    summary.append(dict(id=rid, confidence=r["confidence"], suggested=sugg_conf, review=r["needs_human_review"], conflicts=conflicts,
                        sources=len(r["sources"]), fulltext=sum(s["verified_fulltext"] for s in r["sources"]), coverage=cov, problems=probs, warnings=warns))

print()
only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
for s in summary:
    if only and s["id"] not in only: continue
    print(f"== {s['id']}: confidence={s['confidence']} (по правилам ≤ {s['suggested']}), review={s['review']}, источников={s['sources']} (полный текст {s['fulltext']}), противоречий={s['conflicts']}")
    print("   покрытие:", ", ".join(f"{k}: {v[0]} незав./{v[1]} полн." for k, v in s["coverage"].items()))
    for p in s["problems"]: print("   ✗", p)
    for w in s["warnings"]: print("   !", w)
json.dump(summary, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
