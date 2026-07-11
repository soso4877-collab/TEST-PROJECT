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
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from . import config as cfg
from . import integrated
from . import modules as integrated_modules
from . import pipeline
from .calc import engine
from .content import builder, delivery_quality, factcheck, masking, question_router, safe_lint
from .content.sections_schema import GuardReport, Report23, Section
from .input import normalize as norm
from .input import time_correction as tc
from .models.report import (
    BirthInput,
    CalendarVerification,
    CustomerQuestion,
    ReportPlan,
    SafetyFlags,
    UnifiedReport,
)
from .followup import compose as followup_compose
from .refdate import default_ref_date_iso
from .render import pdf as render_pdf
from .render import verify as render_verify
from .store.orders import OrderState, OrderStore

DEFAULT_DB = "data/orders.sqlite"
MAX_FOLLOWUP_PAGES = 15


class EditNotAllowed(Exception):
    """IN_REVIEW 상태가 아닐 때의 본문 수정 시도."""


@dataclass
class _CoverMeta:
    """최종 재렌더용 표지 메타 — render_html 은 saju 객체에서 input_civil 만
    읽는다(render/pdf.py:77 실측). 의존이 늘면 이 클래스와 회귀 테스트를 함께 확장."""

    input_civil: str = ""


def _required_brand_name(value: object) -> str:
    name = str(value or "").strip()
    if not name:
        raise ValueError("brand is required")
    return name


def _stored_input_civil(report: UnifiedReport) -> str:
    """저장 메타를 우선하고, 없으면 저장된 양력일·시각만 이어 표지 문자열을 만든다."""
    saved = str((report.render_meta or {}).get("input_civil") or "").strip()
    if saved:
        return saved
    solar = (report.calendar_verification.solar_date or report.birth.input_date or "").strip()
    if report.birth.birth_time:
        return f"{solar} {report.birth.birth_time}".strip()
    return solar


def _stored_day_master(report: UnifiedReport) -> str:
    """저장된 사주팔자 문자열의 세 번째 기둥에서 일간을 복원한다(새 계산 0)."""
    bazi = str((report.render_meta or {}).get("bazi") or "").strip().split()
    if len(bazi) < 3 or not bazi[2]:
        raise ValueError("stored day master is required for followup PDF")
    return bazi[2][0]


def _render_followup_pdf(
    report: Report23,
    *,
    render_context: dict,
    concern: str,
    out_name: str,
) -> tuple[str, dict]:
    """저장 본문 전용 슬림 PDF를 표준 render→verify 경로로 렌더한다.

    이름·명식 스펙을 새로 계산하지 않는다. 표지는 저장된 input_civil만 사용하고,
    followup 상품의 10~15쪽 범위와 기존 verify 게이트를 모두 통과해야 한다.
    """
    brand = cfg.brand(_required_brand_name(render_context.get("brand")))
    day_master = str(render_context.get("day_master") or "").strip()
    if not day_master:
        raise ValueError("stored day master is required for followup PDF")
    name = str(render_context.get("name") or "").strip() or None
    identity = builder.personal_identity_spec(
        SimpleNamespace(myeongni=SimpleNamespace(day_master=day_master)),
        name,
    )
    if not identity[0] or not identity[1]:
        raise ValueError("stored day master is unsupported for followup PDF")
    pdf_path = render_pdf.render_pdf(
        report,
        _CoverMeta(input_civil=str(render_context.get("input_civil") or "")),
        out_name=out_name,
        name=None,
        unknown_time=bool(render_context.get("unknown_time")),
        brand=brand,
    )
    verify = dict(
        render_verify.verify(
            pdf_path,
            ref_year=render_context.get("ref_year"),
            names=[name] if name else None,
            identity=identity,
            product="followup",
            concern=concern,
            ref_date=render_context.get("ref_date") or None,
            partner_present=report.partner_present,
        )
    )
    pages = verify.get("pages")
    page_range_clean = bool(
        isinstance(pages, int)
        and delivery_quality.MIN_FOLLOWUP_PAGES <= pages <= MAX_FOLLOWUP_PAGES
    )
    verify["followup_page_range"] = {
        "value": pages,
        "minimum": delivery_quality.MIN_FOLLOWUP_PAGES,
        "maximum": MAX_FOLLOWUP_PAGES,
    }
    verify["followup_page_range_clean"] = page_range_clean
    verify["followup_gate_pass"] = bool(verify.get("gate_pass") and page_range_clean)
    return pdf_path, verify


