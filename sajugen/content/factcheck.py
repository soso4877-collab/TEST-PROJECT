# -*- coding: utf-8 -*-
"""사실일치 린터 — 생성 텍스트의 명리·자미 사실 토큰이 계산 객체에 존재하는지 대조.

원리(메모리 feedback-verify-no-overclaim): 사실은 엔진만 산출. 텍스트에 등장한
干支·자미 별/궁이 이 사주의 계산 집합에 없으면 = 할루시네이션 → 차단.
보수적으로 '특정 사실 토큰'만 검사(일반 한국어 산문은 오탐 없음).
"""

from __future__ import annotations

import re

_GAN = set("甲乙丙丁戊己庚辛壬癸")
_ZHI = set("子丑寅卯辰巳午未申酉戌亥")
_GANZHI_RX = re.compile(r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]")

# 한글 간지 검사(2026-06-12 신설) — 본문 간지 표기가 한글 전용으로 바뀌어
# 한자 검사만으로는 LLM 한글 간지 출력이 사각지대였다. 접미 문맥(일주·년·대운 등)
# 필수로 오탐 억제("기미가 보인다", 인명 '신유' 등 일반어 회피).
_GAN_KO = "갑을병정무기경신임계"
_ZHI_KO = "자축인묘진사오미신유술해"
_GAN_KO_OF = dict(zip("甲乙丙丁戊己庚辛壬癸", _GAN_KO))
_ZHI_KO_OF = dict(zip("子丑寅卯辰巳午未申酉戌亥", _ZHI_KO))
_GANZHI_KO_RX = re.compile(rf"[{_GAN_KO}][{_ZHI_KO}](?=\s*(일주|년|월|일|시|대운|세운|월운|운|생))")
# 간지와 동형인 일상어(빈출) — 허용 집합에 없을 때 오탐 방지(실사고 2026-06-12:
# '들어와 계신 시기'의 '계신'+'시'가 癸申 간지로 오인 → 정상 문장 차단 → consult
# 룰 폴백). 실제 간지로 쓰였다면 계산 집합에 있으므로 여기 도달하지 않는다.
_GANZHI_KO_COMMON_WORDS = {"계신", "임신", "기사", "무사", "병사", "정사", "기미"}


def _gz_ko(ganzhi_hanja: str) -> str:
    """한자 간지쌍 → 한글쌍 (己卯 → 기묘)."""
    if len(ganzhi_hanja) >= 2:
        g, z = _GAN_KO_OF.get(ganzhi_hanja[0]), _ZHI_KO_OF.get(ganzhi_hanja[1])
        if g and z:
            return g + z
    return ""


# 자미두수 14주성(한글) — 텍스트에 별 언급 시 차트 보유 별과 대조
_ZIWEI_MAJORS = {
    "자미",
    "천기",
    "태양",
    "무곡",
    "천동",
    "염정",
    "천부",
    "태음",
    "탐랑",
    "거문",
    "천상",
    "천량",
    "칠살",
    "파군",
}


def allowed_tokens(saju, extra_ganzhi: frozenset[str] = frozenset()) -> dict:
    """SajuResult → 허용 사실 토큰 집합.

    extra_ganzhi: 이 주문에서 추가 계산된 실재 간지(예: 상대방 명식, 한자) —
    content.md 규칙대로 계산 데이터 추가와 동시에만 확장한다.
    """
    m = saju.myeongni
    gz = {m.year.ganzhi, m.month.ganzhi, m.day.ganzhi, m.hour.ganzhi}
    gz |= {d.ganzhi for d in m.daewoon}
    # 세운·월운 간지(lunar-python 산출 실재값) — 본문 언급 시 허용
    gz |= {g for _, g in getattr(m, "seun", [])}
    gz |= {g for _, g in getattr(m, "worun", [])}
    gz |= set(extra_ganzhi)
    star_ko = set()
    for p in saju.ziwei.palaces:
        for s in (*p.major_stars, *p.minor_stars, *p.adjective_stars):
            star_ko.add(s.name)
    return {
        "ganzhi": gz,
        "ganzhi_ko": {k for k in (_gz_ko(g) for g in gz) if k},
        "ziwei_majors_in_chart": {s for s in star_ko if s in _ZIWEI_MAJORS},
        "all_star_ko": star_ko,
    }


def check_with_allow(text: str, allow: dict) -> list[dict]:
    """위반 목록 — 허용 토큰 dict 직접 대조. 빈 리스트면 통과.

    검수 UI의 관리자 수정 재검증처럼 saju 객체 없이 저장된 allowed_tokens
    (JSON 직렬화로 set 이 list 가 된 형태 포함)로 검사할 때 사용.
    기존 check() 는 이 함수에 위임 — 검사 로직은 단일 소스.
    """
    allow = {
        "ganzhi": set(allow.get("ganzhi", ())),
        "ganzhi_ko": set(allow.get("ganzhi_ko", ())),
        "ziwei_majors_in_chart": set(allow.get("ziwei_majors_in_chart", ())),
    }
    out: list[dict] = []

    # 1) 干支 토큰: 텍스트의 모든 간지쌍이 이 사주 허용 집합에 있어야 함
    for m in _GANZHI_RX.finditer(text):
        tok = m.group(0)
        if tok not in allow["ganzhi"]:
            out.append(
                {
                    "type": "ganzhi",
                    "token": tok,
                    "why": "이 사주의 사주팔자/대운에 없는 간지",
                    "pos": m.start(),
                }
            )

    # 1b) 한글 간지(접미 문맥 필수): '갑자년·경오일주'처럼 간지로 쓰인 것만 검사
    for m in _GANZHI_KO_RX.finditer(text):
        tok = m.group(0)
        if tok in _GANZHI_KO_COMMON_WORDS and tok not in allow["ganzhi_ko"]:
            continue  # 일상어 동형(계신·임신 등) — 간지 아님
        if tok not in allow["ganzhi_ko"]:
            out.append(
                {
                    "type": "ganzhi_ko",
                    "token": tok,
                    "why": "이 사주의 사주팔자/대운/세운에 없는 한글 간지",
                    "pos": m.start(),
                }
            )

    # 2) 자미 14주성: 텍스트에 언급된 주성은 이 명반에 실재해야 함
    chart_majors = allow["ziwei_majors_in_chart"]
    for star in _ZIWEI_MAJORS:
        if star in text and star not in chart_majors:
            out.append(
                {"type": "ziwei_star", "token": star, "why": "이 명반에 없는 자미 주성 언급"}
            )
    return out


def check(text: str, saju, extra_ganzhi: frozenset[str] = frozenset()) -> list[dict]:
    """위반 목록. 빈 리스트면 통과."""
    return check_with_allow(text, allowed_tokens(saju, extra_ganzhi))


def is_consistent(text: str, saju, extra_ganzhi: frozenset[str] = frozenset()) -> bool:
    return not check(text, saju, extra_ganzhi)
