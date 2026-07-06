# -*- coding: utf-8 -*-
"""Phase 3(2026-07-06, C3) — 게이트 커버리지 레지스트리 양방 계약.

docs/20-gate-coverage.md 의 "GATE_KEYS 레지스트리" 표를 live sajugen.render.verify.GATE_KEYS
와 양방 대조한다. 하드코딩 복사가 아니라 SSOT(상수)를 읽어(Phase 1 이 죽인 드리프트 버그를
재도입하지 않음), docs/20 을 '테스트된 산출물'로 만든다:
  - 모든 GATE_KEY 가 표에 행이 있어야 한다(미문서화 게이트 → RED — C3 사각 차단).
  - 표의 모든 게이트 행이 live GATE_KEY 여야 한다(팬텀 행 → RED — 문서 rot 차단).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.render import verify  # noqa: E402

_DOC = Path(__file__).resolve().parents[1] / "docs" / "20-gate-coverage.md"


def _parse_registry_keys() -> list[str]:
    """docs/20 의 'GATE_KEYS 레지스트리' 절 표에서 1열 backtick 키만 추출(그 절 한정 —
    벨트 표·커버리지 매트릭스의 backtick 은 제외)."""
    lines = _DOC.read_text(encoding="utf-8").splitlines()
    keys: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## GATE_KEYS 레지스트리"):
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break  # 컴포즈 벨트 하위절에서 종료
        if in_section and line.startswith("|"):
            first_cell = line.split("|")[1]
            m = re.search(r"`([a-z_]+)`", first_cell)
            if m:
                keys.append(m.group(1))
    return keys


def test_registry_matches_gate_keys_both_directions():
    doc_keys = _parse_registry_keys()
    live = list(verify.GATE_KEYS)
    # 파싱 자체 건전성(헤더/구분선 오포함 방지) — 최소 20행.
    assert len(doc_keys) >= 20, f"레지스트리 표 파싱 실패({len(doc_keys)}행)"
    missing = [k for k in live if k not in doc_keys]  # 게이트에 있으나 문서 없음
    phantom = [k for k in doc_keys if k not in set(live)]  # 문서에 있으나 게이트 없음
    assert not missing, f"docs/20 에 행이 없는 GATE_KEY(미문서화): {missing}"
    assert not phantom, f"docs/20 에 있으나 live GATE_KEY 아님(팬텀 행): {phantom}"


def test_registry_has_no_duplicate_rows():
    doc_keys = _parse_registry_keys()
    dupes = {k for k in doc_keys if doc_keys.count(k) > 1}
    assert not dupes, f"레지스트리 중복 행: {dupes}"
