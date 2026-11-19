# -*- coding: utf-8 -*-
"""Транспортные коридоры (слой «Транспортные маршруты») → data/routes.json.
Запуск: python scripts/data/routes_data.py data/routes.json

Правила:
  * Даты: «появление» (appear) — учредительный документ или объявление (на карте пунктир);
    «действует» (operate) — первая реальная перевозка по маршруту (на карте сплошная линия).
  * Линии — схема через узлы, названные в источниках (порты, станции, пограничные пункты).
    Координаты узлов приблизительные (точность около 10 км) и проверяются скриптом build_routes.py
    по полигонам стран Natural Earth; морские участки проверяются на пересечение с сушей.
  * Цифры загрузки — с указанием, кто и как считает (определения у источников различаются).
Источники открыты и прочитаны 19 ноября 2026 г. (verified_fulltext=True — прочитан текст или его релевантный фрагмент).
"""
import json, os, sys
from collections import OrderedDict as OD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import make_S, T, E  # noqa: E402

ACC = "2026-11-19"
S = make_S(ACC)

# ----------------------------------------------------------------------------- узлы: id → (ru, en, долгота, широта, ISO страны или None для моря)
NODES = {
    # Северный морской путь (акватория по ст. 5.1 КТМ РФ: от меридиана мыса Желания и проливов Новой Земли до мыса Дежнёва)
    "karavorota": ("пролив Карские Ворота", "Kara Gates", 57.95, 70.42, None),
    "dikson": ("Диксон", "Dikson", 80.55, 73.51, "RUS"),
    "vilkitsky": ("пролив Вилькицкого", "Vilkitsky Strait", 104.5, 77.9, None),
    "tiksi": ("Тикси", "Tiksi", 128.87, 71.64, "RUS"),
    "sannikov": ("пролив Санникова", "Sannikov Strait", 139.5, 74.6, None),
    "pevek": ("Певек", "Pevek", 170.31, 69.70, "RUS"),
    "longstrait": ("пролив Лонга", "Long Strait", 178.5, 70.3, None),
    "dezhnev": ("мыс Дежнёва", "Cape Dezhnev", -169.65, 66.08, "RUS"),
    # Чёрное море и Кавказ
    "chornomorsk": ("Черноморск (Ильичёвск)", "Chornomorsk (Illichivsk)", 30.65, 46.30, "UKR"),
    "constanta": ("Констанца", "Constanța", 28.65, 44.17, "ROU"),
    "varna": ("Варна", "Varna", 27.92, 43.21, "BGR"),
    "burgas": ("Бургас", "Burgas", 27.47, 42.50, "BGR"),
    "batumi": ("Батуми", "Batumi", 41.64, 41.64, "GEO"),
    "poti": ("Поти", "Poti", 41.67, 42.15, "GEO"),
    "tbilisi": ("Тбилиси", "Tbilisi", 44.79, 41.72, "GEO"),
    "kars": ("Карс", "Kars", 43.10, 40.60, "TUR"),
    "istanbul": ("Стамбул", "Istanbul", 28.98, 41.01, "TUR"),
    "baku": ("Баку", "Baku", 49.87, 40.41, "AZE"),
    "alyat": ("Алят", "Alyat", 49.41, 39.95, "AZE"),
    "shirvan": ("Ширван", "Shirvan", 48.92, 39.93, "AZE"),
    "astara": ("Астара", "Astara", 48.87, 38.45, "AZE"),
    # Каспий и Центральная Азия
    "turkmenbashi": ("Туркменбаши", "Turkmenbashi", 52.97, 40.02, "TKM"),
    "aktau": ("Актау", "Aktau", 51.17, 43.65, "KAZ"),
    "kuryk": ("Курык", "Kuryk", 51.65, 43.17, "KAZ"),
    "ashgabat": ("Ашхабад", "Ashgabat", 58.38, 37.95, "TKM"),
    "tashkent": ("Ташкент", "Tashkent", 69.24, 41.30, "UZB"),
    "dostyk": ("Достык", "Dostyk", 82.48, 45.25, "KAZ"),
    "makat": ("Макат", "Makat", 53.32, 47.65, "KAZ"),
    "beyneu": ("Бейнеу", "Beyneu", 55.20, 45.32, "KAZ"),
    "bolashak": ("Болашак", "Bolashak", 54.05, 42.58, "KAZ"),
    "bereket": ("Берекет", "Bereket", 55.52, 39.24, "TKM"),
    # Россия и Иран
    "saratov": ("Саратов", "Saratov", 46.03, 51.53, "RUS"),
    "astrakhan": ("Астрахань", "Astrakhan", 48.04, 46.35, "RUS"),
    "olya": ("Оля", "Olya", 47.55, 45.78, "RUS"),
    "makhachkala": ("Махачкала", "Makhachkala", 47.50, 42.98, "RUS"),
    "derbent": ("Дербент", "Derbent", 48.29, 42.06, "RUS"),
    "samur": ("Самур (граница России и Азербайджана)", "Samur (Russia–Azerbaijan border)", 48.47, 41.86, "AZE"),
    "rasht": ("Решт", "Rasht", 49.58, 37.28, "IRN"),
    "anzali": ("Энзели", "Anzali", 49.46, 37.47, "IRN"),
    "qazvin": ("Казвин", "Qazvin", 50.00, 36.27, "IRN"),
    "tehran": ("Тегеран", "Tehran", 51.39, 35.69, "IRN"),
    "inchehborun": ("Инче-Бурун", "Incheh Borun", 54.72, 37.45, "IRN"),
    "garmsar": ("Гермсар", "Garmsar", 52.34, 35.22, "IRN"),
    "bafq": ("Бафк", "Bafq", 55.40, 31.60, "IRN"),
    "bandarabbas": ("Бендер-Аббас", "Bandar Abbas", 56.27, 27.18, "IRN"),
    # Индия, Залив, Средиземноморье
    "nhavasheva": ("Нава-Шева (Мумбаи)", "Nhava Sheva (Mumbai)", 72.95, 18.95, "IND"),
    "mundra": ("Мундра", "Mundra", 69.72, 22.84, "IND"),
    "kandla": ("Кандла", "Kandla", 70.22, 23.03, "IND"),
    "jebelali": ("Джебель-Али", "Jebel Ali", 55.06, 25.01, "ARE"),
    "fujairah": ("Эль-Фуджайра", "Fujairah", 56.33, 25.12, "ARE"),
    "ghuwaifat": ("Эль-Гувайфат", "Al-Ghuwaifat", 51.62, 24.12, "ARE"),
    "haradh": ("Харад", "Haradh", 49.07, 24.15, "SAU"),
    "hadithah": ("Эль-Хадиса", "Al-Hadithah", 37.14, 31.46, "SAU"),
    "mafraq": ("Мафрак", "Mafraq", 36.21, 32.34, "JOR"),
    "beitshean": ("Бейт-Шеан", "Beit She'an", 35.50, 32.50, "ISR"),
    "haifa": ("Хайфа", "Haifa", 34.99, 32.82, "ISR"),
    "piraeus": ("Пирей", "Piraeus", 23.65, 37.94, "GRC"),
    "trieste": ("Триест", "Trieste", 13.78, 45.65, "ITA"),
    "marseille": ("Марсель", "Marseille", 5.37, 43.30, "FRA"),
    # Сюник и Нахичевань (TRIPP)
    "aze_border_e": ("граница Армении и Азербайджана (восток)", "Armenia–Azerbaijan border (east)", 46.53, 38.86, "ARM"),
    "meghri": ("Мегри", "Meghri", 46.24, 38.90, "ARM"),
    "nakh_border_w": ("граница Армении и Нахичевани (запад)", "Armenia–Nakhchivan border (west)", 46.10, 38.92, "ARM"),
    "julfa": ("Джульфа", "Julfa", 45.63, 38.96, "AZE"),
    "nakhchivan": ("Нахичевань", "Nakhchivan", 45.41, 39.21, "AZE"),
}
# Морские путевые точки без подписи (обход мысов и островов на схеме)
WAYPOINTS = {
    "w_yamal": (70.0, 74.0), "w_kara": (86.0, 76.0), "w_taymyr": (97.0, 77.6), "w_laptev": (118.0, 76.2), "w_lena": (128.0, 75.2),
    "w_tiksi": (131.0, 72.6), "w_eastsib": (156.0, 72.6), "w_ayon": (171.0, 70.3),
    "w_odesa": (30.9, 45.8), "w_danube": (29.9, 44.9), "w_baku_s": (49.95, 40.25), "w_sinop": (35.1, 42.4),
    "w_kutch": (68.6, 22.5), "w_musandam": (56.2, 26.6), "w_gulf": (55.6, 25.9), "w_istria": (13.3, 45.4),
    "w_absheron_n": (50.5, 41.0), "w_absheron_e": (50.6, 40.3), "w_casp_s": (50.0, 38.6),
    "w_oman": (58.5, 24.6), "w_arab": (62.5, 22.8), "w_hormuz": (56.6, 26.5),
    "w_rhodes": (28.6, 35.5), "w_crete_s": (24.0, 34.6), "w_cyclades": (24.6, 36.9),
    "w_ionian": (19.5, 37.6), "w_otranto": (19.0, 40.3), "w_adriatic": (16.3, 42.6), "w_adriatic_n": (13.2, 44.7),
    "w_sicily": (12.0, 37.0), "w_sardinia": (8.6, 38.6), "w_lion": (6.0, 42.4),
}


def SEG(nodes, mode="land", appear=None, operate=None, planned=False, note=None):
    """Участок ветки. appear/operate по умолчанию — как у маршрута; planned=True — участок не построен (всегда пунктир)."""
    return OD(nodes=list(nodes), mode=mode, appear=appear, operate=operate, planned=planned, note=note)


def BR(bid, ru, en, segments, note=None):
    return OD(id=bid, name=T(ru, en), segments=list(segments), note=note)


def CAP(ru, en, src, kind="estimate"):
    """kind: design (проектная мощность), current (текущая пропускная способность), target (плановый показатель), estimate (оценка)."""
    return OD(kind=kind, text=T(ru, en), source_ids=list(src))


def SERIES(sid, ru, en, unit_ru, unit_en, points, note=None):
    """points: [(год, значение, [источники])]."""
    return OD(id=sid, label=T(ru, en), unit=T(unit_ru, unit_en),
              points=[OD(year=y, value=v, source_ids=list(s)) for y, v, s in points], note=note)


def ROUTE(**k):
    base = OD(id=None, name=None, alt_names=[], kind=None, color=None, parties=[], appear=None, operate=None,
              summary=None, status=None, branches=[], capacity=[], volumes=[], history=[], sources=[],
              confidence=None, needs_human_review=True, review=None, analysis=None)
    base.update(k)
    base["history"] = sorted(base["history"], key=lambda e: e["date"])
    return base


def REVIEW(conflicts=(), notes=()):
    return OD(status="draft", last_checked=ACC, conflicts=list(conflicts), notes=list(notes))


R = []

