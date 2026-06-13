# -*- coding: utf-8 -*-
"""운영자 주문 파기 CLI — `python -m sajugen.delete_order --order-id ... --reason ... --yes`.

개인정보보호법 제21조: 발송 완료(목적 달성)·보유기간 경과 시 개인정보(생년월일·출생지·
고민 원문)는 지체 없이 복구불가 방법으로 파기해야 한다. 이 도구는 orders 행을 하드 삭제하고
audit_log에는 PII 없이 파기 사실(order_id·actor·사유·시각)만 남긴다.

실수 삭제 방지: --yes 미지정 시 실제 삭제하지 않고 안내만 한다(되돌릴 수 없는 작업).
"""

from __future__ import annotations

import typer

from .store.orders import OrderState, OrderStore

app = typer.Typer(add_completion=False, help="주문 파기(개인정보 복구불가 삭제, 제21조)")


@app.command()
def delete(
    order_id: str = typer.Option(..., "--order-id", help="파기할 주문 ID"),
    reason: str = typer.Option(
        "발송 완료·보유기간 경과 파기(제21조)",
        "--reason",
        help="파기 사유(감사 기록용 — 개인정보 기재 금지)",
    ),
    db: str = typer.Option("data/orders.sqlite", "--db", help="주문 DB 경로"),
    extract_insight: bool = typer.Option(
        False,
        "--extract-insight",
        help="파기 전 익명 계산특이점 레코드를 추출·보존(식별자 제거, 엔진 개선용)",
    ),
    yes: bool = typer.Option(
        False, "--yes", help="실제 삭제 실행(미지정 시 미리보기만 — 되돌릴 수 없음)"
    ),
) -> None:
    store = OrderStore(db)
    try:
        try:
            state: OrderState = store.get_state(order_id)
        except KeyError:
            typer.echo(f"주문 없음: {order_id}")
            raise typer.Exit(code=1)

        if not yes:
            typer.echo(
                f"[미리보기] 주문 {order_id} (상태 {state.value}) 를 하드 삭제합니다.\n"
                f"되돌릴 수 없습니다. 실제 파기하려면 --yes 를 붙여 다시 실행하세요."
            )
            raise typer.Exit(code=0)

        # 파기 전 익명 추출(extract-then-purge): 식별자 제거된 계산특이점만 보존
        if extract_insight:
            from . import insight as ins

            report = store.get_report(order_id)
            ins.append_insight(ins.extract_insight(report, extracted_at=ins._now_iso()))
            typer.echo("익명 계산특이점 추출·보존 완료(파기 전).")

        store.delete(order_id, actor="admin", reason=reason)
        typer.echo(f"파기 완료: {order_id} (PII 복구불가 삭제, audit에 파기 기록 보존)")
    finally:
        store.close()


if __name__ == "__main__":
    app()
