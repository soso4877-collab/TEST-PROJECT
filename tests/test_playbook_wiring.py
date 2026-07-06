# -*- coding: utf-8 -*-
"""Phase 8(2026-07-06) — 플레이북(docs/19) 다층검증 배선 계약(rot 방지).

로드맵이 docs/19 에 연결한 핵심 배선이 조용히 사라지지 않게 고정: 주기 루틴↔스킬(/audit·
/adjacent·/done)·발송 전 스윕, 경고 다이어트 원칙(≤10·≤7·1:1), one-way door↔논쟁 트리거.
프로즈 세부가 아니라 구조적 연결만 검사(브리틀 회피).
"""

from pathlib import Path

_DOC = (Path(__file__).resolve().parents[1] / "docs" / "19-operator-playbook.md").read_text(
    encoding="utf-8"
)


def test_routines_wire_ops_skills_and_sweep():
    assert "/audit" in _DOC and "/adjacent" in _DOC and "/done" in _DOC
    assert "hsweep" in _DOC or "이질 렌즈 스윕" in _DOC  # 발송 전 스윕 루틴
    assert "mutation" in _DOC  # 월 감사/대형변경 후 mutation


def test_alarm_diet_principle_present():
    assert "경고 다이어트" in _DOC
    assert "≤ 10건" in _DOC or "≤10건" in _DOC  # 스윕 상한
    assert "≤ 7항목" in _DOC or "≤7항목" in _DOC  # 체크리스트
    assert "1:1" in _DOC  # 알람:인시던트
    assert "폐기 검토" in _DOC  # advisory 순증 금지


def test_debate_trigger_table_wired_to_oneway_doors():
    assert "설계 논쟁 프로토콜" in _DOC
    assert "sg-design-critic" in _DOC
    assert "GATE_KEYS" in _DOC and "발송 상태머신" in _DOC  # 트리거 항목
    assert "two-way door 는 생략" in _DOC  # 남발 금지


def test_session_template_has_layer_marking():
    assert "L0~L4 어느 층" in _DOC  # 세션 시작 시 변경 층 표기
