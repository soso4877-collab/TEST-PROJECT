# -*- coding: utf-8 -*-
"""Phase 4(2026-07-06) — hsweep 계약 테스트 (전부 API 0, FakeBackend 주입).

검증 대상은 '위험한 표면': API 로 나가는 것(PII)·비용 상한·advisory 구조·모델 이질성.
FakeBackend 가 전송 입력(system/user)을 캡처해 실제로 무엇이 나가는지 단언한다.
"""

import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hsweep  # noqa: E402
from sajugen import config as cfg  # noqa: E402
from sajugen.content import llm_usage  # noqa: E402


class FakeBackend:
    """전송 입력 캡처 + 정해진 응답. in/out 토큰 주입으로 캡 분기 테스트."""

    def __init__(self, reply="[]", in_tok=100, out_tok=100):
        self.calls = []
        self.reply, self.in_tok, self.out_tok = reply, in_tok, out_tok

    def complete(self, *, model, system, user):
        self.calls.append({"model": model, "system": system, "user": user})
        return self.reply, self.in_tok, self.out_tok


def _payload_candidate_ids(user: str) -> list[str]:
    try:
        payload = json.loads(user)
    except json.JSONDecodeError:
        return []
    return [
        candidate["candidate_id"]
        for group in payload.get("page_groups", [])
        for candidate in group.get("candidates", [])
    ]


class PipelineBackend(FakeBackend):
    """렌즈·ranker·batch judge 응답을 구분하는 API 0 합성 백엔드."""

    def __init__(self, lens_reply: str, *, disposition="supported", score=0.9):
        super().__init__()
        self.lens_reply = lens_reply
        self.disposition = disposition
        self.score = score

    def complete(self, *, model, system, user):
        self.calls.append({"model": model, "system": system, "user": user})
        candidate_ids = _payload_candidate_ids(user)
        if "opus" in model:
            reply = [
                {"candidate_id": candidate_id, "score": self.score, "reason_code": "grounded"}
                for candidate_id in candidate_ids
            ]
            return json.dumps(reply), 50, 10
        if "비파괴 결함 후보 순위기" in system:
            reply = [
                {
                    "candidate_id": candidate_id,
                    "disposition": self.disposition,
                    "confidence": 0.8,
                    "reason_code": "ranked",
                }
                for candidate_id in candidate_ids
            ]
            return json.dumps(reply), 50, 10
        return self.lens_reply, 50, 10


def _write_synthetic_manifest(tmp_path: Path, subjects: list[dict] | None = None) -> Path:
    path = tmp_path / "pii-manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "subjects": subjects
                or [{"name": "DOC_A", "input_civil": "2000-01-02 09:46"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


# ── 1) PII: API 로 나가는 것에 이름·날짜가 없어야 한다(가장 중요) ──
def test_mask_for_api_removes_name_and_birth():
    masked = hsweep.mask_for_api("DOC_A님 2000-01-02 09:46 태생", ["DOC_A"])
    assert "DOC_A" not in masked
    assert "2000-01-02" not in masked and "09:46" not in masked


def test_mask_for_api_masks_korean_birthdate_with_self_civil_not_timing():
    # self_civils 정밀 마스킹: 한글 형식 생년월일은 막되(_DATE_RX 미커버) 사주 시기 참조
    # (같은 'N월 D일'이라도 생일이 아닌 것)는 오마스킹하지 않는다.
    text = "2000년 1월 2일생입니다. 그리고 2026년 3월 5일에 좋은 흐름이 옵니다."
    masked = hsweep.mask_for_api(text, ["DOC_A"], self_civils=["2000-01-02 09:46"])
    assert "2000년 1월 2일" not in masked  # 생일 한글형 마스킹됨
    assert "3월 5일" in masked  # 시기 참조는 보존(오마스킹 금지)


def test_outgoing_payload_never_contains_pii():
    # 정상 마스킹된 페이지로 스윕 → FakeBackend 가 받은 어떤 system/user 에도 PII 없음.
    pages = [hsweep.mask_for_api("DOC_A님의 재물 흐름 2000-01-02 분석", ["DOC_A"])]
    be = FakeBackend()
    hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=pages)
    assert be.calls, "백엔드가 호출돼야 한다"
    for c in be.calls:
        blob = c["system"] + c["user"]
        assert "DOC_A" not in blob
        assert not hsweep._DATE_RX.search(blob), "날짜/시각이 전송되면 안 된다"


def test_belt_blocks_send_when_name_survives_masking():
    # 마스킹 누락 시나리오(페이지에 이름 잔존) → 전송 벨트가 예외로 차단(fail-closed).
    be = FakeBackend()
    with pytest.raises(hsweep.PIILeakBlocked):
        hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=["DOC_A 잔존 텍스트"])
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
    leaky = '[{"page":1,"severity":"high","rule":"x","rationale":"DOC_A 관련 메타"}]'

    class Seq(FakeBackend):
        def complete(self, *, model, system, user):
            self.calls.append({"model": model, "system": system, "user": user})
            if "opus" in model:
                return "0.9", 10, 2  # judge
            if "적대적 검증자" in system:
                return leaky, 20, 20  # refute 도 이름 되뱉기 시도
            return leaky, 20, 20  # lens

    be = Seq()
    hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=["안전 본문"])
    assert len(be.calls) > len(hsweep.LENS_IDS), "refute/judge 단계까지 도달해야 검증됨"
    for c in be.calls:
        assert "DOC_A" not in c["system"] + c["user"], "다운스트림 페이로드에 이름 유출"


