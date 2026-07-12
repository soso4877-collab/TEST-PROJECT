# -*- coding: utf-8 -*-
"""T1.2 [P0-2] 표지 polish 경로의 생년월일 원본 API 전송 차단 + masking 방어겹.

절대규칙 17: LLM 입력에 생년월일 원본·출생지 비전달(파생 계산값만).
감사 P0-2: cover 룰 텍스트에 input_civil 원문이 있어 polish 로 API 전송되던 결함.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, llm_sections, masking  # noqa: E402
from sajugen.content.question_router import classify as _rule_classify  # noqa: E402

# 생년월일/시각 패턴: YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD, HH:MM, 8자리 생일
_DOB_RX = re.compile(
    r"\d{4}[-./]\d{2}[-./]\d{2}|(?<!\d)\d{2}:\d{2}(?!\d)|(?<![\d-])(?:19|20)\d{6}(?![\d-])"
)


def test_mask_birth_in_text_masks_all_variants():
    civil = "1989-01-02 07:40"
    for raw in (
        "저는 1989-01-02 07:40에 태어났어요",
        "생일은 1989.01.02 입니다",
        "1989/01/02 07:40",
        "19890102 생",
        "1989년 1월 2일 오전에",
    ):
        masked = masking.mask_birth_in_text(raw, civil)
        assert not _DOB_RX.search(masked), (raw, masked)
    # 무관 텍스트/무civil 은 그대로
    assert masking.mask_birth_in_text("간지와 오행 이야기", civil) == "간지와 오행 이야기"
    assert masking.mask_birth_in_text("1989-01-02", None) == "1989-01-02"


def test_mask_concern_still_masks_birth_after_refactor():
    # 리팩터(mask_birth_in_text 추출) 후에도 mask_concern 동작 보존 회귀
    out = masking.mask_concern("제 생일 1989-01-02 07:40 관련 고민", self_civil="1989-01-02 07:40")
    assert not _DOB_RX.search(out), out
    assert masking.mask_concern("") == ""


def test_cover_and_birthdate_never_sent_to_llm(monkeypatch):
    """build_report(use_llm=True) 가 LLM 으로 실제 전송하는 모든 텍스트에 생년월일 0건 +
    표지(cover)가 polish/compose 어느 경로에도 오르지 않음을 실측."""
    sent: list[tuple[str, str, str]] = []  # (kind, title, outbound_text)

    class MockBackend:
        name = "anthropic"

        def classify(self, concern):
            return _rule_classify(concern)

        def compose(
            self,
            *,
            section_id,
            title,
            category,
            base_text,
            quoted_concern,
            ref_year,
            call_name,
            ref_date=None,
            feedback=None,
        ):
            sent.append(("compose", title, base_text or ""))
            if quoted_concern:
                sent.append(("compose_quoted", title, quoted_concern))
            return llm_sections.ComposeResult(
                base_text,
                cache_observed=True,
                api_succeeded=True,
            )  # 폴백 흉내(전송만 관찰)

    monkeypatch.setattr(llm_sections, "get_backend", lambda: MockBackend())

    def spy_polish(rule_text, title, *, mask_civil=None):
        # 실제 API 로 나가는 텍스트 = polish 내부 마스킹 적용 후
        outbound = masking.mask_birth_in_text(rule_text, mask_civil) if mask_civil else rule_text
        sent.append(("polish", title, outbound))
        return rule_text

    monkeypatch.setattr(builder.llm_polish, "polish", spy_polish)

    # 가상 입력(PII 아님). input_civil 이 cover 룰 텍스트에 박히는 경로를 탄다.
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    builder.build_report(saju, use_llm=True, name="가나다", ref_year=2026)

    assert sent, "LLM 경로가 전혀 호출되지 않음 — mock backend 배선 확인"
    leaks = [(k, t) for k, t, txt in sent if _DOB_RX.search(txt)]
    assert leaks == [], f"생년월일 전송 누출: {leaks}"
    # 표지(cover)는 어떤 LLM 경로에도 전달되지 않아야(제목에 '결과지' 포함으로 식별)
    assert all("결과지" not in t for _, t, _ in sent), "cover 가 LLM 경로에 노출됨"


def test_mask_time_expressions_extended():
    # T4.3/G-6: 12시간제(오전/오후 H시 M분·H시)·'H시반' 시각 표기도 마스킹.
    civil = "1989-01-02 07:40"
    for raw in (
        "저는 07:40에 태어났어요",
        "저는 7시 40분에 태어났어요",
        "오전 7시 40분생입니다",
        "오전 7시쯤 태어났다고 들었어요",  # 시(hour) 단독
    ):
        assert masking._MASK_T in masking.mask_birth_in_text(raw, civil), raw


def test_mask_time_no_overmask():
    # 과다 마스킹 금지: 출생시각(07:40)과 다른 시각·일반 숫자는 보존.
    civil = "1989-01-02 07:40"
    for raw in (
        "오전 7시 15분에 회의가 있어요",  # 다른 분(부분 치환 금지)
        "오후 3시에 약속이 있습니다",  # 다른 시
        "7시반에 만나기로 했어요",  # 출생분=40이라 '반' 아님
        "커피 7잔을 마셨어요",  # 시각 아님
    ):
        assert masking._MASK_T not in masking.mask_birth_in_text(raw, civil), raw
    # 출생분이 30이면 '7시반'은 마스킹, '7시 15분'은 보존
    c30 = "1990-05-20 07:30"
    assert masking._MASK_T in masking.mask_birth_in_text("오전 7시반에 태어났어요", c30)
    assert masking._MASK_T not in masking.mask_birth_in_text("오전 7시 15분 회의", c30)


def test_audit_note_and_delete_reason_mask_birthdate():
    # T1.3/E-2: audit note·delete reason 이 mask_birth_in_text 로 위임돼 생년월일이 남지 않음
    civil = "1989-01-02 07:40"
    note = masking.mask_birth_in_text("ValueError: bad birth 1989-01-02 07:40", civil)
    assert not _DOB_RX.search(note), note
    # civil 없이도 8자리 생일형 숫자는 보수적 마스킹(delete reason 경로)
    assert not _DOB_RX.search(masking.mask_birth_in_text("파기 사유 19890102", None))
    assert masking.mask_birth_in_text("", None) == ""
