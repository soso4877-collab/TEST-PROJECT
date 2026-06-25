# -*- coding: utf-8 -*-
"""다인(多人) 사업 궁합 리포트 — 결정론 명식 사실 + 쌍별 관계 + 시기 겹침 → LLM 작성 → tagged PDF.

기존 1인 리포트와 별개 산출물(2026-06-14 운영자 실요청: 김태수·김태성·장순조 3인 사업 궁합).
계산은 전부 결정론(engine.build, partner_pillars 재사용 + 식신생재·재고 신규 탐지). LLM은 그 사실
슬롯만 근거로 작성하고, 3단 가드(safe_lint/style_lint/factcheck=3인 허용토큰 합집합)·반복 백스톱·
브랜드(서담선생)·가정어 가드를 그대로 적용한다. 예측 결과 보장 금지(절대규칙11), 시기는 연도 앵커.
"""

from __future__ import annotations

import os
import re
from types import SimpleNamespace

from . import config as cfg
from .calc import engine
from .calc import partner as calc_partner
from .content import (
    client_tone_lint,
    factcheck,
    masking,
    postprocess,
    quality_lint,
    repetition,
    rules,
    safe_lint,
    style_lint,
    temporal_lint,
    trace,
)
from .input import partner as input_partner
from .render import pdf as render_pdf
from .render import verify as render_verify

# .env 로드(ANTHROPIC_API_KEY) — pipeline 과 동일. 없으면 _compose 가 룰 폴백(무비용).
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    pass

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
_ELEM_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
# 간지 한글 변환(본문 한글 전용 — 1인 리포트와 동일 표기)
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


def _gz_ko(gz: str) -> str:
    """간지(한자) → 한글. '壬寅'→'임인', 단자도 변환."""
    return "".join(_GAN_KO.get(c) or _ZHI_KO.get(c) or c for c in gz)


_JAESEONG = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}  # 일간 → 재성 오행
_MYO = {"木": "未", "火": "戌", "土": "辰", "金": "丑", "水": "辰"}  # 오행 묘고 지지
# 십성 코드(myeongni 는 한자 코드 저장: 正财·食神·七杀 …) — 한자로 매칭
_SIKSANG = {"食神", "伤官", "傷官"}
_JAE = {"偏财", "正财", "偏財", "正財"}
_GWAN = {"七杀", "七殺", "正官", "偏官"}
_INSEONG = {"偏印", "正印"}
_BIGYEOP = {"比肩", "劫财", "劫財"}
_POSITION = {
    "재성": "영업·재무·현실 감각(돈의 흐름을 읽고 만드는 자리)",
    "관성": "관리·책임·조직 운영(틀을 세우고 지키는 자리)",
    "식상": "기획·생산·표현(생각을 결과물로 만드는 자리)",
    "인성": "전략·학습·기반(공부하고 설계하는 자리)",
    "비겁": "실행·추진·독립(앞에서 끌고 부딪치는 자리)",
}


def _all_shishen(m) -> list[str]:
    out: list[str] = []
    for p in (m.year, m.month, m.day, m.hour):
        if p.shishen_gan:
            out.append(p.shishen_gan)
        out.extend(p.shishen_zhi)
    return out


def _dominant_group(ss: list[str]) -> str:
    cnt = {"재성": 0, "관성": 0, "식상": 0, "인성": 0, "비겁": 0}
    for s in ss:
        if s in _JAE:
            cnt["재성"] += 1
        elif s in _GWAN:
            cnt["관성"] += 1
        elif s in _SIKSANG:
            cnt["식상"] += 1
        elif s in _INSEONG:
            cnt["인성"] += 1
        elif s in _BIGYEOP:
            cnt["비겁"] += 1
    return max(cnt, key=lambda k: cnt[k])


def _detect_patterns(m) -> dict:
    """결정론 명리 패턴 — 식신생재·재고. 학설 영역이라 '구조/경향' 라벨(단정 아님)."""
    ss = set(_all_shishen(m))
    branches = {m.year.zhi, m.month.zhi, m.day.zhi, m.hour.zhi}
    dm_elem = _GAN_ELEM.get(m.day_master, "")
    jae_elem = _JAESEONG.get(dm_elem, "")
    jaego_zhi = _MYO.get(jae_elem, "")
    return {
        "sik_saeng_jae": bool(ss & _SIKSANG) and bool(ss & _JAE),
        "jaego": bool(jaego_zhi) and jaego_zhi in branches,
        "jaego_zhi": jaego_zhi,
        "jae_elem_ko": _ELEM_KO.get(jae_elem, ""),
    }


def _favorable_years(m, span: int = 12) -> list[int]:
    """용신(억부 참고) 오행과 같은 천간 오행의 세운 해 = '호기' 참고(결정론, 단정 아님)."""
    yong = (m.yongshin_eokbu or "").strip()
    yong_elem = next((e for e, ko in _ELEM_KO.items() if yong.startswith(ko)), None)
    if not yong_elem:
        return []
    return [y for y, gz in m.seun[:span] if gz and _GAN_ELEM.get(gz[0]) == yong_elem]


def person_facts(name: str, birth: tuple, *, ref_year: int, is_male: bool = True) -> dict:
    y, mo, d, h, mi = birth
    # 성별은 대운 방향(양남음녀)을 좌우 → 하드코딩 금지(여성 참여 시 방향 오류 차단).
    saju = engine.build(y, mo, d, h, mi, is_male=is_male, horoscope_date=f"{ref_year}-06-13")
    m = saju.myeongni
    dom = _dominant_group(_all_shishen(m))
    return {
        "name": name,
        "birth": birth,
        "saju": saju,
        "m": m,
        "bazi": f"{m.year.ganzhi} {m.month.ganzhi} {m.day.ganzhi} {m.hour.ganzhi}",
        "ilju": m.day.ganzhi,
        "day_master": m.day_master,
        "singang": m.singang,
        "geukguk": m.geukguk,
        "yongshin": m.yongshin_eokbu,
        "elements": dict(m.elements),
        "dominant": dom,
        "position": _POSITION[dom],
        "patterns": _detect_patterns(m),
        "favorable_years": _favorable_years(m),
    }


def pair_facts(a: dict, b: dict):
    """a 기준 b와의 관계(십성·천간합·일지 육합/충·삼합·오행 보완)."""
    by, bmo, bd, bh, bmi = b["birth"]
    am = a["m"]
    return calc_partner.partner_pillars(
        by,
        bmo,
        bd,
        bh,
        bmi,
        my_day_gan=am.day_master,
        my_day_zhi=am.day.zhi,
        my_elements=dict(am.elements),
        my_yongshin=am.yongshin_eokbu,
    )


# ───────────────── 사실 슬롯(LLM 근거) ─────────────────


# H1.5 자연화 — 전문용어는 첫 1회 자연어 풀이 + 괄호 병기, 원시 카운트는 본문에서 제외.
_ELEM_MEAN_G = {"木": "성장", "火": "표현", "土": "안정", "金": "결단", "水": "회복"}
_SINGANG_PHRASE = {
    "신강": "스스로 버티는 힘이 강한",
    "신약": "혼자 밀기보다 환경과 사람을 잘 만날 때 힘이 나는",
    "중화": "힘이 한쪽으로 치우치지 않고 고른",
}
_GEOK_PHRASE = {
    "편관격": "압박 속에서 힘이 드러나는 쪽",
    "정관격": "틀과 책임 안에서 힘이 서는 쪽",
    "편재격": "넓게 벌이고 굴리는 쪽",
    "정재격": "꾸준히 모으고 지키는 쪽",
    "식신격": "만들고 표현하며 풀리는 쪽",
    "상관격": "재능을 드러내며 앞서가는 쪽",
    "건록격": "제 힘으로 버티고 끌고 가는 쪽",
    "양인격": "강한 추진력으로 밀고 가는 쪽",
    "정인격": "배우고 받쳐 주는 힘으로 서는 쪽",
    "편인격": "남다른 시선과 궁리로 서는 쪽",
}
_YONG_DIR = {
    "목": "성장과 시작",
    "화": "표현과 추진",
    "토": "안정과 중심",
    "금": "결단과 정리",
    "수": "회복과 유연함",
}
_DOMINANT_PHRASE = {
    "재성": "재물을 다루고 만드는 힘",
    "관성": "틀을 세우고 지키는 힘",
    "식상": "기획하고 표현하는 힘",
    "인성": "배우고 설계하는 힘",
    "비겁": "앞에서 끌고 가는 힘",
}


