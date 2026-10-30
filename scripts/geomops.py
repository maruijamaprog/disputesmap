# -*- coding: utf-8 -*-
"""
Операции над полигонами без сторонних библиотек: объединение, пересечение и разность.

Нужны, чтобы получать зоны споров из готовых границ, не рисуя их вручную. Например:
  разность двух срезов CShapes (Литва 1939 г. минус Литва 1922 г.) даёт Виленский край;
  объединение районов Natural Earth даёт Северную Ирландию без внутренних линий.

Метод: все рёбра колец переводятся в целочисленную сетку 1e-6°, разрезаются в точках пересечения,
из них строится плоский граф, обходятся его грани. Каждая грань классифицируется по
принадлежности к A и B (точка внутри грани проверяется лучом), нужные грани сливаются отменой
общих рёбер. Совпадающие участки границ (а у срезов CShapes и районов NE они совпадают вершина
в вершину) обрабатываются точно.
"""
import math
from collections import defaultdict

Q = 1_000_000


def _polys(geom):
    if geom is None: return []
    if geom["type"] == "Polygon": return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon": return geom["coordinates"]
    return []


def _rings(geoms):
    out = []
    for g in geoms:
        for poly in _polys(g):
            for ring in poly:
                pts = []
                for x, y, *_ in ring:
                    p = (int(round((x + 180.0) * Q)), int(round((y + 90.0) * Q)))
                    if not pts or pts[-1] != p: pts.append(p)
                if len(pts) > 1 and pts[0] == pts[-1]: pts.pop()
                if len(pts) >= 3: out.append(pts)
    return out


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _on_seg(p, a, b):
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def _intersections(s, t):
    """Точки, в которых отрезки s и t касаются или пересекаются (в целой сетке)."""
    (a, b), (c, d) = s, t
    d1, d2, d3, d4 = _cross(c, d, a), _cross(c, d, b), _cross(a, b, c), _cross(a, b, d)
    res = []
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        # собственное пересечение
        den = (a[0] - b[0]) * (c[1] - d[1]) - (a[1] - b[1]) * (c[0] - d[0])
        tnum = (a[0] - c[0]) * (c[1] - d[1]) - (a[1] - c[1]) * (c[0] - d[0])
        x = a[0] + (b[0] - a[0]) * tnum / den
        y = a[1] + (b[1] - a[1]) * tnum / den
        res.append((int(round(x)), int(round(y))))
        return res
    # касания и коллинеарные наложения: концы одного отрезка, лежащие на другом
    if d1 == 0 and _on_seg(a, c, d): res.append(a)
    if d2 == 0 and _on_seg(b, c, d): res.append(b)
    if d3 == 0 and _on_seg(c, a, b): res.append(c)
    if d4 == 0 and _on_seg(d, a, b): res.append(d)
    return res


