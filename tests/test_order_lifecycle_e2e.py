# -*- coding: utf-8 -*-
"""T5.9: 전체 주문 생애주기 통합 실렌더 E2E(정기 실행 방안).

접수→생성(실렌더·use_llm=False→API 0)→검수→승인→최종 발급(DELIVERED)을 실경로로 도려
Phase 3~5 변경(T3.3 최종발급게이트·연도 화이트리스트·윤달 고지 등)이 함께 clean 동작하는지
확인한다. 실렌더 2회(~수분)로 무거워 기본 스위트에서 제외 — SAJUGEN_RUN_E2E=1 로 opt-in:
  SAJUGEN_RUN_E2E=1 ./.venv/Scripts/python.exe -m pytest tests/test_order_lifecycle_e2e.py -q
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import order_flow  # noqa: E402
from sajugen.store.orders import OrderState, OrderStore  # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.environ.get("SAJUGEN_RUN_E2E"),
    reason="통합 실렌더 E2E(무거움) — SAJUGEN_RUN_E2E=1 로 opt-in(T5.9)",
)


def test_full_order_lifecycle_delivers_clean(tmp_path):
    db = str(tmp_path / "e2e.sqlite")
    # 1) 접수
    oid, warnings = order_flow.create_order(
        birth="1990-05-20 14:30",
        gender="남",
        name="테스트",
        brand="seodam",
        horoscope="2026-06-01",
        product="integrated",
        db_path=db,
    )
    # 2) 생성(실렌더, use_llm=False)
    order_flow.run_generation(oid, db_path=db)
    st = OrderStore(db)
    try:
        assert st.get_state(oid) == OrderState.DRAFTED
        rep = st.get_report(oid)
        assert (rep.render_meta.get("verify") or {}).get("gate_pass") is True
        assert rep.render_meta.get("bazi")  # calc 산출 존재
        # 3) 검수 → 4) 승인
        st.transition(oid, OrderState.IN_REVIEW, actor="admin", note="E2E")
        st.transition(oid, OrderState.APPROVED, actor="admin", note="E2E")
        # 5) 최종 발급(T3.3 게이트: saju 재계산+스펙 복원+safe/fact 벨트+재렌더+verify)
        pdf = st.issue_final_pdf(oid, order_flow.final_render_fn, actor="admin")
        assert st.get_state(oid) == OrderState.DELIVERED
        assert Path(pdf).exists()
    finally:
        st.close()
