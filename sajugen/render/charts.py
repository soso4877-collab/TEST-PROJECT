# -*- coding: utf-8 -*-
"""결정론적 인라인 SVG 차트 — 계산값에서만 생성(외부 의존 없음).

오행 분포 막대 + 대운 타임라인. 라벨은 SVG <text>(데코), 본문 해석은 HTML 텍스트(선택가능).
접근성: <svg role=img><title>.
"""

from __future__ import annotations

_ELEM_COLOR = {"木": "#3f7d52", "火": "#b5483d", "土": "#b5872f", "金": "#7c7f86", "水": "#34607d"}
_ELEM_TINT = {"木": "#eaf3ec", "火": "#f7ebe9", "土": "#f6efdd", "金": "#eef0f1", "水": "#e8f0f4"}
_GAN_ELEM = {
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
}
_ZHI_ELEM = {
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
# 자미두수 명반 12궁 고정 지반 좌표(전통 4x4: 외곽 12칸+중앙 정보블록). 한글·한자 키 모두.
_ZHI_GRID = {
    "사": (0, 0),
    "巳": (0, 0),
    "오": (0, 1),
    "午": (0, 1),
    "미": (0, 2),
    "未": (0, 2),
    "신": (0, 3),
    "申": (0, 3),
    "진": (1, 0),
    "辰": (1, 0),
    "유": (1, 3),
    "酉": (1, 3),
    "묘": (2, 0),
    "卯": (2, 0),
    "술": (2, 3),
    "戌": (2, 3),
    "인": (3, 0),
    "寅": (3, 0),
    "축": (3, 1),
    "丑": (3, 1),
    "자": (3, 2),
    "子": (3, 2),
    "해": (3, 3),
    "亥": (3, 3),
}


def _esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ohaeng_bar(elements: dict[str, int], w: int = 460, bar_h: int = 28) -> str:
    order = ["木", "火", "土", "金", "水"]
    mx = max(1, max(elements.values()))
    rows = []
    gap, lw = 16, 72  # 4px 베이스라인 정렬
    track_w = w - lw - 40
    for i, k in enumerate(order):
        v = elements.get(k, 0)
        y = i * (bar_h + gap) + 8
        bl = int(track_w * v / mx) if v else 2
        rows.append(
            # 트랙(전체 길이) 위에 값 막대 — 분포 비교가 직관적
            f'<rect x="{lw}" y="{y}" width="{track_w}" height="{bar_h}" rx="4" '
            f'fill="#fff" stroke="#e7dfc6"/>'
            f'<rect x="{lw}" y="{y}" width="{bl}" height="{bar_h}" rx="4" '
            f'fill="{_ELEM_COLOR[k]}"/>'
            f'<text x="0" y="{y + bar_h - 9}" font-size="14" '
            f'font-weight="600" fill="#22262e">{k} {v}</text>'
        )
    h = len(order) * (bar_h + gap) + 8
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
        f'aria-label="오행 분포 막대 그래프"><title>오행 분포</title>'
        f"{''.join(rows)}</svg>"
    )


def daewoon_timeline(daewoon: list, w: int = 700, h: int = 110, current_age=None) -> str:
    if not daewoon:
        return '<svg width="1" height="1"></svg>'
    n = len(daewoon)
    step = (w - 60) / max(1, n - 1) if n > 1 else 0
    cur_i = None
    if current_age is not None:
        for i, d in enumerate(daewoon):
            if d.start_age <= current_age <= d.end_age:
                cur_i = i
                break
    pts, axis_y = [], 52
    for i, d in enumerate(daewoon):
        x = 30 + i * step
        on = i == cur_i
        r = 8 if on else 5
        fill = "#b5483d" if on else "#b5872f"
        pts.append(
            f'<circle cx="{x:.0f}" cy="{axis_y}" r="{r}" fill="{fill}"/>'
            f'<text x="{x:.0f}" y="{axis_y - 14}" font-size="12" '
            f'font-weight="600" text-anchor="middle" '
            f'fill="#22262e">{_esc(d.ganzhi)}</text>'
            f'<text x="{x:.0f}" y="{axis_y + 22}" font-size="11" '
            f'text-anchor="middle" fill="#54606e">{d.start_age}세</text>'
        )
        if on:
            pts.append(
                f'<text x="{x:.0f}" y="{axis_y + 40}" font-size="11" '
                f'text-anchor="middle" fill="#b5483d">현재</text>'
            )
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
        f'aria-label="대운 타임라인(현재 위치 표시)"><title>대운 흐름</title>'
        f'<line x1="30" y1="{axis_y}" x2="{30 + (n - 1) * step:.0f}" '
        f'y2="{axis_y}" stroke="#d8cdb0" stroke-width="2"/>'
        f"{''.join(pts)}</svg>"
    )


