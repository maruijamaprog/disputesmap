# -*- coding: utf-8 -*-
"""
Данные режима «Военные конфликты» → site/data/wars.json (только стандартная библиотека Python).

Вход (папка raw/, см. scripts/download_extra.bat):
  ucdp-prio-acd-261-csv.zip       UCDP/PRIO Armed Conflict Dataset 26.1 (1946–2025), CC BY 4.0
  Inter-StateWarData_v4.0.csv     Correlates of War, межгосударственные войны (используются 1900–1945)
  Extra-StateWarData_v4.0.csv     Correlates of War, внесистемные (колониальные) войны
  Intra-State-Wars-v5.1.zip       Correlates of War, внутренние войны, файл участников-государств
  CShapes-2.0.geojson             для проверки кодов Gleditsch–Ward
Плюс data/wars_manual.json — ручные записи 2026 г. со ссылками на источники.

Правила:
  * 1900–1945 — Correlates of War (только войны: ≥1000 погибших в бою за 12 месяцев), 1946–2025 — UCDP/PRIO.
  * UCDP: конфликт учитывается в году, если в нём ≥25 погибших в бою и одна из сторон — правительство.
    Внутри года участие длится с 1 января (или с даты начала эпизода) по 31 декабря (или по дате окончания эпизода).
  * 2026 г.: конфликты, активные в 2025 г. по UCDP, продолжаются на карте с пометкой «не проверено» (флаг u),
    пока редакция не подтвердит или не закроет их записью «set» в wars_manual.json (не меньше двух независимых
    источников на каждое решение). Новые конфликты 2026 г. — записи «conflicts» там же.
  * Коды COW переводятся в коды Gleditsch–Ward (они совпадают, кроме Сербии до 1 декабря 1918 г.: COW 345 → GW 340).

Формат участия: [gw, сторона (0 — A, 1 — B), роль (1 — основная, 2 — поддержка войсками), с, по, интенсивность, имя?, флаг?]
Запуск: python scripts/build_wars.py --raw raw --out site/data
"""
import argparse, csv, io, json, os, sys, zipfile, datetime
from collections import defaultdict

TODAY = int(datetime.date.today().strftime("%Y%m%d"))
COW_END = 19451231

def ymd(y, m, d, end=False):
    y, m, d = int(y), int(m), int(d)
    if y < 0: return None
    if m < 1: m = 12 if end else 1
    if d < 1:
        if end:
            d = (datetime.date(y + (m == 12), m % 12 + 1, 1) - datetime.timedelta(days=1)).day
        else:
            d = 1
    return y * 10000 + m * 100 + d

def iso(n):
    return f"{n // 10000:04d}-{n // 100 % 100:02d}-{n % 100:02d}"

def cow_to_gw(c, date):
    c = int(c)
    if c == 345 and date < 19181201: return 340
    return c

RU_NAMES = {
    # межгосударственные войны COW
    "Boxer Rebellion": "Восстание ихэтуаней", "Sino-Russian": "Русско-китайская война", "Russo-Japanese": "Русско-японская война",
    "Third Central American": "Третья центральноамериканская война", "Fourth Central American": "Четвёртая центральноамериканская война",
    "Second Spanish-Moroccan": "Вторая испано-марокканская война", "Italian-Turkish": "Итало-турецкая война",
    "First Balkan": "Первая Балканская война", "Second Balkan": "Вторая Балканская война", "World War I": "Первая мировая война",
    "Estonian Liberation": "Освободительная война Эстонии", "Latvian Liberation": "Освободительная война Латвии",
    "Russo-Polish": "Советско-польская война", "Hungarian Adversaries": "Война Венгрии с Чехословакией и Румынией",
    "Second Greco-Turkish": "Вторая греко-турецкая война", "Franco-Turkish": "Франко-турецкая война",
    "Lithuanian-Polish": "Польско-литовская война", "Manchurian": "Конфликт на Китайско-Восточной железной дороге",
    "Second Sino-Japanese": "Японо-китайская война в Маньчжурии", "Chaco": "Чакская война", "Saudi-Yemeni": "Саудовско-йеменская война",
    "Conquest of Ethiopia": "Итало-эфиопская война", "Third Sino-Japanese": "Японо-китайская война",
    "Changkufeng": "Бои у озера Хасан", "Nomonhan": "Бои на Халхин-Голе", "World War II": "Вторая мировая война",
    "Russo-Finnish": "Советско-финская война", "Franco-Thai": "Франко-тайская война",
    # внесистемные войны COW
    "Second Boer War": "Англо-бурская война", "American-Philippine": "Филиппино-американская война",
    "South West African Revolt": "Восстание гереро и нама", "Maji-Maji Revolt": "Восстание маджи-маджи",
    "Third British-Afghan": "Третья англо-афганская война", "Iraqi-British": "Восстание в Ираке против британского мандата",
    "Rif Rebellion": "Рифская война", "Italian-Sanusi": "Итало-сенуситская война", "Indonesian": "Война за независимость Индонезии",
    "Franco-Syrian": "Франко-сирийская война", "Franco-Druze": "Восстание друзов", "Younghusband Expedition": "Британская экспедиция в Тибет",
    "Moroccan Berber": "Война с берберами в Марокко",
    # внутренние войны COW
    "Russian Civil War of 1917-1920": "Гражданская война в России", "Spanish Civil War of 1936-1939": "Гражданская война в Испании",
    "Finnish Civil War of 1918": "Гражданская война в Финляндии", "Kronstadt Rebellion of 1921": "Кронштадтское восстание",
    "Green Rebellion of 1920-1921": "Тамбовское восстание", "Bashmachi in Turketsan Revolt of 1920-1924": "Басмаческое движение в Туркестане",
    "Chinese Civil War phase 1 of 1930-1936": "Гражданская война в Китае (первый этап)", "Bloody Sunday War of 1905-1906": "Революция 1905–1906 гг. в России",
    "Cristeros Revolt of 1926-1929": "Война кристерос", "Chinese Northern Expedition of 1926-1928": "Северный поход",
    "Greek Civil War round 2 of 1944-1945": "Гражданская война в Греции (декабрь 1944)",
}