def _elements_natural(elements: dict) -> str:
    """오행 분포를 수치 없이 자연어로 — 강한 기운/옅은 기운만(원시 카운트 본문 제외)."""
    if not elements:
        return "다섯 기운이 비교적 고른 편"
    mx, mn = max(elements.values()), min(elements.values())
    strong = "·".join(_ELEM_MEAN_G.get(k, k) for k, v in elements.items() if v == mx)
    weak = "·".join(_ELEM_MEAN_G.get(k, k) for k, v in elements.items() if v == mn)
    if mx == mn:
        return "다섯 기운이 비교적 고르게 놓인 편"
    return f"{strong}의 힘이 강하고, {weak}의 힘은 조금 더 챙기면 좋은 편"


def _person_slot(p: dict) -> str:
    pat = p["patterns"]
    bazi_ko = " ".join(_gz_ko(g) for g in p["bazi"].split())
    geok = (p["geukguk"] or "").split("(")[0]
    yong = (p["yongshin"] or "").strip()
    yong_dir = _YONG_DIR.get(yong[:1], "")
    parts = [
        f"{client_tone_lint.intro(p['name'])}: 사주팔자 {bazi_ko}, {_gz_ko(p['ilju'])}일주(일간 {_GAN_KO.get(p['day_master'], p['day_master'])}).",
        # 신강약·격국·용신은 자연어로 풀고 첫 1회만 괄호 병기(전문용어 정책).
        f"{_SINGANG_PHRASE.get(p['singang'], '고유한 힘의 결을 지닌')} 사주({p['singang']})."
        + (f" 사주의 큰 틀은 {_GEOK_PHRASE[geok]}입니다({geok})." if geok in _GEOK_PHRASE else ""),
        f"다섯 기운은 {_elements_natural(p['elements'])}."
        + (f" 보완하면 좋은 방향은 {yong_dir}의 힘입니다." if yong_dir else ""),
        f"특히 살아나는 결은 {_DOMINANT_PHRASE.get(p['dominant'], p['dominant'])}이라, "
        f"어울리는 자리는 {p['position']}.",
    ]
    if pat["sik_saeng_jae"]:
        parts.append(
            "식신생재(식상에서 재성으로 이어지는) 구조가 있어, 만들고 표현한 것이 재물로 이어지는 결이 있다(구조/경향)."
        )
    if pat["jaego"]:
        parts.append(
            f"재고(재성 {pat['jae_elem_ko']}의 묘고 지지 {_ZHI_KO.get(pat['jaego_zhi'], pat['jaego_zhi'])}) 보유 "
            "— 재물을 모으고 쌓는 창고의 결(구조/경향)."
        )
    fy = p["favorable_years"]
    if fy:
        parts.append(
            f"용신({p['yongshin']}) 기준 세운 호기 해: {', '.join(map(str, fy))} (참고, 단정 아님)."
        )
    return " ".join(parts)


_REL_KO = {"육합": "끌림·합이 잘 맞는", "충": "부딪침·자극이 있는"}
_SS_KO = {
    "比肩": "비견",
    "劫財": "겁재",
    "劫财": "겁재",
    "食神": "식신",
    "傷官": "상관",
    "伤官": "상관",
    "偏財": "편재",
    "偏财": "편재",
    "正財": "정재",
    "正财": "정재",
    "七殺": "칠살(편관)",
    "七杀": "칠살(편관)",
    "正官": "정관",
    "偏印": "편인",
    "正印": "정인",
}


def _pair_slot(a: dict, b: dict) -> str:
    pf = pair_facts(a, b)
    ha, hb = client_tone_lint.honor(a["name"]), client_tone_lint.honor(b["name"])
    bits = [f"{client_tone_lint.pair_label(a['name'], b['name'])}:"]
    if pf.shishen_to_me:
        bits.append(f"{ha} 기준 {hb}는 십성으로 {_SS_KO.get(pf.shishen_to_me, pf.shishen_to_me)}.")
    if pf.gan_hap:
        bits.append(f"일간 천간합({pf.gan_hap}) — 결이 묶이는 끌림.")
    if pf.ilji_relation:
        bits.append(f"일지 {pf.ilji_relation}({_REL_KO.get(pf.ilji_relation, '')}) 관계.")
    if pf.ilji_banhap:
        bits.append(f"일지 삼합 반합({pf.ilji_banhap}) — 같은 방향으로 모이는 협업의 결.")
    if pf.complements_elems_ko:
        bits.append(f"{hb}가 {ha}의 부족 오행({', '.join(pf.complements_elems_ko)})을 보완.")
    if len(bits) == 1:
        bits.append("두드러진 합·충·반합은 약한 편(무난·중립).")
    return " ".join(bits)


def _palace_stars(zw, palace_name: str) -> str:
    palace = next((p for p in zw.palaces if p.name == palace_name), None)
    if not palace:
        return f"{palace_name}의 큰 별은 약하게 보입니다"
    stars = ", ".join(s.name for s in palace.major_stars[:2]) or "주성이 약한 자리"
    return f"{palace_name}은 {stars}가 놓인 자리"


def _ziwei_slot(people: list[dict]) -> str:
    lines = [
        "자미두수는 사람과 관계가 밖에서 드러나는 모습, 돈을 다루는 방식, 일과 생활의 자리를 함께 봅니다."
    ]
    for p in people:
        zw = p["saju"].ziwei
        honor = client_tone_lint.honor(p["name"])
        lines.append(
            f"{honor} 자미두수 명궁은 {zw.soul_palace}, 신궁은 {zw.body_palace}입니다. "
            f"{_palace_stars(zw, '부처궁')}라 가까운 관계에서는 말보다 태도와 생활의 반복이 중요합니다. "
            f"{_palace_stars(zw, '재백궁')}라 돈과 재산을 다루는 방식도 관계의 안정감에 영향을 줍니다. "
            f"{_palace_stars(zw, '관록궁')}라 일과 역할을 어떻게 감당하는지도 두 사람의 관계 지속성을 봅니다."
        )
    return "\n".join(lines)


def _join_years(years: list[int]) -> str:
    """[2026, 2027] → '2026년과 2027년' (고객용 자연 표기)."""
    labels = [f"{y}년" for y in years]
    if len(labels) <= 1:
        return labels[0] if labels else ""
    return ", ".join(labels[:-1]) + "과 " + labels[-1]


