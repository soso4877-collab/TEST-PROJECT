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
            self, *, section_id, title, category, base_text, quoted_concern, ref_year, call_name
        ):
            sent.append(("compose", title, base_text or ""))
            if quoted_concern:
                sent.append(("compose_quoted", title, quoted_concern))
            return base_text  # 폴백 흉내(전송만 관찰)

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
