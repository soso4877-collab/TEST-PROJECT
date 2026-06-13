# -*- coding: utf-8 -*-
"""Phase 9 — 익명 계산특이점 추출 검증.

최중요: 추출 레코드에 PII(이름·출생지·고민 원문)가 일절 없어야 한다(화이트리스트 증명).
부가: 계산 사실·경계 라벨 보존, 경계 판정, JSONL append round-trip.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import insight  # noqa: E402
from sajugen.models.report import (  # noqa: E402
    BirthInput,
    Birthplace,
    CalendarVerification,
    SafetyFlags,
    UnifiedReport,
)

# 식별 가능한 고유 PII 문자열(추출물에서 부재를 확인할 대상)
PII_NAME = "홍길동특이름"
PII_CONCERN = "이혼소송중인고민원문"
PII_PLACE = "대구수성구특이지명"


def _order(
    *,
    oid="ord_test",
    crosscheck_warnings=None,
    normalize_warnings=None,
    needs_review=False,
    hour=10,
    ziwei=None,
    bazi="己卯 丙子 戊午 戊午",
) -> UnifiedReport:
    """생성 완료 형태의 주문(render_meta 포함). PII를 birth·gen_params 양쪽에 심어 둔다."""
    return UnifiedReport(
        order_id=oid,
        birth=BirthInput(
            name=PII_NAME,
            gender="M",
            input_calendar="solar",
            input_date="2000-01-01",
            birth_time=f"{hour:02d}:00",
            birthplace=Birthplace(label=PII_PLACE),
            concern_text=PII_CONCERN,
        ),
        calendar_verification=CalendarVerification(solar_date="2000-01-01"),
        ziwei=ziwei,
        safety_flags=SafetyFlags(needs_review=needs_review),
        render_meta={
            "bazi": bazi,
            "crosscheck_warnings": list(crosscheck_warnings or []),
            "normalize_warnings": list(normalize_warnings or []),
            "gen_params": {
                "year": 2000,
                "month": 1,
                "day": 1,
                "hour": hour,
                "minute": 0,
                "is_male": True,
                "unknown_time": False,
                "name": PII_NAME,  # gen_params 에도 PII 가 있음 — 추출 시 제외돼야
                "concern": PII_CONCERN,
            },
        },
    )


def test_extract_has_no_pii():
    rec = insight.extract_insight(_order(), engine_version="test")
    blob = json.dumps(rec, ensure_ascii=False)
    assert PII_NAME not in blob, "이름 누출"
    assert PII_CONCERN not in blob, "고민 원문 누출"
    assert PII_PLACE not in blob, "출생지 누출"
    assert "ord_test" not in blob, "order_id 연계 누출"


def test_extract_keeps_calc_facts():
    rec = insight.extract_insight(_order(), engine_version="test")
    assert rec["bazi"] == "己卯 丙子 戊午 戊午"
    assert rec["gender"] == "M"
    assert rec["solar_date"] == "2000-01-01"
    assert (rec["year"], rec["month"], rec["day"], rec["hour"]) == (2000, 1, 1, 10)
    assert rec["ziwei_present"] is False  # ziwei=None
    assert rec["schema"] == "calc_insight_v1"


def test_boundary_detection():
    # 월지 불일치 + 한·중 상이 → 경계
    b = _order(
        crosscheck_warnings=["월지 lunar(寅)↔Skyfield(丑) 불일치"],
        normalize_warnings=["한·중 음력 상이일: 중국기준 …"],
    )
    labels = insight.boundary_labels(b)
    assert insight.is_boundary(b)
    assert "month_branch_mismatch" in labels
    assert "kr_cn_lunar_divergence" in labels

    # 자시 경계(23시) + needs_review
    z = _order(hour=23, needs_review=True)
    zl = insight.boundary_labels(z)
    assert "zasi_boundary_2300" in zl and "needs_review" in zl

    # 평범한 케이스 → 경계 아님
    clean = _order()
    assert not insight.is_boundary(clean)
    assert insight.boundary_labels(clean) == []


def test_append_roundtrip(tmp_path):
    out = tmp_path / "calc_insights.jsonl"
    rec = insight.extract_insight(
        _order(), engine_version="test", extracted_at="2026-06-13T00:00:00Z"
    )
    insight.append_insight(rec, str(out))
    insight.append_insight(rec, str(out))  # 누적 append
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    back = json.loads(lines[0])
    assert back["bazi"] == "己卯 丙子 戊午 戊午" and back["extracted_at"] == "2026-06-13T00:00:00Z"