def _timing_slot(people: list[dict]) -> str:
    """세운 호기 해를 고객용 자연문으로 — 내부 메모형 표현 없이(폴백돼도 상품 품질, H1.5.2-final).

    계산값(favorable_years)은 그대로 쓰되 '호기 해/용신 기준 참고/뚜렷한 해 적음' 같은
    내부 표기를 쓰지 않고, 흐름·역할 중심의 자연 문장으로 푼다.
    """
    sets = [set(p["favorable_years"]) for p in people if p["favorable_years"]]
    common = sorted(set.intersection(*sets)) if len(sets) == len(people) and sets else []
    parts = [
        "세 사람의 때는 한 해에 다 같이 확 열리는 구조라기보다, "
        "각자의 흐름이 조금씩 어긋나며 서로를 받쳐 주는 구조입니다."
    ]
    for p in people:
        ys = p["favorable_years"]
        nm = rules._J(client_tone_lint.honor(p["name"]), "은는")  # 호칭 + 받침 는(태수 씨는)
        if ys:
            parts.append(f"{nm} {_join_years(ys)}에 흐름이 살아나는 시기예요.")
        else:
            parts.append(
                f"{nm} 어느 한 해가 특별히 도드라지기보다, "
                "곁에서 꾸준히 흐름을 받쳐 주는 자리입니다."
            )
    if common:
        parts.append(
            f"세 사람의 흐름이 함께 맞물리는 때는 {_join_years(common)}이니, "
            "그 시기에 역할을 모으면 좋습니다."
        )
    else:
        parts.append(
            "세 사람이 같은 해에 한꺼번에 피는 방식은 아니지만, "
            "오히려 그 어긋남이 각자의 역할을 더 분명하게 나눠 줍니다."
        )
    return " ".join(parts)


# ───────────────── compose(궁합 전용) ─────────────────

_GH_SYSTEM = (
    "너는 20년 넘게 사람을 마주해 온 사주 상담가다. 지금 함께 일하는 세 사람의 명식을 앞에 두고, "
    "사업 궁합을 그들에게 직접 말하듯 쓴다. 따뜻하지만 분명하게, 정면으로.\n\n"
    "[형식] 한 호흡(한두 문장) 쓰고 줄을 바꾼다. 의미가 바뀌면 빈 줄. 같은 문형 반복 금지.\n"
    "[말투] '~예요/~해요'와 '~합니다'를 자연스럽게 섞는다. '당신' 금지.\n"
    "[호칭] 표지·근거표만 전체 이름. 본문은 각 사람 첫 소개에서만 '김태수 씨/김태성 씨/장순조 씨'처럼 "
    "성 포함 1회 쓰고, 이후로는 '태수 씨/태성 씨/순조 씨'로 부른다. 둘씩 볼 때는 '태수와 태성/태수와 순조/"
    "태성과 순조'. '김태수는·김태성은·장순조는'처럼 성 포함 전체 이름+조사를 반복하지 마라.\n"
    "[일간] 각 사람의 일간(중심 글자)은 명식에 정해진 하나뿐이다. 근거 자료에 적힌 그 사람의 일간만 쓰고, "
    "다른 천간을 그 사람의 일간/중심 글자로 바꿔 쓰지 마라.\n"
    "[신강약] 신강·신약은 사람마다 다른 결정론 사실이다. 근거 슬롯에 적힌 각자의 값만 쓰고, 세 사람의 "
    "신강약이 모두 같다고 일반화하지 마라('세 사람 모두 신약/신강' 금지). 값이 섞여 있으면 신약인 사람과 "
    "신강인 사람을 나눠서 말하라.\n"
    "[단정] 계산된 사실(간지·십성·격국·식신생재·재고·세운 연도)은 분명하게. 얼버무리지 마라.\n"
    "[시기] 시기는 연도로 말한다('2027년에는'). '약 N세 전후', '~쯤', '~라면' 같은 가정어 금지. "
    "다만 그 해에 일어날 결과 자체는 보장하지 않는다(흐름·준비의 관점).\n"
    "[금지] 근거 자료에 없는 간지·별·수치 생성 금지. 시적 수사·기호 남발 금지. 같은 말 반복 금지.\n"
    "[우리말] 고객용 글이다. 외래어를 쓰지 마라 — 포지션→자리/역할, 리스크→위험/부담, 시스템→체계/틀, "
    "드라이브→추진력, 드라이버→주도하는 사람, 브레이크→속도 조절, 에너지→기운/힘, 파트너→동업자, "
    "팀→세 사람/이 조합, 프로젝트→일/판, 타입→성향, 패턴→되풀이되는 흐름, 컨디션→몸 상태. "
    "'오행 분포'·'오행의 분포'·'십성축'·'신강약' 같은 계산표 용어와 '목 2, 화 2' 같은 숫자 나열은 본문에 쓰지 말고, "
    "전문용어(신약·편관격·용신 등)는 쉬운 말로 풀고 필요하면 괄호 안에 한 번만 둔다.\n"
    "[관점] 좋고 나쁨이 아니라 쓰임과 맡을 자리로. 강점을 먼저, 보완은 그 뒤에. 셋이 어떻게 역할을 나누면 "
    "유리한지 구체적으로.\n"
)

_GH_SECTIONS = [
    ("overview", "세 사람, 그리고 지금의 자리"),
    ("each", "각자의 결 — 성향과 맡을 자리"),
    ("pairs", "둘씩 마주 보면 — 서로의 궁합"),
    ("business", "사업으로 묶일 때 — 역할"),
    ("timing", "언제 풀리는가 — 세 사람의 때"),
]

_GH_GUIDE = {
    "overview": "세 사람이 누구인지 사주팔자와 일주로 각자를 짧게 소개하고, 지금 상황(아래 맥락)을 공감으로 짚는다.",
    "each": "세 사람 각각의 성향·능력·격국·식신생재/재고를 구체적으로 풀고, 어울리는 자리를 분명히 권한다.",
    "pairs": "세 쌍(태수와 태성, 태수와 순조, 태성과 순조)의 궁합을 천간합·일지 육합/충·삼합·오행 보완으로 직설로 푼다.",
    "business": "셋이 사업으로 묶일 때 누가 어떤 역할(총괄·실행·지원)을 맡으면 유리한지, 서로의 부족을 어떻게 메우는지 구체적으로.",
    "timing": "각자 언제 흐름이 풀리는지(세운 연도)와 세 사람의 때가 비슷하게 겹치는지(꽃피우는 시기)를 연도로 말한다.",
}

_REL_SYSTEM = (
    "너는 오래 상담해 온 사주 상담가다. 두 사람의 명식과 질문을 보고, 고객에게 직접 답한다. "
    "명리 판단은 분명하게 말하되 결과를 보장하지 않는다.\n\n"
    "[말투] '~예요/~해요' 중심의 자연스러운 존댓말. '~편이다/~한다/~이다' 보고서체를 피한다.\n"
    "[질문] 상대의 진심, 대화와 갈등, 성격·가치관·연애관, 좋은 영향, 안정성, 앞으로 1년의 판단 기준을 빠뜨리지 않는다.\n"
    "[행동] 고백보다 반복 태도, 약속 이행, 갈등 뒤 회복, 주변 관계에 자연스럽게 놓는지를 구체 기준으로 쓴다.\n"
    "[금지] 홍보 문구, 링크 안내, 장식 이모지, AI/도구 고지, 사주도령 서명 반복 금지.\n"
    "[분량] 각 장은 짧은 표어로 끝내지 않고 최소 세 문장 이상으로 판단 기준과 실제 행동을 함께 쓴다.\n"
)

_REL_SECTIONS = [
    ("overview", "두 사람의 큰 흐름"),
    ("intent", "상대의 진심과 표현 방식"),
    ("conflict", "대화와 갈등이 생길 때"),
    ("values", "성격과 가치관, 연애관"),
    ("ziwei_relation", "자미두수로 보는 관계의 자리"),
    ("chemistry", "끌림과 맞물림"),
    ("daily", "일상에서 맞는 부분과 다른 부분"),
    ("social", "주변 사람과 관계를 놓는 방식"),
    ("pace", "관계 속도와 확인 방식"),
    ("risk", "주의해야 할 장면"),
    ("stability", "안정적으로 이어갈 수 있는가"),
    ("action", "지금 다가가는 방식"),
    ("timing", "앞으로 1년의 흐름"),
    ("decision", "지금 확인해야 할 기준"),
]

