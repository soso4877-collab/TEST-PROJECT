# -*- coding: utf-8 -*-
"""룰 골격 — 계산 결과(SajuResult)에서만 사실을 끌어와 §12-안전 문장을 생성.

이 텍스트는 LLM 없이도 항상 완결·안전(가드 실패 시 폴백 기본값).

말투 원칙(디벨롭3, 공신력 자료 기반 — NN/g Tone·서사 전이·처리유창성):
- 보고서체가 아니라 상담 화법. 읽는 분에게 말하듯 2인칭 친근 존대로 풀되,
  한국어가 자연스럽게 주어를 생략하는 자리는 생략하고 강조에서만 호명(call_name).
  '당신'은 전면 금지(운영자 지시 2026-06-12) — 이름 호명('수하님') 또는 '그대'.
- 같은 문형(템플릿 티)이 반복되지 않도록 _pick 로 연결어·맺음을
  결정론적으로 다양화(같은 입력은 항상 같은 문장 → 테스트·factcheck 재현성).
- 용어는 '라벨: 값' 나열이 아니라 문장에 녹여 간지→특성→제안 순서로.
- 단정·공포·보장 어미 금지(safe_lint). 보편·모호 단정(바넘) 금지: 모든
  진술은 계산 토큰(간지/오행/십성/별/궁)에 근거하고 미래는 열어 둔다.

심화 원칙(계산 무추가): 이미 계산돼 객체에 있는 데이터(지장간·지지십성·
4주 십이운성·납음·자미 보좌성/사화/밝기/12궁)와 단순 산술(나이)만 활용.
간지는 항상 _gz_ko 로 한자+한글 병기(factcheck 정합). 별 이름은 해당 궁
객체에 실재하는 것만.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta, timezone

from .. import modules as integrated_modules

# --- 표시 매핑 (계산 아님: lunar-python/iztro-py 한자 산출물을 한국어 표시로 치환) ---
_SHISHEN_KO = {
    "比肩": "비견",
    "劫财": "겁재",
    "劫財": "겁재",
    "食神": "식신",
    "伤官": "상관",
    "傷官": "상관",
    "偏财": "편재",
    "偏財": "편재",
    "正财": "정재",
    "正財": "정재",
    "七杀": "편관(칠살)",
    "七殺": "편관(칠살)",
    "偏官": "편관",
    "正官": "정관",
    "偏印": "편인",
    "正印": "정인",
    "日主": "일간(나 자신)",
    "": "-",
}
_GAN_KO = {
    "甲": "갑",
    "乙": "을",
    "丙": "병",
    "丁": "정",
    "戊": "무",
    "己": "기",
    "庚": "경",
    "辛": "신",
    "壬": "임",
    "癸": "계",
}
_ZHI_KO = {
    "子": "자",
    "丑": "축",
    "寅": "인",
    "卯": "묘",
    "辰": "진",
    "巳": "사",
    "午": "오",
    "未": "미",
    "申": "신",
    "酉": "유",
    "戌": "술",
    "亥": "해",
}
# 일주 동물·빛깔 표현(결정론 매핑) — "임술 = 검은 개" 식의 사람 풀이 어휘.
# 천간 오행 빛깔(갑을=푸른, 병정=붉은, 무기=누런, 경신=흰, 임계=검은) + 십이지 동물.
_GAN_COLOR = {
    "甲": "푸른",
    "乙": "푸른",
    "丙": "붉은",
    "丁": "붉은",
    "戊": "누런",
    "己": "누런",
    "庚": "흰",
    "辛": "흰",
    "壬": "검은",
    "癸": "검은",
}
_ZHI_ANIMAL = {
    "子": "쥐",
    "丑": "소",
    "寅": "호랑이",
    "卯": "토끼",
    "辰": "용",
    "巳": "뱀",
    "午": "말",
    "未": "양",
    "申": "원숭이",
    "酉": "닭",
    "戌": "개",
    "亥": "돼지",
}


def _gz_animal(ganzhi: str) -> str:
    """간지 -> '검은 개' 빛깔+동물 표현 (예: 壬戌 -> 검은 개). 미지 간지는 빈 문자열."""
    if len(ganzhi) >= 2 and ganzhi[0] in _GAN_COLOR and ganzhi[1] in _ZHI_ANIMAL:
        return f"{_GAN_COLOR[ganzhi[0]]} {_ZHI_ANIMAL[ganzhi[1]]}"
    return ""


# 복성(두 글자 성) — 호명 시 성 제외 판별용
_DOUBLE_SURNAMES = {"남궁", "황보", "제갈", "선우", "독고", "사공", "서문", "동방", "어금", "망절"}


def call_name(name: str | None) -> str:
    """내담자 호칭 — '김수하'→'수하님', '수하'→'수하님', 복성 4자→뒤 2자+님.
    미입력은 '그대'(주어 생략 우선·강조 자리만 — 이름 필수 입력이 기본 경로).
    '당신'은 운영자 지시(2026-06-12)로 전면 금지."""
    if not name or not name.strip():
        return "그대"
    n = name.strip()
    if n.endswith("님"):
        n = n[:-1]
    if len(n) == 4 and n[:2] in _DOUBLE_SURNAMES:
        return f"{n[2:]}님"
    if len(n) == 3:
        return f"{n[1:]}님"
    return f"{n}님"


_DISHI_KO = {
    "长生": "장생",
    "長生": "장생",
    "沐浴": "목욕",
    "冠带": "관대",
    "冠帶": "관대",
    "临官": "건록",
    "臨官": "건록",
    "帝旺": "제왕",
    "衰": "쇠",
    "病": "병(病)",
    "死": "사(死)",
    "墓": "묘(墓)",
    "绝": "절",
    "絕": "절",
    "胎": "태",
    "养": "양",
    "養": "양",
}
_BRIGHT_KO = {
    "庙": "묘(매우 밝음)",
    "廟": "묘(매우 밝음)",
    "旺": "왕(밝음)",
    "得": "득지",
    "利": "이로움",
    "平": "평지",
    "不": "평이",
    "陷": "함지(약함)",
    "闲": "한가",
    "閑": "한가",
}
_ELEM_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
# 자미 오행국 한글(한자 폐기). 例 土五局->토오국
_OGUK_KO = {
    "水二局": "수이국",
    "木三局": "목삼국",
    "金四局": "금사국",
    "土五局": "토오국",
    "火六局": "화육국",
}


def _oguk(s: str) -> str:
    return _OGUK_KO.get(s, s)


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
# 의미 사전 — 계산된 토큰의 '표준 의미'를 상담형으로(개인 단정 아님, 바넘 회피).
_SS_MEAN = {
    "비견": "주체성과 동료와의 협업",
    "겁재": "추진력과 경쟁 속 돌파",
    "식신": "꾸준한 표현과 안정적 생산",
    "상관": "재능과 자유로운 표현",
    "편재": "활동적인 재물 감각과 기회 포착",
    "정재": "성실한 관리와 현실 감각",
    "편관": "결단과 위기 대응",
    "편관(칠살)": "결단과 위기 대응",
    "정관": "책임과 절제, 질서",
    "편인": "독창적 사고와 통찰",
    "정인": "배움과 수용, 안정감",
    "일간(나 자신)": "자기 중심축",
}
_ELEM_MEAN = {
    "木": "성장과 확장",
    "火": "표현과 열정",
    "土": "안정과 중재",
    "金": "결단과 정리",
    "水": "지혜와 유연함",
}
_DISHI_PHASE = {
    "장생": "새로 싹트는 시작의 결",
    "목욕": "다듬어지며 시행착오를 겪는 결",
    "관대": "틀을 갖추어 가는 결",
    "건록": "제 자리를 잡아 안정되는 결",
    "제왕": "기운이 가장 무르익는 절정의 결",
    "쇠": "한 고비를 넘겨 차분해지는 결",
    "병(病)": "속도를 늦추고 살피게 되는 결",
    "사(死)": "한 흐름을 매듭짓는 결",
    "묘(墓)": "안으로 갈무리하는 결",
    "절": "비우고 다음을 준비하는 결",
    "태": "새 가능성이 맺히는 결",
    "양": "조용히 길러지는 결",
}
# 자미두수 핵심 6궁(서사 상세), 나머지 6궁은 1줄 요약
_KEY_PALACES = ["명궁", "재백궁", "관록궁", "부처궁", "복덕궁", "천이궁"]
_PALACE_ROLE = {
    "명궁": "타고난 기본 바탕과 전체 방향",
    "재백궁": "재물을 다루는 방식",
    "관록궁": "일과 성취의 결",
    "부처궁": "가까운 관계의 결",
    "복덕궁": "마음의 여유와 즐거움",
    "천이궁": "바깥 활동과 이동·대인",
}
# 12궁 전체 역할(전 궁 개별 해석용)
_PALACE_ROLE_ALL = {
    "명궁": "타고난 기본 바탕과 전체 방향",
    "형제궁": "형제·동료와의 인연과 협력",
    "부처궁": "가까운 관계와 동반의 결",
    "자녀궁": "자녀·후배·창작물과의 인연",
    "재백궁": "재물을 다루는 방식",
    "질액궁": "건강과 몸 상태를 살피는 자리",
    "천이궁": "바깥 활동과 이동·대인",
    "교우궁": "교우·협력 관계의 결",
    "관록궁": "일과 성취의 결",
    "전택궁": "거주·터전과 안정의 자리",
    "복덕궁": "마음의 여유와 즐거움",
    "부모궁": "부모·윗사람과의 인연",
}
_PALACE_ORDER = [
    "명궁",
    "재백궁",
    "관록궁",
    "천이궁",
    "부처궁",
    "복덕궁",
    "형제궁",
    "자녀궁",
    "전택궁",
    "교우궁",
    "질액궁",
    "부모궁",
]


# 신살 메타: mean(문안)·group(섹션 분류)·weight(노출 우선순위, 길흉 등급 아님).
# weight 는 섹션 상한 적용 시 정렬용 내부값일 뿐 고객 문안에 등급으로 표기 금지(§12).
_SHINSAL_META = {
    "천을귀인": {"mean": "도움을 주는 인연·귀인의 결을 읽는 단서", "group": "귀인", "weight": 9},
    "태극귀인": {"mean": "복록·반전의 결을 읽는 단서", "group": "귀인", "weight": 6},
    "문창귀인": {"mean": "학업·표현·기획 쪽 재능의 결", "group": "학문", "weight": 8},
    "학당귀인": {"mean": "학문·가르침·배움 쪽의 결", "group": "학문", "weight": 6},
    "금여": {"mean": "안정·배우자복·재물의 결을 읽는 단서", "group": "재물", "weight": 7},
    "암록": {"mean": "보이지 않는 조력·뒷배의 결", "group": "재물", "weight": 7},
    "도화살": {"mean": "매력·인기·관계의 활기를 읽는 단서", "group": "활동", "weight": 7},
    "역마살": {"mean": "이동·변화·활동성이 강조되는 결", "group": "활동", "weight": 7},
    "화개살": {"mean": "몰입·예술·학문 쪽으로 기우는 결", "group": "학문", "weight": 6},
    "천문성": {
        "mean": "철학·종교·역학·의료 등 깊이 보는 분야와의 결",
        "group": "적성",
        "weight": 4,
    },
    "고신살": {"mean": "혼자만의 거리·고독의 결을 살피는 단서", "group": "관계", "weight": 5},
    "과숙살": {"mean": "관계에서 거리·여백의 결을 살피는 단서", "group": "관계", "weight": 5},
    "양인": {"mean": "강한 추진력 — 과하지 않게 쓰는 관점", "group": "에너지", "weight": 6},
    "괴강": {"mean": "강단·결단의 기운 — 균형의 관점", "group": "에너지", "weight": 6},
    "백호": {"mean": "기운이 큰 결 — 신중함과 함께 쓰는 관점", "group": "에너지", "weight": 6},
}
# 하위호환: 기존 _SHINSAL_MEAN.get(s, ...) 호출부 유지용 파생 dict.
_SHINSAL_MEAN = {k: v["mean"] for k, v in _SHINSAL_META.items()}
# 12신살(기둥별 영역 색채) 의미 — 비단정·참고.
_TWELVE_MEAN = {
    "겁살": "갑작스런 변동을 미리 살피는 자리",
    "재살": "구설·다툼을 점검하는 자리",
    "천살": "위에서 내려오는 흐름·신념의 자리",
    "지살": "이동·독립·터전 변화의 자리",
    "연살": "인기·매력이 드러나는 자리",
    "월살": "한 박자 멈춰 가다듬는 자리",
    "망신살": "노출·드러남을 다루는 자리",
    "장성살": "중심·주도의 자리",
    "반안살": "안정·자리 잡음의 자리",
    "역마살": "이동·활동이 커지는 자리",
    "육해살": "소모를 줄이고 챙기는 자리",
    "화개살": "몰입·학문·예술의 자리",
}
_PILLAR_KO_LABEL = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
_KST = timezone(timedelta(hours=9))
_JIE_KO = {
    "立春": "입춘",
    "驚蟄": "경칩",
    "清明": "청명",
    "立夏": "입하",
    "芒種": "망종",
    "小暑": "소서",
    "立秋": "입추",
    "白露": "백로",
    "寒露": "한로",
    "立冬": "입동",
    "大雪": "대설",
    "小寒": "소한",
}
_WORUN_JIE = [
    (315, 0),
    (345, 0),
    (15, 0),
    (45, 0),
    (75, 0),
    (105, 0),
    (135, 0),
    (165, 0),
    (195, 0),
    (225, 0),
    (255, 0),
    (285, 1),
    (315, 1),
]


def _term_date(year: int, lon: int):
    """절입 UTC 시각을 고객이 읽는 양력 KST 날짜로 바꾼다. 표시 전용이며 계산 판정은 바꾸지 않는다."""
    from ..calc import solarterms

    raw = solarterms.solar_term_time(year, lon)
    return raw.replace(tzinfo=timezone.utc).astimezone(_KST).date(), solarterms.TERMS[lon]


def _worun_label(ganzhi: str, ref_year: int | None, idx: int) -> str:
    """월운 표시 규약: 간지월(절기명 - 양력 M/D~M/D). 맨몸 n월은 쓰지 않는다."""
    month_name = f"{_gz_ko(ganzhi)}월"
    if not ref_year or not 0 <= idx < 12:
        return f"{month_name}(절기 시기 확인 필요)"
    try:
        start_lon, start_off = _WORUN_JIE[idx]
        end_lon, end_off = _WORUN_JIE[idx + 1]
        start, term = _term_date(ref_year + start_off, start_lon)
        end, _ = _term_date(ref_year + end_off, end_lon)
    except Exception:
        return f"{month_name}(절기 시기 확인 필요)"
    return (
        f"{month_name}({_JIE_KO.get(term, term)} - 양력 "
        f"{start.month}/{start.day}~{end.month}/{end.day})"
    )


def _shinsal_by_weight(detail) -> list:
    """기둥별 신살 detail → (이름, weight) 내림차순 유일 이름 목록."""
    best: dict[str, int] = {}
    for h in detail:
        w = _SHINSAL_META.get(h.name, {}).get("weight", 0)
        best[h.name] = max(best.get(h.name, 0), w)
    return [n for n, _ in sorted(best.items(), key=lambda x: (-x[1], x[0]))]


def _shinsal_per_pillar(detail) -> str:
    """'시주: 천을귀인·태극귀인 / 일주: …' 형식 기둥별 요약."""
    by_pillar: dict[str, list[str]] = {"year": [], "month": [], "day": [], "hour": []}
    for h in detail:
        if h.name not in by_pillar[h.pillar]:
            by_pillar[h.pillar].append(h.name)
    parts = [
        f"{_PILLAR_KO_LABEL[p]}: {'·'.join(by_pillar[p])}"
        for p in ("hour", "day", "month", "year")
        if by_pillar[p]
    ]
    return " / ".join(parts)


def _pick(seed: str, options: list[str]) -> str:
    """seed로 결정론적 선택 — 같은 입력은 항상 같은 표현.

    문형 반복(템플릿 티)을 깨기 위한 표현 다양화. 결정론적이라
    테스트·factcheck 재현성에 영향 없음.
    """
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
    return options[h % len(options)]


def _top_elem(elems: dict[str, int]) -> tuple[str, str]:
    mx = max(elems, key=elems.get)
    mn = min(elems, key=elems.get)
    return mx, mn


def _soul_palace(z):
    return next((p for p in z.palaces if p.is_soul), z.palaces[0])


def _body_palace(z):
    return next((p for p in z.palaces if p.is_body), z.palaces[0])


def _palace(z, name):
    return next((p for p in z.palaces if p.name == name), None)


def _stars_ko(p, n=3):
    names = [s.name for s in p.major_stars][:n]
    return ", ".join(names) if names else "주성 없음(공궁)"


def _gz_ko(ganzhi: str) -> str:
    """干支 -> 한글 reading('庚午'->'경오'). 한자 병기 폐기(AI/기술티 제거, 금강산식 한글 간지).
    실재 사주팔자/대운/세운/월운 간지에만 사용. 한자는 본문에 노출하지 않는다."""
    if len(ganzhi) >= 2 and ganzhi[0] in _GAN_KO and ganzhi[1] in _ZHI_KO:
        return f"{_GAN_KO[ganzhi[0]]}{_ZHI_KO[ganzhi[1]]}"
    return ganzhi


def _gz_elem(ganzhi: str) -> str:
    """간지 천간의 오행을 한글(목·화·토·금·수)로. 새 계산 아님(고정 대응)."""
    if ganzhi and ganzhi[0] in _GAN_ELEM:
        return _ELEM_KO[_GAN_ELEM[ganzhi[0]]]
    return "-"


def _hidegan_ko(hide) -> str:
    # 한글 reading 만(한자 병기·가운뎃점 폐기). 예: '신, 경, 무'
    return ", ".join(_GAN_KO.get(g, g) for g in hide) if hide else "-"


def _ss(x: str) -> str:
    return _SHISHEN_KO.get(x, x or "-")


def _ss_list(xs) -> str:
    return ", ".join(_ss(x) for x in xs) if xs else "-"


def _ss_mean(x: str) -> str:
    k = _ss(x)
    return _SS_MEAN.get(k, k)


def _dishi_phrase(dishi: str) -> str:
    ko = _DISHI_KO.get(dishi, dishi)
    return f"{ko}({_DISHI_PHASE.get(ko, '흐름의 한 단계')})"


def _anchor(s: str) -> str:
    """조사 선택 기준이 되는 '읽는 마지막 한글 음절'을 찾는다.

    문자열 끝에서부터: 한글이면 그 글자, 한자 천간/지지면 그 한글 독음,
    공백·괄호·따옴표·숫자·기타 한자는 건너뛰며 왼쪽으로 더 찾는다.
    한자 병기 '壬午(임오)'→'오', '수(水)'→'수', '재백궁(지지 申)'→'신'.
    """
    elem_hanja = {"金": "금", "木": "목", "水": "수", "火": "화", "土": "토"}
    for ch in reversed(s.strip()):
        if 0xAC00 <= ord(ch) <= 0xD7A3:
            return ch
        if ch in _ZHI_KO:
            return _ZHI_KO[ch]
        if ch in _GAN_KO:
            return _GAN_KO[ch]
        if ch in elem_hanja:
            return elem_hanja[ch]
    return ""


def _jong(ch: str) -> int:
    """한글 음절의 종성 코드(0=받침없음, 8=ㄹ받침). 한글 아니면 0."""
    if ch and 0xAC00 <= ord(ch) <= 0xD7A3:
        return (ord(ch) - 0xAC00) % 28
    return 0


def _josa(word: str, kind: str) -> str:
    """단어 뒤에 붙일 조사만 반환(따옴표 등이 끼어 있을 때 사용).

    kind: '은는'|'이가'|'을를'|'과와'. 받침 유무로 결정론적 선택.
    """
    pairs = {
        "은는": ("은", "는"),
        "이가": ("이", "가"),
        "을를": ("을", "를"),
        "과와": ("과", "와"),
    }
    a, b = pairs[kind]
    return a if _jong(_anchor(word)) else b


def _J(word: str, kind: str) -> str:
    """단어 + 알맞은 조사(은/는·이/가·을/를·과/와)."""
    return word + _josa(word, kind)


def _rojosa(word: str) -> str:
    """'로' 또는 '으로' — 받침 없음/ㄹ받침은 '로', 그 외는 '으로'."""
    return "로" if _jong(_anchor(word)) in (0, 8) else "으로"


def _ro(word: str) -> str:
    return word + _rojosa(word)


def _bare_label(label: str) -> str:
    """'연주(年柱)' → '연주' (괄호 한자 표기 제거, 문장 안에서 자연스럽게)."""
    return label.split("(")[0].strip()


def _pillar_line(label: str, p) -> str:
    """한 기둥을 1~2문장 상담 화법으로 — 라벨 나열이 아니라 풀어서.

    seed=label 로 연결어를 다양화해 네 기둥이 같은 문형으로 반복되지 않게.
    """
    name = _bare_label(label)
    sg, sgm = _ss(p.shishen_gan), _ss_mean(p.shishen_gan)
    lead = _pick(
        label + "L",
        [
            f"{label}에는 {_J(_gz_ko(p.ganzhi), '이가')} 자리합니다.",
            f"{label}를 보면 {_J(_gz_ko(p.ganzhi), '이가')} 놓여 있습니다.",
            f"{name}의 자리에는 {_J(_gz_ko(p.ganzhi), '이가')} 들어 있습니다.",
            f"{label}는 {_ro(_gz_ko(p.ganzhi))} 짜여 있습니다.",
        ],
    )
    inner = (
        f"속에 든 지장간은 {_hidegan_ko(p.hide_gan)}, 십이운성으로는 "
        f"{_dishi_phrase(p.dishi)}의 결입니다."
    )
    read = _pick(
        label + "R",
        [
            f"이 자리는 {sgm}({sg})의 색을 띤다고 읽어 볼 수 있습니다.",
            f"{name}에서는 {sgm}({sg})의 결이 먼저 잡힙니다.",
            f"{sg}, 곧 {sgm}의 결이 이 기둥의 무게 중심입니다.",
        ],
    )
    return f"{lead} {inner} {read}"


def _pillar_block(label: str, p) -> str:
    """한 기둥을 겉(천간)·속(지장간)으로 풀어 — 각론 심화용 상담 화법.

    같은 토큰이라도 seed 로 표현을 바꿔 love/job 등에서 반복돼도 다른 문장.
    """
    name = _bare_label(label)
    sg, sgm = _ss(p.shishen_gan), _ss_mean(p.shishen_gan)
    zhi_mean = _ss_mean(p.shishen_zhi[0]) if p.shishen_zhi else "관계의 작용"
    hg = _hidegan_ko(p.hide_gan)
    lead = _pick(
        "blk" + label + "L",
        [
            f"{label}는 {_gz_ko(p.ganzhi)}입니다.",
            f"{label}에는 {_J(_gz_ko(p.ganzhi), '이가')} 자리합니다.",
            f"{name} 쪽을 보면 {_J(_gz_ko(p.ganzhi), '이가')} 놓입니다.",
        ],
    )
    surface = _pick(
        "blk" + label + "S",
        [
            f"겉으로 먼저 드러나는 색은 {sg}, 곧 {sgm}의 결이고",
            f"바깥으로 보이는 결은 {sg}({sgm}) 쪽이며",
            f"눈에 먼저 띄는 기운은 {sg}({sgm})인데",
        ],
    )
    inside = _pick(
        "blk" + label + "I",
        [
            f"그 안쪽(지장간 {hg})에는 {zhi_mean}의 결이 받쳐 줍니다",
            f"속으로는(지장간 {hg}) {zhi_mean}의 결이 함께 깔려 있습니다",
            f"안에 든 지장간 {hg}에서는 {zhi_mean}의 결이 같이 작동합니다",
        ],
    )
    phase = (
        f"십이운성으로는 {_dishi_phrase(p.dishi)}에 해당해, {name}의 기운이 "
        f"지금 어느 단계의 결에 있는지를 함께 보여 줍니다."
    )
    return f"{lead} {surface}, {inside}. {phase}"


_DOMAIN_PALACE = {
    "연애": "부처궁",
    "직업": "관록궁",
    "재물": "재백궁",
    "건강": "질액궁",
    "활동": "천이궁",
}


def _star_one(s) -> str:
    b = _BRIGHT_KO.get(s.brightness, s.brightness or "")
    sh = f"·{s.sihua}" if getattr(s, "sihua", "") else ""
    return f"{s.name}({b}){sh}" if b else f"{s.name}{sh}"


def _stars_full(p) -> str:
    """주성(밝기·사화) + 보좌성. 객체에 실재하는 별만 — factcheck 정합."""
    if p is None:
        return "정보 없음"
    if not p.major_stars:
        out = "주성이 없는 공궁"  # 공궁 자연 표현(기존 '주성은 주성 없음(공궁)' 중복 제거)
    else:
        out = f"주성은 {', '.join(_star_one(s) for s in p.major_stars)}"
    minr = ", ".join(s.name for s in p.minor_stars)
    if minr:
        out += f", 보좌성은 {minr}"
    return out


def _palace_brief(p, role: str) -> str:
    if p is None:
        return ""
    tag = (
        "(명궁)"
        if (p.is_soul and p.name != "명궁")
        else ("(신궁)" if (p.is_body and p.name != "신궁") else "")
    )
    return f"· {p.name}{tag}(지지 {p.branch}) — {role}: {_stars_full(p)}."


def _palace_para(p, role: str, myeongni_hint: str = "") -> str:
    """한 궁을 상담 화법으로 — 같은 꼬리말이 궁마다 반복되지 않게 _pick.

    P4(2026-07-05, 운영자 실격 판정 후속): myeongni_hint(예 "일주 십성 정관의 결")를
    받으면 꼬리를 명리 참조 통합 문장으로 바꾼다 — 궁 카드가 명리 문맥과 무관하게
    자립 나열되던 단절(스택) 해소. hint 미전달 호출은 기존 seed·문형 그대로(결정론 보존).
    """
    if p is None:
        return f"{_J(role, '을를')} 보는 자리는 이 명반 구성에서는 정보가 제한적입니다."
    tag = (
        "(명궁)"
        if (p.is_soul and p.name != "명궁")
        else ("(신궁)" if (p.is_body and p.name != "신궁") else "")
    )
    pb = f"{p.name}{tag}(지지 {p.branch})"
    head = _pick(
        "pp" + p.name + role,
        [
            f"{_J(role, '은는')} 자미두수에서 {_ro(pb)} 봅니다.",
            f"{_J(pb, '은는')} {_J(role, '을를')} 비추는 자리입니다.",
            f"{_J(role, '을를')} 살필 때는 {_J(pb, '을를')} 봅니다.",
            f"여기서는 {_J(pb, '이가')} {_J(role, '을를')} 보여 주는 자리입니다.",
        ],
    )
    stars = _pick(
        "ppS" + p.name,
        [
            f"이 자리에는 {_stars_full(p)} 자리합니다.",
            f"여기에는 {_stars_full(p)} 들어 있습니다.",
            f"별로 보면 {_stars_full(p)} 놓여 있습니다.",
        ],
    )
    if myeongni_hint:
        # 통합 꼬리(별도 seed "ppT2…" — 기존 hint 미전달 출력의 결정론 불변).
        tail = _pick(
            "ppT2" + p.name + role,
            [
                f"이 자리가 비추는 방향을 앞서 본 {_J(myeongni_hint, '과와')} 겹쳐 읽으면, "
                f"두 판이 같은 자리를 가리키고 있음을 알 수 있습니다.",
                f"앞서 본 {_J(myeongni_hint, '이가')} 큰 흐름이라면, 이 자리는 그 흐름이 "
                f"생활에서 드러나는 국면을 비춥니다. 서로 다른 이야기가 아니라 같은 결을 "
                f"안과 밖에서 본 것입니다.",
                f"별의 밝기와 사화가 더하는 방향을 {_J(myeongni_hint, '과와')} 나란히 놓고 "
                f"읽으면, 이 영역에서 힘을 실을 자리가 하나로 모입니다.",
            ],
        )
    else:
        tail = _pick(
            "ppT" + p.name + role,
            [
                "별의 밝기와 사화(화록·화권·화과·화기)는 이 영역에서 기운이 "
                "드러나는 세기와 방향을 읽는 단서가 됩니다.",
                "밝기는 이 자리의 힘이 드러나는 정도를, 사화는 그 힘이 향하는 "
                "쪽을 가늠하는 단서가 됩니다.",
                "별이 밝을수록 그 결이 분명하게 드러나고, 사화는 그 흐름이 "
                "어디로 기우는지를 보는 실마리가 됩니다.",
                "어느 별이 자리했는지와 그 밝기를, 사화가 더하는 방향과 함께 "
                "읽으면 이 영역의 결이 분명해집니다.",
            ],
        )
    return f"{head} {stars} {tail}"


def _period_clean(v) -> str:
    """대한/유년 토큰이 표시 가능한 한자 간지면 한글병기, 아니면 '' (깨진 로마자 비노출)."""
    if not v:
        return ""
    if len(v) >= 2 and v[0] in _GAN_KO and v[1] in _ZHI_KO:
        return _gz_ko(v[:2])
    return ""


def _age_of(input_civil, ref_year):
    """입력 연도와 기준연도로 나이 산출(단순 산술, 새 계산 아님). 미상 시 None."""
    try:
        by = int(str(input_civil)[:4])
        return (int(ref_year) - by) if ref_year else None
    except Exception:
        return None


def _singang_phrase(singang: str, *, kind: str = "general") -> str:
    """신강약을 상담 화법 한 구절로 — kind 별로 다른 표현(반복 방지)."""
    table = {
        "general": {
            "신강": "스스로 끌고 나갈 때 힘이 실리되 속도가 과하지 않은지를 함께 살피는 관점",
            "신약": "주변의 도움과 환경을 잘 끌어다 쓸 때 힘이 실리는 관점",
            "중화": "주도와 맞춤 사이의 균형을 그때그때 조절하는 관점",
        },
        "rel": {
            "신강": "가까운 사이일수록 주도와 양보의 비중을 한 번 더 살피는 결",
            "신약": "믿고 기댈 사람을 곁에 잘 두는 것이 강점이 되는 결",
            "중화": "상황에 따라 이끌고 맞추기를 오가는 균형 감각이 특징인 결",
        },
        "work": {
            "신강": "추진을 앞세우되 협업의 속도와 맞추는 점이 과제가 되는 결",
            "신약": "함께 갈 사람·환경을 잘 고를 때 안정되는 결",
            "중화": "추진과 협업의 비중을 유연하게 바꿔 쓰는 결",
        },
        "money": {
            "신강": "강한 힘을 덜어 굴리는 쪽(식상·재성 활용)으로 균형을 잡는 결",
            "신약": "무리한 확장보다 지키고 채우며 기반을 다지는 결",
            "중화": "버는 결과 쓰는 결의 균형을 정기적으로 맞춰 가는 결",
        },
        "health": {
            "신강": "기운을 많이 쓰는 결이라 휴식과 완급 조절을 의식적으로 두는 것",
            "신약": "무리한 소모보다 회복과 보강의 박자를 챙기는 것",
            "중화": "활동과 휴식의 균형을 그때그때 살피는 것",
        },
    }
    return table.get(kind, table["general"]).get(singang, "균형을 그때그때 살피는 관점")


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(t in text for t in terms)


def _consult_context(concern_text: str | None) -> dict[str, object]:
    """고객 원문을 그대로 넣지 않고, 안전한 질문 축만 뽑아 consult 초반에 반영한다."""
    text = concern_text or ""
    if not text.strip():
        return {"topics": [], "detail": ""}

    topics: list[str] = []
    detail_parts: list[str] = []
    has_house = _has_any(text, ("집", "아파트", "매매", "부동산", "이사", "거처"))
    has_region = _has_any(
        text, ("지역", "거주지", "생활권", "생활 동선", "동네", "어디로 이사")
    )
    has_group = _has_any(text, ("로타리", "클럽", "창립", "모임", "단체", "봉사"))
    has_helper = _has_any(text, ("도와", "도움", "협조", "귀인", "조력"))
    has_contract = _has_any(text, ("계약", "매매", "대출", "가격", "손해", "명의", "잔금"))
    has_land_asset = _has_any(text, ("땅", "토지", "자산", "재산", "부동산", "땅값"))
    has_children = _has_any(text, ("자식복", "자식", "자녀", "아이"))
    has_danger = _has_any(text, ("위험", "조심", "주의", "손실", "크게 잃", "무너"))
    has_work = _has_any(text, ("이직", "직장", "직업", "창업", "사업", "일"))
    has_income = _has_any(text, ("수입", "월급", "매출", "지출", "돈이 새", "돈 관리"))

    if has_house:
        topics.append("집과 이사")
        detail_parts.append(
            "집은 마음이 끌리는 곳보다 생활 거리와 실제 버틸 힘을 먼저 보아야 합니다."
        )
    if has_region:
        topics.append("지역 비교")
        detail_parts.append(
            "지역을 고를 때는 병원과 장보기 같은 생활 거리, 마음이 안정되는 생활 박자, "
            "주변 관계의 흐름을 함께 보세요."
        )
    if has_group:
        topics.append("모임 창립" if "창립" in text else "모임과 단체 운영")
        detail_parts.append("모임은 역할을 작게 나누고 사람 사이의 속도를 맞추며 시작하는 편이 좋습니다.")
    if has_helper:
        topics.append("도움을 주겠다는 사람의 신뢰")
        detail_parts.append(
            "도움을 주겠다는 사람의 호의는 받되, 맡을 역할과 책임 범위를 직접 확인하고 "
            "관계의 거리를 분명히 두세요."
        )
    if has_contract:
        topics.append("계약과 돈의 결정")
        _contract_focus = "계약과 잔금" if "잔금" in text else "계약과 돈"
        detail_parts.append(
            f"{_contract_focus}의 결정은 마음이 급할수록 한 박자 늦추고 감당할 범위를 "
            "나누어 보세요."
        )
    if has_land_asset and "땅과 자산" not in topics:
        topics.append("땅과 자산")
        detail_parts.append(
            "땅과 자산 문제는 사주가 외부 조건을 정해 주는 영역이 아닙니다. 사주 흐름으로는 "
            "한 번에 넓히기보다 지킬 것과 움직일 것을 나누고 속도를 조절하세요."
        )
    if has_children:
        topics.append("자식복")
        detail_parts.append(
            "자식복은 자식이 잘되는지보다 서로 의지가 되는 거리와 간섭을 줄이는 방식을 함께 보아야 합니다."
        )
    if has_danger:
        topics.append("위험한 시점")
        detail_parts.append(
            "위험하게 느껴지는 때에는 큰 결정을 한꺼번에 겹치지 말고 순서를 나누어 보는 것이 핵심입니다."
        )
    if has_work and not has_group:
        topics.append("직업과 역할 변화")
        detail_parts.append(
            "이직과 일의 변화는 결론을 서두르기보다 맡고 싶은 역할과 오래 이어갈 속도를 먼저 보세요."
        )
    if has_income:
        topics.append("수입과 지출의 흐름")
        detail_parts.append(
            "수입과 지출, 돈 관리의 문제는 넓히는 속도와 지키는 속도 가운데 지금 필요한 "
            "쪽을 먼저 정하세요."
        )

    return {"topics": topics, "detail": " ".join(detail_parts)}


def _concern_snapshot_label(topics: list[str]) -> str:
    axes: list[str] = []
    for topic in topics:
        if ("집" in topic or "이사" in topic or "지역" in topic) and "집과 이동" not in axes:
            axes.append("집과 이동")
        elif ("모임" in topic or "창립" in topic) and "모임과 역할" not in axes:
            axes.append("모임과 역할")
        elif ("사람" in topic or "신뢰" in topic) and "사람의 신뢰" not in axes:
            axes.append("사람의 신뢰")
        elif ("계약" in topic or "돈" in topic) and "계약과 돈" not in axes:
            axes.append("계약과 돈")
        elif ("땅" in topic or "자산" in topic) and "땅과 자산" not in axes:
            axes.append("땅과 자산")
        elif ("자식" in topic) and "자식복" not in axes:
            axes.append("자식복")
        elif ("위험" in topic) and "위험 시점" not in axes:
            axes.append("위험 시점")
        elif ("직업" in topic or "역할" in topic) and "직업과 역할" not in axes:
            axes.append("직업과 역할")
        elif ("수입" in topic or "지출" in topic) and "수입과 지출" not in axes:
            axes.append("수입과 지출")
    return ", ".join(axes) if axes else "조건과 시기"


def _love_context_detail(concern_text: str | None) -> str:
    """연애/재회 질문의 안전한 생활 맥락만 보강한다. 원문 전체나 이름은 넣지 않는다."""
    text = concern_text or ""
    if not text.strip():
        return ""

    detail_parts: list[str] = []
    if _has_any(text, ("군대", "군 복무", "입대", "복무")):
        detail_parts.append(
            "상대가 군대에 있어 연락 폭이 좁다면, 답의 속도만으로 마음을 단정하지 말고 "
            "서로 부담이 적은 때에 짧은 대화가 이어지는지를 보세요."
        )
    if _has_any(text, ("선후배", "학교", "전공", "동기", "동문")):
        detail_parts.append(
            "학교와 전공이 같은 선후배처럼 공통된 접점은 상대를 압박하는 수단이 아니라, "
            "가벼운 대화를 자연스럽게 여는 정도로만 쓰는 편이 좋습니다."
        )
    if _has_any(text, ("겹지인", "공통 지인", "공통지인", "친구")):
        detail_parts.append(
            "겹지인은 마음을 묻는 역할이 아니라 소문이 번지지 않게 접점을 잇는 역할로만 "
            "두고, 두 사람이 직접 편하게 말할 수 있는 거리를 지키는 편이 좋습니다."
        )
    if _has_any(text, ("소개팅", "새 인연", "새로운 인연", "연애를 못", "연애 못", "만남")):
        detail_parts.append(
            "연애가 오래 비어 있었다면 새 만남에서 빠른 확답을 바라기보다, "
            "상대와 대화의 속도가 자연스럽게 맞는지를 천천히 보세요."
        )
    if _has_any(text, ("결혼", "결혼운", "혼인", "배우자", "만나는 사람")):
        detail_parts.append(
            "결혼은 단번에 확정되는 흐름으로 보지 말고, 현재 만나는 사람과 생활의 속도, "
            "역할, 가족과의 거리를 맞춰 가는 문제로 보아야 합니다."
        )
    return " ".join(detail_parts)


def _love_focus(concern_text: str | None) -> str:
    """연애 질문을 재회/새 만남/결혼 축으로 나눈다. 원문은 본문에 넣지 않는다."""

    text = concern_text or ""
    if _has_any(text, ("재회", "전남친", "전여친", "헤어진", "다시 만나")):
        return "reunion"
    if _has_any(text, ("결혼", "결혼운", "혼인", "배우자", "만나는 사람")):
        return "marriage"
    if _has_any(text, ("소개팅", "새 인연", "새로운 인연", "연애를 못", "연애 못", "만남")):
        return "new_love"
    return "relationship"


def _love_consult_intro(focus: str, near_label: str) -> str:
    if focus == "reunion":
        return (
            f"연애와 재회 질문은 마음을 오래 설명하기보다 시기와 판단 지점을 먼저 보아야 합니다. "
            f"{near_label}를 한 묶음으로 보면, 처음부터 결론을 밀어붙이기보다 상대의 반응이 "
            "실제로 살아나는지 살피는 쪽이 맞습니다. 좋은 때는 짧은 연락이 대화로 이어지고 "
            "약속이 구체화되며, 조심할 때는 답이 짧고 늦어지거나 같은 상처가 반복됩니다."
        )
    if focus == "new_love":
        return (
            f"연애가 오래 비어 있었던 질문은 위로보다 실제 만남의 문이 언제 열리는지를 먼저 보아야 합니다. "
            f"{near_label}에는 소개팅, 지인 소개, 가벼운 첫 만남처럼 부담이 작은 자리부터 확인하는 것이 좋습니다. "
            "좋은 때는 대화가 자연스럽게 이어지고 다음 약속이 잡히며, 조심할 때는 외로움 때문에 "
            "상대를 빨리 정하려는 때입니다. 서두르지 말고 첫 만남은 확인하는 자리로 두세요."
        )
    if focus == "marriage":
        return (
            f"결혼 질문은 마음만으로 결론을 내기보다 시기와 생활 조건을 함께 보아야 합니다. "
            f"{near_label}에는 결혼을 확정한다고 보기보다 현재 만나는 사람, 또는 앞으로 만날 사람과 "
            "생활의 속도와 역할, 가족과의 거리가 맞는지 살피는 쪽이 더 중요합니다. 좋은 때는 "
            "서로의 생활 박자를 맞추고, 조심할 때는 감정만 앞서 큰 약속을 잡습니다."
        )
    return (
        f"연애 질문은 감정을 길게 끌기보다 시기와 행동 기준을 먼저 보아야 합니다. "
        f"{near_label}에는 대화가 이어지는지, 만남이 자연스럽게 잡히는지, 혼자만 애쓰고 "
        "있지는 않은지를 보면 마음의 답이 대체로 드러납니다."
    )


def _build_three_pillar_all(
    saju,
    *,
    ref_year: int,
    name: str | None,
    concern_category: str | None,
    concern_text: str | None,
    closing_sign: str | None,
    work_modules: tuple[str, ...] | list[str] | None,
) -> dict[str, str]:
    """삼주 결과만으로 만드는 결정론 룰 골격.

    ``ThreePillarMyeongni``에는 의도적으로 시각 의존 필드가 없다. 이 함수는 그 좁은
    타입 표면만 소비하므로, 정오 기반 옛 ``Myeongni``를 실수로 읽어 시주·자미·용신·
    신강약·대운을 고객 문안에 섞을 수 없다.
    """

    from .unknown_time_policy import THREE_PILLAR_NOTICE

    m = saju.three_pillar
    nm_call = call_name(name)
    nm_pfx = f"{nm_call}, " if name else ""
    dm_ko = _GAN_KO.get(m.day_master, m.day_master)
    day_gz = _gz_ko(m.day.ganzhi)
    month_gz = _gz_ko(m.month.ganzhi)
    year_gz = _gz_ko(m.year.ganzhi)
    geukguk = (m.geukguk or "월령의 틀").split("(")[0]

    # calendar_flow는 계산기가 제공한 세운·월운만 쓴다. 값이 없으면 그 사실을 새로
    # 만들어 내지 않고 생활 기준 문장만 남긴다.
    seun_rows = list(getattr(m, "seun", ()) or ())
    flow_items = [
        f"{year}년 {_gz_ko(ganzhi)} 흐름"
        for year, ganzhi in seun_rows
        if int(year) >= int(ref_year)
    ][:3]
    flow_evidence = ", ".join(flow_items)
    flow_line = (
        f"계산된 해의 흐름 가운데 가까운 기준은 {flow_evidence}입니다. "
        if flow_evidence
        else "해와 달의 흐름은 계산된 달력 사실이 있는 범위에서만 살핍니다. "
    )
    # 질문 답변의 시기 축도 계산기가 실제로 준 세운 연도에만 기대게 한다. 월운은
    # 절기 경계 표기까지 함께 맞춰야 하므로 이 폴백에서 새로 풀어 쓰지 않는다.
    flow_years = [
        int(year) for year, _ganzhi in seun_rows if int(year) >= int(ref_year)
    ][:2]
    if len(flow_years) >= 2:
        timing_line = (
            f"시기는 계산된 세운의 {flow_years[0]}년과 {flow_years[1]}년을 가까운 기준으로 "
            "나누어 봅니다. 앞선 해에는 생활 조건을 정리하고, 다음 해에는 그 조건을 "
            "지키면서 움직일 범위를 넓혀 보세요. "
        )
    elif flow_years:
        timing_line = (
            f"시기는 계산된 세운의 {flow_years[0]}년을 가까운 기준으로 봅니다. "
            "생활 조건을 먼저 정리한 뒤 그 조건을 지키는 범위에서 움직이세요. "
        )
    else:
        timing_line = (
            "시기는 계산된 달력 사실이 있는 범위에서만 나누어 봅니다. "
            "확인되지 않은 연도나 달을 새로 정하지 않습니다. "
        )

    source_note = (
        "아래 내용은 확인된 연주·월주·일주와 출생 시간에 따라 달라지지 않는 사실만 "
        "사용합니다. 시간에 따라 달라지는 내용은 짐작해서 채우지 않고 뺐습니다."
    )
    identity_line = (
        f"일간 {dm_ko}은 풀이에서 자기 중심을 읽는 기준 글자이고, "
        f"{day_gz}일주는 그 기준이 생활과 관계에서 드러나는 바탕을 보여 줍니다."
    )
    month_line = (
        f"월주 {month_gz}의 월령을 중심으로 본 큰 틀은 {geukguk}입니다. "
        "이 이름은 좋고 나쁨을 가르는 판정이 아니라 어떤 역할과 환경에서 힘을 쓰는지 "
        "살피는 분류입니다."
    )

    intro = (
        f"{nm_pfx}이번 풀이는 확인할 수 있는 사실과 확인할 수 없는 사실을 먼저 나누었습니다. "
        f"출생 시간이 확인되지 않은 만큼, 이번 글은 세 기둥에서 분명히 읽을 수 있는 "
        f"내용에 집중했습니다. {source_note}\n\n"
        f"{identity_line} {month_line} 읽을 때에는 한 문장을 운명의 확정으로 받기보다, "
        "현재 선택의 속도와 우선순위를 정리하는 기준으로 써 주세요."
    )
    wonguk = (
        "이번 원국은 확인된 연주·월주·일주만 놓고 읽습니다.\n"
        f"연주는 {year_gz}, 월주는 {month_gz}, 일주는 {day_gz}입니다. "
        "연주는 뿌리와 환경, 월주는 성장 과정과 사회적 역할, 일주는 자기 중심과 가까운 "
        "생활의 바탕을 읽는 자리입니다. 천간은 겉으로 드러나는 기운을 적은 글자이고, "
        "지지는 그 기운을 받치는 바탕 글자입니다. 세 자리는 따로 떼어 길흉을 단정하지 "
        "않고 서로 어떤 방향을 보태는지 살핍니다.\n\n"
        f"{source_note} 따라서 이 장에는 확인되지 않은 세부 자리를 채워 넣지 않았습니다."
    )
    nature = (
        f"{identity_line} 이 중심 글자를 성격표처럼 고정해 읽기보다, 어떤 선택을 할 때 "
        "자기답게 힘을 쓰는지 살피는 출발점으로 보는 편이 알맞습니다.\n\n"
        f"연주 {year_gz}와 월주 {month_gz}가 보여 주는 바깥 환경의 결, 일주 {day_gz}가 "
        "보여 주는 자기 기준을 함께 놓으면, 주변의 기대를 받아들이는 일과 자기 속도를 "
        "지키는 일을 구분해 볼 수 있습니다. 무리하게 한쪽을 없애기보다 맡을 일과 내려놓을 "
        "일을 나누는 습관이 이 고정된 사실을 생활에서 쓰는 방법입니다."
    )
    frame = (
        f"{month_line} {m.geukguk_note or ''} 이 틀은 한 가지 직업을 정답으로 고르는 표가 "
        "아니라, 같은 일을 해도 어떤 역할과 방식에서 오래 버틸 수 있는지 살피는 기준입니다.\n\n"
        "출생 시간에 따라 달라지지 않는 보조 단서만 남겼습니다. 시간의 영향을 받는 힘의 강약, "
        "균형을 돕는 기운, 순위와 시작점은 이번 풀이에서 다루지 않습니다. 알 수 없는 부분을 "
        "좋은 말로 메우지 않는 것이 이번 풀이의 정확도를 지키는 방법입니다."
    )
    love = (
        f"관계에서는 {day_gz}일주가 보여 주는 자기 기준을 먼저 살핍니다. 가까운 사람에게 "
        "맞추는 일과 자기 경계를 지키는 일을 한꺼번에 해결하려 하면 마음이 쉽게 지칩니다. "
        "대화가 이어지는지, 약속이 구체적인지, 한쪽만 계속 설명하고 있지는 않은지를 차례로 "
        "보면 관계의 현재 상태를 더 분명하게 판단할 수 있습니다.\n\n"
        "좋은 관계는 감정의 크기만으로 정해지지 않습니다. 부탁과 거절, 기다림과 확인, 돌봄과 "
        "책임이 한쪽으로 굳지 않는지가 중요합니다. 관계가 흔들릴 때는 결론을 서두르기보다 "
        "지금 확인할 한 가지를 짧게 묻고, 상대의 실제 반응을 본 뒤 다음 속도를 정해 주세요."
    )
    work_job = (
        f"일의 방향은 {month_line} 직업 이름 하나를 맞히기보다, 맡을 역할과 일하는 방식을 "
        "고르는 데 이 기준을 쓰는 편이 안전합니다. 설명하고 가르치는 역할, 사람을 돌보는 "
        "역할, 물건과 흐름을 관리하는 역할 가운데 무엇을 오래 유지할 수 있는지 실제 생활의 "
        "체력과 책임 범위로 좁혀 보세요.\n\n"
        "새 일을 한꺼번에 넓히기보다 이미 해 본 일에서 반복 가능한 부분과 소모가 큰 부분을 "
        "나누는 것이 먼저입니다. 수입의 크기만 보지 말고 준비 시간, 사람을 관리하는 부담, "
        "회복에 필요한 시간을 같은 표에 놓으면 두 번째 일의 조건이 더 구체적으로 보입니다."
    )
    work_wealth = (
        f"재물은 {day_gz}일주의 자기 기준과 월령의 역할을 함께 놓고, 벌기와 지키기의 순서를 "
        "나누어 보는 영역입니다. 큰 결과를 미리 약속하기보다 고정비, 반복 지출, 변동 수입을 "
        "따로 적어 지금 조절할 수 있는 폭부터 확인하는 편이 좋습니다.\n\n"
        "경제적 자유는 특정 해에 저절로 완성되는 사건으로 단정할 수 없습니다. 대신 생활비를 "
        "지키는 일, 새 수입원을 작은 규모로 시험하는 일, 감당하기 어려운 약속을 늦추는 일을 "
        "순서대로 두면 불안을 실제 행동으로 바꿀 수 있습니다."
    )
    health = (
        f"몸과 마음의 박자는 {day_gz}일주의 고정된 바탕을 생활 습관과 연결해 살피되, 질환을 "
        "예측하거나 진단하지 않습니다. 피로가 쌓이는 상황, 쉬어도 회복되지 않는 날, 걱정이 "
        "생활을 방해하는 때를 기록하면 무엇을 줄여야 하는지 더 일찍 알아차릴 수 있습니다.\n\n"
        "해야 할 일만 일정에 넣지 말고 쉬는 시간과 정리 시간을 같은 비중으로 두세요. 걷기, "
        "가벼운 호흡 운동, 손으로 만드는 취미처럼 결과 경쟁이 적고 중간에 멈추기 쉬운 활동은 "
        "일과 돌봄에서 잠시 거리를 만드는 데 도움이 될 수 있습니다. 불편이 이어지면 명리 풀이가 "
        "아닌 의료 검진과 상담의 판단을 우선해야 합니다."
    )
    flow = (
        f"{flow_line}이 흐름은 결과를 보장하는 날짜표가 아니라, 일을 밀 때와 살필 때를 나누는 "
        "달력 기준입니다. 같은 해 안에서도 먼저 정리할 일, 작은 규모로 시험할 일, 다른 사람과 "
        "합의한 뒤 움직일 일을 구분하면 부담을 한꺼번에 떠안지 않을 수 있습니다.\n\n"
        "월 단위로 볼 때에는 한 달마다 가장 중요한 일 하나와 반드시 비워 둘 회복 시간 하나를 "
        "함께 정해 두세요. 계산된 흐름이 있더라도 생활 조건과 몸의 반응이 다르면 속도를 낮추는 "
        "판단이 우선입니다. 달력의 기운은 선택을 대신하지 않고 점검할 때를 알려 주는 보조 기준입니다."
    )
    category = concern_category or "전반"
    # known-time 폴백과 같은 결정론 축 추출기를 재사용한다. 고객 문장을 옮기지 않고
    # 승인된 생활 주제와 조언 문장만 조립하므로, 복합 고민도 PII 없이 직답 근거를 갖는다.
    consult_context = _consult_context(concern_text)
    consult_topics = list(consult_context["topics"])
    consult_detail = str(consult_context["detail"])
    if consult_topics:
        topic_text = ", ".join(consult_topics)
        focus_text = _concern_snapshot_label(consult_topics)
        consult_axis_block = (
            f"질문에 담긴 생활 조건 가운데 {topic_text}을 함께 살펴야 합니다. "
            f"{focus_text}을 한꺼번에 밀어붙이지 말고 각각 감당할 범위와 순서를 나누세요. "
            f"{consult_detail}\n\n"
        )
    else:
        consult_axis_block = ""
    consult = (
        f"{nm_pfx}신청하신 질문은 {category} 영역을 중심으로 봅니다. 결론부터 말하면, 확인되지 "
        f"않은 세부 정보로 답을 크게 만들기보다 {day_gz}일주의 자기 기준과 {geukguk}의 역할 "
        "방식을 바탕으로 선택지를 줄이는 쪽이 맞습니다.\n\n"
        f"{consult_axis_block}"
        "먼저 지금 지켜야 할 생활 조건을 적고, 그 조건을 해치지 않는 가장 작은 행동을 하나 "
        "고르세요. 사람과 함께 정할 일은 혼자 확정하지 말고, 혼자 조절할 수 있는 속도와 휴식은 "
        "남의 허락을 기다리지 않는 편이 좋습니다. 답이 필요한 때일수록 실행 뒤의 반응을 보고 "
        "다음 단계를 정하는 방식이 불안을 줄입니다. 지금 지킬 조건과 바꿀 조건을 나누고, "
        "결정 뒤의 부담을 감당할 수 있는지도 먼저 확인하세요. 결정을 내리기 전에는 지금 가진 "
        "시간과 책임을 적어 보고, 하나를 바꿨을 때 다른 조건이 무너지지 않는지 살피세요.\n\n"
        f"{timing_line}{flow_line}이 근거가 허용하는 범위 안에서 선택의 방향과 완급만 나눕니다. "
        "이 범위를 벗어나는 현실 조건은 이 풀이가 대신 결정하지 않습니다."
    )
    closing = (
        f"{nm_pfx}이번 글에서 분명히 확인한 것은 {year_gz}, {month_gz}, {day_gz} 세 자리와 그에 "
        "기초한 고정된 사실입니다. 확인되지 않은 부분을 채우지 않았기 때문에 문장이 덜 화려해 "
        "보일 수 있지만, 선택에 쓰는 기준은 오히려 분명합니다.\n\n"
        "지금 바로 바꿀 수 있는 한 가지, 조금 더 지켜볼 한 가지, 멈추어야 할 한 가지를 나누어 "
        "적어 보세요. 풀이의 역할은 결정을 대신하는 데 있지 않고, 무리한 선택을 줄이고 자기 "
        "속도를 되찾는 데 있습니다."
        + (f"\n\n{closing_sign}" if closing_sign else "")
    )
    appendix = (
        "용어 풀이\n"
        "본문에 나온 용어를 한곳에 모아 쉬운 말로 풀었습니다.\n"
        "연주: 태어난 해를 기준으로 뿌리와 환경을 읽는 자리.\n"
        "월주: 태어난 달의 절기와 월령을 기준으로 성장 과정과 사회적 역할을 읽는 자리.\n"
        "일주: 태어난 날을 기준으로 자기 중심과 가까운 생활의 바탕을 읽는 자리.\n"
        "일간: 일주의 첫 글자로, 풀이에서 자기 중심을 읽는 기준.\n"
        "격국: 월령을 중심으로 역할과 환경의 큰 틀을 분류한 이름.\n"
        "세운과 월운: 해와 달 단위로 달라지는 달력의 흐름.\n"
        "시간 영향이 없는 사실: 출생 시간이 달라도 내용이 바뀌지 않아 남긴 사실."
    )

    selected_work = ("job", "wealth") if work_modules is None else tuple(work_modules)
    unknown_work = sorted(set(selected_work) - {"job", "wealth"})
    if unknown_work or len(selected_work) != len(set(selected_work)):
        raise ValueError("invalid work module providers")
    work_map = {"job": work_job, "wealth": work_wealth}
    work = "\n\n".join(work_map[module_id] for module_id in selected_work)
    return {
        "cover": THREE_PILLAR_NOTICE,
        "intro": intro,
        "wonguk": wonguk,
        "nature": nature,
        "frame": frame,
        "love": love,
        "work_job": work_job,
        "work_wealth": work_wealth,
        "work": work,
        "health": health,
        "flow": flow,
        "ziwei": "",
        "together": "",
        "consult": consult,
        "closing": closing,
        "appendix_terms": appendix,
        "colophon": closing_sign or "확인된 범위 안에서 정직하게 풀었습니다.",
    }


def build_all(
    saju,
    ref_year: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
    concern_category: str | None = None,
    concern_text: str | None = None,
    closing_sign: str | None = None,
    is_leap: bool = False,
    work_modules: tuple[str, ...] | list[str] | None = None,
    birth_time_mode: str | None = None,
) -> dict[str, str]:
    if birth_time_mode == "three_pillar" or getattr(saju, "birth_time_mode", None) == "three_pillar":
        if ref_year is None:
            ref_year = int(getattr(saju, "ref_year", 0) or 0)
        return _build_three_pillar_all(
            saju,
            ref_year=ref_year,
            name=name,
            concern_category=concern_category,
            concern_text=concern_text,
            closing_sign=closing_sign,
            work_modules=work_modules,
        )
    m, z, x = saju.myeongni, saju.ziwei, saju.crosscheck
    # 호명 = 성 제외('김수하'→'수하님'), '당신' 금지(운영자 지시 2026-06-12).
    nm_call = call_name(name)
    nm_pfx = f"{nm_call}, " if name else ""
    nm_poss = f"{nm_call}의 " if name else ""
    mx, mn = _top_elem(m.elements)
    mx_ko, mn_ko = _ELEM_KO.get(mx, mx), _ELEM_KO.get(mn, mn)
    mx_mn, mn_mn = _ELEM_MEAN.get(mx, ""), _ELEM_MEAN.get(mn, "")
    sp = _soul_palace(z)
    bp = _body_palace(z)
    daewoon_dir = "역행" if not m.daewoon_forward else "순행"
    bazi = (
        f"{_gz_ko(m.year.ganzhi)} {_gz_ko(m.month.ganzhi)} "
        f"{_gz_ko(m.day.ganzhi)} {_gz_ko(m.hour.ganzhi)}"
    )
    dm = m.day_master
    dm_ko = _GAN_KO.get(dm, "")
    gk = (m.geukguk or "").split("(")[0]  # 격국 한자 병기 제거(상관격(傷官格)->상관격)
    dm_elem = _ELEM_KO.get(_GAN_ELEM.get(dm, ""), "오행")
    dm_elem_mn = _ELEM_MEAN.get(_GAN_ELEM.get(dm, ""), "자기 중심축")
    mon_sg, mon_sgm = _ss(m.month.shishen_gan), _ss_mean(m.month.shishen_gan)
    day_sg, day_sgm = _ss(m.day.shishen_gan), _ss_mean(m.day.shishen_gan)
    day_zhi_mn = _ss_mean(m.day.shishen_zhi[0]) if m.day.shishen_zhi else "관계의 작용"
    age = _age_of(saju.input_civil, ref_year)
    is_minor = age is not None and age < 19

    T: dict[str, str] = {}

    T["cover"] = (
        f"{nm_poss}사주풀이\n생년월일시(입력) {saju.input_civil}"
        + ("(생시 미상·추정)" if unknown_time else "")
        + f" · 진태양시 {saju.true_solar} · 경도 보정 {saju.eot_minutes}분"
    )

    # 1페이지 요약 대시보드(피크) — 빠르게 훑는 카드, 도입만 상담 화법으로.
    # 문구 주의(2026-07-05 운영자 지적): '압축해 보겠습니다' 류 작업 예고는 문서 내레이터
    # 말투(AI 인상) — 상담가가 판을 펼쳐 놓고 말하는 화법으로. customer_meta_lint 가
    # writer_task_announcement 로 차단하므로 여기서 '~보겠습니다'를 다시 쓰면 게이트에 걸린다.
    T["summary"] = (
        (
            f"{nm_pfx}사주를 펼쳐 놓고 보면 가장 먼저 눈에 들어오는 그림이 있습니다.\n"
            if name
            else "사주를 펼쳐 놓고 보면 가장 먼저 눈에 들어오는 그림이 있습니다.\n"
        )
        + f"[원국] 사주팔자 {bazi} · 일간 {dm_ko} — 이 글자가 {_J(nm_call, '을를')} "
        f"나타내는 중심입니다.\n"
        f"[기운 짜임] {mx_ko} 기운({mx_mn})이 비교적 강하게 보이고, {mn_ko} "
        f"기운({mn_mn})은 채워 가면 좋은 자리로 봅니다.\n"
        f"[자미 짜임] 자미두수는 별과 12궁으로 삶의 영역을 읽는 체계입니다. 명궁은 "
        f"지지(기운을 받치는 바탕 글자) {sp.branch}에 놓이고 주성은 {_stars_ko(sp)}입니다. "
        f"이 별 이름은 성향과 삶의 영역을 설명하는 상징입니다. 명반의 바탕은 "
        f"{_oguk(z.five_elements_class)}, 신궁은 {z.body_palace}입니다.\n"
        f"[읽는 방향] 여기 적힌 것은 타고난 결의 흐름이지 정해진 운명이 아니니, "
        f"{nm_call}의 선택과 쓰임에 따라 더 좋게 살릴 수 있습니다."
    )

    T["howto"] = (
        "전체 흐름에서 시작해 영역별 이야기, 시간의 결, 현실 적용 순서로 읽어 보세요. "
        "사주팔자(연·월·일·시 네 기둥), 일간(나 자신을 "
        "상징하는 글자), 십성(관계의 작용), 십이운성(기운의 단계), 지장간(지지 "
        "속 숨은 기운), 자미두수 명반(12궁의 구조) 같은 말은 처음 나올 때 "
        "괄호로 짧게 풀어 드리고, 자세한 뜻은 마지막 부록에 한데 모았습니다."
    )

    T["keywords"] = (
        f"이 사주를 빨리 이해할 다섯 단서를 먼저 짚어 드립니다.\n"
        f"① 일간 {dm_ko} — {_J(nm_call, '을를')} 상징하는 중심 글자로, 모든 풀이를 "
        f"읽는 기준점입니다.\n"
        f"② 오행 균형 — {mx_ko}({mx_mn})이 강하고 {mn_ko}({mn_mn})이 옅은 "
        f"짜임이라, 강점을 살리고 약한 쪽을 채우는 방향을 봅니다.\n"
        f"③ 명궁 주성 {_stars_ko(sp, 2)} — 자미두수에서 삶의 기본 구조를 "
        f"읽는 자리입니다.\n"
        f"④ 큰 운의 방향 — {m.daewoon_count}세부터 10년 단위로 판이 바뀌는 "
        f"{daewoon_dir}의 흐름이라, 큰 시기가 바뀌는 결을 가리킵니다.\n"
        f"⑤ 명반의 바탕 {_oguk(z.five_elements_class)} — 자미두수 해석의 토대입니다.\n"
        f"이 다섯을 머리에 두고 읽으면 전체 흐름이 한결 분명해집니다."
    )

    T["wonguk"] = (
        f"원국(原局)은 {_J(nm_call, '이가')} 태어난 네 기둥, 곧 사주팔자입니다. 중심 글자인 "
        f"일간 {_J(dm_ko, '을를')} 기준으로 네 기둥의 짜임을 차례로 풀어 봅니다.\n"
        f"{_pillar_line('연주(年柱)', m.year)}\n"
        f"{_pillar_line('월주(月柱)', m.month)}\n"
        f"{_pillar_line('일주(日柱)', m.day)}\n"
        f"{_pillar_line('시주(時柱)', m.hour)}\n"
        f"네 기둥은 연주(뿌리·환경), 월주(성장·사회), 일주(나 자신), "
        f"시주(지향·후반)라는 네 자리로 나누어 읽되, 한 기둥의 길흉을 따로 떼어 "
        f"단정하기보다 네 기둥이 어떻게 어울리는지를 보는 것이 핵심입니다. "
        f"천간은 겉으로 드러난 기운을 적은 글자이고, 지지는 그 기운을 받치는 바탕 "
        f"글자입니다. 지장간은 겉으로 잘 드러나지 않는 속기운이라, 천간과 함께 보면 결이 "
        f"한층 분명해집니다."
        + (
            "\n태어난 시각이 확인되지 않아 시주(時柱)는 표준시 기준 "
            "추정값으로 두었습니다. 정확한 생시를 아시게 되면 시주 풀이는 "
            "다시 한번 살펴보시는 것이 좋습니다."
            if unknown_time
            else ""
        )
    )

    T["ohaeng"] = (
        f"사주 안의 다섯 기운을 보면, {mx_ko} 기운({mx_mn})이 강하게 자리하고, "
        f"{mn_ko} 기운({mn_mn})은 옅은 편입니다. "
        f"{mx_ko} 기운이 강하다는 것은 그 방향의 활동에 힘이 쉽게 "
        f"실린다는 뜻으로 읽을 수 있고, 반대로 {mn_ko} 기운이 옅은 자리에서는 "
        f"한 번 더 챙기고 준비하면 도움이 됩니다. 다섯 기운은 좋고 나쁨이 "
        f"아니라 균형의 방향을 보는 자리이니, 강한 기운은 살리고 옅은 기운은 "
        f"생활에서 채워 가는 관점으로 보시면 좋습니다."
    )

    _animal = _gz_animal(m.day.ganzhi)
    # 일주 간지 자기소개("○○님은 ◇◇일주")는 원국(wonguk) 장이 소유 — 여기(기질 장)서는 재소개하지
    # 않고 일간부터 바로 풀어, 챕터 간 반복을 근원에서 차단(2026-06-14 운영자 베타 지적). 동물 비유는 유지.
    T["ilgan"] = (
        f"일간 {_J(f'{dm_ko}', '은는')} {nm_call} 자신을 상징하는 글자입니다. "
        + (f"{_animal}의 기운을 타고난 결이에요. " if _animal else "")
        + f"일지 속에는 지장간 "
        f"{_J(_hidegan_ko(m.day.hide_gan), '이가')} 들어 있으며, 십이운성으로는 "
        f"{_dishi_phrase(m.day.dishi)} 단계입니다. 일주의 "
        f"지지 십성 {_J(_ss_list(m.day.shishen_zhi), '은는')} {day_zhi_mn}의 작용으로, "
        f"{_J(nm_call, '이가')} 관계와 일을 풀어 가는 기본 방식을 읽는 단서가 됩니다. 일간이 "
        f"속한 {dm_elem}의 성질, 곧 {dm_elem_mn}의 바탕을 강점으로 살리고 "
        f"과제는 채워 가는 관점으로 보시면 좋습니다. 타고난 결은 고정된 "
        f"테두리가 아니라, 선택과 노력으로 충분히 달라질 수 있는 경향입니다."
    )

    T["sipseong"] = (
        f"십성은 일간을 기준으로 다른 글자가 맺는 '관계의 작용'입니다. 천간 "
        f"쪽을 보면 연은 {_ss(m.year.shishen_gan)}"
        f"({_ss_mean(m.year.shishen_gan)}), 월은 {mon_sg}({mon_sgm}), 일은 "
        f"{_ss(m.day.shishen_gan)}, 시는 {_ss(m.hour.shishen_gan)}"
        f"({_ss_mean(m.hour.shishen_gan)})로 드러납니다. 지지 쪽으로는 연 "
        f"{_ss_list(m.year.shishen_zhi)} / 월 {_ss_list(m.month.shishen_zhi)} / "
        f"일 {_ss_list(m.day.shishen_zhi)} / 시 {_ro(_ss_list(m.hour.shishen_zhi))} "
        f"흩어집니다. 식신은 생각과 재능을 결과물로 내놓는 힘이고, 재성은 현실 자원을 "
        f"다루는 방식, 관성은 책임과 규칙을 받아들이는 방식, 인성은 배움과 보호를 "
        f"받아들이는 힘입니다. 비겁(자기 주도)·식상(표현과 생산)·재성(현실과 재물)·"
        f"관성(책임과 절제)·인성(배움과 수용) 다섯 축이 어디에 몰리고 어디가 "
        f"옅은지가, 일과 관계를 다루는 방식을 읽는 실마리입니다. 두드러진 "
        f"축은 강점으로 살리고 옅은 축은 의식적으로 채워 가시면 됩니다. 십성은 "
        f"우열이 아니라 쓰임의 차이로 보는 것이 핵심입니다."
    )

    T["strength"] = (
        f"먼저 강점입니다. {mx_ko} 기운({mx_mn})을 쓰는 영역에서 {nm_call}의 힘이 "
        f"비교적 자연스럽게 실립니다. 여기에 천간에서 두드러진 {mon_sg}"
        f"({mon_sgm})의 방향을 겹쳐 보면, 무엇을 할 때 강점이 잘 살아나는지 "
        f"방향이 보입니다.\n"
        f"겉과 속의 짜임을 보면, 천간(겉으로 드러나는 성향)은 연 "
        f"{_ss(m.year.shishen_gan)}·월 {mon_sg}·시 {_ss(m.hour.shishen_gan)}, "
        f"지지(속·바탕의 성향)는 {_ss_list(m.day.shishen_zhi)} 중심입니다. 겉과 "
        f"속이 같은 방향이면 일관된 힘으로, 다르면 상황에 따라 다른 모습으로 "
        f"쓰이는 결로 읽습니다. 지장간 {_J(_hidegan_ko(m.day.hide_gan), '은는')} "
        f"평소엔 잘 안 보이다가 특정 상황에서 드러나는 숨은 자원으로 봅니다.\n"
        f"타고난 힘의 강약은 '{m.singang}'으로 봅니다. "
        + (
            "신약은 나약하다는 뜻이 아니라 중심 기운이 도움과 균형을 더 필요로 한다는 뜻입니다. "
            if m.singang == "신약"
            else ""
        )
        + f"{_singang_phrase(m.singang)}이 도움이 되고, {gk}의 틀에서는 "
        f"그 격의 방향을 살리는 쪽이 강점으로 이어지기 쉽습니다.\n"
        f"보완할 점은 {mn_ko} 기운({mn_mn})이 옅다는 자리입니다. 관련 상황에선 "
        f"한 박자 신중하게, 미리 준비하면 한결 수월합니다. 옅은 축은 결핍이 "
        f"아니라 작은 습관으로 채워 갈 여지이고, 어느 쪽도 고정된 한계가 "
        f"아니라 {_J(nm_call, '이가')} 다룰 수 있는 경향입니다."
    )

    # character 종합: 상위 3개만 캡(신살 수가 많아도 문단이 비대해지지 않게)
    _sal_top3 = _shinsal_by_weight(m.shinsal_detail)[:3]
    sal_txt = (
        ", ".join(f"{s}({_SHINSAL_MEAN.get(s, '기운의 한 색')})" for s in _sal_top3)
        if _sal_top3
        else "두드러진 전통 신살은 적은 편"
    )
    T["character"] = (
        f"성격과 기질은 어느 한 글자가 아니라 일간·십성·힘의 강약·신살이 "
        f"한데 어우러진 윤곽으로 드러납니다.\n"
        f"중심은 일간 {dm_ko} — {dm_elem_mn}의 바탕입니다. 바깥에서 "
        f"보이는 결(천간 십성)은 연 {_ss(m.year.shishen_gan)}·월 {mon_sg}·시 "
        f"{_ss(m.hour.shishen_gan)} 쪽이고, 마음이 편한 안쪽 결(일주 지지 "
        f"십성)은 {_ss_list(m.day.shishen_zhi)}입니다. 즉 사회에서 드러나는 "
        f"모습과 혼자 있을 때의 모습이 어느 정도 다르게 보일 수 있다는 "
        f"뜻입니다.\n"
        f"힘의 방향을 보면, "
        + (
            "스스로 끌고 가는 추진의 색이 강해 속도와 완급을 조절하는 것이 과제"
            if m.singang == "신강"
            else "주변·환경과 함께 갈 때 안정되는 색이라 의지처를 잘 두는 것이 강점"
            if m.singang == "신약"
            else "이끌기와 맞추기 사이의 균형 감각이 특징"
        )
        + f"입니다. 여기에 색을 더하는 신살(보조 단서)은 {sal_txt}입니다.\n"
        f"적성의 색을 한마디로 하면, {_J(mon_sgm, '이가')} 살아나는 환경에서 강점이 잘 "
        f"쓰이는 쪽입니다. 성격은 좋고 나쁨이 아니라 쓰임의 방향이고, 같은 "
        f"기질도 상황과 노력에 따라 다르게 나타납니다. 단정으로 받지 마시고 "
        f"자기 이해의 한 단서로 두시길 권합니다."
    )

    T["geukguk"] = (
        f"격국(格局)은 태어난 달의 기운(월령)을 중심으로 사주의 큰 틀을 보는 "
        f"분류입니다. {nm_call}의 사주는 {gk}으로 봅니다 — {m.geukguk_note} "
        f"일간의 힘은 '{m.singang}'으로 보고, "
        f"억부(抑扶) 방식으로 본 용신, 곧 명식 전체의 균형을 돕는 데 쓸 기운은 "
        f"{m.yongshin_eokbu}"
        f"({m.yongshin_axis}) 방향입니다. 다만 용신은 억부·조후·통관·병약·"
        f"종격 등 방식에 따라 달라질 수 있어, 여기서는 억부 한 가지 관점만 "
        f"제시합니다. 학설에 따라 시각이 갈려 단정하지 않고 방향으로 "
        f"짚어드립니다. 격국·용신은 좋고 나쁨의 단정이 아니라, 타고난 "
        f"기운을 어떻게 쓰면 좋을지의 방향을 보는 도구로 쓰시면 됩니다."
    )

    # 공망·12신살 공통 블록(비단정)
    _gong = getattr(m, "gongmang", {}) or {}
    _gong_parts = []
    if _gong.get("day"):
        _gong_parts.append(f"일주 기준 {'·'.join(_gong['day'])}")
    if _gong.get("year"):
        _gong_parts.append(f"년주 기준 {'·'.join(_gong['year'])}")
    _gong_line = (
        f"공망(空亡)은 비어 보이는 자리를 표시하는 전통 표기입니다 — {', '.join(_gong_parts)}. "
        f"해당 글자의 영역은 '없다'가 아니라 채워 가는 여백으로 읽습니다.\n"
        if _gong_parts
        else ""
    )
    _twelve = getattr(m, "twelve_shinsal", {}) or {}
    _tw_parts = [
        f"{_PILLAR_KO_LABEL[p]} {_twelve[p]}({_TWELVE_MEAN.get(_twelve[p], '영역의 색')})"
        for p in ("year", "month", "day", "hour")
        if _twelve.get(p)
    ]
    _twelve_line = (
        f"십이신살(十二神殺)로 본 기둥별 영역의 색은 {', '.join(_tw_parts)}입니다. "
        f"이 역시 길흉이 아니라 영역의 결을 읽는 단서입니다.\n"
        if _tw_parts
        else ""
    )

    if m.shinsal_detail:
        _ordered = _shinsal_by_weight(m.shinsal_detail)
        _per_pillar = _shinsal_per_pillar(m.shinsal_detail)
        _top = _ordered[:8]
        sal_lines = "\n".join(
            f"· {s} — {_SHINSAL_MEAN.get(s, '기운의 한 색을 읽는 단서')}" for s in _top
        )
        _overflow = _ordered[8:]
        _overflow_line = f"\n그 밖에 함께 잡히는 신살: {'·'.join(_overflow)}." if _overflow else ""
        T["shinsal"] = (
            f"신살(神殺)은 전통적으로 사주의 특정 기운을 표 기준으로 살피는 "
            f"보조 단서입니다. 기둥별로 잡히는 자리는 — {_per_pillar} — 이고, "
            f"주요 항목의 결은 다음과 같습니다.\n{sal_lines}{_overflow_line}\n"
            f"{_gong_line}{_twelve_line}"
            f"신살은 길흉의 단정이 아니라 기운의 색을 더하는 보조 단서이고, "
            f"같은 신살도 사주 전체 맥락 안에서 다르게 작동합니다. 무게를 크게 "
            f"두기보다 전체 흐름과 함께 가볍게 곁들여 보시길 권합니다."
        )
    else:
        T["shinsal"] = (
            f"신살(神殺)은 전통적으로 사주의 특정 기운을 표 기준으로 살피는 "
            f"보조 단서입니다. {nm_call}의 사주에서는 길신·살을 기준으로 두드러지게 "
            f"잡히는 항목이 적은 편입니다. 신살이 적다는 것은 좋고 나쁨의 문제가 "
            f"아니라, 특정 기운으로 크게 치우치지 않은 구성으로 읽을 수 있다는 "
            f"읽을 수 있습니다.\n{_gong_line}{_twelve_line}"
        )

    love_p = _palace(z, "부처궁")
    if is_minor:
        T["love"] = (
            f"아직 미성년인 시기라, 연애·"
            f"배우자 중심 풀이 대신 가족·친구처럼 가까운 관계의 결을 중심으로 "
            f"봅니다. {_palace_para(love_p, '가까운 관계')} 관계는 서로의 "
            f"주고받음으로 달라지는 영역이라 특정 결과를 미리 단정하지 않으며, "
            f"연애·결혼에 관한 풀이는 성년이 된 뒤 시점을 정해 다시 살펴보시길 "
            f"권합니다. 지금은 신뢰와 소통의 습관을 기르는 관점이 더 도움이 "
            f"됩니다."
        )
    else:
        T["love"] = (
            f"관계 영역은 명리의 일주와 자미두수 부처궁을 겹쳐서 봅니다.\n"
            f"{_pillar_block('일주(나의 관계 바탕)', m.day)}\n"
            f"{_palace_para(love_p, '가까운 관계', myeongni_hint=f'일주에 놓인 {_ss_list(m.day.shishen_zhi)}의 방식')}\n"
            f"정리하면, 일주의 지지 십성 {_J(_ss_list(m.day.shishen_zhi), '은는')} "
            f"{_J(nm_call, '이가')} 관계에서 편하게 여기는 거리와 방식의 결을 보여 주고, "
            f"힘의 강약 '{m.singang}'{_josa(m.singang, '은는')} {_singang_phrase(m.singang, kind='rel')}"
            f"입니다. {gk}의 틀에서 보면, 가까운 사이일수록 {day_sgm}의 "
            f"방식이 자연스럽게 드러나기 쉽습니다.\n"
            f"관계에서 짚어 보면 좋은 결이 있습니다. {day_sgm}의 방식이 "
            f"상대에게 어떻게 가닿고 있는지 한 번 떠올려 보시고, 일주 지지 십성"
            f"({_ss_list(m.day.shishen_zhi)}){_josa(_ss_list(m.day.shishen_zhi), '이가')} "
            f"편하게 여기는 거리와 상대의 기대가 어긋나는 지점은 일찍 말로 "
            f"풀어 두는 것이 좋습니다. 힘의 강약 '{m.singang}'에 맞춰 "
            + (
                "주도와 양보의 비중을 한 번 더 살펴보면"
                if m.singang != "중화"
                else "그때그때 균형을 맞추는 감각을 유지하면"
            )
            + " 관계의 호흡이 한결 편해집니다. 특정한 만남이나 헤어짐을 "
            f"단정하지 않으며, 관계는 서로의 상호작용으로 달라지는 영역으로 봅니다."
        )

    job_p = _palace(z, "관록궁")
    cheoni_p = _palace(z, _DOMAIN_PALACE["활동"])
    T["job"] = (
        f"일과 직업은 명리의 월주·시주에 자미두수 관록궁(과 활동을 보는 "
        f"천이궁)을 겹쳐서 봅니다.\n"
        f"{_pillar_block('월주(사회·일의 무대)', m.month)}\n"
        f"{_pillar_block('시주(지향·후반의 일)', m.hour)}\n"
        f"{_palace_para(job_p, '일과 성취', myeongni_hint=f'월간 {mon_sg}({mon_sgm})의 방식')}\n"
        f"월간 십성 {_J(f'{mon_sg}({mon_sgm})', '은는')} {_J(nm_call, '이가')} 일하는 방식을, "
        f"{gk}과 억부용신({m.yongshin_eokbu}, {m.yongshin_axis})은 "
        f"어떤 환경에서 강점이 잘 쓰이는지의 방향을 보는 단서입니다."
        + (
            f" 활동·이동 자리는 천이궁도 함께 보는데, 거기에는 "
            f"{_stars_full(cheoni_p)} 들어 있습니다."
            if cheoni_p
            else ""
        )
        + f"\n적성은 {_J(mon_sgm, '이가')} 살아나는 일과 역할에서 먼저 찾는 것이 "
        f"좋습니다. 힘의 강약 '{m.singang}'에 맞춰 "
        f"{_J(_singang_phrase(m.singang, kind='work'), '을를')} 염두에 두고, "
        f"대운(약 10년 단위로 바뀌는 큰 흐름)이 바뀌는 때에는 환경 변화를 미리 "
        f"준비해 두면 흐름을 타기 "
        f"수월해집니다. 적성은 하나의 정답이 아니라 강점이 잘 쓰이는 환경을 "
        f"찾는 관점입니다."
    )

    wealth_p = _palace(z, "재백궁")
    T["wealth"] = (
        f"재물은 명리의 재성·식상 축과 자미두수 재백궁 구조로 재물 흐름을 "
        f"봅니다(기둥 세부는 앞 '일과 직업'의 시주 풀이와 함께 읽어 보세요).\n"
        f"{_palace_para(wealth_p, '재물을 다루는 방식', myeongni_hint=f'재물을 밀어 주는 월간 {mon_sg}의 힘')}\n"
        f"재물은 버는 힘(재성)과 만들어 내는 힘(식상 — 일간이 생하는 작용, "
        f"{mon_sgm} 등)의 균형으로 봅니다. 힘의 강약 '{m.singang}'에 따라 "
        f"{m.yongshin_axis} 방향이 재정 운용 방식을 "
        f"읽는 단서가 되고, 별의 밝기와 사화는 모으기·굴리기·지키기 가운데 "
        f"어느 쪽이 더 자연스러운지의 색을 보여 줍니다.\n"
        f"재정에서는 {_J(_singang_phrase(m.singang, kind='money'), '을를')} 염두에 "
        f"두고 버는 흐름과 쓰는 흐름의 균형을 한 번 점검해 보시고, {gk}의 방향을 "
        f"크게 거스르는 결정 앞에서는 충분히 검토하고 분산해 두는 것이 좋습니다. "
        f"세운(해마다 바뀌는 흐름)이 달라지는 때에는 관리의 박자도 한 번 조정해 보세요."
    )

    health_p = _palace(z, _DOMAIN_PALACE["건강"])
    health_sal = [s for s in m.shinsal if _SHINSAL_META.get(s, {}).get("group") == "에너지"][:3]
    # 의료 비단정 프레이밍은 유지하되, 회피형 안내문은 고객용 문장에 넣지 않는다.
    T["health"] = (
        f"이 장은 병을 진단하는 자리가 아니라, 몸과 마음의 호흡을 살피는 "
        f"자리입니다.\n"
        f"자미두수에서 몸 상태를 보는 자리는 질액궁입니다. "
        f"{_palace_para(health_p, '몸 상태와 생활 관리', myeongni_hint=f'{mx_ko} 기운({mx_mn})의 강약') if health_p else '이 상품 구성에서는 이 자리를 생략합니다.'}\n"
        f"다섯 기운으로 보면, {mx_ko} 기운({mx_mn})이 강하고 {mn_ko} 기운"
        f"({mn_mn})이 옅은 구성입니다. 강한 쪽으로 치우쳐 무리하기 쉬운 결을 "
        f"옅은 쪽을 생활 습관으로 채우며 함께 살펴보세요(좋고 "
        f"나쁨의 단정이 아닙니다). 힘의 강약 '{m.singang}'{_rojosa(m.singang)}는 "
        f"{_singang_phrase(m.singang, kind='health')}이 생활 관리에 도움이 "
        f"되는 관점입니다.\n"
        + (
            f"함께 볼 신살({', '.join(health_sal)})은 기운이 큰 결로 보이니, "
            f"무리한 부담을 피하고 휴식·돌봄의 관점으로 살펴보세요.\n"
            if health_sal
            else ""
        )
        + f"생활에서는 강한 기운으로 치우쳐 무리하지 않게 휴식의 박자를 두고, "
        f"옅은 기운은 수면·식사·운동 같은 생활 습관으로 채워 가는 것이 "
        f"좋습니다. 몸 상태 변화는 그때그때 기록해 두고, 회복이 더딘 날은 "
        f"무리한 일정을 덜어 내세요."
    )

    # 현재 대운 단일 사실(실사고 2026-06-14): 기준 연도의 현재 대운 하나를 명시 주입해
    # 모든 챕터가 같은 대운을 '현재'로 다루게 한다(정미/병오 혼서 모순 근원 차단).
    from ..calc.myeongni import current_daewoon as _current_daewoon

    cur_dw = _current_daewoon(m, ref_year)
    cur_ko = _gz_ko(cur_dw.ganzhi) if cur_dw else ""

    def _dw_tag(d) -> str:
        if cur_dw is None:
            return ""
        if d.start_year == cur_dw.start_year:
            return "(지금 이 시기)"
        return "(지난 시기)" if d.start_year < cur_dw.start_year else "(앞으로 올 시기)"

    dw_lines = "\n".join(
        f"· {d.start_age}~{d.end_age}세 {_gz_ko(d.ganzhi)}{_dw_tag(d)} — "
        f"{_gz_elem(d.ganzhi)} 기운"
        f"({_ELEM_MEAN.get(_GAN_ELEM.get(d.ganzhi[0], ''), '')})이 강조되는 "
        f"시기로 봅니다."
        for d in m.daewoon
    )
    cur_line = (
        f"기준 {ref_year}년 현재, {nm_call}의 대운은 {cur_dw.start_age}~"
        f"{cur_dw.end_age}세 {cur_ko} 대운 하나입니다. 지금은 이 {cur_ko} 대운을 "
        f"지나는 시기이며, 그 앞의 대운은 지난 시기, 그 뒤의 대운은 아직 오지 않은 "
        f"시기이므로 '지금·현재·초입'으로 부르지 않습니다.\n"
        if cur_dw
        else ""
    )
    T["daewoon"] = (
        f"대운은 약 10년 단위로 흐르는 큰 시기입니다. {nm_call}의 대운은 "
        f"{daewoon_dir}이고, {m.daewoon_count}세부터 첫 대운이 들어와 10년 "
        f"단위로 큰 판이 바뀝니다.\n"
        f"{cur_line}"
        f"{dw_lines}\n"
        f"각 대운의 간지는 그 시기에 강조되는 오행 방향을 가리키는 "
        f"단서입니다. 대운이 바뀌는 전환기에는 환경과 역할의 변화를 미리 "
        f"차분히 준비하는 관점이 도움이 됩니다. 특정한 사건을 단정하지 않으며, "
        f"큰 흐름을 읽는 바탕으로 보시길 권합니다."
    )

    yr = _period_clean(z.yearly)
    dc = _period_clean(z.decadal)
    period_str = (
        f"자미두수 유년·대한 기준({('유년 ' + yr) if yr else ''}{(' · 대한 ' + dc) if dc else ''})"
        if (yr or dc)
        else "자미두수 유년·대한(기준 시점을 정해 살피는 시기)"
    )
    age_str = ""  # 나이 가정어('약 N세 전후') 제거 — 시기는 아래 ref_year 세운 연도로 앵커
    # 기준 연도 닻(2026-06-12 버그 수정): '올해'는 ref_year 와 정확히 일치하는
    # 세운만. 과거 해 폴백 금지(LLM "지금은 2025년" 오서술 원인). 세운 나열도
    # 기준 해 이후만 — 현재 대운 구간의 지난 해는 풀이 대상 아님.
    cur_seun = None
    if m.seun and ref_year:
        cur_seun = next((g for y, g in m.seun if y == ref_year), None)
    seun_fwd = [(y, g) for y, g in m.seun if not ref_year or y >= ref_year]
    seun_flow = " · ".join(f"{y}년 {_gz_ko(g)}" for y, g in seun_fwd[:5]) if seun_fwd else ""
    T["thisyear"] = (
        f"가까운 시기의 흐름은 {_J(period_str, '과와')} 대운의 방향을 겹쳐서 "
        f"봅니다.{age_str} 대운 {daewoon_dir}이라는 큰 방향 위에 그해의 색이 "
        f"어떻게 포개지는지를, 단정이 아니라 경향으로 읽습니다.\n"
        + (
            f"올해는 {ref_year}년, {_ro(_gz_ko(cur_seun))}의 해입니다. "
            f"{_gz_elem(cur_seun)} 오행"
            f"({_ELEM_MEAN.get(_GAN_ELEM.get(cur_seun[0], ''), '')})이 올해 "
            f"강조되는 결입니다. 앞으로의 세운 흐름은 {seun_flow}입니다. "
            f"대운({daewoon_dir})이라는 큰 바탕 위에 그해 "
            f"세운이 어떤 색으로 겹치는지를 함께 읽는 것이 핵심입니다.\n"
            if cur_seun
            else ""
        )
        + f"시기 풀이는 '무엇이 정해졌는가'가 아니라 '무엇을 준비하면 좋은가'의 "
        f"관점으로 쓰시길 권합니다. 좋게 보이는 시기에는 강점을 펼치고, "
        f"조심스러운 시기에는 속도를 고르며, 흐름에 맞춰 완급을 조절하는 "
        f"완급을 정하는 단서로 보시면 좋습니다."
    )

    wol_q = ""
    if m.worun and len(m.worun) >= 12:
        q = [m.worun[0], m.worun[3], m.worun[6], m.worun[9]]
        wol_q = " · ".join(
            f"{lab}분기 {_worun_label(g, ref_year, idx)}({_gz_elem(g)})"
            for lab, idx, (_, g) in zip(["1", "2", "3", "4"], [0, 3, 6, 9], q)
        )
    T["monthly"] = (
        f"월별 흐름은 대운({daewoon_dir})과 그해 세운의 방향을 바탕으로 봅니다. "
        f"월마다의 간지와 절기 시기는 일과 관계의 속도를 조절하는 기준으로 "
        f"삼으면 좋습니다.\n"
        + (
            f"{'올해(' + str(ref_year) + '년)' if ref_year else '기준 해'}의 월운을 분기로 나눠 보면 {wol_q}입니다. 분기마다 "
            f"강조되는 오행의 색이 달라지니, 앞쪽은 시작과 준비, 가운데는 "
            f"추진과 돌아보기, 뒤쪽은 마무리와 정리의 순서로 호흡을 잡는 단서가 "
            f"됩니다.\n"
            if wol_q
            else "한 해를 분기로 나눠 시작·추진·마무리의 결로 박자를 잡는 식으로 봅니다.\n"
        )
        + f"달마다의 흐름은 일과 관계의 속도를 잡는 단서로 쓰시고, 구체적인 "
        f"달별 조언은 기준 시점을 정해 이어서 짚어드립니다."
    )

    if seun_fwd:
        seun_str = ", ".join(f"{y}년 {_gz_ko(g)}" for y, g in seun_fwd)
        wol_str = (
            ", ".join(_worun_label(g, ref_year, i) for i, (_, g) in enumerate(m.worun))
            if m.worun
            else "기준 시점을 정하면 이어서 짚어드립니다"
        )
        _yr_lab = f"올해({ref_year}년)의" if ref_year else "기준 해의"
        T["seun"] = (
            f"세운(歲運)은 해마다 바뀌는 흐름, 월운(月運)은 달마다의 오르내림입니다. "
            f"특정 사건의 단정이 아니라 준비의 완급을 읽는 단서입니다.\n"
            f"올해부터의 세운 흐름은 {seun_str}입니다.\n"
            f"{_yr_lab} 월운은 {wol_str}입니다.\n"
            f"각 해·달의 간지는 그 시기에 강조되는 오행 방향을 가리키며, "
            f"대운({daewoon_dir})의 큰 흐름 위에서 함께 봅니다. 좋게 보이는 "
            f"해에는 강점을 펼치고, 조심스러운 해에는 속도를 고르며 완급을 "
            f"조절하는 바탕으로 쓰시길 권합니다."
        )
    else:
        T["seun"] = (
            "세운(해마다의 흐름)과 월운(달마다의 오르내림)은 대운의 큰 흐름 위에서 "
            "함께 보는 흐름입니다. 기준 시점(예: 올해)을 정하면 그 시기의 "
            "세운·월운 간지를 짚어 시기별 준비의 완급을 살펴볼 수 있습니다. "
            "특정 사건을 단정하지 않으며, 시기 풀이는 기준 시점과 상황을 "
            "정해 이어서 짚어드립니다."
        )

    # P4: '명리는 흐름/자미는 구조' 역할분담 정형 소거 — 지도 은유로 교체(반복어 '구조' 억제 겸).
    T["ziwei_summary"] = (
        f"자미두수 명반은 {nm_call}의 삶이 어느 자리에서 펼쳐지는지를 한 판에 그린 "
        f"지도입니다. {nm_call}의 명궁은 {z.soul_palace}(지지 "
        f"{sp.branch})에 놓이고 거기에는 {_stars_full(sp)} 들어 있습니다. "
        f"신궁은 {z.body_palace}(지지 {bp.branch})로, {_stars_full(bp)} "
        f"있습니다. 명반의 바탕은 {_oguk(z.five_elements_class)}입니다. 명궁은 타고난 "
        f"기본 바탕을, 신궁은 살아가며 힘이 실리는 자리를 읽는 단서입니다. "
        f"별이 밝을수록 그 자리의 기운이 분명하게 드러나고, 사화(화록·화권·"
        f"화과·화기)는 그 힘이 향하는 쪽을 읽는 단서가 됩니다. 명반은 길흉의 "
        f"단정이 아니라 삶의 구조를 이해하는 지도처럼 보시길 권합니다."
        + (
            " 子/午시 출생이라 명궁과 신궁이 같은 자리에 놓입니다."
            if sp is bp or z.soul_palace == z.body_palace
            else ""
        )
        + (
            # 윤달 산입 기준 고지(절대규칙 5) — 자미두수 15일 분할법. 자미 섹션에만 넣어
            # 실제로 이 기준이 적용된 리포트에서만 고지된다(명리 단독/시진불명은 자미 미표시).
            " 신청하신 생일이 윤달이라, 자미두수 명반은 15일 분할법으로 산입했습니다"
            "(음력 1~15일생은 그 달, 16일 이후는 다음 달을 기준으로 봅니다)."
            if is_leap
            else ""
        )
    )

    # P4(B안): 9장 핵심 궁도 명리 앵커를 참조해 통합 서술(자미 사일로 해소).
    _ZW_HINT = {
        "명궁": f"일간 {dm_ko}의 중심축",
        "관록궁": f"월간 {mon_sg}({mon_sgm})의 방식",
        "재백궁": "버는 힘과 만들어 내는 힘의 축",
        "부처궁": f"일주에 놓인 {_ss_list(m.day.shishen_zhi)}의 방식",
        "질액궁": f"{mx_ko} 기운({mx_mn})의 강약",
    }
    key_para = []
    for nm in _KEY_PALACES:
        p = _palace(z, nm)
        if p:
            key_para.append(
                "· "
                + _palace_para(
                    p, _PALACE_ROLE.get(nm, "삶의 한 영역"), myeongni_hint=_ZW_HINT.get(nm, "")
                )
            )
    all_lines = []
    seen = set()
    for nm in _PALACE_ORDER:
        p = _palace(z, nm)
        if not p or nm in _KEY_PALACES:
            continue
        seen.add(nm)
        all_lines.append(_palace_brief(p, _PALACE_ROLE_ALL.get(nm, "삶의 한 영역")))
    # _PALACE_ORDER 에 없는 변형 궁명도 누락 없이
    for p in z.palaces:
        if p.name not in _KEY_PALACES and p.name not in seen:
            all_lines.append(_palace_brief(p, _PALACE_ROLE_ALL.get(p.name, "삶의 한 영역")))
    T["ziwei_palaces"] = (
        "자미두수 12궁은 삶의 영역별 구조를 봅니다. 먼저 핵심 궁을 자세히 봅니다.\n"
        + "\n".join(key_para)
        + "\n이제 나머지 궁을 한 줄씩 짚어 봅니다.\n"
        + "\n".join(all_lines)
        + "\n각 궁의 주성·보좌성과 별의 밝기·사화를 함께 보면, 영역별로 힘이 "
        "실리는 곳과 한 번 더 챙길 곳의 결이 보입니다. 어느 궁도 길흉의 "
        "단정이 아니라 구조를 읽는 단서이며, 별 이름은 이 명반에 실재하는 "
        "것만 다룹니다."
    )

    # P4(B안): 10장을 방법론 일반론('명리는 흐름/자미는 구조' 재진술)에서 이 사람의
    # 실제 겹침을 짚는 3영역 교차 요약(관계·일과 재물·시간)으로 재작성. 시진 불명이면
    # 궁 실명 없이 층위 원칙만(절대규칙 8 — 자미 서술 생략).
    _cross_head = (
        f"명리와 자미두수를 교차로 맞춰 보았습니다. 사주팔자 일치는 "
        f"'{'예' if x.bazi_consistent else '아니오'}', 월지 교차는 "
        f"'{'일치' if x.month_branch_ok else '재검토 필요'}'입니다. 두 체계는 같은 출생 "
        f"정보를 다른 방식으로 읽습니다. 여기서는 두 판의 역할을 따로 떼지 않고 "
        f"{nm_call}의 실제 자리에서 겹쳐 읽었습니다.\n"
    )
    if not unknown_time and love_p is not None and job_p is not None and wealth_p is not None:
        _cross_body = (
            f"가까운 관계에서는, 일주에 놓인 {_ss_list(m.day.shishen_zhi)}의 방식이 "
            f"{_J(nm_call, '이가')} 편해하는 거리와 방식을 보여 주고, 부처궁의 "
            f"{_J(_stars_ko(love_p), '이가')} 그 방식이 실제 관계에서 드러나는 장면을 "
            f"비춥니다. 하나는 결의 안쪽이고 하나는 생활의 바깥쪽일 뿐, 같은 이야기입니다.\n"
            f"일과 재물에서도 같습니다. 월간 {mon_sg}({mon_sgm})의 힘이 일하는 방식의 "
            f"큰 줄기라면, 관록궁의 {_J(_stars_ko(job_p), '과와')} 재백궁의 "
            f"{_J(_stars_ko(wealth_p), '은는')} 그 줄기가 어느 무대에서 힘을 받는지의 "
            f"국면입니다.\n"
            f"시간에서는 명리의 대운·세운이 큰 방향을 정하고, 자미두수의 대한·유년은 같은 "
            f"흐름이 지나는 영역을 짚습니다. 두 판이 다르게 보이는 대목은 틀린 것이 아니라 "
            f"층위가 다른 것이라, 큰 방향은 명리를 따르고 영역의 결은 자미두수로 보면 "
            f"됩니다. 같은 출생 정보에서 두 판이 어긋나지 않는다는 것은 풀이의 토대가 "
            f"안정적이라는 근거가 됩니다."
        )
    else:
        _cross_body = (
            f"명리의 대운·세운이 큰 방향을 정하고, 영역별 결은 상황에 따라 나누어 "
            f"살핍니다. 두 체계가 같은 출생 정보에서 어긋나지 않는다는 것은 풀이의 "
            f"토대가 안정적이라는 근거가 됩니다."
        )
    T["cross"] = (
        _cross_head + _cross_body + (f" 함께 볼 점: {' / '.join(x.warnings)}" if x.warnings else "")
    )

    T["advice"] = (
        f"{mn_ko} 기운({mn_mn})의 보완은 생활 "
        f"습관에서 점검하고, {mx_ko} 기운({mx_mn})의 강점은 일과 관계에서 "
        f"의식적으로 살리는 방향을 권합니다. 십성에서 두드러진 {mon_sg}의 "
        f"결은 자연스러운 강점으로 쓰고, 옅은 축은 작은 습관으로 채워 가시면 "
        f"됩니다.\n"
        f"다음 세 달, 작게 시도해 볼 If-Then(상황 → 행동) 메모입니다(보장이 "
        f"아니라 실행을 돕는 점검 틀입니다).\n"
        f"· 중요한 결정을 앞두면 → {mx_ko}의 강점({mx_mn})을 어떻게 쓸지 한 "
        f"줄로 적어 보세요.\n"
        f"· {mn_ko} 기운({mn_mn})이 필요한 상황이면 → 서두르지 말고 확인 "
        f"질문을 하나 두고 시작해 보세요.\n"
        f"· 같은 고민이 반복되면 → {mon_sg}의 결로 치우치지 않았는지 "
        f"점검하고 한 가지만 바꿔 보세요.\n"
        f"한 번에 많이 바꾸기보다 한두 가지를 정해 꾸준히 점검하는 방식을 "
        f"권하며, 더 궁금한 점은 질문 주시면 이어서 짚어드립니다."
    )

    T["caution"] = (
        f"반복되기 쉬운 선택의 결을 일간 {_J(f'{dm_ko}', '과와')} 십성 구조로 함께 "
        f"점검해 보세요. 강한 축은 잘 쓰이면 강점이지만 과하면 같은 흐름을 "
        f"되풀이하게 만들 수 있고, 약한 축은 중요한 결정에서 놓치기 쉬운 "
        f"지점이 됩니다. 예컨대 {mon_sg}의 결이 두드러질 때는 그 방향으로만 "
        f"기울지 않는지 한 번 더 살피는 습관이 도움이 됩니다. 결정 전에 확인 "
        f"질문을 하나 두는 것은 겁을 주려는 것이 아니라 점검의 관점이며, "
        f"되풀이되는 흐름을 알아 두면 같은 자리에서 덜 머뭅니다."
    )

    T["questions"] = (
        "이어서 다루면 좋은 질문을 제안해 드립니다.\n"
        "① 올해 집중할 한 가지는 무엇인가\n"
        "② 관계에서 지금 점검할 부분은 무엇인가\n"
        "③ 일·재물 결정에서 확인할 포인트는 무엇인가\n"
        "④ 다가오는 대운 전환기를 어떻게 준비할 것인가.\n"
        "이 질문들에 대한 답을 사주의 결과 함께 정리하면, 풀이의 내용을 "
        "실제 선택으로 옮기는 데 도움이 됩니다. 정답을 받기보다, 자신에게 "
        "맞는 질문을 다듬는 자리로 활용하시길 권합니다."
    )

    T["closing"] = (
        f"{nm_pfx}여기까지 함께 읽어 주셔서 감사합니다. 타고난 기운은 방향을 "
        f"보는 단서이지, 정해진 결말이 아닙니다. 같은 사주라도 선택과 노력, "
        f"환경에 따라 길은 충분히 달라질 수 있습니다. {nm_call}의 강점인 "
        f"{mx_ko} 기운({mx_mn})은 살리고, 옅은 {mn_ko} 기운은 작은 습관으로 "
        f"채워 가시길 바랍니다. 이 글이 스스로를 차분히 이해하고 다음 "
        f"걸음을 고르게 내딛는 계기가 되면 좋겠습니다. 자신을 너무 단정하지 "
        f"마시고, 흐름을 읽는 지도처럼 곁에 두고 활용하시면 좋겠습니다."
    )

    # 용어 풀이 — 기호(불릿 ·) 없이 '용어: 풀이' 줄 단위(기호 난발 금지, 2026-06-12)
    T["appendix_terms"] = (
        "본문에 나온 전문 용어를 한곳에 모아 쉬운 말로 풀었습니다. "
        "읽다가 막히면 여기를 펼쳐 보세요.\n"
        "사주팔자: 태어난 연, 월, 일, 시를 각각 천간과 지지 두 글자로 적은 "
        "여덟 글자. 인생을 읽는 기본 좌표입니다.\n"
        "천간(天干): 하늘의 기운을 나타내는 열 글자. 겉으로 드러나는 성향입니다.\n"
        "지지(地支): 땅의 기운을 나타내는 열두 글자. 환경과 바탕을 봅니다.\n"
        "일간(日干): 태어난 날의 천간으로, 나 자신을 상징하는 중심 글자.\n"
        "지장간(支藏干): 지지 속에 숨어 있는 천간. 겉으로 안 보이는 속기운.\n"
        "오행(五行): 목, 화, 토, 금, 수 다섯 기운. 강약의 균형을 봅니다.\n"
        "십성(十星): 일간을 기준으로 다른 글자가 맺는 관계의 작용. 비겁, "
        "식상, 재성, 관성, 인성 다섯 갈래로, 일과 관계의 방식을 읽는 단서.\n"
        "십이운성(十二運星): 기운이 자라고 무르익고 정리되는 열두 단계를 "
        "가리키는 보조 지표입니다.\n"
        "납음(納音): 간지 조합에 붙는 오행의 상징적 표현.\n"
        "대운(大運): 약 10년 단위로 흐르는 큰 시기.\n"
        "자미두수 명반: 12궁(자리)에 별을 배치해 인생의 구조를 보는 그림.\n"
        "명궁과 신궁: 타고난 기본 바탕(명궁)과 살아가며 힘이 실리는 자리"
        "(신궁)를 보는 핵심 자리입니다.\n"
        "사화(四化): 별에 붙는 화록, 화권, 화과, 화기 네 가지 변화의 신호.\n"
        "오행국(五行局): 자미두수 명반 해석의 토대가 되는 분류입니다.\n"
        "모든 용어는 좋고 나쁨의 단정이 아니라, 자신을 이해하는 틀로 "
        "보시면 됩니다."
    )

    # colophon = 맺음 서명(절대규칙 18 개정, 2026-06-12 운영자 지시 — 본문에
    # 도구·AI 언급 고지 금지). 브랜드 서명은 R5에서 주입.
    T["next"] = (
        f"{nm_pfx}여기까지가 이번 풀이의 전부입니다.\n\n"
        "명리학과 자미두수는 천 년 넘게 사람의 기질과 때를 읽어 온 학문입니다. "
        "이 풀이도 그 오랜 틀 위에서 한 글자 한 글자 정성을 들여 적었습니다.\n\n"
        "같은 사주라도 길은 선택에 따라 달라집니다. "
        "막히는 자리가 생기면 이 글을 다시 펴 보세요.\n\n"
        + (f"{closing_sign}" if closing_sign else "")
    )

    # Phase5 구간3(룰 폴백) — 신청 고민 라우팅. 카테고리→도메인 결로 안내(비단정).
    # 고객 원문은 본문에 넣지 않는다(가드 주입·PII 회피). 카테고리는 안전한 enum 값뿐.
    _CONSULT_DOMAIN = {
        "연애": "연애·관계의 결",
        "직업": "일·직업의 결",
        "재물": "재물·돈의 결",
        "건강": "건강·생활 관리의 결",
        "대인": "대인관계와 성향의 결",
        "시기": "대운·시기의 흐름",
        "전반": "사주 전반의 큰 흐름",
    }
    _cc = concern_category or "전반"
    _domain = _CONSULT_DOMAIN.get(_cc, _CONSULT_DOMAIN["전반"])
    _near_label = (
        f"{ref_year}년 하반기부터 {ref_year + 1}년 상반기까지" if ref_year else "앞으로 1년 안"
    )
    _ctx = _consult_context(concern_text)
    _ctx_topics = list(_ctx["topics"])
    _ctx_detail = str(_ctx["detail"])
    _love_detail = _love_context_detail(concern_text)
    _love_focus_kind = _love_focus(concern_text)
    # P1(2026-07-05 운영자 실격 판정 후속): 직답에 자미 궁 실명 근거를 대기 위한 결정론 슬롯.
    # 카테고리→궁 매핑, 시진 불명이면 궁 문장 통째 생략(절대규칙 8 — 자미 단독 강등).
    _CONSULT_PALACE = {
        "연애": "부처궁",
        "직업": "관록궁",
        "재물": "재백궁",
        "건강": "질액궁",
        "대인": "천이궁",
    }
    _cp = None
    if not unknown_time:
        _cp = _palace(z, _CONSULT_PALACE[_cc]) if _cc in _CONSULT_PALACE else sp
    _cp_line = ""
    if _cp is not None:
        _cp_line = (
            f"자미두수에서 같은 영역을 비추는 자리는 {_cp.name}인데, 여기에 "
            f"{_J(_stars_ko(_cp), '이가')} 놓여 있습니다. 명리가 가리키는 방식과 이 자리가 "
            f"비추는 영역이 같은 곳을 향하고 있어, 두 판을 겹쳐 읽어도 답의 방향은 하나로 "
            f"모입니다. "
        )
    if _cc == "연애":
        _love_intro = _love_consult_intro(_love_focus_kind, _near_label)
        # QI-2026-07-04(F2): 재회 전제 문구(기존 상대·재접촉·붙잡기)는 원문에 재회 토큰이
        # 실제 있을 때(_love_focus == reunion)만. 그 외 연애 질문(결혼운·새 만남·일반)은
        # 기존 상대를 전제하지 않는 중립 판단 문단으로 서술(과수정 금지 — 연애 답변 자체는 유지).
        if _love_focus_kind == "reunion":
            _love_body = (
                f"연락은 길게 감정을 쏟아내는 방식보다 짧고 담백하게 시작하는 편이 좋고, 직접 닿기 어려운 "
                f"상황이라면 겹지인, 학교, 전공, 일상 동선처럼 자연스럽게 마주치는 자리부터 살피는 것이 "
                f"무리한 접근보다 낫습니다.\n\n"
                f"판단 기준은 분명해야 합니다. 상대가 답을 이어 오고, 약속을 구체적으로 잡고, 예전 문제를 "
                f"피하지 않고 말하려 한다면 관계가 다시 움직일 여지가 있습니다. 반대로 답이 짧고 늦어지거나, "
                f"같은 상처를 반복하거나, 주변을 통해서만 소식을 흘리는 흐름이라면 기다림을 길게 끌수록 "
                f"{nm_call}만 지치기 쉽습니다. 이때는 한 번 더 붙잡는 것보다 마음을 정리하는 쪽이 더 안전합니다. "
                f"접촉이 제한된 상황에서는 무리하게 마음을 확인하려 들기보다, 서로 부담이 적은 자리에서 "
                f"짧은 안부가 자연스럽게 오갈 수 있는지를 먼저 보세요."
            )
            _love_close = "재회나 결혼을 단정하지는 않지만, "
        else:
            _love_body = (
                f"판단 기준은 분명해야 합니다. 대화가 자연스럽게 이어지고, 약속이 구체화되고, 생활의 "
                f"결이 맞는지를 차례로 확인하면 관계가 움직일 여지가 있습니다. 반대로 감정만 앞서 결론을 "
                f"서두르거나 혼자만 애쓰는 흐름이 반복되면 {nm_call}만 지치기 쉬우니 속도를 늦추는 편이 "
                f"안전합니다. 새 만남은 소개팅이나 가벼운 첫 만남에서 짧은 안부와 대화가 자연스럽게 "
                f"이어지는지 보고, 결혼은 생활 기준과 돈 관리가 맞는지부터 확인해야 합니다."
            )
            _love_close = "어떤 결론도 미리 단정하지는 않지만, "
        T["consult"] = (
            f"{nm_pfx}먼저 핵심부터 말하면, {_love_intro} "
            + _love_body
            + (f" {_love_detail}" if _love_detail else "")
            + "\n\n"
            # P1: '명리는 X/자미는 Y' 역할분담 정형 대신 궁 실명 근거(시진 불명 시 생략).
            + _cp_line
            + f"좋은 말만 듣고 버티는 것이 아니라, 언제 다가가고 언제 멈출지를 나누어 보는 것이 "
            f"이 판이 가리키는 방식입니다. "
            + _love_close
            + f"관계가 움직이는 신호와 무리하면 흔들리는 신호를 먼저 살피는 것이 이 고민의 핵심입니다. "
            f"{_near_label}는 감정의 크기를 키우는 때가 아니라 서로의 반응을 천천히 살피는 시기로 "
            f"쓰십시오. 관계의 속도는 마음이 맞는 만큼만 올리는 것이 이 판에 맞는 방식입니다."
        )
    elif _ctx_topics:
        _topic_text = ", ".join(_ctx_topics)
        _focus_text = _concern_snapshot_label(_ctx_topics)
        T["consult"] = (
            f"{nm_pfx}먼저 핵심부터 말하면, 이번 질문은 {_topic_text}을 한꺼번에 보아야 하는 고민입니다. "
            f"{_near_label}에는 한 번에 크게 밀어붙이기보다, {_focus_text}을 나누어 살피는 "
            f"쪽이 더 안전합니다. 움직일 수는 있지만 서두르는 방식은 맞지 않고, "
            f"지금 가장 중요한 한 가지부터 순서를 정하는 쪽이 맞습니다.\n\n"
            f"{_ctx_detail} "
            f"특히 이 질문은 {_focus_text}을 따로 나누어 보아야 합니다. 좋은 말만 믿고 한 번에 넘기기보다, "
            f"{nm_call}이 감당할 수 있는 속도와 우선순위를 정한 뒤 움직이는 편이 낫습니다.\n\n"
            # P1: 역할분담 정형 대신 성향+궁 실명 근거로 방향 단정.
            f"{nm_call}의 판에서 이 고민을 풀 도구는 분명합니다. 월에 놓인 {mon_sg}({mon_sgm})의 "
            f"결이 실제로 쓸 수 있는 힘이라, {mon_sgm} 쪽으로 판을 정리하면 속도가 붙습니다. "
            + _cp_line
            + f"{_near_label}는 방향을 정하고 가장 작은 것부터 실행해 반응을 살피는 시기로 "
            f"쓰십시오. 부담이 커지는 약속만 한 번 더 늦추면, 이 시기의 힘을 안전하게 쓸 수 있습니다."
        )
    else:
        # P1(2026-07-05 운영자 실격 판정): 구 골격은 388자 유보 체크리스트 — 질문에 정면으로
        # 답하는 유일한 챕터가 폴백 시 가장 얇았다(v7 실측). [방향 단정]→[근거 겹침]→[시기]→
        # [조심할 자리]→[첫 행동] 5문단, 계산 사실 슬롯만 근거(결과 보장 없음), 나열 기호 금지.
        T["consult"] = (
            f"{nm_pfx}신청해 주신 고민은 '{_cc}' 영역, 곧 {_domain}에 닿아 있습니다. "
            f"결론부터 말하면, 이 질문은 답을 밖에서 구할 일이 아니라 {nm_call}의 판이 "
            f"이미 가리키고 있는 방식대로 정리하면 되는 일입니다. {dm_ko} 일간에 "
            f"{mx_ko} 기운({mx_mn})이 강하게 놓인 구성은 고민을 오래 쥐고 있을수록 힘이 "
            f"새는 결이라, {_near_label} 안에 매듭을 짓는 쪽이 맞습니다. "
            f"{_singang_phrase(m.singang)}도 같은 방향을 가리킵니다.\n\n"
            f"조금 더 들어가면, 월에 놓인 {mon_sg}({mon_sgm})의 결이 이 고민을 풀 때 "
            f"{nm_call}이 실제로 쓸 수 있는 도구입니다. {mon_sgm} 쪽으로 판을 정리하면 "
            f"속도가 붙고, 그 결을 거슬러 가면 같은 노력에도 진척이 더딥니다. " + _cp_line + "\n\n"
            f"시기는 {_near_label}가 판을 정리하기에 가장 유리한 때입니다. 이때에는 "
            f"새 판을 벌리기보다 이미 걸려 있는 일의 우선순위를 정하는 일이 먼저입니다. "
            f"직접 움직일 수 있는 것과 기다려야 하는 것을 나누고, 마음의 속도를 맞추십시오. "
            f"이 시기 안에서도 무게 배분이 있어, 앞쪽은 정리와 방향 잡기에, 뒤쪽은 실행과 "
            f"결정에 힘을 실으면 같은 힘을 두 번 쓰지 않아도 됩니다. 그 다음 해부터는 "
            f"정리된 판 위에서 넓히는 흐름으로 이어 가면 됩니다.\n\n"
            f"조심할 자리도 분명합니다. {mn_ko} 기운({mn_mn})이 옅은 구성이라, "
            f"{mn_mn}이 필요한 국면에서 서두르면 빈틈이 생기기 쉽습니다. 빈틈은 대개 큰일이 "
            f"아니라 마음과 행동의 속도가 어긋난 데서 생깁니다. 이 대목만 의식적으로 "
            f"한 박자 늦추면, 강한 {mx_ko} 기운이 만들어 둔 판을 안전하게 지킬 수 "
            f"있습니다.\n\n"
            f"오늘 시작할 첫걸음은 이 고민에서 {nm_call}이 직접 움직일 수 있는 것과 "
            f"상대나 상황에 달린 것을 나누어 보는 일입니다. 직접 움직일 수 있는 것 가운데 "
            f"가장 작은 하나를 {_near_label} 초입에 실행하고 반응을 살피십시오. 상황에 달린 "
            f"것은 억지로 당기지 말고 기다림의 경계를 정해 두십시오. 그렇게 하면 이 "
            f"질문의 답이 막연한 감에서 벗어나고, 그때부터는 같은 고민이 "
            f"같은 무게로 돌아오지 않습니다."
        )

    # --- 주제별 챕터 조립 (2026-06-11 재편 1단계: 옛 섹션을 새 챕터 키로 병합) ---
    # 산문화·기호 제거는 2단계에서. 여기서는 키 정합만 맞춘다. toc 는 빌더가 생성.
    def _join(*keys: str) -> str:
        return "\n\n".join(T[k].strip() for k in keys if T.get(k, "").strip())

    # Q7 모듈 제공자 분리: 기본값은 옛 ``_join("job", "wealth")``와 같은 순서·바이트를
    # 유지한다. 부분 조립에서는 integrated 진입점이 선택한 제공자만 넘기며, 빈 튜플은
    # work 섹션을 뒤 단계에서 제외할 때 쓰는 명시적 값이다. 미등록·중복은 조용히 보정하지 않는다.
    selected_work = ("job", "wealth") if work_modules is None else tuple(work_modules)
    unknown_work = sorted(set(selected_work) - {"job", "wealth"})
    if unknown_work:
        raise ValueError(f"unknown work module providers: {unknown_work}")
    if len(selected_work) != len(set(selected_work)):
        raise ValueError("work module providers must not contain duplicates")
    selected_work = tuple(
        module_id
        for module_id in integrated_modules.SELECTABLE_MODULES
        if module_id in selected_work and module_id in {"job", "wealth"}
    )

    NT: dict[str, str] = {
        "cover": T["cover"],
        "intro": _join("summary", "howto", "keywords"),
        "wonguk": _join("wonguk", "ohaeng"),
        "nature": _join("ilgan", "sipseong", "character", "strength"),
        "frame": _join("geukguk", "shinsal"),
        "love": T["love"],
        # 독립 제공자는 integrated 조립과 회귀 테스트가 소비한다. 기존 개인 상품 소비자는
        # 계속 ``work`` 하나만 읽으므로 SECTION_SPECS와 5모듈 기본 출력은 변하지 않는다.
        "work_job": T["job"],
        "work_wealth": T["wealth"],
        "work": _join(*selected_work),
        "health": T["health"],
        "flow": _join("daewoon", "thisyear", "seun", "monthly"),
        "ziwei": _join("ziwei_summary", "ziwei_palaces"),
        "together": T["cross"],
        "consult": T["consult"],
        "closing": _join("advice", "caution", "closing"),
        "appendix_terms": T["appendix_terms"],
        "colophon": T["next"],
    }
    return NT


def partner_block(pf, saju, label: str = "", lunar_input: bool = False) -> str:
    """상대방·가족 명식 사실 슬롯(consult 근거 주입용) — PartnerFacts 표시 계층.

    생년월일 원본은 넣지 않는다(절대규칙 17 — LLM에는 파생 간지·오행·십성만).
    label = '남편 최지호'·'장남 이서연' 식 관계+이름(없으면 '상대방').
    """
    m = saju.myeongni
    my_dm_ko = _GAN_KO.get(m.day.gan, m.day.gan)
    my_dm_elem = _gz_elem(m.day.ganzhi)  # 천간 기준 오행 한글
    d_animal = _gz_animal(pf.day.ganzhi)
    who = label or "상대방"
    hour_note = (
        "" if pf.hour_known else " 태어난 시간은 미상이라 시주는 제외, 대운도 산출하지 않았다."
    )
    lunar_note = " 신청 글의 음력 생일을 양력으로 바꿔 계산했다." if lunar_input else ""
    pillars = (
        f"{_gz_ko(pf.year.ganzhi)}년 {_gz_ko(pf.month.ganzhi)}월 {_gz_ko(pf.day.ganzhi)}일"
        + (f" {_gz_ko(pf.hour.ganzhi)}시" if pf.hour_known and pf.hour else "")
    )
    lines = [
        f"[{who}의 명식 — 신청 글에 적힌 생년월일 기준.{lunar_note}{hour_note} "
        f"아래는 본인이 아니라 '{who}'의 사실이다]",
        f"{who}은(는) {pillars}생, 곧 {_gz_ko(pf.day.ganzhi)}일주"
        + (f", 일주로 보면 {d_animal}의 기운" if d_animal else "")
        + ".",
        f"{who}의 일간은 {_GAN_KO.get(pf.day.gan, pf.day.gan)}, 오행으로 {pf.day_gan_elem_ko}.",
        f"본인 일간 {my_dm_ko}({my_dm_elem}) 기준으로 {who}의 일간 "
        f"{_J(pf.day_gan_elem_ko, '은는')} {_ss(pf.shishen_to_me)}에 해당한다.",
    ]
    if pf.gan_hap:
        lines.append(f"두 사람의 일간은 천간합, {pf.gan_hap}의 짝이다.")
    if pf.ilji_relation == "육합":
        lines.append(f"본인 일지와 {who}의 일지는 육합, 서로 끌어당겨 묶이는 자리다.")
    elif pf.ilji_relation == "충":
        lines.append(f"본인 일지와 {who}의 일지는 충, 강하게 부딪히며 흔드는 자리다.")
    if pf.ilji_hai:
        lines.append(
            f"본인 일지와 {who}의 일지는 해, 생활 흐름이 엇갈리기 쉬워 확인이 필요한 자리다."
        )
    if pf.ilji_po:
        lines.append(
            f"본인 일지와 {who}의 일지는 파, 가까워진 뒤에도 약속과 역할을 다시 맞춰야 하는 자리다."
        )
    if pf.ilji_wonjin:
        lines.append(
            f"본인 일지와 {who}의 일지는 원진, 이유 없이 서먹해지기 쉬워 감정을 천천히 확인해야 하는 자리다."
        )
    if pf.ilji_xing:
        lines.append(
            f"본인 일지와 {who}의 일지는 {pf.ilji_xing}, "
            "비슷한 반응이 반복될 때 속도를 낮춰야 하는 자리다."
        )
    if pf.ilji_banhap:
        lines.append(
            f"본인 일지와 {who}의 일지는 삼합의 짝, 만나면 {pf.ilji_banhap}의 기운이 "
            f"살아나는 짜임이다."
        )
    if pf.complements_elems_ko:
        lines.append(
            f"{who}의 명식에는 본인에게 옅은 "
            + ", ".join(pf.complements_elems_ko)
            + " 기운이 들어 있다."
        )
    if pf.matches_my_yongshin:
        lines.append(f"{who}의 일간 오행은 본인의 억부용신과 같다.")
    return "\n".join(lines)
