# -*- coding: utf-8 -*-
"""Phase 7(2026-07-06) — 다층 검증 키트(vkit) 이식 규격 계약(rot 방지).

규격·정본·스킬·논쟁 기록이 핵심 불변을 유지하는지 고정: L0~L4 + 배포 결정(복사-벤더링,
pip/생성기 기각) + critic 이 드러낸 4 안전장치(특히 PII 형상 재정의) + no-op 자가검증.
"""

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = _ROOT / "docs" / "21-verification-kit.md"
_KIT = _ROOT / "handoff" / "kit"
_DEBATE = _ROOT / "handoff" / "kit" / "design-debate-vkit-distribution.md"
_VKIT = _ROOT / ".claude" / "skills" / "vkit" / "SKILL.md"


def test_spec_defines_all_five_layers():
    body = _SPEC.read_text(encoding="utf-8")
    for layer in ("L0", "L1", "L2", "L3", "L4"):
        assert re.search(rf"\*\*{layer}\*\*", body), f"{layer} 층 정의 필요"
    assert "이질 렌즈" in body and "advisory" in body  # L2
    assert "dead-param" in body  # L3
    assert "≤7" in body or "7항목" in body  # L4 다이어트 체크리스트


def test_distribution_decision_rejects_pip_and_generator():
    body = _SPEC.read_text(encoding="utf-8")
    assert "복사" in body and "벤더링" in body  # 채택 = 복사-적응 + 스탬프 벤더링
    assert "pip" in body and "금지" in body  # 안 B 기각
    assert "결정론" in body and "무의존" in body  # 하드게이트 불변 근거
    assert "ruff" in body  # Phase 2 선례(외부의존 거부)


def test_spec_has_four_adoption_safeguards():
    body = _SPEC.read_text(encoding="utf-8")
    assert "no-op 자가검증" in body
    assert "PII 형상 재정의" in body  # critic 치명 리스크 ②
    assert "이질성" in body
    assert "리터럴 치환" in body
    # 측정된 이식 경계표(critic "그대로 복사" 반증) + crypto PII 형상 예시
    assert "지갑" in body and "생년월일" in body


def test_kit_readme_and_manifest_valid():
    assert (_KIT / "README.md").exists()
    manifest = json.loads((_KIT / "manifest.template.json").read_text(encoding="utf-8"))
    assert "upstream_sha" in manifest
    sg = manifest["safeguards_verified"]
    assert set(sg) == {
        "no_op_self_check",
        "pii_shape_redefined",
        "heterogeneity_verified",
        "domain_literals_replaced",
    }
    assert all(v is False for v in sg.values()), (
        "안전장치는 사람이 통과시켜야 true(초기 전부 false)"
    )


def test_debate_record_is_dogfood_of_phase5():
    body = _DEBATE.read_text(encoding="utf-8")
    assert "sg-design-critic" in body  # Phase 5 프로토콜 실적용
    assert "출처 스탬프 벤더링" in body  # critic 간과된 3안 채택
    assert "복사-적응" in body and "판정" in body


def test_vkit_skill_scaffolds_but_forbids_shell_gates():
    body = _VKIT.read_text(encoding="utf-8")
    assert "스캐폴딩" in body
    # 스캐폴딩이라 Write 는 있으나, 껍데기 no-op 게이트 생성은 금지(fail-closed).
    assert "껍데기" in body and ("금지" in body or "no-op" in body.lower())
    assert "PII" in body and "재정의" in body  # 도메인 PII 형상 필수
