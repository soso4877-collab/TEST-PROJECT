# -*- coding: utf-8 -*-
"""계산 특이점(경계 케이스) 익명 추출 — 엔진 개선용 골든 후보 데이터셋.

개인정보보호법 근거: 식별자(이름·출생지·고민 원문·order_id 연계)를 제거하고 계산 사실·경계
플래그만 남기면 통계·과학적 연구 목적의 가명/익명정보(제28조의2·제58조의2)로 활용 가능하다.
원본 PII는 별도로 파기(제21조, delete_order.py)한다.

설계 원칙 — 화이트리스트 수집:
저장 주문(UnifiedReport)에는 PII가 birth·render_meta.gen_params(name/concern)·content 등 여러 곳에
분산돼 있다. 따라서 '전체 복사 후 제거'가 아니라 **안전 필드만 명시적으로 골라 담는다.**
name·birthplace·concern·order_id·content 는 어떤 경우에도 레코드에 넣지 않는다.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from .models.report import UnifiedReport

# 엔진 버전 태그(골든 회귀 기준선 식별용). 계산 로직 변경 시 갱신.
ENGINE_VERSION = "sajugen-calc/2026-06"
DEFAULT_OUT = "data/calc_insights.jsonl"


def boundary_labels(report: "UnifiedReport") -> list[str]:
    """이 주문의 '계산 특이점' 라벨 목록(비식별 신호에서 도출). 비면 평범한 케이스."""
    labels: list[str] = []
    rm = report.render_meta or {}

    xwarn = rm.get("crosscheck_warnings") or []
    joined = " ".join(xwarn)
    if any("사주팔자 불일치" in w or ("명리" in w and "불일치" in w) for w in xwarn):
        labels.append("bazi_mismatch")
    if "월지" in joined:
        labels.append("month_branch_mismatch")
    if "자시" in joined or "시지" in joined:
        labels.append("hour_zasi_conflict")

    if rm.get("normalize_warnings"):
        labels.append("normalize_warning")
        if any("한·중" in w for w in rm.get("normalize_warnings", [])):
            labels.append("kr_cn_lunar_divergence")

    cv = report.calendar_verification
    if getattr(cv, "near_term_boundary", False):
        labels.append("near_term_boundary")

    # 자시 경계(23:00~23:59 출생) — 일주 전환 학설차가 갈리는 지점
    gp = rm.get("gen_params") or {}
    hour = gp.get("hour")
    if hour == 23:
        labels.append("zasi_boundary_2300")

    if report.safety_flags.needs_review:
        labels.append("needs_review")

    # 중복 제거(순서 보존)
    seen: set[str] = set()
    return [x for x in labels if not (x in seen or seen.add(x))]


def is_boundary(report: "UnifiedReport") -> bool:
    return bool(boundary_labels(report))


def extract_insight(
    report: "UnifiedReport",
    *,
    engine_version: str = ENGINE_VERSION,
    extracted_at: str | None = None,
) -> dict:
    """주문 → 익명 계산특이점 레코드(화이트리스트). PII 일절 미포함.

    포함: 입력(분단위)·성별·역법 + 4주·자미유무 + 경계 신호/라벨.
    미포함: name·birthplace·concern·customer_questions·content·order_id."""
    rm = report.render_meta or {}
    gp = rm.get("gen_params") or {}
    cv = report.calendar_verification
    return {
        "schema": "calc_insight_v1",
        # 입력(식별자 아님 — 이름·출생지·고민 미접근)
        "year": gp.get("year"),
        "month": gp.get("month"),
        "day": gp.get("day"),
        "hour": gp.get("hour"),
        "minute": gp.get("minute"),
        "gender": report.birth.gender,
        "input_calendar": report.birth.input_calendar,
        "is_leap_month": report.birth.is_leap_month,
        "unknown_time": bool(gp.get("unknown_time")),
        "solar_date": cv.solar_date,
        # 파생 계산 사실
        "bazi": rm.get("bazi", ""),
        "ziwei_present": report.ziwei is not None,
        # 경계/특이점 신호
        "near_term_boundary": bool(getattr(cv, "near_term_boundary", False)),
        "term_minutes_diff": getattr(cv, "term_minutes_diff", None),
        "crosscheck_warnings": list(rm.get("crosscheck_warnings") or []),
        "normalize_warnings": list(rm.get("normalize_warnings") or []),
        "needs_review": report.safety_flags.needs_review,
        "boundary_labels": boundary_labels(report),
        # 메타
        "engine_version": engine_version,
        "extracted_at": extracted_at,
    }


def append_insight(record: dict, path: str = DEFAULT_OUT) -> None:
    """레코드를 JSONL 1행으로 append(없으면 디렉터리 생성). 익명 데이터셋 누적."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ───────────────── CLI ─────────────────

app = typer.Typer(add_completion=False, help="계산 특이점 익명 추출(엔진 개선용 골든 후보)")


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@app.command()
def extract(
    order_id: str = typer.Option(..., "--order-id", help="추출할 주문 ID"),
    db: str = typer.Option("data/orders.sqlite", "--db", help="주문 DB 경로"),
    out: str = typer.Option(DEFAULT_OUT, "--out", help="익명 데이터셋 JSONL 경로"),
    all_cases: bool = typer.Option(
        False, "--all", help="경계 아닌 평범한 케이스도 추출(기본: 경계만)"
    ),
) -> None:
    from .store.orders import OrderStore

    store = OrderStore(db)
    try:
        try:
            report = store.get_report(order_id)
        except KeyError:
            typer.echo(f"주문 없음: {order_id}")
            raise typer.Exit(code=1)
        if not all_cases and not is_boundary(report):
            typer.echo(f"평범한 케이스(경계 신호 없음) - 건너뜀. 전수 추출은 --all.")
            raise typer.Exit(code=0)
        rec = extract_insight(report, extracted_at=_now_iso())
        append_insight(rec, out)
        typer.echo(f"추출 완료: {out} (라벨 {rec['boundary_labels']})")
    finally:
        store.close()


@app.command()
def sweep(
    db: str = typer.Option("data/orders.sqlite", "--db", help="주문 DB 경로"),
    out: str = typer.Option(DEFAULT_OUT, "--out", help="익명 데이터셋 JSONL 경로"),
    all_cases: bool = typer.Option(
        False, "--all", help="경계 아닌 평범한 케이스도 추출(기본: 경계만)"
    ),
) -> None:
    from .store.orders import OrderStore

    store = OrderStore(db)
    try:
        n = 0
        for row in store.list_orders():
            report = store.get_report(row["order_id"])
            if not all_cases and not is_boundary(report):
                continue
            append_insight(extract_insight(report, extracted_at=_now_iso()), out)
            n += 1
        typer.echo(f"추출 완료: {n}건 -> {out}")
    finally:
        store.close()


if __name__ == "__main__":
    app()