# ============================================================================= СЕВЕРНЫЙ МОРСКОЙ ПУТЬ
src = [
    S("rulaws-132fz", "Федеральный закон от 28.07.2012 № 132-ФЗ (ст. 5.1 Кодекса торгового мореплавания: акватория Северного морского пути)",
      "Российская Федерация (текст на rulaws.ru)", 2012, "официальный документ стороны", "https://rulaws.ru/laws/Federalnyy-zakon-ot-28.07.2012-N-132-FZ/",
      "RUS", ["route", "history"], True, page="ст. 3, п. 3 (ст. 5.1 КТМ)"),
    S("solski-2013", "New Developments in Russian Regulation of Navigation on the Northern Sea Route", "Jan Jakub Solski (Arctic Review on Law and Politics)", 2013,
      "академическая работа", "https://arcticreview.no/index.php/arctic/article/view/41", "neutral", ["history"], True),
    S("arctic-russia-2020", "History of the Northeast Passage: from idea to first success", "Инвестиционный портал Арктической зоны РФ", 2020, "справочное издание",
      "https://arctic-russia.ru/article/history-of-the-northeast-passage-from-idea-to-first-success-/", "neutral", ["appear", "operate", "history"], True,
      note="7 февраля 2020 г."),
    S("barr-1978", "The Voyage of Sibiryakov, 1932", "William Barr (Polar Record, vol. 19, no. 120)", 1978, "академическая работа",
      "https://www.cambridge.org/core/journals/polar-record/article/abs/voyage-of-sibiryakov-1932/D1C9D2625476726FE42F3414B1D4F3E8", "neutral",
      ["appear", "operate", "history"], True, note="Прочитана аннотация: до лета 1932 г. ни одно судно не прошло путь за одну навигацию"),
    S("atommedia-2026", "Northern Sea Route. Background information", "Атом Медиа (цифровая пресс-служба Росатома)", 2026, "официальный документ стороны",
      "https://atommedia.online/en/reference/severnyy-morskoy-put-spravochnaya-informatsiya-/", "RUS", ["route", "volumes"], True, note="30 марта 2026 г."),
    S("gcaptain-2026", "Northern Sea Route Traffic Slips in 2025 as Sanctions Constrain Russia's Arctic Ambitions", "Malte Humpert (gCaptain)", 2026,
      "публикация СМИ", "https://gcaptain.com/northern-sea-route-traffic-slips-in-2025-as-sanctions-constrain-russias-arctic-ambitions/", "neutral",
      ["volumes", "capacity"], True, note="11 февраля 2026 г."),
    S("euromaidan-2026", "37 million tons instead of 80 million—Russia's Arctic shipping dream hits reverse", "Peeter Helme (Euromaidan Press)", 2026,
      "публикация СМИ", "https://euromaidanpress.com/2026/02/10/russia-arctic-shipping-route-decline/", "neutral", ["volumes", "capacity"], True,
      note="10 февраля 2026 г."),
    S("moscowtimes-2025", "Northern Sea Route Shipping Falls Short of Russia's 2024 Target", "The Moscow Times", 2025, "публикация СМИ",
      "https://www.themoscowtimes.com/2025/01/10/northern-sea-route-shipping-falls-short-of-russias-2024-target-a87558", "neutral",
      ["volumes", "capacity"], True, note="10 января 2025 г.; цифры Росатома"),
    S("wnn-2025", "Northern Sea Route cargo set new record in 2024", "World Nuclear News", 2025, "публикация СМИ",
      "https://wnn.world-nuclear.org/articles/northern-sea-route-cargo-set-new-record-in-2024", "neutral", ["volumes"], True, note="10 января 2025 г.; цифры Росатома"),
    S("erai-2025-nsr", "The Northern Sea Route as a key Russian transport corridor", "ERAI (index1520.com)", 2025, "справочное издание",
      "https://index1520.com/en/analytics/severnyy-morskoy-put-kak-klyuchevoy-transportnyy-koridor-rossii-strategicheskoe-znachenie-i-perspekt/",
      "neutral", ["volumes"], True, note="31 марта 2025 г."),
    S("interfax-2024-nsr", "Cargo traffic on Russia's Northern Sea Route topped 36 mln tonnes in 2023 — Rosatom", "Interfax", 2024, "публикация СМИ",
      "https://interfax.com/newsroom/top-stories/98266/", "neutral", ["volumes"], True, note="10 января 2024 г."),
    S("arcticportal-2024", "In 2023, cargo transportation along the North Sea Route totalled 36.254 mn tons", "Инвестиционный портал Арктической зоны РФ (по данным Росатома)",
      2024, "официальный документ стороны", "https://arctic-russia.ru/en/news/in-2023-cargo-transportation-along-the-north-sea-route-totalled-36-254-mn-tons/",
      "RUS", ["volumes"], True, note="16 января 2024 г."),
    S("chnl-2025", "Main results of NSR transit navigation in 2025", "Centre for High North Logistics (CHNL, Nord University)", 2025, "датасет",
      "https://chnl.no/news/main-results-of-nsr-transit-navigation-in-2025/", "neutral", ["volumes"], True, note="9 декабря 2025 г."),
]
R.append(ROUTE(
    id="nsr", name=T("Северный морской путь (СМП)", "Northern Sea Route (NSR)"), kind="maritime", color="#0b7a75",
    parties=["RUS"], appear="1932", operate="1932",
    summary=T("Морской путь вдоль арктического побережья России — кратчайший между западной частью Евразии и Азиатско-Тихоокеанским регионом. "
              "По закону 2012 г. его акватория простирается от проливов Новой Земли и меридиана мыса Желания до параллели мыса Дежнёва в Беринговом проливе. "
              "Впервые за одну навигацию путь пройден в 1932 г. Основной груз — вывоз сырья из арктических портов; транзит составляет небольшую долю.",
              "A sea route along Russia's Arctic coast, the shortest between western Eurasia and the Asia-Pacific. Under the 2012 law its water area runs "
              "from the Novaya Zemlya straits and the meridian of Cape Zhelaniya to the parallel of Cape Dezhnev in the Bering Strait. "
              "It was first traversed in a single season in 1932. Most cargo is raw materials shipped from Arctic ports; transit is a small share."),
    status=T("Действует; навигация зависит от ледовой обстановки и ледокольного сопровождения.", "Operating; navigation depends on ice conditions and icebreaker escort."),
    branches=[BR("main", "Акватория СМП (схема)", "NSR water area (schematic)", [
        SEG(["karavorota", "w_yamal", "dikson", "w_kara", "w_taymyr", "vilkitsky", "w_laptev", "w_lena", "w_tiksi", "tiksi", "w_tiksi", "sannikov", "w_eastsib", "pevek", "w_ayon", "longstrait", "dezhnev"], mode="sea"),
    ], note=T("Линия проведена через проливы и порты акватории; фактические трассы зависят от ледовой обстановки.",
              "The line runs through the straits and ports of the water area; actual tracks depend on ice conditions."))],
    capacity=[
        CAP("Плановый показатель: 80 млн т в 2024 г. (указ 2018 г.); фактически перевезено менее половины.",
            "Target: 80 million tonnes in 2024 (2018 decree); less than half was actually carried.", ["moscowtimes-2025", "euromaidan-2026"], kind="target"),
        CAP("Прогноз правительства России — до 100 млн т в год к 2030 г.", "Russian government forecast: up to 100 million tonnes a year by 2030.", ["gcaptain-2026"], kind="target"),
        CAP("Стратегия развития Арктической зоны (2020): 130 млн т к 2035 г.", "Arctic Zone strategy (2020): 130 million tonnes by 2035.", ["moscowtimes-2025"], kind="target"),
    ],
    volumes=[
        SERIES("total", "Все перевозки по акватории СМП", "All shipments in the NSR water area", "млн т", "million t", [
            (1987, 6.58, ["euromaidan-2026"]),
            (2022, 34.0, ["interfax-2024-nsr"]),
            (2023, 36.254, ["interfax-2024-nsr", "arcticportal-2024"]),
            (2024, 37.9, ["moscowtimes-2025", "erai-2025-nsr"]),
            (2025, 37.02, ["gcaptain-2026", "atommedia-2026"]),
        ], note=T("Данные Росатома. 1987 г. — советский максимум.", "Rosatom data. 1987 is the Soviet-era peak.")),
        SERIES("transit", "Транзит (между портами вне России)", "Transit (between non-Russian ports)", "млн т", "million t", [
            (2023, 2.129, ["interfax-2024-nsr", "erai-2025-nsr"]),
            (2024, 3.0, ["wnn-2025", "erai-2025-nsr"]),
            (2025, 3.2, ["chnl-2025", "atommedia-2026"]),
        ]),
    ],
    history=[
        E("1932", "event", "Ледокольный пароход «А. Сибиряков» впервые проходит путь за одну навигацию.", "The icebreaking steamer Sibiryakov first completes the route in a single season.", "arctic-russia-2020", "barr-1978"),
        E("1987", "event", "Советский максимум перевозок — 6,58 млн т.", "Soviet-era peak of shipments: 6.58 million tonnes.", "euromaidan-2026"),
        E("2012-07-28", "legal", "Федеральный закон № 132-ФЗ определяет акваторию СМП и правила плавания.", "Federal Law No. 132-FZ defines the NSR water area and navigation rules.", "rulaws-132fz", "solski-2013"),
        E("2024", "event", "Перевезено 37,9 млн т — меньше половины цели в 80 млн т.", "37.9 million tonnes carried — less than half of the 80-million-tonne target.", "moscowtimes-2025", "euromaidan-2026"),
    ],
    sources=src, confidence="medium",
    review=REVIEW(conflicts=["Объём 2024 г.: 37,9 млн т (The Moscow Times, ERAI) или «почти 37,8 млн т» (World Nuclear News); все — по данным Росатома",
                             "2025 г.: Росатом называет 37,02 млн т рекордом, gCaptain и Euromaidan Press — снижением на 2,3% к 2024 г.",
                             "Цель на 2035 г.: 130 млн т (Стратегия 2020 г., по The Moscow Times) или 270 млн т (обещание Росатома, по Euromaidan Press)"],
                  notes=["Объём 2022 г. и советский максимум 1987 г. — по одному источнику",
                         "Создание Главсевморпути в 1932 г. подтверждено только фрагментом обзора CRREL без выходных данных и в карточку не включено",
                         "Линия — схема по проливам и портам; координаты узлов приблизительные"]),
))

# ============================================================================= TRACECA
src = [
    S("traceca-history", "TRACECA History", "Межправительственная комиссия TRACECA (Постоянный секретариат)", None, "официальный документ стороны",
      "https://traceca-org.org/en/about-traceca/history-of-traceca", "international", ["appear", "operate", "parties", "route", "history"], True),
    S("rferl-1998", "Central Asia/Caucasus: Silk Road Conference Agrees On Eurasian Corridor", "RFE/RL", 1998, "публикация СМИ",
      "https://www.rferl.org/amp/1089437.html", "neutral", ["appear", "operate", "history"], True, note="9 сентября 1998 г."),
    S("mfa-am-traceca", "International organisations: TRACECA", "МИД Армении", None, "официальный документ стороны",
      "https://mfa.am/en/international-organisations/9", "ARM", ["appear", "parties", "history"], True),
    S("traceca-ferry-2014", "Ferry line Constanta – Batumi – Ilychevsk as the important transport nodal point in the TRACECA region",
      "Межправительственная комиссия TRACECA (Постоянный секретариат)", 2014, "официальный документ стороны",
      "https://traceca-org.org/en/news/single-news/n/ferry_line_constanta_batumi_ilychevsk_as_the_important_transport_nodal_point_in_the_traceca_region",
      "international", ["route", "history"], True, note="22 октября 2014 г."),
]
R.append(ROUTE(
    id="traceca", name=T("TRACECA (транспортный коридор Европа – Кавказ – Азия)", "TRACECA (Transport Corridor Europe–Caucasus–Asia)"), kind="multimodal",
    color="#7b3fa0", parties=["ARM", "AZE", "BGR", "GEO", "IRN", "KAZ", "KGZ", "MDA", "ROU", "TJK", "TUR", "TKM", "UKR", "UZB"],
    appear="1993-05", operate="1998-09-08",
    summary=T("Программа и межправительственное соглашение о развитии транспорта из Европы через Чёрное море, Кавказ и Каспийское море в Центральную Азию. "
              "Запущена в 1993 г. на конференции в Брюсселе при поддержке ЕС; основное многостороннее соглашение подписано в Баку в 1998 г. "
              "Коридор опирается на существующие порты, железные и автомобильные дороги стран-участниц.",
              "A programme and intergovernmental agreement for transport from Europe across the Black Sea, the Caucasus and the Caspian Sea to Central Asia. "
              "Launched in 1993 at a conference in Brussels with EU support; the Basic Multilateral Agreement was signed in Baku in 1998. "
              "The corridor relies on existing ports, railways and roads of the member states."),
    status=T("Действует как межправительственная программа; 14 стран-участниц, Постоянный секретариат в Баку с 2001 г.",
             "Operating as an intergovernmental programme; 14 member states, Permanent Secretariat in Baku since 2001."),
    branches=[
        BR("blacksea", "Черноморские паромы", "Black Sea ferries", [
            SEG(["chornomorsk", "w_odesa", "w_danube", "constanta"], mode="sea"), SEG(["constanta", "batumi"], mode="sea")],
           note=T("Паромная линия Черноморск (Ильичёвск) – Констанца – Батуми открыта в октябре 2014 г.", "The Chornomorsk (Illichivsk) – Constanța – Batumi ferry line opened in October 2014.")),
        BR("caucasus", "Кавказ – Каспий – Центральная Азия (схема)", "Caucasus – Caspian – Central Asia (schematic)", [
            SEG(["batumi", "tbilisi", "baku"]), SEG(["baku", "w_baku_s", "turkmenbashi"], mode="sea"), SEG(["turkmenbashi", "ashgabat", "tashkent"])],
           note=T("Точные маршруты TRACECA в прочитанных источниках не приведены; линия проведена через порты и столицы стран-участниц.",
                  "The sources read do not give exact TRACECA routes; the line runs through ports and capitals of member states.")),
        BR("kazakhstan", "Каспий – Казахстан (схема)", "Caspian – Kazakhstan (schematic)", [
            SEG(["baku", "w_baku_s", "w_absheron_e", "aktau"], mode="sea"), SEG(["aktau", "kuryk"])],
           note=T("Ветка показывает Казахстан — участника TRACECA. Путь через Каспий к портам Актау и Курык описан Всемирным банком для Среднего коридора; "
                  "как маршрут TRACECA он в прочитанных источниках не обозначен.",
                  "The branch shows Kazakhstan, a TRACECA member. The route across the Caspian to the ports of Aktau and Kuryk is described by the World Bank "
                  "for the Middle Corridor; the sources read do not name it as a TRACECA route.")),
    ],
    analysis="eastwest",
    capacity=[],
    volumes=[],
    history=[
        E("1993-05", "legal", "Конференция в Брюсселе: министры восьми стран Кавказа и Центральной Азии и ЕС запускают TRACECA.",
          "Brussels conference: ministers of eight Caucasus and Central Asian states and the EU launch TRACECA.", "traceca-history", "rferl-1998", "mfa-am-traceca"),
        E("1998-09-08", "legal", "В Баку подписано Основное многостороннее соглашение о международном транспорте по коридору.",
          "The Basic Multilateral Agreement on international transport along the corridor is signed in Baku.", "traceca-history", "rferl-1998"),
        E("2001-02-21", "event", "Открыт Постоянный секретариат в Баку.", "The Permanent Secretariat opens in Baku.", "traceca-history"),
        E("2014-10-16", "event", "Открыта паромная линия Ильичёвск – Констанца – Батуми.", "The Illichivsk – Constanța – Batumi ferry line opens.", "traceca-ferry-2014"),
    ],
    sources=src, confidence="low",
    review=REVIEW(conflicts=["Число участников: 14 (сайт TRACECA) или 13 (МИД Армении, где перечислены 12 стран, включая Монголию)",
                             "Дата подписания соглашения Арменией: 9 августа 1998 г. (МИД Армении) — при общей дате подписания 8 сентября 1998 г."],
                  notes=["Сводной статистики перевозок по коридору и данных о пропускной способности в открытых источниках не найдено",
                         "Сплошная линия показана с даты подписания соглашения (1998 г.): коридор опирается на уже действовавшие пути — допущение редакции",
                         "Вступление соглашения в силу 23.05.1999 — по одному источнику (МИД Армении)",
                         "Линия «Кавказ – Каспий – Центральная Азия» — схема, а не официальный маршрут",
                         "Ветка «Каспий – Казахстан» добавлена как схема, чтобы показать Казахстан; как маршрут TRACECA в источниках не обозначена"]),
))