_REL_GUIDE = {
    "overview": "두 사람의 명식 큰 결을 먼저 말하고, 지금 질문의 핵심을 정리한다.",
    "intent": "상대의 마음을 말이 아니라 반복 태도와 약속 이행으로 확인하는 기준을 적는다.",
    "conflict": "대화 속도와 갈등 회복 방식의 차이를 설명하고, 부딪힐 때의 실제 대응을 제안한다.",
    "values": "성격, 생활 기준, 가치관, 연애관이 맞는 지점과 조심할 지점을 분명히 나눈다.",
    "ziwei_relation": "자미두수 명궁·신궁·부처궁·재백궁·관록궁을 관계의 사람·돈·일·생활 축과 연결한다.",
    "chemistry": "끌림이 생기는 이유와 실제로 맞물리는 지점을 명리와 관계 행동으로 설명한다.",
    "daily": "연락, 약속, 생활 리듬, 말투처럼 일상에서 맞거나 어긋날 부분을 쓴다.",
    "social": "학교, 전공, 겹지인, 주변에 관계를 자연스럽게 놓는 방식이 왜 중요한지 쓴다.",
    "pace": "한쪽은 확인이 빠르고 한쪽은 살피는 속도가 느릴 때 어떻게 맞추는지 쓴다.",
    "risk": "관계가 흔들릴 수 있는 장면과 미리 조심할 기준을 쓴다.",
    "stability": "서로에게 좋은 영향이 되는 조건과 안정 관계로 가는 조건을 쓴다.",
    "action": "지금 먼저 보낼 말, 만남을 여는 방식, 부담을 줄이는 접근 순서를 제안한다.",
    "timing": "앞으로 1년을 중심으로 성급히 밀어붙일 때와 확인할 때를 나누어 말한다.",
    "decision": "고백이나 확답보다 먼저 볼 기준, 물러설 기준, 다음 연락 방식을 제시한다.",
}

_REL_TAIL_FILLERS = {
    "overview": "가장 중요한 기준은 감정의 세기보다 두 사람이 같은 방향을 보려는 태도예요. 좋아하는 마음이 있어도 생활 속 약속이 따라오지 않으면 관계는 쉽게 흔들립니다. 반대로 말이 조금 느려도 약속과 회복이 반복되면 이어갈 힘은 충분히 생겨요.",
    "intent": "진심은 큰말보다 작은 행동에서 먼저 드러나요. 먼저 연락이 늦어져도 다시 설명하고, 약속이 바뀌면 이유를 말하고, 불편한 이야기를 피하지 않는지가 중요합니다. 이 세 가지가 반복되면 마음을 조금 더 믿어도 좋아요.",
    "conflict": "갈등이 생겼을 때 바로 결론을 요구하면 상대가 더 닫힐 수 있어요. 대신 언제 다시 이야기할지, 무엇을 먼저 고칠지, 서로 어떤 말은 피할지를 정해두는 편이 낫습니다. 이 방식이 잡히면 다툼이 관계를 끝내는 일이 아니라 조율하는 과정이 됩니다.",
    "values": "가치관은 거창한 선언보다 생활 기준에서 확인됩니다. 돈을 쓰는 방식, 시간을 지키는 태도, 주변 사람을 대하는 말, 연애를 공개적으로 놓는 속도를 보면 두 사람이 실제로 맞는지 보입니다. 여기서 무리하게 맞추기보다 지킬 수 있는 기준을 고르는 게 좋아요.",
    "ziwei_relation": "자미두수로 볼 때도 관계는 마음 하나만으로 보지 않습니다. 사람을 대하는 자리, 돈과 생활을 다루는 자리, 밖에서 관계가 드러나는 자리가 함께 맞아야 오래 갑니다. 그래서 지금은 설렘만 보지 말고 생활과 주변 관계 안에서 자연스럽게 놓이는지를 같이 보세요.",
    "chemistry": "끌림은 시작을 만들지만 지속은 반복이 만듭니다. 서로에게 끌리는 이유가 있어도 말의 속도와 생활 기준이 맞지 않으면 자주 서운해질 수 있어요. 그래서 지금은 더 깊이 들어가기 전에 서로가 편하게 지킬 수 있는 약속부터 작게 확인하는 편이 안전합니다.",
    "daily": "일상에서는 연락 횟수보다 연락이 끊긴 뒤의 설명이 더 중요해요. 바쁜 날에도 짧게라도 이유를 말하는지, 약속을 미루면 다시 잡는지, 기분이 상한 뒤에도 대화를 회복하는지를 보세요. 이런 부분이 맞으면 관계가 훨씬 안정됩니다.",
    "social": "겹지인과 학교, 전공의 맥락이 있는 관계는 소문보다 자연스러운 태도가 중요합니다. 둘만 있을 때 다정해도 주변에서는 어색하게 숨기면 불안이 커져요. 급히 공개하라는 뜻은 아니지만, 서로를 곤란하게 만들지 않는 방식으로 관계를 놓을 수 있어야 합니다.",
    "pace": "속도가 다르면 마음이 없는 것처럼 느껴질 수 있지만, 실제로는 확인 방식이 다른 경우가 많아요. 한쪽은 말로 확인하고 싶고, 한쪽은 상황을 본 뒤 움직이려 할 수 있습니다. 그래서 질문은 짧게, 기준은 분명하게, 기다리는 시간은 정해두는 게 좋습니다.",
    "risk": "주의할 점은 감정이 올라왔을 때 바로 확답을 요구하는 흐름이에요. 상대가 대답을 미루면 가현 씨는 더 불안해지고, 그 불안이 다시 상대를 밀어붙이는 모양이 될 수 있습니다. 이때는 감정을 숨기기보다 한 번만 분명히 말하고, 이후 행동을 보는 쪽이 낫습니다.",
    "stability": "안정적인 관계가 되려면 둘 다 편한 방식만 고집하면 안 됩니다. 가현 씨는 확인을 조금 줄이고, 상철 씨는 설명을 조금 늘려야 균형이 맞아요. 이 조율이 실제로 가능하면 두 사람은 서로에게 좋은 영향을 줄 수 있습니다.",
    "action": "지금 다가갈 때는 무거운 고백보다 가벼운 안부가 먼저 좋아요. 학교나 전공, 겹지인처럼 자연스러운 접점을 이용하되 상대를 시험하는 말은 피하세요. 짧은 만남을 만들고, 그 뒤 약속을 다시 잡는지 보는 것이 가장 현실적인 확인입니다.",
    "timing": "앞으로 1년은 한 번에 결론을 내기보다 몇 번의 확인으로 나누어 보는 편이 좋아요. 올해 안에는 상대가 불편한 대화 뒤에도 돌아오는지를 보고, 내년 초에는 관계를 더 분명히 놓을 수 있는지 보세요. 시기를 이렇게 나누면 마음을 덜 소모합니다.",
    "decision": "마지막 판단은 상대가 얼마나 달콤하게 말했는지가 아니라 같은 행동을 반복하는지예요. 연락, 약속, 갈등 뒤 회복, 주변 관계에서의 태도가 일정하면 이어갈 수 있습니다. 그 네 가지가 계속 흐려지면 마음이 있어도 안정적인 관계로 가기 어렵습니다.",
}


