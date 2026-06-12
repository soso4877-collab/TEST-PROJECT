# -*- coding: utf-8 -*-
"""룰 골격 — 계산 결과(SajuResult)에서만 사실을 끌어와 §12-안전 문장을 생성.

이 텍스트는 LLM 없이도 항상 완결·안전(가드 실패 시 폴백 기본값).

말투 원칙(디벨롭3, 공신력 자료 기반 — NN/g Tone·서사 전이·처리유창성):
- 보고서체가 아니라 상담 화법. 읽는 분에게 말하듯 2인칭 친근 존대로 풀되,
  한국어가 자연스럽게 주어를 생략하는 자리는 생략하고 강조에서만 '당신'.
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
    "질액궁": "건강과 컨디션을 살피는 자리",
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
    "천을귀인": {"mean": "도움을 주는 인연·귀인의 결을 보는 참고", "group": "귀인", "weight": 9},
    "태극귀인": {"mean": "복록·반전의 결을 보는 참고", "group": "귀인", "weight": 6},
    "문창귀인": {"mean": "학업·표현·기획 쪽 재능의 결", "group": "학문", "weight": 8},
    "학당귀인": {"mean": "학문·가르침·배움 쪽의 결", "group": "학문", "weight": 6},
    "금여": {"mean": "안정·배우자복·재물의 결을 보는 참고", "group": "재물", "weight": 7},
    "암록": {"mean": "보이지 않는 조력·뒷배의 결", "group": "재물", "weight": 7},
    "도화살": {"mean": "매력·인기·관계의 활기를 보는 참고", "group": "활동", "weight": 7},
    "역마살": {"mean": "이동·변화·활동성이 강조되는 결", "group": "활동", "weight": 7},
    "화개살": {"mean": "몰입·예술·학문 쪽으로 기우는 결", "group": "학문", "weight": 6},
    "천문성": {
        "mean": "철학·종교·역학·의료 등 깊이 보는 분야와의 결",
        "group": "적성",
        "weight": 4,
    },
    "고신살": {"mean": "혼자만의 거리·고독의 결을 살피는 참고", "group": "관계", "weight": 5},
    "과숙살": {"mean": "관계에서 거리·여백의 결을 살피는 참고", "group": "관계", "weight": 5},
    "양인": {"mean": "강한 추진력 — 과하지 않게 쓰는 관점", "group": "에너지", "weight": 6},
    "괴강": {"mean": "강단·결단의 기운 — 균형의 관점", "group": "에너지", "weight": 6},
    "백호": {"mean": "에너지가 큰 결 — 신중함과 함께 쓰는 관점", "group": "에너지", "weight": 6},
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
    maj = ", ".join(_star_one(s) for s in p.major_stars) or "주성 없음(공궁)"
    out = f"주성은 {maj}"
    minr = ", ".join(s.name for s in p.minor_stars)
    if minr:
        out += f", 보좌성은 {minr}"
    return out


def _palace_brief(p, role: str) -> str:
    if p is None:
        return ""
    tag = "(명궁)" if p.is_soul else ("(신궁)" if p.is_body else "")
    return f"· {p.name}{tag}(지지 {p.branch}) — {role}: {_stars_full(p)}."


def _palace_para(p, role: str) -> str:
    """한 궁을 상담 화법으로 — 같은 꼬리말이 궁마다 반복되지 않게 _pick."""
    if p is None:
        return f"{_J(role, '을를')} 보는 자리는 이 명반 구성에서는 정보가 제한적입니다."
    tag = "(명궁)" if p.is_soul else ("(신궁)" if p.is_body else "")
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
    tail = _pick(
        "ppT" + p.name + role,
        [
            "별의 밝기와 사화(화록·화권·화과·화기)는 이 영역에서 기운이 "
            "드러나는 세기와 방향을 읽는 단서가 됩니다.",
            "밝기는 이 자리의 힘이 또렷한 정도를, 사화는 그 힘이 향하는 "
            "쪽을 가늠하는 참고가 됩니다.",
            "별이 밝을수록 그 결이 분명하게 드러나고, 사화는 그 흐름이 "
            "어디로 기우는지를 보는 실마리가 됩니다.",
            "어느 별이 자리했는지와 그 밝기를, 사화가 더하는 방향과 함께 "
            "읽으면 이 영역의 결이 또렷해집니다.",
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
            "신강": "에너지를 많이 쓰는 결이라 휴식과 완급 조절을 의식적으로 두는 것",
            "신약": "무리한 소모보다 회복과 보강의 리듬을 챙기는 것",
            "중화": "활동과 휴식의 균형을 그때그때 살피는 것",
        },
    }
    return table.get(kind, table["general"]).get(singang, "균형을 그때그때 살피는 관점")


def build_all(
    saju,
    ref_year: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
    concern_category: str | None = None,
) -> dict[str, str]:
    m, z, x = saju.myeongni, saju.ziwei, saju.crosscheck
    nm_pfx = f"{name}님, " if name else ""
    nm_poss = f"{name}님의 " if name else ""
    nm_call = f"{name}님" if name else "당신"
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
        f"{nm_poss}사주풀이 결과지\n생년월일시(입력) {saju.input_civil}"
        + ("(생시 미상·추정)" if unknown_time else "")
        + f" · 진태양시 {saju.true_solar} · 경도 보정 {saju.eot_minutes}분"
    )

    # 1페이지 요약 대시보드(피크) — 빠르게 훑는 카드, 도입만 상담 화법으로
    T["summary"] = (
        (
            f"{nm_pfx}먼저 사주를 한 장으로 압축해 보겠습니다.\n"
            if name
            else "사주를 한 장으로 압축해 보겠습니다.\n"
        )
        + f"[원국] 사주팔자 {bazi} · 일간 {dm_ko} — 이 글자가 당신을 "
        f"나타내는 중심입니다.\n"
        f"[기운 분포] {mx_ko} 기운({mx_mn})이 비교적 또렷하고, {mn_ko} "
        f"기운({mn_mn})은 채워 가면 좋은 자리로 봅니다.\n"
        f"[자미 구조] 명궁은 지지 {sp.branch}에 놓이고 주성은 {_stars_ko(sp)}, "
        f"오행국은 {_oguk(z.five_elements_class)}, 신궁은 {z.body_palace}입니다.\n"
        f"[읽는 방향] 큰 그림 → 영역별 흐름 → 시간의 결 → 현실 적용 순으로 "
        f"이어집니다. 타고난 결의 흐름이니, 당신의 선택과 쓰임에 따라 "
        f"더 좋게 살릴 수 있습니다."
    )

    T["howto"] = (
        "이 결과지는 '큰 그림 → 영역별 흐름 → 시간의 결 → 현실 적용' 순서로 "
        "읽도록 짜여 있습니다. 사주팔자(연·월·일·시 네 기둥), 일간(나 자신을 "
        "상징하는 글자), 십성(관계의 작용), 십이운성(기운의 단계), 지장간(지지 "
        "속 숨은 기운), 자미두수 명반(12궁의 구조) 같은 말은 처음 나올 때 "
        "괄호로 짧게 풀어 드리고, 자세한 뜻은 마지막 부록에 한데 모았습니다."
    )

    T["keywords"] = (
        f"이 사주를 빨리 이해할 다섯 단서를 먼저 짚어 드립니다.\n"
        f"① 일간 {dm_ko} — 당신을 상징하는 중심 글자로, 모든 풀이를 "
        f"읽는 기준점입니다.\n"
        f"② 오행 균형 — {mx_ko}({mx_mn})이 강하고 {mn_ko}({mn_mn})이 옅은 "
        f"분포라, 강점을 살리고 약한 쪽을 채우는 방향을 봅니다.\n"
        f"③ 명궁 주성 {_stars_ko(sp, 2)} — 자미두수에서 삶의 기본 구조를 "
        f"읽는 자리입니다.\n"
        f"④ 대운 {daewoon_dir}(대운수 {m.daewoon_count}) — 시간이 흐르는 "
        f"방향과 큰 시기가 바뀌는 결을 가리킵니다.\n"
        f"⑤ 오행국 {_oguk(z.five_elements_class)} — 자미두수 명반 해석의 토대입니다.\n"
        f"이 다섯을 머리에 두고 읽으면 전체 흐름이 한결 또렷해집니다."
    )

    T["wonguk"] = (
        f"원국(原局)은 당신이 태어난 네 기둥, 곧 사주팔자입니다. 중심 글자인 "
        f"일간 {_J(dm_ko, '을를')} 기준으로 네 기둥의 짜임을 차례로 풀어 봅니다.\n"
        f"{_pillar_line('연주(年柱)', m.year)}\n"
        f"{_pillar_line('월주(月柱)', m.month)}\n"
        f"{_pillar_line('일주(日柱)', m.day)}\n"
        f"{_pillar_line('시주(時柱)', m.hour)}\n"
        f"네 기둥은 연주(뿌리·환경), 월주(성장·사회), 일주(나 자신), "
        f"시주(지향·후반)의 결로 나누어 읽되, 한 기둥의 길흉을 따로 떼어 "
        f"단정하기보다 네 기둥이 어떻게 어울리는지를 보는 것이 핵심입니다. "
        f"지장간은 겉으로 잘 드러나지 않는 속기운이라, 천간과 함께 보면 결이 "
        f"한층 또렷해집니다."
        + (
            "\n참고로, 태어난 시각이 확인되지 않아 시주(時柱)는 표준시 기준 "
            "추정값으로 두었습니다. 정확한 생시를 아시게 되면 시주 풀이는 "
            "다시 한번 살펴보시는 것이 좋습니다."
            if unknown_time
            else ""
        )
    )

    T["ohaeng"] = (
        f"여덟 글자를 오행으로 세어 보면, "
        + " · ".join(f"{_ELEM_KO.get(k, k)} {v}" for k, v in m.elements.items())
        + " 입니다. "
        + " ".join(
            f"{_J(_ELEM_KO.get(k, k), '은는')} {_ELEM_MEAN.get(k, '')}의 결로 {v}만큼 잡힙니다."
            for k, v in m.elements.items()
        )
        + f" {mx_ko} 기운이 또렷하다는 것은 그 방향의 활동에 힘이 쉽게 "
        f"실린다는 뜻으로 읽을 수 있고, 반대로 {mn_ko} 기운은 옅어서 관련 "
        f"상황에서는 한 번 더 챙기고 준비하면 도움이 됩니다. 오행은 좋고 나쁨이 "
        f"아니라 균형의 방향을 보는 자리이니, 강한 기운은 살리고 옅은 기운은 "
        f"생활에서 채워 가는 관점으로 활용해 보세요."
    )

    T["ilgan"] = (
        f"일간 {_J(f'{dm_ko}', '은는')} 당신 자신을 상징하는 글자입니다. 당신의 "
        f"일주는 {_gz_ko(m.day.ganzhi)}이고, 그 속에는 지장간 "
        f"{_J(_hidegan_ko(m.day.hide_gan), '이가')} 들어 있으며, 십이운성으로는 "
        f"{_dishi_phrase(m.day.dishi)}의 결입니다. 일주의 "
        f"지지 십성 {_J(_ss_list(m.day.shishen_zhi), '은는')} {day_zhi_mn}의 결로, "
        f"당신이 관계와 일을 풀어 가는 기본 방식을 읽는 단서가 됩니다. 일간이 "
        f"속한 {dm_elem}의 성질, 곧 {dm_elem_mn}의 결을 강점으로 살리고 "
        f"과제는 채워 가는 관점으로 보시면 좋습니다. 타고난 결은 고정된 "
        f"테두리가 아니라, 선택과 노력으로 충분히 달라질 수 있는 경향입니다."
    )

    T["sipseong"] = (
        f"십성은 일간을 기준으로 다른 글자가 맺는 '관계의 작용'입니다. 천간 "
        f"쪽을 보면 연은 {_ss(m.year.shishen_gan)}"
        f"({_ss_mean(m.year.shishen_gan)}), 월은 {mon_sg}({mon_sgm}), 일은 "
        f"{_ss(m.day.shishen_gan)}, 시는 {_ss(m.hour.shishen_gan)}"
        f"({_ss_mean(m.hour.shishen_gan)})의 결입니다. 지지 쪽으로는 연 "
        f"{_ss_list(m.year.shishen_zhi)} / 월 {_ss_list(m.month.shishen_zhi)} / "
        f"일 {_ss_list(m.day.shishen_zhi)} / 시 {_ro(_ss_list(m.hour.shishen_zhi))} "
        f"흩어집니다. 비겁(자기 주도)·식상(표현과 생산)·재성(현실과 재물)·"
        f"관성(책임과 절제)·인성(배움과 수용) 다섯 축이 어디에 몰리고 어디가 "
        f"옅은지가, 당신이 일과 관계를 다루는 방식을 읽는 실마리입니다. 두드러진 "
        f"축은 강점으로 살리고 옅은 축은 의식적으로 채워 가시면 됩니다. 십성은 "
        f"우열이 아니라 쓰임의 차이로 보는 것이 핵심입니다."
    )

    T["strength"] = (
        f"먼저 강점입니다. {mx_ko} 기운({mx_mn})을 쓰는 영역에서 당신의 힘이 "
        f"비교적 자연스럽게 실립니다. 여기에 천간에서 두드러진 {mon_sg}"
        f"({mon_sgm})의 결을 겹쳐 보면, 무엇을 할 때 강점이 잘 살아나는지 "
        f"방향이 보입니다.\n"
        f"겉과 속의 결도 함께 보겠습니다. 천간(겉으로 드러나는 결)은 연 "
        f"{_ss(m.year.shishen_gan)}·월 {mon_sg}·시 {_ss(m.hour.shishen_gan)}, "
        f"지지(속·바탕의 결)는 {_ss_list(m.day.shishen_zhi)} 중심입니다. 겉과 "
        f"속이 같은 방향이면 일관된 힘으로, 다르면 상황에 따라 다른 모습으로 "
        f"쓰이는 결로 읽습니다. 지장간 {_J(_hidegan_ko(m.day.hide_gan), '은는')} "
        f"평소엔 잘 안 보이다가 특정 상황에서 드러나는 숨은 자원으로 봅니다.\n"
        f"신강약은 '{m.singang}'(균형 점수 {m.singang_score})입니다. "
        f"{_singang_phrase(m.singang)}이 도움이 되고, {gk}의 틀에서는 "
        f"그 격의 결을 살리는 쪽이 강점으로 이어지기 쉽습니다.\n"
        f"보완할 점은 {mn_ko} 기운({mn_mn})이 옅다는 자리입니다. 관련 상황에선 "
        f"한 박자 신중하게, 미리 준비하면 한결 수월합니다. 옅은 축은 결핍이 "
        f"아니라 작은 습관으로 채워 갈 여지이고, 어느 쪽도 고정된 한계가 "
        f"아니라 당신이 다룰 수 있는 경향입니다."
    )

    # character 종합: 상위 3개만 캡(신살 수가 많아도 문단이 비대해지지 않게)
    _sal_top3 = _shinsal_by_weight(m.shinsal_detail)[:3]
    sal_txt = (
        ", ".join(f"{s}({_SHINSAL_MEAN.get(s, '기운의 한 색')})" for s in _sal_top3)
        if _sal_top3
        else "두드러진 전통 신살은 적은 편"
    )
    _sg_q = f"'{m.singang}'(점수 {m.singang_score})"
    T["character"] = (
        f"이번에는 성격·기질을 일간·십성·신강약·신살로 한데 모아 보겠습니다"
        f"(앞의 '일간과 성향'이 중심 글자라면, 여기서는 전체 윤곽을 종합합니다).\n"
        f"중심은 일간 {dm_ko} — {dm_elem_mn}의 바탕입니다. 바깥에서 "
        f"보이는 결(천간 십성)은 연 {_ss(m.year.shishen_gan)}·월 {mon_sg}·시 "
        f"{_ss(m.hour.shishen_gan)} 쪽이고, 마음이 편한 안쪽 결(일주 지지 "
        f"십성)은 {_ss_list(m.day.shishen_zhi)}입니다. 즉 사회에서 드러나는 "
        f"모습과 혼자 있을 때의 모습이 어느 정도 다르게 보일 수 있다는 "
        f"뜻입니다.\n"
        f"힘의 결은 신강약 {_ro(_sg_q)}, "
        + (
            "스스로 끌고 가는 추진의 색이 강해 속도와 완급을 조절하는 것이 과제"
            if m.singang == "신강"
            else "주변·환경과 함께 갈 때 안정되는 색이라 의지처를 잘 두는 것이 강점"
            if m.singang == "신약"
            else "이끌기와 맞추기 사이의 균형 감각이 특징"
        )
        + f"입니다. 여기에 색을 더하는 신살(참고)은 {sal_txt}입니다.\n"
        f"적성의 색을 한마디로 하면, {_J(mon_sgm, '이가')} 살아나는 환경에서 강점이 잘 "
        f"쓰이는 쪽입니다. 성격은 좋고 나쁨이 아니라 쓰임의 방향이고, 같은 "
        f"기질도 상황과 노력에 따라 다르게 나타납니다. 단정으로 받지 마시고 "
        f"자기 이해의 참고로 두시길 권합니다."
    )

    T["geukguk"] = (
        f"격국(格局)은 태어난 달의 기운(월령)을 중심으로 사주의 큰 틀을 보는 "
        f"분류입니다. 당신의 사주는 {gk}으로 봅니다 — {m.geukguk_note} "
        f"일간의 힘(신강약)은 '{m.singang}'(균형 점수 {m.singang_score})이고, "
        f"억부(抑扶) 방식으로 본 참고 용신은 {m.yongshin_eokbu}"
        f"({m.yongshin_axis}) 방향입니다. 다만 용신은 억부·조후·통관·병약·"
        f"종격 등 방식에 따라 달라질 수 있어, 이 결과지는 억부 한 가지 방식의 "
        f"참고만 제시합니다. 정확한 용신과 격국의 세밀한 판정은 상담에서 "
        f"확정하시길 권합니다. 격국·용신은 좋고 나쁨의 단정이 아니라, 타고난 "
        f"기운을 어떻게 쓰면 좋을지의 방향을 보는 도구로 활용하시면 됩니다."
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
        f"해당 글자의 영역은 '없다'가 아니라 채워 가는 여백으로 읽는 참고입니다.\n"
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
        f"이 역시 길흉이 아니라 영역의 결을 보는 참고입니다.\n"
        if _tw_parts
        else ""
    )

    if m.shinsal_detail:
        _ordered = _shinsal_by_weight(m.shinsal_detail)
        _per_pillar = _shinsal_per_pillar(m.shinsal_detail)
        _top = _ordered[:8]
        sal_lines = "\n".join(
            f"· {s} — {_SHINSAL_MEAN.get(s, '기운의 한 색을 보는 참고')}" for s in _top
        )
        _overflow = _ordered[8:]
        _overflow_line = f"\n그 외 참고로 잡히는 신살: {'·'.join(_overflow)}." if _overflow else ""
        T["shinsal"] = (
            f"신살(神殺)은 전통적으로 사주의 특정 기운을 표 기준으로 살피는 "
            f"보조 참고입니다. 기둥별로 잡히는 자리는 — {_per_pillar} — 이고, "
            f"주요 항목의 결은 다음과 같습니다.\n{sal_lines}{_overflow_line}\n"
            f"{_gong_line}{_twelve_line}"
            f"신살은 길흉의 단정이 아니라 기운의 색을 더하는 보조 참고이고, "
            f"같은 신살도 사주 전체 맥락 안에서 다르게 작동합니다. 무게를 크게 "
            f"두기보다 전체 흐름과 함께 가볍게 곁들여 보시길 권합니다."
        )
    else:
        T["shinsal"] = (
            f"신살(神殺)은 전통적으로 사주의 특정 기운을 표 기준으로 살피는 "
            f"보조 참고입니다. 당신의 사주에서는 길신·살을 기준으로 두드러지게 "
            f"잡히는 항목이 적은 편입니다. 신살이 적다는 것은 좋고 나쁨의 문제가 "
            f"아니라, 특정 기운으로 크게 치우치지 않은 구성으로 읽을 수 있다는 "
            f"참고입니다.\n{_gong_line}{_twelve_line}"
        )

    love_p = _palace(z, "부처궁")
    if is_minor:
        T["love"] = (
            f"이 결과지의 대상은 아직 미성년으로 추정되어(약 {age}세), 연애·"
            f"배우자 중심 풀이 대신 가족·친구처럼 가까운 관계의 결을 중심으로 "
            f"보겠습니다. {_palace_para(love_p, '가까운 관계')} 관계는 서로의 "
            f"주고받음으로 달라지는 영역이라 특정 결과를 미리 단정하지 않으며, "
            f"연애·결혼에 관한 풀이는 성년이 된 뒤 시점을 정해 다시 살펴보시길 "
            f"권합니다. 지금은 신뢰와 소통의 습관을 기르는 관점이 더 도움이 "
            f"됩니다."
        )
    else:
        T["love"] = (
            f"관계 영역은 명리의 일주와 자미두수 부처궁을 겹쳐서 보겠습니다.\n"
            f"{_pillar_block('일주(나의 관계 바탕)', m.day)}\n"
            f"{_palace_para(love_p, '가까운 관계')}\n"
            f"정리하면, 일주의 지지 십성 {_J(_ss_list(m.day.shishen_zhi), '은는')} "
            f"당신이 관계에서 편하게 여기는 거리와 방식의 결을 보여 주고, "
            f"신강약 '{m.singang}'{_josa(m.singang, '은는')} {_singang_phrase(m.singang, kind='rel')}"
            f"입니다. {gk}의 틀에서 보면, 가까운 사이일수록 {day_sgm}의 "
            f"방식이 자연스럽게 드러나기 쉽습니다.\n"
            f"이 사주의 결에서 나온 관계 점검 세 가지를 권합니다. 첫째, "
            f"{day_sgm}의 방식이 상대에게 어떻게 가닿고 있는지 한 번 떠올려 "
            f"보세요. 둘째, 일주 지지 십성({_ss_list(m.day.shishen_zhi)})"
            f"{_josa(_ss_list(m.day.shishen_zhi), '이가')} "
            f"편하게 여기는 거리와 상대의 기대가 어긋나는 지점을 일찍 말로 "
            f"풀어 보세요. 셋째, 신강약 '{m.singang}'에 맞춰 "
            + (
                "주도와 양보의 비중을 한 번 더 살펴보세요"
                if m.singang != "중화"
                else "그때그때 균형을 맞추는 감각을 유지해 보세요"
            )
            + ". 특정한 만남이나 헤어짐을 단정하지 않으며, 관계는 두 사람의 "
            f"상호작용으로 달라지는 영역으로 봅니다."
        )

    job_p = _palace(z, "관록궁")
    cheoni_p = _palace(z, _DOMAIN_PALACE["활동"])
    T["job"] = (
        f"일과 직업은 명리의 월주·시주에 자미두수 관록궁(과 활동을 보는 "
        f"천이궁)을 겹쳐서 봅니다.\n"
        f"{_pillar_block('월주(사회·일의 무대)', m.month)}\n"
        f"{_pillar_block('시주(지향·후반의 일)', m.hour)}\n"
        f"{_palace_para(job_p, '일과 성취')}\n"
        f"월간 십성 {_J(f'{mon_sg}({mon_sgm})', '은는')} 당신이 일하는 방식의 결을, "
        f"{gk}과 억부용신({m.yongshin_eokbu}, {m.yongshin_axis})은 "
        f"어떤 환경에서 강점이 잘 쓰이는지의 방향을 보는 단서입니다."
        + (
            f" 활동·이동의 결은 천이궁도 함께 보는데, 거기에는 "
            f"{_stars_full(cheoni_p)} 들어 있습니다."
            if cheoni_p
            else ""
        )
        + f"\n적성을 볼 때 세 가지 관점을 권합니다. 첫째, {_J(mon_sgm, '이가')} 살아나는 "
        f"일과 역할을 먼저 찾아보세요. 둘째, 신강약 '{m.singang}'에 맞춰 "
        f"{_J(_singang_phrase(m.singang, kind='work'), '을를')} 염두에 두세요. 셋째, "
        f"대운이 바뀌는 전환기에 맞춰 환경 변화를 미리 준비해 두세요. 적성은 "
        f"하나의 정답이 아니라 강점이 잘 쓰이는 환경을 찾는 관점이며, 합격이나 "
        f"취업의 결과를 단정하지는 않습니다."
    )

    wealth_p = _palace(z, "재백궁")
    T["wealth"] = (
        f"재물은 명리의 재성·식상 축과 자미두수 재백궁 구조로 흐름의 결을 "
        f"봅니다(기둥 세부는 앞 '일과 직업'의 시주 풀이를 같이 참고하세요).\n"
        f"{_palace_para(wealth_p, '재물을 다루는 방식')}\n"
        f"재물은 버는 힘(재성)과 만들어 내는 힘(식상 — 일간이 생하는 결, "
        f"{mon_sgm} 등)의 균형으로 봅니다. 신강약 '{m.singang}'(점수 "
        f"{m.singang_score})에 따라 {m.yongshin_axis} 방향이 재정 운용의 결을 "
        f"읽는 참고가 되고, 별의 밝기와 사화는 모으기·굴리기·지키기 가운데 "
        f"어느 쪽이 더 자연스러운지의 색을 보여 줍니다.\n"
        f"이 사주의 결에서 나온 재정 점검 세 가지를 권합니다. 첫째, "
        f"{_J(_singang_phrase(m.singang, kind='money'), '을를')} 염두에 두고, "
        f"버는 흐름과 쓰는 흐름의 균형을 한 번 점검해 보세요. 둘째, "
        f"{gk}의 결을 크게 거스르는 결정 "
        f"앞에서는 충분히 검토하고 분산해 두세요. 셋째, 세운 흐름이 바뀌는 "
        f"전환기에 맞춰 관리의 리듬을 한 번 조정해 보세요. 수익이나 손실을 "
        f"단정하거나 보장하지 않으며, 큰 결정은 전문가 상담을 함께 권합니다."
    )

    health_p = _palace(z, _DOMAIN_PALACE["건강"])
    health_sal = [s for s in m.shinsal if _SHINSAL_META.get(s, {}).get("group") == "에너지"][:3]
    # 의료 비단정 원칙 유지(진단 아님 + 진료 권유) — 표현만 자연스럽게
    # (운영자 지시 2026-06-12: '전문가와 상의' 류 보일러플레이트 금지).
    T["health"] = (
        f"이 장은 병을 진단하는 자리가 아니라, 몸과 마음의 결을 살피는 "
        f"자리입니다. 몸이 보내는 신호가 이어진다면 병원 진료로 먼저 "
        f"확인해 보세요.\n"
        f"자미두수에서 컨디션을 보는 자리는 질액궁입니다. "
        f"{_palace_para(health_p, '컨디션과 생활 관리') if health_p else '이 상품 구성에서는 이 자리를 생략합니다.'}\n"
        f"오행으로 보면, {mx_ko} 기운({mx_mn})이 또렷하고 {mn_ko} 기운"
        f"({mn_mn})이 옅은 구성입니다. 강한 쪽으로 치우쳐 무리하기 쉬운 결을 "
        f"옅은 쪽을 생활 습관으로 채우며 함께 보는 참고로 활용해 보세요(좋고 "
        f"나쁨의 단정이 아닙니다). 신강약 '{m.singang}'{_rojosa(m.singang)}는 "
        f"{_singang_phrase(m.singang, kind='health')}이 생활 관리에 도움이 "
        f"되는 관점입니다.\n"
        + (
            f"참고 신살({', '.join(health_sal)})은 에너지가 큰 결로 보이니, "
            f"무리한 부담을 피하고 휴식·점검의 관점으로 활용해 보세요.\n"
            if health_sal
            else ""
        )
        + f"생활에서 살피면 좋은 세 가지입니다. 첫째, 강한 기운으로 치우쳐 "
        f"무리하지 않게 휴식의 리듬을 두세요. 둘째, 옅은 기운을 수면·식사·"
        f"운동 같은 생활 습관으로 채워 보세요. 셋째, 컨디션 변화는 기록해 두고, "
        f"몸의 신호가 이어지면 병원에서 확인해 보세요."
    )

    dw_lines = "\n".join(
        f"· {d.start_age}~{d.end_age}세 {_gz_ko(d.ganzhi)} — "
        f"{_gz_elem(d.ganzhi)} 기운"
        f"({_ELEM_MEAN.get(_GAN_ELEM.get(d.ganzhi[0], ''), '')})이 강조되는 "
        f"시기로 봅니다."
        for d in m.daewoon
    )
    T["daewoon"] = (
        f"대운은 약 10년 단위로 흐르는 큰 시기의 결입니다. 당신의 대운은 "
        f"{daewoon_dir}이고 대운수는 {m.daewoon_count}입니다.\n"
        f"{dw_lines}\n"
        f"각 대운의 간지는 그 시기에 강조되는 기운의 방향을 가리키는 "
        f"참고입니다. 대운이 바뀌는 전환기에는 환경과 역할의 변화를 미리 "
        f"차분히 준비하는 관점이 도움이 됩니다. 특정한 사건을 단정하지 않으며, "
        f"흐름의 큰 결을 읽는 자료로 보시길 권합니다."
    )

    yr = _period_clean(z.yearly)
    dc = _period_clean(z.decadal)
    period_str = (
        f"자미두수 유년·대한 기준({('유년 ' + yr) if yr else ''}{(' · 대한 ' + dc) if dc else ''})"
        if (yr or dc)
        else "자미두수 유년·대한(상담에서 시점을 정해 함께 살피는 구간)"
    )
    age_str = f" 현재 약 {age}세 전후로 보면," if age is not None else ""
    cur_seun = None
    if m.seun:
        cur_seun = next((g for y, g in m.seun if y == ref_year), m.seun[0][1])
    seun_flow = " · ".join(f"{y}년 {_gz_ko(g)}" for y, g in m.seun[:5]) if m.seun else ""
    T["thisyear"] = (
        f"가까운 시기의 흐름은 {_J(period_str, '과와')} 대운의 결을 겹쳐서 "
        f"봅니다.{age_str} 대운 {daewoon_dir}이라는 큰 방향 위에 그해의 기운이 "
        f"어떻게 포개지는지를, 단정이 아니라 경향으로 읽습니다.\n"
        + (
            f"세운(해마다의 기운) 흐름은 {seun_flow}입니다. 기준 해의 세운은 "
            f"{_ro(_gz_ko(cur_seun))}, {_gz_elem(cur_seun)} 기운"
            f"({_ELEM_MEAN.get(_GAN_ELEM.get(cur_seun[0], ''), '')})이 그해에 "
            f"강조되는 결입니다. 대운({daewoon_dir})이라는 큰 물길 위에 그해 "
            f"세운이 어떤 색으로 겹치는지를 함께 읽는 것이 핵심입니다.\n"
            if cur_seun
            else ""
        )
        + f"시기 풀이는 '무엇이 정해졌는가'가 아니라 '무엇을 준비하면 좋은가'의 "
        f"관점으로 쓰시길 권합니다. 좋게 보이는 시기에는 강점을 펼치고, "
        f"조심스러운 시기에는 속도를 고르며, 흐름에 맞춰 리듬을 조절하는 "
        f"참고로 보시면 좋습니다."
    )

    wol_q = ""
    if m.worun and len(m.worun) >= 12:
        q = [m.worun[0], m.worun[3], m.worun[6], m.worun[9]]
        wol_q = " · ".join(
            f"{lab}분기 {_gz_ko(g)}({_gz_elem(g)})" for lab, (_, g) in zip(["1", "2", "3", "4"], q)
        )
    T["monthly"] = (
        f"월별 흐름은 대운({daewoon_dir})과 그해 세운의 결을 바탕으로 봅니다. "
        f"결과지에서는 큰 흐름만 짚어 드리며, 특정 달에 특정 사건이 일어난다고 "
        f"단정하지 않습니다.\n"
        + (
            f"기준 해의 월운을 분기로 나눠 보면 {wol_q}입니다. 분기마다 "
            f"강조되는 기운의 색이 달라지니, 앞쪽은 시작과 준비, 가운데는 "
            f"추진과 점검, 뒤쪽은 마무리와 정리의 결로 리듬을 잡는 참고가 "
            f"됩니다.\n"
            if wol_q
            else "한 해를 분기로 나눠 시작·추진·마무리의 결로 리듬을 잡는 식으로 봅니다.\n"
        )
        + f"달마다의 결은 일과 관계의 리듬을 잡는 참고로 쓰시고, 구체적인 "
        f"달별 조언은 시점을 정해 상담에서 함께 정리하시길 권합니다."
    )

    if m.seun:
        seun_str = ", ".join(f"{y}년 {_gz_ko(g)}" for y, g in m.seun)
        wol_str = (
            ", ".join(f"{i + 1}월 {_gz_ko(g)}" for i, (_, g) in enumerate(m.worun))
            if m.worun
            else "상담에서 기준 시점을 정해 함께 봅니다"
        )
        T["seun"] = (
            f"세운(歲運)은 해마다 바뀌는 기운, 월운(月運)은 달마다의 결입니다. "
            f"특정 사건의 단정이 아니라 준비의 리듬을 보는 참고입니다.\n"
            f"세운 흐름은 {seun_str}입니다.\n"
            f"기준 해의 월운은 {wol_str}입니다.\n"
            f"각 해·달의 간지는 그 시기에 강조되는 기운의 방향을 가리키며, "
            f"대운({daewoon_dir})의 큰 흐름 위에서 함께 봅니다. 좋게 보이는 "
            f"해에는 강점을 펼치고, 조심스러운 해에는 속도를 고르며 리듬을 "
            f"조절하는 자료로 활용하시길 권합니다."
        )
    else:
        T["seun"] = (
            "세운(해마다의 기운)과 월운(달마다의 결)은 대운의 큰 흐름 위에서 "
            "함께 보는 참고입니다. 기준 시점(예: 올해)을 정하면 그 구간의 "
            "세운·월운 간지를 짚어 시기별 준비의 리듬을 살펴볼 수 있습니다. "
            "특정 사건을 단정하지 않으며, 정확한 시기 풀이는 상담에서 시점을 "
            "정해 함께 정리하시길 권합니다."
        )

    T["ziwei_summary"] = (
        f"자미두수 명반은 인생의 '구조'를 보는 틀입니다. 당신의 명궁은 {z.soul_palace}(지지 "
        f"{sp.branch})에 놓이고 거기에는 {_stars_full(sp)} 들어 있습니다. "
        f"신궁은 {z.body_palace}(지지 {bp.branch})로, {_stars_full(bp)} "
        f"있습니다. 오행국은 {_oguk(z.five_elements_class)}입니다. 명궁은 타고난 "
        f"기본 바탕을, 신궁은 살아가며 힘이 실리는 자리를 보는 참고입니다. "
        f"별이 밝을수록 그 자리의 기운이 또렷하게 드러나고, 사화(화록·화권·"
        f"화과·화기)는 그 힘이 향하는 쪽을 읽는 단서가 됩니다. 명반은 길흉의 "
        f"단정이 아니라 삶의 구조를 이해하는 지도처럼 보시길 권합니다."
        + (
            " 참고로, 子/午시 출생이라 명궁과 신궁이 같은 자리에 놓입니다."
            if sp is bp or z.soul_palace == z.body_palace
            else ""
        )
    )

    key_para = []
    for nm in _KEY_PALACES:
        p = _palace(z, nm)
        if p:
            key_para.append("· " + _palace_para(p, _PALACE_ROLE.get(nm, "삶의 한 영역")))
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
        "자미두수 12궁은 삶의 영역별 구조를 봅니다. 먼저 핵심 궁을 자세히, "
        "이어 나머지 궁을 한 줄로 모두 짚어 드리겠습니다.\n"
        "[핵심 궁]\n"
        + "\n".join(key_para)
        + "\n[그 밖의 궁]\n"
        + "\n".join(all_lines)
        + "\n각 궁의 주성·보좌성과 별의 밝기·사화를 함께 보면, 영역별로 힘이 "
        "실리는 곳과 한 번 더 챙길 곳의 결이 보입니다. 어느 궁도 길흉의 "
        "단정이 아니라 구조를 읽는 참고이며, 별 이름은 이 명반에 실재하는 "
        "것만 다룹니다."
    )

    T["cross"] = (
        f"명리와 자미두수를 교차로 맞춰 보았습니다. 사주팔자 일치는 "
        f"'{'예' if x.bazi_consistent else '아니오'}', 월지 교차는 "
        f"'{'일치' if x.month_branch_ok else '재검토 필요'}'입니다. 두 체계는 "
        f"같은 출생 정보를 다른 방식으로 봅니다. 명리는 시간의 '흐름'을, "
        f"자미두수는 인생의 '구조'를 보는 역할로 나눠, 같은 결론이 나오는 "
        f"부분은 강조하고 관점이 다른 부분은 상황별로 분리해 살핍니다. 두 "
        f"체계가 같은 출생 정보에서 어긋나지 않는다는 것은, 풀이의 토대가 "
        f"안정적이라는 참고가 됩니다." + (f" 참고: {' / '.join(x.warnings)}" if x.warnings else "")
    )

    T["advice"] = (
        f"이제 현실에 적용해 보겠습니다. {mn_ko} 기운({mn_mn})의 보완은 생활 "
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
        f"권하며, 구체적인 계획은 상담에서 시점과 상황을 정해 함께 정리할 수 "
        f"있습니다."
    )

    T["caution"] = (
        f"반복되기 쉬운 선택의 결을 일간 {_J(f'{dm_ko}', '과와')} 십성 구조로 함께 "
        f"점검해 보세요. 강한 축은 잘 쓰이면 강점이지만 과하면 같은 패턴을 "
        f"되풀이하게 만들 수 있고, 약한 축은 중요한 결정에서 놓치기 쉬운 "
        f"지점이 됩니다. 예컨대 {mon_sg}의 결이 두드러질 때는 그 방향으로만 "
        f"기울지 않는지 한 번 더 살피는 습관이 도움이 됩니다. 결정 전에 확인 "
        f"질문을 하나 두는 것은 겁을 주려는 것이 아니라 점검의 관점이며, "
        f"패턴을 알아 두면 같은 자리에서 덜 머뭅니다."
    )

    T["questions"] = (
        "상담에서 함께 다루면 좋은 질문을 제안해 드립니다.\n"
        "① 올해 집중할 한 가지는 무엇인가\n"
        "② 관계에서 지금 점검할 부분은 무엇인가\n"
        "③ 일·재물 결정에서 확인할 포인트는 무엇인가\n"
        "④ 다가오는 대운 전환기를 어떻게 준비할 것인가.\n"
        "이 질문들에 대한 답을 사주의 결과 함께 정리하면, 결과지의 내용을 "
        "실제 선택으로 옮기는 데 도움이 됩니다. 정답을 받기보다, 자신에게 "
        "맞는 질문을 다듬는 자리로 활용하시길 권합니다."
    )

    T["closing"] = (
        f"{nm_pfx}여기까지 함께 읽어 주셔서 감사합니다. 타고난 기운은 방향을 "
        f"보는 참고이지, 정해진 결말이 아닙니다. 같은 사주라도 선택과 노력, "
        f"환경에 따라 길은 충분히 달라질 수 있습니다. {nm_call}의 강점인 "
        f"{mx_ko} 기운({mx_mn})은 살리고, 옅은 {mn_ko} 기운은 작은 습관으로 "
        f"채워 가시길 바랍니다. 이 결과지가 스스로를 차분히 이해하고 다음 "
        f"걸음을 고르게 내딛는 계기가 되면 좋겠습니다. 자신을 너무 단정하지 "
        f"마시고, 흐름을 읽는 지도처럼 곁에 두고 활용하시면 좋겠습니다."
    )

    T["appendix_terms"] = (
        "이 부록은 본문에 나온 전문 용어를 한곳에 모아 쉬운 말로 풀이한 "
        "참고 자료입니다. 읽다가 막히면 여기를 펼쳐 보세요.\n"
        "· 사주팔자: 태어난 연·월·일·시를 각각 천간과 지지 두 글자로 적은 "
        "여덟 글자. 인생을 읽는 기본 좌표입니다.\n"
        "· 천간(天干): 하늘의 기운을 나타내는 열 글자. 겉으로 드러나는 성향의 결.\n"
        "· 지지(地支): 땅의 기운을 나타내는 열두 글자. 환경과 바탕의 결.\n"
        "· 일간(日干): 태어난 날의 천간으로, 나 자신을 상징하는 중심 글자.\n"
        "· 지장간(支藏干): 지지 속에 숨어 있는 천간. 겉으로 안 보이는 속기운.\n"
        "· 오행(五行): 목·화·토·금·수 다섯 기운. 강약의 균형을 봅니다.\n"
        "· 십성(十星): 일간을 기준으로 다른 글자가 맺는 관계의 작용. 비겁·"
        "식상·재성·관성·인성 다섯 갈래로, 일과 관계의 방식을 읽는 단서.\n"
        "· 십이운성(十二運星): 기운이 자라고 무르익고 정리되는 열두 단계를 "
        "가리키는 참고 지표입니다.\n"
        "· 납음(納音): 간지 조합에 붙는 오행의 상징적 표현.\n"
        "· 대운(大運): 약 10년 단위로 흐르는 큰 시기의 결.\n"
        "· 자미두수 명반: 12궁(자리)에 별을 배치해 인생의 구조를 보는 그림.\n"
        "· 명궁·신궁: 타고난 기본 바탕(명궁)과 살아가며 힘이 실리는 자리"
        "(신궁)를 보는 핵심 자리입니다.\n"
        "· 사화(四化): 별에 붙는 화록·화권·화과·화기 네 가지 변화의 신호.\n"
        "· 오행국(五行局): 자미두수 명반 해석의 토대가 되는 분류입니다.\n"
        "모든 용어는 좋고 나쁨의 단정이 아니라, 자신을 이해하는 참고 틀로 "
        "보시길 권합니다."
    )

    # 감수 명시형 고지(절대규칙 18) 유지. 운영자 지시(2026-06-12)로
    # '참고용 상담 자료'·'전문가와 상의' 류 책임회피 문구는 PDF에서 제거.
    T["next"] = (
        "이 자료는 자동 분석 도구로 사주와 자미두수를 산출하고, 운영자가 처음부터 "
        "끝까지 직접 검수하고 감수하여 정리했습니다. 명리학과 자미두수는 오랜 세월 "
        "다듬어져 온 전통 해석 체계로, 타고난 결과 시기의 흐름을 읽습니다. "
        "같은 사주라도 선택과 노력, 환경에 따라 길은 충분히 달라질 수 있습니다."
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
    T["consult"] = (
        f"{nm_pfx}신청해 주신 고민은 '{_cc}' 영역에 닿아 있습니다. "
        f"이 결과지에서는 {_domain}이 그 답의 뼈대가 됩니다. "
        f"같은 기운도 상황과 선택에 따라 다르게 나타나니, 위 영역을 중심으로 "
        f"결과지를 읽어 보세요. 더 깊은 부분은 시점을 정해 상담에서 함께 볼 수 "
        f"있습니다."
    )

    # --- 주제별 챕터 조립 (2026-06-11 재편 1단계: 옛 섹션을 새 챕터 키로 병합) ---
    # 산문화·기호 제거는 2단계에서. 여기서는 키 정합만 맞춘다. toc 는 빌더가 생성.
    def _join(*keys: str) -> str:
        return "\n\n".join(T[k].strip() for k in keys if T.get(k, "").strip())

    NT: dict[str, str] = {
        "cover": T["cover"],
        "intro": _join("summary", "howto", "keywords"),
        "wonguk": _join("wonguk", "ohaeng"),
        "nature": _join("ilgan", "sipseong", "character", "strength"),
        "frame": _join("geukguk", "shinsal"),
        "love": T["love"],
        "work": _join("job", "wealth"),
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
