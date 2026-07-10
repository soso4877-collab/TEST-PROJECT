# -*- coding: utf-8 -*-
"""Phase 4(2026-07-06) — hsweep 계약 테스트 (전부 API 0, FakeBackend 주입).

검증 대상은 '위험한 표면': API 로 나가는 것(PII)·비용 상한·advisory 구조·모델 이질성.
FakeBackend 가 전송 입력(system/user)을 캡처해 실제로 무엇이 나가는지 단언한다.
"""

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hsweep  # noqa: E402
from sajugen import config as cfg  # noqa: E402


class FakeBackend:
    """전송 입력 캡처 + 정해진 응답. in/out 토큰 주입으로 캡 분기 테스트."""

    def __init__(self, reply="[]", in_tok=100, out_tok=100):
        self.calls = []
        self.reply, self.in_tok, self.out_tok = reply, in_tok, out_tok

    def complete(self, *, model, system, user):
        self.calls.append({"model": model, "system": system, "user": user})
        return self.reply, self.in_tok, self.out_tok


# ── 1) PII: API 로 나가는 것에 이름·날짜가 없어야 한다(가장 중요) ──
def test_mask_for_api_removes_name_and_birth():
    masked = hsweep.mask_for_api("김민준님 1997-10-27 09:46 태생", ["김민준"])
    assert "김민준" not in masked
    assert "1997-10-27" not in masked and "09:46" not in masked


def test_mask_for_api_masks_korean_birthdate_with_self_civil_not_timing():
    # self_civils 정밀 마스킹: 한글 형식 생년월일은 막되(_DATE_RX 미커버) 사주 시기 참조
    # (같은 'N월 D일'이라도 생일이 아닌 것)는 오마스킹하지 않는다.
    text = "1997년 10월 27일생입니다. 그리고 2026년 3월 5일에 좋은 흐름이 옵니다."
    masked = hsweep.mask_for_api(text, ["김민준"], self_civils=["1997-10-27 09:46"])
    assert "1997년 10월 27일" not in masked  # 생일 한글형 마스킹됨
    assert "3월 5일" in masked  # 시기 참조는 보존(오마스킹 금지)


def test_outgoing_payload_never_contains_pii():
    # 정상 마스킹된 페이지로 스윕 → FakeBackend 가 받은 어떤 system/user 에도 PII 없음.
    pages = [hsweep.mask_for_api("김민준님의 재물 흐름 1997-10-27 분석", ["김민준"])]
    be = FakeBackend()
    hsweep.sweep("x.pdf", ["김민준"], backend=be, masked_pages=pages)
    assert be.calls, "백엔드가 호출돼야 한다"
    for c in be.calls:
        blob = c["system"] + c["user"]
        assert "김민준" not in blob
        assert not hsweep._DATE_RX.search(blob), "날짜/시각이 전송되면 안 된다"


def test_belt_blocks_send_when_name_survives_masking():
    # 마스킹 누락 시나리오(페이지에 이름 잔존) → 전송 벨트가 예외로 차단(fail-closed).
    be = FakeBackend()
    with pytest.raises(hsweep.PIILeakBlocked):
        hsweep.sweep("x.pdf", ["김민준"], backend=be, masked_pages=["김민준 잔존 텍스트"])
    assert be.calls == [], "차단 시 아무 것도 전송되지 않아야 한다"


def test_names_required_fail_closed():
    be = FakeBackend()
    with pytest.raises(hsweep.PIILeakBlocked):
        hsweep.sweep("x.pdf", None, backend=be, masked_pages=["안전 텍스트"])


def test_empty_names_list_also_fail_closed():
    # 빈 리스트도 is None 가드를 우회하면 안 된다(마스킹 no-op → PII 유출 구멍).
    be = FakeBackend()
    with pytest.raises(hsweep.PIILeakBlocked):
        hsweep.sweep("x.pdf", [], backend=be, masked_pages=["안전 텍스트"])
    with pytest.raises(hsweep.PIILeakBlocked):
        hsweep.mask_for_api("본문", [])
    assert be.calls == []


def test_refute_and_judge_payloads_carry_no_pii_from_rationale():
    # 렌즈가 rationale 에 이름을 되뱉어도 refute/judge 로 나가는 페이로드에 이름이 없어야 한다
    # (parse 스크럽 + _safe_call 벨트 이중 방어). lens 만이 아니라 다운스트림까지 검증.
    leaky = '[{"page":2,"severity":"high","rule":"x","rationale":"김민준 관련 메타"}]'

    class Seq(FakeBackend):
        def complete(self, *, model, system, user):
            self.calls.append({"model": model, "system": system, "user": user})
            if "opus" in model:
                return "0.9", 10, 2  # judge
            if "적대적 검증자" in system:
                return leaky, 20, 20  # refute 도 이름 되뱉기 시도
            return leaky, 20, 20  # lens

    be = Seq()
    hsweep.sweep("x.pdf", ["김민준"], backend=be, masked_pages=["안전 본문"])
    assert len(be.calls) > len(hsweep.LENS_IDS), "refute/judge 단계까지 도달해야 검증됨"
    for c in be.calls:
        assert "김민준" not in c["system"] + c["user"], "다운스트림 페이로드에 이름 유출"