_LLM_SIGNATURE_LINE_RX = re.compile(
    r"(?m)^\s*(?:[*_~\s]*)(?:[🔮🌙🪄🌿]\s*)?(?:사주도령|서담선생)"
    r"(?:\s*[|·-]\s*(?:연애|썸|재회|결혼|궁합|전문|상담)[^\n]*)?(?:[*_~\s]*)$"
)
_LLM_TRAILING_SIGNATURE_RX = re.compile(
    r"\s*(?:[*_~\s]*)(?:[🔮🌙🪄🌿]\s*)?(?:사주도령|서담선생)(?:\s*궁합\s*풀이)?(?:[*_~\s]*)\s*$"
)
_LLM_DECORATIVE_CLOSING_RX = re.compile(r"(?m)^\s*두\s*분의\s*관계,\s*응원합니다\.?\s*[🌿]?\s*$")
_LLM_PROMO_CTA_RX = re.compile(
    r"(?m)^\s*(?:[🔮🌙🪄🌿]\s*)?(?:(?:사주도령|서담선생)\s*(?:전문\s*)?(?:상담|궁합\s*상담)"
    r"|더\s*깊은\s*(?:궁합|해석|풀이|시기별\s*흐름).*(?:확인|신청|상담)"
    r"|.*(?:아래\s*)?링크.*)\s*$"
)
_LLM_INTERNAL_META_RX = re.compile(
    r"(?m)^\s*(?:고객\s*질문|상담\s*대상)\s*:.*$"
    r"|^\s*\[(?:각자\s*명식|두\s*사람\s*관계|자미두수|시기)\]\s*$"
    r"|^\s*근거\s*자료.*$"
)
_DECORATIVE_EMOJI_RX = re.compile(r"[🔮🌙🪄🌿✦★☆]")
_REPORT_ENDING_REPLACEMENTS = (
    ("해야 한다.", "해야 해요."),
    ("해야 한다", "해야 해요"),
    ("세운다.", "세우는 게 좋아요."),
    ("세운다", "세우는 게 좋아요"),
    ("움직인다.", "움직이는 편이 좋아요."),
    ("움직인다", "움직이는 편이 좋아요"),
    ("본다.", "보면 좋아요."),
    ("본다", "보면 좋아요"),
    ("아니다.", "아니에요."),
    ("아니다", "아니에요"),
    ("뜻이다.", "뜻이에요."),
    ("뜻이다", "뜻이에요"),
    ("때다.", "때예요."),
    ("때다", "때예요"),
)


def _strip_llm_signature_lines(text: str) -> str:
    text = _LLM_SIGNATURE_LINE_RX.sub("", text)
    text = _LLM_PROMO_CTA_RX.sub("", text)
    text = _LLM_INTERNAL_META_RX.sub("", text)
    text = _LLM_DECORATIVE_CLOSING_RX.sub("", text)
    lines = []
    for line in text.splitlines():
        lines.append(_LLM_TRAILING_SIGNATURE_RX.sub("", line).rstrip())
    return "\n".join(lines)