def test_main_rejects_raw_pii_argv_without_echo(capsys):
    assert hsweep.main(["--pdf", "x.pdf", "--name", "DOC_A"]) == 2
    captured = capsys.readouterr()
    assert "DOC_A" not in captured.out + captured.err
    assert "원시 개인정보 CLI 인자 금지" in captured.err


@pytest.mark.parametrize(
    "argv",
    (["--help"], ["-h"], ["sweep", "--help"], ["review", "--help"]),
)
def test_cli_help_is_a_successful_non_api_operation(monkeypatch, argv):
    monkeypatch.setattr(
        hsweep,
        "AnthropicSweepBackend",
        lambda: pytest.fail("help must not construct API backend"),
    )

    assert hsweep.main(argv) == 0


def test_main_requires_valid_ignored_manifest_before_lock(monkeypatch, tmp_path, capsys):
    assert hsweep.main(["sweep", "--pdf", "x.pdf"]) == 2
    manifest = _write_synthetic_manifest(tmp_path)
    monkeypatch.setattr(hsweep, "_is_ignored_local_manifest", lambda path: True)
    monkeypatch.delenv("SAJUGEN_HARNESS_ALLOW_REGEN", raising=False)
    assert hsweep.main(["sweep", "--pdf", "x.pdf", "--pii-manifest", str(manifest)]) == 3
    captured = capsys.readouterr()
    assert "DOC_A" not in captured.out + captured.err
    assert "2000-01-02" not in captured.out + captured.err


def test_invalid_manifest_stops_before_pdf_or_backend(monkeypatch, tmp_path, capsys):
    manifest = _write_synthetic_manifest(tmp_path)
    manifest.write_text('{"schema_version":2,"subjects":[]}', encoding="utf-8")
    monkeypatch.setattr(hsweep, "_is_ignored_local_manifest", lambda path: True)
    monkeypatch.setattr(
        hsweep,
        "extract_masked_pages",
        lambda *args, **kwargs: pytest.fail("invalid manifest must stop before PDF"),
    )
    monkeypatch.setattr(
        hsweep,
        "AnthropicSweepBackend",
        lambda: pytest.fail("invalid manifest must stop before backend"),
    )
    assert hsweep.main(["sweep", "--pdf", "x.pdf", "--pii-manifest", str(manifest)]) == 2
    captured = capsys.readouterr()
    assert "PII manifest 검증 실패" in captured.err
    assert "DOC_A" not in captured.out + captured.err


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": 2, "subjects": []},
        {"schema_version": 1, "subjects": []},
        {
            "schema_version": 1,
            "subjects": [{"name": "DOC_A", "input_civil": "2000-02-30 09:46"}],
        },
        {
            "schema_version": 1,
            "subjects": [
                {"name": "DOC_A", "input_civil": "2000-01-02 09:46", "extra": "x"}
            ],
        },
    ],
)
def test_pii_manifest_schema_is_strict(monkeypatch, tmp_path, payload):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(hsweep, "_is_ignored_local_manifest", lambda path: True)
    with pytest.raises(hsweep.PIIManifestError):
        hsweep.load_pii_manifest(str(manifest))


def test_live_main_masks_korean_birth_and_ampm_before_backend(
    monkeypatch, tmp_path, capsys
):
    manifest = _write_synthetic_manifest(tmp_path)
    monkeypatch.setattr(hsweep, "_is_ignored_local_manifest", lambda path: True)

    class FakePage:
        def get_text(self):
            return "DOC_A은 2000년 1월 2일 오전 9시 46분에 태어났습니다."

    class FakeDoc(list):
        def close(self):
            return None

    monkeypatch.setitem(
        sys.modules,
        "fitz",
        SimpleNamespace(open=lambda path: FakeDoc([FakePage()])),
    )
    backend = FakeBackend(reply="[]")
    monkeypatch.setattr(hsweep, "AnthropicSweepBackend", lambda: backend)
    monkeypatch.setattr(hsweep, "_write_report", lambda report, stamp: tmp_path / "report")
    monkeypatch.setenv("SAJUGEN_HARNESS_ALLOW_REGEN", "1")

    exit_code = hsweep.main(
        [
            "sweep",
            "--pdf",
            "synthetic.pdf",
            "--pii-manifest",
            str(manifest),
            "--approve",
            "--allow-llm",
        ]
    )
    assert exit_code == 0
    assert backend.calls
    for call in backend.calls:
        outbound = call["system"] + call["user"]
        assert "DOC_A" not in outbound
        assert "2000년 1월 2일" not in outbound
        assert "오전 9시 46분" not in outbound
    captured = capsys.readouterr()
    assert "DOC_A" not in captured.out + captured.err
    assert "2000-01-02" not in captured.out + captured.err


