# -*- coding: utf-8 -*-
"""관리자 검수 화면(docs/10 1차 MVP) — 주문 목록·상세·승인·반려·최종 발급.

설계: 라우트는 얇게(order_flow 호출만), JS 없이 form POST + 303 리다이렉트(PRG).
생성 중(NORMALIZED·CALC_OK)에는 상세 페이지가 meta refresh 로 자동 새로고침.
DB 경로는 환경변수 SAJUGEN_ORDERS_DB(테스트 격리용), 기본 data/orders.sqlite.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import modules as integrated_modules
from . import order_flow
from .content.question_router import QuestionCategory
from .input import time_correction as tc
from .store.orders import ApprovalRequired, IllegalTransition, OrderState, OrderStore

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "web_templates"))

# 생성 진행 중(상세 페이지 자동 새로고침 대상) 상태
_IN_PROGRESS = {OrderState.RECEIVED, OrderState.NORMALIZED, OrderState.CALC_OK}

# 검수 체크리스트(docs/10 — 승인 버튼 옆 고정 표시)
_CHECKLIST = [
    "교차검증 3원 일치 (불일치 시 사유 확인 완료)",
    "고객 질문 답변이 근거와 부합",
    "safe_lint 위반 0건",
    "윤달/시진불명 고지 문구 삽입 확인",
    "이름·호명 오기 없음",
    "PDF 게이트 PASS(텍스트레이어·폰트·태그)",
]


def _db() -> str:
    return os.environ.get("SAJUGEN_ORDERS_DB", order_flow.DEFAULT_DB)


def _store() -> OrderStore:
    # 커넥션은 요청마다 새로 열고 닫는다(스레드 공유 금지 — order_flow 설계)
    return OrderStore(_db())


# ───────────────── 목록 ─────────────────


@router.get("", response_class=HTMLResponse)
def order_list(request: Request, state: str = ""):
    try:
        flt = OrderState(state) if state else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"알 수 없는 상태: {state}")
    st = _store()
    try:
        rows = st.list_orders(flt)
    finally:
        st.close()
    return templates.TemplateResponse(
        request,
        "admin_list.html.j2",
        {
            "rows": rows,
            "state": state,
            "states": [s.value for s in OrderState],
            "seoul_lon": tc.SEOUL_LON,
            "seoul_lat": tc.SEOUL_LAT,
        },
    )


# ───────────────── 접수 ─────────────────


@router.post("/orders")
def intake(
    background: BackgroundTasks,
    birth: str = Form(...),
    lunar: bool = Form(False),
    leap: bool = Form(False),
    gender: str = Form("male"),
    longitude: float = Form(tc.SEOUL_LON),
    latitude: float = Form(tc.SEOUL_LAT),
    yajasi: bool = Form(False),
    horoscope: str = Form(""),
    llm: bool = Form(False),
    name: str = Form(...),
    product: str = Form("integrated"),
    concern: str = Form(""),
    brand: str = Form("sajudoryeong"),
):
    try:
        order_id, _warnings = order_flow.create_order(
            birth=birth,
            lunar=lunar,
            leap=leap,
            gender=gender,
            longitude=longitude,
            latitude=latitude,
            yajasi=yajasi,
            horoscope=horoscope,
            use_llm=llm,
            name=name,
            product=product,
            concern=concern,
            brand=brand,
            db_path=_db(),
        )
    except ValueError as e:  # 정규화 실패 — 주문 미생성(1차 MVP: NEEDS_INFO 미사용)
        raise HTTPException(status_code=422, detail=f"입력 정규화 실패: {e}")
    background.add_task(order_flow.run_generation, order_id, db_path=_db())
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


# ───────────────── 상세 ─────────────────


def _detail_response(
    request: Request,
    order_id: str,
    *,
    status_code: int = 200,
    edit_violations: list | None = None,
    edit_section_id: str = "",
    edit_text: str = "",
    action_error: str = "",
):
    st = _store()
    try:
        try:
            state = st.get_state(order_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"주문 없음: {order_id}")
        report = st.get_report(order_id)
        audit = st.audit(order_id)
    finally:
        st.close()
    meta = report.render_meta
    sections = (report.content or {}).get("sections", [])
    guard = meta.get("guard", {})
    category_state = order_flow.question_category_state(report)
    module_state = order_flow.module_selection_state(report)
    gen_params = dict(meta.get("gen_params", {}))
    raw_partner = gen_params.get("partner")
    partner_present = isinstance(raw_partner, dict) and bool(raw_partner)
    partner_summary = (
        {
            "name": str(raw_partner.get("name") or ""),
            "is_male": bool(raw_partner.get("is_male")),
        }
        if partner_present
        else None
    )
    return templates.TemplateResponse(
        request,
        "admin_detail.html.j2",
        {
            "order_id": order_id,
            "state": state.value,
            "in_progress": state in _IN_PROGRESS,
            "report": report,
            "meta": meta,
            "gen_params": gen_params,
            "sections": sections,
            "guard": guard,
            "flags": report.safety_flags,
            "audit": audit,
            "checklist": _CHECKLIST,
            "edit_violations": edit_violations or [],
            "edit_section_id": edit_section_id,
            "edit_text": edit_text,
            "action_error": action_error,
            "question_category": category_state,
            "question_categories": [category.value for category in QuestionCategory],
            "module_selection": module_state,
            "module_options": tuple(
                module_id
                for module_id in integrated_modules.SELECTABLE_MODULES
                if partner_present or module_id != "gunghap"
            ),
            "recommended_modules": integrated_modules.recommended_modules_for_category(
                category_state["value"],
                partner_present=partner_present,
            ),
            "partner_summary": partner_summary,
        },
        status_code=status_code,
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def order_detail(request: Request, order_id: str):
    return _detail_response(request, order_id)


# ───────────────── 액션(전이) ─────────────────


def _transition_or_409(order_id: str, to_state: OrderState, *, note: str = "") -> None:
    st = _store()
    try:
        st.transition(order_id, to_state, actor="admin", note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"주문 없음: {order_id}")
    except IllegalTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
    finally:
        st.close()


@router.post("/orders/{order_id}/review")
def start_review(order_id: str):
    _transition_or_409(order_id, OrderState.IN_REVIEW, note="검수 시작")
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/approve")
def approve(request: Request, order_id: str, confirm: str = Form("")):
    """관리자 승인 — needs_review(절입 근접·게이트 미클린 등) 주문은 확인(confirm)
    없이는 409(T3.3/G-5). 검수 신호를 무시한 원클릭 승인을 물리 차단(우회 아님 —
    확인 파라미터로 명시 컨펌만 요구)."""
    st = _store()
    try:
        try:
            report = st.get_report(order_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"주문 없음: {order_id}")
        needs_review = bool(getattr(report.safety_flags, "needs_review", False))
        category_state = order_flow.question_category_state(report)
    finally:
        st.close()
    if category_state["needs_confirmation"]:
        return _detail_response(
            request,
            order_id,
            status_code=409,
            action_error="전반으로 자동분류된 질문은 카테고리를 먼저 확정해야 승인할 수 있습니다.",
        )
    if needs_review and not confirm.strip():
        return _detail_response(
            request,
            order_id,
            status_code=409,
            action_error="검수 필요 주문입니다(절입 근접 또는 게이트 미클린). "
            "확인란을 체크한 뒤 승인하세요.",
        )
    _transition_or_409(order_id, OrderState.APPROVED, note="관리자 승인")
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/reject")
def reject(order_id: str, note: str = Form("")):
    _transition_or_409(order_id, OrderState.DRAFTED, note=f"반려: {note}"[:300])
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/retry")
def retry(order_id: str, background: BackgroundTasks):
    st = _store()
    try:
        try:
            state = st.get_state(order_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"주문 없음: {order_id}")
        if state not in (OrderState.CALC_MISMATCH, OrderState.NORMALIZED, OrderState.CALC_OK):
            raise HTTPException(status_code=409, detail=f"재시도 불가 상태: {state.value}")
    finally:
        st.close()
    order_flow.retry_calc(order_id, db_path=_db())
    background.add_task(order_flow.run_generation, order_id, db_path=_db())
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/deliver")
def deliver(request: Request, order_id: str):
    """최종 PDF 발급 — issue_final_pdf(절대규칙 16 게이트) + 재렌더·verify."""
    st = _store()
    try:
        try:
            pdf_path = st.issue_final_pdf(order_id, order_flow.final_render_fn, actor="admin")
        except KeyError:
            raise HTTPException(status_code=404, detail=f"주문 없음: {order_id}")
        except ApprovalRequired as e:
            raise HTTPException(status_code=409, detail=str(e))
        except RuntimeError as e:  # 최종 렌더 게이트 실패 — APPROVED 에 머묾
            return _detail_response(request, order_id, status_code=502, action_error=str(e))
        # 발급 성공 — 최종 경로를 render_meta 에 기록(상태 불변 save)
        report = st.get_report(order_id)
        report = report.model_copy(
            update={"render_meta": {**report.render_meta, "final_pdf": pdf_path}}
        )
        st.save_report(order_id, report, actor="admin")
    finally:
        st.close()
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


# ───────────────── 섹션 직접 수정 ─────────────────


@router.post("/orders/{order_id}/question-category")
def confirm_question_category(
    order_id: str,
    category: str = Form(...),
):
    try:
        order_flow.confirm_question_category(order_id, category, db_path=_db())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except order_flow.EditNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/module-selection")
def confirm_module_selection(
    order_id: str,
    modules: list[str] | None = Form(None),
):
    try:
        order_flow.confirm_module_selection(
            order_id,
            modules or [],
            db_path=_db(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except order_flow.EditNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


@router.post("/orders/{order_id}/sections/{section_id}")
def edit_section(request: Request, order_id: str, section_id: str, text: str = Form("")):
    try:
        violations = order_flow.edit_section(order_id, section_id, text, db_path=_db())
    except order_flow.EditNotAllowed as e:
        raise HTTPException(status_code=403, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if violations:
        # 저장 거부 — 위반 사유와 입력 원문을 유지한 채 상세 화면 재표시(422)
        return _detail_response(
            request,
            order_id,
            status_code=422,
            edit_violations=violations,
            edit_section_id=section_id,
            edit_text=text,
        )
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


# ───────────────── PDF 다운로드 ─────────────────


@router.get("/orders/{order_id}/pdf")
def download_pdf(order_id: str, kind: str = "draft"):
    if kind not in ("draft", "final"):
        raise HTTPException(status_code=422, detail=f"kind 는 draft|final: {kind}")
    st = _store()
    try:
        try:
            report = st.get_report(order_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"주문 없음: {order_id}")
    finally:
        st.close()
    path = report.render_meta.get(f"{kind}_pdf", "")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{kind} PDF 없음")
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))
