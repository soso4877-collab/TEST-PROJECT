# -*- coding: utf-8 -*-
"""LLM API 사용량 집계 단일 소스 — 비용 관측 (PII 0: 토큰 수·호출 수만).

배경(2026-07-05 백로그): llm_sections 의 카운터가 소비처 0(어디에도 출력 안 됨)이었고,
gunghap._compose / llm_polish / classify 는 카운터를 아예 거치지 않아 재생성 지출을
로컬 기록으로 확인할 수 없었다("배선됐지만 소비 안 되는 파라미터"의 사용량 판).
이 모듈이 카운터의 단일 소스이며, llm_sections 는 하위호환 위임만 남긴다.

출력 표면: 각 빌드 CLI(sajugen.cli / gunghap / integrated)가 종료 시 format_line() 을
stdout 으로 남기고, hrun._regen_pdf 가 그 줄을 파싱해 summary(regen_llm_usage)로 올린다.
줄 형식은 ASCII 키(cp949-safe): "LLM usage: calls=N input_tokens=I output_tokens=O".
"""

from __future__ import annotations

import logging
import re
import threading

_log = logging.getLogger(__name__)

_lock = threading.Lock()
_usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

# hrun 파싱과 CLI 출력이 공유하는 형식(변경 시 양쪽 테스트가 함께 깨지도록 단일 정의).
LINE_RX = re.compile(r"LLM usage: calls=(\d+) input_tokens=(\d+) output_tokens=(\d+)")


def add(input_tokens: int, output_tokens: int) -> None:
    with _lock:
        _usage["input_tokens"] += int(input_tokens)
        _usage["output_tokens"] += int(output_tokens)
        _usage["calls"] += 1


def add_response(resp) -> None:
    """anthropic Message 또는 instructor 반환 모델에서 usage 를 안전 추출해 누적.

    instructor 는 파싱된 pydantic 모델에 _raw_response 로 원 응답을 붙인다.
    사용량 관측 실패가 본 기능(compose/polish/classify)을 깨면 안 되므로 예외는
    삼키되, 조용한 no-op 금지 규율(B-6)에 따라 warning 을 남긴다.
    """
    try:
        u = getattr(resp, "usage", None)
        if u is None:
            raw = getattr(resp, "_raw_response", None)
            u = getattr(raw, "usage", None)
        if u is None:
            return  # 테스트 mock 등 usage 무첨부 응답 — 관측 대상 아님(정상 no-op)
        add(int(getattr(u, "input_tokens", 0) or 0), int(getattr(u, "output_tokens", 0) or 0))
    except Exception as e:
        _log.warning("LLM usage 추출 실패(관측만 누락, 본 기능 무영향): %s", type(e).__name__)


def snapshot() -> dict:
    with _lock:
        return dict(_usage)


def reset() -> None:
    with _lock:
        _usage.update(input_tokens=0, output_tokens=0, calls=0)


def format_line() -> str:
    s = snapshot()
    return (
        f"LLM usage: calls={s['calls']} "
        f"input_tokens={s['input_tokens']} output_tokens={s['output_tokens']}"
    )


def parse_line(text: str) -> dict | None:
    """텍스트(서브프로세스 stdout 등)에서 usage 줄을 찾아 dict 로. 없으면 None.

    여러 줄이면 마지막 줄 채택(빌드 최종 합계가 마지막에 출력됨)."""
    matches = LINE_RX.findall(text or "")
    if not matches:
        return None
    c, i, o = matches[-1]
    return {"calls": int(c), "input_tokens": int(i), "output_tokens": int(o)}
