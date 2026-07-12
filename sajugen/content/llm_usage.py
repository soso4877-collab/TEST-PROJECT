# -*- coding: utf-8 -*-
"""LLM API 사용량 집계 단일 소스 — 합계 하위호환 + PII-free 호출 이벤트.

기존 stdout 계약(``LLM usage: calls=N input_tokens=I output_tokens=O``)과
``snapshot/format_line/parse_line`` 반환형은 그대로 유지한다. 역할·모델·챕터·캐시 사용량은
별도 ``LLM usage detail:`` JSON 줄로 내보내 기존 소비자를 깨지 않고 hrun이 확장 관측한다.
이벤트에는 프롬프트·응답·고객 식별자를 넣지 않고 ASCII 식별자와 숫자만 허용한다.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from contextlib import contextmanager
from contextvars import ContextVar, copy_context
from functools import wraps
from typing import Callable, Iterator, TypeVar

from sajugen import config as cfg

_log = logging.getLogger(__name__)


class _UsageState:
    """한 PDF/명령 run의 합계와 이벤트를 함께 잠그는 내부 collector."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self.events: list[dict[str, object]] = []


_DEFAULT_STATE = _UsageState()
_CURRENT_STATE: ContextVar[_UsageState] = ContextVar(
    "sajugen_llm_usage_state", default=_DEFAULT_STATE
)
_F = TypeVar("_F", bound=Callable[..., object])


class UsageRun:
    """컨텍스트가 끝난 뒤에도 특정 run의 PII-free 계측을 읽는 핸들."""

    def __init__(self, state: _UsageState) -> None:
        self._state = state

    def snapshot(self) -> dict[str, int]:
        return _snapshot(self._state)

    def events_snapshot(self) -> list[dict[str, object]]:
        return _events_snapshot(self._state)


@contextmanager
def usage_run() -> Iterator[UsageRun]:
    """현재 실행만 쓰는 새 collector를 활성화해 다른 PDF/스레드 run과 격리한다."""

    state = _UsageState()
    token = _CURRENT_STATE.set(state)
    try:
        yield UsageRun(state)
    finally:
        _CURRENT_STATE.reset(token)