def _normalize_customer_body_terms(text: str) -> str:
    replacements = {
        "이 풀이에서는": "이 기준으로는",
        "이 풀이에서": "이 기준에서",
        "이 풀이를": "이 기준을",
        "이 풀이": "이 기준",
        "이 자료에서는": "이 글에서는",
        "이 자료는": "이 글은",
        "이 장에서 가장 중요한 기준은": "가장 중요한 기준은",
        "이 장에서": "여기서",
        "관계의 자리": "관계의 방향",
        "단체 자리": "여러 사람이 함께 있는 만남",
        "작은 자리": "가벼운 안부 자리",
        "거리를 재고": "거리를 살피고",
        "상황을 재고": "상황을 살피고",
        "한 번 더 재고 나서야": "한 번 더 생각하고 나서야",
        "먼저 재고": "먼저 살피고",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("안정되아", "안정되어")
    return text


def _soften_report_style_endings(text: str) -> str:
    for old, new in _REPORT_ENDING_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def _normalize_gunghap_honorifics(text: str, full_names: list[str]) -> str:
    """Keep customer body honorifics consistent: given-name + 씨, not mixed 님/씨."""
    for full in full_names:
        given = client_tone_lint.given_name(full)
        if not given:
            continue
        for stem in {full, given}:
            text = re.sub(
                rf"{re.escape(stem)}\s*님(?=(?:\s|은|는|이|가|을|를|에게|한테|께|과|와|도|만|의|,|\.|$))",
                f"{given} 씨",
                text,
            )
    return text


def _relationship_layout_variants(llm_active: bool) -> list[tuple[str, str]]:
    if not llm_active:
        return [("14.5pt", "1.8")]
    return [
        ("13.8pt", "1.68"),
        ("13.6pt", "1.64"),
        ("13.4pt", "1.60"),
        ("13.2pt", "1.56"),
        ("13.0pt", "1.52"),
        ("12.8pt", "1.48"),
    ]


def _only_low_density_failure(v: dict) -> bool:
    dq = v.get("delivery_quality") or {}
    failures = dq.get("failures") or []
    if not failures or any(f.get("rule") != "premium_low_density_pages" for f in failures):
        return False
    return all(
        bool(v.get(k, True))
        for k in (
            "text_layer_ok",
            "fonts_embedded",
            "tagged",
            "markdown_clean",
            "daewoon_consistent",
            "quality_clean",
            "temporal_clean",
            "loanword_clean",
            "raw_calc_head_clean",
            "name_policy_clean",
            "identity_role_clean",
            "singang_role_clean",
        )
    )


def _relationship_slot(section_id: str, people: list[dict], persons_txt: str, pairs_txt: str, timing_txt: str, situation: str) -> str:
    names = [client_tone_lint.honor(p["name"]) for p in people]
    unknown = [client_tone_lint.honor(p["name"]) for p in people if p.get("unknown_time")]
    unknown_note = (
        "출생시각은 미상인 사람이 있어 세부 기질은 단정하지 않고 큰 성향과 관계 흐름 위주로 봅니다."
        if unknown
        else "두 사람의 출생시각을 기준으로 큰 흐름과 세부 기질을 함께 봅니다."
    )
    ziwei_txt = _ziwei_slot(people)
    shared = (
        f"{unknown_note}\n\n"
        f"두 사람을 함께 보면 다음 명식 근거가 먼저 보입니다.\n{persons_txt}\n\n"
        f"두 사람 사이에서 실제로 맞물리는 부분은 다음과 같습니다.\n{pairs_txt}\n\n"
        f"자미두수로는 사람과 관계, 돈과 생활, 일의 자리를 함께 봅니다.\n{ziwei_txt}\n\n"
        f"시기 흐름은 다음처럼 나누어 봅니다.\n{timing_txt}"
    )
    focus = {
        "overview": "먼저 두 사람의 전체 궁합과 현재 질문의 핵심을 답합니다.",
        "intent": "상대의 진심은 말보다 약속 이행, 대화 회복, 주변 관계에 자연스럽게 놓는지로 봅니다.",
        "conflict": "갈등은 마음의 크기보다 표현 속도와 회복 방식의 차이로 봅니다.",
        "values": "성격, 가치관, 연애관은 생활 기준과 관계 기준이 맞는지로 풉니다.",
        "ziwei_relation": "자미두수에서는 사람과 관계, 돈, 일, 생활의 자리가 어떻게 관계 안정에 이어지는지 봅니다.",
        "chemistry": "서로 끌리는 지점과 실제로 맞물리는 지점은 따로 봅니다.",
        "daily": "일상에서는 연락, 약속, 생활 리듬, 말의 속도를 봅니다.",
        "social": "겹지인, 학교, 전공처럼 주변에 관계가 놓이는 방식도 안정성을 봅니다.",
        "pace": "관계 속도와 확인 방식이 다르면 마음이 있어도 오해가 생길 수 있습니다.",
        "risk": "주의할 장면은 말이 끊길 때, 약속이 밀릴 때, 갈등 뒤 회복이 늦을 때입니다.",
        "stability": "서로에게 좋은 영향이 되는 조건과 안정적으로 이어갈 조건을 봅니다.",
        "action": "지금 다가가는 방식은 부담을 줄이고 확인할 기준을 세우는 쪽으로 봅니다.",
        "timing": "앞으로 1년 안에서 서두를 때와 확인할 때를 나누어 봅니다.",
        "decision": "지금 다가가는 방식, 확인해야 할 기준, 물러설 기준을 제시합니다.",
    }
    return f"{focus.get(section_id, '')}\n\n{shared}"


def _relationship_fallback(section_id: str, people: list[dict], situation: str) -> str:
    """Relationship-mode fallback shown to customers when LLM output is rejected.

    The LLM prompt still receives the deterministic fact slot, but the PDF must never fall
    back to raw fact labels such as "십성", "일지 삼합", "명궁은 명궁", or prompt metadata.
    """
    honors = [client_tone_lint.honor(p["name"]) for p in people]
    a = honors[0] if honors else "한쪽"
    b = honors[1] if len(honors) > 1 else "상대"
    unknown_note = (
        f"{b}는 출생시각은 미상이라 세부 기질은 단정하지 않고, 큰 성향과 관계에서 드러나는 태도 위주로 봅니다. "
        if any(p.get("unknown_time") for p in people)
        else ""
    )
    common_open = (
        f"{a}와 {b}는 호감이 생길 수 있는 감각은 있으나, 관계를 안정적으로 이어가려면 말보다 반복되는 태도를 먼저 봐야 합니다. "
        f"{unknown_note}"
    )
    texts = {
        "overview": (
            common_open +
            "이 궁합은 처음부터 안 맞는 쪽이라기보다, 서로 마음을 확인하는 속도와 갈등 뒤 회복 방식이 달라 조율이 필요한 쪽입니다. "
            "좋아하는 마음이 있어도 약속이 흐려지거나 불편한 이야기를 계속 피하면 불안이 커질 수 있어요. "
            "반대로 연락이 늦어도 이유를 말하고, 약속을 다시 잡고, 주변 관계 안에서도 자연스럽게 배려한다면 이어갈 힘은 충분히 있습니다."
        ),
        "intent": (
            f"{b}의 진심은 고백의 크기보다 작은 행동에서 먼저 보세요. "
            "바쁜 날에도 이유를 설명하는지, 약속이 바뀌면 다시 맞추는지, 갈등 뒤에 대화를 회복하려는지, "
            "그리고 둘의 관계를 주변 사람들 앞에서 지나치게 숨기지 않는지가 기준입니다. "
            "다정한 말은 있는데 이 네 가지가 반복되지 않으면 아직은 마음보다 분위기에 가까울 수 있습니다."
        ),
        "conflict": (
            f"{a}는 마음이 기울면 관계의 방향을 확인해야 안정되는 편이고, {b}는 속내를 바로 꺼내기보다 상황을 살핀 뒤 움직이는 쪽으로 보입니다. "
            "그래서 다툼이 생겼을 때 한쪽은 바로 답을 원하고, 한쪽은 잠시 물러나려는 모양이 생길 수 있어요. "
            "이때 성격이 안 맞는다고 단정하기보다, 언제 다시 이야기할지와 무엇을 고칠지를 짧게 정하는 편이 낫습니다."
        ),
        "values": (
            "성격과 가치관은 큰 선언보다 생활 기준에서 확인됩니다. "
            "시간 약속을 지키는 태도, 돈을 쓰는 방식, 공부나 일에 대한 책임감, 연애를 주변 관계 안에 놓는 방식이 맞아야 오래 갑니다. "
            "지금은 감정의 깊이보다 이런 기준을 서로 무리 없이 맞출 수 있는지 보는 단계예요."
        ),
        "ziwei_relation": (
            "자미두수로 볼 때도 이 관계는 마음 하나만으로 판단하기보다 사람을 대하는 방식, 생활의 안정감, 밖에서 관계가 드러나는 모양을 함께 봐야 합니다. "
            f"{a}는 관계의 방향이 보여야 마음이 안정되고, {b}는 스스로 납득할 시간이 있어야 태도가 분명해지는 쪽으로 읽힙니다. "
            "따라서 급히 결론을 몰아가기보다, 관계가 생활 안에서 자연스럽게 자리 잡는지를 확인하는 편이 좋습니다."
        ),
        "chemistry": (
            "끌림은 있는 편입니다. 다만 끌림만으로 안정적인 연애가 되지는 않습니다. "
            "서로에게 좋은 영향을 주려면 한쪽은 확인을 조금 줄이고, 한쪽은 설명을 조금 늘려야 해요. "
            "이 균형이 잡히면 서로를 밀어내기보다 생활을 정돈해 주는 관계가 될 수 있습니다."
        ),
        "daily": (
            "일상에서는 연락 횟수보다 연락이 끊긴 뒤의 설명이 중요합니다. "
            "약속을 못 지켰을 때 그냥 넘기는지, 다시 시간을 잡는지, 기분이 상한 뒤에도 대화를 회복하는지를 보세요. "
            "이 부분이 맞으면 나이 차이나 표현 속도 차이는 충분히 줄어듭니다."
        ),
        "social": (
            "겹지인과 학교, 전공이 같은 관계라면 너무 급히 드러내는 것도 부담이고, 지나치게 숨기는 것도 불안을 만듭니다. "
            "지금은 소문을 만들기보다 서로를 곤란하게 하지 않는 선에서 자연스럽게 안부와 만남을 이어가는 방식이 좋습니다. "
            "둘만 있을 때와 주변 사람들 앞에서의 태도가 너무 다르지 않은지도 함께 보세요."
        ),
        "pace": (
            "관계 속도는 천천히 맞추는 쪽이 좋습니다. "
            f"{a}가 너무 자주 확인하면 {b}는 부담을 느껴 더 말을 아낄 수 있고, {b}가 설명을 너무 줄이면 {a}는 마음이 식었다고 느낄 수 있습니다. "
            "질문은 짧게, 기준은 분명하게, 기다리는 시간은 정해 두는 편이 가장 현실적입니다."
        ),
        "risk": (
            "주의할 지점은 세 가지입니다. 약속이 반복해서 밀리는 것, 불편한 이야기를 계속 피하는 것, 주변 관계 안에서 어색하게 숨기는 것입니다. "
            "이 셋이 같이 나타나면 마음이 없어서라기보다 관계를 책임질 준비가 부족한 신호일 수 있어요. "
            "그럴 때는 더 매달리기보다 한 번 분명히 말하고, 이후 행동이 달라지는지 보는 편이 낫습니다."
        ),
        "stability": (
            "안정적인 관계가 되려면 두 사람 모두 조금씩 양보해야 합니다. "
            f"{a}는 마음을 확인하고 싶은 말을 너무 길게 늘리지 않는 것이 좋고, {b}는 침묵으로 넘기지 말고 짧게라도 설명하는 습관이 필요합니다. "
            "이 조율이 가능하면 서로에게 좋은 영향을 주는 관계로 이어질 수 있습니다."
        ),
        "action": (
            "지금 다가가는 방식은 무거운 고백보다 가벼운 안부와 자연스러운 접점이 좋습니다. "
            "학교나 전공, 겹지인을 이용하되 상대를 시험하는 말은 피하세요. "
            "짧게 안부를 묻고, 편한 만남을 제안하고, 그 약속을 실제로 지키는지 보는 순서가 가장 안전합니다."
        ),
        "timing": (
            "앞으로 1년은 한 번에 결론을 내기보다 몇 번의 확인으로 나누어 보는 편이 좋습니다. "
            "가까운 시기에는 연락과 만남의 리듬을 보고, 그다음에는 갈등 뒤 회복이 되는지를 보세요. "
            "이 두 가지가 잡히면 관계를 더 분명히 해도 되고, 계속 흐려지면 마음을 오래 묶어 두지 않는 편이 낫습니다."
        ),
        "decision": (
            f"마지막 기준은 {b}가 얼마나 달콤하게 말하느냐가 아니라, {a}를 불안하게 만든 뒤 다시 회복하려는 태도가 있는지입니다. "
            "연락, 약속, 갈등 뒤 대화, 주변 관계에서의 태도가 일정하면 이어가 볼 만합니다. "
            "그 네 가지가 계속 흐려진다면 지금의 호감은 있어도 안정적인 연애로 가기에는 아직 약합니다. "
            "한 번의 고백보다 작은 반복을 먼저 보세요."
        ),
    }
    return texts.get(section_id, common_open).strip()


def _relationship_frontload_summary() -> str:
    return (
        "결론부터 말씀드리면, 이 궁합은 호감과 끌림은 있으나 대화 속도와 확인 방식에서 조율이 필요한 관계예요. "
        "상대의 진심은 말보다 연락 회복, 약속 이행, 갈등 뒤 다시 돌아오는 태도에서 먼저 보아야 합니다. "
        "앞으로 1년은 서두른 확답보다 올해 하반기와 내년 초의 반복 행동을 나누어 확인하는 시기예요. "
        "먼저 가벼운 안부와 자연스러운 접점을 만들고, 상대가 생활 기준과 연애관을 실제 행동으로 맞추는지 보세요."
    )


def _stabilize_relationship_section_lengths(sections: list[object]) -> None:
    for section in sections:
        filler = _REL_TAIL_FILLERS.get(section.id)
        if not filler:
            continue
        text = section.final_text.strip()
        if 650 <= len(text) <= 1800 and filler not in text:
            section.final_text = (text + "\n\n" + filler).strip()


def _finalize(text: str) -> str:
    """본문 표시용 정제 — 개인 경로(builder)와 동일한 postprocess 공통 함수 사용.

    순서: 마크다운/메타 제거(strip_artifacts) → 정당한 간지 한자→한글 보존 변환 →
    남은 비간지 한자(食神·七殺·용신 火 등) 제거 + em dash·가운뎃점·화살표 산문화.
    LLM 출력과 폴백 슬롯 모두에 적용한다('---'·'**'·'화(火)' 누출 실사고 2026-06-14).
    """
    text = _strip_llm_signature_lines(text)
    text = postprocess.strip_artifacts(text)
    text = _DECORATIVE_EMOJI_RX.sub("", text)
    text = _normalize_customer_body_terms(text)
    # 천간·지지 한자는 한글로 보존 변환(간지 글자는 일상어에 안 쓰여 전역 치환 안전)
    text = "".join(_GAN_KO.get(c) or _ZHI_KO.get(c) or c for c in text)
    text = postprocess.hanja_clean(text)
    text = _soften_report_style_endings(text)
    return text.strip()


def _identity_spec(people: list[dict]) -> tuple:
    """(expected_gans, expected_terms, subject_specs) — 일간 role 가드용(주체별 정확 판정)."""
    gans, terms, specs = set(), set(), []
    for p in people:
        gan = _GAN_KO.get(p["day_master"], "")
        term = client_tone_lint.gan_to_term(gan)
        gans.add(gan)
        terms.add(term)
        aliases = [
            p["name"],
            client_tone_lint.given_name(p["name"]),
            client_tone_lint.honor(p["name"]),
        ]
        specs.append((aliases, term))
    return gans, terms, specs


def _singang_specs(people: list[dict]) -> list[dict]:
    """신강약 role/group 가드용 spec(사람별 결정론 신강약, H1.5.3.2)."""
    return [
        {
            "full": p["name"],
            "given": client_tone_lint.given_name(p["name"]),
            "honor": client_tone_lint.honor(p["name"]),
            "singang": p["singang"],
        }
        for p in people
    ]


def _compose(
    section_id: str,
    base_text: str,
    allow: dict,
    situation: str,
    names: list[str] | None = None,
    ref_year: int | None = None,
    id_spec: tuple | None = None,
    singang_specs: list[dict] | None = None,
    fallback_text: str | None = None,
    use_llm: bool = False,
) -> str:
    """궁합 섹션 1개 작성 + 가드. 무키/실패/가드불통과 시 사실 슬롯(base_text) 폴백.

    LLM 출력과 폴백 모두 _finalize 로 정제 후 반환 — 마크다운/비간지 한자 누출 차단.
    situation 은 호출부에서 이미 마스킹된 본문이 들어온다(절대규칙 17, build_gunghap).
    가드 = §12 안전 + AI틱 스타일 + 품질(모순·오타) + 시제 + 사실(간지·별).
    """
    fallback = _finalize(fallback_text if fallback_text is not None else base_text)
    if not use_llm or not os.environ.get("ANTHROPIC_API_KEY"):
        return fallback
    try:
        import anthropic
    except Exception:
        return fallback
    guide = _REL_GUIDE.get(section_id) or _GH_GUIDE.get(section_id, "")
    system_prompt = _REL_SYSTEM if section_id in _REL_GUIDE else _GH_SYSTEM
    user = (
        f"[작성 방향]\n{guide}\n\n"
        f"[현재 맥락 - 참고용이며 그대로 인용하지 말 것]\n{situation}\n\n"
        f"[참고 근거 - 원문 라벨과 전문용어를 그대로 쓰지 말고 고객 문장으로 풀 것]\n{base_text}\n"
    )
    try:
        client = anthropic.Anthropic(max_retries=8)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user}],
        )
        cand = (msg.content[0].text if msg.content else "").strip()
    except Exception:
        return fallback
    if not cand:
        return fallback
    cand = _finalize(cand)
    cand = client_tone_lint.normalize_loanwords(cand)  # 외래어 1차 자동 순화(폴백 전, H1.5.1)
    if names:
        cand = client_tone_lint.normalize_names(cand, names)  # 전체이름→호칭 1차 순화(H1.5.3)
    bad = (
        safe_lint.lint(cand)
        + style_lint.lint(cand)
        + quality_lint.lint(cand, names)
        + temporal_lint.lint(cand, ref_year)
        + client_tone_lint.loanword_lint(cand)  # 외래어 hard-ban(고객 본문)
        + client_tone_lint.raw_calc_lint(cand)  # 날것 계산표현(오행 분포·목 2 화 2…)
        + (client_tone_lint.name_policy_lint(cand, names) if names else [])  # 전체이름 반복(H1.5.3)
        + (  # 일간 role 오서술(H1.5.3)
            client_tone_lint.identity_role_lint(cand, id_spec[0], id_spec[1], id_spec[2])
            if id_spec
            else []
        )
        + (  # 신강약 group/role 오서술(H1.5.3.2)
            client_tone_lint.singang_role_lint(cand, singang_specs) if singang_specs else []
        )
        + factcheck.check_with_allow(cand, allow)
    )
    if bad:
        return (
            fallback  # 가드 실패(외래어·계산표현·이름·일간·모순·오타·시제 포함) → 결정론 슬롯 폴백
        )
    return cand