# ============================================================================= МТК «СЕВЕР – ЮГ»
src = [
    S("ady-instc", "North-South Transport Corridor", "Азербайджанские железные дороги (ADY)", None, "официальный документ стороны",
      "https://freight.ady.az/en/international-corridors/north-south-transport-corridor", "AZE", ["appear", "parties", "route", "status"], True),
    S("iranprimer-instc", "International North-South Transport Corridor", "The Iran Primer (U.S. Institute of Peace)", 2023, "справочное издание",
      "https://iranprimer.usip.org/node/11761", "neutral", ["appear", "operate", "route", "volumes", "status", "history"], True,
      note="Без даты; последнее событие — 17 мая 2023 г."),
    S("erai-instc-2025", "Overcoming infrastructure barriers to the development of the International North-South Transport Corridor", "ERAI (index1520.com), по докладу ЕАБР",
      2025, "академическая работа", "https://index1520.com/upload/medialibrary/dfe/yi0ikrx2vy47e1bnf19wclcmp8i1w2pu/INSTC_EN.pdf", "neutral",
      ["route", "volumes", "capacity", "status", "operate"], True, note="Апрель 2025 г."),
    S("rferl-2014-kti", "Presidents Of Iran, Turkmenistan, Kazakhstan Inaugurate Railway", "RFE/RL", 2014, "публикация СМИ",
      "https://www.rferl.org/a/presidents-of-iran-turkmenistan-kazakhstan-inaugurate-railway/26722762.html", "neutral", ["operate", "capacity", "history"], True,
      note="3 декабря 2014 г."),
    S("irandaily-rasht", "Russian minister announces 15-million-ton freight capacity for Rasht–Astara railway", "Iran Daily", 2025, "публикация СМИ",
      "https://newspaper.irandaily.ir/7833/3/15400", "neutral", ["capacity", "status"], True, note="Без даты; по данным I квартала 2025 г."),
    S("mintrans-2026", "Объем перевозок по Международному транспортному коридору «Север-Юг» активно растет", "Министерство транспорта России", 2026,
      "официальный документ стороны", "https://mintrans.gov.ru/press-center/news/12937", "RUS", ["volumes"], True, note="2 сентября 2026 г."),
]
R.append(ROUTE(
    id="instc", name=T("Международный транспортный коридор «Север – Юг»", "International North–South Transport Corridor (INSTC)"), kind="multimodal",
    color="#2e7d32", parties=["RUS", "IRN", "IND", "AZE"], appear="2000-09-12", operate=None,
    summary=T("Коридор из России к Персидскому заливу и в Индию. Соглашение подписали Россия, Иран и Индия 12 сентября 2000 г. в Санкт-Петербурге; "
              "позже присоединились другие страны, в том числе Азербайджан (2005). Три ветви: западная — по железной дороге через Азербайджан; "
              "транскаспийская — морем через Каспий; восточная — через Казахстан и Туркменистан. Ключевой недостающий участок — железная дорога Решт – Астара в Иране.",
              "A corridor from Russia to the Persian Gulf and India. Russia, Iran and India signed the agreement on 12 September 2000 in St Petersburg; "
              "other states joined later, including Azerbaijan (2005). Three branches: the western one by rail through Azerbaijan; the trans-Caspian one "
              "by sea across the Caspian; the eastern one through Kazakhstan and Turkmenistan. The key missing link is the Rasht–Astara railway in Iran."),
    status=T("Действует частично: восточная и транскаспийская ветви работают; на западной не построен участок Решт – Астара (около 162 км), грузы перегружают на автотранспорт.",
             "Partly operating: the eastern and trans-Caspian branches work; on the western branch the Rasht–Astara section (about 162 km) is not built and cargo is transferred to road."),
    branches=[
        BR("trunk", "Поволжье", "Volga trunk", [SEG(["saratov", "astrakhan"], operate="2014-12-03")]),
        BR("west", "Западная ветвь (через Азербайджан)", "Western branch (via Azerbaijan)", [
            SEG(["astrakhan", "makhachkala", "derbent", "samur", "shirvan", "astara"], operate="2017-12"),
            SEG(["astara", "rasht"], planned=True, note=T("Железная дорога Решт – Астара не построена; соглашение о финансировании — май 2023 г.", "The Rasht–Astara railway is not built; financing agreement signed in May 2023.")),
            SEG(["rasht", "qazvin", "tehran"], operate="2019-03-06"),
        ]),
        BR("caspian", "Транскаспийская ветвь", "Trans-Caspian branch", [
            SEG(["astrakhan", "olya"], operate="2022"),
            SEG(["olya", "w_absheron_n", "w_absheron_e", "w_casp_s", "anzali"], mode="sea", operate="2022"),
            SEG(["anzali", "rasht"], operate="2022"),
        ]),
        BR("east", "Восточная ветвь (через Казахстан и Туркменистан)", "Eastern branch (via Kazakhstan and Turkmenistan)", [
            SEG(["astrakhan", "makat", "beyneu", "bolashak", "bereket", "inchehborun", "garmsar", "tehran"], operate="2014-12-03"),
        ]),
        BR("south", "Иран – Индия", "Iran – India", [
            SEG(["tehran", "bafq", "bandarabbas"], operate="2014-12-03"),
            SEG(["bandarabbas", "w_hormuz", "w_oman", "w_arab", "nhavasheva"], mode="sea", operate="2014-12-03"),
        ]),
    ],
    capacity=[
        CAP("Узкое место западной ветви — участок Дербент – Самур: около 8 млн т в год; российская часть — до 20 млн т к концу 2027 г.",
            "The western branch bottleneck is the Derbent–Samur section: about 8 million t a year; the Russian section is to reach 20 million t by end-2027.",
            ["erai-instc-2025"], kind="current"),
        CAP("После постройки железной дороги Решт – Астара (план — 2028 г.) — до 15 млн т в год.",
            "After the Rasht–Astara railway is built (planned for 2028): up to 15 million t a year.", ["erai-instc-2025", "irandaily-rasht"], kind="design"),
        CAP("Железная дорога Казахстан – Туркменистан – Иран: при открытии в 2014 г. — 10 млн т в год с ростом до 20 млн т; участок Болашак – Берекет сейчас — 10 млн т.",
            "Kazakhstan–Turkmenistan–Iran railway: 10 million t a year at opening in 2014, rising to 20 million t; the Bolashak–Bereket section today: 10 million t.",
            ["rferl-2014-kti", "erai-instc-2025"], kind="design"),
        CAP("Мощность российских портов Каспия — 23,5 млн т в год.", "Capacity of Russian Caspian ports: 23.5 million t a year.", ["erai-instc-2025"], kind="current"),
    ],
    volumes=[
        SERIES("total", "Все перевозки по коридору (все виды транспорта)", "All corridor traffic (all modes)", "млн т", "million t", [
            (2022, 19.0, ["erai-instc-2025"]), (2023, 22.6, ["erai-instc-2025"]), (2024, 26.9, ["erai-instc-2025"]),
        ], note=T("Оценка ERAI по докладу ЕАБР; включает перевозки всех стран коридора.", "ERAI estimate based on the EDB report; includes traffic of all corridor countries.")),
        SERIES("rus-irn", "Перевозки России и Ирана по маршрутам, 2025 г.", "Russia–Iran traffic by route, 2025", "млн т", "million t", [
            (2025, 1.8, ["mintrans-2026"]),
        ], note=T("Транскаспийский маршрут; по данным Минтранса России, в 2025 г. также: морем 2,8 млн т, автотранспортом 1,2 млн т, "
                  "по железной дороге западным маршрутом 0,66 млн т, восточным — 0,04 млн т.",
                  "Trans-Caspian route; per Russia's Ministry of Transport, 2025 also saw 2.8 million t by sea, 1.2 million t by road, "
                  "0.66 million t by rail on the western route and 0.04 million t on the eastern route.")),
    ],
    history=[
        E("2000-09-12", "legal", "Россия, Иран и Индия подписывают соглашение о коридоре «Север – Юг» в Санкт-Петербурге.",
          "Russia, Iran and India sign the North–South corridor agreement in St Petersburg.", "ady-instc", "iranprimer-instc"),
        E("2002-05-16", "legal", "Соглашение вступает в силу.", "The agreement enters into force.", "iranprimer-instc"),
        E("2005-09-20", "legal", "Азербайджан присоединяется к соглашению.", "Azerbaijan accedes to the agreement.", "ady-instc"),
        E("2014-12-03", "event", "Открыта железная дорога Узень – Берекет – Горган (Казахстан – Туркменистан – Иран).",
          "The Uzen–Bereket–Gorgan railway (Kazakhstan–Turkmenistan–Iran) opens.", "rferl-2014-kti", "iranprimer-instc"),
        E("2017-12", "event", "Испытан железнодорожный участок Астара (Азербайджан) – Астара (Иран).", "The Astara (Azerbaijan) – Astara (Iran) rail link is tested.", "iranprimer-instc"),
        E("2019-03-06", "event", "Открыта железная дорога Казвин – Решт.", "The Qazvin–Rasht railway opens.", "iranprimer-instc"),
        E("2022-07", "event", "Первая коммерческая перевозка по восточной ветви (3800 км).", "First commercial shipment on the eastern branch (3,800 km).", "erai-instc-2025"),
        E("2023-05-17", "legal", "Россия и Иран подписывают соглашение о финансировании железной дороги Решт – Астара.",
          "Russia and Iran sign a financing agreement for the Rasht–Astara railway.", "iranprimer-instc"),
    ],
    sources=src, confidence="low",
    review=REVIEW(conflicts=["Объём перевозок в 2022 г.: 19 млн т (ERAI, все виды транспорта) или «более 8 млн т» (The Iran Primer со ссылкой на Минтранс России) — разные определения",
                             "Длина недостающего участка Решт – Астара: 162 км (Iran Daily) или 167 км (ADY)"],
                  notes=["Ряд объёмов 2022–2024 гг. — по одному источнику (ERAI)",
                         "Общие участки (Саратов – Астрахань, Тегеран – Бендер-Аббас – Нава-Шева) показаны сплошными с открытия восточной ветви в декабре 2014 г. — допущение редакции",
                         "Участники соглашения в карточке — Россия, Иран, Индия и Азербайджан (по прочитанным источникам); Казахстан и Туркменистан показаны как страны, через которые проходит ветвь",
                         "Сплошная линия западной ветви с декабря 2017 г. (испытание участка Астара – Астара) и транскаспийской с 2022 г. — по одному источнику (The Iran Primer)",
                         "Вступление соглашения в силу 16.05.2002 — по одному источнику",
                         "Линии — схема через узлы, названные ERAI; координаты приблизительные"]),
))

