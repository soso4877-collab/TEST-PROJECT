# -*- coding: utf-8 -*-

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import delivery_quality as dq  # noqa: E402


def _premium_text() -> str:
    lead = (
        "자미두수로 보면 집과 터전의 판단이 강하고, 돈과 계약은 서류 확인이 먼저입니다. "
        "이사는 김포와 계양을 모두 놓고 생활 거리와 병원, 사람의 도움을 같이 보아야 합니다. "
        "로타리 클럽 창립은 모임의 역할을 작게 나누고 돈 관리는 따로 두면 좋습니다. "
        "배우자의 도움은 받을 수 있지만 명의와 큰돈은 직접 확인해야 합니다. "
        "올해 하반기에는 매매 조건을 고르고, 내년 상반기에는 실제 거처를 굳히는 판단 지점이 옵니다. "
        "먼저 가격과 계약 조건을 적고, 서두르지 말고 사람의 말보다 문서를 확인하세요. "
        "청마라는 이름은 이전 맥락으로만 짧게 참고하면 충분합니다. "
    )
    filler = (
        "이 풀이에서는 집 문제와 사람 문제를 분리해서 봅니다. "
        "매매는 급히 낮추기보다 조건을 고르는 쪽이 낫고, 이동은 생활의 편함을 먼저 보아야 합니다. "
        "돈은 새 일을 키우는 힘이 되지만 약속을 말로만 두면 부담이 커집니다. "
    )
    return lead + filler * 95


def test_nonpremium_default_reports_without_paid_threshold_failure():
    r = dq.analyze("짧은 일반 점검 본문입니다.", pages=3)
    assert r["clean"] is True
    assert r["premium"] is False


def test_nonpremium_without_question_reports_repetition_as_warning_only():
    r = dq.analyze("또렷 " * 4, pages=2)
    assert r["clean"] is True
    assert "repetitive_phrasing" in {w["rule"] for w in r["warnings"]}
    assert "repetitive_phrasing" not in {f["rule"] for f in r["failures"]}


def test_premium_thin_report_fails_density_and_ziwei():
    r = dq.analyze("짧은 본문입니다.", pages=14, premium=True)
    rules = {f["rule"] for f in r["failures"]}
    assert "premium_pages" in rules
    assert "premium_text_chars" in rules
    assert "missing_usable_ziwei" in rules
    assert r["clean"] is False


def test_gunghap_relationship_requires_30_pages_and_question_axes():
    concern = (
        "현재 8살 연상의 남성과 썸을 타고 있습니다. 서로 호감은 있지만 대화나 갈등에서 "
        "생각하는 방식 차이가 있습니다. 상대방의 진심, 성격, 가치관, 연애관, 좋은 영향, "
        "안정적인 관계를 이어갈 수 있는 궁합인지 궁금합니다."
    )
    text = (
        "결론부터 말하면 이 관계는 호감과 진심을 확인하되 대화와 갈등의 속도를 맞추는 것이 핵심입니다. "
        "성격과 가치관, 연애관은 생활 기준과 약속을 어떻게 맞추는지에서 드러납니다. "
        "상대의 마음은 말보다 표현과 반복되는 태도, 신뢰를 지키는 방식으로 보아야 합니다. "
        "두 사람은 서로에게 좋은 영향을 줄 수 있지만 안정적으로 이어가려면 조율과 속도 조절이 필요합니다. "
        "앞으로 1년은 올해 하반기와 내년 상반기를 나누어 판단하면 좋습니다. "
        "먼저 안부와 대화를 가볍게 열고, 서두르지 말고 관계 기준을 확인해야 합니다. "
        "명리에서는 궁합과 보완을 보고, 자미두수로는 사람과 관계, 돈과 생활, 밖에서 드러나는 모습을 함께 봅니다. "
    ) * 70
    thin = dq.analyze(text, pages=29, product="gunghap_relationship", concern=concern)
    assert thin["clean"] is False
    assert {"rule": "premium_pages", "value": 29, "minimum": 30} in thin["failures"]

    ok = dq.analyze(text, pages=30, product="gunghap_relationship", concern=concern)
    assert ok["clean"] is True, ok
    assert ok["min_gunghap_pages"] == 30
    assert ok["missing_axes"] == []