def _merge_allow(people: list[dict]) -> dict:
    merged: dict[str, set] = {}
    for p in people:
        # 세운 간지도 실재 사실이므로 허용 토큰에 포함(LLM이 호기 해를 간지로 인용해도 통과)
        seun_gz = frozenset(gz for _, gz in p["m"].seun if gz)
        for k, v in factcheck.allowed_tokens(p["saju"], seun_gz).items():
            merged.setdefault(k, set()).update(v)
    return {k: sorted(v) for k, v in merged.items()}


def build_gunghap(
    people_in: list[tuple],
    *,
    situation: str = "",
    ref_year: int = 2026,
    out_name: str = "gunghap.pdf",
    brand: str = "seodam",
    mode: str = "business",
    use_llm: bool = False,
) -> dict:
    """people_in = [(이름, (y,mo,d,h,mi), is_male), ...]. 성별 생략 시 남(하위호환).

    결정론 사실 → (마스킹 situation) compose → 정제·그라운딩 → 서담선생 PDF → 렌더 후 게이트.
    개인 경로(builder)와 동일한 공통 후처리·그라운딩·게이트를 거치게 통일했다(실사고 2026-06-14).
    """
    people = []
    for item in people_in:
        nm, b = item[0], item[1]
        is_male = item[2] if len(item) >= 3 else True
        unknown_time = bool(item[3]) if len(item) >= 4 else False
        facts = person_facts(nm, b, ref_year=ref_year, is_male=is_male)
        facts["unknown_time"] = unknown_time
        people.append(facts)
    allow = _merge_allow(people)

    # 절대규칙 17: situation(운영자 상황 메모)에 생년월일·시각이 섞여 있으면 LLM 전달 전 마스킹.
    spans: list[tuple[int, int]] = []
    try:
        pms = input_partner.find_partner_births(situation) if situation else []
        spans = [(pm.start, pm.end) for pm in pms]
        spans += [pm.time_span for pm in pms if pm.time_span]
    except Exception:
        spans = []
    masked_situation = masking.mask_concern(situation, self_civil=None, partner_spans=spans)

    from itertools import combinations

    persons_txt = "\n".join(_person_slot(p) for p in people)
    pairs_txt = "\n".join(
        _pair_slot(people[i], people[j]) for i, j in combinations(range(len(people)), 2)
    )
    timing_txt = _timing_slot(people)
    if mode == "relationship":
        section_defs = _REL_SECTIONS
        slot = {
            sid: _relationship_slot(sid, people, persons_txt, pairs_txt, timing_txt, masked_situation)
            for sid, _title in section_defs
        }
        fallback_slot = {
            sid: _relationship_fallback(sid, people, masked_situation)
            for sid, _title in section_defs
        }
    else:
        section_defs = _GH_SECTIONS
        slot = {
            "overview": persons_txt,
            "each": persons_txt,
            "pairs": pairs_txt,
            "business": persons_txt + "\n" + pairs_txt,
            "timing": timing_txt,
        }
        fallback_slot = {}

    names = [p["name"] for p in people]
    id_spec = _identity_spec(people)  # 일간 role 가드(주체별 expected, H1.5.3)
    singang_specs = _singang_specs(people)  # 신강약 group/role 가드(H1.5.3.2)
    sections = []
    for sid, title in section_defs:
        final_text = _compose(
            sid,
            slot[sid],
            allow,
            masked_situation,
            names,
            ref_year,
            id_spec,
            singang_specs,
            fallback_text=fallback_slot.get(sid),
            use_llm=use_llm,
        )
        if mode == "relationship" and sid == "overview":
            final_text = _relationship_frontload_summary() + "\n\n" + final_text
        sections.append(
            SimpleNamespace(
                id=sid,
                title=title,
                source_keys=["gunghap"],  # 그라운딩(trace.check) — 결정론 사실 슬롯 근거
                final_text=final_text,
            )
        )

    repetition.dedup_ilju_intro(sections, owner_id="overview")
    if mode == "relationship":
        _stabilize_relationship_section_lengths(sections)

    # PDF-wide 이름 순화(H1.5.3.1) — _person_slot 이 여러 섹션에 재사용돼 'FULL 씨'가 PDF 전체에
    # 여러 번 등장하는 문제를 render 직전에 최종 보증: 사람별 첫 소개 1회만 보존, 2회째부터 호칭.
    normalized = client_tone_lint.normalize_names_pdfwide([s.final_text for s in sections], names)
    for s, nt in zip(sections, normalized):
        s.final_text = _normalize_gunghap_honorifics(nt, names)

    # 그라운딩 게이트 — 빈 본문/근거 없는 섹션 차단(개인 경로 builder 와 동일 정책)
    grounding_ok, gbad = trace.check(sections)
    if not grounding_ok:
        raise RuntimeError(f"궁합 그라운딩 실패(빌드 중단): {gbad}")

    product = "gunghap_relationship" if mode == "relationship" else None
    premium = mode == "relationship"
    bp = dict(cfg.brand(brand))
    label = "궁합 풀이" if mode == "relationship" else "사업 궁합 풀이"
    bp["cover_title"] = f"{bp.get('seal', '서담선생')} {label}"
    fake_saju = SimpleNamespace(input_civil=" · ".join(p["name"] for p in people))
    report = SimpleNamespace(sections=sections)
    llm_active = bool(use_llm and os.environ.get("ANTHROPIC_API_KEY"))
    layout_attempts: list[dict] = []
    pdf_path = ""
    v: dict = {}
    variants = _relationship_layout_variants(mode == "relationship" and llm_active)
    for idx, (body_font_size, body_line_height) in enumerate(variants):
        pdf_path = render_pdf.render_pdf(
            report,
            fake_saju,
            out_name,
            name="",
            brand=bp,
            chapter_breaks=True,
            body_font_size=body_font_size,
            body_line_height=body_line_height,
        )

        # 렌더 후 PDF 게이트 — 마크다운/품질/시제/orphan/이름·일간·신강약 결함 시 빌드 실패.
        v = render_verify.verify(
            pdf_path,
            ref_year=ref_year,
            names=names,
            name_full=names,
            identity=id_spec,
            singang=singang_specs,
            product=product,
            premium=premium,
            concern=masked_situation,
            ref_date=f"{ref_year}-06-13",
        )
        layout_attempts.append(
            {
                "body_font_size": body_font_size,
                "body_line_height": body_line_height,
                "gate_pass": bool(v.get("gate_pass")),
                "low_density_only": _only_low_density_failure(v),
            }
        )
        if not v.get("markdown_clean", True):
            raise RuntimeError(f"궁합 PDF 마크다운 누출(빌드 실패): {v.get('markdown_hits')}")
        if v.get("gate_pass"):
            break
        if idx < len(variants) - 1 and _only_low_density_failure(v):
            continue
        raise RuntimeError(f"궁합 PDF 하드 게이트 실패(빌드 실패): {v}")

    return {
        "pdf_path": pdf_path,
        "people": people,
        "sections": sections,
        "allow": allow,
        "verify": v,
        "mode": mode,
        "product": product,
        "layout_attempts": layout_attempts,
    }