# ── 2) 비용 상한: pre-call fail-closed + 부분 리포트 ──
def test_cost_cap_halts_with_partial_report():
    # 첫 콜이 폭발적 토큰을 보고 → 다음 check_before 가 상한 초과로 중단.
    be = FakeBackend(reply="[]", in_tok=1, out_tok=10_000_000)
    pages = [hsweep.mask_for_api("안전한 본문", ["DOC_A"])]
    rep = hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=pages)
    assert rep["partial"] is True
    assert "partial_reason" in rep
    assert rep["cost_usd"] > 0  # 실사용 관측 기록
    assert len(be.calls) < len(hsweep.LENS_IDS), "상한 초과 후 남은 렌즈는 호출되지 않아야 한다"
    assert rep["candidates"] == 0
    assert rep["operator_review_complete"] is False
    assert rep["K"] is None and rep["Z_new_class"] is None


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
    rep = hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=["안전 텍스트"])
    assert rep.get("advisory") is True
    assert "gate_pass" not in rep and "clean" not in rep
    assert rep["partial"] is False
    assert rep["review_status"] == "pending"
    assert rep["operator_review_complete"] is False
    assert rep["operator_review_blocked_by_pipeline"] is False
    assert rep["K"] is None and rep["Z_new_class"] is None
    assert all(
        rep["stage_status"][f"lens:{lens_id}"]["status"] == "complete_empty"
        for lens_id in hsweep.LENS_IDS
    )
    reviewed = hsweep.apply_operator_review(
        rep,
        {
            "schema_version": 1,
            "review_status": "complete",
            "operator_review_completed_at": "2026-07-12T12:00:00+09:00",
            "operator_candidate_labels": [],
            "operator_discoveries": [],
        },
    )
    assert reviewed["operator_review_complete"] is True
    assert reviewed["K"] == 0 and reviewed["Z"] == 0


def test_malformed_lens_is_not_treated_as_valid_empty():
    rep = hsweep.sweep(
        "x.pdf",
        ["DOC_A"],
        backend=FakeBackend(reply="not-json"),
        masked_pages=["안전한 합성 본문"],
    )
    assert rep["candidates"] == 0
    assert rep["partial"] is True
    assert all(
        rep["stage_status"][f"lens:{lens_id}"]["status"] == "malformed_output"
        for lens_id in hsweep.LENS_IDS
    )
    assert "malformed_output:lens:" in rep["partial_reason"]
    assert rep["operator_review_complete"] is False
    assert rep["operator_review_blocked_by_pipeline"] is True
    assert rep["K"] is None and rep["Z_known_recurrence"] is None


def test_zero_candidates_with_incomplete_stage_cannot_confirm_operator_zero():
    clean = hsweep.sweep(
        "x.pdf",
        ["DOC_A"],
        backend=FakeBackend(reply="[]"),
        masked_pages=["안전한 합성 본문"],
    )
    incomplete = dict(clean)
    incomplete["partial"] = True
    incomplete["stage_status"] = {
        stage: dict(status) for stage, status in clean["stage_status"].items()
    }
    incomplete["stage_status"]["lens:narrator_tone"] = {
        "status": "incomplete",
        "items": 0,
    }
    reviewed = hsweep.apply_operator_review(
        incomplete,
        {
            "schema_version": 1,
            "review_status": "complete",
            "operator_review_completed_at": "2026-07-12T12:00:00+09:00",
            "operator_candidate_labels": [],
            "operator_discoveries": [],
        },
    )
    assert reviewed["candidates"] == 0
    assert reviewed["operator_review_complete"] is False
    assert reviewed["K"] is None
    assert reviewed["Z_new_class"] is None
    assert reviewed["Z_known_recurrence"] is None


@pytest.mark.parametrize(
    ("ranker_reply", "expected_status"),
    [("[]", "incomplete"), ("not-json", "malformed")],
)
def test_empty_and_malformed_ranker_are_distinct_and_both_observable(
    ranker_reply, expected_status
):
    finding = (
        '[{"page":1,"severity":"high","rule":"x","rationale":"합성 결함",'
        '"defect_class":"other","model_novelty_suggestion":"unknown"}]'
    )

    class RankerReplyBackend(PipelineBackend):
        def complete(self, *, model, system, user):
            if "비파괴 결함 후보 순위기" in system:
                self.calls.append({"model": model, "system": system, "user": user})
                return ranker_reply, 10, 2
            return super().complete(model=model, system=system, user=user)

    backend = RankerReplyBackend(finding)
    rep = hsweep.sweep(
        "x.pdf", ["DOC_A"], backend=backend, masked_pages=["안전한 합성 본문"]
    )
    assert rep["stage_status"]["ranker"]["status"] == expected_status
    assert rep["partial"] is True
    assert len([call for call in backend.calls if "opus" in call["model"]]) == 2


