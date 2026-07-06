# -*- coding: utf-8 -*-
"""Phase 5(2026-07-06) — 설계 결정 논쟁 프로토콜 계약(산출물 rot 방지).

sg-design-critic 에이전트와 design_debate 템플릿이 프로토콜의 핵심 불변을 유지하는지 고정:
- 비평자 모델이 생성 모델(Sonnet)과 이질(자기선호 편향 회피, 2404.13076).
- 비평자는 읽기 전용(코드 수정 금지 — 비평만).
- 템플릿에 one-way door 트리거 + 루브릭 judge 분리 + 반박 ≤1 이 명시.
"""

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CRITIC = _ROOT / ".claude" / "agents" / "sg-design-critic.md"
_TEMPLATE = _ROOT / "handoff" / "templates" / "design_debate.md"


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    assert m, f"{path.name}: frontmatter(--- 블록) 필요"
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def test_critic_agent_exists_with_heterogeneous_readonly_config():
    assert _CRITIC.exists(), "sg-design-critic.md 필요"
    fm = _frontmatter(_CRITIC)
    # 비평 모델 = Opus, 생성 모델(Sonnet)과 이질 — 동일화 시 자기선호 편향 방어 무력.
    assert "opus" in fm.get("model", "").lower(), "비평자는 Opus(생성 Sonnet 과 이질)여야 함"
    assert "sonnet" not in fm.get("model", "").lower()
    # 읽기 전용(비평자는 코드 수정 금지) — Edit/Write 툴 부재.
    tools = fm.get("tools", "")
    assert "Edit" not in tools and "Write" not in tools, "비평자는 읽기 전용이어야 함"
    assert "Read" in tools


def test_critic_prompt_forbids_picking_winner():
    body = _CRITIC.read_text(encoding="utf-8")
    # 승자 선택은 별도 judge/운영자 몫 — 비평자는 실패만 드러낸다.
    assert "프리모템" in body
    assert "승자" in body and ("금지" in body or "고르지 마라" in body)


def test_debate_template_has_trigger_and_judge_separation():
    assert _TEMPLATE.exists(), "design_debate.md 필요"
    body = _TEMPLATE.read_text(encoding="utf-8")
    assert "one-way door" in body, "발동 트리거(one-way door) 명시 필요"
    assert "GATE_KEYS" in body and "발송 상태머신" in body, "트리거 체크리스트 필요"
    assert "루브릭" in body and "judge" in body, "루브릭 judge 단계 필요"
    assert "다른" in body and "모델" in body, "생성/비평/judge 모델 분리 명시 필요"
    assert "반박" in body, "반박 라운드(≤1) 명시 필요"
    assert "two-way door" in body, "two-way door 는 생략(남발 금지) 명시 필요"
