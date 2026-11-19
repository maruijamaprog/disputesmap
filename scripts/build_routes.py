# -*- coding: utf-8 -*-
"""
Слой «Транспортные маршруты»: data/routes.json → site/data/routes.json (только стандартная библиотека Python).

Проверки:
  * каждая ссылка на источник существует; у даты появления и даты запуска — не меньше двух независимых
    источников или примечание в review.notes;
  * узел с кодом страны лежит в её полигоне Natural Earth 10m (допуск 15 км: порты и пограничные пункты);
  * морской участок почти не проходит по суше Natural Earth 50m (не более 3% длины без учёта 20 км у портов);
  * линии, пересекающие 180-й меридиан, разрезаются на две части.
Запуск: python scripts/build_routes.py --raw raw --out site/data
"""
import argparse, json, math, os, sys
from collections import OrderedDict as OD

OPEN = 99999999


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def polys(g):
    return [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]


def bbox(g):
    xs = [p[0] for poly in polys(g) for p in poly[0]]; ys = [p[1] for poly in polys(g) for p in poly[0]]
    return min(xs), min(ys), max(xs), max(ys)


def inside(x, y, g):
    for poly in polys(g):
        c = False
        for ring in poly:
            j = len(ring) - 1
            for i in range(len(ring)):
                xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    c = not c
                j = i
        if c:
            return True
    return False


def km(a, b):
    """Расстояние по большому кругу, км."""
    lo1, la1, lo2, la2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(min(1, math.sqrt(h)))


def dist_to_poly_km(x, y, g):
    best = 1e9
    for poly in polys(g):
        for ring in poly:
            for i in range(0, len(ring), 2):
                d = km((x, y), ring[i])
                if d < best: best = d
    return best


def dint(s, end=False):
    """«1932», «2013-11», «2015-08-03» → ГГГГММДД (начало периода)."""
    if s is None: return None
    p = str(s).split("-")
    y = int(p[0]); m = int(p[1]) if len(p) > 1 else 1; d = int(p[2]) if len(p) > 2 else 1
    return y * 10000 + m * 100 + d


