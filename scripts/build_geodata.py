# -*- coding: utf-8 -*-
"""
Сборка геоданных сайта из исходных датасетов (только стандартная библиотека Python 3.9+, без GDAL).

Вход (папка raw/, см. scripts/download_raw.bat):
  CShapes-2.0.geojson                     — CShapes 2.0 (ETH Zürich), CC BY-NC 4.0
  ne_10m_admin_0_disputed_areas.geojson   — Natural Earth 5.1.x, public domain
  ne_10m_admin_1_states_provinces.geojson — Natural Earth 5.1.x, public domain
  ne_50m_admin_0_countries.geojson        — Natural Earth 5.1.x, public domain
  ne_10m_admin_0_countries.geojson        — Natural Earth 5.1.x (названия RU/EN, коды ISO)
Плюс data/disputes.json (метаданные споров) и scripts/geometry_sources.json (откуда брать полигон каждой зоны).

Выход (site/data/):
  countries.<эпоха>.topo.json — государства и колонии CShapes по эпохам (общие дуги, упрощение Висвалингам)
  land.topo.json              — суша (Natural Earth 50m) как нейтральная подложка
  disputes.topo.json          — полигоны зон споров + точечные маркеры для мелких островов
  units.json                  — справочник единиц CShapes: код стороны, названия RU/EN
  meta.json                   — эпохи, версии, годы событий

Запуск:  python scripts/build_geodata.py --raw raw --out site/data
"""
import argparse, heapq, json, math, os, sys, datetime
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geomops import overlay, polylabel   # noqa: E402

DATASET_END = 20191231          # последняя дата CShapes 2.0
OPEN_END = 99991231
ERAS = [(1900, 1918), (1919, 1945), (1946, 1991), (1992, 2026)]

# ----------------------------------------------------------------------------- utils
def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def polygons(geom):
    if geom is None: return []
    if geom["type"] == "Polygon": return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon": return geom["coordinates"]
    return []

def ring_area_km2(r):
    R = 6371.0088; a = 0.0
    for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
        a += math.radians(x2 - x1) * (2 + math.sin(math.radians(y1)) + math.sin(math.radians(y2)))
    return abs(a * R * R / 2)

def geom_area_km2(geom):
    return sum(ring_area_km2(p[0]) - sum(ring_area_km2(h) for h in p[1:]) for p in polygons(geom))

def label_point(geom):
    """Центр самого большого кольца (для маркеров мелких островов)."""
    best, ba = None, -1
    for p in polygons(geom):
        a = ring_area_km2(p[0])
        if a > ba:
            ba, best = a, p[0]
    xs = [pt[0] for pt in best]; ys = [pt[1] for pt in best]
    return [round(sum(xs) / len(xs), 5), round(sum(ys) / len(ys), 5)]

# ----------------------------------------------------------------------------- topology
Q = 1_000_000  # внутренняя сетка квантования (1e-6°) для поиска общих вершин

def qpt(x, y):
    return (int(round((x + 180.0) * Q)), int(round((y + 90.0) * Q)))