# ============================================================================= СРЕДНИЙ КОРИДОР (ТМТМ)
src = [
    S("titr-history", "History of the Association", "Международная ассоциация «Транскаспийский международный транспортный маршрут»", None, "официальный документ стороны",
      "https://middlecorridor.com/en/about-the-association/history-en", "international", ["appear", "operate", "history"], True),
    S("bta-titr", "Explainer: Trans-Caspian International Transport Route (TITR)", "БТА (Болгарское телеграфное агентство)", 2025, "публикация СМИ",
      "https://www.bta.bg/en/news/1205568-explainer-trans-caspian-international-transport-route-titr-", "neutral", ["appear", "route", "volumes", "parties"], True),
    S("astanatimes-2015", "Trans-Caspian Rail Route Launched", "The Astana Times", 2015, "публикация СМИ",
      "https://astanatimes.com/2015/08/trans-caspian-rail-route-launched/", "neutral", ["operate", "route", "history"], True, note="5 августа 2015 г."),
    S("tengri-2015", "New transportation opportunities for Trans-Caspian Route: Nomad express container train welcomed in Baku", "Tengrinews", 2015,
      "публикация СМИ", "https://en.tengrinews.kz/news/261459", "neutral", ["operate", "route"], True, note="10 августа 2015 г."),
    S("astanatimes-2026", "Can Middle Corridor Deliver on Its Promise?", "Dana Omirgazy (The Astana Times)", 2026, "публикация СМИ",
      "https://astanatimes.com/2026/10/can-middle-corridor-deliver-on-its-promise/", "neutral", ["volumes", "capacity"], True,
      note="12 октября 2026 г.; данные Министерства транспорта Казахстана"),
    S("timesca-2026", "Freight volumes on Middle Corridor through Kazakhstan rise fivefold in seven years", "Sergey Kwan (The Times of Central Asia)", 2026,
      "публикация СМИ", "https://timesca.com/freight-volumes-on-middle-corridor-through-kazakhstan-rise-fivefold-in-seven-years/", "neutral", ["volumes", "capacity"], True,
      note="11 марта 2026 г."),
    S("bmge-2026", "Container traffic surges 36% on Trans-Caspian Middle Corridor in 2025", "BM.GE", 2026, "публикация СМИ",
      "https://bm.ge/en/news/container-traffic-surges-36-on-trans-caspian-middle-corridor-in-2025", "neutral", ["volumes"], True,
      note="17 февраля 2026 г.; данные Ассоциации ТМТМ"),
    S("wb-2023", "Middle Corridor through Central Asia, Caucasus Can Boost Trade Connectivity and Supply Chain Resilience", "Всемирный банк", 2023,
      "официальный документ стороны", "https://www.worldbank.org/en/news/press-release/2023/11/27/middle-corridor-through-central-asia-caucasus-can-boost-trade-connectivity-and-supply-chain-resilience",
      "international", ["capacity"], True, note="27 ноября 2023 г."),
    S("astanatimes-2023-wb", "World Bank Estimates Tripling Trade Volumes on Middle Corridor by 2030", "The Astana Times", 2023, "публикация СМИ",
      "https://astanatimes.com/2023/11/world-bank-estimates-tripling-trade-volumes-on-middle-corridor-by-2030/", "neutral", ["capacity"], True),
]
R.append(ROUTE(
    id="middle", name=T("Средний коридор (Транскаспийский международный транспортный маршрут, ТМТМ)", "Middle Corridor (Trans-Caspian International Transport Route, TITR)"),
    kind="multimodal", color="#d35400", parties=["KAZ", "AZE", "GEO"], appear="2013-11-07", operate="2015-08-03",
    summary=T("Маршрут из Китая через Казахстан, Каспийское море, Азербайджан и Грузию в Турцию и Европу (в том числе через черноморские порты Болгарии и Румынии). "
              "Соглашение о координационном комитете подписали железные дороги Казахстана, Азербайджана и Грузии в 2013 г.; первый контейнерный поезд прошёл в 2015 г. "
              "Перевозки резко выросли после 2022 г., когда грузы стали искать пути в обход России.",
              "A route from China through Kazakhstan, the Caspian Sea, Azerbaijan and Georgia to Türkiye and Europe (including via Black Sea ports in Bulgaria and Romania). "
              "The railways of Kazakhstan, Azerbaijan and Georgia agreed to set up a coordination committee in 2013; the first container train ran in 2015. "
              "Traffic rose sharply after 2022 as shippers sought routes avoiding Russia."),
    status=T("Действует; паромная переправа через Каспий и порты — главные ограничения пропускной способности.",
             "Operating; the Caspian ferry crossing and ports are the main capacity constraints."),
    branches=[
        BR("main", "Китай – Каспий – Грузия", "China – Caspian – Georgia", [
            SEG(["dostyk", "aktau"]), SEG(["aktau", "w_absheron_e", "alyat"], mode="sea"), SEG(["kuryk", "aktau"]),
            SEG(["alyat", "tbilisi", "poti"]), SEG(["tbilisi", "batumi"])]),
        BR("blacksea", "Черноморские линии в Европу", "Black Sea lines to Europe", [
            SEG(["poti", "varna"], mode="sea"), SEG(["batumi", "w_sinop", "burgas"], mode="sea"), SEG(["poti", "constanta"], mode="sea")]),
        BR("turkey", "Через Турцию", "Via Türkiye", [SEG(["tbilisi", "kars", "istanbul"])],
           note=T("Направление через Турцию — схема. Железная дорога Баку – Тбилиси – Карс открыта 30 октября 2017 г. (по данным МИД Турции).",
                  "The route via Türkiye is schematic. The Baku–Tbilisi–Kars railway opened on 30 October 2017 (per Türkiye's Foreign Ministry).")),
    ],
    analysis="eastwest",
    capacity=[
        CAP("Пропускная способность — около 6 млн т и до 182 тыс. контейнеров в год (Министерство транспорта Казахстана).",
            "Capacity: about 6 million t and up to 182,000 containers a year (Kazakhstan's Ministry of Transport).", ["astanatimes-2026"], kind="current"),
        CAP("Всемирный банк (2023): при вложениях в инфраструктуру объёмы к 2030 г. могут утроиться, а время в пути — сократиться вдвое.",
            "World Bank (2023): with infrastructure investment, volumes could triple and transit time halve by 2030.", ["wb-2023", "astanatimes-2023-wb"], kind="estimate"),
        CAP("Цель Казахстана — 300 тыс. ДФЭ в год к 2029 г.", "Kazakhstan's goal: 300,000 TEU a year by 2029.", ["timesca-2026"], kind="target"),
    ],
    volumes=[
        SERIES("kz", "Перевозки по ТМТМ (данные Казахстана)", "TITR traffic (Kazakhstan's data)", "млн т", "million t", [
            (2021, 0.586, ["bta-titr"]), (2022, 1.7, ["astanatimes-2026"]), (2023, 2.76, ["astanatimes-2026"]),
            (2024, 4.5, ["astanatimes-2026", "timesca-2026", "bta-titr"]), (2025, 4.1, ["astanatimes-2026"]),
        ]),
        SERIES("teu", "Контейнеры", "Containers", "тыс. ДФЭ", "thousand TEU", [
            (2024, 56.5, ["astanatimes-2026"]), (2025, 77.0, ["astanatimes-2026", "timesca-2026"]),
        ]),
    ],
    history=[
        E("2013-11-07", "legal", "Железные дороги Казахстана, Азербайджана и Грузии подписывают в Астане соглашение о создании координационного комитета ТМТМ.",
          "The railways of Kazakhstan, Azerbaijan and Georgia sign an agreement in Astana to set up the TITR coordination committee.", "titr-history", "bta-titr"),
        E("2014-02", "event", "Создан координационный комитет.", "The coordination committee is established.", "titr-history", "bta-titr"),
        E("2015-08-03", "event", "Первый контейнерный поезд «Номад Экспресс» (Шихэцзы – Достык – Актау – Алят) прибывает в Баку.",
          "The first container train, Nomad Express (Shihezi – Dostyk – Aktau – Alyat), arrives in Baku.", "astanatimes-2015", "tengri-2015"),
        E("2017-02", "event", "Начинает работу Международная ассоциация ТМТМ.", "The International Association TITR begins operating.", "titr-history", "bta-titr"),
        E("2024", "event", "Перевезено 4,5 млн т — в несколько раз больше, чем до 2022 г.", "4.5 million t carried — several times more than before 2022.", "astanatimes-2026", "timesca-2026"),
    ],
    sources=src, confidence="medium",
    review=REVIEW(conflicts=["2025 г.: 4,1 млн т, снижение на 8,9% (Министерство транспорта Казахстана, по The Astana Times) или 1,867 млн т, рост на 0,5% "
                             "(Ассоциация ТМТМ, по BM.GE) — у ведомства и ассоциации разные методики учёта",
                             "Контейнеры в 2025 г.: около 77 тыс. ДФЭ (Казахстан, по The Astana Times и TimesCA) или 42 тыс. ДФЭ (КТЖ, по Trend)"],
                  notes=["Объёмы 2021–2023 и 2025 гг. — по одному источнику каждый",
                         "Пропускная способность 6 млн т — по одному источнику",
                         "Направление через Турцию и узел Карс — схема"]),
))

# ============================================================================= IMEC
src = [
    S("wh-imec-mou", "Memorandum of Understanding on the Principles of an India – Middle East – Europe Economic Corridor", "Белый дом (архив администрации Байдена)", 2023,
      "официальный документ стороны", "https://bidenwhitehouse.archives.gov/briefing-room/statements-releases/2023/09/09/memorandum-of-understanding-on-the-principles-of-an-india-middle-east-europe-economic-corridor/",
      "USA", ["appear", "parties", "route", "status"], True, note="9 сентября 2023 г."),
    S("reuters-2023-imec", "US, India, Saudi, EU unveil rail, ports deal on G20 sidelines", "Reuters (The Jakarta Post)", 2023, "публикация СМИ",
      "https://www.thejakartapost.com/business/2023/09/10/us-india-saudi-eu-unveil-rail-ports-deal-on-g20-sidelines.html", "neutral", ["appear", "parties", "route"], True,
      note="10 сентября 2023 г."),
    S("mei-2026", "The India-Middle East-Europe Economic Corridor (backgrounder)", "Walter Murdoch, Karen E. Young (Middle East Institute)", 2026, "справочное издание",
      "https://mei.edu/backgrounder/the-india-middle-east-europe-economic-corridor/", "neutral", ["route", "status", "capacity"], True, note="3 июня 2026 г."),
    S("theprint-2026", "IMEC gets a Trump boost as the India-Middle East-Europe trade route remains a work in progress", "Debdutta Chakraborty (ThePrint)", 2026,
      "публикация СМИ", "https://theprint.in/diplomacy/imec-gets-a-trump-boost-as-the-india-middle-east-europe-trade-route-remains-a-work-in-progress/3054039/",
      "neutral", ["status", "capacity", "parties"], True, note="26 сентября 2026 г."),
    S("indiaseatrade-2024", "Work on India-UAE leg of $20b trade corridor set to kick off", "India Sea Trade News", 2024, "публикация СМИ",
      "https://indiaseatradenews.com/work-on-india-uae-leg-of-20b-trade-corridor-set-to-kick-off/", "neutral", ["route", "capacity", "status"], True, note="28 июня 2024 г."),
]
R.append(ROUTE(
    id="imec", name=T("Экономический коридор «Индия – Ближний Восток – Европа» (IMEC)", "India–Middle East–Europe Economic Corridor (IMEC)"), kind="economic",
    color="#1f5fbf", parties=["IND", "SAU", "ARE", "FRA", "DEU", "ITA", "USA"], appear="2023-09-09", operate=None,
    summary=T("Проект, объявленный на саммите G20 в Нью-Дели 9 сентября 2023 г.: восточный коридор связывает Индию с Персидским заливом, северный — Залив с Европой. "
              "Предусмотрены морские перевозки из индийских портов в ОАЭ, железная дорога через Саудовскую Аравию и Иорданию до порта Хайфа, "
              "далее морем в Европу, а также кабели связи, линии электропередачи и трубопровод для водорода. Меморандум не имеет обязательной силы.",
              "A project announced at the G20 summit in New Delhi on 9 September 2023: an eastern corridor links India to the Persian Gulf and a northern one links the Gulf to Europe. "
              "It envisages shipping from Indian ports to the UAE, a railway across Saudi Arabia and Jordan to the port of Haifa, then by sea to Europe, "
              "plus data and power cables and a hydrogen pipeline. The memorandum is not legally binding."),
    status=T("Проект; недостающие железные дороги (Эль-Гувайфат – Харад, участок через Иорданию) не построены. Работа замедлилась из-за войн в Газе и вокруг Ирана.",
             "Project; the missing railways (Al-Ghuwaifat – Haradh, the section across Jordan) are not built. Work slowed because of the wars in Gaza and around Iran."),
    branches=[
        BR("east", "Восточный коридор: Индия – Залив", "Eastern corridor: India – Gulf", [
            SEG(["mundra", "w_kutch", "w_oman", "w_hormuz", "w_musandam", "w_gulf", "jebelali"], mode="sea"),
            SEG(["nhavasheva", "fujairah"], mode="sea")]),
        BR("rail", "Железная дорога через Аравию", "Rail across Arabia", [
            SEG(["jebelali", "ghuwaifat"]), SEG(["ghuwaifat", "haradh"], planned=True,
                note=T("Разрыв около 269 км (оценка — около 2 млрд долл.).", "A gap of about 269 km (estimated at about $2 billion).")),
            SEG(["haradh", "hadithah"]), SEG(["hadithah", "mafraq", "beitshean"], planned=True,
                note=T("Железной дороги через Иорданию нет; обязательств по строительству не принято.", "There is no railway across Jordan; no construction commitments have been made.")),
            SEG(["beitshean", "haifa"])]),
        BR("north", "Северный коридор: Средиземное море – Европа", "Northern corridor: Mediterranean – Europe", [
            SEG(["haifa", "w_rhodes", "w_cyclades", "piraeus"], mode="sea"),
            SEG(["haifa", "w_crete_s", "w_ionian", "w_otranto", "w_adriatic", "w_adriatic_n", "w_istria", "trieste"], mode="sea"),
            SEG(["haifa", "w_crete_s", "w_sicily", "w_sardinia", "w_lion", "marseille"], mode="sea")]),
    ],
    capacity=[
        CAP("Ожидаемый эффект: доставка быстрее до 40%, логистика дешевле до 30%.", "Expected effect: delivery up to 40% faster and logistics up to 30% cheaper.",
            ["theprint-2026", "mei-2026"], kind="estimate"),
        CAP("Потенциал — около 3 млн ДФЭ в год.", "Potential: about 3 million TEU a year.", ["mei-2026"], kind="estimate"),
        CAP("Длина около 4800 км, стоимость около 20 млрд долл.; цель — 48 часов от Мундры до Хайфы.",
            "About 4,800 km long and about $20 billion; the goal is 48 hours from Mundra to Haifa.", ["indiaseatrade-2024"], kind="design"),
    ],
    volumes=[],
    history=[
        E("2023-09-09", "legal", "На полях саммита G20 в Нью-Дели подписан меморандум о принципах коридора.", "A memorandum on the corridor's principles is signed on the sidelines of the G20 summit in New Delhi.",
          "wh-imec-mou", "reuters-2023-imec"),
        E("2024-06", "event", "Работа начинается с цифровой платформы обмена документами между портами Индии и ОАЭ.",
          "Work starts with a digital document-exchange platform between Indian and UAE ports.", "indiaseatrade-2024"),
        E("2026-09", "event", "США заявляют о поддержке коридора; проект остаётся незавершённым.", "The US voices support for the corridor; the project remains a work in progress.", "theprint-2026"),
    ],
    sources=src, confidence="medium",
    review=REVIEW(conflicts=["Состав участников: меморандум 2023 г. называет Саудовскую Аравию, ЕС, Индию, ОАЭ, Францию, Германию, Италию и США; "
                             "Middle East Institute относит к основным участникам также Израиль и Иорданию, отмечая, что Иордания ничего официально не подписывала"],
                  notes=["Действующих перевозок по коридору как единому маршруту нет; объёмы не показаны",
                         "Потенциал 3 млн ДФЭ, длина и стоимость — по одному источнику",
                         "ЕС — участник меморандума; на карте закрашиваются только государства",
                         "Морские линии — схема; порты Индии и ОАЭ — по India Sea Trade News (порт Кандла на схеме не показан), узлы в Аравии и Европе — по Middle East Institute"]),
))