def _node(segments, cell=40_000):
    """Разрезать отрезки во всех точках взаимного касания/пересечения."""
    segs = list(segments)
    grid = defaultdict(list)
    for i, (a, b) in enumerate(segs):
        x0, x1 = sorted((a[0] // cell, b[0] // cell)); y0, y1 = sorted((a[1] // cell, b[1] // cell))
        for gx in range(x0, x1 + 1):
            for gy in range(y0, y1 + 1):
                grid[(gx, gy)].append(i)
    cuts = defaultdict(set)
    seen = set()
    for ids in grid.values():
        n = len(ids)
        for u in range(n):
            i = ids[u]; si = segs[i]
            for v in range(u + 1, n):
                j = ids[v]
                key = (i, j) if i < j else (j, i)
                if key in seen: continue
                seen.add(key)
                sj = segs[j]
                # быстрый отсев по охвату
                if max(si[0][0], si[1][0]) < min(sj[0][0], sj[1][0]) or max(sj[0][0], sj[1][0]) < min(si[0][0], si[1][0]): continue
                if max(si[0][1], si[1][1]) < min(sj[0][1], sj[1][1]) or max(sj[0][1], sj[1][1]) < min(si[0][1], si[1][1]): continue
                for p in _intersections(si, sj):
                    if p != si[0] and p != si[1]: cuts[i].add(p)
                    if p != sj[0] and p != sj[1]: cuts[j].add(p)
    out = set()
    for i, (a, b) in enumerate(segs):
        pts = [a] + sorted(cuts.get(i, ()), key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2) + [b]
        for p, q in zip(pts, pts[1:]):
            if p != q: out.add((p, q) if p < q else (q, p))
    return out


def _faces(edges):
    """Обход граней плоского графа. Возвращает список циклов (списки вершин) с площадью."""
    nb = defaultdict(list)
    for p, q in edges:
        nb[p].append(q); nb[q].append(p)
    order = {}
    for v, lst in nb.items():
        lst.sort(key=lambda w: math.atan2(w[1] - v[1], w[0] - v[0]))
        order[v] = {w: k for k, w in enumerate(lst)}
    visited = set()
    cycles = []
    for p, q in edges:
        for u0, v0 in ((p, q), (q, p)):
            if (u0, v0) in visited: continue
            cyc = []
            u, v = u0, v0
            while (u, v) not in visited:
                visited.add((u, v)); cyc.append(u)
                lst = nb[v]; k = order[v][u]
                w = lst[(k - 1) % len(lst)]
                u, v = v, w
            cycles.append(cyc)
    return cycles


def _area2(cyc):
    s = 0
    n = len(cyc)
    for i in range(n):
        x1, y1 = cyc[i]; x2, y2 = cyc[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return s


def _pip(pt, rings):
    """Точка внутри набора колец (правило чётности)."""
    x, y = pt
    inside = False
    for r in rings:
        n = len(r)
        j = n - 1
        for i in range(n):
            xi, yi = r[i]; xj, yj = r[j]
            if (yi > y) != (yj > y):
                xx = (xj - xi) * (y - yi) / (yj - yi) + xi
                if x < xx: inside = not inside
            j = i
    return inside


def _sample(cyc):
    """Точка строго внутри грани (обход против часовой — внутренность слева от рёбер)."""
    best, bl = None, -1
    n = len(cyc)
    for i in range(n):
        a, b = cyc[i], cyc[(i + 1) % n]
        l2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        if l2 > bl: bl, best = l2, (a, b)
    (ax, ay), (bx, by) = best
    L = math.sqrt(bl)
    eps = min(L * 0.01, 2.0)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    return (mx - (by - ay) / L * eps, my + (bx - ax) / L * eps)


def _assemble(directed):
    """Собрать кольца из направленных рёбер границы."""
    out = defaultdict(list)
    for u, v in directed: out[u].append(v)
    used = set()
    rings = []
    for u0, v0 in directed:
        if (u0, v0) in used: continue
        ring = []
        u, v = u0, v0
        while (u, v) not in used:
            used.add((u, v)); ring.append(u)
            cands = [w for w in out[v] if (v, w) not in used]
            if not cands: break
            if len(cands) == 1:
                w = cands[0]
            else:
                # как при обходе граней: ближайшее по часовой стрелке от обратного направления ребро
                inc = math.atan2(u[1] - v[1], u[0] - v[0])
                w = min(cands, key=lambda c: (inc - math.atan2(c[1] - v[1], c[0] - v[0])) % (2 * math.pi) or 2 * math.pi)
            u, v = v, w
        if len(ring) >= 3: rings.append(ring)
    return rings


def overlay(a_geoms, b_geoms, op):
    """op: 'union' | 'intersection' | 'difference' (A минус B). Возвращает GeoJSON MultiPolygon или None."""
    ra, rb = _rings(a_geoms), _rings(b_geoms)
    segs = set()
    for r in ra + rb:
        n = len(r)
        for i in range(n):
            p, q = r[i], r[(i + 1) % n]
            if p != q: segs.add((p, q) if p < q else (q, p))
    edges = _node(segs)
    cycles = _faces(edges)
    keep = []
    for cyc in cycles:
        ar = _area2(cyc)
        if ar <= 0: continue
        s = _sample(cyc)
        ia, ib = _pip(s, ra), _pip(s, rb)
        sel = (ia or ib) if op == "union" else (ia and ib) if op == "intersection" else (ia and not ib)
        if sel: keep.append(cyc)
    if not keep: return None
    directed = set()
    for cyc in keep:
        n = len(cyc)
        for i in range(n):
            e = (cyc[i], cyc[(i + 1) % n])
            r = (e[1], e[0])
            if r in directed: directed.discard(r)
            else: directed.add(e)
    rings = _assemble(directed)
    outers = [r for r in rings if _area2(r) > 0]
    holes = [r for r in rings if _area2(r) < 0]
    polys = [[o] for o in outers]
    for h in holes:
        cands = [k for k, o in enumerate(outers) if _pip((h[0][0] + 0.25, h[0][1] + 0.25), [o]) or _pip(h[0], [o])]
        if cands:
            k = min(cands, key=lambda k: _area2(outers[k]))
            polys[k].append(h)
    def deg(r):
        pts = [[round(x / Q - 180.0, 6), round(y / Q - 90.0, 6)] for x, y in r]
        return pts + [pts[0]]
    # GeoJSON: внешние кольца против часовой, дыры по часовой — как получилось при обходе
    return {"type": "MultiPolygon", "coordinates": [[deg(r) for r in p] for p in polys]}


def area_km2(geom):
    R = 6371.0088
    def ring(r):
        a = 0.0
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            a += math.radians(x2 - x1) * (2 + math.sin(math.radians(y1)) + math.sin(math.radians(y2)))
        return abs(a * R * R / 2)
    return sum(ring(p[0]) - sum(ring(h) for h in p[1:]) for p in _polys(geom))


def polylabel(geom, precision_deg=0.02):
    """Полюс недоступности самого большого полигона (алгоритм Mapbox polylabel) — для подписей."""
    import heapq
    polys = _polys(geom)
    if not polys: return None
    poly = max(polys, key=lambda p: area_km2({"type": "Polygon", "coordinates": [p[0]]}))
    rings = [[(x, y) for x, y, *_ in r] for r in poly]
    outer = rings[0]
    xs = [p[0] for p in outer]; ys = [p[1] for p in outer]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    size = min(w, h)
    if size == 0: return [round(minx, 4), round(miny, 4)]
    precision = max(precision_deg, size / 200)

    def dist(x, y):
        inside = False; md = float("inf")
        for r in rings:
            n = len(r); j = n - 1
            for i in range(n):
                ax, ay = r[i]; bx, by = r[j]
                if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax: inside = not inside
                dx, dy = bx - ax, by - ay
                if dx or dy:
                    t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
                    px, py = ax + t * dx, ay + t * dy
                else:
                    px, py = ax, ay
                md = min(md, (x - px) ** 2 + (y - py) ** 2)
                j = i
        return (1 if inside else -1) * math.sqrt(md)

    def cell(x, y, hh):
        d = dist(x, y)
        return (-(d + hh * math.sqrt(2)), d, x, y, hh)

    heap = []
    hh = size / 2
    x = minx
    while x < maxx:
        y = miny
        while y < maxy:
            heapq.heappush(heap, cell(x + hh, y + hh, hh)); y += size
        x += size
    # центроид как первое приближение
    a2 = 0; cx = cy = 0
    for i in range(len(outer) - 1):
        (x1, y1), (x2, y2) = outer[i], outer[i + 1]
        f = x1 * y2 - x2 * y1; a2 += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f
    if a2: best = cell(cx / (3 * a2), cy / (3 * a2), 0)
    else: best = cell(xs[0], ys[0], 0)
    bb = cell(minx + w / 2, miny + h / 2, 0)
    if bb[1] > best[1]: best = bb
    n = 0
    while heap and n < 4000:
        c = heapq.heappop(heap); n += 1
        if c[1] > best[1]: best = c
        if -c[0] - best[1] <= precision: continue
        hh = c[4] / 2
        for dx in (-hh, hh):
            for dy in (-hh, hh):
                heapq.heappush(heap, cell(c[2] + dx, c[3] + dy, hh))
    return [round(best[2], 4), round(best[3], 4)]