def build_topology(geoms):
    """geoms: список геометрий GeoJSON. Возвращает (arcs, shapes),
    arcs — список дуг (списки точек в целочисленной сетке), shapes — для каждой геометрии список полигонов,
    полигон — список колец, кольцо — список индексов дуг (~i для обратного направления)."""
    rings_all = []   # (geom_idx, poly_idx, ring_idx, pts)
    for gi, g in enumerate(geoms):
        for pi, poly in enumerate(polygons(g)):
            for ri, ring in enumerate(poly):
                pts = [qpt(x, y) for x, y, *_ in ring]
                # убрать замыкающую точку и подряд идущие дубли
                clean = []
                for p in pts:
                    if not clean or clean[-1] != p: clean.append(p)
                if len(clean) > 1 and clean[0] == clean[-1]: clean.pop()
                if len(clean) >= 3:
                    rings_all.append((gi, pi, ri, clean))
    # 1. узлы: точки, у которых встречаются разные пары соседей
    seen = {}
    junction = set()
    for _, _, _, pts in rings_all:
        n = len(pts)
        for j, p in enumerate(pts):
            a, b = pts[j - 1], pts[(j + 1) % n]
            nb = (a, b) if a <= b else (b, a)
            s = seen.get(p)
            if s is None: seen[p] = nb
            elif s != nb: junction.add(p)
    del seen
    # 2. разрезание колец на дуги и дедупликация
    arc_index = {}
    arcs = []
    def add_arc(seq):
        key = tuple(seq)
        if key in arc_index: return arc_index[key]
        rkey = key[::-1]
        if rkey in arc_index: return ~arc_index[rkey]
        arc_index[key] = len(arcs); arcs.append(list(seq))
        return arc_index[key]
    shapes = [defaultdict(lambda: defaultdict(list)) for _ in geoms]
    for gi, pi, ri, pts in rings_all:
        n = len(pts)
        js = [j for j, p in enumerate(pts) if p in junction]
        if not js:
            # кольцо без узлов: канонический старт (минимальная точка) и ориентация
            k = min(range(n), key=lambda j: pts[j])
            rot = pts[k:] + pts[:k]
            fwd = rot + [rot[0]]
            rev = [rot[0]] + rot[:0:-1] + [rot[0]]
            if tuple(rev) in arc_index and tuple(fwd) not in arc_index:
                idx = ~arc_index[tuple(rev)]
            else:
                idx = add_arc(fwd)
            shapes[gi][pi][ri] = [idx]
            continue
        rot = pts[js[0]:] + pts[:js[0]]
        jset = set(j - js[0] if j >= js[0] else j - js[0] + n for j in js)
        ring_arcs, cur = [], [rot[0]]
        for j in range(1, n + 1):
            p = rot[j % n]
            cur.append(p)
            if (j % n) in jset:
                ring_arcs.append(add_arc(cur)); cur = [p]
        shapes[gi][pi][ri] = ring_arcs
    out = []
    for gi in range(len(geoms)):
        polys = []
        for pi in sorted(shapes[gi]):
            polys.append([shapes[gi][pi][ri] for ri in sorted(shapes[gi][pi])])
        out.append(polys)
    return arcs, out