# ============================================================================= TRIPP
src = [
    S("mfa-am-tripp", "Joint Statement on the Publication of the Armenia-U.S. Implementation Framework for the Trump Route for International Peace and Prosperity (TRIPP)",
      "МИД Армении", 2026, "официальный документ стороны", "https://www.mfa.am/en/press-releases/2026/01/14/TRIPP/13721", "ARM,USA",
      ["appear", "parties", "route", "status"], True, note="14 января 2026 г."),
    S("eurasianet-2026-01", "US and Armenia unveil TRIPP development blueprint", "Eurasianet", 2026, "публикация СМИ",
      "https://eurasianet.org/us-and-armenia-unveil-tripp-development-blueprint", "neutral", ["route", "status"], True, note="14 января 2026 г."),
    S("carnegie-2026", "Rewiring the South Caucasus: TRIPP and the New Geopolitics of Connectivity", "Thomas de Waal, Areg Kochinyan, Zaur Shiriyev (Carnegie Endowment)", 2026,
      "академическая работа", "https://carnegieendowment.org/research/2026/03/rewiring-the-south-caucasus-tripp-and-the-new-geopolitics-of-connectivity", "neutral",
      ["appear", "route", "status", "capacity"], True, note="1 апреля 2026 г."),
    S("eurasianet-2026-09", "Start date for TRIPP trade corridor connecting Armenia and Azerbaijan pushed back", "Eurasianet", 2026, "публикация СМИ",
      "https://eurasianet.org/start-date-for-tripp-trade-corridor-connecting-armenia-and-azerbaijan-pushed-back", "neutral", ["route", "status"], True,
      note="10 сентября 2026 г."),
]
R.append(ROUTE(
    id="tripp", name=T("Маршрут Трампа во имя международного мира и процветания (TRIPP)", "Trump Route for International Peace and Prosperity (TRIPP)"), kind="multimodal",
    color="#a07800", parties=["ARM", "AZE", "USA"], appear="2025-08-08", operate=None,
    summary=T("Транзитный маршрут через территорию Армении, связывающий основную часть Азербайджана с Нахичеванской Автономной Республикой и далее с сетью Турции. "
              "Объявлен 8 августа 2025 г. на встрече лидеров Армении и Азербайджана в Белом доме. Основа — восстановление железной дороги длиной около 43 км "
              "вдоль границы Армении с Ираном через Мегри; планируются также дорога, газопровод, линии электропередачи и оптоволокно. "
              "Рамочный документ США и Армении (январь 2026 г.) закрепляет суверенитет и юрисдикцию Армении над пограничным и таможенным контролем.",
              "A transit route across Armenian territory linking the main part of Azerbaijan with the Nakhchivan Autonomous Republic and on to Türkiye's network. "
              "Announced on 8 August 2025 at a meeting of the Armenian and Azerbaijani leaders at the White House. Its core is restoring a railway of about 43 km "
              "along Armenia's border with Iran through Meghri; a road, a gas pipeline, power lines and fibre optics are also planned. "
              "The US–Armenia framework (January 2026) affirms Armenia's sovereignty and jurisdiction over border and customs control."),
    status=T("Проект; строительство в Армении ожидается не раньше 2027 г. Компания-разработчик: 74% у США, 26% у Армении, права — на 49 лет с возможным продлением на 50 лет.",
             "Project; construction in Armenia is not expected before 2027. Development company: 74% US, 26% Armenia; rights for 49 years, extendable by 50 years."),
    branches=[
        BR("armenia", "Армянский участок (около 42–43 км, через Мегри)", "Armenian section (about 42–43 km, via Meghri)", [
            SEG(["aze_border_e", "meghri", "nakh_border_w"])]),
        BR("nakhchivan", "Связь с Нахичеванью", "Link to Nakhchivan", [SEG(["nakh_border_w", "julfa", "nakhchivan"])],
           note=T("Азербайджан модернизирует нахичеванский участок; связь с сетью Турции — схема.", "Azerbaijan is upgrading the Nakhchivan section; the link to Türkiye's network is schematic.")),
    ],
    capacity=[
        CAP("Данных о пропускной способности нет. Оценка стоимости железнодорожного участка 43 км — 250–400 млн долл.",
            "No capacity data. The 43-km rail section is estimated at $250–400 million.", ["carnegie-2026"], kind="estimate"),
    ],
    volumes=[],
    history=[
        E("2025-08-08", "legal", "Совместная декларация Армении и Азербайджана в Белом доме; маршрут получает название TRIPP.",
          "Armenia–Azerbaijan joint declaration at the White House; the route is named TRIPP.", "mfa-am-tripp", "carnegie-2026"),
        E("2026-01-13", "legal", "США и Армения публикуют рамочный документ о реализации TRIPP.", "The US and Armenia publish the TRIPP implementation framework.",
          "mfa-am-tripp", "eurasianet-2026-01"),
        E("2026-09", "event", "Начало строительства перенесено: работы не начнутся раньше 2027 г.", "Start of construction postponed: works will not begin before 2027.", "eurasianet-2026-09"),
    ],
    sources=src, confidence="medium",
    review=REVIEW(conflicts=["Длина армянского участка: около 42 км (Eurasianet) или 43 км (Carnegie)"],
                  notes=["Рамочный документ указывает, что места прохождения маршрута будут определены позже; линия через Мегри — по описанию Carnegie и Eurasianet",
                         "Перенос начала строительства на 2027 г. — по одному источнику",
                         "Название, используемое в Азербайджане, в карточку не включено: источник не прочитан"]),
))


# ============================================================================= СПРАВКА «ЗНАЧЕНИЕ»: TRACECA И СРЕДНИЙ КОРИДОР
# Тезисы автора карты (таблица «выгоды / риски» по странам) проверены по источникам и переписаны нейтрально,
# с указанием, чья это оценка. Тезисы без подтверждения не включены (см. review.notes).
# Пункт с источниками одной организации помечается на сайте «1 источник» (считает build_routes.py).

def PT(ru, en, *src):
    return OD(text=T(ru, en), source_ids=list(src))


# Коды Correlates of War (gwcode в CShapes) — для подсветки страны на карте; у Румынии в CShapes нет ISO-кода
GW = {"KAZ": 705, "UZB": 704, "TKM": 701, "AZE": 373, "GEO": 372, "TUR": 640, "UKR": 369, "ROU": 360,
      "ARM": 371, "IRN": 630, "CHN": 710, "USA": 2, "RUS": 365}


def ACTOR(code, group, ru, en, econ=(), pol=(), risks=(), confidence="medium", note=None):
    """group: route — страны маршрутов; external — другие участники и внешние игроки. code — ISO-код или EU."""
    return OD(code=code, gw=GW.get(code), group=group, name=T(ru, en), econ=list(econ), pol=list(pol), risks=list(risks),
              confidence=confidence, note=note)


def REUSE(rid, sid):
    """Источник, уже описанный в карточке маршрута rid."""
    r = next(x for x in R if x["id"] == rid)
    return next(s for s in r["sources"] if s["id"] == sid)