def test_premium_without_customer_context_reports_layout_and_repetition_only():
    text = (
        "자미두수로 보면 집과 돈과 일이 함께 보이고 흐름도 함께 봅니다. "
        "자미두수의 사람과 관계, 이동의 단서도 흐름으로 참고합니다. "
    ) * 220
    r = dq.analyze(
        text,
        pages=24,
        product="integrated",
        low_density_pages=[{"page": 3, "chars": 50, "text": "짧은 페이지"}],
    )
    failure_rules = {f["rule"] for f in r["failures"]}
    warning_rules = {w["rule"] for w in r["warnings"]}
    assert r["clean"] is True
    assert "premium_low_density_pages" not in failure_rules
    assert "repetitive_phrasing" not in failure_rules
    assert "premium_low_density_pages" in warning_rules
    assert "domain_term_repetition" in warning_rules


def test_premium_integrated_question_passes_when_axes_and_ziwei_are_present():
    concern = "아파트 매매와 김포 이사, 로타리 클럽 창립, 도와주는 사람과 시기가 궁금합니다"
    r = dq.analyze(
        _premium_text(),
        pages=27,
        product="integrated",
        concern=concern,
        expected_context_terms=["청마"],
    )
    assert r["clean"] is True, r
    assert r["premium"] is True
    assert r["missing_axes"] == []
    assert r["ziwei"]["ok"] is True
    assert r["expected_context_hits"]["청마"] == 1
    assert r["frontloaded_answer"]["ok"] is True
    assert r["ziwei"]["cross_domains"]


def test_generated_premium_context_report_passes_with_domain_term_repetition_warning(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(1966, 8, 1, 2, 0, is_male=False, horoscope_date="2026-06-01")
    concern = (
        "집 매매와 김포 이주, 계양과 비교, 청마로타리클럽 창립, "
        "도와주는 사람 도움 여부, 계약 주의점과 시기가 궁금합니다"
    )
    rep = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        name="정숙",
        concern=concern,
        product="integrated",
    )
    body = "\n".join(s.final_text for s in rep.sections)
    r = dq.analyze(
        body,
        pages=27,
        product="integrated",
        premium=True,
        concern=concern,
        expected_context_terms=["청마"],
    )
    assert r["clean"] is True, r
    assert r["frontloaded_answer"]["ok"] is True
    assert r["missing_axes"] == []
    assert r["ziwei"]["ok"] is True
    assert r["expected_context_hits"]["청마"] == 1
    assert "domain_term_repetition" in {w["rule"] for w in r["warnings"]}
    assert "repetitive_phrasing" not in {f["rule"] for f in r["failures"]}