# ----------------------------------------------------------------------------- simplification
def visvalingam(arc, min_area):
    """Упрощение дуги с фиксированными концами. Площадь треугольника — в градусах² с поправкой cos(широты)."""
    n = len(arc)
    if n <= 2: return arc
    pts = [((x / Q - 180.0), (y / Q - 90.0)) for x, y in arc]
    def area(i, j, k):
        (x1, y1), (x2, y2), (x3, y3) = pts[i], pts[j], pts[k]
        c = math.cos(math.radians(y2))
        return abs((x1 - x3) * c * (y2 - y3) - (x2 - x3) * c * (y1 - y3)) / 2
    prev = list(range(-1, n - 1)); nxt = list(range(1, n + 1)); alive = [True] * n
    heap = [(area(i - 1, i, i + 1), i) for i in range(1, n - 1)]
    heapq.heapify(heap)
    cur_area = {i: a for a, i in heap}
    last = 0.0
    while heap:
        a, i = heapq.heappop(heap)
        if not alive[i] or cur_area.get(i) != a: continue
        if a >= min_area: break
        a = max(a, last); last = a
        alive[i] = False
        p, q = prev[i], nxt[i]
        nxt[p] = q; prev[q] = p
        for j in (p, q):
            if 0 < j < n - 1 and alive[j]:
                na = max(area(prev[j], j, nxt[j]), last)
                cur_area[j] = na; heapq.heappush(heap, (na, j))
    res = [arc[i] for i in range(n) if alive[i]]
    # замкнутая дуга-кольцо не должна схлопываться
    if arc[0] == arc[-1] and len(res) < 4:
        step = max(1, (n - 1) // 3)
        res = [arc[0], arc[step], arc[min(2 * step, n - 2)], arc[-1]]
    return res

# ----------------------------------------------------------------------------- topojson writer
def write_topojson(path, objects, arcs, quant):
    """objects: {name: [(geom_type, polys_or_point, props, id)]}. Дуги переквантовываются и кодируются дельтами."""
    used = sorted({a if a >= 0 else ~a for objs in objects.values() for t, g, _, _ in objs if t != "Point"
                   for poly in g for ring in poly for a in ring})
    remap = {old: new for new, old in enumerate(used)}
    kx = 360.0 / (quant - 1); ky = 180.0 / (quant - 1)
    def qq(p):
        x, y = p[0] / Q - 180.0, p[1] / Q - 90.0
        return int(round((x + 180.0) / kx)), int(round((y + 90.0) / ky))
    out_arcs = []
    for old in used:
        prevx = prevy = None; enc = []
        for p in arcs[old]:
            x, y = qq(p)
            if prevx is None: enc.append([x, y])
            elif (x, y) != (prevx, prevy): enc.append([x - prevx, y - prevy])
            else: continue
            prevx, prevy = x, y
        if len(enc) == 1: enc.append([0, 0])
        out_arcs.append(enc)
    def ra(a): return remap[a] if a >= 0 else ~remap[~a]
    topo = {"type": "Topology", "transform": {"scale": [kx, ky], "translate": [-180.0, -90.0]}, "arcs": out_arcs, "objects": {}}
    for name, objs in objects.items():
        geoms = []
        for t, g, props, fid in objs:
            if t == "Point":
                x, y = g
                gg = {"type": "Point", "coordinates": [int(round((x + 180.0) / kx)), int(round((y + 90.0) / ky))]}
            else:
                polys = [[[ra(a) for a in ring] for ring in poly] for poly in g]
                gg = {"type": "MultiPolygon", "arcs": polys} if len(polys) != 1 else {"type": "Polygon", "arcs": polys[0]}
            gg["properties"] = props
            if fid is not None: gg["id"] = fid
            geoms.append(gg)
        topo["objects"][name] = {"type": "GeometryCollection", "geometries": geoms}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(topo, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(path), len(used), sum(len(a) for a in out_arcs)

# ----------------------------------------------------------------------------- CShapes units → стороны
# Коды сторон для единиц CShapes. Ключ: код Gleditsch–Ward. Значение: список (с даты, по дату, код, RU, EN) по порядку.
# Если единица (например, колония) не попадает ни в один интервал — у неё нет кода стороны и роли при наведении не считаются.
GW_ACTORS = {
    2:   [(None, None, "USA", "США", "United States")],
    160: [(None, None, "ARG", "Аргентина", "Argentina")],
    200: [(None, None, "GBR", "Великобритания", "United Kingdom")],
    220: [(None, None, "FRA", "Франция", "France")],
    230: [(None, None, "ESP", "Испания", "Spain")],
    255: [(None, 19450508, "DEU", "Германия", "Germany")],
    260: [(19490521, None, "DEU", "Германия (ФРГ)", "Germany (FRG)")],
    265: [(None, None, "DDR", "ГДР", "German Democratic Republic")],
    290: [(None, None, "POL", "Польша", "Poland")],
    291: [(None, None, "X-DANZIG", "Вольный город Данциг", "Free City of Danzig")],
    352: [(19600816, None, "CYP", "Кипр", "Cyprus")],
    365: [(None, 19171107, "SUN", "Российская империя", "Russian Empire"),
          (19171107, 19221230, "SUN", "Советская Россия", "Soviet Russia"),
          (19221230, 19911221, "SUN", "СССР", "USSR"),
          (19911221, None, "RUS", "Россия", "Russia")],
    369: [(19910824, None, "UKR", "Украина", "Ukraine")],
    371: [(19910921, None, "ARM", "Армения", "Armenia")],
    373: [(19910830, None, "AZE", "Азербайджан", "Azerbaijan")],
    435: [(19601128, None, "MRT", "Мавритания", "Mauritania")],
    600: [(None, None, "MAR", "Марокко", "Morocco")],
    640: [(None, None, "TUR", "Турция", "Türkiye")],
    645: [(None, None, "IRQ", "Ирак", "Iraq")],
    690: [(None, None, "KWT", "Кувейт", "Kuwait")],
    710: [(None, None, "CHN", "Китай", "China")],
    713: [(19491207, None, "TWN", "Тайвань (Китайская Республика)", "Taiwan (Republic of China)")],
    750: [(19470815, None, "IND", "Индия", "India")],
    770: [(19470814, None, "PAK", "Пакистан", "Pakistan")],
    816: [(None, None, "VNM", "Вьетнам", "Viet Nam")],
    817: [(None, None, "VNM", "Республика Вьетнам (Южный)", "Republic of Vietnam (South)")],
    820: [(None, None, "MYS", "Малайзия", "Malaysia")],
    835: [(None, None, "BRN", "Бруней", "Brunei")],
    840: [(None, None, "PHL", "Филиппины", "Philippines")],
    345: [(19181201, 20060603, "YUG", "Югославия", "Yugoslavia"), (20060603, None, "SRB", "Сербия", "Serbia")],
    340: [(20060603, None, "SRB", "Сербия", "Serbia")],
    347: [(20080217, None, "XKX", "Косово", "Kosovo")],
    372: [(19910409, None, "GEO", "Грузия", "Georgia")],
    359: [(19910827, None, "MDA", "Молдова", "Moldova")],
    740: [(None, None, "JPN", "Япония", "Japan")],
    666: [(None, None, "ISR", "Израиль", "Israel")],
    652: [(19460101, None, "SYR", "Сирия", "Syria")],
    663: [(19460525, None, "JOR", "Иордания", "Jordan")],
    651: [(19220228, None, "EGY", "Египет", "Egypt")],
    # партия 3
    305: [(19181103, None, "AUT", "Австрия", "Austria")],
    325: [(None, None, "ITA", "Италия", "Italy")],
    368: [(None, None, "LTU", "Литва", "Lithuania")],
    315: [(None, 19930101, "CSK", "Чехословакия", "Czechoslovakia")],
    205: [(None, None, "IRL", "Ирландия", "Ireland")],
    344: [(19920427, None, "HRV", "Хорватия", "Croatia")],
    346: [(19920427, None, "BIH", "Босния и Герцеговина", "Bosnia and Herzegovina")],
    341: [(20060603, None, "MNE", "Черногория", "Montenegro")],
    350: [(None, None, "GRC", "Греция", "Greece")],
    366: [(None, None, "EST", "Эстония", "Estonia")],
    367: [(None, None, "LVA", "Латвия", "Latvia")],
}

# Русские названия исторических единиц CShapes, которых нет в Natural Earth (редакционный перевод, требует проверки)
NAME_RU = {
    "Aden": "Аден", "Alaska": "Аляска", "Austria-Hungary": "Австро-Венгрия", "Bokhara": "Бухарский эмират", "Bosnia": "Босния",
    "Bosnia-Herzegovina": "Босния и Герцеговина", "British Cameroons": "Британский Камерун", "British Somaliland (Somaliland Republic)": "Британское Сомали",
    "British Togoland": "Британское Того", "Cape Colony": "Капская колония", "Congo, Democratic Republic of (Zaire)": "ДР Конго (Заир)",
    "Cote D'Ivoire": "Кот-д'Ивуар", "Czechoslovakia": "Чехословакия", "East Aden Protectorate": "Протекторат Восточный Аден",
    "Federated Malay States": "Федерированные малайские государства", "Federation of Rhodesia and Nyasaland": "Федерация Родезии и Ньясаленда",
    "Federation of South Arabia": "Федерация Южной Аравии", "French Guyana": "Французская Гвиана", "French West Africa": "Французская Западная Африка",
    "Gaza": "Газа", "German Federal Republic": "ФРГ", "German Togoland": "Германское Того", "Guadeloupe": "Гваделупа", "Hawaii": "Гавайи",
    "Herzegovina": "Герцеговина", "Inini": "Инини", "Italian Somaliland": "Итальянское Сомали", "Italy/Sardinia": "Италия",
    "Jammu and Kashmir": "Джамму и Кашмир", "Kamerun": "Германский Камерун", "Khiva": "Хивинское ханство", "Korea": "Корея",
    "Korea, People's Republic of": "КНДР", "Korea, Republic of": "Республика Корея", "Lagos": "Лагос",
    "Macedonia (FYROM/North Macedonia)": "Северная Македония", "Martinique": "Мартиника", "Natal": "Наталь",
    "New Caledonia and Dependencies": "Новая Каледония", "New Guinea (German New Guinea) (Kaiser Wilhelmsland)": "Германская Новая Гвинея",
    "New South Wales": "Новый Южный Уэльс", "Newfoundland": "Ньюфаундленд", "Northeastern Rhodesia": "Северо-Восточная Родезия",
    "Northern Nigeria": "Северная Нигерия", "Northwestern Rhodesia": "Северо-Западная Родезия", "Orange Free State": "Оранжевое Свободное государство",
    "Papua": "Папуа", "Queensland": "Квинсленд", "Reunion": "Реюньон", "Rumania": "Румыния", "Rwanda-Urundi": "Руанда-Урунди",
    "Sabah (North Borneo)": "Северное Борнео (Сабах)", "Sarawak": "Саравак", "South Australia": "Южная Австралия",
    "Southern Nigeria": "Южная Нигерия", "Southern Sakhalin Island": "Южный Сахалин", "Southern zone of Spanish Morocco": "Южная зона Испанского Марокко",
    "Spanish Morocco": "Испанское Марокко", "Spanish Sahara": "Испанская Сахара", "Spanish West Africa": "Испанская Западная Африка",
    "Straits Settlements": "Стрейтс-Сетлментс", "Surinam": "Суринам", "Swaziland (Eswatini)": "Эсватини", "Tasmania": "Тасмания", "Tibet": "Тибет",
    "Transvaal": "Трансвааль", "Unfederated Malay States": "Нефедерированные малайские государства", "Victoria": "Виктория", "West Bank": "Западный берег",
    "West Irian (Dutch New Guinea)": "Нидерландская Новая Гвинея", "Western Australia": "Западная Австралия", "Yemen, People's Republic of": "НДР Йемен",
    "Zanzibar": "Занзибар",
}

def ymd(p, pre):
    return p[pre + "year"] * 10000 + p[pre + "month"] * 100 + p[pre + "day"]

def unit_actor(gw, s, e):
    """Код стороны для единицы CShapes, действующей с s по e (yyyymmdd)."""
    for f, t, code, ru, en in GW_ACTORS.get(gw, []):
        if (f is None or s >= f) and (t is None or s < t):
            return code, ru, en
    return None, None, None

def arcs_to_geom(arcs, polys):
    """Геометрия единицы из (упрощённых) дуг топологии — для расчёта точек подписей."""
    def ring(ids):
        pts = []
        for a in ids:
            seq = arcs[a] if a >= 0 else arcs[~a][::-1]
            seq = [((x / Q - 180.0), (y / Q - 90.0)) for x, y in seq]
            pts.extend(seq if not pts else seq[1:])
        return pts
    return {"type": "MultiPolygon", "coordinates": [[ring(r) for r in poly] for poly in polys]}

def label_rank(km2):
    """Ранг подписи: 1 — крупнейшие государства … 6 — мелкие (видны только при приближении)."""
    for k, lim in enumerate((2_500_000, 600_000, 150_000, 30_000, 5_000), start=1):
        if km2 >= lim: return k
    return 6

def short_name(name):
    return name.split(" (")[0].strip()

def color_index(units_meta, shapes):
    """Номер цвета (0–6) для «политической» темы: соседние в одно время государства получают разные цвета.
    Цвет привязан к коду GW, чтобы страна не меняла цвет при движении по шкале времени."""
    arc_users = defaultdict(list)
    for k, (i, gw, s, e) in enumerate(units_meta):
        for poly in shapes[i]:
            for ring in poly:
                for a in ring:
                    arc_users[a if a >= 0 else ~a].append(k)
    adj = defaultdict(set)
    for users in arc_users.values():
        if len(users) < 2: continue
        for x in users:
            for y in users:
                if x >= y: continue
                _, gx, sx, ex = units_meta[x]; _, gy, sy, ey = units_meta[y]
                if gx != gy and sx <= ey and sy <= ex:
                    adj[gx].add(gy); adj[gy].add(gx)
    gws = sorted({m[1] for m in units_meta})
    color = {}
    # DSATUR: сначала вершины с наибольшим числом уже окрашенных соседей разных цветов
    while len(color) < len(gws):
        best = max((g for g in gws if g not in color),
                   key=lambda g: (len({color[n] for n in adj[g] if n in color}), len(adj[g]), -g))
        used = {color[n] for n in adj[best] if n in color}
        c = next(c for c in range(20) if c not in used)
        color[best] = c
    return color, max(color.values()) + 1

def pick_cshapes(cs_by_gw, key):
    """cshapes:<gw>@last | @first | @<yyyymmdd> — единица, действующая на дату."""
    gw, which = key.split("@")
    fs = sorted(cs_by_gw[int(gw)], key=lambda f: ymd(f["properties"], "gws"))
    if which == "last": return fs[-1]["geometry"]
    if which == "first": return fs[0]["geometry"]
    d = int(which)
    for f in fs:
        if ymd(f["properties"], "gws") <= d <= ymd(f["properties"], "gwe"): return f["geometry"]
    raise KeyError(f"нет единицы CShapes {key}")

# ----------------------------------------------------------------------------- main
def _point_in(x, y, geom):
    """Точка внутри (Multi)Polygon — правило чётности по всем кольцам."""
    for poly in polygons(geom):
        inside = False
        for ring in poly:
            j = len(ring) - 1
            for k in range(len(ring)):
                xi, yi = ring[k][0], ring[k][1]; xj, yj = ring[j][0], ring[j][1]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
                j = k
        if inside:
            return True
    return False

def _bbox(geom):
    xs = [pt[0] for p in polygons(geom) for pt in p[0]]; ys = [pt[1] for p in polygons(geom) for pt in p[0]]
    return min(xs), min(ys), max(xs), max(ys)

def _day(d, delta):
    t = datetime.date(d // 10000, d // 100 % 100, d % 100) + datetime.timedelta(days=delta)
    return t.year * 10000 + t.month * 100 + t.day

def uncovered_land(ne50, cs, say):
    """Для каждой страны Natural Earth 50m — периоды, когда её внутренняя точка не покрыта ни одной единицей CShapes.
    Такие территории на карте не закрашены; по ним сайт показывает справку (название и современный статус по Natural Earth)."""
    iv = []
    for f in cs:
        p = f["properties"]; s, e = ymd(p, "gws"), ymd(p, "gwe")
        if e >= DATASET_END: e = OPEN_END
        if e < 19000101: continue
        iv.append((_bbox(f["geometry"]), f["geometry"], max(s, 19000101), e))
    admin_ru = {f["properties"]["ADMIN"]: f["properties"].get("NAME_RU") for f in ne50}
    out, n_gap = [], 0
    for k, f in enumerate(ne50):
        p = f["properties"]
        pt = polylabel(f["geometry"], precision_deg=0.02)
        props = {"k": k}
        if pt:
            x, y = pt
            cov = sorted((s, e) for b, g, s, e in iv if b[0] <= x <= b[2] and b[1] <= y <= b[3] and _point_in(x, y, g))
            gaps, cur = [], 19000101
            for s, e in cov:
                if s > cur: gaps.append((cur, _day(s, -1)))
                if e >= OPEN_END: cur = None; break
                cur = max(cur, _day(e, 1))
            if cur is not None and cur <= OPEN_END: gaps.append((cur, OPEN_END))
            gaps = [g for g in gaps if g[1] - g[0] >= 100]   # короче месяца — стыки срезов, не пропуски
            if gaps:
                n_gap += 1
                sov = p.get("SOVEREIGNT") or ""
                props.update({"n": p.get("NAME"), "r": p.get("NAME_RU") or p.get("NAME"), "t": p.get("TYPE") or "",
                              "sv": sov if sov != p.get("ADMIN") else "", "svr": (admin_ru.get(sov) or sov) if sov != p.get("ADMIN") else "",
                              "u": ",".join(f"{s0}-{e0}" for s0, e0 in gaps)})
        out.append(props)
    say("Суша без единицы CShapes хотя бы в один период: стран Natural Earth", n_gap)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw"); ap.add_argument("--out", default="site/data")
    ap.add_argument("--disputes", default="data/disputes.json"); ap.add_argument("--sources", default="scripts/geometry_sources.json")
    ap.add_argument("--min-area", type=float, default=2.5e-4, help="порог Висвалингама, градусы² (≈ 3 км²)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    log = []
    def say(*x):
        s = " ".join(str(v) for v in x); print(s); log.append(s)

    # --- CShapes
    cs = load(os.path.join(a.raw, "CShapes-2.0.geojson"))["features"]
    say("CShapes: единиц", len(cs))
    geoms = [f["geometry"] for f in cs]
    arcs, shapes = build_topology(geoms)
    npts = sum(len(x) for x in arcs)
    say("CShapes: дуг", len(arcs), "точек в дугах", npts)
    arcs = [visvalingam(x, a.min_area) for x in arcs]
    say("CShapes: после упрощения точек", sum(len(x) for x in arcs))

    # названия для единиц без кода стороны: Natural Earth NAME_RU по совпадению английского названия
    ne10 = load(os.path.join(a.raw, "ne_10m_admin_0_countries.geojson"))["features"]
    ne_by_name = {}
    for f in ne10:
        p = f["properties"]
        for k in ("NAME", "NAME_LONG", "ADMIN", "NAME_EN", "FORMAL_EN", "SOVEREIGNT"):
            v = p.get(k)
            if v: ne_by_name.setdefault(v.lower(), p)

    units, objs_by_era = [], {e: [] for e in ERAS}
    labels_by_era = {e: [] for e in ERAS}
    unmatched = set()
    kept = []
    for i, f in enumerate(cs):
        p = f["properties"]
        s, e = ymd(p, "gws"), ymd(p, "gwe")
        if e >= DATASET_END: e = OPEN_END
        if e >= 19000101: kept.append((i, p["gwcode"], s, e))
    colors, ncolors = color_index(kept, shapes)
    say("Политическая раскраска: цветов", ncolors)
    for i, f in enumerate(cs):
        p = f["properties"]
        s, e = ymd(p, "gws"), ymd(p, "gwe")
        if e >= DATASET_END: e = OPEN_END            # продление до наших дней (см. ARCHITECTURE.md §5)
        if e < 19000101: continue
        code, ru, en = unit_actor(p["gwcode"], s, e)
        name_en = p["cntry_name"]
        if not ru:
            base = name_en.split(" (")[0].lower()
            m = ne_by_name.get(name_en.lower()) or ne_by_name.get(base)
            ru = NAME_RU.get(name_en) or (m or {}).get("NAME_RU")
            if not ru:
                ru = name_en; unmatched.add(name_en)
        iso = None
        if code and len(code) == 3 and code.isalpha() and code not in ("SUN", "YUG", "DDR"):
            iso = code
        elif e == OPEN_END:
            m = ne_by_name.get(name_en.lower()) or ne_by_name.get(name_en.split(" (")[0].lower())
            if m:
                iso = m.get("ISO_A3") if m.get("ISO_A3") not in (None, "-99") else m.get("ADM0_A3")
        props = {"i": i, "g": p["gwcode"], "s": s, "e": e, "a": code or "", "n": en or name_en, "r": ru,
                 "c": colors.get(p["gwcode"], 0)}
        if iso: props["iso"] = iso
        units.append({"i": i, "gw": p["gwcode"], "cshapes_name": name_en, "start": s, "end": e, "actor": code, "iso": iso,
                      "name_ru": ru, "name_en": en or name_en})
        km2 = p.get("area") or 0
        lp = polylabel(arcs_to_geom(arcs, shapes[i]), precision_deg=0.05)
        lprops = {"i": i, "s": s, "e": e, "n": short_name(en or name_en), "r": short_name(ru), "k": label_rank(km2)}
        for (y0, y1) in ERAS:
            if s <= y1 * 10000 + 1231 and e >= y0 * 10000 + 101:
                objs_by_era[(y0, y1)].append(("Polygon", shapes[i], props, i))
                if lp: labels_by_era[(y0, y1)].append(("Point", lp, lprops, None))
    say("Единиц без русского названия из Natural Earth:", len(unmatched))

    meta_eras = []
    for (y0, y1), objs in objs_by_era.items():
        fn = f"countries.{y0}-{y1}.topo.json"
        size, na, np_ = write_topojson(os.path.join(a.out, fn), {"countries": objs, "labels": labels_by_era[(y0, y1)]}, arcs, 200_000)
        say(f"{fn}: единиц {len(objs)}, дуг {na}, точек {np_}, {size/1e6:.2f} МБ")
        meta_eras.append({"from": y0, "to": y1, "file": fn})

    # --- суша (Natural Earth 50m) — нейтральная подложка и справка для территорий без единицы CShapes
    ne50 = load(os.path.join(a.raw, "ne_50m_admin_0_countries.geojson"))["features"]
    larcs, lshapes = build_topology([f["geometry"] for f in ne50])
    larcs = [visvalingam(x, a.min_area) for x in larcs]
    land_props = uncovered_land(ne50, cs, say)
    lobjs = [("Polygon", lshapes[i], land_props[i], None) for i in range(len(ne50))]
    size, na, np_ = write_topojson(os.path.join(a.out, "land.topo.json"), {"land": lobjs}, larcs, 100_000)
    say(f"land.topo.json: {size/1e6:.2f} МБ, точек {np_}")

    # --- зоны споров
    src = load(a.sources)
    disp = {d["id"]: d for d in load(a.disputes)["disputes"]}
    nedisp = {f["properties"]["BRK_A3"]: f for f in load(os.path.join(a.raw, "ne_10m_admin_0_disputed_areas.geojson"))["features"]}
    adm1 = {}
    for f in load(os.path.join(a.raw, "ne_10m_admin_1_states_provinces.geojson"))["features"]:
        adm1.setdefault(f["properties"]["iso_3166_2"], []).append(f)
    cs_by_gw = defaultdict(list)
    for f in cs: cs_by_gw[f["properties"]["gwcode"]].append(f)
    ne10_by_iso = defaultdict(list)
    for f in ne10:
        ne10_by_iso[f["properties"].get("ADM0_A3")].append(f)
    def ne0_part(iso, lon, lat):
        """Отдельный полигон страны Natural Earth 10m, ближайший к точке (например, остров)."""
        best, bd = None, 1e9
        for f in ne10_by_iso[iso]:
            for poly in polygons(f["geometry"]):
                xs = [p[0] for p in poly[0]]; ys = [p[1] for p in poly[0]]
                cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
                d = (cx - lon) ** 2 + (cy - lat) ** 2
                if d < bd: bd, best = d, poly
        if bd > 0.05: say("!! далеко от точки", iso, lon, lat, round(bd, 4))
        return {"type": "Polygon", "coordinates": best}

    dgeoms, dprops, markers, gmeta = [], [], [], {}
    for area_id, spec in src["areas"].items():
        did = area_id.split("--")[0]
        if did not in disp:
            say("!! нет спора", did, "для", area_id); continue
        def resolve(ref):
            if isinstance(ref, dict):
                g = overlay([x for r in ref["a"] for x in resolve(r)], [x for r in ref.get("b", []) for x in resolve(r)], ref["op"])
                if g is None: say("!! пустой результат операции для", area_id)
                return [g] if g else []
            kind, key = ref.split(":", 1)
            if kind == "ne":
                return [nedisp[key]["geometry"]]
            if kind == "adm1":
                if key not in adm1: say("!! нет adm1", key); return []
                return [f["geometry"] for f in adm1[key]]
            if kind == "adm1unit":          # все районы с данным geonunit, например «Northern Ireland»
                return [f["geometry"] for fs in adm1.values() for f in fs if f["properties"].get("geonunit") == key]
            if kind == "ne0":               # полигоны страны NE 10m около точки «ISO@lon,lat»
                iso, ll = key.split("@"); lon, lat = map(float, ll.split(","))
                return [ne0_part(iso, lon, lat)]
            if kind == "cshapes":
                return [pick_cshapes(cs_by_gw, key)]
            if kind == "bbox":              # прямоугольник «запад,юг,восток,север» — только для отсечения в операциях
                x0, y0, x1, y1 = map(float, key.split(","))
                return [{"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}]
            raise ValueError(ref)
        parts = []
        for ref in spec["parts"]:
            parts += resolve(ref)
        if len(parts) > 1:   # слить части в одну фигуру без внутренних линий
            u = overlay(parts, [], "union")
            if u: parts = [u]
        area_total = 0
        for g in parts:
            dgeoms.append(g); dprops.append({"area_id": area_id, "dispute_id": did, "ol": 1 if len(parts) == 1 else 0})
            area_total += geom_area_km2(g)
        gmeta[area_id] = {"source": spec["source"], "quality": spec["quality"], "note": spec.get("note"), "km2": round(area_total)}
        if area_total < 400:   # мелкие острова и зоны — маркер, чтобы были видны на мелком масштабе
            markers.append(("Point", label_point(max(parts, key=geom_area_km2)), {"area_id": area_id, "dispute_id": did}, None))
    darcs, dshapes = build_topology(dgeoms)
    darcs = [visvalingam(x, a.min_area / 25) for x in darcs]
    dobjs = [("Polygon", dshapes[i], dprops[i], None) for i in range(len(dgeoms))]
    size, na, np_ = write_topojson(os.path.join(a.out, "disputes.topo.json"), {"areas": dobjs, "markers": markers}, darcs, 2_000_000)
    say(f"disputes.topo.json: частей {len(dobjs)}, маркеров {len(markers)}, {size/1e6:.2f} МБ")

    with open(os.path.join(a.out, "units.json"), "w", encoding="utf-8") as f:
        json.dump(units, f, ensure_ascii=False, separators=(",", ":"))
    meta = {"built": datetime.date.today().isoformat(), "eras": meta_eras, "dataset_end": DATASET_END,
            "geometry": gmeta, "sources": {
                "CShapes 2.0": "ETH Zürich, CC BY-NC 4.0 (Schvitz et al. 2022)",
                "Natural Earth 5.1": "public domain"},
            "simplify_min_area_deg2": a.min_area}
    with open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "build_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n\nЕдиницы без названия в Natural Earth (оставлено английское):\n" + "\n".join(sorted(unmatched)))

if __name__ == "__main__":
    main()