def question_category_state(report: UnifiedReport) -> dict:
    """주문 상세·승인에서 공유하는 질문 분류 상태를 반환한다."""
    render_meta = report.render_meta or {}
    followup_meta = dict(render_meta.get("followup", {}))
    concern = str(
        followup_meta.get("masked_question") or report.birth.concern_text or ""
    ).strip()
    meta = dict(render_meta.get("question_category", {}))
    category = str(meta.get("value") or "").strip()
    if not category and followup_meta:
        category = str(followup_meta.get("category") or "").strip()
    if report.content:
        try:
            stored = Report23.model_validate(report.content).concern_category
            if stored:
                category = stored.strip()
        except Exception:
            # 생성 중의 부분 content나 레거시 저장본은 접수 메타를 사용한다.
            pass
    allowed = {item.value for item in question_router.QuestionCategory}
    if category not in allowed:
        category = question_router.classify(concern).value
    confirmed = bool(meta.get("confirmed") or followup_meta.get("category_confirmed"))
    return {
        "value": category,
        "confirmed": confirmed,
        "source": str(meta.get("source") or "auto"),
        "has_concern": bool(concern),
        "needs_confirmation": bool(
            concern
            and category == question_router.QuestionCategory.GENERAL.value
            and not confirmed
        ),
    }


def module_selection_state(report: UnifiedReport) -> dict:
    """integrated_full 주문의 생성용 모듈 확정 상태를 결정론으로 반환한다.

    3-A 접수는 고객에게 모듈을 받지 않고 빈 목록을 저장한다. 3-B 관리자 UI가 같은
    ``gen_params.modules``에 확정값을 기록하기 전까지 생성·재시도는 fail-closed다.
    """

    render_meta = report.render_meta or {}
    params = dict(render_meta.get("gen_params", {}))
    product = str(params.get("product") or report.report_plan.product or "").strip()
    raw_modules = params.get("modules")
    modules = (
        [str(module_id).strip() for module_id in raw_modules if str(module_id).strip()]
        if isinstance(raw_modules, (list, tuple))
        else []
    )
    confirmed = bool(modules)
    return {
        "product": product,
        "modules": modules,
        "confirmed": confirmed,
        "needs_confirmation": bool(product == integrated.PRODUCT and not confirmed),
    }


def _integrated_report23(result: dict) -> Report23:
    """integrated 조립 결과를 주문 편집·안전 벨트가 소비하는 Report23으로 변환한다."""

    raw_guard = result.get("guard")
    if hasattr(raw_guard, "model_dump"):
        raw_guard = raw_guard.model_dump()
    if not isinstance(raw_guard, dict) or not raw_guard:
        raise RuntimeError("integrated_full guard metadata missing")
    raw_sections = result.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        raise RuntimeError("integrated_full sections missing")
    sections: list[Section] = []
    for raw in raw_sections:
        final_text = str(getattr(raw, "final_text", "") or "")
        sections.append(
            Section(
                id=str(getattr(raw, "id", "") or ""),
                title=str(getattr(raw, "title", "") or ""),
                source_keys=list(getattr(raw, "source_keys", []) or []),
                # 조립기는 검증 완료된 최종 문장만 복사한다. 주문 검수 편집 스키마의
                # 필수 rule_text에는 같은 안전 본문을 넣어 새 사실을 만들지 않는다.
                rule_text=str(getattr(raw, "rule_text", final_text) or final_text),
                final_text=final_text,
                polished=bool(getattr(raw, "polished", False)),
                guard_violations=list(getattr(raw, "guard_violations", []) or []),
            )
        )
    return Report23(
        sections=sections,
        guard=GuardReport.model_validate(raw_guard),
        concern_category=result.get("concern_category"),
        allow_tokens=dict(result.get("allow_tokens") or {}),
        partner_present=bool(result.get("partner_present", False)),
    )


def _integrated_identity_json(identity: object) -> list:
    """identity 3-튜플을 UnifiedReport JSON에 안전한 순서 고정 목록으로 바꾼다."""

    if not isinstance(identity, (list, tuple)) or len(identity) != 3:
        raise RuntimeError("integrated_full identity metadata missing")
    return [
        sorted(str(value) for value in identity[0]),
        sorted(str(value) for value in identity[1]),
        list(identity[2]),
    ]


