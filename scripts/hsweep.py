# -*- coding: utf-8 -*-
"""발송 전 이질 렌즈 스윕 (Phase 4, L2 advisory).

육안급 결함을 발송 전에 선제 적발하는 후보 발굴기. 연구 근거(설계): 동종 debate 는
다수결을 못 넘음(2311.17371) → 렌즈/모델 이질성 + generator-critic 분리. LLM judge
자기선호 편향(2404.13076) → 렌즈≠judge 모델 + 순서 스왑. 코드리뷰 오탐 15-30%
(2407.00215) → advisory 전용, 사람 최종.

파이프라인: (a) 이질 렌즈 5종 후보 발굴(Sonnet, 렌즈별 신선 컨텍스트) → (b) 근거 페이지를
함께 보는 비파괴 ranker 1콜 → (c) 원시 후보 전부를 묶어 보는 루브릭 judge(Opus, 순서 스왑
2콜 평균) → (d) schema v2 sweep.json/md. ranker가 낮게 평가한 후보도 삭제하지 않는다.

불변(구조적):
- **advisory**: 이 모듈은 verify/order_flow/게이트 상태머신을 import 하지 않는다(코드로 보장).
  gate_pass·발송 판정에 일절 접촉 없음. 산출은 정보 전용(exit code 포함).
- **PII 0(fail-closed)**: live CLI는 원시 PII 인자를 받지 않고 Git-ignored 로컬 manifest만
  읽는다. API 전송 전 이름·생년월일·시각을 마스킹하고 전송 직전 잔존을 재검증한다.
- **비용 상한(pre-call, 보수적)**: 매 호출 전 상한 초과 여부를 과대추정으로 점검, 초과 시
  중단하고 부분 리포트. 실사용 토큰은 관측 기록.
- **인용 금지**: 렌즈 프롬프트는 본문 verbatim 인용을 금지하고, 리포트 스키마에 고객 본문
  자유텍스트 필드가 없다(rule/page/severity/비-PII 근거만).

실제 스윕 실행(API 과금)은 운영자 명시 승인 + 3중 잠금(--approve --allow-llm + env) 후에만.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import secrets
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# advisory: 게이트/주문 모듈 비import — masking(PII)·config(모델)·llm_usage(관측)만.
from sajugen.content import llm_usage, masking  # noqa: E402
from sajugen import config as cfg  # noqa: E402

_PROMPT_DIR = ROOT / "harness" / "prompts" / "sweep"
LENS_IDS = (
    "narrator_tone",  # 내레이터 말투(문서가 스스로를 지칭·작업 예고)
    "direct_answer",  # 직답 만족도(신청 질문에 정면으로 답하는가)
    "raw_terms",  # 날것 용어(대운수·오행국 등 미순화 계산어)
    "myeongni_ziwei",  # 명리-자미 통합감(사일로·역할분담 정형)
    "immersion_repetition",  # 몰입·반복감(같은 문형·기호 난발)
)
_USAGE_SECTION_BY_STAGE = {
    **{f"lens:{lens_id}": f"sweep_{lens_id}" for lens_id in LENS_IDS},
    "ranker": "sweep_ranker",
    "judge:normal": "sweep_judge_normal",
    "judge:reverse": "sweep_judge_reverse",
}
COST_CAP_USD = 3.0
MAX_REPORT_FINDINGS = 10
# 보수적 과대추정 단가(USD/1M tok, opus 기준으로 일괄 상향 — 캡은 안전 백스톱이라 고평가가 옳다).
_EST_IN_PER_MTOK = 15.0
_EST_OUT_PER_MTOK = 75.0
# 실측 단가(관측 기록용, 모델별). 캡 점검엔 위 과대추정을 쓴다.
_PRICE = {
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
    "haiku": (0.8, 4.0),
}

# 날짜/시각/8자리 생일형(이름은 masking + supplied names 로 별도 처리 — regex 는 한글 이름 미포착).
_DATE_RX = re.compile(
    r"\d{4}[-./]\d{2}[-./]\d{2}|(?<!\d)\d{2}:\d{2}(?!\d)|(?<![\d\-])(?:19|20)\d{6}(?![\d\-])"
)
_INPUT_CIVIL_RX = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
_MAX_PII_MANIFEST_BYTES = 64 * 1024


class CostCapExceeded(Exception):
    """상한 초과 — 중단하고 부분 리포트."""


class PIILeakBlocked(Exception):
    """마스킹 후에도 PII 잔존 — 전송 차단(fail-closed)."""


class PIIManifestError(Exception):
    """로컬 PII manifest 계약 위반. 값과 경로는 오류 메시지에 포함하지 않는다."""


class OperatorLabelError(Exception):
    """운영자 판정 라벨 계약 위반."""


class CostGuard:
    """pre-call 상한 점검 + 실사용 관측. 캡은 보수적 과대추정으로 fail-closed."""

    def __init__(self, cap_usd: float = COST_CAP_USD):
        self.cap = cap_usd
        self.spent_usd = 0.0
        self.calls = 0
        self.trace: list[dict] = []
        self.partial_reason: str | None = None
        self.partial_reasons: list[str] = []
        self.cap_blocked = False

    def mark_partial(self, reason_code: str) -> None:
        """고객/모델 원문 없이 일반화된 실패 코드만 누적한다."""
        if reason_code not in self.partial_reasons:
            self.partial_reasons.append(reason_code)
        self.partial_reason = "; ".join(self.partial_reasons)

    def check_before(self, est_in: int, est_out: int) -> None:
        projected = self.spent_usd + self._est(est_in, est_out)
        if projected > self.cap:
            raise CostCapExceeded(
                f"예상 지출 ${projected:.2f} > 상한 ${self.cap:.2f} (누적 ${self.spent_usd:.2f})"
            )

    def record(
        self,
        in_tok: int,
        out_tok: int,
        price_key: str = "sonnet",
        *,
        stage: str = "unknown",
        role: str = "unknown",
        model: str = "unknown",
    ) -> None:
        pin, pout = _PRICE.get(price_key, _PRICE["opus"])
        call_cost = in_tok / 1e6 * pin + out_tok / 1e6 * pout
        self.spent_usd += call_cost
        self.calls += 1
        self.trace.append(
            {
                "stage": stage,
                "role": role,
                "model": model,
                "input_tokens": int(in_tok),
                "output_tokens": int(out_tok),
                "cost_usd": round(call_cost, 6),
                "status": "completed",
            }
        )

    def mark_cap(
        self,
        _exc: CostCapExceeded,
        *,
        stage: str,
        role: str,
        model: str,
        est_in: int,
        est_out: int,
    ) -> None:
        """호출하지 못한 단계도 흔적을 남기되 후보나 본문은 기록하지 않는다."""
        self.cap_blocked = True
        self.mark_partial(f"cost_cap:{stage}")
        self.trace.append(
            {
                "stage": stage,
                "role": role,
                "model": model,
                "estimated_input_tokens": int(est_in),
                "estimated_output_tokens": int(est_out),
                "cost_usd": 0.0,
                "status": "cap_blocked",
            }
        )

    @staticmethod
    def _est(in_tok: int, out_tok: int) -> float:
        return in_tok / 1e6 * _EST_IN_PER_MTOK + out_tok / 1e6 * _EST_OUT_PER_MTOK


def _scrub(text: str, names: list[str]) -> str:
    """이름 + 날짜/시각/8자리 리댁션(rationale 등 모델 출력 정화 — 리포트·다운스트림 방어)."""
    out = text or ""
    for nm in names or []:
        nm = (nm or "").strip()
        if nm:
            out = out.replace(nm, "[이름 비공개]")
    return _DATE_RX.sub("[비공개]", out)


def _is_ignored_local_manifest(path: Path) -> bool:
    """repo 내부이며 Git이 실제로 ignore하는 일반 파일만 허용한다."""
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(ROOT.resolve())
    except (FileNotFoundError, OSError, ValueError):
        return False
    if path.is_symlink() or not resolved.is_file():
        return False
    checked = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(relative)],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return checked.returncode == 0


def load_pii_manifest(path_text: str | None) -> tuple[list[str], list[str]]:
    """ignored 로컬 manifest를 엄격 검증하고 이름·입력 시민시각을 메모리로만 반환한다."""
    if not isinstance(path_text, str) or not path_text.strip():
        raise PIIManifestError("PII_MANIFEST_REQUIRED")
    path = Path(path_text)
    try:
        if path.is_symlink():
            raise PIIManifestError("PII_MANIFEST_NOT_IGNORED_LOCAL")
        path = path.resolve(strict=True)
    except PIIManifestError:
        raise
    except (FileNotFoundError, OSError) as exc:
        raise PIIManifestError("PII_MANIFEST_NOT_IGNORED_LOCAL") from exc
    if not _is_ignored_local_manifest(path):
        raise PIIManifestError("PII_MANIFEST_NOT_IGNORED_LOCAL")
    try:
        if path.stat().st_size > _MAX_PII_MANIFEST_BYTES:
            raise PIIManifestError("PII_MANIFEST_TOO_LARGE")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except PIIManifestError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PIIManifestError("PII_MANIFEST_INVALID_JSON") from exc

    if not isinstance(payload, dict) or set(payload) != {"schema_version", "subjects"}:
        raise PIIManifestError("PII_MANIFEST_INVALID_SCHEMA")
    if payload["schema_version"] != 1:
        raise PIIManifestError("PII_MANIFEST_INVALID_SCHEMA")
    subjects = payload["subjects"]
    if not isinstance(subjects, list) or not 1 <= len(subjects) <= 2:
        raise PIIManifestError("PII_MANIFEST_INVALID_SCHEMA")

    names: list[str] = []
    self_civils: list[str] = []
    for subject in subjects:
        if not isinstance(subject, dict) or set(subject) != {"name", "input_civil"}:
            raise PIIManifestError("PII_MANIFEST_INVALID_SCHEMA")
        name = subject["name"]
        civil = subject["input_civil"]
        if (
            not isinstance(name, str)
            or name != name.strip()
            or not 1 <= len(name) <= 80
            or any(ord(char) < 32 for char in name)
        ):
            raise PIIManifestError("PII_MANIFEST_INVALID_SUBJECT")
        if not isinstance(civil, str) or not _INPUT_CIVIL_RX.fullmatch(civil):
            raise PIIManifestError("PII_MANIFEST_INVALID_SUBJECT")
        try:
            datetime.strptime(civil, "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise PIIManifestError("PII_MANIFEST_INVALID_SUBJECT") from exc
        if name in names:
            raise PIIManifestError("PII_MANIFEST_DUPLICATE_SUBJECT")
        names.append(name)
        self_civils.append(civil)
    return names, self_civils


def mask_for_api(text: str, names: list[str], self_civils: list[str] | None = None) -> str:
    """API 전송용 마스킹: 생년월일시 + 공급된 이름 치환. names 필수(빈 값 fail-closed).

    self_civils(각 인물 "YYYY-MM-DD HH:MM")를 주면 masking.mask_birth_in_text 가 그 생일의
    표기 변형 전부(한글 'YYYY년 M월 D일'·'오전 H시 M분' 포함)를 정밀 마스킹한다 — 이게 있어야
    한글 형식 생년월일이 막힌다(_DATE_RX 는 dashed/HH:MM/8자리만 커버). self_civils 없이 bare
    'N월 D일'을 통째 마스킹하지는 않는다(사주 시기 참조를 오마스킹하면 스윕 입력이 망가짐 —
    정밀 마스킹은 특정 인물 생일만). 벨트(assert_pii_free)는 dashed/이름 backstop 으로 유지."""
    if not names:
        raise PIILeakBlocked("names 인자는 필수·비어있으면 안 됨(마스킹 없이 전송 금지)")
    out = text or ""
    for civ in self_civils or [None]:
        out = masking.mask_birth_in_text(out, civ)
    for nm in names:
        nm = (nm or "").strip()
        if nm:
            out = out.replace(nm, "[이름 비공개]")
    out = _DATE_RX.sub("[비공개]", out)
    return out


def assert_pii_free(text: str, names: list[str]) -> None:
    """전송 직전 벨트(fail-closed): 이름/날짜 잔존 시 예외 — 전송하지 않는다."""
    for nm in names or []:
        nm = (nm or "").strip()
        if nm and nm in text:
            raise PIILeakBlocked("이름 잔존 — 전송 차단")
    if _DATE_RX.search(text):
        raise PIILeakBlocked("날짜/시각 잔존 — 전송 차단")


def _safe_call(
    backend,
    *,
    role: str,
    system: str,
    user: str,
    names: list[str],
    guard: CostGuard,
    stage: str | None = None,
):
    """모든 API 경유는 이 함수만 통과 — 마스킹 벨트 + pre-call 캡을 강제한다."""
    assert_pii_free(system, names)
    assert_pii_free(user, names)
    est_in = (len(system) + len(user)) // 3  # 보수적 토큰 추정(문자/3)
    model = cfg.llm_model(role)
    safe_role = role if role in {"sweep_lens", "sweep_judge"} else "unspecified"
    requested_stage = stage or role
    stage = requested_stage if requested_stage in _USAGE_SECTION_BY_STAGE else "unknown"
    try:
        guard.check_before(est_in, 1500)
    except CostCapExceeded as exc:
        guard.mark_cap(
            exc,
            stage=stage,
            role=safe_role,
            model=model,
            est_in=est_in,
            est_out=1500,
        )
        raise
    if hasattr(backend, "complete_with_metadata"):
        text, in_tok, out_tok = backend.complete_with_metadata(
            model=model,
            system=system,
            user=user,
            role=safe_role,
            stage=stage,
        )
    else:
        text, in_tok, out_tok = backend.complete(model=model, system=system, user=user)
    price_key = "opus" if "opus" in model else ("haiku" if "haiku" in model else "sonnet")
    guard.record(
        in_tok,
        out_tok,
        price_key,
        stage=stage,
        role=safe_role,
        model=model,
    )
    return text


def _load_lens_prompt(lens_id: str) -> str:
    p = _PROMPT_DIR / f"lens_{lens_id}.md"
    return p.read_text(encoding="utf-8")


def _decode_json_array(text: str) -> tuple[list, bool]:
    """유효한 빈 배열과 JSON 파싱 실패를 구분한다."""
    try:
        match = re.search(r"\[.*\]", text or "", re.S)
        if not match:
            return [], False
        value = json.loads(match.group(0))
    except (AttributeError, json.JSONDecodeError):
        return [], False
    return (value, True) if isinstance(value, list) else ([], False)


def _parse_findings_result(
    text: str,
    lens_id: str,
    names: list[str],
    page_count: int | None = None,
) -> tuple[list[dict], str]:
    """모델 출력에서 JSON findings 파싱 — 스키마 밖 필드 폐기(고객 본문 자유텍스트 유입 차단).
    rationale 는 모델 free-text 라 parse 시점에 name/date 스크럽(리포트·refute/judge 다운스트림
    양쪽 정화 — 이름/날짜 외 PII 잔여는 벨트+프롬프트로 축소, docs 에 residual 명시)."""
    raw, valid_json = _decode_json_array(text)
    if not valid_json:
        return [], "malformed"
    out = []
    malformed_item = False
    invalid_page = False
    for f in raw:
        if isinstance(f, dict) and "page" in f:
            page = f.get("page")
            if (
                not isinstance(page, int)
                or isinstance(page, bool)
                or page < 1
                or (page_count is not None and page > page_count)
            ):
                invalid_page = True
                continue
        if (
            not isinstance(f, dict)
            or not {"page", "severity", "rule", "rationale"}.issubset(f)
            or f.get("severity") not in {"low", "medium", "high"}
            or not isinstance(f.get("rule"), str)
            or not isinstance(f.get("rationale"), str)
        ):
            malformed_item = True
            continue
        suggestion = f.get("model_novelty_suggestion", f.get("class_novelty", "unknown"))
        out.append(
            {
                "lens": lens_id,
                "page": f.get("page"),
                "severity": str(f.get("severity", "unknown"))[:12],
                "rule": _scrub(str(f.get("rule", "")), names)[:60],
                "rationale": _scrub(str(f.get("rationale", "")), names)[:400],
                "defect_class": _scrub(
                    str(f.get("defect_class", f.get("rule", lens_id))), names
                )[:60],
                "model_novelty_suggestion": {
                    "known_class": "known_class_recurrence",
                    "known_class_recurrence": "known_class_recurrence",
                    "new_class": "new_class",
                    "unknown": "unknown",
                }.get(str(suggestion), "unknown"),
            }
        )
    if invalid_page:
        return out, "invalid_page_evidence"
    return out, ("malformed" if malformed_item else "valid")


def _parse_findings(text: str, lens_id: str, names: list[str]) -> list[dict]:
    """기존 호출자 호환: 상태가 필요 없는 곳에는 파싱 결과 목록만 반환한다."""
    return _parse_findings_result(text, lens_id, names)[0]


def run_lenses(
    masked_pages: list[str],
    backend,
    guard: CostGuard,
    names: list[str],
    stage_status: dict[str, dict] | None = None,
) -> list[dict]:
    body = "\n\n".join(f"[p{i + 1}]\n{t}" for i, t in enumerate(masked_pages))
    findings: list[dict] = []
    stage_status = stage_status if stage_status is not None else {}
    for lens_id in LENS_IDS:
        stage = f"lens:{lens_id}"
        system = _load_lens_prompt(lens_id)
        try:
            out = _safe_call(
                backend,
                role="sweep_lens",
                system=system,
                user=body,
                names=names,
                guard=guard,
                stage=stage,
            )
        except CostCapExceeded:
            stage_status[stage] = {"status": "cap_blocked", "items": 0}
            break
        parsed, parse_status = _parse_findings_result(
            out, lens_id, names, page_count=len(masked_pages)
        )
        stage_status[stage] = {
            "status": (
                parse_status
                if parse_status == "invalid_page_evidence"
                else (
                    "malformed_output"
                    if parse_status == "malformed"
                    else ("complete_empty" if not parsed else "complete")
                )
            ),
            "items": len(parsed),
        }
        if parse_status in {"malformed", "invalid_page_evidence"}:
            reason = (
                "malformed_output"
                if parse_status == "malformed"
                else "invalid_page_evidence"
            )
            guard.mark_partial(f"{reason}:{stage}")
        findings.extend(parsed)
    return findings


def _candidate_records(findings: list[dict]) -> list[dict]:
    """원시 후보를 건드리지 않고 안정적인 ID와 ranker 기본 상태를 붙인다."""
    return [
        {
            "candidate_id": f"c{index:04d}",
            **dict(finding),
            "ranker_disposition": "unranked",
            "ranker_confidence": None,
            "ranker_reason_code": "not_returned",
        }
        for index, finding in enumerate(findings, start=1)
    ]


def _page_number(value, page_count: int) -> int | None:
    try:
        page = int(value)
    except (TypeError, ValueError):
        return None
    return page if 1 <= page <= page_count else None


def _grouped_candidate_payload(
    candidates: list[dict], masked_pages: list[str], *, reverse: bool = False
) -> dict:
    """후보를 페이지별로 묶고 각 페이지 본문을 요청당 정확히 한 번만 싣는다."""
    grouped: dict[int | None, list[dict]] = {}
    for candidate in candidates:
        page = _page_number(candidate.get("page"), len(masked_pages))
        record = {
            "candidate_id": candidate["candidate_id"],
            "lens": candidate.get("lens"),
            "page": candidate.get("page"),
            "severity": candidate.get("severity"),
            "rule": candidate.get("rule"),
            "rationale": candidate.get("rationale"),
            "defect_class": candidate.get("defect_class"),
            "model_novelty_suggestion": candidate.get(
                "model_novelty_suggestion", "unknown"
            ),
        }
        if "ranker_disposition" in candidate:
            record["ranker_disposition"] = candidate.get("ranker_disposition")
            record["ranker_confidence"] = candidate.get("ranker_confidence")
            record["ranker_reason_code"] = candidate.get("ranker_reason_code")
        grouped.setdefault(page, []).append(record)

    page_keys = sorted(grouped, key=lambda page: (page is None, page or 0))
    if reverse:
        page_keys.reverse()
    groups = []
    for page in page_keys:
        records = list(grouped[page])
        if reverse:
            records.reverse()
        groups.append(
            {
                "page": page,
                "page_evidence": masked_pages[page - 1] if page is not None else None,
                "candidates": records,
            }
        )
    return {"candidate_count": len(candidates), "page_groups": groups}


def _json_array(text: str) -> list:
    """기존 호출자 호환 wrapper. 파싱 상태는 _decode_json_array를 사용한다."""
    return _decode_json_array(text)[0]


def _parse_rankings_result(
    text: str, candidate_ids: set[str]
) -> tuple[dict[str, dict], str]:
    items, valid_json = _decode_json_array(text)
    if not valid_json:
        return {}, "malformed"
    parsed: dict[str, dict] = {}
    invalid_item = False
    for item in items:
        if not isinstance(item, dict):
            invalid_item = True
            continue
        candidate_id = str(item.get("candidate_id", ""))
        disposition = str(item.get("disposition", ""))
        if candidate_id not in candidate_ids or disposition not in {
            "supported",
            "uncertain",
            "unsupported",
        } or candidate_id in parsed:
            invalid_item = True
            continue
        try:
            confidence = min(1.0, max(0.0, float(item.get("confidence", 0.0))))
        except (TypeError, ValueError):
            invalid_item = True
            continue
        reason_code = re.sub(r"[^a-z0-9_\-]", "_", str(item.get("reason_code", "")))[:60]
        parsed[candidate_id] = {
            "ranker_disposition": disposition,
            "ranker_confidence": round(confidence, 3),
            "ranker_reason_code": reason_code or "unspecified",
        }
    status = "complete" if not invalid_item and set(parsed) == candidate_ids else "incomplete"
    return parsed, status


def _parse_rankings(text: str, candidate_ids: set[str]) -> dict[str, dict]:
    return _parse_rankings_result(text, candidate_ids)[0]


def rank_candidates(
    findings: list[dict],
    masked_pages: list[str],
    backend,
    guard: CostGuard,
    names: list[str],
    stage_status: dict[str, dict] | None = None,
) -> list[dict]:
    """후보를 삭제하지 않는 근거 기반 ranker. 출력 길이는 언제나 입력 길이와 같다."""
    ranked = _candidate_records(findings)
    stage_status = stage_status if stage_status is not None else {}
    if not ranked:
        stage_status["ranker"] = {"status": "not_run", "items": 0, "reason": "no_candidates"}
        return []
    system = (
        "너는 비파괴 결함 후보 순위기다. 페이지 근거와 후보를 대조하되 어떤 후보도 삭제하거나 "
        "생략하지 마라. 각 candidate_id마다 supported|uncertain|unsupported 중 하나와 0~1 "
        "confidence, 짧은 영문 reason_code만 JSON 배열로 반환하라. 고객 본문을 인용하지 마라. "
        "문서체·AI식 register와 시험 일정·점수·자격·서류 절차 같은 외부 도메인 조언도 "
        "독립 결함으로 판정한다."
    )
    user = json.dumps(
        _grouped_candidate_payload(ranked, masked_pages),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    try:
        out = _safe_call(
            backend,
            role="sweep_lens",
            system=system,
            user=user,
            names=names,
            guard=guard,
            stage="ranker",
        )
    except CostCapExceeded:
        stage_status["ranker"] = {"status": "cap_blocked", "items": 0}
        return ranked
    candidate_ids = {candidate["candidate_id"] for candidate in ranked}
    updates, parse_status = _parse_rankings_result(out, candidate_ids)
    stage_status["ranker"] = {"status": parse_status, "items": len(updates)}
    if parse_status != "complete":
        guard.mark_partial(f"{parse_status}_output:ranker")
    return [{**candidate, **updates.get(candidate["candidate_id"], {})} for candidate in ranked]


def refute(
    findings: list[dict],
    backend,
    guard: CostGuard,
    names: list[str],
    masked_pages: list[str] | None = None,
) -> list[dict]:
    """v1 함수명 호환 wrapper. 이제 필터가 아니라 모든 후보를 보존하는 ranker다."""
    return rank_candidates(findings, masked_pages or [], backend, guard, names)


def _parse_judge_scores_result(
    text: str, candidate_ids: set[str]
) -> tuple[dict[str, dict], str]:
    items, valid_json = _decode_json_array(text)
    parsed: dict[str, dict] = {}
    if not valid_json:
        # 과거 단일 후보 scalar 형식만 읽기 호환한다.
        if len(candidate_ids) == 1:
            match = re.fullmatch(r"\s*([01](?:\.\d+)?)\s*", text or "")
            if match:
                candidate_id = next(iter(candidate_ids))
                return (
                    {
                        candidate_id: {
                            "score": min(1.0, float(match.group(1))),
                            "reason_code": "legacy_scalar",
                        }
                    },
                    "legacy_complete",
                )
        return {}, "malformed"
    invalid_item = False
    for item in items:
        if not isinstance(item, dict):
            invalid_item = True
            continue
        candidate_id = str(item.get("candidate_id", ""))
        if candidate_id not in candidate_ids or candidate_id in parsed:
            invalid_item = True
            continue
        try:
            score = min(1.0, max(0.0, float(item.get("score"))))
        except (TypeError, ValueError):
            invalid_item = True
            continue
        reason_code = re.sub(r"[^a-z0-9_\-]", "_", str(item.get("reason_code", "")))[:60]
        parsed[candidate_id] = {
            "score": round(score, 3),
            "reason_code": reason_code or "unspecified",
        }
    status = "complete" if not invalid_item and set(parsed) == candidate_ids else "incomplete"
    return parsed, status


def _parse_judge_scores(text: str, candidate_ids: set[str]) -> dict[str, dict]:
    return _parse_judge_scores_result(text, candidate_ids)[0]


def judge_candidates(
    ranked: list[dict],
    masked_pages: list[str],
    backend,
    guard: CostGuard,
    names: list[str],
    stage_status: dict[str, dict] | None = None,
) -> list[dict]:
    """원시 후보 전부를 후보별 호출 없이 두 개의 결정론적 batch로 심사한다."""
    if not ranked:
        return []
    stage_status = stage_status if stage_status is not None else {}
    rubric = (
        "페이지 근거를 직접 확인해 모든 candidate_id를 0.0~1.0으로 채점하라. ranker의 "
        "unsupported 판정도 독립적으로 다시 심사하며 후보를 생략하지 마라. 0=오탐/무의미, "
        "0.5=경미, 1=발송 전 반드시 수정이다. 문서체·AI식 register와 외부 시험 일정·점수·"
        "자격·서류·행정 절차 조언은 결함 층으로 포함하되, 사주 근거의 시기·완급·방향·관계 "
        "조율은 허용한다. 본문 인용 없이 candidate_id, score, 영문 reason_code만 JSON 배열로 "
        "반환하라."
    )
    candidate_ids = {candidate["candidate_id"] for candidate in ranked}
    runs: dict[str, list[dict]] = {candidate_id: [] for candidate_id in candidate_ids}
    for order, reverse in (("normal", False), ("reverse", True)):
        user = json.dumps(
            _grouped_candidate_payload(ranked, masked_pages, reverse=reverse),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        try:
            out = _safe_call(
                backend,
                role="sweep_judge",
                system=rubric,
                user=user,
                names=names,
                guard=guard,
                stage=f"judge:{order}",
            )
        except CostCapExceeded:
            stage_status[f"judge:{order}"] = {"status": "cap_blocked", "items": 0}
            break
        parsed, parse_status = _parse_judge_scores_result(out, candidate_ids)
        stage_status[f"judge:{order}"] = {"status": parse_status, "items": len(parsed)}
        if parse_status not in {"complete", "legacy_complete"}:
            guard.mark_partial(f"{parse_status}_output:judge:{order}")
        for candidate_id, result in parsed.items():
            runs[candidate_id].append({"order": order, **result})

    results = []
    for candidate in ranked:
        candidate_id = candidate["candidate_id"]
        candidate_runs = runs[candidate_id]
        score = (
            round(sum(run["score"] for run in candidate_runs) / len(candidate_runs), 3)
            if candidate_runs
            else None
        )
        results.append(
            {
                "candidate_id": candidate_id,
                "score": score,
                "status": (
                    "scored"
                    if len(candidate_runs) == 2
                    else ("partial_scored" if candidate_runs else "unscored")
                ),
                "run_count": len(candidate_runs),
                "reason_codes": [run["reason_code"] for run in candidate_runs],
            }
        )
    return results


def judge(finding: dict, backend, guard: CostGuard, names: list[str]) -> float:
    """과거 단일 후보 호출자를 위한 호환 wrapper."""
    ranked = _candidate_records([finding])
    results = judge_candidates(ranked, [], backend, guard, names)
    return float(results[0]["score"] or 0.0) if results else 0.0


_OPERATOR_ID_RX = re.compile(r"[a-z][a-z0-9_\-]{0,59}")
_DISCOVERY_ID_RX = re.compile(r"d\d{4,8}")


def _reviewed_at(value: object) -> datetime:
    if not isinstance(value, str):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    try:
        reviewed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID") from exc
    if reviewed.tzinfo is None:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    return reviewed


def _normalize_operator_candidate_labels(report: dict, labels: object) -> list[dict]:
    if not isinstance(labels, list):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    candidate_ids = {
        str(candidate.get("candidate_id"))
        for candidate in report.get("ranked_candidates", [])
        if candidate.get("candidate_id")
    }
    normalized = []
    seen: set[str] = set()
    for label in labels:
        if not isinstance(label, dict):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        keys = set(label)
        canonical_keys = {"candidate_id", "verdict", "defect_class", "reviewed_at"}
        legacy_keys = canonical_keys | {"novelty"}
        if keys != canonical_keys and keys != legacy_keys:
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        candidate_id = label["candidate_id"]
        verdict = label["verdict"]
        defect_class = label["defect_class"]
        if (
            not isinstance(candidate_id, str)
            or candidate_id not in candidate_ids
            or candidate_id in seen
            or verdict not in {"confirmed", "rejected"}
            or not isinstance(defect_class, str)
            or not _OPERATOR_ID_RX.fullmatch(defect_class)
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        if "novelty" in label and label["novelty"] not in {
            "new_class",
            "known_recurrence",
            "not_applicable",
        }:
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        _reviewed_at(label["reviewed_at"])
        seen.add(candidate_id)
        normalized.append(
            {
                "candidate_id": candidate_id,
                "verdict": verdict,
                "defect_class": defect_class,
                "reviewed_at": label["reviewed_at"],
            }
        )
    return sorted(normalized, key=lambda label: label["candidate_id"])


def _normalize_operator_discoveries(report: dict, discoveries: object) -> list[dict]:
    if not isinstance(discoveries, list):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    page_count = report.get("page_count")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 0:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    normalized = []
    seen: set[str] = set()
    required = {"discovery_id", "defect_class", "novelty", "reviewed_at"}
    for discovery in discoveries:
        if not isinstance(discovery, dict) or not required <= set(discovery) <= required | {"page"}:
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        discovery_id = discovery["discovery_id"]
        defect_class = discovery["defect_class"]
        novelty = discovery["novelty"]
        page = discovery.get("page")
        if (
            not isinstance(discovery_id, str)
            or not _DISCOVERY_ID_RX.fullmatch(discovery_id)
            or discovery_id in seen
            or not isinstance(defect_class, str)
            or not _OPERATOR_ID_RX.fullmatch(defect_class)
            or novelty not in {"new_class", "known_recurrence"}
            or (
                page is not None
                and (
                    not isinstance(page, int)
                    or isinstance(page, bool)
                    or not 1 <= page <= page_count
                )
            )
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        _reviewed_at(discovery["reviewed_at"])
        seen.add(discovery_id)
        item = {
            "discovery_id": discovery_id,
            "defect_class": defect_class,
            "novelty": novelty,
            "reviewed_at": discovery["reviewed_at"],
        }
        if page is not None:
            item["page"] = page
        normalized.append(item)
    return sorted(normalized, key=lambda item: item["discovery_id"])


def _pipeline_complete_for_operator_review(report: dict) -> bool:
    candidate_count = len(report.get("ranked_candidates", []))
    stage_status = report.get("stage_status", {})
    lens_complete = all(
        stage_status.get(f"lens:{lens_id}", {}).get("status")
        in {"complete", "complete_empty"}
        for lens_id in LENS_IDS
    )
    if candidate_count:
        downstream_complete = (
            stage_status.get("ranker", {}).get("status") == "complete"
            and stage_status.get("judge:normal", {}).get("status")
            in {"complete", "legacy_complete"}
            and stage_status.get("judge:reverse", {}).get("status")
            in {"complete", "legacy_complete"}
        )
    else:
        downstream_complete = all(
            stage_status.get(stage, {}).get("status") == "not_run"
            and stage_status.get(stage, {}).get("reason") == "no_candidates"
            for stage in ("ranker", "judge:normal", "judge:reverse")
        )
    return (
        report.get("partial") is False
        and report.get("ranker_complete") is True
        and report.get("judge_complete") is True
        and lens_complete
        and downstream_complete
    )


def apply_operator_review(report: dict, review: dict | None) -> dict:
    """명시적으로 완료된 사람 검수에서만 후보 K와 후보 밖 발견 Z를 확정한다."""
    result = dict(report)
    candidate_count = len(result.get("ranked_candidates", []))
    if review is None:
        candidate_labels: list[dict] = []
        discoveries: list[dict] = []
        review_status = "pending"
        completed_at = None
        explicit_complete = False
    else:
        required = {
            "schema_version",
            "review_status",
            "operator_review_completed_at",
            "operator_candidate_labels",
            "operator_discoveries",
        }
        if not isinstance(review, dict) or set(review) != required:
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        if review["schema_version"] != 1 or review["review_status"] != "complete":
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        completed_at = review["operator_review_completed_at"]
        _reviewed_at(completed_at)
        candidate_labels = _normalize_operator_candidate_labels(
            result, review["operator_candidate_labels"]
        )
        discoveries = _normalize_operator_discoveries(
            result, review["operator_discoveries"]
        )
        review_status = "complete"
        explicit_complete = True

    pipeline_complete = _pipeline_complete_for_operator_review(result)
    coverage_complete = len(candidate_labels) == candidate_count
    review_complete = explicit_complete and pipeline_complete and coverage_complete
    confirmed_labels = [
        label for label in candidate_labels if label["verdict"] == "confirmed"
    ]
    result["review_status"] = review_status
    result["operator_review_completed_at"] = completed_at
    result["operator_candidate_labels"] = candidate_labels
    result["operator_discoveries"] = discoveries
    result["operator_labels"] = list(candidate_labels)  # v2 구 소비자용 alias
    result["operator_review_complete"] = review_complete
    result["operator_review_blocked_by_pipeline"] = not pipeline_complete
    result["operator_pending"] = candidate_count - len(candidate_labels)
    result["operator_confirmed"] = len(confirmed_labels)
    result["operator_rejected"] = sum(
        label["verdict"] == "rejected" for label in candidate_labels
    )
    result["K"] = len(confirmed_labels) if review_complete else None
    result["Z"] = len(discoveries) if review_complete else None
    result["Z_new_class"] = (
        sum(discovery["novelty"] == "new_class" for discovery in discoveries)
        if review_complete
        else None
    )
    result["Z_known_recurrence"] = (
        sum(discovery["novelty"] == "known_recurrence" for discovery in discoveries)
        if review_complete
        else None
    )
    return result


def apply_operator_labels(report: dict, labels: list[dict] | None) -> dict:
    """v2 호환 wrapper. 완료 시각·discovery가 없으므로 K/Z를 확정하지 않는다."""
    result = apply_operator_review(report, None)
    normalized = _normalize_operator_candidate_labels(result, labels or [])
    result["operator_candidate_labels"] = normalized
    result["operator_labels"] = list(normalized)
    result["operator_pending"] = len(result.get("ranked_candidates", [])) - len(normalized)
    result["operator_confirmed"] = sum(
        label["verdict"] == "confirmed" for label in normalized
    )
    result["operator_rejected"] = sum(
        label["verdict"] == "rejected" for label in normalized
    )
    return result


def migrate_v1_report(report: dict) -> dict:
    """역사적 v1 confirmed를 운영자 K로 오인하지 않도록 명시적으로 v2 읽기 변환한다."""
    if int(report.get("schema_version", 1)) >= 2:
        return dict(report)
    migrated = dict(report)
    migrated["schema_version"] = 2
    migrated["judge_confirmed"] = int(report.get("confirmed", 0) or 0)
    migrated["judge_findings"] = list(report.get("findings", []))
    migrated["operator_labels"] = []
    migrated["operator_candidate_labels"] = []
    migrated["operator_discoveries"] = []
    migrated["review_status"] = "legacy_unverified"
    migrated["operator_review_completed_at"] = None
    migrated["operator_review_complete"] = False
    migrated["operator_review_blocked_by_pipeline"] = True
    migrated["operator_pending"] = None
    migrated["operator_confirmed"] = None
    migrated["operator_rejected"] = None
    migrated["K"] = None
    migrated["Z"] = None
    migrated["Z_new_class"] = None
    migrated["Z_known_recurrence"] = None
    migrated["migration"] = {
        "source_schema_version": 1,
        "legacy_confirmed_semantics": "judge_confirmed",
        "operator_metrics_available": False,
    }
    return migrated


def migrate_v2_report(report: dict) -> dict:
    """초기 v2 operator_labels를 후보 라벨로만 보존하고 K/Z 확정값은 폐기한다."""
    if int(report.get("schema_version", 0)) != 2:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    if {
        "operator_candidate_labels",
        "operator_discoveries",
        "review_status",
        "operator_review_completed_at",
    } <= set(report):
        return dict(report)
    migrated = dict(report)
    legacy_labels = report.get("operator_labels", [])
    migrated["operator_candidate_labels"] = _normalize_operator_candidate_labels(
        migrated, legacy_labels
    )
    migrated["operator_labels"] = list(migrated["operator_candidate_labels"])
    migrated["operator_discoveries"] = []
    migrated["review_status"] = "legacy_unverified"
    migrated["operator_review_completed_at"] = None
    migrated["operator_review_complete"] = False
    migrated["operator_review_blocked_by_pipeline"] = not _pipeline_complete_for_operator_review(
        migrated
    )
    migrated["K"] = None
    migrated["Z"] = None
    migrated["Z_new_class"] = None
    migrated["Z_known_recurrence"] = None
    migrated["migration"] = {
        "source_schema_version": 2,
        "legacy_operator_labels_semantics": "candidate_labels_only",
        "operator_discoveries_available": False,
    }
    return migrated


def migrate_report(report: dict) -> dict:
    """review subcommand가 과거 sweep.json을 안전한 현재 v2 표면으로 읽는 단일 진입점."""
    try:
        version = int(report.get("schema_version", 1))
    except (AttributeError, TypeError, ValueError) as exc:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID") from exc
    if version == 1:
        return migrate_v1_report(report)
    if version == 2:
        return migrate_v2_report(report)
    raise OperatorLabelError("OPERATOR_REVIEW_INVALID")


def _canonical_sweep_report_for_review(report: dict) -> dict:
    """입력 dict를 재사용하지 않고 PII-free 고정 필드만 새 review 표면으로 복사한다."""
    if (
        report.get("schema_version") != 2
        or not isinstance(report.get("partial"), bool)
        or not isinstance(report.get("ranker_complete"), bool)
        or not isinstance(report.get("judge_complete"), bool)
        or not isinstance(report.get("stage_status"), dict)
        or report.get("advisory") is not True
    ):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    page_count = report.get("page_count")
    raw_candidates = report.get("raw_candidates")
    ranked_candidates = report.get("ranked_candidates")
    judge_results = report.get("judge_results")
    if (
        not isinstance(page_count, int)
        or isinstance(page_count, bool)
        or page_count < 0
        or not isinstance(raw_candidates, list)
        or not isinstance(ranked_candidates, list)
        or not isinstance(judge_results, list)
        or len(raw_candidates) != len(ranked_candidates)
        or len(judge_results) != len(ranked_candidates)
    ):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")

    def candidate_surface(candidate: object) -> dict:
        if not isinstance(candidate, dict):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        lens = candidate.get("lens")
        page = candidate.get("page")
        severity = candidate.get("severity")
        rule = candidate.get("rule")
        defect_class = candidate.get("defect_class")
        suggestion = candidate.get("model_novelty_suggestion", "unknown")
        if (
            lens not in LENS_IDS
            or not isinstance(page, int)
            or isinstance(page, bool)
            or not 1 <= page <= page_count
            or severity not in {"low", "medium", "high"}
            or not isinstance(rule, str)
            or not _OPERATOR_ID_RX.fullmatch(rule)
            or not isinstance(defect_class, str)
            or not _OPERATOR_ID_RX.fullmatch(defect_class)
            or suggestion not in {"new_class", "known_class_recurrence", "unknown"}
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        return {
            "lens": lens,
            "page": page,
            "severity": severity,
            "rule": rule,
            "defect_class": defect_class,
            "model_novelty_suggestion": suggestion,
        }

    canonical_raw = [candidate_surface(candidate) for candidate in raw_candidates]
    canonical_ranked = []
    seen_ids: set[str] = set()
    for index, candidate in enumerate(ranked_candidates, start=1):
        surface = candidate_surface(candidate)
        candidate_id = candidate.get("candidate_id")
        disposition = candidate.get("ranker_disposition")
        confidence = candidate.get("ranker_confidence")
        reason_code = candidate.get("ranker_reason_code")
        if (
            candidate_id != f"c{index:04d}"
            or candidate_id in seen_ids
            or surface != canonical_raw[index - 1]
            or disposition not in {"unranked", "supported", "uncertain", "unsupported"}
            or (
                confidence is not None
                and (
                    isinstance(confidence, bool)
                    or not isinstance(confidence, (int, float))
                    or not math.isfinite(float(confidence))
                    or not 0 <= float(confidence) <= 1
                )
            )
            or not isinstance(reason_code, str)
            or not _OPERATOR_ID_RX.fullmatch(reason_code)
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        seen_ids.add(candidate_id)
        canonical_ranked.append(
            {
                "candidate_id": candidate_id,
                **surface,
                "ranker_disposition": disposition,
                "ranker_confidence": (
                    round(float(confidence), 3) if confidence is not None else None
                ),
                "ranker_reason_code": reason_code,
            }
        )

    canonical_judge = []
    seen_judge: set[str] = set()
    for result in judge_results:
        if not isinstance(result, dict):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        candidate_id = result.get("candidate_id")
        score = result.get("score")
        status = result.get("status")
        run_count = result.get("run_count")
        reason_codes = result.get("reason_codes")
        if (
            candidate_id not in seen_ids
            or candidate_id in seen_judge
            or (
                score is not None
                and (
                    isinstance(score, bool)
                    or not isinstance(score, (int, float))
                    or not math.isfinite(float(score))
                    or not 0 <= float(score) <= 1
                )
            )
            or status not in {"scored", "partial_scored", "unscored"}
            or not isinstance(run_count, int)
            or isinstance(run_count, bool)
            or not 0 <= run_count <= 2
            or not isinstance(reason_codes, list)
            or len(reason_codes) > 2
            or any(
                not isinstance(reason, str) or not _OPERATOR_ID_RX.fullmatch(reason)
                for reason in reason_codes
            )
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        seen_judge.add(candidate_id)
        canonical_judge.append(
            {
                "candidate_id": candidate_id,
                "score": round(float(score), 3) if score is not None else None,
                "status": status,
                "run_count": run_count,
                "reason_codes": list(reason_codes),
            }
        )
    if seen_judge != seen_ids:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")

    expected_stages = {
        *(f"lens:{lens_id}" for lens_id in LENS_IDS),
        "ranker",
        "judge:normal",
        "judge:reverse",
    }
    raw_stage_status = report["stage_status"]
    if set(raw_stage_status) != expected_stages:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    allowed_status = {
        "not_run",
        "complete",
        "complete_empty",
        "malformed_output",
        "invalid_page_evidence",
        "incomplete",
        "malformed",
        "legacy_complete",
        "cap_blocked",
    }
    canonical_stage_status = {}
    for stage in sorted(expected_stages):
        item = raw_stage_status[stage]
        if not isinstance(item, dict) or not {"status", "items"} <= set(item):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        status = item["status"]
        items = item["items"]
        reason = item.get("reason")
        if (
            status not in allowed_status
            or not isinstance(items, int)
            or isinstance(items, bool)
            or items < 0
            or reason not in {None, "no_candidates", "cost_cap_upstream"}
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        canonical_stage_status[stage] = {"status": status, "items": items}
        if reason is not None:
            canonical_stage_status[stage]["reason"] = reason

    canonical_trace = []
    for item in report.get("stage_trace", []):
        if not isinstance(item, dict):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        stage = item.get("stage")
        role = item.get("role")
        model = item.get("model")
        status = item.get("status")
        cost = item.get("cost_usd")
        if (
            stage not in expected_stages | {"unknown"}
            or role not in {"sweep_lens", "sweep_judge", "unspecified"}
            or not llm_usage.event_identifier_is_safe("model", model)
            or status not in {"completed", "cap_blocked"}
            or isinstance(cost, bool)
            or not isinstance(cost, (int, float))
            or not math.isfinite(float(cost))
            or float(cost) < 0
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        token_keys = (
            ("input_tokens", "output_tokens")
            if status == "completed"
            else ("estimated_input_tokens", "estimated_output_tokens")
        )
        if any(
            not isinstance(item.get(key), int)
            or isinstance(item.get(key), bool)
            or item[key] < 0
            for key in token_keys
        ):
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        canonical_trace.append(
            {
                "stage": stage,
                "role": role,
                "model": model,
                token_keys[0]: item[token_keys[0]],
                token_keys[1]: item[token_keys[1]],
                "cost_usd": round(float(cost), 6),
                "status": status,
            }
        )

    ranker_complete = all(
        candidate["ranker_disposition"] != "unranked" for candidate in canonical_ranked
    )
    judge_complete = all(result["run_count"] == 2 for result in canonical_judge)
    if (
        report["ranker_complete"] is not ranker_complete
        or report["judge_complete"] is not judge_complete
    ):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    threshold = report.get("judge_threshold", 0.5)
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(float(threshold))
        or not 0 <= float(threshold) <= 1
    ):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    judge_by_id = {result["candidate_id"]: result for result in canonical_judge}
    observed = []
    for candidate in canonical_ranked:
        result = judge_by_id[candidate["candidate_id"]]
        if result["score"] is not None and result["score"] >= float(threshold):
            observed.append({**candidate, "judge_score": result["score"]})
    observed.sort(key=lambda item: (-item["judge_score"], item["candidate_id"]))
    cost = report.get("cost_usd")
    calls = report.get("calls")
    if (
        isinstance(cost, bool)
        or not isinstance(cost, (int, float))
        or not math.isfinite(float(cost))
        or float(cost) < 0
        or not isinstance(calls, int)
        or isinstance(calls, bool)
        or calls < 0
    ):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    partial = report["partial"]
    return {
        "schema_version": 2,
        "pdf": "LOCAL_PDF",
        "page_count": page_count,
        "lenses": list(LENS_IDS),
        "partial": partial,
        **({"partial_reason": "PIPELINE_PARTIAL"} if partial else {}),
        "candidates": len(canonical_raw),
        "survivors": sum(
            candidate["ranker_disposition"] in {"supported", "uncertain"}
            for candidate in canonical_ranked
        ),
        "raw_candidates": canonical_raw,
        "ranked_candidates": canonical_ranked,
        "judge_results": canonical_judge,
        "judge_confirmed_observed": len(observed),
        "judge_confirmed": None if partial else len(observed),
        "judge_findings": observed[:MAX_REPORT_FINDINGS],
        "confirmed": None if partial else len(observed),
        "findings": observed[:MAX_REPORT_FINDINGS],
        "truncated": max(0, len(observed) - MAX_REPORT_FINDINGS),
        "stage_status": canonical_stage_status,
        "stage_trace": canonical_trace,
        "ranker_complete": ranker_complete,
        "judge_complete": judge_complete,
        "judge_threshold": float(threshold),
        "cost_usd": round(float(cost), 4),
        "calls": calls,
        "advisory": True,
    }


def sweep(
    pdf_path: str,
    names: list[str],
    *,
    backend,
    guard: CostGuard | None = None,
    masked_pages: list[str] | None = None,
    self_civils: list[str] | None = None,
    operator_labels: list[dict] | None = None,
    operator_review: dict | None = None,
    judge_threshold: float = 0.5,
) -> dict:
    """전 파이프라인. masked_pages 를 주면 PDF 추출을 건너뛴다(테스트/재사용).
    실 PDF 경로는 manifest에서 온 self_civils가 필수이며, 합성 masked_pages 주입만 예외다."""
    if not names:
        raise PIILeakBlocked("names 필수·비어있으면 안 됨 — 마스킹 없이 스윕 불가(fail-closed)")
    guard = guard or CostGuard()
    if masked_pages is None:
        if not self_civils or len(self_civils) != len(names):
            raise PIILeakBlocked("실 PDF 스윕은 검증된 input_civil 목록 필수")
        masked_pages = extract_masked_pages(pdf_path, names, self_civils)
    stage_status = {
        **{
            f"lens:{lens_id}": {"status": "not_run", "items": 0}
            for lens_id in LENS_IDS
        },
        "ranker": {"status": "not_run", "items": 0},
        "judge:normal": {"status": "not_run", "items": 0},
        "judge:reverse": {"status": "not_run", "items": 0},
    }
    report = {
        "schema_version": 2,
        # 로컬 파일명에도 이름이 섞일 수 있어 리포트에는 원본 basename을 남기지 않는다.
        "pdf": "LOCAL_PDF",
        "page_count": len(masked_pages),
        "lenses": list(LENS_IDS),
        "partial": False,
        "candidates": 0,
        "survivors": 0,
        "confirmed": 0,
        "findings": [],
        "raw_candidates": [],
        "ranked_candidates": [],
        "judge_results": [],
        "judge_threshold": float(judge_threshold),
        "operator_labels": [],
        "stage_trace": [],
        "stage_status": stage_status,
        "ranker_complete": True,
        "judge_complete": True,
        "metric_semantics": {
            "N_candidates": "렌즈 원시 후보 수",
            "M_survivors": "ranker가 supported 또는 uncertain으로 표시한 수",
            "legacy_v1_confirmed": "judge 점수가 임계값 이상인 수; K가 아닌 호환 alias",
            "K": "전체 후보를 검토한 운영자의 confirmed 수; 미검토면 null",
            "Z": "스윕 후보 밖 운영자 discovery 수; 미검토면 null",
            "Z_new_class": "operator_discoveries 중 신규 결함 클래스 수",
            "Z_known_recurrence": "operator_discoveries 중 기존 결함 클래스 재발 수",
        },
        "legacy_count_semantics": {
            "N_candidates": "렌즈 원시 후보 수",
            "M_survivors": "ranker가 supported 또는 uncertain으로 표시한 수",
            "confirmed": "v1 judge 확정 호환값; 운영자 K가 아님",
        },
        "cost_usd": 0.0,
        "advisory": True,
    }
    cands = run_lenses(masked_pages, backend, guard, names, stage_status)
    raw_candidates = [dict(candidate) for candidate in cands]
    report["raw_candidates"] = raw_candidates
    report["candidates"] = len(raw_candidates)

    if guard.cap_blocked:
        stage_status["ranker"] = {
            "status": "not_run",
            "items": 0,
            "reason": "cost_cap_upstream",
        }
        ranked = _candidate_records(raw_candidates)
    else:
        ranked = rank_candidates(
            raw_candidates, masked_pages, backend, guard, names, stage_status
        )
    report["ranked_candidates"] = ranked
    report["ranker_complete"] = all(
        candidate["ranker_disposition"] != "unranked" for candidate in ranked
    )
    report["survivors"] = sum(
        candidate["ranker_disposition"] in {"supported", "uncertain"}
        for candidate in ranked
    )

    if not ranked:
        stage_status["judge:normal"] = {
            "status": "not_run",
            "items": 0,
            "reason": "no_candidates",
        }
        stage_status["judge:reverse"] = {
            "status": "not_run",
            "items": 0,
            "reason": "no_candidates",
        }
        judge_results = []
    elif guard.cap_blocked:
        stage_status["judge:normal"] = {
            "status": "not_run",
            "items": 0,
            "reason": "cost_cap_upstream",
        }
        stage_status["judge:reverse"] = {
            "status": "not_run",
            "items": 0,
            "reason": "cost_cap_upstream",
        }
        judge_results = [
            {
                "candidate_id": candidate["candidate_id"],
                "score": None,
                "status": "unscored",
                "run_count": 0,
                "reason_codes": [],
            }
            for candidate in ranked
        ]
    else:
        judge_results = judge_candidates(
            ranked, masked_pages, backend, guard, names, stage_status
        )
    report["judge_results"] = judge_results
    report["judge_complete"] = all(
        result["run_count"] == 2 for result in judge_results
    )

    result_by_id = {result["candidate_id"]: result for result in judge_results}
    confirmed = []
    for candidate in ranked:
        result = result_by_id.get(candidate["candidate_id"], {})
        score = result.get("score")
        if score is not None and score >= judge_threshold:
            confirmed.append({**candidate, "judge_score": score})
    confirmed.sort(key=lambda item: (-item["judge_score"], item["candidate_id"]))
    if guard.partial_reason:
        report["partial"] = True
        report["partial_reason"] = guard.partial_reason
    elif ranked and not report["judge_complete"]:
        report["partial"] = True
        report["partial_reason"] = "incomplete_output:judge"
    report["judge_confirmed_observed"] = len(confirmed)
    report["judge_confirmed"] = None if report["partial"] else len(confirmed)
    report["judge_findings"] = confirmed[:MAX_REPORT_FINDINGS]
    # v1 소비자 호환 alias. 부분 파이프라인에서는 숫자 0으로 위장하지 않는다.
    report["confirmed"] = report["judge_confirmed"]
    report["findings"] = list(report["judge_findings"])
    report["truncated"] = max(0, len(confirmed) - MAX_REPORT_FINDINGS)
    report["cost_usd"] = round(guard.spent_usd, 4)
    report["calls"] = guard.calls
    report["stage_trace"] = list(guard.trace)
    if operator_review is not None and operator_labels is not None:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    if operator_review is not None:
        return apply_operator_review(report, operator_review)
    if operator_labels is not None:
        return apply_operator_labels(report, operator_labels)
    return apply_operator_review(report, None)


def extract_masked_pages(
    pdf_path: str, names: list[str], self_civils: list[str] | None = None
) -> list[str]:
    """PDF 페이지별 텍스트 추출 + 마스킹(self_civils 로 정밀 생일 마스킹) + 전송 벨트.
    names 필수(fail-closed). self_civils 를 주면 한글 형식 생년월일까지 막힌다."""
    if not names:
        raise PIILeakBlocked("names 필수·비어있으면 안 됨")
    import fitz  # lazy(무 PDF 테스트는 masked_pages 주입으로 우회)

    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        masked = mask_for_api(page.get_text(), names, self_civils)
        assert_pii_free(masked, names)  # 전송 전 벨트
        pages.append(masked)
    doc.close()
    return pages


class AnthropicSweepBackend:
    """실 API 백엔드 — anthropic lazy import. 무키/실패는 예외(advisory 파일럿에서 관측)."""

    def complete(self, *, model: str, system: str, user: str) -> tuple[str, int, int]:
        return self.complete_with_metadata(
            model=model,
            system=system,
            user=user,
            role="unspecified",
            stage="global",
        )

    def complete_with_metadata(
        self,
        *,
        model: str,
        system: str,
        user: str,
        role: str,
        stage: str,
    ) -> tuple[str, int, int]:
        import anthropic

        client = anthropic.Anthropic(max_retries=1)
        res = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        llm_usage.add_response(
            res,
            role=role,
            model=model,
            section=_USAGE_SECTION_BY_STAGE.get(stage, "global"),
            attempt=1,
        )
        text = "".join(b.text for b in res.content if getattr(b, "type", "") == "text")
        u = res.usage
        return text, int(u.input_tokens), int(u.output_tokens)


def _write_report(report: dict, stamp: str) -> Path:
    out_dir = ROOT / "handoff" / "reports" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sweep.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = [
        f"# 발송 전 렌즈 스윕 (advisory) — {report['pdf']}",
        "",
        f"- N 후보 {report['candidates']} → M ranker 생존 {report['survivors']}",
        f"- judge_confirmed {report.get('judge_confirmed')} · 운영자 K {report.get('K')}",
        f"- Z 신규 {report.get('Z_new_class')} · Z 기존 재발 {report.get('Z_known_recurrence')}",
        f"- 비용 ${report['cost_usd']} · 콜 {report.get('calls')} · partial={report['partial']}",
        "",
    ]
    for f in report["findings"]:
        md.append(
            f"- [{f['severity']}|{f.get('judge_score')}] p{f['page']} {f['rule']}: {f['rationale']}"
        )
    (out_dir / "sweep.md").write_text("\n".join(md), encoding="utf-8")
    return out_dir


def _is_ignored_local_output(path: Path) -> bool:
    try:
        if path.exists():
            return _is_ignored_local_manifest(path)
        parent = path.parent.resolve(strict=True)
        resolved = parent / path.name
        relative = resolved.relative_to(ROOT.resolve())
    except (FileNotFoundError, OSError, ValueError):
        return False
    checked = subprocess.run(
        ["git", "check-ignore", "--quiet", "--", str(relative)],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return checked.returncode == 0


def _load_ignored_json(path_text: str | None) -> dict:
    if not isinstance(path_text, str) or not path_text.strip():
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    path = Path(path_text)
    if not _is_ignored_local_manifest(path):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    try:
        if path.stat().st_size > _MAX_PII_MANIFEST_BYTES:
            raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OperatorLabelError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID") from exc
    if not isinstance(payload, dict):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    return payload


def _write_ignored_review(path_text: str | None, report: dict) -> None:
    if not isinstance(path_text, str) or not path_text.strip():
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    path = Path(path_text)
    if path.suffix.lower() != ".json" or not _is_ignored_local_output(path):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    temporary = path.with_name(
        f".hsweep-review-{secrets.token_hex(8)}{path.suffix.lower()}"
    )
    if not _is_ignored_local_output(temporary):
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID")
    created = False
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            created = True
            handle.write(json.dumps(report, ensure_ascii=False, indent=2))
        temporary.replace(path)
    except OSError as exc:
        raise OperatorLabelError("OPERATOR_REVIEW_INVALID") from exc
    finally:
        if created and temporary.exists():
            try:
                temporary.unlink()
            except OSError as exc:
                raise OperatorLabelError("OPERATOR_REVIEW_INVALID") from exc


def _sweep_main(raw_argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="발송 전 이질 렌즈 스윕(advisory)")
    ap.add_argument("--pdf")
    ap.add_argument(
        "--pii-manifest",
        help="ignored 로컬 JSON 경로(schema_version=1). 값은 CLI에 직접 쓰지 않음.",
    )
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--approve", action="store_true", help="(잠금) 실 API 스윕 승인")
    ap.add_argument("--allow-llm", action="store_true", help="(잠금) LLM 호출 허용")
    try:
        args, unknown = ap.parse_known_args(raw_argv)
    except SystemExit as exc:
        # 정상 도움말은 argparse exit 0이다. 이를 오류 2로 바꾸지 않고, 잘못된 인자만
        # 기존 계약대로 2로 돌려준다.
        return int(exc.code or 0)
    if unknown or not args.pdf or not args.pii_manifest:
        print("필수 인자 또는 허용 인자 계약 위반", file=sys.stderr)
        return 2
    try:
        names, self_civils = load_pii_manifest(args.pii_manifest)
    except PIIManifestError:
        print("PII manifest 검증 실패", file=sys.stderr)
        return 2
    import os

    approved = (
        args.approve and args.allow_llm and os.environ.get("SAJUGEN_HARNESS_ALLOW_REGEN") == "1"
    )
    if not approved:
        print(
            "실 API 스윕은 3중 잠금(--approve --allow-llm + env SAJUGEN_HARNESS_ALLOW_REGEN=1) 필요",
            file=sys.stderr,
        )
        return 3
    import time

    stamp = args.stamp or time.strftime("%Y%m%d-%H%M%S") + "-sweep"
    report = sweep(
        args.pdf,
        names,
        self_civils=self_civils,
        backend=AnthropicSweepBackend(),
    )
    out = _write_report(report, stamp)
    print(
        f"sweep: {out} (advisory — gate 무접촉) partial={report['partial']} cost=${report['cost_usd']}"
    )
    print(llm_usage.format_line())
    detail_line = llm_usage.format_detail_line()
    if detail_line:
        print(detail_line)
    return 0  # advisory: 결함이 있어도 발송 차단 아님(정보 전용)


def _review_main(raw_argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="hsweep 운영자 검수 결합(API 0)")
    ap.add_argument("--sweep-report")
    ap.add_argument("--operator-review")
    ap.add_argument("--out")
    try:
        args, unknown = ap.parse_known_args(raw_argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    if unknown or not args.sweep_report or not args.operator_review or not args.out:
        print("review 인자 계약 위반", file=sys.stderr)
        return 2
    try:
        report = _canonical_sweep_report_for_review(
            migrate_report(_load_ignored_json(args.sweep_report))
        )
        review = _load_ignored_json(args.operator_review)
        merged = apply_operator_review(report, review)
        _write_ignored_review(args.out, merged)
    except OperatorLabelError:
        print("운영자 review 검증 실패", file=sys.stderr)
        return 2
    print("review: merged")
    return 0


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv in (["-h"], ["--help"]):
        top = argparse.ArgumentParser(description="발송 전 hsweep 도구")
        top.add_argument("command", choices=("sweep", "review"))
        top.print_help()
        return 0
    forbidden = {"--name", "--input-civil", "--birth", "--birth-time"}
    if any(
        argument in forbidden
        or any(argument.startswith(f"{flag}=") for flag in forbidden)
        for argument in raw_argv
    ):
        print("원시 개인정보 CLI 인자 금지 — ignored PII manifest를 사용하세요", file=sys.stderr)
        return 2
    if not raw_argv or raw_argv[0] not in {"sweep", "review"}:
        print("명시적 subcommand(sweep|review)가 필요합니다", file=sys.stderr)
        return 2
    command, command_argv = raw_argv[0], raw_argv[1:]
    return _sweep_main(command_argv) if command == "sweep" else _review_main(command_argv)


if __name__ == "__main__":
    sys.exit(main())