A_SRC = [
    S("ew-wb-2023", "Middle Trade and Transport Corridor: Policies and Investments to Triple Freight Volumes and Halve Travel Time by 2030", "Всемирный банк",
      2023, "академическая работа", "https://www.developmentaid.org/api/frontend/cms/file/2023/11/Middle-Trade-and-Transport-Corridor-World-Bank-FINAL.pdf",
      "international", ["analysis"], True, note="Ноябрь 2023 г.; прочитана копия PDF, размещённая DevelopmentAid"),
    S("ew-oecd-2023", "Realising the Potential of the Middle Corridor", "ОЭСР", 2023, "академическая работа",
      "https://www.oecd.org/en/publications/realising-the-potential-of-the-middle-corridor_635ad854-en/full-report.html", "international", ["analysis"], False,
      note="Прочитано только описание доклада"),
    S("ew-oecd-2025", "Enhancing the Competitiveness of the Trans-Caspian Transport Corridor in Central Asia", "ОЭСР", None, "академическая работа",
      "https://www.oecd.org/en/publications/enhancing-the-competitiveness-of-the-trans-caspian-transport-corridor-in-central-asia_f261e7fa-en/full-report/turkmenistan_17b40db7",
      "international", ["analysis"], False, note="Прочитано только описание доклада; год выпуска на странице не указан"),
    S("ew-bri-2023", "Middle Corridor: from Western-initiated TRACECA to China's Belt and Road Initiative", "Vusal Guliyev (Baku Research Institute)", 2023,
      "академическая работа", "https://bakuresearchinstitute.org/en/middle-corridor-from-western-initiated-traceca-to-chinas-belt-and-road-initiative/",
      "neutral", ["analysis"], True, note="11 сентября 2023 г."),
    S("ew-ec-2024", "Global Gateway: EU and Central Asian countries agree building blocks to develop Trans-Caspian transport corridor", "Европейская комиссия", 2024,
      "официальный документ стороны",
      "https://international-partnerships.ec.europa.eu/news-and-events/news/global-gateway-eu-and-central-asian-countries-agree-building-blocks-develop-trans-caspian-transport-2024-01-30_en",
      "EU", ["analysis"], True, note="30 января 2024 г.; название по адресу страницы"),
    S("ew-scmp-2026", "Alternate Route: China Invests in Europe Cargo Corridor That Avoids Russia, Middle East", "Ralph Jennings (South China Morning Post; перепечатка Caspian Post)",
      None, "публикация СМИ", "https://caspianpost.com/regions/alternate-route-china-invests-in-europe-cargo-corridor-that-avoids-russia-middle-east",
      "neutral", ["analysis"], True, note="29 июня; год на странице не указан"),
    S("ew-merics-2019", "On the \"Middle Corridor,\" China is largely absent", "Jacob Mardell (MERICS)", 2019, "академическая работа",
      "https://merics.org/index%2Ephp/en/comment/middle-corridor-china-largely-absent", "neutral", ["analysis"], True,
      note="25 октября 2019 г.; впервые опубликовано в Berlin Policy Journal"),
    S("ew-timesca-2024-uzb", "Azerbaijan Is Bringing Uzbekistan into the Middle Corridor", "Robert M. Cutler (The Times of Central Asia)", 2024, "публикация СМИ",
      "https://timesca.com/azerbaijan-is-bringing-uzbekistan-into-the-middle-corridor/", "neutral", ["analysis"], True, note="19 сентября 2024 г."),
    S("ew-pmc-2026", "Middle Corridor Transit Cargo Flows: Georgia", "PMC Research", 2026, "датасет", "https://research.pmcg-i.com/periodic/15",
      "neutral", ["analysis"], True, note="8 сентября 2026 г."),
    S("ew-eurasianet-anaklia", "China quietly exits Georgian port deal", "Eurasianet", 2026, "публикация СМИ",
      "https://eurasianet.org/china-quietly-exits-georgian-port-deal", "neutral", ["analysis"], True, note="8 июля 2026 г."),
    S("ew-intellinews-tkm", "Red tape means Turkmenistan's modern Caspian Sea port operating at third of capacity, says Middle Corridor official", "bne IntelliNews",
      2026, "публикация СМИ",
      "https://www.intellinews.com/red-tape-means-turkmenistan-s-modern-caspian-sea-port-operating-at-third-of-capacity-says-middle-corridor-official-450563/",
      "neutral", ["analysis"], True, note="24 июня 2026 г.; слова генсекретаря TRACECA Ж. Чориева из интервью Gazeta.uz в пересказе Turkmen News"),
    S("ew-mfa-tr", "Türkiye's Multilateral Transportation Policy", "МИД Турции", None, "официальный документ стороны",
      "https://mfa.gov.tr/turkiye_s-multilateral-transportation-policy.en.mfa", "TUR", ["analysis"], True, note="Без даты; название по адресу страницы"),
    S("ew-oc-2023", "Armenia proposes opening regional transport links as part of Crossroads of Peace", "OC Media", 2023, "публикация СМИ",
      "https://oc-media.org/armenia-proposes-opening-regional-transport-links-as-part-of-crossroads-of-peace", "neutral", ["analysis"], True,
      note="27 октября 2023 г.; название по адресу страницы"),
    S("ew-aljazeera-2025", "Iran rejects planned transit corridor outlined in Armenia-Azerbaijan pact", "Al Jazeera", 2025, "публикация СМИ",
      "https://aljazeera.com/news/2025/8/9/iran-rejects-planned-transit-corridor-outlined-in-armenia-azerbaijan-pact", "neutral", ["analysis"], True,
      note="9 августа 2025 г."),
    S("ew-caci-2024", "Is the Aras Corridor an Alternative to Zangezur?", "Vali Kaleji (CACI Analyst)", 2024, "академическая работа",
      "https://www.cacianalyst.org/publications/analytical-articles/item/13788-is-the-aras-corridor-an-alternative-to-zangezur", "neutral", ["analysis"], True,
      note="5 февраля 2024 г.; название по адресу страницы"),
    S("ew-oc-2025-russia", "Russian officials issue contradictory statements on Armenia–Azerbaijan Washington summit", "OC Media", 2025, "публикация СМИ",
      "https://oc-media.org/russian-officials-issue-contradictory-statements-on-armenia-azerbaijan-washington-summit", "neutral", ["analysis"], True,
      note="Не ранее 6 сентября 2025 г. (дата заявления А. Оверчука)"),
    S("ew-trilateral-2020", "Trilateral Statement of the leaders of Azerbaijan, Russian Federation and Armenia of November 10, 2020", "МИД Азербайджана (текст заявления)",
      2020, "официальный документ стороны",
      "https://mfa.gov.az/en/category/end-of-the-conflict-in-november-2020-and-post-conflict-situation/trilateral-statement-of-the-leaders-of-azerbaijan-russian-federation-and-armenia-of-november-10-2020",
      "AZE,ARM,RUS", ["analysis"], True, page="п. 9"),
    S("ew-national-2026", "AD Ports boosts Middle Corridor strategy with Black Sea deal", "The National", 2026, "публикация СМИ",
      "https://www.thenationalnews.com/business/economy/2026/04/14/ad-ports-boosts-middle-corridor-strategy-with-black-sea-deal/", "neutral", ["analysis"], True,
      note="14 апреля 2026 г.; название по адресу страницы"),
    S("ew-rbj-2019", "Grampet Group will connect Constanta Port to Asia-Europe rail transit through the Middle Corridor", "Romanian Business Journal", 2019,
      "публикация СМИ", "https://www.romanianbusinessjournal.ro/grampet-group-will-connect-constanta-port-to-asia-europe-rail-transit-through-the-middle-corridor/",
      "neutral", ["analysis"], True, note="23 октября 2019 г."),
    S("ew-pravda-2025", "Ukraine and Georgia resume ferry service", "Украинская правда", 2025, "публикация СМИ",
      "https://www.pravda.com.ua/eng/news/2025/04/10/7506919", "neutral", ["analysis"], True, note="10 апреля 2025 г."),
    S("ew-reuters-2024", "Ukraine Resumes Ferry Services to Georgia's Black Sea Port of Batumi", "Reuters (MarineLink)", 2024, "публикация СМИ",
      "https://www.marinelink.com/news/ukraine-resumes-ferry-services-georgias-514594", "neutral", ["analysis"], True, note="19 июня 2024 г."),
]
A_SRC += [REUSE("middle", "astanatimes-2026"), REUSE("middle", "bmge-2026"), REUSE("traceca", "traceca-history"), REUSE("traceca", "traceca-ferry-2014"),
          REUSE("tripp", "carnegie-2026"), REUSE("tripp", "eurasianet-2026-09"), REUSE("tripp", "mfa-am-tripp"), REUSE("tripp", "eurasianet-2026-01"),
          REUSE("instc", "erai-instc-2025"), REUSE("instc", "mintrans-2026")]

GENERAL = [
    OD(id="link", title=T("TRACECA и Средний коридор", "TRACECA and the Middle Corridor"), points=[
        PT("TRACECA запущена при поддержке ЕС в 1993 г. для развития портов и сухопутной инфраструктуры; основа Среднего коридора (ТМТМ) заложена позже — в 2013 г. в Астане. "
           "Аналитики описывают Средний коридор как продолжение того же пути через Кавказ и Каспий, поэтому справка общая для двух маршрутов.",
           "TRACECA was launched with EU support in 1993 to develop port and land infrastructure; the Middle Corridor (TITR) was founded later, in 2013 in Astana. "
           "Analysts describe the Middle Corridor as a continuation of the same route across the Caucasus and the Caspian, so this section is shared by both routes.",
           "ew-wb-2023", "ew-bri-2023"),
        PT("Генеральный секретарь TRACECA публично оценивает работу портов транскаспийского пути — например, туркменского порта Туркменбаши.",
           "The TRACECA Secretary General publicly assesses the work of trans-Caspian ports, such as Turkmenistan's port of Turkmenbashi.", "ew-intellinews-tkm"),
    ]),
    OD(id="geoecon", title=T("Геоэкономика", "Geo-economics"), points=[
        PT("Путь связывает Китай и Центральную Азию с Европой в обход России и не зависит от морских маршрутов через Ближний Восток и вокруг Африки. "
           "После 2022 г. санкции осложнили северный путь через Россию, и перевозки через Каспий выросли.",
           "The route links China and Central Asia with Europe while bypassing Russia and the sea routes via the Middle East and around Africa. "
           "After 2022, sanctions complicated the northern route through Russia and traffic across the Caspian grew.",
           "ew-oecd-2023", "ew-scmp-2026", "ew-bri-2023"),
        PT("По времени путь выигрывает у моря: 15–18 дней из Китая в Европу против 45–60 дней по океану (оценка турецкого дипломатического источника); "
           "по данным Казахстана, доставка сократилась с 38 до 13–17 дней.",
           "It is faster than the sea: 15–18 days from China to Europe versus 45–60 days by ocean (a Turkish diplomatic source's estimate); "
           "according to Kazakhstan, delivery time has fallen from 38 to 13–17 days.",
           "ew-scmp-2026", "astanatimes-2026"),
        PT("Но объёмы пока малы: по прогнозу Всемирного банка, через Каспий пойдёт около 1% торговли Китая и ЕС; путь уступает северному через Россию по ёмкости и цене.",
           "But volumes are still small: the World Bank expects the Caspian route to carry about 1% of China–EU trade; it is less capacious and more costly than the northern route via Russia.",
           "ew-wb-2023", "ew-scmp-2026", "ew-merics-2019"),
    ]),
    OD(id="geopol", title=T("Геополитика", "Geopolitics"), points=[
        PT("В развитии коридора одновременно участвуют ЕС (10 млрд евро в рамках Global Gateway), Китай (порты Актау и Баку, консорциум перевозчиков), "
           "США (TRIPP) и Турция (железная дорога Карс – Нахичевань).",
           "The EU (€10 billion under Global Gateway), China (the ports of Aktau and Baku, a carriers' consortium), the US (TRIPP) and Türkiye "
           "(the Kars–Nakhchivan railway) are all involved in developing the corridor.",
           "ew-ec-2024", "ew-scmp-2026", "astanatimes-2026", "carnegie-2026"),
        PT("По оценкам источников, выигрывают прежде всего транзитные страны и внешние игроки, ищущие путь в обход России; транзитная роль России и Ирана снижается. Подробно — по странам ниже.",
           "According to the sources, the main beneficiaries are the transit countries and external actors seeking a route around Russia, while the transit role of Russia and Iran declines. Details by country are below.",
           "ew-wb-2023", "carnegie-2026", "ew-bri-2023"),
    ]),
    OD(id="forecast", title=T("Прогноз и факт", "Forecast and reality"), points=[
        PT("Всемирный банк (2023): при вложениях в инфраструктуру перевозки через Каспий к 2030 г. утроятся по сравнению с 2021 г. — до 11 млн т.",
           "World Bank (2023): with infrastructure investment, traffic across the Caspian would triple by 2030 compared with 2021, to 11 million t.", "ew-wb-2023"),
        PT("Факт 2025 г. считают по-разному: 4,1 млн т (Министерство транспорта Казахстана) или 1,867 млн т (Ассоциация ТМТМ). Сопоставимой статистики нет, "
           "а сводных данных по TRACECA в открытых источниках нет вовсе.",
           "Figures for 2025 differ: 4.1 million t (Kazakhstan's Ministry of Transport) or 1.867 million t (the TITR Association). There are no comparable statistics, "
           "and no consolidated TRACECA data in open sources at all.",
           "astanatimes-2026", "bmge-2026"),
    ]),
    OD(id="risks", title=T("Риски", "Risks"), points=[
        PT("Узкие места (Всемирный банк): нехватка судов на Каспии, задержки на границах, высокие тарифы, нет единой координации коридора. "
           "ОЭСР добавляет неформальные платежи и нехватку складов в Центральной Азии.",
           "Bottlenecks (World Bank): a shortage of Caspian vessels, delays at borders, high tariffs and no single corridor management. "
           "The OECD adds informal fees and a lack of warehousing in Central Asia.",
           "ew-wb-2023", "ew-oecd-2025"),
        PT("Политические риски: мирный договор Армении и Азербайджана на весну 2026 г. не подписан, начало строительства TRIPP перенесено, "
           "продолжение войны вокруг Ирана может сделать маршрут опасным, полного финансирования нет.",
           "Political risks: the Armenia–Azerbaijan peace treaty had not been signed as of spring 2026, the start of TRIPP construction has been postponed, "
           "a continued war around Iran could make the route dangerous, and full financing is not in place.",
           "carnegie-2026", "eurasianet-2026-09"),
    ]),
    OD(id="summary", title=T("Итог по источникам", "Bottom line from the sources"), points=[
        PT("Объёмы пока далеки от прогнозов, а судьба ключевых участков зависит от политических решений — мирного договора, TRIPP, санкций, ситуации вокруг Ирана — "
           "не меньше, чем от инфраструктуры.",
           "Volumes are still far from forecasts, and the fate of key sections depends on political decisions — the peace treaty, TRIPP, sanctions, the situation around Iran — "
           "as much as on infrastructure.",
           "ew-wb-2023", "astanatimes-2026", "carnegie-2026"),
    ]),
]