def _run_integrated_generation(params: dict, order_id: str) -> SimpleNamespace:
    """확정된 1인 모듈 주문을 native integrated_full 빌더로 생성한다."""

    ref_date = default_ref_date_iso()
    horoscope = str(params.get("horoscope") or "").strip()
    try:
        ref_year = int(horoscope[:4]) if horoscope else int(ref_date[:4])
    except (TypeError, ValueError):
        ref_year = int(ref_date[:4])
    policy = tc.ZasiPolicy.YAJASI_SPLIT if params.get("yajasi") else tc.ZasiPolicy.JST_2300
    result = integrated.build_integrated_full(
        [
            (
                str(params.get("name") or ""),
                (
                    int(params["year"]),
                    int(params["month"]),
                    int(params["day"]),
                    int(params["hour"]),
                    int(params["minute"]),
                ),
                bool(params.get("is_male")),
            )
        ],
        receiver_name=str(params.get("name") or "") or None,
        situation=str(params.get("concern") or ""),
        ref_year=ref_year,
        ref_date=ref_date,
        out_name=f"draft_{order_id}.pdf",
        brand=_required_brand_name(params.get("brand")),
        use_llm=bool(params.get("use_llm")),
        render=True,
        modules=list(params.get("modules") or []),
        longitude=float(params.get("longitude", tc.SEOUL_LON)),
        latitude=float(params.get("latitude", tc.SEOUL_LAT)),
        policy=policy,
        horoscope_date=horoscope or f"{ref_year}-06-01",
    )
    content_path = str(result.get("content_path") or "").strip()
    if not content_path or not Path(content_path).is_file():
        raise RuntimeError("integrated_full content persistence missing")
    report23 = _integrated_report23(result)
    verify = dict(result.get("verify") or {})
    guard = report23.guard.model_dump()
    calc_consistent = bool(result.get("calc_consistent"))
    reasons: list[str] = []
    if not calc_consistent:
        reasons.append("integrated_full calculation crosscheck mismatch")
    if not verify.get("gate_pass"):
        reasons.append("integrated_full render gate failed")
    if not report23.guard.clean:
        reasons.append("integrated_full content guard failed")

    people = list(result.get("people") or [])
    names = [str(person.get("name") or "") for person in people if person.get("name")]
    if not names:
        raise RuntimeError("integrated_full names metadata missing")
    identity_json = _integrated_identity_json(result.get("identity"))
    singang = list(result.get("singang") or [])
    role_perspective = list(result.get("role_perspective") or [])
    honorific = list(result.get("honorific") or [])
    if (
        not identity_json[0]
        or not identity_json[1]
        or not identity_json[2]
        or not singang
        or not role_perspective
        or not honorific
    ):
        raise RuntimeError("integrated_full gate spec metadata missing")
    selected_modules = integrated_modules.normalize_modules(result.get("modules"))
    requested_modules = integrated_modules.normalize_modules(params.get("modules"))
    module_sections = dict(result.get("module_sections") or {})
    premerge_section_ids = list(result.get("premerge_section_ids") or [])
    coverage = verify.get("module_coverage")
    if (
        selected_modules != requested_modules
        or result.get("module_schema_version") != integrated.MODULE_SCHEMA_VERSION
        or not module_sections
        or not premerge_section_ids
        or not isinstance(coverage, dict)
        or coverage.get("skipped") is not False
    ):
        raise RuntimeError("integrated_full module gate metadata invalid")
    full_meta = {
        "content_path": content_path,
        "names": names,
        "receiver": str(result.get("receiver") or ""),
        "ref_year": int(result.get("ref_year", ref_year)),
        "ref_date": str(result.get("ref_date") or ref_date),
        "identity": identity_json,
        "singang": singang,
        "role_perspective": role_perspective,
        "honorific": honorific,
        "selected_modules": list(selected_modules),
        "module_schema_version": result.get("module_schema_version"),
        "module_sections": module_sections,
        "premerge_section_ids": premerge_section_ids,
    }
    return SimpleNamespace(
        pdf_path=str(result.get("pdf_path") or ""),
        ok=not reasons,
        reasons=reasons,
        verify=verify,
        guard=guard,
        crosscheck_warnings=list(result.get("crosscheck_warnings") or []),
        bazi=str(result.get("bazi") or ""),
        report=report23,
        calc_consistent=calc_consistent,
        input_civil=str(result.get("input_civil") or ""),
        near_term_boundary=bool(result.get("near_term_boundary")),
        integrated_full_meta=full_meta,
    )


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
    if product == integrated.PRODUCT and unknown_time:
        # 자미 강등이 아직 없는 integrated_full은 정오 추정으로 조용히 진행하지 않는다.
        # 예외는 OrderStore 생성 전에 올려 주문이 물리적으로 남지 않게 한다.
        raise ValueError("integrated_full requires a known birth time")

    # 음력/윤달 입력은 KASI 1차 기준으로 양력 정규화(app.py /generate 와 동일 규칙)
    nd = norm.normalize_date(iy, imo, ida, is_lunar=lunar, is_leap=leap)
    warnings = list(nd.warnings) if nd.input_kind == "lunar" else []

    is_male = gender.strip().lower() in ("male", "m", "남", "남자")
    auto_category = question_router.classify(concern).value
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
            # 접수 직후부터 관리자 상세에 보이도록 자동분류를 저장한다. 생성 완료 뒤에는
            # 동일 분류가 Report23.concern_category에 들어가며 운영자 확정 POST가 그 필드를 갱신한다.
            "question_category": {
                "value": auto_category,
                "confirmed": False,
                "source": "auto",
            },
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
                "brand": _required_brand_name(brand),
                # 윤달 고지(자미 15일 분할법, 절대규칙5) — 음력 윤달생만(T4.4)
                "is_leap": bool(leap and lunar),
                # 3-B 관리자 확정 전의 명시적 빈 상태다. 기존 상품에는 키를 추가하지 않아
                # 저장 JSON과 재생성 입력의 하위호환을 보존한다.
                **({"modules": []} if product == integrated.PRODUCT else {}),
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
        selection = module_selection_state(report)
        if selection["needs_confirmation"]:
            # 생성과 재시도가 공유하는 물리 차단점이다. 상태는 그대로 두고, 감사에는
            # 상품/원인만 남겨 이름·생년월일·질문 원문이 복제되지 않게 한다.
            st.add_audit(
                order_id,
                action="generation_blocked",
                note="integrated_full modules unconfirmed",
            )
            return
        try:
            if selection["product"] == integrated.PRODUCT:
                r = _run_integrated_generation(p, order_id)
            else:
                r = gen(
                    p["year"],
                    p["month"],
                    p["day"],
                    p["hour"],
                    p["minute"],
                    is_male=p["is_male"],
                    longitude=p.get("longitude", tc.SEOUL_LON),
                    latitude=p.get("latitude", tc.SEOUL_LAT),
                    policy=(
                        tc.ZasiPolicy.YAJASI_SPLIT
                        if p.get("yajasi")
                        else tc.ZasiPolicy.JST_2300
                    ),
                    horoscope_date=p.get("horoscope") or None,
                    use_llm=bool(p.get("use_llm")),
                    out_name=f"draft_{order_id}.pdf",
                    name=p.get("name") or None,
                    unknown_time=bool(p.get("unknown_time")),
                    product=p.get("product", "integrated"),
                    concern=p.get("concern") or None,
                    brand=_required_brand_name(p.get("brand")),
                    is_leap=bool(p.get("is_leap")),
                )
        except Exception as e:  # 생성 실패 — 상태는 그대로(재시도 가능), 감사만 기록
            # 예외 문자열에 생년월일이 섞여 audit_log(영속)에 남지 않도록 마스킹(T1.3/E-2).
            try:
                civil = (
                    f"{int(p['year'])}-{int(p['month']):02d}-{int(p['day']):02d} "
                    f"{int(p['hour']):02d}:{int(p['minute']):02d}"
                )
            except Exception:
                civil = None
            note = masking.mask_birth_in_text(f"{type(e).__name__}: {str(e)}", civil)
            st.add_audit(order_id, action="generation_error", note=note[:200])
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
                    "verify": r.verify,
                    "guard": guard,
                    "reasons": list(r.reasons),
                    "crosscheck_warnings": list(r.crosscheck_warnings),
                    **(
                        {"integrated_full": dict(r.integrated_full_meta)}
                        if hasattr(r, "integrated_full_meta")
                        else {}
                    ),
                },
                # 절입 ±2분 근접(T2.2/G-2) = 계산 검수 플래그 충전(관리자 화면 near_term_boundary)
                "calendar_verification": report.calendar_verification.model_copy(
                    update={"near_term_boundary": bool(r.near_term_boundary)}
                ),
                "safety_flags": SafetyFlags(
                    safe_lint_total=int(guard.get("safe_lint_total", 0)),
                    factcheck_total=int(guard.get("factcheck_total", 0)),
                    grounding_ok=bool(guard.get("grounding_ok", True)),
                    # 게이트 실패·가드 미클린 또는 절입 근접 = 검수 강화 표시(차단 아님 — 최종 발급이 재게이트)
                    needs_review=(not r.ok) or bool(r.near_term_boundary),
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


def _followup_domain(category: str) -> str:
    return {
        "연애": "love",
        "직업": "job",
        "재물": "wealth",
        "건강": "health",
        "시기": "timing",
    }.get(category, "etc")


def run_followup(
    *,
    alias: str,
    question: str,
    kind: str = "followup",
    order_id: str | None = None,
    use_llm: bool = False,
    db_path: str = DEFAULT_DB,
    backend=None,
    today=None,
    pdf: bool = False,
) -> dict:
    """저장 report_json 기반 후속 답변 주문 생성.

    계산은 건너뛰고 부모 주문의 저장 사실만 재사용한다. 기본은 기존 텍스트 답변이며,
    pdf=True일 때만 저장 섹션과 새 consult를 조립한 슬림 PDF를 표준 게이트로 검증한다.
    게이트 실패 시 새 주문을 만들지 않는다.
    """
    clean_alias = (alias or "").strip()
    if not clean_alias:
        return {"ok": False, "reason": "alias 없음", "failures": [], "skipped": []}
    st = OrderStore(db_path)
    try:
        st.get_customer(clean_alias)
        parent_id = order_id or st.latest_order_for_alias(clean_alias)
        parent = st.get_report(parent_id)
        parent_params = dict((parent.render_meta or {}).get("gen_params", {}))
        parent_product = str(
            parent_params.get("product") or parent.report_plan.product or ""
        ).strip()
        if parent_product == integrated.PRODUCT:
            # 부분 조합 저장본은 질문 영역의 근거 장이 없을 수 있고 현 compose는 이를
            # 조용히 건너뛴다. 별도 지원 단계 전까지 텍스트·PDF를 같은 지점에서 막는다.
            return {
                "ok": False,
                "answer": "",
                "reason": "integrated_full parent followup is not supported",
                "failures": [
                    {
                        "source": "followup",
                        "rule": "integrated_full_parent_unsupported",
                    }
                ],
                "skipped": [],
            }
        if backend is None:
            from .content import llm_sections

            backend = llm_sections.get_backend() if use_llm else llm_sections.RuleBackend()
        result = followup_compose.compose(
            parent,
            question,
            backend=backend,
            today=today,
            pdf=pdf,
        )
        if not result.get("ok"):
            return result

        pdf_report = result.pop("pdf_report", None)
        pdf_path = ""
        pdf_verify: dict = {}
        render_context: dict = {}
        if pdf:
            if not isinstance(pdf_report, Report23):
                return {
                    **result,
                    "ok": False,
                    "answer": "",
                    "reason": "후속 PDF 조립 결과 없음",
                    "failures": [{"source": "followup", "rule": "missing_pdf_report"}],
                }
            try:
                render_context = {
                    "brand": parent_params.get("brand"),
                    "unknown_time": bool(parent_params.get("unknown_time")),
                    "input_civil": _stored_input_civil(parent),
                    "day_master": _stored_day_master(parent),
                    "name": parent.birth.name,
                    "ref_year": result.get("ref_year"),
                    "ref_date": result.get("ref_date"),
                }
                pdf_path, pdf_verify = _render_followup_pdf(
                    pdf_report,
                    render_context=render_context,
                    concern=question,
                    out_name=f"draft_followup_{uuid4().hex}.pdf",
                )
            except Exception as exc:
                return {
                    **result,
                    "ok": False,
                    "answer": "",
                    "reason": f"후속 PDF 생성 실패({type(exc).__name__})",
                    "failures": [{"source": "render", "rule": "followup_pdf_error"}],
                }
            if not pdf_verify.get("followup_gate_pass"):
                return {
                    **result,
                    "ok": False,
                    "answer": "",
                    "reason": "후속 PDF 게이트 실패",
                    "failures": [
                        {
                            "source": "render_verify",
                            "rule": "followup_pdf_gate",
                            "gate_pass": bool(pdf_verify.get("gate_pass")),
                            "page_range_clean": bool(
                                pdf_verify.get("followup_page_range_clean")
                            ),
                        }
                    ],
                }

        answer = result["answer"]
        masked_question = result.get("masked_question", "")
        category = result.get("category", "전반")
        followup_meta = {
            "parent_order_id": parent_id,
            "category": category,
            "masked_question": masked_question,
        }
        if pdf:
            followup_meta.update(
                {
                    "pdf": True,
                    "brand": render_context["brand"],
                    "unknown_time": render_context["unknown_time"],
                    "day_master": render_context["day_master"],
                    "ref_year": render_context["ref_year"],
                    "ref_date": render_context["ref_date"],
                }
            )
        report_updates = {
            "order_id": "",
            "content": pdf_report.model_dump() if pdf else {},
            "customer_questions": [
                CustomerQuestion(
                    raw=masked_question,
                    domain=_followup_domain(category),
                    answer_text=answer,
                    answer_status="draft",
                )
            ],
            "derived_interpretation": {
                **dict(parent.derived_interpretation or {}),
                "followup_answer": answer,
            },
            "render_meta": {"followup": followup_meta},
            "safety_flags": SafetyFlags(
                safe_lint_total=0,
                factcheck_total=0,
                grounding_ok=True,
                needs_review=False,
            ),
        }
        if pdf:
            report_updates.update(
                {
                    "report_plan": parent.report_plan.model_copy(
                        update={
                            "product": "followup",
                            "sections": [section.id for section in pdf_report.sections],
                        }
                    ),
                    "render_meta": {
                        "followup": followup_meta,
                        "draft_pdf": pdf_path,
                        "input_civil": render_context["input_civil"],
                        "verify": pdf_verify,
                        "guard": pdf_report.guard.model_dump(),
                    },
                }
            )
        report = parent.model_copy(
            deep=True,
            update=report_updates,
        )
        new_id = st.create(
            report,
            alias=clean_alias,
            parent_order_id=parent_id,
            kind=kind if kind in {"followup", "revisit"} else "followup",
        )
        st.transition(new_id, OrderState.NORMALIZED, actor="system", note="followup stored facts reused")
        st.transition(new_id, OrderState.CALC_OK, actor="system", note="calculation skipped")
        st.transition(new_id, OrderState.DRAFTED, actor="system", note="followup answer gate pass")
        st.transition(new_id, OrderState.IN_REVIEW, actor="system", note="followup ready for review")
        response = {
            **result,
            "order_id": new_id,
            "parent_order_id": parent_id,
            "state": st.get_state(new_id).value,
        }
        if pdf:
            response.update({"pdf": True, "draft_pdf": pdf_path, "verify": pdf_verify})
        return response
    finally:
        st.close()


# ───────────────── 검수 중 본문 수정 ─────────────────


def confirm_question_category(
    order_id: str,
    category: str,
    *,
    actor: str = "admin",
    db_path: str = DEFAULT_DB,
) -> str:
    """IN_REVIEW 주문의 Report23 질문 카테고리를 운영자가 확정한다.

    상태 전이는 하지 않고 report_json과 감사 로그만 갱신한다. 감사 note에는 7종
    카테고리 값만 기록해 질문 원문이 영속 로그로 복제되지 않게 한다.
    """
    try:
        selected = question_router.QuestionCategory(category)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in question_router.QuestionCategory)
        raise ValueError(f"알 수 없는 질문 카테고리: {category} (허용: {allowed})") from exc

    st = OrderStore(db_path)
    try:
        if st.get_state(order_id) != OrderState.IN_REVIEW:
            raise EditNotAllowed("질문 카테고리 확정은 IN_REVIEW(검수 중) 상태에서만 가능합니다")
        report = st.get_report(order_id)
        followup_meta = dict((report.render_meta or {}).get("followup", {}))
        content = report.content
        if content:
            report23 = Report23.model_validate(content).model_copy(
                update={"concern_category": selected.value}
            )
            content = report23.model_dump()
        elif not followup_meta:
            raise KeyError(f"본문 없음(생성 미완료): {order_id}")
        if followup_meta:
            followup_meta.update(
                {
                    "category": selected.value,
                    "category_confirmed": True,
                }
            )
        report = report.model_copy(
            update={
                "content": content,
                "render_meta": {
                    **report.render_meta,
                    **({"followup": followup_meta} if followup_meta else {}),
                    "question_category": {
                        "value": selected.value,
                        "confirmed": True,
                        "source": "admin",
                    },
                },
            }
        )
        st.save_report(order_id, report, actor=actor)
        st.add_audit(
            order_id,
            action="confirm_question_category",
            actor=actor,
            section="concern_category",
            note=selected.value,
        )
        return selected.value
    finally:
        st.close()


