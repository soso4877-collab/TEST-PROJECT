# -*- coding: utf-8 -*-
"""Phase 6(2026-07-06) — 운영 자동화 스킬 계약(/audit·/adjacent·/done rot 방지).

스킬 정의가 핵심 불변을 유지하는지 고정: 유효 frontmatter, /adjacent·/audit 는 읽기 전용
(advisory — 코드 수정 금지), /done 은 증거 3종(pytest·SHA·명령) 명시.
"""

import re
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"


def _read(name: str) -> tuple[dict, str]:
    text = (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^---\n(.*?)\n---\n(.*)", text, re.S)
    assert m, f"{name}: frontmatter 필요"
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, m.group(2)


def test_all_three_skills_exist_with_valid_frontmatter():
    for name in ("audit", "adjacent", "done"):
        fm, body = _read(name)
        assert fm.get("name") == name
        assert fm.get("description"), f"{name}: description 필요"
        assert "user-invocable: true" in (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        assert len(body) > 200, f"{name}: 본문 지시 필요"


def test_advisory_skills_are_read_only():
    # /adjacent·/audit 는 발견·기록만(코드 수정 금지) — allowed-tools 에 Write/Edit 부재.
    for name in ("adjacent", "audit"):
        raw = (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        fm_block = re.search(r"^---\n(.*?)\n---", raw, re.S).group(1)
        assert "Write" not in fm_block and "Edit" not in fm_block, f"{name}: 읽기 전용이어야 함"
        assert "Read" in fm_block


def test_done_requires_evidence_triplet():
    _, body = _read("done")
    assert "pytest" in body and "SHA" in body
    assert "실행 명령" in body and "출력" in body
    assert "추정 금지" in body or "실측만" in body  # 주장으로 대체 금지


def test_audit_covers_doc_code_and_postmortem_and_mutation():
    _, body = _read("audit")
    assert "문서" in body and "코드" in body  # 문서-코드 대조
    assert "docs/16" in body and "포스트모템" in body  # 포스트모템 리뷰
    assert "mutation" in body.lower() or "변이" in body  # mutation testing
    assert "verify.py" in body and "temporal_lint" in body  # D-2 대상 명시
    assert "미검증" in body  # 회의적 재검증(확인 못 한 것 분리)


def test_adjacent_lists_boundary_and_scope_axes():
    _, body = _read("adjacent")
    assert "경계값" in body and "스코프 제외" in body
    assert "골격" in body  # 동일 문구 타 골격 동기화
    assert "advisory" in body.lower()
