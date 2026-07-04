# -*- coding: utf-8 -*-
"""intro 직답 유지 가드(QI-2026-07-04-02 후속) 양방 회귀.

실사고(v5): intro 윤문이 골격의 '신청 질문부터 먼저 답하면' 직답 문단을 유실 →
문서 초반 1800자 frontload 게이트가 missing_frontloaded_answer 로 FAIL.
챕터 단위 선검사로 직답을 유실한 intro 후보는 폴백(골격=직답 보존, 항상 통과)된다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder, llm_polish, llm_sections  # noqa: E402
from sajugen.content.question_router import QuestionCategory  # noqa: E402

_SAJU = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
_CONCERN = "올해 몇월부터 돈이 들어올까요. 시기가 궁금합니다."


def _build_with_intro(monkeypatch, intro_text):
    class _Stub:
        name = "anthropic"

        def classify(self, concern):
            return QuestionCategory.WEALTH

        def compose(self, *, section_id, base_text, **kw):
            if section_id == "intro":
                return intro_text  # 직답 유실/보존 시나리오 주입
            return base_text + " 흐름이 이어집니다."

    monkeypatch.setattr(llm_sections, "get_backend", lambda: _Stub())
    monkeypatch.setattr(llm_polish, "polish", lambda text, title, **kw: text)
    return builder.build_report(
        _SAJU,
        use_llm=True,
        ref_year=2026,
        name="테스트",
        concern=_CONCERN,
        ref_date="2026-07-04",
    )


def test_intro_dropping_direct_answer_falls_back(monkeypatch):
    # 직답 없는 intro(인사+그릇 소개만) → 가드가 잡아 골격 폴백(직답 스냅샷 보존)
    r = _build_with_intro(
        monkeypatch,
        "테스트님 안녕하세요. 임수 일간의 그릇을 지닌 분입니다. 이 글은 원국부터 차례로 풀어 갑니다.",
    )
    intro = next(s for s in r.sections if s.id == "intro")
    assert intro.polished is False  # 폴백됨
    assert "신청 질문부터 먼저 답하면" in intro.final_text  # 골격 직답 복원


def test_intro_keeping_direct_answer_stays_polished(monkeypatch):
    # 직답(방향·시기·행동)을 유지한 intro 는 윤문 보존(과차단 0 앵커)
    r = _build_with_intro(
        monkeypatch,
        "테스트님 안녕하세요. 신청 질문부터 먼저 답하면, 올해 하반기 구간부터 재물 흐름이 "
        "살아나니 9월과 10월을 좋은 구간으로 보고, 지금은 지출을 정리하는 행동부터 시작하면 "
        "됩니다. 무리하게 서두르지 말고 확인하면서 움직이세요. 이제 그릇 이야기부터 차례로 풀겠습니다.",
    )
    intro = next(s for s in r.sections if s.id == "intro")
    assert intro.polished is True, intro.guard_violations
    assert "9월" in intro.final_text  # 윤문 유지
