# -*- coding: utf-8 -*-
"""KASI(공공데이터포털) 음양력·절기 전수 캐시 빌더 → data/kasi_cache.sqlite.

절대규칙 4: 런타임은 이 캐시만 읽는다(calc/kasi.py). 이 스크립트만 네트워크를 친다.
실측(2026-06-10): 음양력은 월 일괄(solDay 생략·numOfRows=31)로 1900~2050 전 구간,
절기는 연 일괄(solMonth 생략)로 2000~2027만 제공. 합계 약 1,840콜 → 수 분 내 1회 구축.

재개 가능: 이미 적재된 월/연은 스킵하므로 중단 후 재실행하면 이어서 받는다.
실행:
  ./.venv/Scripts/python.exe -m scripts.kasi_dump                # 전체(1900~2050 음양력 + 2000~2027 절기)
  ./.venv/Scripts/python.exe -m scripts.kasi_dump --terms-only   # 절기만
  ./.venv/Scripts/python.exe -m scripts.kasi_dump --start-year 1990 --end-year 1990
"""

from __future__ import annotations

import argparse
import calendar
import os
import sqlite3
import sys
import time
from pathlib import Path

import httpx

# 패키지 임포트 보장
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True), override=False)
except Exception:
    pass

from sajugen.calc import kasi  # noqa: E402

_BASE = "http://apis.data.go.kr/B090041/openapi/service"
_LUNAR_URL = f"{_BASE}/LrsrCldInfoService/getLunCalInfo"
_TERM_URL = f"{_BASE}/SpcdeInfoService/get24DivisionsInfo"

# 음양력 가용 범위(실측). 절기는 정부가 매년 ~2년 앞까지만 갱신 → 상한은 프로브로 확정.
LUNAR_START, LUNAR_END = 1900, 2050
TERM_START, TERM_END = 2000, 2027

_DELAY = 0.15  # 초당 호출 제한 여유


def _items(payload: dict) -> list[dict]:
    """KASI JSON 응답에서 item 리스트 추출(0건/단건/다건 모두 처리)."""
    body = payload.get("response", {}).get("body", {})
    items = (body or {}).get("items")
    if not items:
        return []
    it = items.get("item")
    if it is None:
        return []
    return it if isinstance(it, list) else [it]


def _result_code(payload: dict) -> str:
    return payload.get("response", {}).get("header", {}).get("resultCode", "")


def _fetch(client: httpx.Client, url: str, params: dict, key: str) -> dict:
    p = dict(params)
    p["ServiceKey"] = key
    p["_type"] = "json"
    r = client.get(url, params=p, timeout=30.0)
    r.raise_for_status()
    try:
        return r.json()
    except Exception as e:  # XML 에러 응답(키 미등록 등)
        raise RuntimeError(f"비JSON 응답: {r.text[:300]}") from e


def _check_key_ok(payload: dict) -> None:
    code = _result_code(payload)
    if code in ("30", "31"):  # 키 미등록/만료
        raise SystemExit(
            "KASI 키 오류(resultCode=%s). 발급 직후면 게이트웨이 동기화에 최대 1시간 — 잠시 후 재시도."
            % code
        )


def _lunar_month_done(conn: sqlite3.Connection, year: int, month: int) -> bool:
    lo = year * 10000 + month * 100 + 1
    hi = year * 10000 + month * 100 + 31
    n = conn.execute(
        "SELECT COUNT(*) FROM lunar WHERE sol_ymd BETWEEN ? AND ?", (lo, hi)
    ).fetchone()[0]
    return n >= calendar.monthrange(year, month)[1]


def _term_year_done(conn: sqlite3.Connection, year: int) -> bool:
    n = conn.execute("SELECT COUNT(*) FROM solarterm WHERE year=?", (year,)).fetchone()[0]
    return n >= 24


def dump_lunar(client, conn, key, y0, y1) -> int:
    total = 0
    for y in range(y0, y1 + 1):
        for m in range(1, 13):
            if _lunar_month_done(conn, y, m):
                continue
            payload = _fetch(
                client, _LUNAR_URL, {"solYear": y, "solMonth": f"{m:02d}", "numOfRows": 31}, key
            )
            _check_key_ok(payload)
            rows = _items(payload)
            if not rows:
                print(f"  [경고] 음양력 {y}-{m:02d} 0건(범위 밖?)", flush=True)
                continue
            n = kasi.upsert_lunar_rows(conn, rows)
            total += n
            time.sleep(_DELAY)
        print(f"  음양력 {y} 완료 (누적 {total}일)", flush=True)
    return total


def dump_terms(client, conn, key, y0, y1) -> int:
    total = 0
    for y in range(y0, y1 + 1):
        if _term_year_done(conn, y):
            continue
        payload = _fetch(client, _TERM_URL, {"solYear": y, "numOfRows": 30}, key)
        _check_key_ok(payload)
        rows = _items(payload)
        if not rows:
            print(f"  [정보] 절기 {y} 0건 — KASI 미수록 연도(스킵)", flush=True)
            continue
        if len(rows) != 24:
            print(f"  [경고] 절기 {y} {len(rows)}건(24 아님) — 그대로 정규화 적재", flush=True)
        n = kasi.upsert_solarterm_rows(conn, y, rows)
        total += n
        time.sleep(_DELAY)
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description="KASI 음양력·절기 캐시 빌더")
    ap.add_argument("--cache", default=str(kasi.DEFAULT_CACHE))
    ap.add_argument("--start-year", type=int, default=LUNAR_START)
    ap.add_argument("--end-year", type=int, default=LUNAR_END)
    ap.add_argument("--term-start", type=int, default=TERM_START)
    ap.add_argument("--term-end", type=int, default=TERM_END)
    ap.add_argument("--lunar-only", action="store_true")
    ap.add_argument("--terms-only", action="store_true")
    args = ap.parse_args()

    key = os.environ.get("KASI_API_KEY", "").strip()
    if not key:
        raise SystemExit("KASI_API_KEY 미설정 — .env 확인")

    cache_path = Path(args.cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(cache_path)
    kasi.init_db(conn)

    with httpx.Client(http2=False) as client:
        if not args.terms_only:
            print(f"[음양력] {args.start_year}~{args.end_year} 적재 시작", flush=True)
            n = dump_lunar(client, conn, key, args.start_year, args.end_year)
            print(f"[음양력] 적재 {n}일", flush=True)
        if not args.lunar_only:
            print(f"[절기] {args.term_start}~{args.term_end} 적재 시작", flush=True)
            n = dump_terms(client, conn, key, args.term_start, args.term_end)
            print(f"[절기] 적재 {n}건", flush=True)

    kasi.set_meta(conn, "lunar_range", f"{args.start_year}-{args.end_year}")
    kasi.set_meta(conn, "term_range_attempted", f"{args.term_start}-{args.term_end}")
    rng = conn.execute("SELECT MIN(year), MAX(year) FROM solarterm").fetchone()
    if rng and rng[0] is not None:
        kasi.set_meta(conn, "term_range_actual", f"{rng[0]}-{rng[1]}")
    lc = conn.execute("SELECT COUNT(*) FROM lunar").fetchone()[0]
    tc = conn.execute("SELECT COUNT(*) FROM solarterm").fetchone()[0]
    print(f"[완료] lunar {lc}일 / solarterm {tc}건 → {cache_path}", flush=True)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