ACTORS = [
    # ---- страны маршрутов
    ACTOR("KAZ", "route", "Казахстан", "Kazakhstan",
          econ=[PT("Грузы между Китаем и Каспийским морем идут через Казахстан; порты Актау и Курык — точка перехода на суда через Каспий к портам Азербайджана.",
                   "Cargo between China and the Caspian Sea crosses Kazakhstan; the ports of Aktau and Kuryk are where it moves onto vessels across the Caspian to Azerbaijan.",
                   "ew-wb-2023", "astanatimes-2026", "ew-timesca-2024-uzb"),
                PT("В Актау построен контейнерный хаб вместе с китайским портом Ляньюньган. Для Казахстана ставка — не только доходы от транзита, но и логистика и производство.",
                   "A container hub has been built at Aktau together with China's Lianyungang port. For Kazakhstan the stakes go beyond transit revenue to logistics and manufacturing.",
                   "astanatimes-2026", "ew-scmp-2026")],
          pol=[PT("После 2022 г. санкции осложнили северный путь через Россию, и интерес к сухопутной связи с Европой через Каспий вырос.",
                  "After 2022, sanctions complicated the northern route through Russia and interest in an overland link to Europe across the Caspian grew.",
                  "ew-oecd-2023", "ew-scmp-2026", "ew-bri-2023")],
          risks=[PT("Пропускная способность ограничена: Министерство транспорта Казахстана оценивает её примерно в 6 млн т в год; Всемирный банк называет узкими местами "
                    "нехватку судов на Каспии, задержки на границах и высокие тарифы.",
                    "Capacity is limited: Kazakhstan's Ministry of Transport puts it at about 6 million t a year; the World Bank names a shortage of Caspian vessels, "
                    "border delays and high tariffs as bottlenecks.", "astanatimes-2026", "ew-wb-2023"),
                 PT("Маршрут зависит от слаженной работы всех стран цепочки: Всемирный банк считает главной проблемой отсутствие единого управления коридором; задержка в одной точке сказывается на всём пути.",
                    "The route depends on all countries along the chain working together: the World Bank sees the lack of single corridor management as the main problem; a delay at one point affects the whole route.",
                    "ew-wb-2023", "astanatimes-2026")]),
    ACTOR("UZB", "route", "Узбекистан", "Uzbekistan",
          econ=[PT("По оценке Всемирного банка, транзит через Каспий в основном обслуживает торговлю Центральной Азии — прежде всего Узбекистана — с Европой.",
                   "According to the World Bank, transit across the Caspian mainly serves trade between Central Asia — above all Uzbekistan — and Europe.", "ew-wb-2023"),
                PT("Узбекистан договаривается с Азербайджаном о выходе к Каспию и рынкам Европы: по железной дороге через Туркменистан к порту Туркменбаши или через Казахстан "
                   "к Актау и Курыку, затем через порт Алят. Соглашения предусматривают цифровые таможенные процедуры.",
                   "Uzbekistan is negotiating with Azerbaijan for access to the Caspian and European markets: by rail via Turkmenistan to the port of Turkmenbashi or via Kazakhstan "
                   "to Aktau and Kuryk, then through the port of Alyat. The agreements provide for digital customs procedures.", "ew-timesca-2024-uzb"),
                PT("Страны Центральной Азии, по оценке ОЭСР, заметно продвинулись в цифровизации таможенных процедур и пограничного контроля.",
                   "According to the OECD, Central Asian countries have made significant progress in digitalising customs procedures and border controls.", "ew-oecd-2025")],
          pol=[PT("Узбекистан участвует в управлении коридором: генеральный секретарь TRACECA в 2026 г. — заместитель министра транспорта Узбекистана Жасурбек Чориев.",
                  "Uzbekistan takes part in running the corridor: in 2026 the TRACECA Secretary General is Uzbekistan's deputy transport minister, Jasurbek Choriev.",
                  "ew-intellinews-tkm")],
          risks=[PT("Грузы Узбекистана идут к морю через территорию соседей; на пути через Туркменистан перевозчикам трудно получать визы и разрешения — вице-премьер Узбекистана назвал это существенным барьером.",
                    "Uzbek cargo reaches the sea through neighbouring countries; carriers crossing Turkmenistan struggle to obtain visas and permits, which Uzbekistan's deputy prime minister called a significant barrier.",
                    "ew-intellinews-tkm", "ew-timesca-2024-uzb"),
                 PT("Общие ограничения для Центральной Азии (ОЭСР): неформальные платежи, нехватка складских мощностей, мало частных инвестиций.",
                    "Common constraints in Central Asia (OECD): informal fees, warehousing bottlenecks and limited private investment.", "ew-oecd-2025")],
          confidence="low"),
    ACTOR("TKM", "route", "Туркменистан", "Turkmenistan",
          econ=[PT("Порт Туркменбаши (открыт в мае 2018 г.) — альтернатива казахстанским портам для перевозок через Каспий в Азербайджан; в 2025 г. он обработал 7,3 млн т грузов.",
                   "The port of Turkmenbashi (opened in May 2018) is an alternative to Kazakhstan's ports for shipments across the Caspian to Azerbaijan; it handled 7.3 million t in 2025.",
                   "ew-intellinews-tkm", "ew-timesca-2024-uzb")],
          pol=[PT("Туркменистан входит в число стран Центральной Азии, с которыми ЕС в 2024 г. согласовал развитие Транскаспийского коридора.",
                  "Turkmenistan is among the Central Asian countries with which the EU agreed in 2024 to develop the Trans-Caspian corridor.", "ew-ec-2024"),
               PT("По оценке генсекретаря TRACECA, если Туркменистан решит проблемы порта, он сможет сильнее конкурировать с Казахстаном за транскаспийские грузы.",
                  "According to the TRACECA Secretary General, if Turkmenistan solves the port's problems it could compete more strongly with Kazakhstan for trans-Caspian cargo.",
                  "ew-intellinews-tkm")],
          risks=[PT("Порт загружен примерно на 25–30%: перевозчикам трудно получить визы и разрешения.",
                    "The port runs at about 25–30% of capacity: carriers find it hard to obtain visas and permits.", "ew-intellinews-tkm")],
          confidence="low"),
    ACTOR("AZE", "route", "Азербайджан", "Azerbaijan",
          econ=[PT("Порт Баку в Аляте принимает грузы с Каспия; дальше они идут по железной дороге в Грузию и Турцию — линия Баку – Тбилиси – Карс открыта 30 октября 2017 г.",
                   "The Port of Baku at Alyat receives cargo from across the Caspian; it then moves by rail to Georgia and Türkiye — the Baku–Tbilisi–Kars line opened on 30 October 2017.",
                   "ew-wb-2023", "ew-timesca-2024-uzb", "ew-mfa-tr")],
          pol=[PT("Маршрут через Армению (TRIPP) восстанавливает кратчайшую сухопутную связь основной части Азербайджана с Нахичеванью. В Азербайджане его называют "
                  "«Зангезурским коридором»; в Армении это название не используют.",
                  "The route through Armenia (TRIPP) restores the shortest overland link between mainland Azerbaijan and Nakhchivan. In Azerbaijan it is called the "
                  "\"Zangezur corridor\"; Armenians do not use this name.", "carnegie-2026", "ew-caci-2024", "ew-oc-2023"),
               PT("Параллельно Азербайджан и Иран 9 октября 2023 г. договорились о дороге и железной дороге в Нахичевань через Иран вдоль Аракса (около 55 км).",
                  "In parallel, on 9 October 2023 Azerbaijan and Iran agreed on a road and railway to Nakhchivan through Iran along the Aras (about 55 km).",
                  "ew-caci-2024", "carnegie-2026")],
          risks=[PT("Мирный договор с Арменией на весну 2026 г. был парафирован, но не подписан.",
                    "As of spring 2026 the peace treaty with Armenia had been initialled but not signed.", "carnegie-2026"),
                 PT("Начало строительства армянского участка TRIPP перенесено — не раньше 2027 г.",
                    "Construction of the Armenian section of TRIPP has been postponed until 2027 at the earliest.", "eurasianet-2026-09")]),
    ACTOR("GEO", "route", "Грузия", "Georgia",
          econ=[PT("Грузия — звено между Каспием и Чёрным морем: грузы идут по железной дороге к портам Поти и Батуми и дальше через Чёрное море (например, в Констанцу) или через Турцию.",
                   "Georgia links the Caspian and the Black Sea: cargo travels by rail to the ports of Poti and Batumi and on across the Black Sea (for example, to Constanța) or via Türkiye.",
                   "ew-wb-2023", "ew-rbj-2019"),
                PT("Транзит по Среднему коридору через Грузию вырос вдвое с 2018 по 2025 г. — до 4,6 млн т; рост 2025 г. обеспечила в основном региональная торговля, максимум — 5,0 млн т в 2022 г.",
                   "Middle Corridor transit through Georgia doubled between 2018 and 2025 to 4.6 million t; growth in 2025 came mainly from regional trade; the peak was 5.0 million t in 2022.",
                   "ew-pmc-2026")],
          pol=[PT("Глубоководный порт Анаклия: контракт с грузино-американским консорциумом расторгнут в 2020 г., в 2024 г. подряд получил китайский консорциум, "
                  "в июле 2026 г. правительство объявило о его выходе и о государственной собственности на порт. Критики считают это попыткой вернуть расположение Запада, сохранив роль в Среднем коридоре.",
                  "Anaklia deep-sea port: the contract with a Georgian–US consortium was cancelled in 2020, a Chinese consortium won the contract in 2024, and in July 2026 "
                  "the government announced its exit and state ownership of the port. Critics see this as an attempt to regain Western goodwill while keeping a Middle Corridor role.",
                  "ew-eurasianet-anaklia")],
          risks=[PT("Всемирный банк (2023) рекомендует снизить тарифы на обработку контейнеров в черноморских портах коридора — по его данным, самые высокие на Чёрном море.",
                    "The World Bank (2023) recommends cutting container handling tariffs at the corridor's Black Sea ports, which it says are the highest on the Black Sea.",
                    "ew-wb-2023")]),
    ACTOR("TUR", "route", "Турция", "Türkiye",
          econ=[PT("Турция продвигает Средний коридор как часть возрождения Шёлкового пути: через её порты азиатские грузы получают выход на Ближний Восток, в Северную Африку и Средиземноморье.",
                   "Türkiye promotes the Middle Corridor as part of reviving the Silk Road: its ports give Asian cargo access to the Middle East, North Africa and the Mediterranean.",
                   "ew-mfa-tr", "carnegie-2026"),
                PT("МИД Турции называет железную дорогу Баку – Тбилиси – Карс (открыта 30 октября 2017 г.) новой возможностью для бесперебойной торговли Китая и Европы.",
                   "Türkiye's Foreign Ministry calls the Baku–Tbilisi–Kars railway (opened 30 October 2017) a new opportunity for uninterrupted China–Europe trade.", "ew-mfa-tr")],
          pol=[PT("Турция строит двухпутную железную дорогу Карс – Дилуджу (Нахичевань), чтобы через TRIPP напрямую связать Турцию и Азербайджан.",
                  "Türkiye is building a double-track railway from Kars to Dilucu (Nakhchivan) to link Türkiye and Azerbaijan directly via TRIPP.", "carnegie-2026"),
               PT("Турция — участник TRACECA, Постоянный секретариат которой находится в Баку.",
                  "Türkiye is a member of TRACECA, whose Permanent Secretariat is in Baku.", "ew-mfa-tr", "traceca-history")],
          risks=[PT("По оценке Всемирного банка (2023), из-за неэффективности и пробелов в инфраструктуре на территории Турции операторы пока предпочитают путь через Чёрное море.",
                    "According to the World Bank (2023), inefficiencies and infrastructure gaps in Türkiye mean operators currently prefer the Black Sea route.", "ew-wb-2023")]),
    ACTOR("UKR", "route", "Украина", "Ukraine",
          econ=[PT("Паромная линия Черноморск – Батуми даёт Украине прямой выход к рынкам Кавказа и Центральной Азии; линия Ильичёвск (Черноморск) – Констанца – Батуми работала как узел TRACECA с 2014 г.",
                   "The Chornomorsk–Batumi ferry gives Ukraine direct access to markets in the Caucasus and Central Asia; the Illichivsk (Chornomorsk) – Constanța – Batumi line has served as a TRACECA hub since 2014.",
                   "ew-reuters-2024", "traceca-ferry-2014")],
          risks=[PT("Паромное сообщение остановлено после начала полномасштабного вторжения России в 2022 г. Возобновление объявлено в июне 2024 г.; первые рейсы после перерыва, "
                    "по данным «Укрзализныци», прошли 18 и 26 марта 2025 г.",
                    "Ferry services stopped after Russia's full-scale invasion in 2022. A restart was announced in June 2024; according to Ukrzaliznytsia, the first sailings after the break "
                    "took place on 18 and 26 March 2025.", "ew-reuters-2024", "ew-pravda-2025")],
          confidence="low", note=T("Политическая функция маршрута для Украины в прочитанных источниках не описана.", "The sources read do not describe the route's political role for Ukraine.")),
    ACTOR("ROU", "route", "Румыния", "Romania",
          econ=[PT("Констанца — один из крупнейших портов Европы (около 88 млн т в 2025 г.); он связывает черноморские линии с внутренними водными путями Центральной и Восточной Европы. "
                   "В апреле 2026 г. AD Ports Group (ОАЭ) договорилась изучить инвестиции в порт в рамках своей стратегии по Среднему коридору.",
                   "Constanța is one of Europe's largest ports (about 88 million t in 2025); it links Black Sea shipping with the inland waterways of Central and Eastern Europe. "
                   "In April 2026 AD Ports Group (UAE) agreed to explore investment in the port as part of its Middle Corridor strategy.", "ew-national-2026"),
                PT("Морская линия Батуми/Поти – Констанца связывает Средний коридор с Румынией; её оператор называл её «последним недостающим звеном» цепочки. "
                   "Паромы до Констанцы ходят и по линии TRACECA.",
                   "The Batumi/Poti – Constanța sea link connects the Middle Corridor with Romania; its operator called it \"the last missing link\" in the chain. "
                   "Ferries to Constanța also run on the TRACECA line.", "ew-rbj-2019", "traceca-ferry-2014")],
          confidence="low", note=T("Политическая функция и риски для Румынии в прочитанных источниках не описаны.", "The sources read do not describe the political role or risks for Romania.")),
    # ---- другие участники и внешние игроки
    ACTOR("ARM", "external", "Армения", "Armenia",
          econ=[PT("Армения рассматривает открытие границ как условие диверсификации экономики и видит себя региональным транспортным узлом (концепция «Перекрёсток мира», 2023 г.). "
                   "Границы с Турцией и Азербайджаном закрыты с 1990-х годов.",
                   "Armenia sees open borders as essential to diversifying its economy and envisions itself as a regional transport hub (the Crossroads of Peace concept, 2023). "
                   "Its borders with Türkiye and Azerbaijan have been closed since the 1990s.", "carnegie-2026", "ew-oc-2023")],
          pol=[PT("Принцип «Перекрёстка мира» — суверенитет и юрисдикция страны над проходящими через неё путями; по рамочному документу США и Армении инфраструктура TRIPP остаётся под суверенитетом Армении.",
                  "The Crossroads of Peace principle is each country's sovereignty and jurisdiction over routes through its territory; under the US–Armenia framework, TRIPP infrastructure remains under Armenian sovereignty.",
                  "ew-oc-2023", "carnegie-2026", "mfa-am-tripp")],
          risks=[PT("Реализация TRIPP — «большое испытание» для Армении (Carnegie): полное финансирование не обеспечено, инциденты безопасности легко политизируются, оппозиция может попытаться изменить курс правительства.",
                    "Implementing TRIPP is a \"big test\" for Armenia (Carnegie): full financing is not secured, security incidents are easily politicised, and the opposition may try to change the government's course.",
                    "carnegie-2026"),
                 PT("Начало строительства перенесено — не раньше 2027 г.", "The start of construction has been postponed until 2027 at the earliest.", "eurasianet-2026-09")],
          note=T("Армения — участник TRACECA; линия TRACECA на карте через её территорию не проходит. См. также карточку TRIPP.",
                 "Armenia is a TRACECA member; the TRACECA line on the map does not cross its territory. See also the TRIPP card.")),
    ACTOR("IRN", "external", "Иран", "Iran",
          econ=[PT("Иран опасается потерять роль транзитной страны между основной частью Азербайджана и Нахичеванью; альтернатива для него — согласованный 9 октября 2023 г. маршрут через Иран вдоль Аракса.",
                   "Iran fears losing its role as a transit country between mainland Azerbaijan and Nakhchivan; its alternative is the route through Iran along the Aras agreed on 9 October 2023.",
                   "carnegie-2026", "ew-caci-2024")],
          pol=[PT("В августе 2025 г. советник верховного лидера Ирана Али Акбар Велаяти заявил, что Иран заблокирует маршрут «с Россией или без»; МИД Ирана, приветствуя мирное соглашение, "
                  "призвал развивать проекты у границ Ирана без иностранного вмешательства.",
                  "In August 2025 Ali Akbar Velayati, adviser to Iran's Supreme Leader, said Iran would block the route \"with or without Russia\"; Iran's Foreign Ministry, while welcoming the peace deal, "
                  "called for projects near Iran's borders to proceed without foreign interference.", "ew-aljazeera-2025", "carnegie-2026"),
               PT("Аналитики Carnegie допускают, что Иран может смириться с железной дорогой под юрисдикцией Армении.",
                  "Carnegie analysts suggest Iran could tolerate a railway under Armenian jurisdiction.", "carnegie-2026")],
          note=T("Иран — участник TRACECA; линия TRACECA на карте через его территорию не проходит.", "Iran is a TRACECA member; the TRACECA line on the map does not cross its territory.")),
    ACTOR("CHN", "external", "Китай", "China",
          econ=[PT("Для Китая путь через Каспий — способ диверсифицировать поставки в Европу в обход России и морских «узких мест». Китайские госкомпании вложили в коридор сотни миллионов долларов, "
                   "в том числе в порты Актау и Баку.",
                   "For China, the Caspian route is a way to diversify shipments to Europe around Russia and maritime chokepoints. Chinese state firms have invested hundreds of millions of dollars in the corridor, "
                   "including in the ports of Aktau and Baku.", "ew-scmp-2026", "astanatimes-2026")],
          pol=[PT("Роль Китая выросла: в 2019 г. аналитики MERICS писали, что Китай почти не участвует в коридоре и сомневается в его жизнеспособности; в 2026 г. China Railway Container Transport "
                  "вошла в консорциум «Средний коридор», а в Актау работает хаб с портом Ляньюньган.",
                  "China's role has grown: in 2019 MERICS analysts wrote that China was largely absent from the corridor and doubted its viability; in 2026 China Railway Container Transport "
                  "joined the Middle Corridor consortium, and a hub with Lianyungang port operates at Aktau.", "ew-merics-2019", "astanatimes-2026")],
          risks=[PT("Маршрут уступает пути через Россию по ёмкости и эффективности; по прогнозу Всемирного банка, через Каспий пойдёт лишь около 1% торговли Китая и ЕС.",
                    "The route falls short of the path through Russia in capacity and efficiency; the World Bank expects only about 1% of China–EU trade to go across the Caspian.",
                    "ew-wb-2023", "ew-scmp-2026")]),
    ACTOR("EU", "external", "Европейский союз", "European Union",
          econ=[PT("В январе 2024 г. на форуме инвесторов ЕС – Центральная Азия объявлено о вложениях 10 млрд евро в транспорт Центральной Азии (гранты и гарантии Еврокомиссии, ЕИБ, ЕБРР, "
                   "страны ЕС, частный сектор). Цель — путь между Европой и Центральной Азией через Чёрное море и Кавказ за 15 дней.",
                   "In January 2024 the EU–Central Asia investors forum announced €10 billion for transport in Central Asia (European Commission grants and guarantees, the EIB, the EBRD, "
                   "EU member states and the private sector). The goal is a 15-day route between Europe and Central Asia via the Black Sea and the Caucasus.", "ew-ec-2024")],
          pol=[PT("TRACECA запущена при поддержке ЕС в 1993 г. для развития портов и сухопутной инфраструктуры и задумывалась как путь в обход России и Ирана. После 2022 г. интерес вырос: "
                  "санкции осложнили северный путь через Россию.",
                  "TRACECA was launched with EU support in 1993 to develop port and land infrastructure and was conceived as a route avoiding Russia and Iran. Interest grew after 2022, "
                  "when sanctions complicated the northern route through Russia.", "ew-wb-2023", "ew-bri-2023", "ew-oecd-2023")],
          risks=[PT("Пока это путь малой ёмкости: Всемирный банк не ожидает, что Средний коридор полностью заменит северный, а его доля в торговле ЕС и Китая останется около 1%.",
                    "For now it is a low-capacity route: the World Bank does not expect the Middle Corridor to fully replace the northern one, and its share of EU–China trade to stay around 1%.",
                    "ew-wb-2023", "ew-scmp-2026")],
          note=T("ЕС — не государство, поэтому на карте не подсвечивается.", "The EU is not a state, so it is not highlighted on the map.")),
    ACTOR("USA", "external", "США", "United States",
          econ=[PT("По рамочному документу США и Армении (январь 2026 г.) TRIPP строит компания-разработчик: 74% у США, 26% у Армении; права — на 49 лет с возможным продлением на 50 лет.",
                   "Under the US–Armenia framework (January 2026), TRIPP is built by a development company: 74% US, 26% Armenia; rights for 49 years, extendable by 50 years.",
                   "mfa-am-tripp", "eurasianet-2026-01")],
          pol=[PT("Маршрут назван в честь президента США; часть стран региона, по оценке Carnegie, приветствует участие США как способ уменьшить влияние России. Иран считает присутствие США у своей границы угрозой.",
                  "The route is named after the US president; according to Carnegie, some countries in the region welcome US involvement as a way to reduce Russian influence. Iran sees a US presence near its border as a threat.",
                  "carnegie-2026", "ew-aljazeera-2025")],
          risks=[PT("Полное финансирование TRIPP не обеспечено (Carnegie); строительство в Армении перенесено не раньше 2027 г. (Eurasianet).",
                    "Full financing for TRIPP is not secured (Carnegie); construction in Armenia has been postponed until 2027 at the earliest (Eurasianet).",
                    "carnegie-2026", "eurasianet-2026-09")]),
    ACTOR("RUS", "external", "Россия", "Russia",
          econ=[PT("Санкции против перевозок через Россию повысили интерес к пути через Каспий, но, по оценке Всемирного банка, Средний коридор не заменит северный путь полностью.",
                   "Sanctions on shipments through Russia raised interest in the Caspian route, but according to the World Bank the Middle Corridor will not fully replace the northern route.",
                   "ew-oecd-2023", "ew-wb-2023"),
                PT("Россия развивает собственный выход на юг — МТК «Север – Юг» (см. карточку маршрута); Минтранс России сообщает о росте перевозок по нему.",
                   "Russia is developing its own southern outlet, the North–South Transport Corridor (see its card); Russia's Ministry of Transport reports growing traffic on it.",
                   "erai-instc-2025", "mintrans-2026")],
          pol=[PT("По заявлению лидеров Азербайджана, Армении и России от 10 ноября 2020 г. контроль за транспортным сообщением с Нахичеванью должны были осуществлять пограничники ФСБ России. "
                  "Рамочный документ TRIPP оставляет пограничный и таможенный контроль за Арменией.",
                  "Under the 10 November 2020 statement by the leaders of Azerbaijan, Armenia and Russia, transport links to Nakhchivan were to be controlled by Russia's FSB Border Guard Service. "
                  "The TRIPP framework leaves border and customs control with Armenia.", "ew-trilateral-2020", "carnegie-2026", "mfa-am-tripp"),
               PT("Оценки в Москве расходились: вице-премьер Алексей Оверчук назвал дорогу вкладом в общий транспортный каркас Евразии, министр иностранных дел Сергей Лавров сомневался в прочности договорённостей.",
                  "Views in Moscow differed: Deputy Prime Minister Alexei Overchuk called the road a contribution to a common Eurasian transport framework, while Foreign Minister Sergei Lavrov doubted the deals would hold.",
                  "ew-oc-2025-russia")],
          risks=[PT("По оценке Carnegie, влияние России на Южном Кавказе резко ослабло.", "According to Carnegie, Russia's influence in the South Caucasus has sharply diminished.", "carnegie-2026")]),
]