def test_main_refuses_without_names_and_without_lock(monkeypatch):
    assert hsweep.main(["--pdf", "x.pdf"]) == 2  # names 없음
    # 이름 있어도 3중 잠금 미충족이면 실행 거부(실 API 미승인)
    monkeypatch.delenv("SAJUGEN_HARNESS_ALLOW_REGEN", raising=False)
    assert hsweep.main(["--pdf", "x.pdf", "--name", "홍길동"]) == 3


# ── 2) 비용 상한: pre-call fail-closed + 부분 리포트 ──
def test_cost_cap_halts_with_partial_report():
    # 첫 콜이 폭발적 토큰을 보고 → 다음 check_before 가 상한 초과로 중단.
    be = FakeBackend(reply="[]", in_tok=1, out_tok=10_000_000)
    pages = [hsweep.mask_for_api("안전한 본문", ["홍길동"])]
    rep = hsweep.sweep("x.pdf", ["홍길동"], backend=be, masked_pages=pages)
    assert rep["partial"] is True
    assert "partial_reason" in rep
    assert rep["cost_usd"] > 0  # 실사용 관측 기록
    assert len(be.calls) < len(hsweep.LENS_IDS), "상한 초과 후 남은 렌즈는 호출되지 않아야 한다"


# ── 3) advisory: 구조적으로 게이트/주문 모듈 비접촉 ──
def test_hsweep_does_not_import_gate_or_order_modules():
    src = (Path(hsweep.__file__)).read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    forbidden = ("sajugen.render.verify", "order_flow", "hrun", "hsummary", "hstate")
    for f in forbidden:
        assert not any(f in m for m in imported), f"advisory 위반: {f} import 금지"


def test_report_is_advisory_and_has_no_gate_field():
    be = FakeBackend()
    rep = hsweep.sweep("x.pdf", ["홍길동"], backend=be, masked_pages=["안전 텍스트"])
    assert rep.get("advisory") is True
    assert "gate_pass" not in rep and "clean" not in rep


def test_findings_schema_has_no_freetext_customer_field():
    # 모델이 본문을 되뱉어도 파서가 스키마 밖 필드를 버린다(고객 본문 자유텍스트 유입 차단).
    malicious = (
        '[{"page":3,"severity":"high","rule":"x","rationale":"ok","verbatim":"김민준 원문"}]'
    )
    parsed = hsweep._parse_findings(malicious, "narrator_tone", ["김민준"])
    assert parsed and set(parsed[0].keys()) == {"lens", "page", "severity", "rule", "rationale"}
    assert "verbatim" not in parsed[0]
    assert "김민준" not in parsed[0]["rationale"]  # rationale free-text 스크럽


# ── 4) 모델 이질성: 렌즈 ≠ judge ──
def test_lens_and_judge_models_differ():
    assert cfg.llm_model("sweep_lens") != cfg.llm_model("sweep_judge")


# ── 5) 렌즈 프롬프트 계약: 5파일 존재 + 인용 금지 + JSON 스키마 ──
def test_lens_prompts_exist_and_forbid_quoting():
    for lens_id in hsweep.LENS_IDS:
        p = hsweep._PROMPT_DIR / f"lens_{lens_id}.md"
        assert p.exists(), f"렌즈 프롬프트 없음: {lens_id}"
        body = p.read_text(encoding="utf-8")
        assert "인용하지 마라" in body, f"{lens_id}: verbatim 인용 금지 지시 필요"
        assert "JSON" in body and "rationale" in body, f"{lens_id}: 출력 스키마 명시 필요"


# ── 파이프라인 전 단계가 FakeBackend 로 검증됨(happy path + judge 순서 스왑) ──
def test_full_pipeline_with_fake_backend():
    finding = (
        '[{"page":5,"severity":"high","rule":"document_self_reference","rationale":"메타 발화"}]'
    )

    class Seq(FakeBackend):
        def complete(self, *, model, system, user):
            self.calls.append({"model": model, "system": system, "user": user})
            if "judge" in model or "opus" in model or "채점" in system:
                return "0.9", 50, 5
            if "적대적 검증자" in system:
                return finding, 50, 50  # refute: 후보 유지
            return finding, 50, 50  # lens

    be = Seq()
    rep = hsweep.sweep("x.pdf", ["홍길동"], backend=be, masked_pages=["안전 본문"])
    assert rep["candidates"] >= 1
    assert rep["confirmed"] >= 1
    # judge 순서 스왑 = 확정 후보당 2콜(자기선호/위치 편향 완화)
    judge_calls = [c for c in be.calls if "opus" in c["model"]]
    assert len(judge_calls) % 2 == 0 and len(judge_calls) >= 2
