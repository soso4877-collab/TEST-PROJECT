# -*- coding: utf-8 -*-
"""T0-④ 상담가 페르소나 메타발화 제거 회귀.

정규식 하드 게이트를 만들지 않고, 확정 제거한 보일러플레이트 문구와
문맥형으로 유지해야 하는 문구만 좁게 고정한다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import delivery_quality, rules, safe_lint  # noqa: E402


def _sections() -> dict[str, str]:
    # PII 0 합성 입력. 지역 키워드는 문맥형 "병원과 장보기" 앵커를 생성한다.
    saju = engine.build(1989, 1, 2, 7, 40, is_male=False, horoscope_date="2026-06-01")
    return rules.build_all(
        saju,
        ref_year=2026,
        name="테스트",
        concern_category="건강",
        concern_text="김포와 계양 중 생활 동선이 궁금한 합성 고민입니다.",
    )


def test_removed_disclaimer_boilerplate_does_not_return():
    sections = _sections()
    target = "\n".join(sections[sid] for sid in ("work", "health", "flow"))

    removed = [
        "합격이나 취업의 결과를 단정하지는 않습니다",
        "수익이나 손실을 단정하거나 보장하지는 않습니다",
        "병원 진료로 먼저 확인해 보세요",
        "병원에서 확인해 보세요",
        "결과지에서는 큰 흐름만 짚어 드리며",
        "특정 달에 특정 사건이 일어난다고 단정하지 않습니다",
    ]
    for phrase in removed:
        assert phrase not in target


def test_contextual_health_and_region_phrasing_stays():
    sections = _sections()

    # 건강장은 진단이 아니라 생활 리듬을 살피는 프레이밍까지 지우면 안 된다.
    assert "병을 진단하는 자리가 아니라" in sections["health"]

    # 지역 비교 맥락에서 나온 생활권 문장은 의료 회피형 보일러플레이트가 아니므로 유지한다.
    assert "병원과 장보기" in sections["consult"]


def test_metadiscourse_cleanup_keeps_safety_guards_clean():
    sections = _sections()

    for sid in ("work", "health", "flow"):
        text = sections[sid]
        assert safe_lint.lint(text) == [], (sid, safe_lint.lint(text))
        assert delivery_quality.guarantee_lint(text) == [], (
            sid,
            delivery_quality.guarantee_lint(text),
        )