def test_findings_schema_has_no_freetext_customer_field():
    # 모델이 본문을 되뱉어도 파서가 스키마 밖 필드를 버린다(고객 본문 자유텍스트 유입 차단).
    malicious = (
        '[{"page":3,"severity":"high","rule":"x","rationale":"ok","verbatim":"DOC_A 원문"}]'
    )
    parsed = hsweep._parse_findings(malicious, "narrator_tone", ["DOC_A"])
    assert parsed and set(parsed[0].keys()) == {
        "lens",
        "page",
        "severity",
        "rule",
        "rationale",
        "defect_class",
        "model_novelty_suggestion",
    }
    assert "verbatim" not in parsed[0]
    assert "DOC_A" not in parsed[0]["rationale"]  # rationale free-text 스크럽


@pytest.mark.parametrize("page_json", ["0", "2", '"1"', "true"])
def test_lens_candidate_page_must_be_strict_int_inside_masked_page_range(page_json):
    finding = (
        f'[{{"page":{page_json},"severity":"high","rule":"x",'
        '"rationale":"합성 결함","defect_class":"other"}]'
    )
    backend = PipelineBackend(finding)
    report = hsweep.sweep(
        "x.pdf", ["DOC_A"], backend=backend, masked_pages=["한 페이지 합성 본문"]
    )
    assert report["candidates"] == 0
    assert report["partial"] is True
    assert report["judge_confirmed"] is None
    assert report["confirmed"] is None
    assert all(
        report["stage_status"][f"lens:{lens_id}"]["status"]
        == "invalid_page_evidence"
        for lens_id in hsweep.LENS_IDS
    )
    assert not any("opus" in call["model"] for call in backend.calls)


# ── 4) 모델 이질성: 렌즈 ≠ judge ──
def test_lens_and_judge_models_differ():
    assert cfg.llm_model("sweep_lens") != cfg.llm_model("sweep_judge")


def test_anthropic_backend_records_safe_lens_and_judge_usage_metadata(monkeypatch):
    class FakeMessages:
        def create(self, *, model, **kwargs):
            return SimpleNamespace(
                model=model,
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="[]")],
                usage=SimpleNamespace(input_tokens=11, output_tokens=3),
            )

    fake_client = SimpleNamespace(messages=FakeMessages())
    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=lambda **kwargs: fake_client),
    )
    llm_usage.reset()
    backend = hsweep.AnthropicSweepBackend()
    backend.complete_with_metadata(
        model=cfg.llm_model("sweep_lens"),
        system="safe",
        user="safe",
        role="sweep_lens",
        stage="lens:narrator_tone",
    )
    backend.complete_with_metadata(
        model=cfg.llm_model("sweep_judge"),
        system="safe",
        user="safe",
        role="sweep_judge",
        stage="judge:normal",
    )
    events = llm_usage.events_snapshot()
    assert [(event["role"], event["model"], event["section"]) for event in events] == [
        ("sweep_lens", cfg.llm_model("sweep_lens"), "sweep_narrator_tone"),
        ("sweep_judge", cfg.llm_model("sweep_judge"), "sweep_judge_normal"),
    ]
    llm_usage.reset()


def test_unsafe_usage_role_and_stage_cannot_emit_pii(monkeypatch):
    class FakeMessages:
        def create(self, *, model, **kwargs):
            return SimpleNamespace(
                model=model,
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="[]")],
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            )

    fake_client = SimpleNamespace(messages=FakeMessages())
    monkeypatch.setitem(
        sys.modules,
        "anthropic",
        SimpleNamespace(Anthropic=lambda **kwargs: fake_client),
    )
    llm_usage.reset()
    hsweep.AnthropicSweepBackend().complete_with_metadata(
        model=cfg.llm_model("sweep_lens"),
        system="safe",
        user="safe",
        role="sweep_lens/DOC_A",
        stage="lens:DOC_A",
    )
    event = llm_usage.events_snapshot()[0]
    assert event["role"] == "unspecified"
    assert event["section"] == "global"
    assert "DOC_A" not in (llm_usage.format_detail_line() or "")
    llm_usage.reset()

    guard = hsweep.CostGuard()
    hsweep._safe_call(
        FakeBackend(),
        role="sweep_lens",
        system="safe",
        user="safe",
        names=["DOC_A"],
        guard=guard,
        stage="lens:DOC_A",
    )
    assert guard.trace[0]["stage"] == "unknown"
    assert "DOC_A" not in json.dumps(guard.trace, ensure_ascii=False)


