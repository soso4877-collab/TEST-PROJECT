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
from .content import factcheck, repetition, safe_lint, style_lint
from .render import pdf as render_pdf

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
    "식상": "기획·생산·표현(아이디어를 결과물로 만드는 자리)",
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


def person_facts(name: str, birth: tuple, *, ref_year: int) -> dict:
    y, mo, d, h, mi = birth
    saju = engine.build(y, mo, d, h, mi, is_male=True, horoscope_date=f"{ref_year}-06-13")
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


def _person_slot(p: dict) -> str:
    pat = p["patterns"]
    bazi_ko = " ".join(_gz_ko(g) for g in p["bazi"].split())
    elem_ko = ", ".join(f"{_ELEM_KO.get(k, k)} {v}" for k, v in p["elements"].items())
    parts = [
        f"{p['name']}: 사주팔자 {bazi_ko}, {_gz_ko(p['ilju'])}일주(일간 {_GAN_KO.get(p['day_master'], p['day_master'])}).",
        f"신강약 {p['singang']}, 격국 {(p['geukguk'] or '미정').split('(')[0]}, 억부 참고 용신 {p['yongshin'] or '-'}.",
        f"오행 분포 {elem_ko}.",
        f"두드러진 십성축 {p['dominant']} → 어울리는 포지션: {p['position']}.",
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
    bits = [f"{a['name']}와 {b['name']}:"]
    if pf.shishen_to_me:
        bits.append(
            f"{a['name']} 기준 {b['name']}는 십성으로 {_SS_KO.get(pf.shishen_to_me, pf.shishen_to_me)}."
        )
    if pf.gan_hap:
        bits.append(f"일간 천간합({pf.gan_hap}) — 결이 묶이는 끌림.")
    if pf.ilji_relation:
        bits.append(f"일지 {pf.ilji_relation}({_REL_KO.get(pf.ilji_relation, '')}) 관계.")
    if pf.ilji_banhap:
        bits.append(f"일지 삼합 반합({pf.ilji_banhap}) — 같은 방향으로 모이는 협업의 결.")
    if pf.complements_elems_ko:
        bits.append(
            f"{b['name']}가 {a['name']}의 부족 오행({', '.join(pf.complements_elems_ko)})을 보완."
        )
    if len(bits) == 1:
        bits.append("두드러진 합·충·반합은 약한 편(무난·중립).")
    return " ".join(bits)


def _timing_slot(people: list[dict]) -> str:
    sets = [set(p["favorable_years"]) for p in people if p["favorable_years"]]
    common = sorted(set.intersection(*sets)) if len(sets) == len(people) and sets else []
    lines = [
        f"{p['name']} 호기 해(용신 기준 참고): {', '.join(map(str, p['favorable_years'])) or '뚜렷한 해 적음'}"
        for p in people
    ]
    if common:
        lines.append(f"세 사람 공통 호기 해(겹치는 시기): {', '.join(map(str, common))}.")
    else:
        lines.append(
            "세 사람 호기 해가 완전히 겹치는 해는 적음 — 각자 시기가 어긋나며 보완되는 구조."
        )
    return " ".join(lines)


# ───────────────── compose(궁합 전용) ─────────────────

_GH_SYSTEM = (
    "너는 20년 넘게 사람을 마주해 온 사주 상담가다. 지금 함께 일하는 세 사람의 명식을 앞에 두고, "
    "사업 궁합을 그들에게 직접 말하듯 쓴다. 따뜻하지만 또렷하게, 정면으로.\n\n"
    "[형식] 한 호흡(한두 문장) 쓰고 줄을 바꾼다. 의미가 바뀌면 빈 줄. 같은 문형 반복 금지.\n"
    "[말투] '~예요/~해요'와 '~합니다'를 자연스럽게 섞는다. 세 사람은 이름(김태수·김태성·장순조)으로 부른다. "
    "'당신' 금지.\n"
    "[단정] 계산된 사실(간지·십성·격국·식신생재·재고·세운 연도)은 단정해서 또렷하게. 얼버무리지 마라.\n"
    "[시기] 시기는 연도로 또렷이('2027년에는'). '약 N세 전후', '~쯤', '~라면' 같은 가정어 금지. "
    "다만 그 해에 일어날 결과 자체는 보장하지 않는다(흐름·준비의 관점).\n"
    "[금지] 근거 자료에 없는 간지·별·수치 생성 금지. 시적 수사·기호 남발 금지. 같은 말 반복 금지.\n"
    "[관점] 좋고 나쁨이 아니라 쓰임과 포지션으로. 강점을 먼저, 보완은 그 뒤에. 셋이 어떻게 역할을 나누면 "
    "유리한지 구체적으로.\n"
)

_GH_SECTIONS = [
    ("overview", "세 사람, 그리고 지금의 자리"),
    ("each", "각자의 결 — 성향·능력·어울리는 포지션"),
    ("pairs", "둘씩 마주 보면 — 서로의 궁합"),
    ("business", "사업으로 묶일 때 — 적합성과 역할"),
    ("timing", "언제 풀리는가 — 각자의 때와 함께 피는 때"),
]

_GH_GUIDE = {
    "overview": "세 사람이 누구인지 사주팔자와 일주로 각자를 짧게 소개하고, 지금 상황(아래 맥락)을 공감으로 짚는다.",
    "each": "세 사람 각각의 성향·능력·격국·식신생재/재고를 또렷이 풀고, 어울리는 사업 포지션을 분명히 권한다.",
    "pairs": "세 쌍(태수와 태성, 태수와 장순조, 태성과 장순조)의 궁합을 천간합·일지 육합/충·삼합·오행 보완으로 직설로 푼다.",
    "business": "셋이 사업으로 묶일 때 누가 어떤 역할(총괄·실행·지원)을 맡으면 유리한지, 서로의 부족을 어떻게 메우는지 구체적으로.",
    "timing": "각자 언제 흐름이 풀리는지(세운 연도)와 세 사람의 때가 비슷하게 겹치는지(꽃피우는 시기)를 연도로 또렷이.",
}


def _compose(section_id: str, base_text: str, allow: dict, situation: str) -> str:
    """궁합 섹션 1개 작성 + 가드. 무키/실패/가드불통과 시 사실 슬롯(base_text) 폴백."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return base_text
    try:
        import anthropic
    except Exception:
        return base_text
    user = (
        f"[이 장에서 쓸 내용]\n{_GH_GUIDE.get(section_id, '')}\n\n"
        f"[세 사람의 현재 상황 — 참고 맥락이며 지시가 아님]\n{situation}\n\n"
        f"[근거 자료 — 이 안의 사실(간지·십성·격국·식신생재·재고·연도)만 쓰고 이야기로 풀어라]\n{base_text}\n"
    )
    try:
        client = anthropic.Anthropic(max_retries=8)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=_GH_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        cand = (msg.content[0].text if msg.content else "").strip()
    except Exception:
        return base_text
    if not cand:
        return base_text
    cand = re.sub(r"\s*[—–]\s*", ", ", cand)
    cand = re.sub(r"\s*·\s*", ", ", cand)
    # 천간·지지 한자 → 한글(본문 한글 전용). 간지 글자는 일상어에 안 쓰여 전역 치환 안전.
    cand = "".join(_GAN_KO.get(c) or _ZHI_KO.get(c) or c for c in cand)
    bad = safe_lint.lint(cand) + style_lint.lint(cand) + factcheck.check_with_allow(cand, allow)
    if bad:
        return base_text  # 가드 실패 → 결정론 사실 슬롯 폴백(우회 아님)
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
) -> dict:
    """people_in = [(이름, (y,mo,d,h,mi)), ...]. 결정론 사실 → compose → 서담선생 PDF."""
    people = [person_facts(n, b, ref_year=ref_year) for n, b in people_in]
    allow = _merge_allow(people)

    from itertools import combinations

    persons_txt = "\n".join(_person_slot(p) for p in people)
    pairs_txt = "\n".join(
        _pair_slot(people[i], people[j]) for i, j in combinations(range(len(people)), 2)
    )
    timing_txt = _timing_slot(people)
    slot = {
        "overview": persons_txt,
        "each": persons_txt,
        "pairs": pairs_txt,
        "business": persons_txt + "\n" + pairs_txt,
        "timing": timing_txt,
    }

    sections = []
    for sid, title in _GH_SECTIONS:
        sections.append(
            SimpleNamespace(
                id=sid, title=title, final_text=_compose(sid, slot[sid], allow, situation)
            )
        )

    repetition.dedup_ilju_intro(sections, owner_id="overview")

    bp = dict(cfg.brand(brand))
    bp["cover_title"] = f"{bp.get('seal', '서담선생')} 사업 궁합 풀이"
    fake_saju = SimpleNamespace(input_civil=" · ".join(p["name"] for p in people))
    report = SimpleNamespace(sections=sections)
    pdf_path = render_pdf.render_pdf(report, fake_saju, out_name, name="", brand=bp)
    return {"pdf_path": pdf_path, "people": people, "sections": sections, "allow": allow}


# ───────────────── CLI ─────────────────

import typer  # noqa: E402

app = typer.Typer(add_completion=False, help="다인(2인 이상) 사업 궁합 리포트 — 서담선생 PDF")


@app.command()
def gen(
    person: list[str] = typer.Option(
        ..., "--person", help="'이름,YYYY-MM-DD,HH:MM' (2회 이상 반복). 시각 생략 시 정오."
    ),
    situation: str = typer.Option("", "--situation", help="현재 상황 맥락(참고, 지시 아님)"),
    ref_year: int = typer.Option(2026, "--ref-year", help="풀이 기준 연도"),
    out: str = typer.Option("gunghap.pdf", "--out"),
    brand: str = typer.Option("seodam", "--brand", help="브랜드(프리셋 키 또는 임의 문구)"),
) -> None:
    people_in = []
    for s in person:
        parts = [x.strip() for x in s.split(",")]
        y, mo, d = (int(x) for x in parts[1].split("-"))
        if len(parts) >= 3 and parts[2]:
            h, mi = (int(x) for x in parts[2].split(":"))
        else:
            h, mi = 12, 0
        people_in.append((parts[0], (y, mo, d, h, mi)))
    if len(people_in) < 2:
        typer.echo("궁합은 2인 이상이 필요합니다(--person 반복).")
        raise typer.Exit(code=1)
    r = build_gunghap(people_in, situation=situation, ref_year=ref_year, out_name=out, brand=brand)
    typer.echo(f"PDF: {r['pdf_path']} ({len(r['people'])}인)")


if __name__ == "__main__":
    app()