# 십성 5축(비겁/식상/재성/관성/인성) 강약 카드 — 객체 십성 카운트만 사용.
_SS_AXIS = {
    "比肩": "비겁",
    "劫财": "비겁",
    "劫財": "비겁",
    "食神": "식상",
    "伤官": "식상",
    "傷官": "식상",
    "偏财": "재성",
    "偏財": "재성",
    "正财": "재성",
    "正財": "재성",
    "七杀": "관성",
    "七殺": "관성",
    "偏官": "관성",
    "正官": "관성",
    "偏印": "인성",
    "正印": "인성",
}
_AXIS_ORDER = ["비겁", "식상", "재성", "관성", "인성"]
_AXIS_COLOR = {
    "비겁": "#3f7d52",
    "식상": "#b5483d",
    "재성": "#b5872f",
    "관성": "#7c7f86",
    "인성": "#34607d",
}


def sipseong_card(myeongni, w: int = 700) -> str:
    """비겁·식상·재성·관성·인성 5축 분포(천간+지지 십성 카운트). 새 계산 아님."""
    m = myeongni
    cnt = {k: 0 for k in _AXIS_ORDER}
    for p in (m.year, m.month, m.day, m.hour):
        toks = [p.shishen_gan] + list(p.shishen_zhi or [])
        for t in toks:
            ax = _SS_AXIS.get(t)
            if ax:
                cnt[ax] += 1
    mxv = max(1, max(cnt.values()))
    bar_h, gap, lw = 24, 16, 64  # 4px 베이스라인 정렬
    track_w = w - lw - 60
    rows = []
    for i, ax in enumerate(_AXIS_ORDER):
        v = cnt[ax]
        y = i * (bar_h + gap) + 8
        bl = int(track_w * v / mxv) if v else 2
        rows.append(
            f'<rect x="{lw}" y="{y}" width="{track_w}" height="{bar_h}" rx="4" '
            f'fill="#fff" stroke="#e7dfc6"/>'
            f'<rect x="{lw}" y="{y}" width="{bl}" height="{bar_h}" rx="4" '
            f'fill="{_AXIS_COLOR[ax]}"/>'
            f'<text x="0" y="{y + bar_h - 7}" font-size="14" '
            f'font-weight="600" fill="#22262e">{ax} {v}</text>'
        )
    hh = len(_AXIS_ORDER) * (bar_h + gap) + 8
    return (
        f'<svg viewBox="0 0 {w} {hh}" width="100%" role="img" '
        f'aria-label="십성 5축 분포 그래프"><title>십성 구조</title>'
        f"{''.join(rows)}</svg>"
    )


def manse_table(myeongni, w: int = 720) -> str:
    """만세력 명식표 — 4주 x [천간/지지/지장간/천간십성/지지십성/십이운성/납음].

    값은 계산 객체에서만(하드코딩 0). 한자 정자 표기는 전통 만세력 관례.
    """
    m = myeongni
    pillars = [("年", m.year), ("月", m.month), ("日", m.day), ("時", m.hour)]
    rows = ["천간", "지지", "지장간", "천간십성", "지지십성", "십이운성", "납음"]
    lw, hh, rh = 90, 30, 34
    cw = (w - lw) / 4
    h = hh + rh * len(rows) + 30
    out = [
        f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" '
        f'aria-label="만세력 명식표"><title>만세력 명식표</title>'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#fffdf8"/>'
    ]
    out.append(
        f'<rect x="0" y="0" width="{lw}" height="{hh}" fill="#f6efdd" '
        f'stroke="#d8cdb0"/><text x="{lw / 2:.0f}" y="20" font-size="12" '
        f'text-anchor="middle" fill="#54606e">구분</text>'
    )
    for i, (lab, _) in enumerate(pillars):
        cx = lw + i * cw
        out.append(
            f'<rect x="{cx:.0f}" y="0" width="{cw:.0f}" height="{hh}" '
            f'fill="#f6efdd" stroke="#d8cdb0"/><text x="{cx + cw / 2:.0f}" y="20" '
            f'font-size="13" text-anchor="middle" fill="#22262e">{lab}柱</text>'
        )
    for ri, rlab in enumerate(rows):
        y = hh + ri * rh
        out.append(
            f'<rect x="0" y="{y}" width="{lw}" height="{rh}" fill="#faf5e8" '
            f'stroke="#d8cdb0"/><text x="{lw / 2:.0f}" y="{y + rh / 2 + 4:.0f}" '
            f'font-size="11" text-anchor="middle" fill="#54606e">{rlab}</text>'
        )
        for ci, (_, p) in enumerate(pillars):
            cx = lw + ci * cw
            if rlab == "천간":
                val, fill, fs = p.gan, _ELEM_TINT.get(_GAN_ELEM.get(p.gan, ""), "#fff"), 16
            elif rlab == "지지":
                val, fill, fs = p.zhi, _ELEM_TINT.get(_ZHI_ELEM.get(p.zhi, ""), "#fff"), 16
            elif rlab == "지장간":
                val, fill, fs = "·".join(p.hide_gan) or "-", "#fff", 12
            elif rlab == "천간십성":
                val, fill, fs = (p.shishen_gan or "日主"), "#fff", 12
            elif rlab == "지지십성":
                val, fill, fs = "·".join(p.shishen_zhi) or "-", "#fff", 12
            elif rlab == "십이운성":
                val, fill, fs = p.dishi, "#fff", 12
            else:
                val, fill, fs = p.nayin, "#fff", 12
            out.append(
                f'<rect x="{cx:.0f}" y="{y}" width="{cw:.0f}" height="{rh}" '
                f'fill="{fill}" stroke="#d8cdb0"/><text x="{cx + cw / 2:.0f}" '
                f'y="{y + rh / 2 + 5:.0f}" font-size="{fs}" text-anchor="middle" '
                f'fill="#22262e">{_esc(val)}</text>'
            )
    cap = f"명궁 납음 {m.ming_gong_nayin} · 신궁 납음 {m.shen_gong_nayin} · 일간 {m.day_master}"
    out.append(
        f'<text x="{w / 2:.0f}" y="{h - 9:.0f}" font-size="11" '
        f'text-anchor="middle" fill="#54606e">{_esc(cap)}</text>'
    )
    return "".join(out) + "</svg>"