# ── 5) 렌즈 프롬프트 계약: 5파일 존재 + 인용 금지 + JSON 스키마 ──
def test_lens_prompts_exist_and_forbid_quoting():
    for lens_id in hsweep.LENS_IDS:
        p = hsweep._PROMPT_DIR / f"lens_{lens_id}.md"
        assert p.exists(), f"렌즈 프롬프트 없음: {lens_id}"
        body = p.read_text(encoding="utf-8")
        assert "인용하지 마라" in body, f"{lens_id}: verbatim 인용 금지 지시 필요"
        assert "JSON" in body and "rationale" in body, f"{lens_id}: 출력 스키마 명시 필요"

    narrator = (hsweep._PROMPT_DIR / "lens_narrator_tone.md").read_text(encoding="utf-8")
    direct = (hsweep._PROMPT_DIR / "lens_direct_answer.md").read_text(encoding="utf-8")
    assert "register" in narrator and "결과지" in narrator
    assert "외부 도메인 조언" in direct and "서류" in direct
    assert "model_novelty_suggestion" in narrator + direct
    assert "최종 신규/재발 판정은 운영자" in narrator + direct


# ── 파이프라인 전 단계가 FakeBackend 로 검증됨(happy path + judge 순서 스왑) ──
def test_full_pipeline_with_fake_backend():
    finding = (
        '[{"page":1,"severity":"high","rule":"document_self_reference","rationale":"메타 발화",'
        '"defect_class":"narrator_tone","model_novelty_suggestion":"known_class_recurrence"}]'
    )

    be = PipelineBackend(finding)
    rep = hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=["안전 본문"])
    assert rep["candidates"] >= 1
    assert rep["confirmed"] >= 1
    assert rep["schema_version"] == 2
    assert len(rep["raw_candidates"]) == len(rep["ranked_candidates"])
    assert len(rep["judge_results"]) == rep["candidates"]
    assert rep["operator_labels"] == []
    assert rep["stage_trace"]
    # 후보 수와 무관하게 전체 batch를 순서 스왑 2콜로 심사한다.
    judge_calls = [c for c in be.calls if "opus" in c["model"]]
    assert len(judge_calls) == 2


def test_ranker_rejection_never_deletes_raw_and_judge_still_sees_every_candidate():
    finding = (
        '[{"page":1,"severity":"high","rule":"client_register","rationale":"문서체",'
        '"defect_class":"client_register","model_novelty_suggestion":"known_class_recurrence"}]'
    )
    be = PipelineBackend(finding, disposition="unsupported", score=0.8)
    rep = hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=["유일한 페이지 근거"])

    assert rep["candidates"] == len(hsweep.LENS_IDS)
    assert rep["survivors"] == 0, "기존 M 의미는 ranker 생존 수로 유지한다"
    assert len(rep["raw_candidates"]) == rep["candidates"]
    assert len(rep["ranked_candidates"]) == rep["candidates"]
    assert all(c["ranker_disposition"] == "unsupported" for c in rep["ranked_candidates"])
    assert len(rep["judge_results"]) == rep["candidates"]
    assert rep["confirmed"] == rep["candidates"], "M=0이어도 Opus가 N 전체를 심사해야 한다"

    judge_calls = [call for call in be.calls if "opus" in call["model"]]
    assert len(judge_calls) == 2, "후보별 호출이 아니라 전체 batch 순서 스왑 2콜이어야 한다"
    expected_ids = {candidate["candidate_id"] for candidate in rep["ranked_candidates"]}
    for call in judge_calls:
        assert set(_payload_candidate_ids(call["user"])) == expected_ids


def test_ranker_and_judge_payload_group_duplicate_page_evidence_once_per_request():
    finding = (
        '[{"page":1,"severity":"medium","rule":"x","rationale":"합성 근거",'
        '"defect_class":"other","model_novelty_suggestion":"new_class"}]'
    )
    be = PipelineBackend(finding)
    rep = hsweep.sweep("x.pdf", ["DOC_A"], backend=be, masked_pages=["PAGE_EVIDENCE_SENTINEL"])
    assert rep["candidates"] == len(hsweep.LENS_IDS)

    downstream = [
        call
        for call in be.calls
        if "비파괴 결함 후보 순위기" in call["system"] or "opus" in call["model"]
    ]
    assert len(downstream) == 3  # ranker 1 + judge 2
    for call in downstream:
        payload = json.loads(call["user"])
        assert len(payload["page_groups"]) == 1
        assert call["user"].count("PAGE_EVIDENCE_SENTINEL") == 1
        assert len(payload["page_groups"][0]["candidates"]) == len(hsweep.LENS_IDS)