ANALYSES = OD(eastwest=OD(
    id="eastwest",
    title=T("Значение маршрута", "Significance of the route"),
    scope=T("Справка общая для TRACECA и Среднего коридора: современный путь TRACECA через Каспий совпадает со Средним коридором. "
            "Тезисы автора карты проверены по источникам; оценки приписаны их авторам.",
            "This section is shared by TRACECA and the Middle Corridor: TRACECA's present-day route across the Caspian coincides with the Middle Corridor. "
            "The map author's points were checked against sources; assessments are attributed to their authors."),
    general=GENERAL, actors=ACTORS, sources=A_SRC, confidence="medium",
    review=REVIEW(
        conflicts=["Возобновление парома Черноморск – Батуми: объявлено на июль 2024 г. (Reuters), первые рейсы после перерыва — 18 и 26 марта 2025 г. (Украинская правда со ссылкой на «Укрзализныцю»)",
                   "Объём 2025 г.: 4,1 млн т по Среднему коридору (Минтранс Казахстана) или 1,867 млн т (Ассоциация ТМТМ); через Грузию — 4,6 млн т (PMC Research) — методики разные",
                   "Роль Китая: «почти не участвует» (MERICS, 2019) и «сотни миллионов долларов» вложений (SCMP, 2026) — оценки разных лет"],
        notes=["Тезисы из таблицы автора без подтверждения в прочитанных источниках не включены: «отсутствие военной гарантии» для ЕС, «затраты Турции на БТК», "
               "«нагрузка на инфраструктуру» и «конкуренция с северными маршрутами» для Грузии, «риск изоляции без ратификации» для Армении",
               "Доклады ОЭСР (2023, 2025) прочитаны только в виде описания",
               "Оценки «кто выигрывает, кто теряет» приписаны источникам; это не вывод редакции",
               "Позиции по TRIPP даны на дату источников (2025–2026 гг.) и могут меняться",
               "Справки по Туркменистану, Узбекистану, Украине и Румынии опираются в основном на один источник на тезис"]),
))


def main(path):
    out = OD(meta=OD(generated=ACC, note_ru="Схема транспортных коридоров. Линии проведены через узлы, названные в источниках; координаты приблизительные.",
                     note_en="Schematic transport corridors. Lines run through nodes named in the sources; coordinates are approximate."),
             nodes=OD((k, OD(ru=v[0], en=v[1], lon=v[2], lat=v[3], iso=v[4])) for k, v in NODES.items()),
             waypoints=OD((k, OD(lon=v[0], lat=v[1])) for k, v in WAYPOINTS.items()),
             routes=R, analyses=ANALYSES)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("маршрутов:", len(R), "узлов:", len(NODES))


if __name__ == "__main__":
    main(sys.argv[1])
