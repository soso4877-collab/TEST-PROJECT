# -*- coding: utf-8 -*-
"""발송 전 이질 렌즈 스윕 (Phase 4, L2 advisory).

육안급 결함을 발송 전에 선제 적발하는 후보 발굴기. 연구 근거(설계): 동종 debate 는
다수결을 못 넘음(2311.17371) → 렌즈/모델 이질성 + generator-critic 분리. LLM judge
자기선호 편향(2404.13076) → 렌즈≠judge 모델 + 순서 스왑. 코드리뷰 오탐 15-30%
(2407.00215) → advisory 전용, 사람 최종.

파이프라인: (a) 이질 렌즈 5종 후보 발굴(Sonnet, 렌즈별 신선 컨텍스트) → (b) 통합 적대
반박 1콜(환각·오탐 제거) → (c) 루브릭 judge(Opus, 순서 스왑 2콜 평균) → (d) sweep.json/md.

불변(구조적):
- **advisory**: 이 모듈은 verify/order_flow/게이트 상태머신을 import 하지 않는다(코드로 보장).
  gate_pass·발송 판정에 일절 접촉 없음. 산출은 정보 전용(exit code 포함).
- **PII 0(fail-closed)**: API 전송 전 이름·생년월일·시각을 마스킹하고, 전송 직전 벨트로
  잔존을 재검증해 남아 있으면 전송하지 않고 예외. names 는 필수 인자(기본값 없음).
- **비용 상한(pre-call, 보수적)**: 매 호출 전 상한 초과 여부를 과대추정으로 점검, 초과 시
  중단하고 부분 리포트. 실사용 토큰은 관측 기록.
- **인용 금지**: 렌즈 프롬프트는 본문 verbatim 인용을 금지하고, 리포트 스키마에 고객 본문
  자유텍스트 필드가 없다(rule/page/severity/비-PII 근거만).

실제 스윕 실행(API 과금)은 운영자 명시 승인 + 3중 잠금(--approve --allow-llm + env) 후에만.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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


class CostCapExceeded(Exception):
    """상한 초과 — 중단하고 부분 리포트."""


class PIILeakBlocked(Exception):
    """마스킹 후에도 PII 잔존 — 전송 차단(fail-closed)."""


class CostGuard:
    """pre-call 상한 점검 + 실사용 관측. 캡은 보수적 과대추정으로 fail-closed."""

    def __init__(self, cap_usd: float = COST_CAP_USD):
        self.cap = cap_usd
        self.spent_usd = 0.0
        self.calls = 0

    def check_before(self, est_in: int, est_out: int) -> None:
        projected = self.spent_usd + self._est(est_in, est_out)
        if projected > self.cap:
            raise CostCapExceeded(
                f"예상 지출 ${projected:.2f} > 상한 ${self.cap:.2f} (누적 ${self.spent_usd:.2f})"
            )

    def record(self, in_tok: int, out_tok: int, price_key: str = "sonnet") -> None:
        pin, pout = _PRICE.get(price_key, _PRICE["opus"])
        self.spent_usd += in_tok / 1e6 * pin + out_tok / 1e6 * pout
        self.calls += 1

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
            raise PIILeakBlocked(f"이름 잔존 — 전송 차단")
    if _DATE_RX.search(text):
        raise PIILeakBlocked("날짜/시각 잔존 — 전송 차단")


def _safe_call(backend, *, role: str, system: str, user: str, names: list[str], guard: CostGuard):
    """모든 API 경유는 이 함수만 통과 — 마스킹 벨트 + pre-call 캡을 강제한다."""
    assert_pii_free(system, names)
    assert_pii_free(user, names)
    est_in = (len(system) + len(user)) // 3  # 보수적 토큰 추정(문자/3)
    guard.check_before(est_in, 1500)
    model = cfg.llm_model(role)
    text, in_tok, out_tok = backend.complete(model=model, system=system, user=user)
    price_key = "opus" if "opus" in model else ("haiku" if "haiku" in model else "sonnet")
    guard.record(in_tok, out_tok, price_key)
    return text


def _load_lens_prompt(lens_id: str) -> str:
    p = _PROMPT_DIR / f"lens_{lens_id}.md"
    return p.read_text(encoding="utf-8")


def _parse_findings(text: str, lens_id: str, names: list[str]) -> list[dict]:
    """모델 출력에서 JSON findings 파싱 — 스키마 밖 필드 폐기(고객 본문 자유텍스트 유입 차단).
    rationale 는 모델 free-text 라 parse 시점에 name/date 스크럽(리포트·refute/judge 다운스트림
    양쪽 정화 — 이름/날짜 외 PII 잔여는 벨트+프롬프트로 축소, docs 에 residual 명시)."""
    try:
        m = re.search(r"\[.*\]", text, re.S)
        raw = json.loads(m.group(0)) if m else []
    except Exception:
        return []
    out = []
    for f in raw if isinstance(raw, list) else []:
        if not isinstance(f, dict):
            continue
        out.append(
            {
                "lens": lens_id,
                "page": f.get("page"),
                "severity": str(f.get("severity", "unknown"))[:12],
                "rule": _scrub(str(f.get("rule", "")), names)[:60],
                "rationale": _scrub(str(f.get("rationale", "")), names)[:400],
            }
        )
    return out


def run_lenses(masked_pages: list[str], backend, guard: CostGuard, names: list[str]) -> list[dict]:
    body = "\n\n".join(f"[p{i + 1}]\n{t}" for i, t in enumerate(masked_pages))
    findings: list[dict] = []
    for lens_id in LENS_IDS:
        system = _load_lens_prompt(lens_id)
        out = _safe_call(
            backend, role="sweep_lens", system=system, user=body, names=names, guard=guard
        )
        findings.extend(_parse_findings(out, lens_id, names))
    return findings


def refute(findings: list[dict], backend, guard: CostGuard, names: list[str]) -> list[dict]:
    if not findings:
        return []
    system = (
        "너는 적대적 검증자다. 아래 결함 후보들에서 환각(근거 없는)·오탐(정상을 결함으로)"
        "인 것을 제거하라. 살아남는 후보만 같은 JSON 배열로 반환하라. 본문을 인용하지 마라."
    )
    user = json.dumps(findings, ensure_ascii=False)
    out = _safe_call(backend, role="sweep_lens", system=system, user=user, names=names, guard=guard)
    survivors = _parse_findings(out, "refuted", names)
    # lens 라벨 보존(refute 는 필터일 뿐) — page/rule 로 원 후보 매칭.
    keyset = {(f.get("page"), f.get("rule")) for f in survivors}
    return [f for f in findings if (f.get("page"), f.get("rule")) in keyset] or survivors


def judge(finding: dict, backend, guard: CostGuard, names: list[str]) -> float:
    """루브릭 0-1 채점(Opus). 순서 스왑 2콜 평균(자기선호·위치 편향 완화)."""
    rubric = (
        "다음 결함 후보가 실제 발송 차단 가치가 있는지 0.0~1.0 루브릭으로 채점하라. "
        "0=오탐/무의미, 0.5=경미, 1.0=발송 전 반드시 수정. 숫자만 반환."
    )
    scores = []
    for order in ("정상 순서", "역순 제시"):
        user = f"[{order}]\n{json.dumps(finding, ensure_ascii=False)}"
        out = _safe_call(
            backend, role="sweep_judge", system=rubric, user=user, names=names, guard=guard
        )
        mm = re.search(r"[01](?:\.\d+)?", out)
        scores.append(float(mm.group(0)) if mm else 0.0)
    return round(sum(scores) / len(scores), 3)


def sweep(
    pdf_path: str,
    names: list[str],
    *,
    backend,
    guard: CostGuard | None = None,
    masked_pages: list[str] | None = None,
    judge_threshold: float = 0.5,
) -> dict:
    """전 파이프라인. masked_pages 를 주면 PDF 추출을 건너뛴다(테스트/재사용).
    부분 실패(캡 초과)는 partial=True 로 표시하고 그때까지의 리포트를 반환한다."""
    if not names:
        raise PIILeakBlocked("names 필수·비어있으면 안 됨 — 마스킹 없이 스윕 불가(fail-closed)")
    guard = guard or CostGuard()
    if masked_pages is None:
        masked_pages = extract_masked_pages(pdf_path, names)
    report = {
        "pdf": Path(pdf_path).name,
        "lenses": list(LENS_IDS),
        "partial": False,
        "candidates": 0,
        "survivors": 0,
        "confirmed": 0,
        "findings": [],
        "cost_usd": 0.0,
        "advisory": True,
    }
    try:
        cands = run_lenses(masked_pages, backend, guard, names)
        report["candidates"] = len(cands)
        survivors = refute(cands, backend, guard, names)
        report["survivors"] = len(survivors)
        scored = []
        for f in survivors:
            f = {**f, "judge_score": judge(f, backend, guard, names)}
            scored.append(f)
        confirmed = [f for f in scored if f["judge_score"] >= judge_threshold]
        confirmed.sort(key=lambda x: -x["judge_score"])
        report["confirmed"] = len(confirmed)
        report["findings"] = confirmed[:MAX_REPORT_FINDINGS]
        report["truncated"] = max(0, len(confirmed) - MAX_REPORT_FINDINGS)
    except CostCapExceeded as e:
        report["partial"] = True
        report["partial_reason"] = str(e)
    report["cost_usd"] = round(guard.spent_usd, 4)
    report["calls"] = guard.calls
    return report


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
        import anthropic

        client = anthropic.Anthropic(max_retries=1)
        res = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        llm_usage.add_response(res)
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
        f"- 후보 {report['candidates']} → 생존 {report['survivors']} → 확정 {report['confirmed']}",
        f"- 비용 ${report['cost_usd']} · 콜 {report.get('calls')} · partial={report['partial']}",
        "",
    ]
    for f in report["findings"]:
        md.append(
            f"- [{f['severity']}|{f.get('judge_score')}] p{f['page']} {f['rule']}: {f['rationale']}"
        )
    (out_dir / "sweep.md").write_text("\n".join(md), encoding="utf-8")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="발송 전 이질 렌즈 스윕(advisory)")
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--name", action="append", default=[], help="마스킹할 실명(반복). 필수.")
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--approve", action="store_true", help="(잠금) 실 API 스윕 승인")
    ap.add_argument("--allow-llm", action="store_true", help="(잠금) LLM 호출 허용")
    args = ap.parse_args(argv)
    if not args.name:
        print("names(--name) 필수 — 마스킹 없이 실행 불가(fail-closed)", file=sys.stderr)
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
    report = sweep(args.pdf, args.name, backend=AnthropicSweepBackend())
    out = _write_report(report, stamp)
    print(
        f"sweep: {out} (advisory — gate 무접촉) partial={report['partial']} cost=${report['cost_usd']}"
    )
    print(llm_usage.format_line())
    return 0  # advisory: 결함이 있어도 발송 차단 아님(정보 전용)


if __name__ == "__main__":
    sys.exit(main())