def split_antimeridian(coords):
    """Разрезать ломаную на части там, где соседние точки разделены 180-м меридианом."""
    parts, cur = [], [coords[0]]
    for a, b in zip(coords, coords[1:]):
        if abs(b[0] - a[0]) > 180:
            bx = b[0] + 360 if b[0] < 0 else b[0] - 360          # b, перенесённая на сторону a
            edge = 180 if a[0] > 0 else -180
            t = (edge - a[0]) / (bx - a[0])
            lat = a[1] + t * (b[1] - a[1])
            cur.append([edge, round(lat, 4)]); parts.append(cur)
            cur = [[-edge, round(lat, 4)], b]
        else:
            cur.append(b)
    parts.append(cur)
    return parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw"); ap.add_argument("--out", default="site/data"); ap.add_argument("--data", default="data/routes.json")
    a = ap.parse_args()
    D = load(a.data)
    probs, warns = [], []

    countries = {}
    for f in load(os.path.join(a.raw, "ne_10m_admin_0_countries.geojson"))["features"]:
        iso = f["properties"].get("ADM0_A3")
        countries.setdefault(iso, []).append((bbox(f["geometry"]), f["geometry"]))
    land = [(bbox(f["geometry"]), f["geometry"]) for f in load(os.path.join(a.raw, "ne_50m_admin_0_countries.geojson"))["features"]]

    def on_land(x, y):
        return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] and inside(x, y, g) for b, g in land)

    # --- узлы
    nodes, wps = D["nodes"], D["waypoints"]
    for k, n in nodes.items():
        if not n["iso"]:
            continue
        cand = countries.get(n["iso"], [])
        ok = any(b[0] <= n["lon"] <= b[2] and b[1] <= n["lat"] <= b[3] and inside(n["lon"], n["lat"], g) for b, g in cand)
        if not ok:
            d = min((dist_to_poly_km(n["lon"], n["lat"], g) for _, g in cand), default=1e9)
            if d > 15: probs.append(f"узел {k} ({n['ru']}): вне {n['iso']} на {d:.0f} км")
            else: warns.append(f"узел {k}: у границы {n['iso']} ({d:.1f} км) — порт или погранпункт")
    for k, w in wps.items():
        if on_land(w["lon"], w["lat"]): probs.append(f"путевая точка {k} на суше")

    def xy(nid):
        if nid in nodes: return [nodes[nid]["lon"], nodes[nid]["lat"]]
        if nid in wps: return [wps[nid]["lon"], wps[nid]["lat"]]
        raise KeyError(nid)

    feats, through = [], OD()
    for ri, r in enumerate(D["routes"]):
        rid = r["id"]
        ids = {s["id"]: s for s in r["sources"]}
        # ссылки
        refs = [x for c in r["capacity"] for x in c["source_ids"]] + [x for s in r["volumes"] for p in s["points"] for x in p["source_ids"]] \
            + [x for e in r["history"] for x in e["source_ids"]]
        for x in refs:
            if x not in ids: probs.append(f"{rid}: нет источника {x}")
        # даты: ≥2 независимых источника
        org = lambda s: s["author"].split(" (")[0]
        for key, val in (("appear", r["appear"]), ("operate", r["operate"])):
            if val is None: continue
            orgs = {org(s) for s in r["sources"] if key in s["supports"]}
            if len(orgs) < 2 and not r["review"]["notes"]:
                probs.append(f"{rid}: «{key}» — {len(orgs)} независимых источников и нет примечаний")
            elif len(orgs) < 2:
                warns.append(f"{rid}: «{key}» — {len(orgs)} независимых источников (см. примечания)")
        r_s, r_o = dint(r["appear"]), dint(r["operate"])
        isos = OD()
        for b in r["branches"]:
            for si, seg in enumerate(b["segments"]):
                coords = [xy(n) for n in seg["nodes"]]
                for n in seg["nodes"]:
                    if n in nodes and nodes[n]["iso"]: isos[nodes[n]["iso"]] = True
                s = dint(seg["appear"]) or r_s
                o = OPEN if seg["planned"] else (dint(seg["operate"]) or r_o or OPEN)
                if seg["mode"] == "sea":
                    total = landkm = 0.0
                    for p, q in zip(coords, coords[1:]):
                        L = km(p, q); n = max(2, int(L / 5))
                        for i in range(1, n):
                            t = i / n; x = p[0] + t * (q[0] - p[0]); y = p[1] + t * (q[1] - p[1])
                            if abs(q[0] - p[0]) > 180: continue
                            if km((x, y), coords[0]) < 20 or km((x, y), coords[-1]) < 20: continue
                            total += L / n
                            if on_land(x, y): landkm += L / n
                    share = landkm / total if total else 0
                    msg = f"{rid}/{b['id']}#{si}: по суше {landkm:.0f} из {total:.0f} км ({share:.0%})"
                    if share > 0.03: probs.append(msg)
                    elif landkm > 0: warns.append(msg)
                for part in split_antimeridian(coords):
                    feats.append(OD(type="Feature", properties=OD(r=rid, b=b["id"], s=s, o=o, c=r["color"], k=ri, sea=1 if seg["mode"] == "sea" else 0),
                                    geometry=OD(type="LineString", coordinates=[[round(c[0], 4), round(c[1], 4)] for c in part])))
        through[rid] = list(isos.keys())

    # --- справки «Значение»: ссылки на источники, пометка «1 источник» (меньше двух независимых организаций)
    analyses = D.get("analyses") or {}
    for r in D["routes"]:
        if r.get("analysis") and r["analysis"] not in analyses:
            probs.append(f"{r['id']}: нет справки {r['analysis']}")
    for aid, an in analyses.items():
        ids = {s["id"]: s for s in an["sources"]}
        if len(ids) != len(an["sources"]):
            probs.append(f"справка {aid}: повторяются id источников")
        org = lambda s: s["author"].split(" (")[0]

        def check(pt, where):
            for x in pt["source_ids"]:
                if x not in ids: probs.append(f"справка {aid}/{where}: нет источника {x}")
            if not pt["source_ids"]: probs.append(f"справка {aid}/{where}: пункт без источников")
            pt["single"] = len({org(ids[x]) for x in pt["source_ids"] if x in ids}) < 2
        for sec in an["general"]:
            for i, pt in enumerate(sec["points"]): check(pt, f"{sec['id']}#{i}")
        codes = set()
        for ac in an["actors"]:
            if ac["code"] in codes: probs.append(f"справка {aid}: страна {ac['code']} повторяется")
            codes.add(ac["code"])
            if ac["group"] not in ("route", "external"): probs.append(f"справка {aid}/{ac['code']}: группа {ac['group']}")
            for part in ("econ", "pol", "risks"):
                for i, pt in enumerate(ac[part]): check(pt, f"{ac['code']}.{part}#{i}")
        pts = [pt for s in an["general"] for pt in s["points"]] + [pt for ac in an["actors"] for p in ("econ", "pol", "risks") for pt in ac[p]]
        print(f"справка {aid}: стран {len(an['actors'])}, пунктов {len(pts)}, из них по одному источнику {sum(p.get('single', True) for p in pts)}, источников {len(ids)}")

    for w in warns: print("  !", w)
    for p in probs: print("  ✗", p)
    if probs:
        sys.exit("Ошибки в данных маршрутов — сборка остановлена")

    out = OD(meta=D["meta"], nodes=nodes, routes=D["routes"], through=through, analyses=analyses, geo=OD(type="FeatureCollection", features=feats))
    path = os.path.join(a.out, "routes.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"routes.json: маршрутов {len(D['routes'])}, линий {len(feats)}, {os.path.getsize(path)/1e3:.0f} КБ")


if __name__ == "__main__":
    main()