def test_generated_reunion_context_report_frontloads_question_answer(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(2000, 1, 1, 12, 0, is_male=False, horoscope_date="2026-06-01")
    concern = (
        "헤어진지 7개월이고 상대가 군대에 있어 접촉 기회가 잘 없습니다. "
        "겹지인이 많고 학교와 전공이 같은 선후배 사이인데 어떤 방식으로 다가가야 할까요"
    )
    rep = builder.build_report(
        saju,
        use_llm=False,
        ref_year=2026,
        name="은채",
        concern=concern,
        product="integrated",
    )
    body = "\n".join(s.final_text for s in rep.sections)
    r = dq.analyze(body, pages=24, product="integrated", premium=True, concern=concern)
    rules = {f["rule"] for f in r["failures"]}
    assert r["clean"] is True, r
    assert "missing_frontloaded_answer" not in rules
    assert r["frontloaded_answer"]["ok"] is True
    assert r["near_term_timing"]["ok"] is True
    assert "군대" in body and "휴가나 외출" in body
    assert "학교와 전공이 같은 선후배" in body
    assert "짧은 안부" in body
    assert "재회합니다" not in body and "결혼합니다" not in body


def test_generated_question_type_matrix_keeps_customer_axes_visible(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from sajugen.calc import engine
    from sajugen.content import builder

    saju = engine.build(1988, 5, 14, 10, 0, is_male=False, horoscope_date="2026-06-01")
    cases = [
        {
            "concern": "연애를 못한 지 오래됐는데 앞으로 1년 안에 만남이 들어올까요. 소개팅을 받아도 되는지 궁금합니다",
            "contains": ["연애", "만남", "소개팅", "짧은 안부"],
            "absent": [],
        },
        {
            "concern": "나이가 있어서 언제 결혼운이 들어오는지 궁금합니다. 지금 만나는 사람과 결혼까지 봐도 될까요",
            "contains": ["결혼", "현재 만나는 사람", "생활 기준", "돈 관리"],
            "absent": [],
        },
        {
            "concern": "아파트 매매와 이사 시기가 궁금합니다. 계약과 잔금, 대출을 어떻게 조심해야 할까요",
            "contains": ["집과 이사", "계약", "잔금"],
            "absent": [],
        },
        {
            "concern": "모임을 창립하고 작은 사업도 같이 준비하려 합니다. 사람을 모으고 돈 관리를 어떻게 해야 할까요",
            "contains": ["모임 창립", "돈 관리", "역할"],
            "absent": ["이사와 집 문제", "집과 사람과 계약"],
        },
        {
            "concern": "이직과 수입 흐름이 궁금합니다. 올해 움직여도 되는지, 돈이 새는 부분은 무엇인지 알고 싶습니다",
            "contains": ["이직", "수입", "지출", "직업"],
            "absent": ["이사와 집 문제", "집과 사람과 계약"],
        },
        {
            "concern": "가지고 있는 땅이 언제 더 큰 자산이 될까요. 자식복과 재산이 크게 부풀어질 시점, 위험한 시점도 궁금합니다",
            "contains": ["땅과 자산", "자식복", "위험 시점", "개발 계획", "현금화 시점"],
            "absent": ["대인관계와 성향"],
        },
    ]
    for case in cases:
        rep = builder.build_report(
            saju,
            use_llm=False,
            ref_year=2026,
            name="고객",
            concern=case["concern"],
            product="integrated",
        )
        body = "\n".join(s.final_text for s in rep.sections)
        r = dq.analyze(body, pages=24, product="integrated", premium=True, concern=case["concern"])
        assert r["clean"] is True, (case["concern"], r)
        assert r["frontloaded_answer"]["ok"] is True, case["concern"]
        assert r["near_term_timing"]["ok"] is True, case["concern"]
        assert r["missing_axes"] == [], (case["concern"], r["missing_axes"])
        assert r["ziwei"]["ok"] is True, case["concern"]
        for term in case["contains"]:
            assert term in body, (case["concern"], term)
        for term in case["absent"]:
            assert term not in body, (case["concern"], term)
        assert "재회합니다" not in body and "결혼합니다" not in body
        assert "또렷" not in body


def test_love_or_reunion_question_requires_near_term_timing_and_action():
    text = (
        "재회 문제는 상대의 연락과 대화 태도를 보아야 합니다. "
        "상대가 실제로 대화를 이어 오는지 확인하세요. "
        "자미두수로 보면 사람과 관계, 돈의 부담이 함께 걸립니다. "
    ) * 70
    r = dq.analyze(text, pages=22, premium=True, concern="헤어진 사람과 재회가 될까요")
    assert "timing" in r["missing_axes"]
    assert r["clean"] is False


def test_premium_question_requires_frontloaded_answer_not_late_only():
    late_answer = (
        "정성스럽게 전체 흐름을 천천히 살펴보겠습니다. "
        "여러 갈래가 겹쳐 있으니 배경부터 길게 보겠습니다. "
    ) * 45
    late_answer += _premium_text()
    r = dq.analyze(
        late_answer,
        pages=27,
        product="integrated",
        concern="아파트 매매와 김포 이사, 로타리 클럽 창립 시기가 궁금합니다",
        expected_context_terms=["청마"],
    )
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_frontloaded_answer" in rules
    assert r["frontloaded_answer"]["ok"] is False


def test_reunion_question_requires_near_term_timing_not_only_generic_timing():
    text = (
        "결론부터 말하면 재회 문제는 상대의 연락과 대화 태도를 먼저 보아야 합니다. "
        "다가갈 때는 학교와 겹지인을 이용하되 부담을 주지 않는 말부터 시작하세요. "
        "시기는 너무 멀리 보지 말고 상대가 실제로 대화를 이어 오는지 확인해야 합니다. "
        "자미두수로 보면 사람과 관계, 돈의 부담이 함께 걸립니다. "
    ) * 45
    r = dq.analyze(
        text, pages=24, product="integrated", concern="헤어진 사람과 재회 시기가 궁금합니다"
    )
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_near_term_timing" in rules
    assert r["near_term_timing"]["required"] is True


def test_reunion_question_passes_with_one_year_timing_and_contact_action():
    text = (
        "결론부터 말하면 1년 안에서는 올해 하반기보다 내년 초가 더 조심스럽게 볼 구간입니다. "
        "먼저 연락을 세게 밀지 말고, 겹지인과 학교 접점을 통해 짧은 안부부터 여는 편이 좋습니다. "
        "상대가 대화를 이어 오면 다음 단계로 가고, 반응이 끊기면 한 번 물러서야 합니다. "
        "명리에서는 시기의 흐름을 먼저 보고 조심할 구간을 나눕니다. "
        "자미두수로 보면 관계와 사람의 자리가 함께 움직여, 연락보다 분위기 회복이 먼저입니다. "
    ) * 60
    r = dq.analyze(
        text, pages=24, product="integrated", concern="헤어진 사람과 재회 시기와 다가가는 방법"
    )
    assert r["near_term_timing"]["ok"] is True
    assert r["frontloaded_answer"]["ok"] is True
    assert "missing_near_term_timing" not in {f["rule"] for f in r["failures"]}


def test_love_axis_requires_action_caution_and_myeongni():
    text = (
        "결론부터 말하면 1년 안의 연애 흐름은 소개팅과 첫 만남에서 확인해야 합니다. "
        "자미두수로 보면 사람과 관계, 돈 관리의 부담도 함께 보입니다. "
        "올해와 내년의 흐름을 길게 설명합니다. "
    ) * 55
    r = dq.analyze(
        text, pages=24, product="integrated", concern="연애를 못했는데 만남이 들어올까요"
    )
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_love_reunion_action" in rules
    assert "missing_love_myeongni" in rules
    assert r["clean"] is False


def test_new_love_question_passes_with_meeting_action_caution_and_two_views():
    text = (
        "결론부터 말하면 1년 안에는 소개팅이나 가벼운 첫 만남으로 확인할 구간이 있습니다. "
        "먼저 대화를 이어 보는 자리로 두고, 서두르지 말고 상대가 다음 약속을 잡는지 보세요. "
        "조심할 점은 외로움 때문에 결론을 빨리 정하려는 마음입니다. "
        "명리에서는 시기의 흐름을 보고, 자미두수로 보면 사람과 관계, 돈 관리의 부담을 함께 봅니다. "
    ) * 60
    r = dq.analyze(
        text, pages=24, product="integrated", concern="연애를 못했는데 소개팅을 받아도 될까요"
    )
    assert r["clean"] is True, r
    assert r["love_action"]["ok"] is True
    assert r["love_myeongni"]["ok"] is True


def test_marriage_question_passes_with_conditions_money_caution_and_two_views():
    text = (
        "결론부터 말하면 1년 안의 결혼운은 현재 만나는 사람과 생활 기준을 맞추는지부터 보아야 합니다. "
        "먼저 돈 관리와 가족의 거리를 확인하고, 큰 약속은 서두르지 않는 것이 좋습니다. "
        "조심할 점은 감정만 앞서 결혼 이야기를 크게 잡는 흐름입니다. "
        "명리에서는 시기의 흐름을 보고, 자미두수로 보면 사람과 관계, 돈과 가족의 자리를 함께 봅니다. "
    ) * 60
    r = dq.analyze(
        text,
        pages=24,
        product="integrated",
        concern="언제 결혼운이 들어오고 지금 만나는 사람과 결혼까지 볼 수 있나요",
    )
    assert r["clean"] is True, r
    assert r["love_action"]["ok"] is True
    assert r["love_myeongni"]["ok"] is True


def test_ziwei_name_only_without_cross_domains_fails_premium():
    text = (
        "자미두수도 참고했습니다. "
        + ("설명을 이어갑니다. " * 40)
        + (
            "집 문제와 돈 문제와 사람 문제를 충분히 설명합니다. "
            "이사와 계약과 관계를 차분히 보아야 합니다. "
        )
        * 120
    )
    r = dq.analyze(text, pages=27, premium=True)
    rules = {f["rule"] for f in r["failures"]}
    assert "missing_usable_ziwei" in rules
    assert r["ziwei"]["markers"]
    assert len(r["ziwei"]["cross_domains"]) < 2


def test_customer_specific_context_requires_source_or_expected_context():
    r = dq.analyze(_premium_text(), pages=27, product="integrated")
    rules = {f["rule"] for f in r["failures"]}
    assert "unbacked_context_terms" in rules
    assert r["context_provenance"]["unbacked_terms"] == ["청마"]


def test_repetitive_ai_like_word_and_absolute_guarantee_fail():
    text = _premium_text() + " 또렷 또렷 100% 재회합니다"
    r = dq.analyze(text, pages=27, premium=True, concern="재회 시기가 궁금합니다")
    rules = {f["rule"] for f in r["failures"]}
    assert "repetitive_phrasing" in rules
    assert "absolute_guarantee" in rules


def test_context_required_for_helper():
    assert dq.context_required_for("integrated_full") is True
    assert dq.context_required_for("gunghap_relationship") is True
    assert dq.context_required_for("gunghap") is True
    assert dq.context_required_for("integrated") is False
    assert dq.context_required_for("personal") is False
    assert dq.context_required_for(None) is False


def test_context_required_without_concern_fails_missing_customer_context():
    # P1: 고객 질문 필수 상품인데 concern 부재 → 조용한 통과 금지.
    r = dq.analyze(_premium_text(), pages=57, product="integrated_full", context_required=True)
    assert r["has_customer_context"] is False
    assert "missing_customer_context" in {f["rule"] for f in r["failures"]}
    assert r["clean"] is False


def test_context_required_with_concern_passes_context_and_populates_axes():
    concern = "도와주는 사람과 시기가 궁금하고 어떻게 준비할지 알고 싶습니다"
    r = dq.analyze(
        _premium_text(),
        pages=57,
        product="integrated_full",
        concern=concern,
        context_required=True,
    )
    assert r["has_customer_context"] is True
    assert r["required_axes"] != []
    assert "missing_customer_context" not in {f["rule"] for f in r["failures"]}


def test_context_required_default_false_preserves_no_concern_paths():
    # 기존 무고객 합성/단위 경로 보존 — 기본 False 면 실패 추가 없음.
    r = dq.analyze(_premium_text(), pages=57, product="integrated_full")
    assert "missing_customer_context" not in {f["rule"] for f in r["failures"]}


_PF_CONCERN = "도와주는 사람과 시기가 궁금하고 어떻게 준비할지 알고 싶습니다"


def test_physical_frontloaded_flags_cover_toc_first_pages():
    # P5: 물리 p1~p3이 표지/목차뿐이고 답변이 p4 이후면 warning(보고)로 드러남.
    pages = ["표지", "차례", "인사말 페이지", _premium_text()]
    r = dq.analyze(
        _premium_text(),
        pages=57,
        product="integrated_full",
        concern=_PF_CONCERN,
        context_required=True,
        page_texts=pages,
    )
    pf = r["physical_frontloaded_answer"]
    assert pf["required"] is True
    assert pf["ok"] is False
    assert pf["answer_page"] == 4
    assert "physical_frontloaded_answer" in {w["rule"] for w in r["warnings"]}
    # 보고용 warning — failures 로는 올라가지 않는다(게이트 미변경).
    assert "physical_frontloaded_answer" not in {f["rule"] for f in r["failures"]}


def test_physical_frontloaded_ok_when_answer_in_first_pages():
    # P5: 물리 첫 페이지에 답변 근거가 있으면 ok=True, warning 없음.
    pages = [_premium_text(), "표지", "차례"]
    r = dq.analyze(
        _premium_text(),
        pages=57,
        product="integrated_full",
        concern=_PF_CONCERN,
        context_required=True,
        page_texts=pages,
    )
    pf = r["physical_frontloaded_answer"]
    assert pf["ok"] is True
    assert pf["answer_page"] == 1
    assert "physical_frontloaded_answer" not in {w["rule"] for w in r["warnings"]}


def test_physical_frontloaded_not_evaluated_without_concern_or_pages():
    # 기존 무고객/무페이지 경로 보존 — 평가 안 함, warning 없음.
    r = dq.analyze(_premium_text(), pages=57, product="integrated_full")
    assert r["physical_frontloaded_answer"]["required"] is False
    assert "physical_frontloaded_answer" not in {w["rule"] for w in r["warnings"]}


def test_guarantee_lint_flags_absolute_guarantee_family():
    # public 헬퍼는 absolute_guarantee 계열을 잡는다(compose 단계 가드용).
    assert dq.guarantee_lint("무조건")
    assert dq.guarantee_lint("결혼합니다")
    assert dq.guarantee_lint("재회합니다")
    assert dq.guarantee_lint("100%")
    assert dq.guarantee_lint("100 %")
    assert dq.guarantee_lint("반드시 성공")
    assert dq.guarantee_lint("확실히 된다")


def test_guarantee_lint_allows_non_guarantee_phrasing():
    # 결과 보장이 아닌 표현은 차단하지 않는다(과탐 회귀).
    assert dq.guarantee_lint("반드시 확인해 보세요") == []
    assert dq.guarantee_lint("결혼을 준비하는 마음으로 점검해 보세요") == []
    assert dq.guarantee_lint("") == []


def test_guarantee_lint_matches_analyze_criteria_no_drift():
    # public 헬퍼와 analyze() 의 absolute_guarantee 기준이 동일(중복정의·드리프트 없음).
    text = _premium_text() + " 결혼합니다 무조건 100%"
    assert dq.guarantee_lint(text) == dq.analyze(text, pages=27, premium=True)["guarantee_hits"]
    assert dq.guarantee_lint(text)


def test_guarantee_lint_catches_hard_outcome_that_safe_lint_misses():
    # retry3 갭: safe_lint 가 놓치는 보장형 hard-outcome 도 guarantee_lint 는 잡는다.
    from sajugen.content import safe_lint

    for phrase in ("이 흐름이면 두 분은 결혼합니다", "두 분은 무조건 잘 맞습니다"):
        assert safe_lint.lint(phrase) == []  # safe_lint 단독으로는 통과(갭)
        assert dq.guarantee_lint(phrase)  # guarantee_lint 가 안전망


def test_expected_context_missing_fails_and_overuse_warns():
    missing = dq.analyze(
        _premium_text(), pages=27, premium=True, expected_context_terms=["청마", "새이름"]
    )
    assert "새이름" in missing["missing_context_terms"]
    assert missing["clean"] is False

    overused_text = _premium_text() + " 청마 청마 청마 청마"
    overused = dq.analyze(overused_text, pages=27, premium=True, expected_context_terms=["청마"])
    assert overused["overused_context_terms"]["청마"] > 3
    assert overused["warnings"]


def test_pipeline_passes_product_and_concern_to_pdf_verify(monkeypatch):
    from sajugen import pipeline

    captured = {}

    def fake_verify(pdf_path, **kwargs):
        captured.update(kwargs)
        return {
            "gate_pass": True,
            "text_chars": 12_000,
            "tagged": True,
            "fonts_embedded": True,
        }

    monkeypatch.setattr(pipeline.render_pdf, "render_pdf", lambda *a, **k: "fake.pdf")
    monkeypatch.setattr(pipeline.render_verify, "verify", fake_verify)

    r = pipeline.generate(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
        product="integrated",
        concern="아파트 매매와 이사 시기가 궁금합니다",
    )
    assert r.ok is True
    assert captured["product"] == "integrated"
    assert captured["concern"] == "아파트 매매와 이사 시기가 궁금합니다"


def test_final_render_passes_order_product_and_concern_to_pdf_verify(monkeypatch):
    from sajugen import order_flow
    from sajugen.models.report import BirthInput, CalendarVerification, ReportPlan, UnifiedReport

    captured = {}

    def fake_verify(pdf_path, **kwargs):
        captured.update(kwargs)
        return {"gate_pass": True}

    report = UnifiedReport(
        order_id="ord_test",
        birth=BirthInput(gender="F", input_date="2000-01-01", concern_text="재회 시기"),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        report_plan=ReportPlan(product="integrated"),
        content={
            "sections": [
                {
                    "id": "consult",
                    "title": "상담",
                    "source_keys": ["input"],
                    "rule_text": "본문",
                    "final_text": "본문",
                    "polished": False,
                    "guard_violations": [],
                }
            ],
            "guard": {
                "safe_lint_total": 0,
                "factcheck_total": 0,
                "grounding_ok": True,
                "polished_sections": 0,
                "fallback_sections": 0,
                "clean": True,
            },
            "concern_category": None,
            "allow_tokens": {},
        },
        render_meta={
            "gen_params": {
                "product": "integrated",
                "concern": "재회 시기",
                "brand": "default",
            },
            "input_civil": "2000-01-01 12:00",
        },
    )
    monkeypatch.setattr(order_flow.render_pdf, "render_pdf", lambda *a, **k: "final.pdf")
    monkeypatch.setattr(order_flow.render_verify, "verify", fake_verify)

    assert order_flow.final_render_fn(report) == "final.pdf"
    assert captured["product"] == "integrated"
    assert captured["concern"] == "재회 시기"
