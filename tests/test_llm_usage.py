# -*- coding: utf-8 -*-
"""LLM 사용량 관측 배선(2026-07-05 백로그) — 카운터 단일 소스 + 응답 추출 + 줄 왕복.

배경: llm_sections 카운터가 소비처 0 이었고 gunghap._compose/llm_polish/classify 는
집계를 아예 거치지 않아, h153 재생성 지출을 로컬 기록으로 답할 수 없었다(QI-2026-07-05-01
세션 실측). 이 스위트는 (a) 카운터·추출 동작 (b) 소비처(경로 배선·출력·파싱)를 고정한다.
검증하지 않는 것: 실제 API 과금액(Console 전용) — 토큰·호출 수 집계까지만.
"""

import json
import sys
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import llm_sections, llm_usage  # noqa: E402


def test_add_snapshot_reset_roundtrip():
    llm_usage.reset()
    llm_usage.add(100, 20)
    llm_usage.add(50, 10)
    s = llm_usage.snapshot()
    assert s == {"input_tokens": 150, "output_tokens": 30, "calls": 2}
    llm_usage.reset()
    assert llm_usage.snapshot() == {"input_tokens": 0, "output_tokens": 0, "calls": 0}


def test_add_response_direct_usage_and_instructor_raw():
    llm_usage.reset()
    # anthropic Message 형(usage 직접 첨부)
    msg = types.SimpleNamespace(usage=types.SimpleNamespace(input_tokens=7, output_tokens=3))
    llm_usage.add_response(msg)
    # instructor 반환 모델 형(_raw_response 경유)
    model = types.SimpleNamespace(
        _raw_response=types.SimpleNamespace(
            usage=types.SimpleNamespace(input_tokens=5, output_tokens=2)
        )
    )
    llm_usage.add_response(model)
    s = llm_usage.snapshot()
    assert s == {"input_tokens": 12, "output_tokens": 5, "calls": 2}


def test_add_response_without_usage_is_noop():
    # 테스트 mock 등 usage 무첨부 응답 — 본 기능을 깨지 않는 무해 no-op(호출 수도 미증가)
    llm_usage.reset()
    llm_usage.add_response(types.SimpleNamespace())
    llm_usage.add_response(None)
    assert llm_usage.snapshot()["calls"] == 0


def test_format_and_parse_line_roundtrip():
    llm_usage.reset()
    llm_usage.add(1234, 567)
    line = llm_usage.format_line()
    assert line == "LLM usage: calls=1 input_tokens=1234 output_tokens=567"
    parsed = llm_usage.parse_line(f"PDF: x.pdf (2인)\n{line}\n")
    assert parsed == {"calls": 1, "input_tokens": 1234, "output_tokens": 567}
    # 여러 줄이면 마지막(최종 합계) 채택
    two = "LLM usage: calls=1 input_tokens=1 output_tokens=1\n" + line
    assert llm_usage.parse_line(two)["input_tokens"] == 1234
    # 줄 부재 = None(구 빌드/무LLM — 양방)
    assert llm_usage.parse_line("PDF: x.pdf") is None
    assert llm_usage.parse_line("") is None


def test_detail_event_extracts_cache_and_keeps_legacy_totals():
    llm_usage.reset()
    msg = types.SimpleNamespace(
        model="claude-sonnet-4-6",
        stop_reason="end_turn",
        usage=types.SimpleNamespace(
            input_tokens=120,
            output_tokens=30,
            cache_creation_input_tokens=80,
            cache_read_input_tokens=10,
            thinking_tokens=7,
        ),
    )
    event = llm_usage.add_response(
        msg,
        role="compose",
        model="claude-sonnet-4-6",
        section="consult",
        attempt=2,
    )
    assert llm_usage.snapshot() == {"input_tokens": 120, "output_tokens": 30, "calls": 1}
    assert event == {
        "role": "compose",
        "model": "claude-sonnet-4-6",
        "section": "consult",
        "attempt": 2,
        "input_tokens": 120,
        "cache_creation_input_tokens": 80,
        "cache_read_input_tokens": 10,
        "output_tokens": 30,
        "thinking_tokens": 7,
        "stop_reason": "end_turn",
    }
    detail_line = llm_usage.format_detail_line()
    assert detail_line and detail_line.startswith("LLM usage detail: ")
    combined = llm_usage.format_line() + "\n" + detail_line
    parsed = llm_usage.parse_output(combined)
    assert parsed["calls"] == 1
    assert parsed["cache_creation_input_tokens"] == 80
    assert parsed["cache_read_input_tokens"] == 10
    assert parsed["thinking_tokens"] == 7
    assert parsed["events"] == [event]


