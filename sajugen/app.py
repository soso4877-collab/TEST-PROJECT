# -*- coding: utf-8 -*-
"""운영자 로컬 폼(FastAPI) — 입력 → 사주풀이 PDF 다운로드. 로컬 전용·무인증(내부 도구).

실행: uvicorn sajugen.app:app --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

from urllib.parse import quote

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from . import admin
from .input import normalize as norm
from .input import time_correction as tc
from .pipeline import generate

app = FastAPI(title="사주풀이 PDF 생성기 (내부 도구)")
app.include_router(admin.router)  # 검수 화면(/admin) — 주문 접수·검수·승인·발급

_FORM = """<!doctype html><meta charset="utf-8"><title>사주풀이 생성기</title>
<body style="font-family:Malgun Gothic,sans-serif;max-width:520px;margin:40px auto">
<h2>사주풀이 PDF 생성 (운영자)</h2>
<p><a href="/admin">주문 검수 화면(접수·검수·승인·발급)으로 이동</a></p>
<p style="font-size:13px;color:#555">아래 폼은 주문 기록 없이 즉시 PDF 만 받는 구형 경로입니다.
실주문은 검수 화면에서 접수하세요.</p>
<form method="post" action="/generate">
 <p>생년월일시(시민시각): <input name="birth" placeholder="2000-01-01 12:00 (생시 미상이면 날짜만)" required></p>
 <p><label><input type="checkbox" name="lunar"> 음력 입력</label>
   &nbsp;<label><input type="checkbox" name="leap"> 윤달(음력 체크 시)</label></p>
 <p>이름(필수, 호명 개인화): <input name="name" placeholder="홍길동" required></p>
 <p>성별: <select name="gender"><option value="male">남</option>
   <option value="female">여</option></select></p>
 <p>상품: <select name="product"><option value="integrated">통합(명리+자미)</option>
   <option value="myeongni">명리만</option><option value="ziwei">자미만</option></select></p>
 <p>브랜드: <input name="brand" value="seodam" placeholder="seodam·default 또는 원하는 문구"></p>
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
    product: str = Form("integrated"),
    concern: str = Form(""),
    brand: str = Form("default"),
):
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
        out_name=f"saju_{y}{mo:02d}{da:02d}_{hh:02d}{mi:02d}.pdf",
        name=name or None,
        unknown_time=unknown_time,
        product=product,
        concern=concern or None,
        brand=brand or None,
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
    headers = {
        "X-Saju-Bazi": quote(r.bazi),
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