def test_judge_cap_returns_partial_without_dropping_candidates():
    finding = (
        '[{"page":1,"severity":"high","rule":"external_domain_advice","rationale":"합성 절차",'
        '"defect_class":"external_domain_advice","model_novelty_suggestion":"known_class_recurrence"}]'
    )

    class JudgeCapBackend(PipelineBackend):
        def complete(self, *, model, system, user):
            text, in_tok, out_tok = super().complete(model=model, system=system, user=user)
            if "비파괴 결함 후보 순위기" in system:
                return text, in_tok, 60_000  # $0.90 관측 후 judge pre-call에서 $1 cap 차단
            return text, 0, 0

    be = JudgeCapBackend(finding)
    rep = hsweep.sweep(
        "x.pdf",
        ["DOC_A"],
        backend=be,
        masked_pages=["안전한 합성 본문"],
        guard=hsweep.CostGuard(cap_usd=1.0),
    )

    assert rep["partial"] is True
    assert rep["candidates"] == len(rep["raw_candidates"]) == len(rep["ranked_candidates"])
    assert len(rep["judge_results"]) == rep["candidates"]
    assert all(result["status"] == "unscored" for result in rep["judge_results"])
    assert rep["stage_trace"][-1]["status"] == "cap_blocked"
    assert rep["stage_trace"][-1]["stage"] == "judge:normal"


def test_clean_and_defect_documents_take_opposite_fake_paths():
    clean_backend = PipelineBackend("[]")
    clean = hsweep.sweep(
        "clean.pdf", ["DOC_A"], backend=clean_backend, masked_pages=["평온한 합성 본문"]
    )
    assert clean["candidates"] == clean["confirmed"] == 0
    assert not any("opus" in call["model"] for call in clean_backend.calls)

    defect = (
        '[{"page":1,"severity":"high","rule":"client_register","rationale":"합성 결함",'
        '"defect_class":"client_register","model_novelty_suggestion":"known_class_recurrence"}]'
    )
    defect_backend = PipelineBackend(defect, score=0.9)
    defective = hsweep.sweep(
        "defect.pdf", ["DOC_A"], backend=defect_backend, masked_pages=["결함이 있는 합성 본문"]
    )
    assert defective["candidates"] > 0
    assert defective["confirmed"] == defective["candidates"]
    assert len([call for call in defect_backend.calls if "opus" in call["model"]]) == 2


def test_incomplete_judge_output_cannot_masquerade_as_complete_k_zero():
    finding = (
        '[{"page":1,"severity":"high","rule":"client_register","rationale":"합성 결함",'
        '"defect_class":"client_register","model_novelty_suggestion":"known_class_recurrence"}]'
    )

    class MissingJudgeBackend(PipelineBackend):
        def complete(self, *, model, system, user):
            if "opus" in model:
                self.calls.append({"model": model, "system": system, "user": user})
                return "[]", 10, 2
            return super().complete(model=model, system=system, user=user)

    rep = hsweep.sweep(
        "defect.pdf",
        ["DOC_A"],
        backend=MissingJudgeBackend(finding),
        masked_pages=["결함이 있는 합성 본문"],
    )
    assert rep["candidates"] > 0 and rep["confirmed"] is None
    assert rep["judge_confirmed_observed"] == 0
    assert rep["judge_complete"] is False
    assert rep["partial"] is True
    assert "incomplete_output:judge" in rep["partial_reason"]


def test_operator_k_and_z_are_separate_from_judge_and_require_complete_review():
    finding = (
        '[{"page":1,"severity":"high","rule":"client_register","rationale":"합성 결함",'
        '"defect_class":"client_register","model_novelty_suggestion":"new_class"}]'
    )
    report = hsweep.sweep(
        "x.pdf",
        ["DOC_A"],
        backend=PipelineBackend(finding, score=0.9),
        masked_pages=["안전한 합성 본문"],
    )
    assert report["judge_confirmed"] == report["confirmed"] == len(hsweep.LENS_IDS)
    assert report["operator_review_complete"] is False
    assert report["K"] is None and report["Z_new_class"] is None

    candidate_ids = [candidate["candidate_id"] for candidate in report["ranked_candidates"]]
    partial = hsweep.apply_operator_labels(
        report,
        [
            {
                "candidate_id": candidate_ids[0],
                "verdict": "confirmed",
                "defect_class": "client_register",
                "reviewed_at": "2026-07-12T12:00:00+09:00",
            }
        ],
    )
    assert partial["operator_confirmed"] == 1
    assert partial["K"] is None, "부분 검수의 누적 1건을 확정 K=1로 표시하면 안 된다"

    labels = []
    for index, candidate_id in enumerate(candidate_ids):
        if index == 0:
            verdict = "confirmed"
        elif index == 1:
            verdict = "confirmed"
        else:
            verdict = "rejected"
        labels.append(
            {
                "candidate_id": candidate_id,
                "verdict": verdict,
                "defect_class": "client_register",
                "reviewed_at": "2026-07-12T12:00:00+09:00",
            }
        )
    reviewed = hsweep.apply_operator_review(
        report,
        {
            "schema_version": 1,
            "review_status": "complete",
            "operator_review_completed_at": "2026-07-12T12:05:00+09:00",
            "operator_candidate_labels": labels,
            "operator_discoveries": [
                {
                    "discovery_id": "d0001",
                    "defect_class": "new_register_variant",
                    "novelty": "new_class",
                    "page": 1,
                    "reviewed_at": "2026-07-12T12:01:00+09:00",
                },
                {
                    "discovery_id": "d0002",
                    "defect_class": "client_register",
                    "novelty": "known_recurrence",
                    "reviewed_at": "2026-07-12T12:02:00+09:00",
                },
            ],
        },
    )
    assert reviewed["operator_review_complete"] is True
    assert reviewed["K"] == 2
    assert reviewed["Z"] == 2
    assert reviewed["Z_new_class"] == 1
    assert reviewed["Z_known_recurrence"] == 1
    assert reviewed["judge_confirmed"] == len(hsweep.LENS_IDS)
    assert all("class_novelty" not in candidate for candidate in reviewed["raw_candidates"])


