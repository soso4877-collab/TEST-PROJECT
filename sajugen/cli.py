# -*- coding: utf-8 -*-
"""운영자 CLI - `python -m sajugen.cli gen ...`. 검증 게이트 실패 시 비정상 종료."""

from __future__ import annotations

import typer

from . import order_flow
from .content import llm_usage
from .input import normalize as norm
from .input import time_correction as tc
from .pipeline import generate
from .store.orders import OrderStore

app = typer.Typer(add_completion=False, help="사주풀이 PDF 생성기 (운영자 내부 도구)")


@app.command("customer-find")
def customer_find(
    name: str | None = typer.Option(None, "--name", help="마스킹 식별자 검색어"),
    alias: str | None = typer.Option(None, "--alias", help="단골 별칭"),
    db: str = typer.Option(order_flow.DEFAULT_DB, "--db", help="주문 DB 경로"),
) -> None:
    """단골 별칭과 최근 주문을 찾는다. 이름은 name_masked 저장값만 출력한다."""
    if not name and not alias:
        typer.echo("--name 또는 --alias 중 하나는 필요합니다.")
        raise typer.Exit(code=1)
    store = OrderStore(db)
    try:
        rows = store.find_customers(alias=alias, name_masked=name)
    finally:
        store.close()
    if not rows:
        typer.echo("검색 결과 없음")
        raise typer.Exit(code=1)
    for row in rows:
        typer.echo(
            "alias={alias} name_masked={name} latest_order_id={order} "
            "kind={kind} purged_at={purged}".format(
                alias=row.get("alias") or "",
                name=row.get("name_masked") or "",
                order=row.get("latest_order_id") or "",
                kind=row.get("latest_kind") or "",
                purged=row.get("purged_at") or "",
            )
        )


@app.command("customer-purge")
def customer_purge(
    alias: str = typer.Option(..., "--alias", help="식별자를 파기할 단골 별칭"),
    yes: bool = typer.Option(False, "--yes", help="확인 프롬프트 없이 식별자 파기 실행"),
    db: str = typer.Option(order_flow.DEFAULT_DB, "--db", help="주문 DB 경로"),
) -> None:
    """단골 식별자(name_masked)만 파기하고 명식·주문·별칭은 보존한다."""
    store = OrderStore(db)
    try:
        try:
            store.get_customer(alias)
        except KeyError:
            typer.echo(f"단골 없음(alias={alias})")
            raise typer.Exit(code=1)

        if not yes:
            ok = typer.confirm(f"alias={alias} 식별자만 파기할까요? 명식·별칭·주문은 보존됩니다.")
            if not ok:
                typer.echo("식별자 파기 취소")
                raise typer.Exit(code=1)

        try:
            store.purge_identifier(alias)
        except KeyError:
            typer.echo(f"단골 없음(alias={alias})")
            raise typer.Exit(code=1)
        customer = store.get_customer(alias)
        typer.echo(
            "식별자 파기 완료(alias={alias}, purged_at={purged_at}, 명식·별칭 보존)".format(
                alias=alias,
                purged_at=customer.get("purged_at") or "",
            )
        )
    finally:
        store.close()


@app.command("gen-followup")
def gen_followup(
    alias: str = typer.Option(..., "--alias", help="단골 별칭"),
    question: str = typer.Option(..., "--question", help="후속 질문"),
    kind: str = typer.Option("followup", "--kind", help="followup|revisit"),
    order_id: str | None = typer.Option(None, "--order-id", help="부모 주문 ID(미지정 시 최신 주문)"),
    llm: bool = typer.Option(False, "--llm", help="ANTHROPIC_API_KEY가 있을 때 LLM 답변 생성"),
    pdf: bool = typer.Option(False, "--pdf", help="저장 사실로 10~15쪽 슬림 PDF도 생성"),
    db: str = typer.Option(order_flow.DEFAULT_DB, "--db", help="주문 DB 경로"),
) -> None:
    """저장 리포트 사실만 재사용해 후속 텍스트 또는 슬림 PDF 주문을 만든다."""
    result = order_flow.run_followup(
        alias=alias,
        question=question,
        kind=kind,
        order_id=order_id,
        use_llm=llm,
        pdf=pdf,
        db_path=db,
    )
    if not result.get("ok"):
        typer.echo("게이트: FAIL - " + str(result.get("reason") or "후속 답변 실패"))
        rules = sorted({str(f.get("rule")) for f in result.get("failures", []) if f.get("rule")})
        if rules:
            typer.echo("failures: " + ",".join(rules[:12]))
        raise typer.Exit(code=1)
    typer.echo(f"order_id={result['order_id']} parent_order_id={result['parent_order_id']} state={result['state']}")
    if pdf:
        typer.echo(f"draft_pdf={result['draft_pdf']}")
    typer.echo(result["answer"])