def test_event_identifiers_cannot_emit_customer_text():
    llm_usage.reset()
    event = llm_usage.add(
        1,
        2,
        role="compose CUSTOMER_1",
        model="claude-sonnet-4-6",
        section="consult/DOC_A",
        stop_reason="end turn CUSTOMER_1",
    )
    dumped = llm_usage.format_detail_line()
    assert dumped is not None
    assert "CUSTOMER_1" not in dumped and "DOC_A" not in dumped
    assert event["role"] == "unspecified"
    assert event["section"] == "global"
    assert not llm_usage.event_identifier_is_safe("model", "claude-john-doe-19900101")


def test_usage_runs_isolate_concurrent_pdfs_and_propagate_to_worker_threads():
    llm_usage.reset()

    def collect_run(call_count: int, tokens: int):
        with llm_usage.usage_run() as run:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(
                        llm_usage.bind_current(
                            llm_usage.add,
                            tokens,
                            1,
                            role="compose",
                            model="claude-sonnet-4-6",
                            section="intro",
                        )
                    )
                    for _ in range(call_count)
                ]
                for future in futures:
                    future.result()
        return run.snapshot(), run.events_snapshot()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_future = executor.submit(collect_run, 3, 10)
        second_future = executor.submit(collect_run, 5, 20)
        first = first_future.result()
        second = second_future.result()

    assert first[0] == {"input_tokens": 30, "output_tokens": 3, "calls": 3}
    assert second[0] == {"input_tokens": 100, "output_tokens": 5, "calls": 5}
    assert len(first[1]) == 3 and len(second[1]) == 5
    assert llm_usage.snapshot() == {"input_tokens": 0, "output_tokens": 0, "calls": 0}


def test_parse_output_rejects_detail_that_overwrites_totals_or_has_pii_fields():
    legacy = "LLM usage: calls=2 input_tokens=30 output_tokens=4\n"
    forged = {
        "calls": 999,
        "cache_creation_input_tokens": 1,
        "cache_read_input_tokens": 2,
        "events": [],
    }
    text = legacy + llm_usage.DETAIL_PREFIX + json.dumps(forged) + "\n"
    assert llm_usage.parse_output(text) == {
        "calls": 2,
        "input_tokens": 30,
        "output_tokens": 4,
    }

    pii_event = {
        "cache_creation_input_tokens": 1,
        "cache_read_input_tokens": 2,
        "events": [
            {
                "role": "compose",
                "model": "claude-sonnet-4-6",
                "section": "consult",
                "attempt": 1,
                "input_tokens": 3,
                "cache_creation_input_tokens": 1,
                "cache_read_input_tokens": 0,
                "output_tokens": 1,
                "stop_reason": "end_turn",
                "prompt": "customer text",
            }
        ],
    }
    text = legacy + llm_usage.DETAIL_PREFIX + json.dumps(pii_event) + "\n"
    assert llm_usage.parse_output(text) == {
        "calls": 2,
        "input_tokens": 30,
        "output_tokens": 4,
    }


def test_llm_sections_delegates_to_single_source():
    # 하위호환 위임 — 카운터 이중화(경로별 드리프트) 방지 앵커
    llm_usage.reset()
    llm_sections._usage_add(10, 5)
    assert llm_usage.snapshot() == {"input_tokens": 10, "output_tokens": 5, "calls": 1}
    assert llm_sections.usage_snapshot() == llm_usage.snapshot()
    llm_sections.usage_reset()
    assert llm_usage.snapshot()["calls"] == 0


def test_gunghap_compose_records_usage(monkeypatch):
    # 배선 회귀: 궁합 compose 가 집계를 거친다(그동안 미경유 — 재생성 지출 관측 불가의 원인).
    import sys as _sys

    from sajugen import gunghap as g

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *a, **k):
            return types.SimpleNamespace(
                content=[
                    types.SimpleNamespace(text="흐름이 이어지도록 확인의 속도를 맞추면 좋아요.")
                ],
                usage=types.SimpleNamespace(input_tokens=111, output_tokens=22),
            )

    class _Anthropic:
        def __init__(self, *a, **k):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setitem(_sys.modules, "anthropic", fake)

    llm_usage.reset()
    g._compose(
        "each", "근거 슬롯", {"ganzhi": [], "ganzhi_ko": []}, "", ["김민준"], 2026, use_llm=True
    )
    s = llm_usage.snapshot()
    assert s == {"input_tokens": 111, "output_tokens": 22, "calls": 1}


def test_gunghap_cli_prints_usage_line(monkeypatch):
    # 출력 표면 배선: CLI 종료 시 usage 줄이 stdout 에 남는다(hrun 파싱 대상).
    from typer.testing import CliRunner

    from sajugen import gunghap as g

    monkeypatch.setattr(
        g, "build_gunghap", lambda *a, **k: {"pdf_path": "fake.pdf", "people": [{}, {}]}
    )
    llm_usage.reset()
    r = CliRunner().invoke(
        g.app,
        ["--person", "합성갑,1990-01-01,10:00,남", "--person", "합성을,1991-02-02,11:00,여"],
    )
    assert r.exit_code == 0, r.output
    assert "LLM usage: calls=0 input_tokens=0 output_tokens=0" in r.output
