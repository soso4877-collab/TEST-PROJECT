# -*- coding: utf-8 -*-
"""Phase 1 KASI 검증층: 캐시 빌더·리더·3원 교차검증.

네트워크 비의존 — tests/fixtures/kasi_sample.json(2026-06-10 실데이터 캡처)으로
임시 sqlite 캐시를 만들어 결정론 검증한다(절대규칙 4: 런타임 실시간 API 금지).
"""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import kasi  # noqa: E402

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "kasi_sample.json"


@pytest.fixture(scope="module")
def cache(tmp_path_factory) -> kasi.KasiCache:
    """픽스처 실데이터로 임시 캐시 sqlite 구축 후 읽기전용 리더 반환."""
    fx = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    db = tmp_path_factory.mktemp("kasi") / "cache.sqlite"
    conn = sqlite3.connect(db)
    kasi.init_db(conn)
    kasi.upsert_lunar_rows(conn, fx["lunar"])
    for y, rows in fx["solarterm"].items():
        kasi.upsert_solarterm_rows(conn, int(y), rows)
    conn.close()
    return kasi.KasiCache(db)


# ─────────────────────────── 음양력(일별 간지·윤달) ───────────────────────────


def test_lunar_lookup_1990_05_20(cache):
    # 양력 1990-05-20 → 음력 4월 26일, 일진 을유(乙酉), 평달 (KASI 실값)
    r = cache.lunar_of(1990, 5, 20)
    assert r is not None
    assert (r["lun_year"], r["lun_month"], r["lun_day"]) == (1990, 4, 26)
    assert r["leap"] == 0
    assert r["iljin"].startswith("을유")


def test_lunar_iljin_matches_myeongni_golden(cache):
    # 골든 2000-01-01 명리 일주 = 戊午. KASI 일진도 무오(戊午)여야 함(체계 독립 교차).
    r = cache.lunar_of(2000, 1, 1)
    assert r is not None
    assert r["iljin"].startswith("무오"), r["iljin"]


def test_lunar_missing_returns_none(cache):
    # 캐시에 없는 날짜(픽스처 범위 밖)는 None
    assert cache.lunar_of(2030, 6, 15) is None


# ─────────────────────────── 절기 정규화(결함 우회) ───────────────────────────


def test_solarterm_defect_normalized_to_usu(cache):
    # KASI 2000-02 우수 행 dateName='입춘' 오기 → Skyfield 최근접 매칭으로 雨水로 정규화.
    terms = cache.solar_terms_kst(2000)
    assert "雨水" in terms and "立春" in terms
    # 24절기 전부 고유 키로 적재(중복 라벨로 인한 누락 없음)
    assert len(terms) == 24


# ─────────────────────────── 3원 교차검증 ───────────────────────────


def test_crosscheck3_year_2000(cache):
    res = kasi.crosscheck3_year(2000, cache=cache)
    assert res["kasi_available"] is True
    assert res["mode"].startswith("3원")
    assert res["all_ok"], res["max_diff_min"]  # lunar↔Skyfield
    assert res["all_kasi_ok"], res["max_kasi_diff_min"]  # Skyfield↔KASI
    assert res["max_kasi_diff_min"] <= 2.0, res["max_kasi_diff_min"]


def test_crosscheck3_year_2026(cache):
    res = kasi.crosscheck3_year(2026, cache=cache)
    assert res["kasi_available"] is True
    assert res["all_kasi_ok"], res["max_kasi_diff_min"]
    assert res["max_kasi_diff_min"] <= 2.0, res["max_kasi_diff_min"]


def test_crosscheck3_year_2011_known_defects(cache):
    # 2011은 KASI 원본 결함 2건(大寒 1일·立冬 6h). 계산엔진 2원은 일치(≤0.03분).
    # 기지 결함으로 분류되어 all_kasi_ok는 True 유지(차단 대상 아님), 결함은 목록에 surface.
    res = kasi.crosscheck3_year(2011, cache=cache)
    assert res["kasi_available"] is True
    assert res["all_ok"], res["max_diff_min"]  # lunar↔Skyfield 정상
    assert res["all_kasi_ok"], res["kasi_unknown_mismatches"]  # 기지 결함뿐 → 통과
    assert res["kasi_unknown_mismatches"] == []
    terms_flagged = " ".join(res["kasi_known_defects"])
    assert "大寒" in terms_flagged and "立冬" in terms_flagged