@app.command()
@llm_usage.isolated_run
def gen(
    birth: str = typer.Option(
        ..., help="생년월일시 'YYYY-MM-DD HH:MM'. 생시 미상이면 'YYYY-MM-DD' 만"
    ),
    lunar: bool = typer.Option(False, help="입력이 음력이면 지정(기본 양력)"),
    leap: bool = typer.Option(False, help="음력 윤달생이면 지정(--lunar 와 함께)"),
    gender: str = typer.Option(..., help="male|female 또는 남|여"),
    longitude: float = typer.Option(tc.SEOUL_LON, help="출생지 경도(기본 서울)"),
    latitude: float = typer.Option(tc.SEOUL_LAT, help="출생지 위도(기본 서울)"),
    yajasi: bool = typer.Option(False, help="야자시/조자시 분리 정책 사용"),
    horoscope: str = typer.Option(None, help="대한/유년 기준일 'YYYY-MM-DD'"),
    llm: bool = typer.Option(False, help="LLM 윤문 사용(무키 시 자동 룰 폴백)"),
    name: str = typer.Option(..., help="이름(필수 - 호명 '수하님' 개인화, 운영자 지시 2026-06-12)"),
    concern: str = typer.Option(None, help="고객 고민/질문(선택). 분류 -> 맞춤 안내 섹션"),
    product: str = typer.Option("integrated", help="상품: integrated|myeongni|ziwei"),
    brand: str = typer.Option(
        "sajudoryeong",
        help="브랜드: 프리셋 키(sajudoryeong/seodam/default) 또는 임의 문구(그 문구로 표기)",
    ),
    out: str = typer.Option("saju_report.pdf", help="출력 파일명"),
) -> None:
    parts = birth.split()
    d = parts[0]
    iy, imo, ida = (int(x) for x in d.split("-"))
    unknown_time = len(parts) < 2
    if unknown_time:
        hh, mi = 12, 0  # 생시 미상: 표준시 정오로 계산하되 시주는 '추정'으로 고지
    else:
        hh, mi = (int(x) for x in parts[1].split(":"))

    # 음력/윤달 입력은 KASI 1차 기준으로 양력 정규화 후 엔진에 투입
    nd = norm.normalize_date(iy, imo, ida, is_lunar=lunar, is_leap=leap)
    y, mo, da = nd.year, nd.month, nd.day
    if nd.input_kind == "lunar":
        typer.echo(f"입력 정규화: {nd.note} [{nd.source}]")
        for w in nd.warnings:
            typer.echo("  주의: " + w)

    is_male = gender.strip().lower() in ("male", "m", "남", "남자")
    policy = tc.ZasiPolicy.YAJASI_SPLIT if yajasi else tc.ZasiPolicy.JST_2300

    r = generate(
        y,
        mo,
        da,
        hh,
        mi,
        is_male=is_male,
        longitude=longitude,
        latitude=latitude,
        policy=policy,
        horoscope_date=horoscope,
        use_llm=llm,
        out_name=out,
        name=name,
        unknown_time=unknown_time,
        product=product,
        concern=concern,
        brand=brand,
        is_leap=bool(leap and lunar),  # 윤달 고지(자미 15일 분할법)는 음력 윤달생만
    )

    typer.echo(f"사주팔자: {r.bazi}")
    typer.echo(
        f"PDF: {r.pdf_path}  ({r.verify['pages']}p, "
        f"텍스트 {r.verify['text_chars']}자, tagged={r.verify['tagged']})"
    )
    if r.crosscheck_warnings:
        typer.echo("경고: " + " / ".join(r.crosscheck_warnings))
    # 사용량 관측(2026-07-05): 빌드 1회의 LLM 지출을 stdout 에 남긴다(PII 0, ASCII 키).
    # hrun._regen_pdf 가 이 줄을 파싱해 summary(regen_llm_usage)로 올린다.
    typer.echo(llm_usage.format_line())
    if usage_detail := llm_usage.format_detail_line():
        typer.echo(usage_detail)  # 역할·모델·캐시 토큰만 포함(프롬프트/응답/PII 없음)
    # 챕터별 윤문/폴백 관측(P0 2026-07-05): 어느 챕터가 골격으로 남았는지 즉시 확인
    # (QI-2026-07-05-03: v7 consult 폴백이 카운트만으로는 안 보였던 관측 갭). PII 0.
    g = r.report.guard
    typer.echo(
        "chapters: polished="
        + (",".join(g.polished_section_ids) or "-")
        + " fallback="
        + (",".join(g.fallback_section_ids) or "-")
    )
    if r.ok:
        typer.echo("게이트: PASS")
    else:
        typer.echo("게이트: FAIL - " + " / ".join(r.reasons))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
