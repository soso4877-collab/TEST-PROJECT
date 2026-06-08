"""HomeStat(카카오 채널 홈 통계) 추세 집계 — 읽기전용.

parse_homestat.py로 구조 확인 결과: 컬럼 = [날짜, 방문자수, 조회수], 일별.
(친구 수가 아니라 '채널 홈' 방문/조회 통계임에 주의.)
이 스크립트는 월별 추세 + 최근/기준선 평균 + 쇠퇴율을 출력한다.

사용: python saju-growth-system/automation/analyze_homestat.py [경로]
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DEFAULT_PATH = r"C:\Users\pc\Downloads\HomeStat_2025-01-01_2026-06-07.xls"


def main():
    import pandas as pd

    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    df = pd.read_excel(path, engine="xlrd")
    # 컬럼이 깨질 수 있어 위치로 참조: 0=날짜 1=방문자수 2=조회수
    df = df.iloc[:, :3]
    df.columns = ["date", "visitors", "views"]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    total_days = len(df)
    span = f"{df['date'].min().date()} ~ {df['date'].max().date()}"
    print(f"[기간] {span}  ({total_days}일)")
    print(f"[합계] 방문자 {int(df['visitors'].sum()):,}  조회 {int(df['views'].sum()):,}")

    # 월별 추세
    m = df.set_index("date").resample("MS").sum(numeric_only=True)
    print("\n[월별 합계]  월 | 방문자 | 조회")
    for idx, row in m.iterrows():
        print(f"  {idx.strftime('%Y-%m')} | {int(row['visitors']):>6,} | {int(row['views']):>6,}")

    def avg_last(days):
        sub = df.tail(days)
        return sub["visitors"].mean(), sub["views"].mean()

    print("\n[최근 평균(일)]  구간 | 방문자/일 | 조회/일")
    for d in (7, 30, 90):
        v, w = avg_last(d)
        print(f"  최근{d:>3}일 | {v:8.1f} | {w:8.1f}")

    base = df[(df["date"] >= "2025-01-01") & (df["date"] <= "2025-01-31")]
    bv, bw = base["visitors"].mean(), base["views"].mean()
    rv, rw = avg_last(30)
    print(f"\n[기준선] 2025-01 평균/일: 방문자 {bv:.1f}  조회 {bw:.1f}")
    print(f"[현재]   최근30일 평균/일: 방문자 {rv:.1f}  조회 {rw:.1f}")
    if bv:
        print(f"[쇠퇴율] 방문자 {rv / bv * 100:.1f}% 수준 (= {bv / max(rv, 0.01):.1f}배 감소)")

    peak = df.loc[df["views"].idxmax()]
    print(
        f"\n[최대 조회일] {peak['date'].date()}  방문자 {int(peak['visitors'])}  조회 {int(peak['views'])}"
    )
    # 최근 6개월 0방문일 비율
    recent = df.tail(180)
    zero = int((recent["visitors"] == 0).sum())
    print(f"[최근180일] 방문자 0인 날 {zero}/{len(recent)}일 ({zero / len(recent) * 100:.0f}%)")


if __name__ == "__main__":
    main()
