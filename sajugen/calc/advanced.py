# -*- coding: utf-8 -*-
"""명리 심화 계산 — 격국·억부(신강약)·세운/월운.

원칙(메모리 feedback-verify-no-overclaim·decision-sajugen-accuracy-guard):
- 결정론만. 격국=월령 본기 십성(자평진전 기본). 억부=일간 생조 vs 극설
  점수. 세운/월운=lunar-python 출력 노출.
- 용신은 억부 1방식 '참고'만 산출(라벨). 단정·보장은 문안 계층에서 금지.
- 신살은 calc/shinsal.py(레지스트리·기둥별·공망) 로 분리(docs/12).
"""

from __future__ import annotations

from functools import lru_cache

from lunar_python import Lunar, Solar
from lunar_python.util import LunarUtil

_ELEM = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
    "申": "金",
    "酉": "金",
    "子": "水",
    "亥": "水",
}
# 오행 상생(생): X 가 생하는 것. 상극(극): X 가 극하는 것.
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_GEN_BY = {v: k for k, v in _SHENG.items()}  # X 를 생하는 오행(인성)
_KE_BY = {v: k for k, v in _KE.items()}  # X 를 극하는 오행(관성)

_GE_KO = {
    "比肩": "건록격(建祿格)",
    "劫财": "양인격(羊刃格)",
    "劫財": "양인격(羊刃格)",
    "食神": "식신격(食神格)",
    "伤官": "상관격(傷官格)",
    "傷官": "상관격(傷官格)",
    "偏财": "편재격(偏財格)",
    "偏財": "편재격(偏財格)",
    "正财": "정재격(正財格)",
    "正財": "정재격(正財格)",
    "七杀": "편관격(七殺格)",
    "七殺": "편관격(七殺格)",
    "偏官": "편관격(偏官格)",
    "正官": "정관격(正官格)",
    "偏印": "편인격(偏印格)",
    "正印": "정인격(正印格)",
}
_ELEM_KO = {"木": "목(木)", "火": "화(火)", "土": "토(土)", "金": "금(金)", "水": "수(水)"}


def geukguk(month) -> tuple[str, str]:
    """월령 본기(정기) 십성으로 격 판정(자평진전 기본). 미판정 시 잡격.

    격 판정은 월지 본기 십성만으로 결정되므로 day_master 는 불필요(2026-07-06 Phase 2
    dead-param 정리로 미사용 인자 제거 — 미사용이라 산출 불변, 골든 회귀로 확인)."""
    bon = month.shishen_zhi[0] if month.shishen_zhi else ""
    ge = _GE_KO.get(bon)
    if ge:
        return ge, "월지 본기(정기) 십성 기준. 투간·통근에 따라 달리 볼 여지가 있습니다."
    return "잡격(雜格)", "월령 본기로 정격이 잡히지 않아 잡격으로 봅니다."


def eokbu(pillars: dict, day_master: str) -> dict:
    """일간 기준 생조(인성·비겁) vs 극설(식상·재성·관성) 점수 → 신강/중화/신약.

    용신은 억부 원칙의 '참고' 라벨만 산출(단정 아님).
    """
    de = _ELEM.get(day_master, "")
    if not de:
        return {"label": "판정 불가", "score": 0, "yongshin": "-", "axis": "-"}
    inseong = _GEN_BY[de]  # 일간을 생하는 오행
    bigyeop = de  # 같은 오행
    siksang = _SHENG[de]  # 일간이 생하는
    jaeseong = _KE[de]  # 일간이 극하는
    gwanseong = _KE_BY[de]  # 일간을 극하는
    score = 0
    for who, p in pillars.items():
        w = 2 if who == "Month" else 1  # 월령 가중
        for ch in (p.gan, p.zhi):
            e = _ELEM.get(ch)
            if e in (inseong, bigyeop):
                score += w
            elif e in (siksang, jaeseong, gwanseong):
                score -= w
    if score >= 2:
        # 신강: 식상·재성·관성으로 설·극(대표 참고로 재성 오행)
        label, yong_e, axis = "신강", jaeseong, "설기·극(식상·재성·관성)"
    elif score <= -2:
        # 신약: 인성·비겁으로 생조(대표 참고로 인성 오행)
        label, yong_e, axis = "신약", inseong, "생조(인성·비겁)"
    else:
        return {
            "label": "중화",
            "score": score,
            "yongshin": "중화에 가까워 단정이 어려움",
            "axis": "단정 대신 참고로 제시",
        }
    return {
        "label": label,
        "score": score,
        "yongshin": _ELEM_KO.get(yong_e, yong_e),
        "axis": axis,
    }


def current_daewoon(daewoon: list, ref_year: int | None):
    """start_year가 기준 연도 이하인 마지막 대운을 단일 규칙으로 고른다."""
    if not ref_year or not daewoon:
        return None
    cur = None
    for item in daewoon:
        if item.start_year <= ref_year:
            cur = item
        else:
            break
    return cur


@lru_cache(maxsize=None)
def _seun_ganzhi(year: int) -> str:
    """起運과 무관한 연간지를 연도별 결정값으로 캐시한다."""
    return Lunar.fromYmd(year, 6, 1).getYearInGanZhiExact()


@lru_cache(maxsize=None)
def _worun_ganzhi(ref_year: int) -> tuple[tuple[str, str], ...]:
    """절기월 중앙에서 조회한 寅~丑 12월 간지를 기준 연도별로 캐시한다."""
    month_points = [(ref_year, month, 15) for month in range(2, 13)]
    month_points.append((ref_year + 1, 1, 15))
    rows = []
    for index, (year, month, day) in enumerate(month_points, start=1):
        lunar = Solar.fromYmd(year, month, day).getLunar()
        rows.append((LunarUtil.MONTH[index], lunar.getMonthInGanZhiExact()))
    return tuple(rows)


def seun_worun(yun, ref_year: int | None, daewoon: list):
    """우리 start_year로 고른 현재 대운의 세운·월운 간지를 lunar 달력에서 조회한다."""
    seun: list[tuple[int, str]] = []
    worun: list[tuple[str, str]] = []
    if yun is None or not ref_year or not daewoon:
        return seun, worun
    cur = current_daewoon(daewoon, ref_year)
    if cur is None:
        return seun, worun

    # 대운 경계에서 ref± 범위가 이웃 대운으로 새지 않게 현재 구간과 교집합만 노출한다.
    cur_index = daewoon.index(cur)
    if cur_index + 1 < len(daewoon):
        end_year = daewoon[cur_index + 1].start_year - 1
    else:
        end_year = cur.start_year + 9
    year_start = max(ref_year - 1, cur.start_year)
    year_end = min(ref_year + 3, end_year)
    if year_start > year_end:
        return seun, worun

    # 연간지는 起運과 무관한 달력값이다. 입춘에서 멀리 떨어진 음력 6월 1일로 연간지를 조회한다.
    for year in range(year_start, year_end + 1):
        seun.append((year, _seun_ganzhi(year)))

    # 월운 12개는 寅월(正月)부터 丑월(臘月)까지 각 절기월 중앙의 간지를 조회한다.
    worun.extend(_worun_ganzhi(ref_year))
    return seun, worun