def ziwei_chart(ziwei, w: int = 720) -> str:
    """자미두수 12궁 명반 — 전통 4x4 격자(외곽 12궁 + 중앙 정보블록).

    각 궁: 궁명·지지·주성(밝기·사화)·보좌성·잡성. 명궁/신궁 골드 강조.
    별 이름은 모두 Palace 객체에서만 추출(하드코딩 0).
    """
    z = ziwei
    cell = w / 4
    h = cell * 4 + 8
    out = [
        f'<svg viewBox="0 0 {w} {h:.0f}" width="100%" role="img" '
        f'aria-label="자미두수 12궁 명반"><title>자미두수 12궁 명반</title>'
        f'<rect x="0" y="0" width="{w}" height="{h:.0f}" fill="#fffdf8"/>'
    ]
    for p in z.palaces:
        rc = _ZHI_GRID.get(p.branch)
        if not rc:
            continue
        r, c = rc
        x, y = c * cell, r * cell
        if p.is_soul:
            stroke, sw, bg = "#b5872f", 3, "#f6efdd"
        elif p.is_body:
            stroke, sw, bg = "#b5872f", 2, "#fbf6ea"
        else:
            stroke, sw, bg = "#d8cdb0", 1, "#ffffff"
        out.append(
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{cell:.0f}" '
            f'height="{cell:.0f}" fill="{bg}" stroke="{stroke}" '
            f'stroke-width="{sw}"/>'
        )
        tag = " ★명궁" if p.is_soul else (" ☆신궁" if p.is_body else "")
        out.append(
            f'<text x="{x + 8:.0f}" y="{y + 18:.0f}" font-size="12" '
            f'fill="#b5872f">{_esc(p.name)}{tag}</text>'
            f'<text x="{x + cell - 8:.0f}" y="{y + 18:.0f}" font-size="12" '
            f'text-anchor="end" fill="#54606e">{_esc(p.branch)}</text>'
        )
        ty = y + 40
        for s in p.major_stars:
            br = f" {s.brightness}" if s.brightness else ""
            color = "#b5483d" if s.sihua == "화기" else "#22262e"
            sh = f" {s.sihua}" if s.sihua else ""
            out.append(
                f'<text x="{x + 8:.0f}" y="{ty:.0f}" font-size="13" '
                f'fill="{color}">{_esc(s.name)}{_esc(br)}{_esc(sh)}</text>'
            )
            ty += 19
        minr = " ".join(s.name for s in p.minor_stars[:5])
        if minr:
            out.append(
                f'<text x="{x + 8:.0f}" y="{ty:.0f}" font-size="10.5" '
                f'fill="#5b6472">{_esc(minr)}</text>'
            )
            ty += 17
        adj = " ".join(s.name for s in p.adjective_stars[:6])
        if adj:
            out.append(
                f'<text x="{x + 8:.0f}" y="{ty:.0f}" font-size="9.5" '
                f'fill="#9aa0a8">{_esc(adj)}</text>'
            )
    out.append(
        f'<rect x="{cell:.0f}" y="{cell:.0f}" width="{cell * 2:.0f}" '
        f'height="{cell * 2:.0f}" fill="#faf5e8" stroke="#d8cdb0"/>'
    )
    soul = next((p for p in z.palaces if p.is_soul), None)
    body = next((p for p in z.palaces if p.is_body), None)
    sb = f"명궁 지지 {soul.branch}" if soul else "명궁"
    bb = f"신궁 {z.body_palace}(지지 {body.branch})" if body else f"신궁 {z.body_palace}"
    info = [
        ("자미두수 명반", 15, "#b5872f"),
        (f"오행국 {z.five_elements_class}", 13, "#22262e"),
        (f"{sb} · {bb}", 12, "#5b6472"),
        (f"음력 {z.lunar_date}", 11, "#6b6f76"),
    ]
    icy = cell + cell * 0.7
    for txt, fs, col in info:
        out.append(
            f'<text x="{w / 2:.0f}" y="{icy:.0f}" font-size="{fs}" '
            f'text-anchor="middle" fill="{col}">{_esc(txt)}</text>'
        )
        icy += 30
    return "".join(out) + "</svg>"