def test_operator_label_contract_rejects_unknown_candidate_and_naive_timestamp():
    report = {
        "schema_version": 2,
        "ranked_candidates": [{"candidate_id": "c0001"}],
    }
    bad = {
        "candidate_id": "missing",
        "verdict": "confirmed",
        "defect_class": "client_register",
        "novelty": "new_class",
        "reviewed_at": "2026-07-12T12:00:00",
    }
    with pytest.raises(hsweep.OperatorLabelError):
        hsweep.apply_operator_labels(report, [bad])


def test_v1_report_migration_never_relabels_judge_confirmed_as_operator_k():
    v1 = {
        "pdf": "synthetic.pdf",
        "candidates": 3,
        "survivors": 2,
        "confirmed": 1,
        "findings": [{"rule": "legacy"}],
    }
    migrated = hsweep.migrate_v1_report(v1)
    assert migrated["schema_version"] == 2
    assert migrated["judge_confirmed"] == 1
    assert migrated["judge_findings"] == v1["findings"]
    assert migrated["K"] is None
    assert migrated["operator_confirmed"] is None
    assert migrated["migration"]["legacy_confirmed_semantics"] == "judge_confirmed"


def test_legacy_v2_labels_migrate_to_candidate_only_without_k_or_z():
    current = hsweep.sweep(
        "x.pdf",
        ["DOC_A"],
        backend=PipelineBackend(
            '[{"page":1,"severity":"high","rule":"x","rationale":"합성",'
            '"defect_class":"other"}]'
        ),
        masked_pages=["합성 본문"],
    )
    legacy = dict(current)
    for key in (
        "operator_candidate_labels",
        "operator_discoveries",
        "review_status",
        "operator_review_completed_at",
    ):
        legacy.pop(key, None)
    legacy["operator_labels"] = [
        {
            "candidate_id": legacy["ranked_candidates"][0]["candidate_id"],
            "verdict": "confirmed",
            "defect_class": "other",
            "novelty": "new_class",
            "reviewed_at": "2026-07-12T12:00:00+09:00",
        }
    ]
    legacy["K"] = 1
    legacy["Z_new_class"] = 1
    migrated = hsweep.migrate_v2_report(legacy)
    assert migrated["operator_candidate_labels"][0]["candidate_id"] == "c0001"
    assert "novelty" not in migrated["operator_candidate_labels"][0]
    assert migrated["review_status"] == "legacy_unverified"
    assert migrated["K"] is None and migrated["Z"] is None


def test_operator_discovery_contract_rejects_raw_text_and_invalid_page():
    report = hsweep.sweep(
        "x.pdf", ["DOC_A"], backend=FakeBackend("[]"), masked_pages=["합성 본문"]
    )
    report["verbatim_customer_text"] = "SENSITIVE_SENTINEL"
    report["stage_status"]["lens:narrator_tone"]["verbatim_customer_text"] = (
        "SENSITIVE_SENTINEL"
    )
    report["stage_trace"][0]["verbatim_customer_text"] = "SENSITIVE_SENTINEL"
    base = {
        "schema_version": 1,
        "review_status": "complete",
        "operator_review_completed_at": "2026-07-12T12:05:00+09:00",
        "operator_candidate_labels": [],
        "operator_discoveries": [],
    }
    missing_completion = dict(base)
    missing_completion.pop("operator_review_completed_at")
    with pytest.raises(hsweep.OperatorLabelError):
        hsweep.apply_operator_review(report, missing_completion)

    raw_text = dict(base)
    raw_text["operator_discoveries"] = [
        {
            "discovery_id": "d0001",
            "defect_class": "client_register",
            "novelty": "new_class",
            "page": 1,
            "reviewed_at": "2026-07-12T12:00:00+09:00",
            "verbatim": "고객 원문 금지",
        }
    ]
    with pytest.raises(hsweep.OperatorLabelError):
        hsweep.apply_operator_review(report, raw_text)

    invalid_page = dict(base)
    invalid_page["operator_discoveries"] = [
        {
            "discovery_id": "d0001",
            "defect_class": "client_register",
            "novelty": "new_class",
            "page": 2,
            "reviewed_at": "2026-07-12T12:00:00+09:00",
        }
    ]
    with pytest.raises(hsweep.OperatorLabelError):
        hsweep.apply_operator_review(report, invalid_page)


