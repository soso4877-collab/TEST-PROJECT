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
from .content import delivery_quality as _delivery_quality
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
    # 검수 UI 연결(2026-06-13, additive — CLI 경로 영향 없음)
    report: object | None = None  # Report23 (섹션 본문·가드·허용 토큰)
    calc_consistent: bool = True  # 명리↔자미·월지 교차 일치(절대규칙 7 — False 면 주문 차단)
    input_civil: str = ""  # 표지용 시민시각 문자열(최종 재렌더에 필요)
    near_term_boundary: bool = False  # 절입 ±2분 knife-edge — needs_review 유발(차단 아님, T2.2)


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
    concern: str | None = None,
    brand: str | None = None,
    is_leap: bool = False,
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
    # 브랜드 프로필(다계정, config/brands.yaml) — 표지·낙관·맺음 서명 가변
    from . import config as cfg

    bp = cfg.brand(brand)
    report = builder.build_report(
        saju,
        use_llm=use_llm,
        ref_year=ref_year,
        name=name,
        unknown_time=unknown_time,
        product=product,
        concern=concern,
        closing_sign=bp.get("closing_sign"),
        is_leap=is_leap,
        # 월 단위 시제 닻(QI-2026-07-04-02): compose·temporal 가드에 기준 일자 전달.
        ref_date=horoscope_date,
    )
    # 개인 일간 role 게이트(H1.5.3) — 결정론 일간만 정답. 이름 정책은 개인 미적용(단일 호명).
    _id_spec = builder.personal_identity_spec(saju, name)

    # 저밀도 단독 실패 시 무과금 재렌더 재시도(2026-07-04 — integrated 검증 패턴 이식).
    # compose 는 이미 끝난 상태라 레이아웃 변형(폰트 14.5→13.8pt)은 API 0. 저밀도 '단독'
    # 실패일 때만 발동하고(다른 게이트 실패 = 즉시 반환), 하한 13.8pt 도 실패하면 그대로
    # FAIL 보고(열화 발급 금지·게이트 완화 0). 개인 경로엔 이 재시도가 없어 저밀도 1건에도
    # 재compose 과금이 강제되던 갭(QI-2026-07-04 후속 실측: 재시도 2회 $1 소모)의 근본 차단.
    from . import integrated as _integrated

    pdf_path = ""
    v: dict = {}
    for _fs, _lh in _integrated._LAYOUT_VARIANTS:
        pdf_path = render_pdf.render_pdf(
            report,
            saju,
            out_name,
            age=age,
            name=name,
            unknown_time=unknown_time,
            brand=bp,
            body_font_size=_fs,
            body_line_height=_lh,
        )
        v = render_verify.verify(
            pdf_path,
            ref_year=ref_year,
            names=[name] if name else None,
            identity=_id_spec,
            product=product,
            concern=concern,
            ref_date=horoscope_date,
            # QI-2026-07-04: 1인 문서(파트너 부재)면 커플 지칭 candidate 를 hard 승격.
            partner_present=getattr(report, "partner_present", None),
        )
        if v.get("gate_pass") or not _integrated._integrated_only_low_density_failure(v):
            break

    reasons: list[str] = []
    if not v["gate_pass"]:
        reasons.append(
            f"렌더 게이트 실패(text={v['text_chars']}, tagged={v['tagged']}, "
            f"fonts={v['fonts_embedded']})"
        )
    # P2(QI-2026-07-05-03): consult 직답성 하드 게이트 — 질문 답변 챕터가 얇은 유보
    # 골격으로 붕괴한 채 발급되는 것을 차단(v7 false-PASS 실사고). concern 없으면 skipped.
    _cd = _delivery_quality.consult_direct_result(report.section("consult").final_text, concern)
    if not _cd.get("ok", True):
        reasons.append("consult 직답 미달(" + ",".join(_cd.get("missing", [])) + ")")
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
    if not saju.crosscheck.year_branch_ok:
        reasons.append("연지 lunar↔Skyfield 불일치(입춘 경계)")
    if not saju.crosscheck.kasi_consistent:
        reasons.append("KASI 3원 교차 미지 불일치(절입 시각)")

    return GenResult(
        pdf_path=pdf_path,
        ok=not reasons,
        reasons=reasons,
        verify=v,
        guard=report.guard.model_dump(),
        crosscheck_warnings=saju.crosscheck.warnings,
        bazi=saju.crosscheck.bazi_myeongni,
        report=report,
        calc_consistent=(
            saju.crosscheck.bazi_consistent
            and saju.crosscheck.month_branch_ok
            and saju.crosscheck.year_branch_ok
            and saju.crosscheck.kasi_consistent
        ),
        input_civil=str(saju.input_civil),
        near_term_boundary=saju.crosscheck.near_term_boundary,
    )
