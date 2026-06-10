# -*- coding: utf-8 -*-
"""Phase 2 입력 정규화 검증 — 음력/윤달 → 양력(KASI 1차 기준) + 엔진 E2E.

KASI 경로는 픽스처(tests/fixtures/kasi_sample.json)로 결정론 검증.
윤달·한·중 상이일은 실 캐시(data/kasi_cache.sqlite) 있을 때만(없으면 스킵).
"""

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine, kasi  # noqa: E402
from sajugen.input import normalize as norm  # noqa: E402

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "kasi_sample.json"


@pytest.fixture(scope="module")
def cache(tmp_path_factory) -> kasi.KasiCache:
    fx = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    db = tmp_path_factory.mktemp("kasi_norm") / "cache.sqlite"
    conn = sqlite3.connect(db)
    kasi.init_db(conn)
    kasi.upsert_lunar_rows(conn, fx["lunar"])
    conn.close()
    return kasi.KasiCache(db)


def test_solar_passthrough(cache):
    nd = norm.normalize_date(1990, 5, 20, is_lunar=False, cache=cache)
    assert (nd.year, nd.month, nd.day) == (1990, 5, 20)
    assert nd.source == "solar" and nd.input_kind == "solar"
    assert nd.warnings == []


def test_lunar_to_solar_via_kasi(cache):
    # 픽스처 실값: 양력 1990-05-20 = 음력 4월 26일(평달) → 역변환 일치, 출처 KASI
    nd = norm.normalize_date(1990, 4, 26, is_lunar=True, is_leap=False, cache=cache)
    assert (nd.year, nd.month, nd.day) == (1990, 5, 20)
    assert nd.source == "kasi" and nd.input_kind == "lunar"


def test_lunar_nonexistent_raises(cache):
    # 음력 1990-04-31 은 존재하지 않음(KASI 미스 → 폴백도 실패) → ValueError
    with pytest.raises(ValueError):
        norm.normalize_date(1990, 4, 31, is_lunar=True, cache=cache)


def test_fallback_to_lunar_python_when_cache_missing(tmp_path):
    # 캐시 부재 → lunar-python(중국 기준) 폴백 + 경고
    empty = kasi.KasiCache(tmp_path / "nope.sqlite")
    nd = norm.normalize_date(1990, 4, 26, is_lunar=True, cache=empty)
    assert nd.source == "lunar_python_cn"
    assert nd.warnings and "폴백" in nd.warnings[0]
    assert (nd.year, nd.month) == (1990, 5)  # 중국기준도 1990-05 근방


def test_e2e_lunar_input_drives_engine(cache):
    # E2E: 음력 1990-4-26 → 양력 1990-05-20 정규화 → 엔진 일주 = 乙酉(KASI 일진과 일치)
    nd = norm.normalize_date(1990, 4, 26, is_lunar=True, cache=cache)
    r = engine.build(nd.year, nd.month, nd.day, 14, 30, is_male=True)
    assert r.myeongni.day.ganzhi == "乙酉", r.myeongni.day.ganzhi


# ─────────── 실 캐시 전용(윤달·한·중 상이일) ───────────


def _real_cache():
    c = kasi.KasiCache()
    return c if c.exists else None


def test_leap_month_via_real_cache():
    # 윤달 입력: 2012 윤3월 1일 → 양력 2012-04-21 (KASI 한국 기준). 캐시 없으면 스킵.
    c = _real_cache()
    if c is None:
        pytest.skip("실 캐시 미구축")
    nd = norm.normalize_date(2012, 3, 1, is_lunar=True, is_leap=True, cache=c)
    assert (nd.year, nd.month, nd.day) == (2012, 4, 21), nd
    assert nd.source == "kasi"


def test_kr_cn_divergence_warning_via_real_cache():
    # 2012 윤3월은 한·중 상이(중국=윤4월) → KASI 채택 + 경고 surface. 캐시 없으면 스킵.
    c = _real_cache()
    if c is None:
        pytest.skip("실 캐시 미구축")
    nd = norm.normalize_date(2012, 3, 1, is_lunar=True, is_leap=True, cache=c)
    assert nd.source == "kasi"
    assert any("한·중 음력 상이일" in w for w in nd.warnings), nd.warnings
