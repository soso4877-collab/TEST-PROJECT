"""HomeStat(카카오 채널 홈 통계) .xls 읽기전용 파서 — 탐색 단계.

카카오 채널 관리자센터에서 내려받은 통계 파일은 확장자가 .xls여도
실제로는 (a) 구식 BIFF .xls, (b) HTML 표를 .xls로 위장, (c) .xlsx 중 하나일 수 있다.
이 스크립트는 파일을 수정하지 않고 구조만 출력한다(시트·컬럼·앞뒤 행).
구조 파악 후 친구수/추세 추출 로직을 별도로 확정한다.

사용: python saju-growth-system/automation/parse_homestat.py [경로]
"""

import sys

DEFAULT_PATH = r"C:\Users\pc\Downloads\HomeStat_2025-01-01_2026-06-07.xls"


def sniff(path):
    with open(path, "rb") as f:
        head = f.read(512)
    return head


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    print(f"[file] {path}")

    head = sniff(path)
    is_ole = head[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # 구식 BIFF .xls
    is_zip = head[:2] == b"PK"  # xlsx
    low = head[:200].lower()
    is_html = (b"<html" in low) or (b"<table" in low) or (b"<?xml" in low and b"spreadsheet" in low)
    print(f"[sniff] OLE(.xls)={is_ole}  ZIP(.xlsx)={is_zip}  HTML/XML={is_html}")
    print(f"[head]  {head[:80]!r}")

    import pandas as pd

    frames = {}
    # 1) HTML 위장 우선 시도(카카오가 흔히 이렇게 내보냄)
    if is_html or not (is_ole or is_zip):
        try:
            tables = pd.read_html(path)
            for i, t in enumerate(tables):
                frames[f"html_table_{i}"] = t
            print(f"[read_html] {len(tables)}개 표 파싱 성공")
        except Exception as e:
            print(f"[read_html] 실패: {e}")

    # 2) 엔진별 read_excel 시도
    if not frames:
        for engine in ("xlrd", "openpyxl", "calamine"):
            try:
                xl = pd.read_excel(path, sheet_name=None, engine=engine)
                frames = {f"{engine}:{k}": v for k, v in xl.items()}
                print(f"[read_excel] engine={engine} 성공, 시트 {list(xl.keys())}")
                break
            except Exception as e:
                print(f"[read_excel] engine={engine} 실패: {type(e).__name__}: {e}")

    if not frames:
        print("[결과] 어떤 방법으로도 파싱 실패 — 파일 형식 재확인 필요")
        return

    for name, df in frames.items():
        print("\n" + "=" * 60)
        print(f"[frame] {name}  shape={df.shape}")
        print(f"[columns] {list(df.columns)}")
        with pd.option_context("display.max_columns", None, "display.width", 200):
            print("[head]\n", df.head(8).to_string())
            print("[tail]\n", df.tail(5).to_string())


if __name__ == "__main__":
    main()