def test_full_cache_defect_inventory():
    # 실 캐시(data/kasi_cache.sqlite)가 있으면 2000~2027 전수 스캔으로 KASI 결함이
    # 문서화된 3건과 정확히 일치하는지 회귀 고정. 캐시 없으면 스킵(타 환경/CI).
    real = kasi.KasiCache()
    if not real.exists or (real.solar_term_years() or (0, 0))[1] < 2027:
        pytest.skip("실 캐시 미구축 — scripts.kasi_dump 실행 후 검증")
    found = set()
    for y in range(2000, 2028):
        res = kasi.crosscheck3_year(y, cache=real)
        assert res["all_ok"], (y, res["max_diff_min"])  # 2원은 전 구간 정상
        for r in res["rows"]:
            if r.get("kasi_defect_known") or (r.get("kasi_ok") is False):
                found.add((y, r["term"]))
    assert found == set(kasi.KNOWN_KASI_TERM_DEFECTS.keys()), found


def test_lunar_iljin_full_continuity_sampled():
    # 실 캐시가 있으면 1900~2050 전 구간을 표본(매 137일)으로 일진(干支) 무결성 회귀:
    # (1) KASI 일진 == lunar-python 일진(달력 무관 연속값 → 100% 일치 필수),
    # (2) 인접 표본은 (간격 % 60)만큼 60갑자 전진. 캐시 없으면 스킵.
    from lunar_python import Solar

    real = kasi.KasiCache()
    if not real.exists:
        pytest.skip("실 캐시 미구축 — scripts.kasi_dump 실행 후 검증")
    gan, zhi = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
    jiazi = {gan[i % 10] + zhi[i % 12]: i for i in range(60)}
    conn = real._c()
    rows = conn.execute(
        "SELECT sol_ymd, iljin FROM lunar WHERE (sol_ymd*131+7)%137=0 ORDER BY sol_ymd"
    ).fetchall()
    assert len(rows) > 300, len(rows)
    from datetime import date as _date

    prev = None
    for r in rows:
        ymd = r["sol_ymd"]
        y, m, d = ymd // 10000, (ymd // 100) % 100, ymd % 100
        ilj = r["iljin"][r["iljin"].index("(") + 1 : r["iljin"].index(")")]
        lp = Solar.fromYmd(y, m, d).getLunar().getDayInGanZhi()
        assert ilj == lp, (ymd, ilj, lp)  # KASI 일진 == lunar-python
        cur = (_date(y, m, d), jiazi[ilj])
        if prev is not None:
            gap = (cur[0] - prev[0]).days
            assert (prev[1] + gap) % 60 == cur[1], (ymd, gap)  # 60갑자 연속성
        prev = cur


def test_kr_cn_divergence_2012_kasi_authoritative():
    # 한·중 음력 차이 대표사례: 2012-04-21 → KASI=한국 윤3월 1일, lunar-python=중국 4월 1일.
    # 일진은 동일(壬子)해야 함(날짜 무결성). 정책상 KASI(한국 공식) 채택. 캐시 없으면 스킵.
    from lunar_python import Solar

    real = kasi.KasiCache()
    if not real.exists:
        pytest.skip("실 캐시 미구축")
    r = real.lunar_of(2012, 4, 21)
    assert r is not None
    assert (r["lun_month"], r["lun_day"], r["leap"]) == (3, 1, 1), r  # KASI 윤3월 1일
    lp = Solar.fromYmd(2012, 4, 21).getLunar()
    assert (abs(lp.getMonth()), lp.getDay(), 1 if lp.getMonth() < 0 else 0) == (
        4,
        1,
        0,
    )  # 중국 4월 1일
    assert r["iljin"].endswith("(壬子)") and lp.getDayInGanZhi() == "壬子"  # 일진 동일


def test_crosscheck3_falls_back_when_year_absent(cache):
    # 절기 미수록 연도(1990)는 KASI 비활성 → 기존 2원 결과 유지(폴백)
    res = kasi.crosscheck3_year(1990, cache=cache)
    assert res["kasi_available"] is False
    assert res["mode"].startswith("2원")
    assert res["all_ok"]  # 2원 자체는 정상


def test_crosscheck3_falls_back_when_cache_missing(tmp_path):
    # 캐시 파일 부재 시에도 안전하게 2원으로 동작
    empty = kasi.KasiCache(tmp_path / "nope.sqlite")
    res = kasi.crosscheck3_year(2026, cache=empty)
    assert res["kasi_available"] is False
    assert res["all_ok"]
