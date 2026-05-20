# -*- coding: utf-8 -*-
"""단일 오케스트레이션 — CLI·FastAPI 공통. 검증 게이트 일원화.

흐름: P1 보정 → P2 계산(명리+자미+교차) → P3 콘텐츠+가드 → P4 렌더+게이트.
하드 게이트(실패 시 ok=False): 렌더 게이트 + 콘텐츠 clean + 명리↔자미 사주팔자 일치
+ 월지 교차 일치. (시지 자시충돌은 학설 차이 → 경고만, 실패 아님)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# .env 자동 로드 (운영자 도구: ANTHROPIC_API_KEY 등). CLI/FastAPI 공통 진입점.
# dotenv 미설치/파일 없음/실패 시 무영향 — 키 없으면 llm_polish 가 룰 폴백(무비용).
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    pass

from .calc import engine
from .content import builder
from .input import time_correction as tc
from .render import pdf as render_pdf
from .render import verify as render_verify


@dataclass
class GenResult:
    pdf_path: str
    ok: bool
    reasons: list[str]
    verify: dict
    guard: dict
    crosscheck_warnings: list[str] = field(default_factory=list)
    bazi: str = ""


def generate(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    *,
    is_male: bool,
    longitude: float = tc.SEOUL_LON,
    latitude: float = tc.SEOUL_LAT,
    policy: tc.ZasiPolicy = tc.ZasiPolicy.JST_2300,
    horoscope_date: str | None = None,
    use_llm: bool = False,
    out_name: str = "saju_report.pdf",
    name: str | None = None,
    unknown_time: bool = False,
    product: str = "integrated",
) -> GenResult:
    saju = engine.build(
        year,
        month,
        day,
        hour,
        minute,
        is_male=is_male,
        longitude=longitude,
        latitude=latitude,
        policy=policy,
        horoscope_date=horoscope_date,
    )
    # horoscope_date 연도 → 미성년 등 개인화 분기 기준(단순 산술, 새 계산 아님)
    ref_year = None
    if horoscope_date:
        try:
            ref_year = int(str(horoscope_date)[:4])
        except Exception:
            ref_year = None
    age = None
    if ref_year:
        try:
            age = ref_year - int(str(saju.input_civil)[:4])
        except Exception:
            age = None
    report = builder.build_report(
        saju,
        use_llm=use_llm,
        ref_year=ref_year,
        name=name,
        unknown_time=unknown_time,
        product=product,
    )
    pdf_path = render_pdf.render_pdf(
        report, saju, out_name, age=age, name=name, unknown_time=unknown_time
    )
    v = render_verify.verify(pdf_path)

    reasons: list[str] = []
    if not v["gate_pass"]:
        reasons.append(
            f"렌더 게이트 실패(text={v['text_chars']}, tagged={v['tagged']}, "
            f"fonts={v['fonts_embedded']})"
        )
    if not report.guard.clean:
        reasons.append(
            f"콘텐츠 가드 미통과(§12={report.guard.safe_lint_total}, "
            f"사실={report.guard.factcheck_total}, "
            f"grounding={report.guard.grounding_ok})"
        )
    if not saju.crosscheck.bazi_consistent:
        reasons.append("명리↔자미 사주팔자 불일치")
    if not saju.crosscheck.month_branch_ok:
        reasons.append("월지 lunar↔Skyfield 불일치")

    return GenResult(
        pdf_path=pdf_path,
        ok=not reasons,
        reasons=reasons,
        verify=v,
        guard=report.guard.model_dump(),
        crosscheck_warnings=saju.crosscheck.warnings,
        bazi=saju.crosscheck.bazi_myeongni,
    )
