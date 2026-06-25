# -*- coding: utf-8 -*-
"""운영자 CLI - `python -m sajugen.cli gen ...`. 검증 게이트 실패 시 비정상 종료."""

from __future__ import annotations

import typer

from .input import normalize as norm
from .input import time_correction as tc
from .pipeline import generate

app = typer.Typer(add_completion=False, help="사주풀이 PDF 생성기 (운영자 내부 도구)")


@app.command()
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
        "sajudoryeong", help="브랜드: 프리셋 키(sajudoryeong/seodam/default) 또는 임의 문구(그 문구로 표기)"
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
    )

    typer.echo(f"사주팔자: {r.bazi}")
    typer.echo(
        f"PDF: {r.pdf_path}  ({r.verify['pages']}p, "
        f"텍스트 {r.verify['text_chars']}자, tagged={r.verify['tagged']})"
    )
    if r.crosscheck_warnings:
        typer.echo("경고: " + " / ".join(r.crosscheck_warnings))
    if r.ok:
        typer.echo("게이트: PASS")
    else:
        typer.echo("게이트: FAIL - " + " / ".join(r.reasons))
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