def test_review_subcommand_is_api_zero_and_writes_sanitized_merged_report(
    monkeypatch, tmp_path, capsys
):
    report = hsweep.sweep(
        "x.pdf", ["DOC_A"], backend=FakeBackend("[]"), masked_pages=["합성 본문"]
    )
    review = {
        "schema_version": 1,
        "review_status": "complete",
        "operator_review_completed_at": "2026-07-12T12:05:00+09:00",
        "operator_candidate_labels": [],
        "operator_discoveries": [
            {
                "discovery_id": "d0001",
                "defect_class": "client_register",
                "novelty": "new_class",
                "page": 1,
                "reviewed_at": "2026-07-12T12:00:00+09:00",
            }
        ],
    }
    report_path = tmp_path / "sweep.json"
    review_path = tmp_path / "operator-review.json"
    output_path = tmp_path / "merged.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(hsweep, "_is_ignored_local_manifest", lambda path: True)
    monkeypatch.setattr(hsweep, "_is_ignored_local_output", lambda path: True)
    monkeypatch.setattr(
        hsweep,
        "AnthropicSweepBackend",
        lambda: pytest.fail("review subcommand must not construct API backend"),
    )

    exit_code = hsweep.main(
        [
            "review",
            "--sweep-report",
            str(report_path),
            "--operator-review",
            str(review_path),
            "--out",
            str(output_path),
        ]
    )
    assert exit_code == 0
    merged = json.loads(output_path.read_text(encoding="utf-8"))
    merged_text = json.dumps(merged, ensure_ascii=False)
    assert "verbatim_customer_text" not in merged_text
    assert "SENSITIVE_SENTINEL" not in merged_text
    assert merged["K"] == 0
    assert merged["Z"] == 1 and merged["Z_new_class"] == 1
    assert merged["operator_discoveries"][0]["discovery_id"] == "d0001"
    captured = capsys.readouterr()
    assert captured.out.strip() == "review: merged"
    assert "d0001" not in captured.out + captured.err


def test_review_canonicalizer_drops_unknown_raw_ranked_and_judge_text_fields():
    finding = (
        '[{"page":1,"severity":"high","rule":"client_register","rationale":"합성 근거",'
        '"defect_class":"client_register"}]'
    )
    report = hsweep.sweep(
        "x.pdf",
        ["DOC_A"],
        backend=PipelineBackend(finding),
        masked_pages=["합성 본문"],
    )
    report["verbatim_customer_text"] = "SENSITIVE_SENTINEL"
    report["raw_candidates"][0]["verbatim_customer_text"] = "SENSITIVE_SENTINEL"
    report["ranked_candidates"][0]["verbatim_customer_text"] = "SENSITIVE_SENTINEL"
    report["judge_results"][0]["verbatim_customer_text"] = "SENSITIVE_SENTINEL"
    canonical = hsweep._canonical_sweep_report_for_review(report)
    dumped = json.dumps(canonical, ensure_ascii=False)
    assert "SENSITIVE_SENTINEL" not in dumped
    assert "verbatim_customer_text" not in dumped
    assert "rationale" not in canonical["raw_candidates"][0]
    assert set(canonical["judge_results"][0]) == {
        "candidate_id",
        "score",
        "status",
        "run_count",
        "reason_codes",
    }


def test_review_temp_must_be_ignored_before_any_write(monkeypatch, tmp_path):
    output = tmp_path / "merged.json"

    def only_output_is_ignored(path):
        return Path(path) == output

    monkeypatch.setattr(hsweep, "_is_ignored_local_output", only_output_is_ignored)
    with pytest.raises(hsweep.OperatorLabelError):
        hsweep._write_ignored_review(str(output), {"schema_version": 2})
    assert list(tmp_path.iterdir()) == []


def test_review_replace_failure_cleans_temp_and_preserves_only_output(monkeypatch, tmp_path):
    output = tmp_path / "merged.json"
    output.write_text("ORIGINAL", encoding="utf-8")
    monkeypatch.setattr(hsweep, "_is_ignored_local_output", lambda path: True)
    original_replace = Path.replace

    def fail_review_replace(path, target):
        if path.name.startswith(".hsweep-review-"):
            raise OSError("synthetic replace failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_review_replace)
    with pytest.raises(hsweep.OperatorLabelError):
        hsweep._write_ignored_review(str(output), {"schema_version": 2})
    assert output.read_text(encoding="utf-8") == "ORIGINAL"
    assert [path.name for path in tmp_path.iterdir()] == ["merged.json"]
