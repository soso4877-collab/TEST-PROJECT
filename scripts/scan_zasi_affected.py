# -*- coding: utf-8 -*-
"""T2.1 자시 영향 구간 스캔 — 진태양시 23:00~24:00(일주 익일 전환) 출생 주문 식별.

자시 정책(JST_2300) 일주 반영 수정(T2.1, 커밋 0e90048) '이전'에 발급된 주문은 일주가
어긋났을 수 있어 운영자 재검토가 필요하다. 이 스캔은 식별·보고용이며 재렌더/재발송은
운영자 승인 하에만 한다. 출력은 order_id + 상태 + day_offset 만(이름·생년월일 등 PII 미출력).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.input import time_correction as tc  # noqa: E402
from sajugen.store.orders import OrderStore  # noqa: E402


def scan(db_path: str) -> list[dict]:
    """영향 주문 목록(day_offset=1) — PII 없이 order_id/state/day_offset 만."""
    st = OrderStore(db_path)
    try:
        out: list[dict] = []
        for r in st.list_orders():
            oid = r["order_id"]
            try:
                p = st.get_report(oid).render_meta.get("gen_params", {})
                ct = tc.correct(
                    int(p["year"]),
                    int(p["month"]),
                    int(p["day"]),
                    int(p["hour"]),
                    int(p["minute"]),
                    longitude=p.get("longitude", tc.SEOUL_LON),
                    latitude=p.get("latitude", tc.SEOUL_LAT),
                    policy=(
                        tc.ZasiPolicy.YAJASI_SPLIT if p.get("yajasi") else tc.ZasiPolicy.JST_2300
                    ),
                )
                if ct.day_offset:
                    out.append(
                        {"order_id": oid, "state": r.get("state"), "day_offset": ct.day_offset}
                    )
            except Exception as e:  # 파라미터 결손 등 — 개별 주문 skip(전체 스캔 지속)
                out.append({"order_id": oid, "state": r.get("state"), "error": type(e).__name__})
        return out
    finally:
        st.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="T2.1 자시 영향(진태양시 23~24시) 주문 스캔")
    ap.add_argument("--db", default="data/orders.sqlite", help="orders DB 경로")
    args = ap.parse_args()
    affected = scan(args.db)
    delivered = [a for a in affected if a.get("state") == "DELIVERED"]
    print(f"T2.1 자시 영향(진태양시 23~24시, 일주 익일) 주문: {len(affected)}건")
    print(f"  이미 발급(DELIVERED = 재검토 대상): {len(delivered)}건")
    for a in affected:
        detail = f"error={a['error']}" if "error" in a else f"day_offset={a['day_offset']}"
        print(f"  - {a['order_id']} state={a.get('state')} {detail}")
    print("[주의] 재렌더/재발송은 운영자 승인 하에만. 이 스캔은 식별·보고용(PII 미출력).")


if __name__ == "__main__":
    main()
