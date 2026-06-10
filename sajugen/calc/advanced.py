# -*- coding: utf-8 -*-
"""명리 심화 계산 — 격국·억부(신강약)·세운/월운.

원칙(메모리 feedback-verify-no-overclaim·decision-sajugen-accuracy-guard):
- 결정론만. 격국=월령 본기 십성(자평진전 기본). 억부=일간 생조 vs 극설
  점수. 세운/월운=lunar-python 출력 노출.
- 용신은 억부 1방식 '참고'만 산출(라벨). 단정·보장은 문안 계층에서 금지.
- 신살은 calc/shinsal.py(레지스트리·기둥별·공망) 로 분리(docs/12).
"""

from __future__ import annotations

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


def geukguk(month, day_master: str) -> tuple[str, str]:
    """월령 본기(정기) 십성으로 격 판정(자평진전 기본). 미판정 시 잡격."""
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
            "axis": "상담에서 확정 권장",
        }
    return {
        "label": label,
        "score": score,
        "yongshin": _ELEM_KO.get(yong_e, yong_e),
        "axis": axis,
    }


def seun_worun(yun, ref_year: int | None):
    """현재(ref_year) 대운 구간의 세운(년·간지)과 그해 월운(월·간지).

    lunar-python DaYun.getLiuNian / LiuNian.getLiuYue 출력만 노출(추정 없음).
    """
    seun: list[tuple[int, str]] = []
    worun: list[tuple[str, str]] = []
    if yun is None or not ref_year:
        return seun, worun
    try:
        dy = yun.getDaYun()
    except Exception:
        return seun, worun
    cur = None
    for d in dy:
        try:
            if d.getStartYear() <= ref_year <= d.getEndYear():
                cur = d
                break
        except Exception:
            continue
    if cur is None:
        return seun, worun
    try:
        ln = cur.getLiuNian()
    except Exception:
        return seun, worun
    y_obj = None
    for x in ln:
        try:
            yy = x.getYear()
        except Exception:
            continue
        if ref_year - 1 <= yy <= ref_year + 3:
            seun.append((yy, x.getGanZhi()))
        if yy == ref_year:
            y_obj = x
    if y_obj is not None:
        try:
            for m in y_obj.getLiuYue():
                worun.append((m.getMonthInChinese(), m.getGanZhi()))
        except Exception:
            pass
    return seun, worun
