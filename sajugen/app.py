# -*- coding: utf-8 -*-
"""운영자 로컬 폼(FastAPI) — 입력 → 사주풀이 PDF 다운로드. 로컬 전용·무인증(내부 도구).

실행: uvicorn sajugen.app:app --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import os
import uuid
from urllib.parse import quote

from fastapi import BackgroundTasks, FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from . import admin, integrated, order_flow
from .input import normalize as norm
from .input import time_correction as tc
from .pipeline import generate

app = FastAPI(title="사주풀이 PDF 생성기 (내부 도구)")
app.include_router(admin.router)  # 검수 화면(/admin) — 주문 접수·검수·승인·발급

_FORM = """<!doctype html><meta charset="utf-8"><title>사주풀이 생성기</title>
<body style="font-family:Malgun Gothic,sans-serif;max-width:520px;margin:40px auto">
<h2>사주풀이 PDF 생성 (운영자)</h2>
<p><a href="/admin">주문 검수 화면(접수·검수·승인·발급)으로 이동</a></p>
<p style="font-size:13px;color:#555">기존 상품은 주문 기록 없이 즉시 PDF를 받는 구형 경로입니다.
통합 전체(모듈형)는 모듈 확정을 위해 주문으로 접수됩니다.</p>
<form method="post" action="/generate">
 <p>생년월일시(시민시각): <input name="birth" placeholder="2000-01-01 12:00 (생시 미상이면 날짜만)" required></p>
 <p><label><input type="checkbox" name="lunar"> 음력 입력</label>
   &nbsp;<label><input type="checkbox" name="leap"> 윤달(음력 체크 시)</label></p>
 <p>이름(필수, 호명 개인화): <input name="name" placeholder="홍길동" required></p>
 <p>성별: <select name="gender"><option value="male">남</option>
   <option value="female">여</option></select></p>
 <fieldset style="margin:16px 0;padding:10px">
  <legend>상대 정보(통합 전체·궁합 모듈 선택 시에만 입력)</legend>
  <p>상대 이름: <input name="partner_name" placeholder="합성 상대"></p>
  <p>상대 생년월일시: <input name="partner_birth" placeholder="2001-02-02 13:30"></p>
  <p><label><input type="checkbox" name="partner_lunar"> 상대 음력 입력</label>
    &nbsp;<label><input type="checkbox" name="partner_leap"> 상대 윤달(음력 체크 시)</label></p>
  <p>상대 성별: <select name="partner_gender"><option value="male">남</option>
    <option value="female">여</option></select></p>
 </fieldset>
 <p>상품: <select name="product"><option value="integrated">통합(명리+자미)</option>
   <option value="integrated_full">통합 전체(모듈형)</option>
   <option value="myeongni">명리만</option><option value="ziwei">자미만</option></select></p>
 <p>브랜드: <input name="brand" value="sajudoryeong" placeholder="sajudoryeong·seodam·default 또는 원하는 문구"></p>
 <p>경도: <input name="longitude" value="126.978"> 위도: <input name="latitude" value="37.566"></p>
 <p><label><input type="checkbox" name="yajasi"> 야자시/조자시 분리</label></p>
 <p>대한·유년 기준일: <input name="horoscope" placeholder="2026-06-01"></p>
 <p>고민/질문(선택): <input name="concern" placeholder="예: 올해 이직해도 될까요"></p>
 <p><label><input type="checkbox" name="llm"> LLM 윤문(무키 시 룰 폴백)</label></p>
 <button type="submit">PDF 생성</button>
</form></body>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _FORM


@app.post("/generate")
def gen(
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
    name: str = Form(...),  # 필수 — 호명 개인화(운영자 지시 2026-06-12)
    partner_name: str = Form(""),
    partner_birth: str = Form(""),
    partner_lunar: bool = Form(False),
    partner_leap: bool = Form(False),
    partner_gender: str = Form("male"),
    product: str = Form("integrated"),
    concern: str = Form(""),
    brand: str = Form("sajudoryeong"),
):
    # 상대 birth가 입력된 주문만 2인 주문이다. 기존 즉시 생성 상품에는 상대 소비처가
    # 없으므로 조용히 무시하지 않고 주문·PDF 생성 전에 차단한다.
    if partner_birth.strip() and product != integrated.PRODUCT:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "reasons": ["partner input is only supported for integrated_full"],
            },
        )
    if product == integrated.PRODUCT:
        # 구형 즉시 PDF 폼에서도 integrated_full만큼은 모듈 확정이 필요한 주문 상품이다.
        # pipeline.generate로 강등하지 않고 주문을 만든 뒤, 공용 생성 진입점이 빈 모듈
        # 상태를 fail-closed로 막게 한다. 기존 세 상품의 즉시 PDF 동작은 아래에서 유지한다.
        db_path = os.environ.get("SAJUGEN_ORDERS_DB", order_flow.DEFAULT_DB)
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
                partner_name=partner_name,
                partner_birth=partner_birth,
                partner_lunar=partner_lunar,
                partner_leap=partner_leap,
                partner_gender=partner_gender,
                product=product,
                concern=concern,
                brand=brand,
                db_path=db_path,
            )
        except ValueError as exc:
            return JSONResponse(
                status_code=422,
                content={"ok": False, "reasons": [str(exc)]},
            )
        background.add_task(order_flow.run_generation, order_id, db_path=db_path)
        return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)

    parts = birth.split()
    iy, imo, ida = (int(x) for x in parts[0].split("-"))
    unknown_time = len(parts) < 2
    hh, mi = (12, 0) if unknown_time else (int(x) for x in parts[1].split(":"))

    # 음력/윤달 입력은 KASI 1차 기준으로 양력 정규화
    try:
        nd = norm.normalize_date(iy, imo, ida, is_lunar=lunar, is_leap=leap)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"ok": False, "reasons": [str(e)]})
    y, mo, da = nd.year, nd.month, nd.day
    norm_warnings = nd.warnings if nd.input_kind == "lunar" else []

    is_male = gender.strip().lower() in ("male", "m", "남", "남자")
    policy = tc.ZasiPolicy.YAJASI_SPLIT if yajasi else tc.ZasiPolicy.JST_2300
    brand_name = brand.strip()
    if not brand_name:
        return JSONResponse(
            status_code=422, content={"ok": False, "reasons": ["brand is required"]}
        )

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
        horoscope_date=horoscope or None,
        use_llm=llm,
        # 파일명에 생년월일 비노출(T4.5/E-1) — 다운로드 파일명·디스크명 PII 제거.
        out_name=f"saju_{uuid.uuid4().hex[:12]}.pdf",
        name=name or None,
        unknown_time=unknown_time,
        product=product,
        concern=concern or None,
        brand=brand_name,
    )

    if not r.ok:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "reasons": r.reasons,
                "warnings": norm_warnings + r.crosscheck_warnings,
            },
        )
    # X-Saju-Bazi(사주팔자) 헤더 제거(T4.5/E-1) — 응답 헤더로 파생 PII 노출 차단.
    headers = {
        "X-Gate": "PASS",
        "X-Pages": str(r.verify["pages"]),
    }
    if norm_warnings:
        headers["X-Input-Normalize"] = quote(" / ".join(norm_warnings))
    return FileResponse(
        r.pdf_path,
        media_type="application/pdf",
        filename=r.pdf_path.split("\\")[-1].split("/")[-1],
        headers=headers,
    )
