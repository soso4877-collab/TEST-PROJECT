# -*- coding: utf-8 -*-
"""주문 오케스트레이션 — 웹 접수와 OrderStore 상태머신·pipeline 을 잇는 레이어.

설계(플랜 sleepy-sleeping-puppy, 2026-06-13):
- pipeline.generate 는 store 를 모른다(CLI 공용 진입점 보존). 전이는 전부 여기서.
- SQLite 커넥션은 스레드 간 공유 금지 — 호출마다 OrderStore 를 새로 열고 닫는다.
- 상태 매핑: 접수(동기) = create(RECEIVED)+NORMALIZED. 백그라운드 생성 =
  교차 불일치면 CALC_MISMATCH(차단, 절대규칙 7), 일치면 CALC_OK → report 채움 → DRAFTED.
  게이트 실패·가드 미클린은 DRAFTED 유지 + needs_review(검수 강화 — 최종 발급 시
  verify 게이트를 다시 통과해야 하므로 가드 우회가 아니다).
- 최종 발급 render_fn 은 항상 재렌더(검수 중 수정 반영 단일 경로) + verify 게이트.
  실패 시 예외 → issue_final_pdf 가 전이하지 않음(절대규칙 16 비우회).
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config as cfg
from . import pipeline
from .content import factcheck, safe_lint
from .content.sections_schema import Report23
from .input import normalize as norm
from .input import time_correction as tc
from .models.report import (
    BirthInput,
    CalendarVerification,
    ReportPlan,
    SafetyFlags,
    UnifiedReport,
)
from .render import pdf as render_pdf
from .render import verify as render_verify
from .store.orders import OrderState, OrderStore

DEFAULT_DB = "data/orders.sqlite"


class EditNotAllowed(Exception):
    """IN_REVIEW 상태가 아닐 때의 본문 수정 시도."""


@dataclass
class _CoverMeta:
    """최종 재렌더용 표지 메타 — render_html 은 saju 객체에서 input_civil 만
    읽는다(render/pdf.py:77 실측). 의존이 늘면 이 클래스와 회귀 테스트를 함께 확장."""

    input_civil: str = ""


# ───────────────── 접수(동기) ─────────────────


def create_order(
    *,
    birth: str,
    lunar: bool = False,
    leap: bool = False,
    gender: str = "male",
    longitude: float = tc.SEOUL_LON,
    latitude: float = tc.SEOUL_LAT,
    yajasi: bool = False,
    horoscope: str = "",
    use_llm: bool = False,
    name: str = "",
    product: str = "integrated",
    concern: str = "",
    brand: str = "default",
    db_path: str = DEFAULT_DB,
) -> tuple[str, list[str]]:
    """주문 접수 — 정규화 성공 시 create(RECEIVED)→NORMALIZED. 실패는 ValueError 그대로
    올림(주문 미생성). 반환 (order_id, 정규화 경고 목록)."""
    parts = birth.split()
    iy, imo, ida = (int(x) for x in parts[0].split("-"))
    unknown_time = len(parts) < 2
    hh, mi = (12, 0) if unknown_time else (int(x) for x in parts[1].split(":"))

    # 음력/윤달 입력은 KASI 1차 기준으로 양력 정규화(app.py /generate 와 동일 규칙)
    nd = norm.normalize_date(iy, imo, ida, is_lunar=lunar, is_leap=leap)
    warnings = list(nd.warnings) if nd.input_kind == "lunar" else []

    is_male = gender.strip().lower() in ("male", "m", "남", "남자")
    report = UnifiedReport(
        order_id="",
        birth=BirthInput(
            name=name,
            gender="M" if is_male else "F",
            input_calendar="lunar" if lunar else "solar",
            input_date=parts[0],
            is_leap_month=leap,
            birth_time=None if unknown_time else f"{hh:02d}:{mi:02d}",
            concern_text=concern or "",
        ),
        calendar_verification=CalendarVerification(
            solar_date=f"{nd.year:04d}-{nd.month:02d}-{nd.day:02d}",
        ),
        report_plan=ReportPlan(product=product),
        render_meta={
            # 백그라운드 생성·재시도가 그대로 쓰는 파라미터(양력 정규화 완료본)
            "gen_params": {
                "year": nd.year,
                "month": nd.month,
                "day": nd.day,
                "hour": hh,
                "minute": mi,
                "is_male": is_male,
                "longitude": longitude,
                "latitude": latitude,
                "yajasi": yajasi,
                "horoscope": horoscope or "",
                "use_llm": use_llm,
                "name": name or "",
                "unknown_time": unknown_time,
                "product": product,
                "concern": concern or "",
                "brand": brand or "default",
            },
            "normalize_warnings": warnings,
        },
    )
    st = OrderStore(db_path)
    try:
        order_id = st.create(report)
        st.transition(
            order_id,
            OrderState.NORMALIZED,
            actor="system",
            note="; ".join(warnings)[:300],
        )
    finally:
        st.close()
    return order_id, warnings


# ───────────────── 생성(백그라운드) ─────────────────


def run_generation(order_id: str, *, generate_fn=None, db_path: str = DEFAULT_DB) -> None:
    """파이프라인 실행 + 상태 전이. LLM 포함 시 3~5분 — BackgroundTasks 로 호출.

    generate_fn 주입은 테스트용(기본 pipeline.generate, 호출 시점 해석이라
    monkeypatch 유효)."""
    gen = generate_fn or pipeline.generate
    st = OrderStore(db_path)
    try:
        report = st.get_report(order_id)
        p = dict(report.render_meta.get("gen_params", {}))
        try:
            r = gen(
                p["year"],
                p["month"],
                p["day"],
                p["hour"],
                p["minute"],
                is_male=p["is_male"],
                longitude=p.get("longitude", tc.SEOUL_LON),
                latitude=p.get("latitude", tc.SEOUL_LAT),
                policy=(tc.ZasiPolicy.YAJASI_SPLIT if p.get("yajasi") else tc.ZasiPolicy.JST_2300),
                horoscope_date=p.get("horoscope") or None,
                use_llm=bool(p.get("use_llm")),
                out_name=f"draft_{order_id}.pdf",
                name=p.get("name") or None,
                unknown_time=bool(p.get("unknown_time")),
                product=p.get("product", "integrated"),
                concern=p.get("concern") or None,
                brand=p.get("brand") or None,
            )
        except Exception as e:  # 생성 실패 — 상태는 그대로(재시도 가능), 감사만 기록
            st.add_audit(
                order_id,
                action="generation_error",
                note=f"{type(e).__name__}: {str(e)[:200]}",
            )
            return

        if not r.calc_consistent:
            # 3원/명리↔자미 교차 불일치 = 주문 차단(절대규칙 7). 관리자 해소 후 재시도.
            mismatch = [x for x in r.reasons if "불일치" in x] or r.reasons
            st.transition(
                order_id,
                OrderState.CALC_MISMATCH,
                actor="system",
                note="; ".join(mismatch)[:300],
            )
            return

        if st.get_state(order_id) == OrderState.NORMALIZED:
            st.transition(order_id, OrderState.CALC_OK, actor="system", note=r.bazi)

        # 기준 연도·나이(표지/개인화) — pipeline 과 동일 산술
        age = None
        horoscope = p.get("horoscope") or ""
        try:
            if horoscope and r.input_civil:
                age = int(str(horoscope)[:4]) - int(str(r.input_civil)[:4])
        except Exception:
            age = None

        report = st.get_report(order_id)  # 최신본 재로드(경합 회피)
        guard = r.guard or {}
        report = report.model_copy(
            update={
                "content": (r.report.model_dump() if r.report is not None else {}),
                "render_meta": {
                    **report.render_meta,
                    "draft_pdf": r.pdf_path,
                    "input_civil": r.input_civil,
                    "bazi": r.bazi,
                    "age": age,
                    "verify": r.verify,
                    "guard": guard,
                    "reasons": list(r.reasons),
                    "crosscheck_warnings": list(r.crosscheck_warnings),
                },
                "safety_flags": SafetyFlags(
                    safe_lint_total=int(guard.get("safe_lint_total", 0)),
                    factcheck_total=int(guard.get("factcheck_total", 0)),
                    grounding_ok=bool(guard.get("grounding_ok", True)),
                    # 게이트 실패·가드 미클린 = 검수 강화 표시(차단 아님 — 최종 발급이 재게이트)
                    needs_review=not r.ok,
                ),
            }
        )
        st.save_report(order_id, report, actor="system")
        st.transition(order_id, OrderState.DRAFTED, actor="system", note=r.pdf_path)
    finally:
        st.close()


def retry_calc(order_id: str, *, db_path: str = DEFAULT_DB) -> None:
    """CALC_MISMATCH 해소 재시도 — NORMALIZED 로 되돌리는 동기 전이만 수행.
    실제 재생성은 호출측이 run_generation 을 백그라운드로 예약한다."""
    st = OrderStore(db_path)
    try:
        if st.get_state(order_id) == OrderState.CALC_MISMATCH:
            st.transition(order_id, OrderState.NORMALIZED, actor="admin", note="재계산 재시도")
    finally:
        st.close()


# ───────────────── 검수 중 본문 수정 ─────────────────


def edit_section(
    order_id: str, section_id: str, text: str, *, actor: str = "admin", db_path: str = DEFAULT_DB
) -> list[dict]:
    """섹션 본문 직접 수정 — 가드 재검증(safe_lint + factcheck 허용 토큰 + 빈 본문).
    위반 목록 반환(빈 리스트=저장 완료). IN_REVIEW 외 상태는 EditNotAllowed."""
    st = OrderStore(db_path)
    try:
        if st.get_state(order_id) != OrderState.IN_REVIEW:
            raise EditNotAllowed("본문 수정은 IN_REVIEW(검수 중) 상태에서만 가능합니다")
        report = st.get_report(order_id)
        if not report.content:
            raise KeyError(f"본문 없음(생성 미완료): {order_id}")
        r23 = Report23.model_validate(report.content)
        try:
            sec = r23.section(section_id)
        except StopIteration:
            raise KeyError(f"섹션 없음: {section_id}") from None

        text = (text or "").strip()
        violations: list[dict] = []
        if not text:
            violations.append(
                {"match": "(빈 본문)", "why": "빈 본문", "suggest": "내용을 입력하세요"}
            )
        else:
            violations += safe_lint.lint(text)
            violations += factcheck.check_with_allow(text, r23.allow_tokens)
        if violations:
            return violations

        sec.final_text = text
        report = report.model_copy(update={"content": r23.model_dump()})
        st.save_report(order_id, report, actor=actor)
        st.add_audit(
            order_id,
            action="edit_section",
            actor=actor,
            section=section_id,
            note=f"{len(text)}자",
        )
        return []
    finally:
        st.close()


# ───────────────── 최종 발급(재렌더 + verify 게이트) ─────────────────


def final_render_fn(report: UnifiedReport) -> str:
    """issue_final_pdf 에 넘기는 render_fn — 저장된 본문(검수 수정 반영)을 항상
    재렌더하고 verify 게이트를 통과해야 경로를 반환. 실패 시 예외 →
    issue_final_pdf 가 DELIVERED 로 전이하지 않는다(게이트 비우회)."""
    if not report.content:
        raise RuntimeError(f"본문 없음(생성 미완료): {report.order_id}")
    r23 = Report23.model_validate(report.content)
    meta = report.render_meta
    p = meta.get("gen_params", {})
    bp = cfg.brand(p.get("brand") or None)
    pdf_path = render_pdf.render_pdf(
        r23,
        _CoverMeta(input_civil=str(meta.get("input_civil", ""))),
        out_name=f"final_{report.order_id}.pdf",
        age=meta.get("age"),
        name=p.get("name") or None,
        unknown_time=bool(p.get("unknown_time")),
        brand=bp,
    )
    v = render_verify.verify(pdf_path)
    if not v.get("gate_pass"):
        raise RuntimeError(
            f"최종 렌더 게이트 실패(text={v.get('text_chars')}, tagged={v.get('tagged')}, "
            f"fonts={v.get('fonts_embedded')})"
        )
    return pdf_path
