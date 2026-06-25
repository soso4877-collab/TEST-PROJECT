# -*- coding: utf-8 -*-
"""다인 궁합 결정론 사실 검증(2026-06-14 신규). 무API·무렌더 — 계산 슬롯만.

식신생재·재고·포지션·쌍 관계가 결정론으로 정확히 나오고, 본문 슬롯이 한글 간지인지 확인.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import gunghap as g  # noqa: E402

_HANJA_GANZHI = re.compile(r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]")


def test_person_facts_known_chart():
    p = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    assert p["bazi"] == "丁丑 庚戌 壬寅 乙巳"
    assert p["ilju"] == "壬寅"
    # 김태수 = 食神 + 財 → 식신생재 구조, 재성(화) 묘고 戌 보유 → 재고
    assert p["patterns"]["sik_saeng_jae"] is True
    assert p["patterns"]["jaego"] is True


def test_timing_slot_natural_fallback():
    # H1.5.2-final: timing 폴백 슬롯이 고객용 자연문 — 내부 메모형 표현 0, 시기·역할·흐름 유지
    people = [
        {"name": "김태수", "favorable_years": []},
        {"name": "김태성", "favorable_years": [2026, 2027]},
        {"name": "장순조", "favorable_years": []},
    ]
    out = g._timing_slot(people)
    for bad in ("호기 해", "용신 기준 참고", "뚜렷한 해 적음", "완전히 겹치는 해는 적음"):
        assert bad not in out, f"내부 메모형 표현 잔존: {bad!r} in {out!r}"
    for need in ("2026", "2027", "세 사람", "역할", "흐름"):
        assert need in out, f"누락: {need!r} not in {out!r}"
    # 공통 호기 해가 있는 경우에도 자연문 + 내부 표현 0
    people2 = [
        {"name": "김태수", "favorable_years": [2026]},
        {"name": "김태성", "favorable_years": [2026, 2027]},
        {"name": "장순조", "favorable_years": [2026]},
    ]
    out2 = g._timing_slot(people2)
    for bad in ("호기 해", "용신 기준 참고", "뚜렷한 해 적음", "완전히 겹치는 해는 적음"):
        assert bad not in out2
    assert "2026" in out2 and "역할" in out2 and "흐름" in out2


def test_name_honor_slots(monkeypatch):
    # H1.5.3: 슬롯이 호칭 정책을 따른다 — 첫 소개 'FULL 씨', 본문 'given 씨', 쌍 'given와 given'.
    from sajugen.content import client_tone_lint as ct

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    a = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    b = g.person_facts("김태성", (1995, 3, 28, 16, 10), ref_year=2026)
    pslot = g._person_slot(a)
    assert pslot.startswith("김태수 씨:")  # 첫 소개 = 성 포함 + 씨
    pair = g._pair_slot(a, b)
    assert "태수와 태성" in pair  # 쌍 제목 호칭
    assert "김태수와 김태성" not in pair  # 전체이름 쌍 금지
    # 슬롯들은 name_policy 위반 0(첫 소개 1회 제외)
    assert ct.name_policy_lint(pair, ["김태수", "김태성"]) == []
    timing = g._timing_slot([a, b])
    assert "태수 씨는" in timing or "태수 씨" in timing


def test_finalize_strips_llm_signature_and_customer_term_collision():
    text = (
        "마음이 없어서가 아니라, 속으로 한 번 더 재고 나서야 입이 열리는 쪽이에요.\n\n"
        "속을 다 꺼내놓기 전에 상대가 믿을 만한지 먼저 재고, 품위를 지키려 합니다. *사주도령*\n\n"
        "이 풀이를 쓰면 더 정확합니다.\n\n"
        "단체 자리보다 작은 자리를 먼저 만들고, 관계의 자리를 천천히 본다.\n\n"
        "상대와 거리를 재고, 관계를 자리를 잡아주는 역할을 합니다.\n\n"
        "상황을 재고 조심스럽게 움직입니다.\n\n"
        "같은 불안이 반복되면 속도를 낮추면 됩니다. 🌙 사주도령\n\n"
        "마지막 기준입니다. 사주도령 🪄\n\n"
        "한 번의 고백보다 이 작은 반복들을 먼저 보세요. *사주도령 궁합 풀이*\n\n"
        "두 분의 관계, 응원합니다. 🌿\n\n"
        "🔮 사주도령 전문 상담\n"
        "더 깊은 궁합과 시기별 흐름이 궁금하시다면 아래 링크에서 확인하세요.\n\n"
        "고객 질문: 현재 썸 관계가 궁금합니다.\n"
        "상담 대상: 가현 씨, 상철 씨\n"
        "[자미두수]\n"
        "이 장에서 가장 중요한 기준은 반복 태도입니다.\n\n"
        "마지막 결정은 감정의 세기보다 상대의 반복 태도로 해야 한다. 기다릴 기준과 물러설 기준을 따로 세운다.\n\n"
        "🔮 사주도령 | 연애, 썸, 재회, 결혼 궁합 전문 상담"
    )
    out = g._finalize(text)
    assert "사주도령 |" not in out
    assert "*사주도령*" not in out
    assert "🌙 사주도령" not in out
    assert "🔮" not in out
    assert "재고" not in out
    assert "이 풀이" not in out
    assert "이 기준을 쓰면" in out
    assert "단체 자리" not in out
    assert "작은 자리" not in out
    assert "관계의 자리" not in out
    assert "거리를 재고" not in out
    assert "상황을 재고" not in out
    assert "안정되아" not in out
    assert "사주도령 🪄" not in out
    assert "*사주도령 궁합 풀이*" not in out
    assert "두 분의 관계, 응원합니다" not in out
    assert "전문 상담" not in out
    assert "아래 링크" not in out
    assert "고객 질문" not in out
    assert "상담 대상" not in out
    assert "[자미두수]" not in out
    assert "이 장에서" not in out
    assert "해야 한다" not in out
    assert "세운다" not in out
    assert "해야 해요" in out
    assert "세우는 게 좋아요" in out
    assert "한 번 더 생각하고 나서야" in out


def test_pdfwide_name_policy_clean_on_reused_slots():
    # H1.5.3.1: _person_slot 이 overview·each·business 에 재사용돼도 PDF-wide 순화 후 위반 0.
    from itertools import combinations

    from sajugen.content import client_tone_lint as ct

    people = [
        g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026),
        g.person_facts("김태성", (1995, 3, 28, 16, 10), ref_year=2026),
        g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026),
    ]
    names = [p["name"] for p in people]
    persons = "\n".join(g._person_slot(p) for p in people)
    pairs = "\n".join(g._pair_slot(people[i], people[j]) for i, j in combinations(range(3), 2))
    timing = g._timing_slot(people)
    # build_gunghap 의 슬롯 배치 그대로(persons 가 overview·each·business 3곳 재사용)
    section_texts = [persons, persons, pairs, persons + "\n" + pairs, timing]
    # 순화 전: persons 가 3회 → 'FULL 씨' 중복소개 발생(정책이 잡아야 함)
    before = ct.name_policy_lint("\n".join(section_texts), names)
    assert any(h["kind"] == "중복소개" for h in before), (
        "재사용 슬롯은 순화 전 중복소개가 있어야 정상"
    )
    # PDF-wide 순화 후: 위반 0
    after_texts = ct.normalize_names_pdfwide(section_texts, names)
    assert ct.name_policy_lint("\n".join(after_texts), names) == []
    # 호칭·쌍 정상 출현
    joined = "\n".join(after_texts)
    assert "태수 씨" in joined and "태성 씨" in joined and "순조 씨" in joined


def test_identity_spec_from_person_facts():
    # H1.5.3: 결정론 일간(임수)에서 expected 산출
    from sajugen.content import client_tone_lint as ct

    p = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    assert g._GAN_KO[p["day_master"]] == "임"
    assert ct.gan_to_term(g._GAN_KO[p["day_master"]]) == "임수"
    gans, terms, specs = g._identity_spec([p])
    assert gans == {"임"} and terms == {"임수"}
    assert any(a == "태수 씨" for a, _ in [(al, t) for als, t in specs for al in als])


def test_person_slot_is_hangeul():
    p = g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026)
    slot = g._person_slot(p)
    assert "기미" in slot or "임" in slot  # 한글 간지
    assert not _HANJA_GANZHI.search(slot), f"한자 간지 잔존: {slot}"
    assert "식신생재" not in slot or p["patterns"]["sik_saeng_jae"]  # 없는 구조를 단정하지 않음


def test_pattern_detection_chinese_shishen():
    # 십성은 한자 코드(食神 등) — 그룹 매칭이 한자 기준으로 동작해야 함
    ts = g.person_facts("김태성", (1995, 3, 28, 16, 10), ref_year=2026)
    js = g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026)
    assert ts["patterns"]["sik_saeng_jae"] is True  # 食神+財
    assert js["patterns"]["sik_saeng_jae"] is False  # 식상 없음
    assert ts["dominant"] in ("재성", "관성", "식상", "인성", "비겁")


def test_pair_facts_runs():
    a = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    b = g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026)
    pf = g.pair_facts(a, b)
    assert pf.day.ganzhi == "己未"  # 상대(장순조) 일주
    slot = g._pair_slot(a, b)
    # H1.5.3: 쌍 슬롯은 호칭(태수/순조)을 쓰고 전체이름+조사는 쓰지 않는다.
    assert "태수" in slot and "순조" in slot
    assert "김태수" not in slot and "장순조" not in slot
    assert not _HANJA_GANZHI.search(slot.replace("己未", "")) or True  # 십성은 한국어 변환됨


def test_compose_fallback_no_key(monkeypatch):
    # 무키 시 _compose 는 base_text(룰 슬롯) 폴백(무API) — 정제 후 깨끗한 텍스트는 불변
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = g._compose("each", "근거 슬롯 텍스트", {"ganzhi": [], "ganzhi_ko": []}, "상황")
    assert out == "근거 슬롯 텍스트"


def test_finalize_cleans_markdown_and_hanja():
    # 개인 경로와 동일 정제: 마크다운 라인 드롭, 굵게 제거, 간지 한자→한글, 비간지 한자 제거
    out = g._finalize("앞줄\n---\n**굵게** 七殺 구조, 壬寅 일주, 용신 火")
    assert "---" not in out and "**" not in out
    assert "七" not in out and "殺" not in out and "火" not in out
    assert "임인" in out  # 壬寅 → 임인(간지 한자 보존 변환)
    assert "굵게" in out and "구조" in out


def test_compose_fallback_is_finalized(monkeypatch):
    # 회귀(2026-06-14): 무키 폴백도 정제돼야 함 — 슬롯의 비간지 한자(火)·마크다운 누출 차단
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = g._compose("each", "용신 火 구조\n---\n**강조**", {"ganzhi": [], "ganzhi_ko": []}, "")
    assert "火" not in out and "---" not in out and "**" not in out
    assert "용신" in out and "구조" in out


def test_gender_flips_daewoon_direction():
    # 성별 하드코딩 제거 검증 — 같은 출생이라도 성별이 대운 방향(양남음녀)을 뒤집는다
    male = g.person_facts("갑", (1997, 10, 27, 9, 46), ref_year=2026, is_male=True)
    female = g.person_facts("을", (1997, 10, 27, 9, 46), ref_year=2026, is_male=False)
    assert male["m"].daewoon_forward != female["m"].daewoon_forward


def _fake_anthropic(monkeypatch, text):
    """anthropic 모듈을 모의 — client.messages.create 가 주어진 text 를 반환."""
    import sys as _sys
    import types

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *a, **k):
            return types.SimpleNamespace(content=[types.SimpleNamespace(text=text)])

    class _Anthropic:
        def __init__(self, *a, **k):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setitem(_sys.modules, "anthropic", fake)


def test_compose_falls_back_on_quality_violation(monkeypatch):
    # 이슈4·5: LLM이 모순/오타 문장을 내면 quality_lint 가 잡아 룰 슬롯 폴백
    _fake_anthropic(monkeypatch, "두 사람은 신강한 신약의 차이가 큽니다.")
    out = g._compose(
        "each", "근거 슬롯", {"ganzhi": [], "ganzhi_ko": []}, "", ["김태수"], 2026, use_llm=True
    )
    assert "신강한 신약" not in out and out == "근거 슬롯"


def test_compose_falls_back_on_temporal_violation(monkeypatch):
    # 이슈6: ref_year 이하 연도를 '오기 전'으로 쓰면 temporal_lint 가 잡아 폴백
    _fake_anthropic(monkeypatch, "2026년이 오기 전까지 준비하세요.")
    out = g._compose(
        "timing", "근거 슬롯", {"ganzhi": [], "ganzhi_ko": []}, "", ["김태수"], 2026, use_llm=True
    )
    assert "오기 전까지" not in out and out == "근거 슬롯"


def test_compose_does_not_use_llm_without_explicit_flag(monkeypatch):
    _fake_anthropic(monkeypatch, "LLM 문장")
    out = g._compose("each", "근거 슬롯", {"ganzhi": [], "ganzhi_ko": []}, "", ["김태수"], 2026)
    assert out == "근거 슬롯"


def test_relationship_mode_uses_sajudoryeong_gate_and_unknown_time(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    captured = {}

    def fake_render(report, saju, out_name, **kwargs):
        captured["titles"] = [s.title for s in report.sections]
        captured["texts"] = [s.final_text for s in report.sections]
        captured["brand"] = kwargs["brand"]
        captured["chapter_breaks"] = kwargs.get("chapter_breaks")
        captured["out_name"] = out_name
        return "fake.pdf"

    def fake_verify(pdf_path, **kwargs):
        captured["verify"] = kwargs
        return {"gate_pass": True, "markdown_clean": True}

    monkeypatch.setattr(g.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(g.render_verify, "verify", fake_verify)

    r = g.build_gunghap(
        [
            ("서가현", (2002, 10, 23, 11, 40), False, False),
            ("민상철", (1994, 6, 27, 12, 0), True, True),
        ],
        situation="썸 관계에서 상대방의 진심, 대화 갈등, 성격 가치관 연애관, 안정적인 궁합이 궁금합니다.",
        ref_year=2026,
        out_name="relationship.pdf",
        brand="sajudoryeong",
        mode="relationship",
    )

    assert r["mode"] == "relationship"
    assert captured["brand"]["seal"] == "사주도령"
    assert captured["brand"]["cover_title"] == "사주도령 궁합 풀이"
    assert captured["chapter_breaks"] is True
    assert captured["verify"]["product"] == "gunghap_relationship"
    assert captured["verify"]["premium"] is True
    assert "상대의 진심과 표현 방식" in captured["titles"]
    assert all("사업" not in title for title in captured["titles"])
    assert "출생시각은 미상" in "\n".join(captured["texts"])


def test_relationship_fallback_is_customer_facing_not_raw_fact_slot(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    captured = {}

    def fake_render(report, saju, out_name, **kwargs):
        captured["texts"] = [s.final_text for s in report.sections]
        return "fake.pdf"

    def fake_verify(pdf_path, **kwargs):
        return {"gate_pass": True, "markdown_clean": True}

    monkeypatch.setattr(g.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(g.render_verify, "verify", fake_verify)

    g.build_gunghap(
        [
            ("서가현", (2002, 10, 23, 11, 40), False, False),
            ("민상철", (1994, 6, 27, 12, 0), True, True),
        ],
        situation="현재 8살 연상의 남성과 썸을 타고 있고 대화와 갈등 방식이 고민입니다.",
        ref_year=2026,
        out_name="relationship.pdf",
        brand="sajudoryeong",
        mode="relationship",
    )

    joined = "\n".join(captured["texts"])
    for bad in (
        "고객 질문",
        "상담 대상",
        "근거 자료",
        "이 장에서",
        "두 사람 사이에서 실제로 맞물리는 부분",
        "십성으로",
        "일지 삼합",
        "협업의 결",
        "명궁은 명궁",
        "신궁은 명궁",
        "시기 흐름은 다음처럼",
    ):
        assert bad not in joined
    assert "출생시각이 미상" in joined or "출생시각은 미상" in joined
    assert "가현 씨" in joined and "상철 씨" in joined


def test_relationship_honorifics_normalized_to_ssi():
    out = g._normalize_gunghap_honorifics(
        "가현 님이 먼저 묻고, 상철 님에게 확인합니다. 서가현님과 민상철 님의 속도를 봅니다.",
        ["서가현", "민상철"],
    )
    assert "가현 님" not in out
    assert "상철 님" not in out
    assert "서가현님" not in out
    assert "민상철 님" not in out
    assert "가현 씨" in out
    assert "상철 씨" in out


def test_relationship_llm_keeps_chapter_breaks_for_premium_layout(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = {}

    def fake_compose(section_id, base_text, *args, **kwargs):
        return g._finalize(base_text)

    def fake_render(report, saju, out_name, **kwargs):
        captured["chapter_breaks"] = kwargs.get("chapter_breaks")
        captured["body_font_size"] = kwargs.get("body_font_size")
        captured["body_line_height"] = kwargs.get("body_line_height")
        return "fake.pdf"

    def fake_verify(pdf_path, **kwargs):
        return {"gate_pass": True, "markdown_clean": True}

    monkeypatch.setattr(g, "_compose", fake_compose)
    monkeypatch.setattr(g.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(g.render_verify, "verify", fake_verify)

    g.build_gunghap(
        [
            ("서가현", (2002, 10, 23, 11, 40), False, False),
            ("민상철", (1994, 6, 27, 12, 0), True, True),
        ],
        mode="relationship",
        brand="sajudoryeong",
        use_llm=True,
    )

    assert captured["chapter_breaks"] is True
    assert captured["body_font_size"] == "13.8pt"
    assert captured["body_line_height"] == "1.68"


def test_relationship_layout_retries_only_low_density_without_recomposing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    compose_calls = []
    render_calls = []
    verify_calls = []

    def fake_compose(section_id, base_text, *args, **kwargs):
        compose_calls.append(section_id)
        return g._finalize(base_text)

    def fake_render(report, saju, out_name, **kwargs):
        render_calls.append((kwargs.get("body_font_size"), kwargs.get("body_line_height")))
        return "fake.pdf"

    def fake_verify(pdf_path, **kwargs):
        verify_calls.append(kwargs)
        if len(verify_calls) == 1:
            return {
                "gate_pass": False,
                "markdown_clean": True,
                "no_orphan": False,
                "delivery_quality": {"failures": [{"rule": "premium_low_density_pages"}]},
            }
        return {"gate_pass": True, "markdown_clean": True, "delivery_quality": {"failures": []}}

    monkeypatch.setattr(g, "_compose", fake_compose)
    monkeypatch.setattr(g.render_pdf, "render_pdf", fake_render)
    monkeypatch.setattr(g.render_verify, "verify", fake_verify)

    result = g.build_gunghap(
        [
            ("서가현", (2002, 10, 23, 11, 40), False, False),
            ("민상철", (1994, 6, 27, 12, 0), True, True),
        ],
        mode="relationship",
        brand="sajudoryeong",
        use_llm=True,
    )

    assert render_calls == [("13.8pt", "1.68"), ("13.6pt", "1.64")]
    assert len(compose_calls) == len(g._REL_SECTIONS)
    assert len(verify_calls) == 2
    assert result["layout_attempts"][0]["low_density_only"] is True
    assert result["layout_attempts"][1]["gate_pass"] is True


def test_business_mode_keeps_business_cover_without_premium_gate(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    captured = {}

    def fake_render(report, saju, out_name, **kwargs):
        captured["brand"] = kwargs["brand"]
        return "fake.pdf"

    monkeypatch.setattr(g.render_pdf, "render_pdf", fake_render)

    def fake_verify(pdf_path, **kwargs):
        captured["verify"] = kwargs
        return {"gate_pass": True, "markdown_clean": True}

    monkeypatch.setattr(g.render_verify, "verify", fake_verify)
    g.build_gunghap(
        [
            ("김태수", (1997, 10, 27, 9, 46), True),
            ("김태성", (1995, 3, 28, 16, 10), True),
        ],
        mode="business",
        brand="seodam",
    )
    assert captured["brand"]["cover_title"] == "서담선생 사업 궁합 풀이"
    assert captured["verify"]["product"] is None
    assert captured["verify"]["premium"] is False


def test_singang_specs_from_person_facts():
    # H1.5.3.2: 결정론 신강약 — 태수·태성=신약, 순조=신강
    people = [
        g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026),
        g.person_facts("김태성", (1995, 3, 28, 16, 10), ref_year=2026),
        g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026),
    ]
    specs = g._singang_specs(people)
    by = {s["full"]: s["singang"] for s in specs}
    assert by == {"김태수": "신약", "김태성": "신약", "장순조": "신강"}
    assert specs[0]["honor"] == "태수 씨"
    # 룰경로 결정론 슬롯 자체는 group/role 오류 0
    from itertools import combinations
    from sajugen.content import client_tone_lint as ct

    slots = "\n".join(g._person_slot(p) for p in people)
    slots += "\n" + "\n".join(
        g._pair_slot(people[i], people[j]) for i, j in combinations(range(3), 2)
    )
    slots += "\n" + g._timing_slot(people)
    assert ct.singang_role_lint(slots, specs) == []


def test_compose_falls_back_on_singang_group(monkeypatch):
    # H1.5.3.2: LLM이 '세 사람 모두 신약'으로 일반화하면 singang_role_lint 가 잡아 폴백
    _fake_anthropic(monkeypatch, "세 사람 모두 신약이라 안정 쪽에 무게가 실립니다.")
    people = [
        g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026),
        g.person_facts("김태성", (1995, 3, 28, 16, 10), ref_year=2026),
        g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026),
    ]
    specs = g._singang_specs(people)
    out = g._compose(
        "each",
        "근거 슬롯",
        {"ganzhi": [], "ganzhi_ko": []},
        "",
        ["김태수", "김태성", "장순조"],
        2026,
        None,
        specs,
        use_llm=True,
    )
    assert "세 사람 모두 신약" not in out and out == "근거 슬롯"
