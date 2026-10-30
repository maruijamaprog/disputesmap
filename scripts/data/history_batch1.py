# -*- coding: utf-8 -*-
"""
История (хронология событий) для 10 споров партии 1.
Каждое событие опирается только на источники, уже проверенные в записи (source_ids).
kind: background — предыстория; event — событие; control — смена фактического контроля; legal — правовой акт или решение.
Запуск: python scripts/data/history_batch1.py data/disputes.json
"""
import json, sys

def E(date, kind, ru, en, *src):
    return {"date": date, "kind": kind, "text": {"ru": ru, "en": en}, "source_ids": list(src)}

HISTORY = {
    "crimea": [
        E("1991", "background", "С 1991 г. Крым — часть независимой Украины.", "From 1991 Crimea is part of independent Ukraine.", "echr-crimea-2020", "unga-68-262"),
        E("2014-02-20", "event", "Дата, которую закон Украины № 685-VIII считает началом временной оккупации Крыма.", "The date that Ukrainian Law No. 685-VIII sets as the start of the temporary occupation of Crimea.", "ua-law-685-2015"),
        E("2014-02-27", "control", "С этой даты, по выводу ЕСПЧ, Россия осуществляет эффективный контроль над Крымом.", "From this date, according to the ECtHR, Russia exercises effective control over Crimea.", "echr-crimea-2020"),
        E("2014-03-16", "event", "Референдум о статусе Крыма. ГА ООН позднее признала его не имеющим силы.", "Referendum on the status of Crimea. The UN General Assembly later declared it invalid.", "unga-68-262", "loc-glm-2014"),
        E("2014-03-18", "legal", "Подписан договор о принятии Республики Крым и Севастополя в состав России.", "Treaty on the admission of the Republic of Crimea and Sevastopol into Russia signed.", "ru-treaty-2014"),
        E("2014-03-27", "legal", "Резолюция ГА ООН 68/262 «Территориальная целостность Украины».", "UN General Assembly resolution 68/262 'Territorial integrity of Ukraine'.", "unga-68-262", "loc-glm-2014"),
        E("2018-12-17", "legal", "Резолюция ГА ООН 73/194 называет положение «временной оккупацией», а Россию — «оккупирующей державой».", "UN General Assembly resolution 73/194 refers to a 'temporary occupation' and to Russia as 'the occupying Power'.", "unga-73-194"),
        E("2020-12-16", "legal", "ЕСПЧ признал жалобу Украины приемлемой и установил эффективный контроль России с 27 февраля 2014 г.", "The ECtHR declared Ukraine's application admissible and found Russian effective control from 27 February 2014.", "echr-crimea-2020"),
        E("2024-06-25", "legal", "ЕСПЧ вынес постановление по существу дела «Украина против России (Крым)».", "The ECtHR delivered its judgment on the merits in Ukraine v. Russia (re Crimea).", "dzehtsiarou-2024"),
    ],
    "kashmir": [
        E("1947-10", "control", "После раздела Британской Индии в княжество Джамму и Кашмир вторглись вооружённые отряды, махараджа согласился на присоединение к Индии; начались боевые действия Индии и Пакистана.", "After the partition of British India armed groups invaded the princely state of Jammu and Kashmir, the Maharaja agreed to accede to India, and fighting between India and Pakistan began.", "cascon-kas"),
        E("1948-04-21", "legal", "Резолюция СБ ООН 47 рекомендует определить принадлежность территории плебисцитом.", "UN Security Council resolution 47 recommends deciding the territory's status by plebiscite.", "unsc-47-1948"),
        E("1949-07-27", "control", "Карачинское соглашение устанавливает линию прекращения огня.", "The Karachi Agreement establishes the ceasefire line.", "karachi-1949"),
        E("1963", "control", "По соглашению КНР и Пакистана долина Шаксгам переходит под управление КНР; Индия соглашение не признаёт.", "Under a China–Pakistan agreement the Shaksgam Valley comes under Chinese administration; India does not recognise the agreement.", "arpi-2024", "in-mea-2024"),
        E("1972-07-02", "legal", "Симлское соглашение: стороны обязуются уважать линию контроля без ущерба для своих позиций.", "Simla Agreement: the parties undertake to respect the Line of Control without prejudice to their positions.", "simla-1972"),
        E("1984-04-13", "control", "Индия устанавливает контроль над ледником Сиачен.", "India takes control of the Siachen Glacier.", "orf-siachen-2024"),
        E("2019-10", "event", "Индия преобразует штат Джамму и Кашмир в союзные территории Джамму и Кашмир и Ладакх; КНР заявляет протест.", "India reorganises the state of Jammu and Kashmir into the union territories of Jammu and Kashmir and Ladakh; China protests.", "cn-mfa-2019", "in-mea-2024"),
    ],
    "south-china-sea": [
        E("1932", "background", "1932–1933 гг.: Франция (Французский Индокитай) заявляет права на Парасельские острова и объявляет о занятии островов Спратли; Китай направляет протесты, их объём источники оценивают по-разному.", "1932–1933: France (French Indochina) asserts rights to the Paracels and announces the occupation of the Spratlys; China protests, though sources differ on the scope of the protests.", "vn-research-2012", "cn-whitepaper-2016", "behrendt-2020"),
        E("1974-01", "control", "После столкновения с Республикой Вьетнам КНР устанавливает контроль над всеми Парасельскими островами.", "After a clash with the Republic of Vietnam, the PRC takes control of all the Paracel Islands.", "behrendt-2020", "tonnesson-2022"),
        E("2012-06", "control", "После противостояния у рифа Скарборо контроль над рифом переходит к КНР.", "After a standoff at Scarborough Shoal, control of the shoal passes to the PRC.", "amti-2017-scarborough", "wong-2024-nbr"),
        E("2013-01-22", "legal", "Филиппины начинают арбитражное разбирательство против КНР.", "The Philippines institutes arbitral proceedings against the PRC.", "pca-2016-pr"),
        E("2016-07-12", "legal", "Решение арбитража: у КНР нет правового основания для исторических прав в пределах «линии из девяти пунктиров»; суверенитет над островами не рассматривался.", "Arbitral award: no legal basis for Chinese historic rights within the 'nine-dash line'; sovereignty over the islands was not addressed.", "pca-2016-pr", "williams-2016-lawfare"),
        E("2016-07-12", "event", "КНР называет решение ничтожным; Законодательный юань Тайваня считает его неприемлемым.", "The PRC calls the award null and void; Taiwan's Legislative Yuan deems it unacceptable.", "cn-mfa-2016", "tw-cna-2016"),
    ],
    "northern-cyprus": [
        E("1960", "background", "Независимость Республики Кипр.", "Independence of the Republic of Cyprus.", "cy-mfa", "unsc-541-1983"),
        E("1964", "event", "На остров направлены миротворческие силы ООН (UNFICYP).", "The UN peacekeeping force (UNFICYP) is deployed on the island.", "unficyp-about"),
        E("1974-07-20", "control", "Начало военной операции Турции. Республика Кипр называет её вторжением; в Турции этот день отмечается как День мира и свободы.", "Turkey's military operation begins. The Republic of Cyprus calls it an invasion; in Turkey the day is marked as Peace and Freedom Day.", "cy-mfa", "tr-mfa-2024"),
        E("1974-08", "control", "Остров разделён линиями прекращения огня; между ними — буферная зона ООН.", "The island is divided by ceasefire lines with a UN buffer zone between them.", "unficyp-about"),
        E("1975-02-13", "event", "Киприоты-турки объявляют о создании «Федеративного турецкого государства Кипр»; СБ ООН выражает сожаление в связи с этим решением (367).", "Turkish Cypriots announce a 'Federated Turkish State of Cyprus'; the UN Security Council regrets the decision (resolution 367).", "unsc-367-1975"),
        E("1983-05-13", "legal", "ГА ООН (37/253) требует вывода всех оккупационных сил.", "The UN General Assembly (37/253) demands the withdrawal of all occupation forces.", "unga-37-253"),
        E("1983-11-15", "event", "Провозглашена «Турецкая Республика Северного Кипра».", "The 'Turkish Republic of Northern Cyprus' is proclaimed.", "unsc-541-1983", "trnc-pio-2023"),
        E("1983-11-18", "legal", "СБ ООН (541) признаёт провозглашение юридически недействительным.", "The UN Security Council (541) deems the declaration legally invalid.", "unsc-541-1983"),
        E("1996-12-18", "legal", "ЕСПЧ («Лоизиду против Турции»): Турция осуществляет эффективный общий контроль над северной частью острова.", "ECtHR (Loizidou v. Turkey): Turkey exercises effective overall control over the northern part of the island.", "echr-loizidou-1996"),
    ],
    "western-sahara": [
        E("1963", "legal", "ООН включает Западную Сахару (тогда Испанскую Сахару) в список несамоуправляющихся территорий.", "The UN lists Western Sahara (then Spanish Sahara) as a non-self-governing territory.", "un-nsgt"),
        E("1975-10-16", "legal", "Консультативное заключение Международного суда ООН: связей территориального суверенитета с Марокко или Мавританией не установлено.", "ICJ advisory opinion: no ties of territorial sovereignty with Morocco or Mauritania established.", "icj-ws-1975"),
        E("1975-11-14", "event", "Мадридские соглашения Испании, Марокко и Мавритании о передаче управления территорией.", "Madrid Accords between Spain, Morocco and Mauritania on transferring administration of the territory.", "icrc-ws"),
        E("1976-02-26", "control", "Испания прекращает присутствие на территории; на следующий день ПОЛИСАРИО провозглашает САДР.", "Spain ends its presence in the territory; the next day Polisario proclaims the SADR.", "un-nsgt", "icrc-ws", "sadr-proclamation"),
        E("1979-08-05", "event", "Мавритания отказывается от претензий на территорию.", "Mauritania renounces its claims to the territory.", "icrc-ws"),
        E("1991", "control", "Прекращение огня и начало работы миссии ООН (МООНРЗС); ПОЛИСАРИО контролирует районы восточнее песчаного вала.", "Ceasefire and start of the UN mission (MINURSO); Polisario controls areas east of the berm.", "icrc-ws"),
        E("2007-04", "event", "Марокко представляет в ООН инициативу об автономии Сахары под суверенитетом Королевства.", "Morocco submits to the UN its autonomy initiative for the Sahara under the Kingdom's sovereignty.", "ma-s-2007-206"),
        E("2024-10-04", "legal", "Суд ЕС: Западная Сахара — территория, «отдельная и отличная» от Марокко.", "Court of Justice of the EU: Western Sahara is 'separate and distinct' from Morocco.", "odermatt-2024"),
        E("2025-10-31", "legal", "СБ ООН (2797) называет подлинную автономию под суверенитетом Марокко наиболее осуществимым решением и продлевает мандат МООНРЗС.", "The UN Security Council (2797) calls genuine autonomy under Moroccan sovereignty the most feasible solution and extends MINURSO's mandate.", "unsc-2797-2025"),
    ],
    "falklands-malvinas": [
        E("1833", "control", "Великобритания устанавливает управление островами; Аргентина считает это узурпацией.", "Britain establishes administration of the islands; Argentina regards this as usurpation.", "ar-cancilleria", "fig-facts"),
        E("1946", "legal", "Острова включены в список несамоуправляющихся территорий ООН.", "The islands are placed on the UN list of non-self-governing territories.", "un-nsgt"),
        E("1965-12-16", "legal", "ГА ООН (2065) констатирует спор о суверенитете и призывает к переговорам.", "The UN General Assembly (2065) notes the sovereignty dispute and calls for negotiations.", "unga-2065"),
        E("1982-04-02", "control", "Аргентинские войска занимают острова.", "Argentine forces take the islands.", "fk-archives-1982", "unsc-502"),
        E("1982-04-03", "legal", "СБ ООН (502) требует вывода аргентинских войск.", "The UN Security Council (502) demands the withdrawal of Argentine forces.", "unsc-502"),
        E("1982-04-25", "control", "Британские силы возвращают контроль над Южной Георгией.", "British forces regain control of South Georgia.", "thatcher-1982"),
        E("1982-06-14", "control", "Капитуляция аргентинских сил на островах; британский контроль восстановлен.", "Argentine forces on the islands surrender; British control is restored.", "fk-archives-1982", "thatcher-1982"),
        E("1994", "legal", "Конституция Аргентины (Первая переходная статья) закрепляет претензию на острова.", "Argentina's Constitution (First Transitional Provision) enshrines the claim to the islands.", "ar-cancilleria"),
        E("2013-03", "event", "Референдум на островах: 99,8% проголосовавших — за сохранение статуса британской заморской территории.", "Referendum on the islands: 99.8% of voters back remaining a British Overseas Territory.", "uk-gov-2014", "fig-facts"),
    ],
    "alsace-lorraine": [
        E("1871-05-10", "legal", "По Франкфуртскому договору Эльзас и часть Лотарингии отходят Германии.", "Under the Treaty of Frankfurt, Alsace and part of Lorraine pass to Germany.", "versailles-51"),
        E("1918-01-08", "event", "В «14 пунктах» президент США называет отторжение 1871 г. несправедливостью, которую следует исправить.", "In the Fourteen Points the US President calls the 1871 cession a wrong that should be righted.", "wilson-1918"),
        E("1918-11-11", "control", "Перемирие; с этой даты, по Версальскому договору, территория возвращается под суверенитет Франции.", "Armistice; from this date, under the Treaty of Versailles, the territory returns to French sovereignty.", "versailles-51"),
        E("1919-06-28", "legal", "Версальский договор (ст. 51) закрепляет возвращение территории Франции.", "The Treaty of Versailles (Art. 51) confirms the return of the territory to France.", "versailles-51"),
        E("1940", "control", "Германия фактически присоединяет Эльзас и Мозель без какого-либо договора.", "Germany de facto annexes Alsace and Moselle without any treaty.", "memorial-am-1940"),
        E("1944-11", "control", "Начало освобождения Эльзаса союзными и французскими войсками.", "Allied and French forces begin liberating Alsace.", "defense-gouv-1944"),
        E("1945-02", "control", "Ликвидирован Кольмарский котёл.", "The Colmar Pocket is eliminated.", "europeremembers-colmar"),
        E("1945-03-19", "control", "Контроль Франции над территорией полностью восстановлен.", "French control over the territory is fully restored.", "defense-gouv-1944"),
    ],
    "danzig": [
        E("1919-06-28", "legal", "Версальский договор (ст. 100–108): Германия отказывается от прав на Данциг, создаётся Вольный город под защитой Лиги Наций с особыми правами Польши.", "Treaty of Versailles (Arts. 100–108): Germany renounces Danzig, which becomes a Free City under League of Nations protection with special rights for Poland.", "versailles-100-108"),
        E("1920-11-15", "control", "Провозглашён Вольный город Данциг.", "The Free City of Danzig is proclaimed.", "bundesarchiv-danzig"),
        E("1931-12-11", "legal", "Консультативное заключение Постоянной палаты международного правосудия о доступе польских военных кораблей в порт Данцига.", "Advisory opinion of the Permanent Court of International Justice on access of Polish warships to the port of Danzig.", "pcij-22-1931"),
        E("1938-10", "event", "Германия предлагает Польше согласиться на «воссоединение» Данцига с рейхом; Польша отказывается.", "Germany asks Poland to agree to the 'reunion' of Danzig with the Reich; Poland refuses.", "imt-1945-12-06"),
        E("1939-09-01", "control", "В первый день Второй мировой войны Данциг присоединён к Германии.", "On the first day of the Second World War Danzig is annexed to Germany.", "bluebook-108", "bundesarchiv-danzig"),
        E("1945-03-30", "control", "Город занят советскими войсками.", "The city is taken by Soviet forces.", "bundesarchiv-danzig"),
        E("1945-08", "legal", "Потсдамская конференция: район бывшего Вольного города передаётся под администрацию Польши до мирного урегулирования.", "Potsdam Conference: the former Free City area is placed under Polish administration pending a peace settlement.", "potsdam-proposal-1945"),
    ],
    "iraq-kuwait": [
        E("1961-06-19", "background", "Независимость Кувейта.", "Kuwait becomes independent.", "cascon-kui"),
        E("1961-06-25", "event", "Ирак объявляет Кувейт своей «неотъемлемой частью».", "Iraq declares Kuwait an 'integral part' of Iraq.", "hjil-1991", "cascon-kui"),
        E("1963-10-04", "legal", "Согласованный протокол: Ирак признаёт независимость и полный суверенитет Кувейта.", "Agreed Minutes: Iraq recognises Kuwait's independence and full sovereignty.", "unts-7063"),
        E("1990-08-02", "control", "Иракские войска вторгаются в Кувейт.", "Iraqi forces invade Kuwait.", "hjil-1991", "unsc-674"),
        E("1990-08-08", "event", "Ирак объявляет о «полном союзе» с Кувейтом, то есть о его присоединении.", "Iraq announces a 'comprehensive merger' with Kuwait, i.e. its annexation.", "hjil-1991"),
        E("1990-08-09", "legal", "СБ ООН (662): аннексия не имеет юридической силы и ничтожна.", "UN Security Council (662): the annexation has no legal validity and is null and void.", "unsc-662"),
        E("1991-02-26", "control", "Освобождение Кувейта; в Кувейте этот день отмечают как День освобождения.", "Liberation of Kuwait, marked in Kuwait as Liberation Day.", "kuwait-times-2026"),
        E("1993-05-27", "legal", "СБ ООН (833): решения комиссии ООН по демаркации границы окончательны.", "UN Security Council (833): the UN boundary demarcation commission's decisions are final.", "unsc-833"),
        E("1994-11-10", "legal", "Ирак официально признаёт суверенитет, территориальную целостность и границы Кувейта.", "Iraq formally recognises Kuwait's sovereignty, territorial integrity and borders.", "deseret-1994", "un-prst-1994-68"),
    ],
    "nagorno-karabakh": [
        E("1988-02-20", "event", "Областной совет НКАО просит о передаче области из Азербайджанской ССР в Армянскую ССР.", "The Nagorno-Karabakh regional soviet requests transfer of the region from the Azerbaijan SSR to the Armenian SSR.", "nkao-1988"),
        E("1991-09-02", "event", "Провозглашена Нагорно-Карабахская Республика.", "The Nagorno-Karabakh Republic is proclaimed.", "artsakh-mfa-2023"),
        E("1993-04-30", "legal", "СБ ООН (822) требует вывода всех оккупирующих сил из района Кельбаджара и других недавно оккупированных районов Азербайджана.", "The UN Security Council (822) demands the withdrawal of all occupying forces from the Kelbajar district and other recently occupied areas of Azerbaijan.", "unsc-822"),
        E("1994-05-12", "control", "Прекращение огня; армянские силы контролируют область и прилегающие районы.", "Ceasefire; Armenian forces control the region and surrounding districts.", "osce-2009"),
        E("2008-03-14", "legal", "ГА ООН (62/243) называет районы «оккупированными территориями Азербайджана».", "The UN General Assembly (62/243) refers to 'the occupied territories of Azerbaijan'.", "unga-62-243"),
        E("2015-06-16", "legal", "ЕСПЧ («Чирагов и др. против Армении»): Армения осуществляет эффективный контроль над Нагорным Карабахом и прилегающими территориями.", "ECtHR (Chiragov and Others v. Armenia): Armenia exercises effective control over Nagorno-Karabakh and the surrounding territories.", "echr-am-profile"),
        E("2020-11-10", "control", "Трёхстороннее заявление о прекращении огня после войны 2020 г.; прилегающие районы переходят под контроль Азербайджана.", "Trilateral ceasefire statement after the 2020 war; the surrounding districts pass to Azerbaijani control.", "az-mfa-trilateral", "trilateral-2020-bpb"),
        E("2022-10-06", "legal", "Армения и Азербайджан подтверждают взаимное признание территориальной целостности по Алма-Атинской декларации 1991 г.", "Armenia and Azerbaijan reaffirm mutual recognition of territorial integrity under the 1991 Alma-Ata Declaration.", "prague-2022"),
        E("2023-09-20", "control", "После военной операции Азербайджана прекращаются боевые действия; вся территория переходит под контроль Азербайджана.", "After Azerbaijan's military operation hostilities end; the whole territory passes to Azerbaijani control.", "nkr-decree-2023", "afp-2023-dissolve"),
        E("2023-09-28", "event", "Указ о роспуске всех учреждений НКР к 1 января 2024 г.", "Decree dissolving all NKR institutions by 1 January 2024.", "nkr-decree-2023", "afp-2023-dissolve"),
        E("2025-08-08", "legal", "В Вашингтоне парафирован мирный договор Армении и Азербайджана.", "The Armenia–Azerbaijan peace treaty is initialled in Washington.", "osw-2025"),
    ],
}


def main(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for d in data["disputes"]:
        if d["id"] not in HISTORY: continue
        ids = {s["id"] for s in d["sources"]}
        for e in HISTORY[d["id"]]:
            missing = [s for s in e["source_ids"] if s not in ids]
            if missing: raise SystemExit(f"{d['id']} {e['date']}: нет источников {missing}")
        d["history"] = sorted(HISTORY[d["id"]], key=lambda e: e["date"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("история добавлена:", ", ".join(HISTORY))


if __name__ == "__main__":
    main(sys.argv[1])
