# -*- coding: utf-8 -*-
"""P2 자미두수 — iztro_py(ko-KR) 래퍼. P1 진태양시 기준 time_index로 명반 산출.

명리=흐름, 자미두수=구조(보고서 §8). 사실값은 iztro_py에서만 산출.
"""

from __future__ import annotations

import iztro_py
from pydantic import BaseModel, Field

from .. import config as _cfg
from ..input.time_correction import CorrectedTime

_SIHUA = {"祿": "화록", "權": "화권", "科": "화과", "忌": "화기"}


def _time_index(hour: int) -> int:
    """진태양시 시각 → iztro time_index(0=早子,1=丑,…,11=亥,12=晚子)."""
    if hour == 0:
        return 0
    if hour >= 23:
        return 12
    return (hour + 1) // 2


class Star(BaseModel):
    name: str  # 한글
    type: str
    brightness: str = ""
    sihua: str = ""  # 사화(화록/권/과/기) 한글


class Palace(BaseModel):
    index: int
    name: str  # 한글 궁명
    branch: str  # 한글 지지
    stem: str
    is_soul: bool
    is_body: bool
    major_stars: list[Star] = Field(default_factory=list)
    minor_stars: list[Star] = Field(default_factory=list)
    adjective_stars: list[Star] = Field(default_factory=list)


class Ziwei(BaseModel):
    solar_date: str
    lunar_date: str
    chinese_date: str  # 명리 사주팔자와 교차검증용
    five_elements_class: str  # 오행국
    soul_palace: str  # 명궁(한글)
    body_palace: str  # 신궁(한글)
    soul_star_raw: str  # 命主(원키)
    body_star_raw: str  # 身主(원키)
    palaces: list[Palace]
    decadal: str = ""  # 현재 대한(요청시각 기준)
    yearly: str = ""  # 해당 유년


def _stars(lst) -> list[Star]:
    out = []
    for s in lst:
        try:
            nm = s.translate_name()
        except Exception:
            nm = s.name
        out.append(
            Star(
                name=nm,
                type=getattr(s, "type", ""),
                brightness=s.brightness or "",
                sihua=_SIHUA.get(s.mutagen or "", ""),
            )
        )
    return out


def build(ct: CorrectedTime, *, is_male: bool, horoscope_date: str | None = None) -> Ziwei:
    ts = ct.true_solar
    zw = _cfg.ziwei()  # 유파 정책(절대규칙 6): 윤달/언어 등은 설정에서만 분기
    a = iztro_py.by_solar(
        f"{ts.year}-{ts.month:02d}-{ts.day:02d}",
        _time_index(ts.hour),
        "男" if is_male else "女",
        bool(zw.get("fix_leap", True)),
        str(zw.get("language", "ko-KR")),
    )
    sp, bp = a.get_soul_palace(), a.get_body_palace()
    palaces = []
    for p in a.palaces:
        try:
            nm = p.translate_name()
            br = p.translate_earthly_branch()
        except Exception:
            nm, br = p.name, p.earthly_branch
        palaces.append(
            Palace(
                index=p.index,
                name=nm,
                branch=br,
                stem=p.heavenly_stem,
                is_soul=(p.name == sp.name),
                is_body=bool(p.is_body_palace),
                major_stars=_stars(p.major_stars),
                minor_stars=_stars(p.minor_stars),
                adjective_stars=_stars(p.adjective_stars),
            )
        )

    decadal = yearly = ""
    if horoscope_date:
        try:
            h = a.horoscope(horoscope_date)
            hd = h.model_dump()
            decadal = str(hd.get("decadal", {}).get("heavenly_stem", "")) + str(
                hd.get("decadal", {}).get("earthly_branch", "")
            )
            yearly = str(hd.get("yearly", {}).get("heavenly_stem", "")) + str(
                hd.get("yearly", {}).get("earthly_branch", "")
            )
        except Exception:
            pass

    return Ziwei(
        solar_date=str(a.solar_date),
        lunar_date=str(a.lunar_date),
        chinese_date=str(a.chinese_date),
        five_elements_class=str(a.five_elements_class),
        soul_palace=sp.translate_name(),
        body_palace=bp.translate_name(),
        soul_star_raw=str(a.soul),
        body_star_raw=str(a.body),
        palaces=palaces,
        decadal=decadal,
        yearly=yearly,
    )