def confirm_module_selection(
    order_id: str,
    modules: list[str] | tuple[str, ...],
    *,
    actor: str = "admin",
    db_path: str = DEFAULT_DB,
) -> tuple[str, ...]:
    """생성 전 integrated_full 주문의 모듈 목록을 검증해 저장한다.

    레지스트리 정규화를 그대로 사용하므로 빈 목록·미등록·중복은 fail-closed다. 1인 주문
    관리자 경로에서는 gunghap을 한 번 더 거부한다. 상태 전이는 하지 않으며 감사 note에는
    정규화된 모듈 ID만 기록해 고객 입력을 복제하지 않는다.
    """

    st = OrderStore(db_path)
    try:
        state = st.get_state(order_id)
        if state != OrderState.NORMALIZED:
            raise EditNotAllowed(
                "모듈 확정은 생성 전 NORMALIZED 상태에서만 가능합니다"
            )
        report = st.get_report(order_id)
        selection = module_selection_state(report)
        if selection["product"] != integrated.PRODUCT:
            raise ValueError("모듈 확정은 integrated_full 주문에만 사용할 수 있습니다")
        selected = integrated_modules.normalize_modules(modules)
        if "gunghap" in selected:
            raise ValueError("1인 integrated_full 주문에서는 gunghap 모듈을 선택할 수 없습니다")

        render_meta = dict(report.render_meta or {})
        gen_params = dict(render_meta.get("gen_params", {}))
        gen_params["modules"] = list(selected)
        render_meta["gen_params"] = gen_params
        report_plan = report.report_plan.model_copy(
            update={"sections": list(selected)}
        )
        saved = report.model_copy(
            update={
                "render_meta": render_meta,
                "report_plan": report_plan,
            }
        )
        st.save_report(order_id, saved, actor=actor)
        st.add_audit(
            order_id,
            action="confirm_module_selection",
            actor=actor,
            section="modules",
            note=",".join(selected),
        )
        return selected
    finally:
        st.close()


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
    issue_final_pdf 가 DELIVERED 로 전이하지 않는다(게이트 비우회).

    T3.3(B-1+G-5) 최종 발급 게이트 완전화:
    - 그동안 이 최종 재검증이 verify 에 이름·일간 스펙(names/identity)을 전달하지 않아
      해당 게이트가 no-op 였다. draft 시점(pipeline.generate)과 동일하게 gen_params 로
      saju 를 재계산(추가 재렌더 대비 무시할 계산량 — 직렬화 드리프트 0)해 identity/names 를
      복원하고, draft verify 와 동일한 인자(ref_year/ref_date/names/identity)로 최종 게이트를
      건다. singang/role_perspective/honorific 은 다인 상품(integrated_full·gunghap) 전용
      게이트다(integrated.py 가 셋 다 전달; gunghap 은 singang + 호칭 텍스트정규화). 개인 단독
      리포트(order_flow)에는 의미가 없어 None — 개인 경로 실공백은 identity+names 2종.
    - 안전(§12)·사실(factcheck) 재검증 벨트: 최종 비우회 게이트에 안전·사실 검증이 부재해
      검수 수정분이 재검증 없이 발급될 여지가 있었다. Report23 영속 본문·allow_tokens 로
      섹션별 재검증(edit_section 과 동일 함수). 위반은 카운트만 노출(본문 미노출, T1.3/PII).
    """
    if not report.content:
        raise RuntimeError(f"본문 없음(생성 미완료): {report.order_id}")
    r23 = Report23.model_validate(report.content)
    meta = report.render_meta
    p = meta.get("gen_params", {})

    # 안전·사실 재검증 벨트(렌더 전 빠른 차단) — 검수 수정 본문 포함 전 섹션 재검증.
    # match(본문 조각)는 노출하지 않고 카운트만 집계(절대규칙 17 / T1.3).
    belt_safe = 0
    belt_fact = 0
    for sec in r23.sections:
        txt = (getattr(sec, "final_text", "") or "").strip()
        if not txt:
            continue
        belt_safe += len(safe_lint.lint(txt))
        belt_fact += len(factcheck.check_with_allow(txt, r23.allow_tokens))
    if belt_safe or belt_fact:
        raise RuntimeError(
            f"최종 안전·사실 재검증 실패(safe_lint={belt_safe}, factcheck={belt_fact})"
        )

    # 후속 PDF는 저장 Report23만 재렌더한다. 개인 최종본 경로의 engine.build를 타지 않아
    # 최초 리포트 이후 새 계산이 0회라는 followup 경계를 최종 발급에서도 보존한다.
    followup_meta = meta.get("followup", {})
    if bool(followup_meta.get("pdf")):
        concern = str(followup_meta.get("masked_question") or "")
        pdf_path, verify = _render_followup_pdf(
            r23,
            render_context={
                "brand": followup_meta.get("brand"),
                "unknown_time": bool(followup_meta.get("unknown_time")),
                "input_civil": str(meta.get("input_civil") or ""),
                "day_master": followup_meta.get("day_master"),
                "name": report.birth.name,
                "ref_year": followup_meta.get("ref_year"),
                "ref_date": followup_meta.get("ref_date"),
            },
            concern=concern,
            out_name=f"final_{report.order_id}.pdf",
        )
        if not verify.get("followup_gate_pass"):
            page_range = verify.get("followup_page_range", {})
            raise RuntimeError(
                "최종 후속 PDF 게이트 실패("
                f"gate={bool(verify.get('gate_pass'))}, pages={page_range.get('value')}, "
                f"range={bool(verify.get('followup_page_range_clean'))})"
            )
        return pdf_path

    # native integrated_full은 저장 Report23 본문을 같은 integrated 렌더러와 같은
    # identity·singang·role·모듈 커버리지 스펙으로 재검증한다. 메타가 하나라도 없으면
    # 개인 Report23 경로로 강등하지 않고 발급을 차단한다(B-1 no-op 재발 방지).
    if str(p.get("product") or "") == integrated.PRODUCT:
        full_meta = meta.get("integrated_full")
        if not isinstance(full_meta, dict):
            raise RuntimeError("integrated_full final metadata missing")
        required = {
            "names",
            "identity",
            "singang",
            "role_perspective",
            "honorific",
            "selected_modules",
            "module_schema_version",
            "module_sections",
            "premerge_section_ids",
            "ref_year",
            "ref_date",
        }
        missing = sorted(required - set(full_meta))
        if missing:
            raise RuntimeError(f"integrated_full final metadata incomplete(count={len(missing)})")
        if full_meta.get("module_schema_version") != integrated.MODULE_SCHEMA_VERSION:
            raise RuntimeError("integrated_full module schema mismatch")
        try:
            selected_modules = integrated_modules.normalize_modules(
                full_meta.get("selected_modules")
            )
            requested_modules = integrated_modules.normalize_modules(p.get("modules"))
        except ValueError as exc:
            raise RuntimeError("integrated_full final module metadata invalid") from exc
        if selected_modules != requested_modules:
            raise RuntimeError("integrated_full final module metadata mismatch")

        names = [str(name) for name in full_meta.get("names") or [] if str(name)]
        identity_raw = full_meta.get("identity")
        singang = list(full_meta.get("singang") or [])
        role_specs = list(full_meta.get("role_perspective") or [])
        honorific_specs = list(full_meta.get("honorific") or [])
        module_sections = dict(full_meta.get("module_sections") or {})
        premerge_section_ids = list(full_meta.get("premerge_section_ids") or [])
        ref_date = str(full_meta.get("ref_date") or "").strip()
        if (
            not names
            or not isinstance(identity_raw, (list, tuple))
            or len(identity_raw) != 3
            or not identity_raw[0]
            or not identity_raw[1]
            or not identity_raw[2]
            or not singang
            or not role_specs
            or not honorific_specs
            or honorific_specs != role_specs
            or not module_sections
            or not premerge_section_ids
            or not ref_date
        ):
            raise RuntimeError("integrated_full final gate spec missing")
        identity = (list(identity_raw[0]), list(identity_raw[1]), list(identity_raw[2]))
        pdf_path, verify, _attempts = integrated._render_integrated(
            SimpleNamespace(sections=r23.sections),
            names=names,
            ref_year=int(full_meta["ref_year"]),
            situation=str(p.get("concern") or ""),
            identity=identity,
            singang=singang,
            role_specs=role_specs,
            brand=_required_brand_name(p.get("brand")),
            out_name=f"final_{report.order_id}.pdf",
            out_dir=None,
            selected_modules=selected_modules,
            module_sections=module_sections,
            premerge_section_ids=premerge_section_ids,
            ref_date=ref_date,
        )
        coverage = verify.get("module_coverage")
        if (
            not verify.get("gate_pass")
            or not isinstance(coverage, dict)
            or coverage.get("skipped") is not False
        ):
            raise RuntimeError("최종 integrated_full 모듈 게이트 실패")
        return pdf_path

    # draft 와 동일 스펙 복원 — saju 재계산(정책 매핑·horoscope→ref_year 를 pipeline 과 일치).
    bp = cfg.brand(_required_brand_name(p.get("brand")))
    name = p.get("name") or None
    horoscope = p.get("horoscope") or ""
    ref_year = None
    if horoscope:
        try:
            ref_year = int(str(horoscope)[:4])
        except Exception:
            ref_year = None
    identity = None
    names = None
    try:
        saju = engine.build(
            int(p["year"]),
            int(p["month"]),
            int(p["day"]),
            int(p["hour"]),
            int(p["minute"]),
            is_male=bool(p.get("is_male")),
            longitude=p.get("longitude", tc.SEOUL_LON),
            latitude=p.get("latitude", tc.SEOUL_LAT),
            policy=(tc.ZasiPolicy.YAJASI_SPLIT if p.get("yajasi") else tc.ZasiPolicy.JST_2300),
            horoscope_date=horoscope or None,
        )
        identity = builder.personal_identity_spec(saju, name)  # 일간 role 가드(H1.5.3)
        names = [name] if name else None
    except Exception as e:
        # 스펙 재계산 실패 시 게이트를 우회하지 않는다 — 최종 발급 차단(재현 불가는 발급 금지).
        raise RuntimeError(f"최종 스펙 재계산 실패({type(e).__name__})") from e

    pdf_path = render_pdf.render_pdf(
        r23,
        _CoverMeta(input_civil=str(meta.get("input_civil", ""))),
        out_name=f"final_{report.order_id}.pdf",
        name=name,
        unknown_time=bool(p.get("unknown_time")),
        brand=bp,
    )
    v = render_verify.verify(
        pdf_path,
        ref_year=ref_year,
        names=names,
        identity=identity,
        product=p.get("product"),
        concern=p.get("concern") or None,
        ref_date=horoscope or None,
        # QI-2026-07-04: 저장된 Report23 의 파트너 유무로 커플 지칭 승격(레거시 None=비적용).
        partner_present=getattr(r23, "partner_present", None),
    )
    if not v.get("gate_pass"):
        # 불리언 clean 플래그만 노출(hit 본문 미포함 — B-3/PII).
        raise RuntimeError(
            f"최종 렌더 게이트 실패(text={v.get('text_chars')}, tagged={v.get('tagged')}, "
            f"fonts={v.get('fonts_embedded')}, name={v.get('name_policy_clean')}, "
            f"identity={v.get('identity_role_clean')})"
        )
    return pdf_path