def read_csv_text(text):
    return list(csv.DictReader(io.StringIO(text)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw"); ap.add_argument("--out", default="site/data")
    ap.add_argument("--manual", default="data/wars_manual.json")
    a = ap.parse_args()
    log = []
    def say(*x):
        s = " ".join(str(v) for v in x); print(s); log.append(s)

    gw_known = set()
    cs = json.load(open(os.path.join(a.raw, "CShapes-2.0.geojson"), encoding="utf-8"))["features"]
    for f in cs: gw_known.add(f["properties"]["gwcode"])
    unknown = defaultdict(int)
    def check(g):
        if g and g not in gw_known: unknown[g] += 1
        return g

    conflicts = []

    # ------------------------------------------------------------------ COW, межгосударственные (1900–1945)
    inter = list(csv.DictReader(open(os.path.join(a.raw, "Inter-StateWarData_v4.0.csv"), encoding="latin-1", newline=None)))
    wars = defaultdict(list)
    for r in inter: wars[(r["WarNum"], r["WarName"])].append(r)
    for (num, name), rows in sorted(wars.items(), key=lambda kv: float(kv[0][0])):
        parts = []
        for r in rows:
            for k in ("1", "2"):
                s = ymd(r[f"StartYear{k}"], r[f"StartMonth{k}"], r[f"StartDay{k}"])
                e = ymd(r[f"EndYear{k}"], r[f"EndMonth{k}"], r[f"EndDay{k}"], end=True)
                if s is None: continue
                if e is None: e = s
                if e < 19000101 or s > COW_END: continue
                s, e = max(s, 19000101), min(e, COW_END)
                parts.append([check(cow_to_gw(r["ccode"], s)), int(r["Side"]) - 1, 1, s, e, 2])
        if not parts: continue
        conflicts.append({"id": f"cow-inter-{num}", "src": "cow", "kind": "interstate",
                          "name": {"ru": RU_NAMES.get(name), "en": name}, "parts": parts,
                          "start": min(p[3] for p in parts), "end": max(p[4] for p in parts)})

    # ------------------------------------------------------------------ COW, внесистемные (колониальные)
    extra = list(csv.DictReader(open(os.path.join(a.raw, "Extra-StateWarData_v4.0.csv"), encoding="latin-1", newline=None)))
    wars = defaultdict(list)
    for r in extra: wars[(r["WarNum"], r["WarName"])].append(r)
    for (num, name), rows in sorted(wars.items(), key=lambda kv: float(kv[0][0])):
        parts = []
        nonstate = set()
        for r in rows:
            for k in ("1", "2"):
                endday = r.get(f"EndDay{k}") or r.get(f"EndDay{k} ") or "-9"
                s = ymd(r[f"StartYear{k}"], r[f"StartMonth{k}"], r[f"StartDay{k}"])
                e = ymd(r[f"EndYear{k}"], r[f"EndMonth{k}"], endday, end=True)
                if s is None: continue
                if e is None: e = s
                if e < 19000101 or s > COW_END: continue
                s, e = max(s, 19000101), min(e, COW_END)
                if int(r["ccode1"]) > 0: parts.append([check(cow_to_gw(r["ccode1"], s)), 0, 1, s, e, 2])
                if int(r["ccode2"]) > 0: parts.append([check(cow_to_gw(r["ccode2"], s)), 1, 1, s, e, 2])
                if r["SideB"] not in ("-8", "-9", ""): nonstate.add((r["SideB"], s, e))
        if not parts: continue
        for n, s, e in sorted(nonstate): parts.append([0, 1, 1, s, e, 2, n])
        conflicts.append({"id": f"cow-extra-{num}", "src": "cow", "kind": "extrastate",
                          "name": {"ru": RU_NAMES.get(name), "en": name}, "parts": parts,
                          "start": min(p[3] for p in parts), "end": max(p[4] for p in parts)})

    # ------------------------------------------------------------------ COW, внутренние (файл участников)
    zf = zipfile.ZipFile(os.path.join(a.raw, "Intra-State-Wars-v5.1.zip"))
    pname = next(n for n in zf.namelist() if "participants" in n.lower() and n.lower().endswith(".csv"))
    intra = read_csv_text(zf.read(pname).decode("latin-1"))
    wname = next(n for n in zf.namelist() if "wars" in n.lower() and "participant" not in n.lower() and n.lower().endswith(".csv"))
    wrows = read_csv_text(zf.read(wname).decode("latin-1"))
    gov_of = {r["WarNum"]: int(r["CcodeA"]) for r in wrows}
    # в файле участников название одной войны иногда записано по-разному (лишний пробел, другие годы) —
    # группируем по номеру, а название берём из файла войн
    norm = lambda x: " ".join(x.split())
    name_of = {r["WarNum"]: norm(r["WarName"]) for r in wrows}
    wars = defaultdict(list)
    for r in intra: wars[r["WarNum"]].append(r)
    for num, rows in sorted(wars.items(), key=lambda kv: float(kv[0])):
        name = name_of.get(num) or norm(rows[0]["WarName"])
        parts = []
        foreign = False
        for r in rows:
            for k in ("1", "2", "3", "4"):
                s = ymd(r[f"StartYr{k}"], r[f"StartMo{k}"], r[f"StartDy{k}"])
                e = ymd(r[f"EndYr{k}"], r[f"EndMo{k}"], r[f"EndDy{k}"], end=True)
                if s is None: continue
                if e is None or e < 0: e = s
                if e < 19000101 or s > COW_END: continue
                s, e = max(s, 19000101), min(e, COW_END)
                ca, cb = int(r["CcodeA"]), int(r["CcodeB"])
                if ca > 0: parts.append([check(cow_to_gw(ca, s)), 0, 1, s, e, 2])
                elif r["SideA"] not in ("-8", "-9", ""): parts.append([0, 0, 1, s, e, 2, r["SideA"]])
                if cb > 0: parts.append([check(cow_to_gw(cb, s)), 1, 1, s, e, 2])
                elif r["SideB"] not in ("-8", "-9", ""): parts.append([0, 1, 1, s, e, 2, r["SideB"]])
            if r["Intnl"] == "1": foreign = True
        if not parts or not any(p[0] for p in parts): continue
        # государства, вмешавшиеся во внутреннюю войну, — роль «поддержка» (основная сторона — правительство страны)
        main_gov = gov_of.get(num) if gov_of.get(num, -8) > 0 else None
        for p in parts:
            if p[0] and main_gov and p[0] != cow_to_gw(main_gov, p[3]): p[2] = 2
        conflicts.append({"id": f"cow-intra-{num}", "src": "cow", "kind": "internationalized" if foreign else "intrastate",
                          "name": {"ru": RU_NAMES.get(name), "en": name}, "parts": parts,
                          "start": min(p[3] for p in parts), "end": max(p[4] for p in parts)})
    say("COW (1900–1945): войн", len(conflicts))

    # ------------------------------------------------------------------ UCDP/PRIO 1946–2025
    zf = zipfile.ZipFile(os.path.join(a.raw, "ucdp-prio-acd-261-csv.zip"))
    acd = read_csv_text(zf.read(zf.namelist()[0]).decode("utf-8"))
    last_year = max(int(r["year"]) for r in acd)
    say("UCDP: строк", len(acd), "последний год", last_year)
    KIND = {"1": "extrastate", "2": "interstate", "3": "intrastate", "4": "internationalized"}
    INC = {"1": "territory", "2": "government", "3": "both"}
    by_id = defaultdict(list)
    for r in acd: by_id[r["conflict_id"]].append(r)
    nucdp = 0
    for cid, rows in by_id.items():
        rows.sort(key=lambda r: int(r["year"]))
        parts, ky = [], []
        for r in rows:
            y = int(r["year"])
            s, e = y * 10000 + 101, y * 10000 + 1231
            ep_start = r["start_date2"]
            if ep_start and int(ep_start[:4]) == y: s = int(ep_start.replace("-", ""))
            if r["ep_end"] == "1" and r["ep_end_date"] and int(r["ep_end_date"][:4]) == y:
                e = int(r["ep_end_date"].replace("-", ""))
            e = max(e, s)
            it = int(r["intensity_level"])
            def gws(v): return [int(x) for x in v.replace(" ", "").split(",") if x]
            for side, (prim, sec, names) in enumerate([(r["gwno_a"], r["gwno_a_2nd"], r["side_a"]), (r["gwno_b"], r["gwno_b_2nd"], r["side_b"])]):
                for g in gws(prim): parts.append([check(g), side, 1, s, e, it])
                for g in gws(sec): parts.append([check(g), side, 2, s, e, it])
                if not gws(prim):
                    parts.append([0, side, 1, s, e, it, names])
            k = KIND[r["type_of_conflict"]]
            if not ky or ky[-1][1] != k: ky.append([y, k])
            # 2026: продолжение без проверки
            if y == last_year and r["ep_end"] != "1":
                s2, e2 = (last_year + 1) * 10000 + 101, TODAY
                if e2 >= s2:
                    for side, (prim, sec, names) in enumerate([(r["gwno_a"], r["gwno_a_2nd"], r["side_a"]), (r["gwno_b"], r["gwno_b_2nd"], r["side_b"])]):
                        for g in gws(prim): parts.append([g, side, 1, s2, e2, it, None, "u"])
                        for g in gws(sec): parts.append([g, side, 2, s2, e2, it, None, "u"])
                        if not gws(prim): parts.append([0, side, 1, s2, e2, it, names, "u"])
        # слить смежные годы с одинаковыми параметрами
        parts.sort(key=lambda p: (p[0], p[1], p[2], str(p[6] if len(p) > 6 else ""), p[3]))
        merged = []
        for p in parts:
            q = merged[-1] if merged else None
            key = lambda x: (x[0], x[1], x[2], x[5], x[6] if len(x) > 6 else None, x[7] if len(x) > 7 else None)
            if q and key(q) == key(p) and datetime.date(*map(int, iso(q[4]).split("-"))) + datetime.timedelta(days=1) >= datetime.date(*map(int, iso(p[3]).split("-"))):
                q[4] = max(q[4], p[4])
            else:
                merged.append(list(p))
        for p in merged:
            while len(p) > 6 and p[-1] is None: p.pop()
        last = rows[-1]
        conflicts.append({
            "id": f"ucdp-{cid}", "src": "ucdp", "kind": KIND[last["type_of_conflict"]], "ky": ky if len(ky) > 1 else None,
            "inc": INC.get(last["incompatibility"]), "terr": last["territory_name"] or None,
            "loc": [check(int(x)) for x in last["gwno_loc"].replace(" ", "").split(",") if x],
            "location": last["location"], "parts": merged,
            "start": int(rows[0]["start_date"].replace("-", "")),
            "end": None if last["ep_end"] != "1" and int(last["year"]) == last_year else max(p[4] for p in merged if len(p) < 8 or p[7] != "u"),
            "years": [[int(r["year"]), int(r["intensity_level"])] for r in rows],
        })
        nucdp += 1
    say("UCDP: конфликтов", nucdp)

    # ------------------------------------------------------------------ ручные записи
    manual = {"conflicts": [], "set": [], "sources": []}
    if os.path.exists(a.manual):
        manual = json.load(open(a.manual, encoding="utf-8"))
    src_by = {s["id"]: s for s in manual.get("sources", [])}
    def srcs(ids):
        miss = [i for i in ids if i not in src_by]
        if miss: raise SystemExit(f"wars_manual.json: нет источников {miss}")
        return [{k: v for k, v in src_by[i].items() if k != "id"} for i in ids]
    def d8(s): return int(s.replace("-", "")) if s else None
    def next_day(n):
        d = datetime.date(n // 10000, n // 100 % 100, n % 100) + datetime.timedelta(days=1)
        return int(d.strftime("%Y%m%d"))
    def unflag(p):
        q = list(p[:7])
        while len(q) > 6 and q[-1] is None: q.pop()
        return q
    by = {c["id"]: c for c in conflicts}
    nset = {"verified": 0, "closed": 0, "noted": 0}
    for op in manual.get("set", []):
        # Правка продолжения 2026 г. по источникам (см. docs/VERIFICATION_REPORT.md):
        #   from        — начало проверенного периода 2026 г. (раньше — удалить);
        #   verified_to — до этой даты снять флаг «не проверено», после — оставить;
        #   to          — конфликт завершён этой датой (перемирие), всё позже удалить;
        #   clip        — применить «to» и к годам UCDP (уточнить конец последнего эпизода);
        #   int         — интенсивность в 2026 г. по источникам (1 — 25–999, 2 — ≥1000 погибших);
        #   keep_u      — коды GW, участие которых в 2026 г. не подтверждено источниками;
        #   only_note   — только добавить пояснение и источники, флаг не снимать.
        c = by.get(op["id"])
        if not c: raise SystemExit(f"wars_manual.json: нет конфликта {op['id']}")
        f, vt, to = d8(op.get("from")), d8(op.get("verified_to")), d8(op.get("to"))
        keep = set(op.get("keep_u", []))
        out_parts = []
        for p in c["parts"]:
            u = len(p) > 7 and p[7] == "u"
            if not u:
                if to and op.get("clip"):
                    if p[3] > to: continue
                    p[4] = min(p[4], to)
                out_parts.append(p); continue
            if op.get("only_note"): out_parts.append(p); continue
            if f:
                if p[4] < f: continue
                p[3] = max(p[3], f)
            if to:
                if p[3] > to: continue
                p[4] = min(p[4], to)
            if op.get("int"): p[5] = op["int"]
            if p[0] in keep: out_parts.append(p); continue
            if vt and p[4] > vt:
                if p[3] <= vt:
                    head = unflag(p); head[4] = vt
                    tail = list(p); tail[3] = next_day(vt)
                    out_parts += [head, tail]
                else:
                    out_parts.append(p)
            else:
                out_parts.append(unflag(p))
        c["parts"] = out_parts
        if to: c["end"] = to; nset["closed"] += 1
        elif op.get("only_note"): nset["noted"] += 1
        else: nset["verified"] += 1
        c["note"] = op.get("note"); c["sources"] = srcs(op.get("sources", []))
    say("Ручные правки 2026 г.:", nset)
    for m in manual.get("conflicts", []):
        parts = []
        for p in m["parts"]:
            row = [p["g"], p["side"], p["role"], d8(p["from"]), d8(p["to"]) if p.get("to") else TODAY, p["int"]]
            if p.get("name"): row.append(p["name"])
            parts.append(row)
        conflicts.append({"id": m["id"], "src": "manual", "kind": m["kind"], "name": m["name"], "inc": m.get("inc"),
                          "terr": m.get("terr"), "loc": m.get("loc", []), "location": m.get("location"),
                          "parts": parts, "start": d8(m["start"]), "end": d8(m.get("end")),
                          "years": [[2026, max(p[5] for p in parts)]], "note": m.get("note"), "sources": srcs(m.get("sources", []))})
    say("Ручные конфликты 2026 г.:", len(manual.get("conflicts", [])))

    if unknown: say("Коды GW вне CShapes (не будут закрашены):", dict(unknown))
    # компактный вывод
    for c in conflicts:
        for k in [k for k, v in c.items() if v is None]: del c[k]
        if c.get("name") and not c["name"].get("ru"): c["name"] = {"en": c["name"]["en"]}
    out = {"meta": {"built": datetime.date.today().isoformat(), "ucdp_version": "26.1", "ucdp_last_year": last_year,
                    "sources": {"UCDP/PRIO Armed Conflict Dataset 26.1": "Uppsala Conflict Data Program / PRIO, CC BY 4.0 (Gleditsch et al. 2002; Davies et al. 2025)",
                                "Correlates of War War Data v4.0, Intra-State v5.1": "Sarkees & Wayman 2010; Dixon & Sarkees 2016"}},
           "conflicts": conflicts}
    path = os.path.join(a.out, "wars.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    say(f"wars.json: конфликтов {len(conflicts)}, {os.path.getsize(path)/1e6:.2f} МБ")

if __name__ == "__main__":
    main()
