# -*- coding: utf-8 -*-
"""Общие конструкторы записей споров (формат schema/disputes.schema.json)."""
from collections import OrderedDict as OD

def make_S(acc):
    def S(id, title, author, year, type_, url, perspective, supports, verified, page=None, doi=None, note=None, lang=None):
        return OD(id=id, title=title, author=author, year=year, type=type_, url=url, doi=doi,
                  page_or_article=page if verified else None, perspective=perspective, supports=list(supports),
                  verified_fulltext=verified, accessed=acc, language=lang, note=note)
    return S

def T(ru, en): return OD(ru=ru, en=en)

def CL(actor, f, t, ru=None, en=None, src=(), kind=None):
    o = OD(actor=actor, **{"from": f, "to": t}, basis=(T(ru, en) if ru else None), source_ids=list(src))
    if kind: o["claim_type"] = kind
    return o

def EXT(state, f, t, ru, en, src): return OD(state=state, **{"from": f, "to": t}, basis=T(ru, en), source_ids=list(src))

def CT(state, f, t, control="full", ctype="state", src=()):
    return OD(state=state, **{"from": f, "to": t}, control=control, controller_type=ctype, source_ids=list(src))

def AREA(did, aid, ru, en, ctrls, claimants=None, ext=None, period=None):
    o = OD(area_id=f"{did}--{aid}", name=T(ru, en), de_facto_controller=ctrls)
    if claimants is not None: o["claimants"] = claimants
    if ext: o["external_control"] = ext
    if period: o["period"] = period
    return o

def POS(actor, ru, en, src): return OD(actor=actor, text=T(ru, en), source_ids=list(src))
def ALT(name, lang, used_by): return OD(name=name, lang=lang, used_by=list(used_by))
def GEOM(q, method, src, lic, note): return OD(quality=q, method=method, source=src, license=lic, note=note)
def E(date, kind, ru, en, *src): return OD(date=date, kind=kind, text=T(ru, en), source_ids=list(src))
def INTL(ru, en, src): return OD(text=T(ru, en), source_ids=list(src))

def REC(batch, acc, **k):
    base = OD(id=None, name=None, territory=None, alt_names=[], region=None, claimants=[], de_facto_controller=[],
              areas=[], period=None, type=None, secondary_types=[], legal_status=None, positions=[],
              international_position=None, summary=None, history=[], sources=[], geometry=None, confidence=None,
              needs_human_review=True, review=None, batch=batch, v1=True)
    base.update(k)
    base["history"] = sorted(base["history"], key=lambda e: e["date"])
    return base

def REVIEW(acc, conflicts=(), notes=()):
    return OD(status="draft", last_checked=acc, conflicts=list(conflicts), notes=list(notes))

NE = "Natural Earth 10m: Admin-0 Breakaway & Disputed Areas"
DEC = "Положение на карте не выражает позиции авторов"