# ───────────────── CLI ─────────────────

import typer  # noqa: E402

app = typer.Typer(add_completion=False, help="다인(2인 이상) 궁합 리포트 - 사주도령 PDF")


@app.command()
def gen(
    person: list[str] = typer.Option(
        ...,
        "--person",
        help="'이름,YYYY-MM-DD,HH:MM,성별' (2회 이상 반복). 시각 생략 시 정오 추정, 성별 생략 시 남.",
    ),
    situation: str = typer.Option("", "--situation", help="현재 상황 맥락(참고, 지시 아님)"),
    ref_year: int = typer.Option(2026, "--ref-year", help="풀이 기준 연도"),
    out: str = typer.Option("gunghap.pdf", "--out"),
    brand: str = typer.Option("sajudoryeong", "--brand", help="브랜드(프리셋 키 또는 임의 문구)"),
    mode: str = typer.Option("business", "--mode", help="business|relationship"),
    llm: bool = typer.Option(False, "--llm", help="ANTHROPIC_API_KEY가 있을 때 LLM 윤문 사용"),
) -> None:
    female_tokens = {"여", "여자", "f", "female", "0"}
    people_in = []
    for s in person:
        parts = [x.strip() for x in s.split(",")]
        y, mo, d = (int(x) for x in parts[1].split("-"))
        unknown_time = not (len(parts) >= 3 and parts[2])
        if not unknown_time:
            h, mi = (int(x) for x in parts[2].split(":"))
        else:
            h, mi = 12, 0
        # 성별(4번째 필드) — 대운 방향 결정. 생략 시 남(하위호환). '여/female/f/0' = 여성.
        is_male = not (len(parts) >= 4 and parts[3].lower() in female_tokens)
        people_in.append((parts[0], (y, mo, d, h, mi), is_male, unknown_time))
    if len(people_in) < 2:
        typer.echo("궁합은 2인 이상이 필요합니다(--person 반복).")
        raise typer.Exit(code=1)
    r = build_gunghap(
        people_in,
        situation=situation,
        ref_year=ref_year,
        out_name=out,
        brand=brand,
        mode=mode,
        use_llm=llm,
    )
    typer.echo(f"PDF: {r['pdf_path']} ({len(r['people'])}인)")


if __name__ == "__main__":
    app()