def isolated_run(func: _F) -> _F:
    """CLI 명령 전체를 새 usage run으로 감싸는 시그니처 보존 데코레이터."""

    @wraps(func)
    def wrapped(*args, **kwargs):
        with usage_run():
            return func(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def bind_current(func: Callable[..., object], /, *args, **kwargs) -> Callable[[], object]:
    """현재 usage run을 새 worker Context에 복사한 무인자 호출을 만든다.

    ``Context`` 하나는 동시에 두 스레드에 진입할 수 없으므로 worker 제출마다 이 함수를
    다시 호출해야 한다. 복사된 Context들은 같은 thread-safe collector 객체를 가리킨다.
    """

    context = copy_context()

    def bound():
        return context.run(func, *args, **kwargs)

    return bound

# hrun 파싱과 CLI 출력이 공유하는 기존 형식. 이 정규식과 format_line은 하위호환 고정이다.
LINE_RX = re.compile(r"LLM usage: calls=(\d+) input_tokens=(\d+) output_tokens=(\d+)")
DETAIL_PREFIX = "LLM usage detail: "
_SAFE_ROLES = frozenset(
    {
        "unspecified",
        "classify",
        "polish",
        "compose",
        "gunghap_compose",
        "relationship_compose",
        "sweep_lens",
        "sweep_judge",
    }
)
_SAFE_SECTIONS = frozenset(
    {
        "global",
        "question_category",
        "legacy_polish",
        "intro",
        "wonguk",
        "nature",
        "frame",
        "love",
        "work",
        "health",
        "flow",
        "ziwei",
        "together",
        "consult",
        "closing",
        "overview",
        "each",
        "pairs",
        "business",
        "timing",
        "intent",
        "conflict",
        "values",
        "ziwei_relation",
        "chemistry",
        "daily",
        "social",
        "pace",
        "risk",
        "stability",
        "action",
        "decision",
        "sweep_narrator_tone",
        "sweep_direct_answer",
        "sweep_raw_terms",
        "sweep_myeongni_ziwei",
        "sweep_immersion_repetition",
        "sweep_ranker",
        "sweep_judge_normal",
        "sweep_judge_reverse",
    }
)
_SAFE_STOP_REASONS = frozenset(
    {"unknown", "end_turn", "max_tokens", "stop_sequence", "tool_use", "pause_turn", "refusal"}
)
_DETAIL_TOTAL_KEYS = frozenset(
    {"cache_creation_input_tokens", "cache_read_input_tokens", "thinking_tokens", "events"}
)
_DETAIL_REQUIRED_KEYS = frozenset(
    {"cache_creation_input_tokens", "cache_read_input_tokens", "events"}
)
_EVENT_ID_KEYS = ("role", "model", "section", "stop_reason")
_EVENT_INT_KEYS = (
    "attempt",
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
    "thinking_tokens",
)
_EVENT_REQUIRED_KEYS = frozenset(
    {
        "role",
        "model",
        "section",
        "attempt",
        "input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "output_tokens",
        "stop_reason",
    }
)


def event_identifier_is_safe(kind: str, value: object) -> bool:
    """이벤트 ID가 정해진 역할/섹션/모델/종료 코드인지 검사한다."""
    text = str(value or "").strip()
    if kind == "role":
        return text in _SAFE_ROLES
    if kind == "section":
        return text in _SAFE_SECTIONS
    if kind == "model":
        # 임의 ``claude-*`` 문자열은 영문 이름·생일을 모델 ID처럼 숨길 수 있다. 현재
        # 실행 설정에 실제 등록된 모델 값과 unknown만 허용해 summary 표면을 exact allowlist로 둔다.
        try:
            configured_models = {str(model) for model in cfg.llm_models().values()}
        except Exception:
            configured_models = set()
        return text == "unknown" or text in configured_models
    if kind == "stop_reason":
        return text in _SAFE_STOP_REASONS
    return False


def _safe_identifier(kind: str, value: object, fallback: str) -> str:
    """허용 목록 밖 값 전체를 버린다. 부분 정제로 ASCII 이름을 살리지 않는다."""
    text = str(value or "").strip()
    return text if event_identifier_is_safe(kind, text) else fallback


def _nonnegative_int(value: object, default: int = 0) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return default


def _is_nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validated_detail_payload(payload: object) -> dict[str, object] | None:
    """detail JSON을 exact schema로 다시 검사해 합계 오염과 PII 필드 주입을 막는다."""

    if not isinstance(payload, dict):
        return None
    if not _DETAIL_REQUIRED_KEYS <= set(payload) <= _DETAIL_TOTAL_KEYS:
        return None
    if not _is_nonnegative_int(payload.get("cache_creation_input_tokens")):
        return None
    if not _is_nonnegative_int(payload.get("cache_read_input_tokens")):
        return None
    if "thinking_tokens" in payload and not _is_nonnegative_int(payload["thinking_tokens"]):
        return None
    raw_events = payload.get("events")
    if not isinstance(raw_events, list) or len(raw_events) > 100:
        return None
    events: list[dict[str, object]] = []
    allowed_event_keys = set(_EVENT_ID_KEYS) | set(_EVENT_INT_KEYS)
    for raw in raw_events:
        if not isinstance(raw, dict):
            return None
        if not _EVENT_REQUIRED_KEYS <= set(raw) <= allowed_event_keys:
            return None
        event: dict[str, object] = {}
        for key in _EVENT_ID_KEYS:
            value = raw.get(key)
            if not isinstance(value, str) or not event_identifier_is_safe(key, value):
                return None
            event[key] = value
        for key in _EVENT_INT_KEYS:
            if key not in raw:
                continue
            value = raw[key]
            if not _is_nonnegative_int(value):
                return None
            event[key] = value
        events.append(event)
    validated: dict[str, object] = {
        "cache_creation_input_tokens": payload["cache_creation_input_tokens"],
        "cache_read_input_tokens": payload["cache_read_input_tokens"],
        "events": events,
    }
    if "thinking_tokens" in payload:
        validated["thinking_tokens"] = payload["thinking_tokens"]
    return validated


def add(
    input_tokens: int,
    output_tokens: int,
    *,
    role: str = "unspecified",
    model: str = "unknown",
    section: str = "global",
    attempt: int = 1,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
    thinking_tokens: int | None = None,
    stop_reason: str | None = None,
) -> dict[str, object]:
    """합계와 PII-free 호출 이벤트를 원자적으로 누적하고 이벤트 사본을 반환한다."""
    event: dict[str, object] = {
        "role": _safe_identifier("role", role, "unspecified"),
        "model": _safe_identifier("model", model, "unknown"),
        "section": _safe_identifier("section", section, "global"),
        "attempt": max(1, _nonnegative_int(attempt, 1)),
        "input_tokens": _nonnegative_int(input_tokens),
        "cache_creation_input_tokens": _nonnegative_int(cache_creation_input_tokens),
        "cache_read_input_tokens": _nonnegative_int(cache_read_input_tokens),
        "output_tokens": _nonnegative_int(output_tokens),
        "stop_reason": _safe_identifier("stop_reason", stop_reason, "unknown"),
    }
    if thinking_tokens is not None:
        event["thinking_tokens"] = _nonnegative_int(thinking_tokens)
    state = _CURRENT_STATE.get()
    with state.lock:
        state.usage["input_tokens"] += int(event["input_tokens"])
        state.usage["output_tokens"] += int(event["output_tokens"])
        state.usage["calls"] += 1
        state.events.append(event)
    return dict(event)


def _raw_response(resp):
    """Instructor 모델과 Anthropic Message를 같은 관측 경로로 정규화한다."""
    raw = getattr(resp, "_raw_response", None)
    return raw if raw is not None else resp


def _thinking_tokens(usage) -> int | None:
    """SDK가 별도 thinking 토큰을 제공하는 버전에서만 값을 읽는다.

    Anthropic 0.102의 Usage는 별도 필드가 없고 output_tokens에 포함하므로 그때는 ``None``을
    유지한다. 존재하지 않는 값을 0으로 단언하지 않는다.
    """
    direct = getattr(usage, "thinking_tokens", None)
    if direct is not None:
        return _nonnegative_int(direct)
    details = getattr(usage, "output_tokens_details", None)
    nested = getattr(details, "thinking_tokens", None) if details is not None else None
    return _nonnegative_int(nested) if nested is not None else None


def add_response(
    resp,
    *,
    role: str = "unspecified",
    model: str | None = None,
    section: str | None = None,
    attempt: int = 1,
) -> dict[str, object] | None:
    """Anthropic/Instructor 응답에서 합계·캐시·종료 정보를 안전하게 추출한다.

    사용량 관측 실패가 compose/polish/classify를 깨면 안 되므로 예외는 흡수하되, 조용한
    실패를 피하려고 예외 타입만 warning으로 남긴다. 프롬프트나 응답 원문은 기록하지 않는다.
    """
    try:
        raw = _raw_response(resp)
        usage = getattr(raw, "usage", None)
        if usage is None:
            return None  # 테스트 mock 등 usage 무첨부 응답은 정상 비관측 경로다.
        return add(
            getattr(usage, "input_tokens", 0),
            getattr(usage, "output_tokens", 0),
            role=role,
            model=model or getattr(raw, "model", None) or "unknown",
            section=section or "global",
            attempt=attempt,
            cache_creation_input_tokens=getattr(usage, "cache_creation_input_tokens", 0),
            cache_read_input_tokens=getattr(usage, "cache_read_input_tokens", 0),
            thinking_tokens=_thinking_tokens(usage),
            stop_reason=getattr(raw, "stop_reason", None),
        )
    except Exception as exc:
        _log.warning("LLM usage 추출 실패(관측만 누락, 본 기능 무영향): %s", type(exc).__name__)
        return None


def _snapshot(state: _UsageState) -> dict[str, int]:
    with state.lock:
        return dict(state.usage)


def snapshot() -> dict:
    """기존 3개 합계만 반환한다. 새 필드 때문에 구 소비자가 깨지지 않게 고정한다."""
    return _snapshot(_CURRENT_STATE.get())


def _events_snapshot(state: _UsageState) -> list[dict[str, object]]:
    with state.lock:
        return [dict(event) for event in state.events]


def events_snapshot() -> list[dict[str, object]]:
    """호출별 PII-free 이벤트 사본을 반환한다."""
    return _events_snapshot(_CURRENT_STATE.get())


def detail_snapshot() -> dict[str, object]:
    """캐시/생각 토큰 합계와 호출 이벤트를 hrun 전달 형식으로 만든다."""
    events = events_snapshot()
    detail: dict[str, object] = {
        "cache_creation_input_tokens": sum(
            int(event.get("cache_creation_input_tokens", 0)) for event in events
        ),
        "cache_read_input_tokens": sum(
            int(event.get("cache_read_input_tokens", 0)) for event in events
        ),
        "events": events,
    }
    thinking = [int(event["thinking_tokens"]) for event in events if "thinking_tokens" in event]
    if thinking:
        detail["thinking_tokens"] = sum(thinking)
    return detail


def reset() -> None:
    state = _CURRENT_STATE.get()
    with state.lock:
        state.usage.update(input_tokens=0, output_tokens=0, calls=0)
        state.events.clear()


def format_line() -> str:
    """기존 합계 한 줄. 문자열 형식은 cp949-safe 하위호환 계약이다."""
    current = snapshot()
    return (
        f"LLM usage: calls={current['calls']} "
        f"input_tokens={current['input_tokens']} output_tokens={current['output_tokens']}"
    )


def format_detail_line() -> str | None:
    """호출이 있을 때만 ASCII-safe 확장 JSON 한 줄을 만든다."""
    if not events_snapshot():
        return None
    payload = json.dumps(detail_snapshot(), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return DETAIL_PREFIX + payload


def parse_line(text: str) -> dict | None:
    """stdout에서 기존 합계 줄을 찾아 구 반환형 그대로 돌려준다."""
    matches = LINE_RX.findall(text or "")
    if not matches:
        return None
    calls, input_tokens, output_tokens = matches[-1]
    return {
        "calls": int(calls),
        "input_tokens": int(input_tokens),
        "output_tokens": int(output_tokens),
    }


def parse_detail_line(text: str) -> dict[str, object] | None:
    """stdout의 마지막 확장 줄을 파싱한다. 손상·구 버전 출력은 ``None``이다."""
    lines = [line for line in (text or "").splitlines() if line.startswith(DETAIL_PREFIX)]
    if not lines:
        return None
    try:
        payload = json.loads(lines[-1][len(DETAIL_PREFIX) :])
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return _validated_detail_payload(payload)


def parse_output(text: str) -> dict[str, object] | None:
    """hrun용 확장 파서. 구 stdout이면 기존 3개 합계만 반환한다."""
    total = parse_line(text)
    detail = parse_detail_line(text)
    if total is None:
        return None
    if detail:
        total.update(detail)
    return total
