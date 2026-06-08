#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""콘텐츠 캘린더 CSV -> 스케줄러(Publer/Metricool) 임포트용 CSV 변환.

외부 API 의존 없음. 파일 in/out만.
입력: content/7-day-content-calendar.csv
  (열: date,day,channel,pillar,format,hook,cta,publish_time,status,notes)
출력: Publer 호환 벌크 CSV
  (열: Date,Time,Account,Content,Media URL,Labels)

컴플라이언스: 카카오(kakao) 행은 자동 발행 대상이 아니므로 기본 제외(관리자센터 수동).
  --include-kakao 로 포함 가능(검수용).

사용 예:
  python calendar_to_csv.py --in ../content/7-day-content-calendar.csv --out publer_import.csv
"""

import argparse
import csv
import sys

# 캘린더 channel -> 스케줄러 계정 라벨 매핑(사용자가 실제 계정명으로 교체)
ACCOUNT_MAP = {
    "threads": "Threads",
    "instagram": "Instagram",
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "kakao": "KakaoChannel(manual)",
}

# 자동 발행 대상이 아닌 채널(스케줄러 미지원)
MANUAL_ONLY = {"kakao"}


def build_content(row):
    """후킹 + CTA로 게시 본문 초안 구성."""
    hook = (row.get("hook") or "").strip()
    cta = (row.get("cta") or "").strip()
    fmt = (row.get("format") or "").strip()
    parts = [hook]
    if cta:
        parts.append(cta)
    body = "\n\n".join([p for p in parts if p])
    return f"[{fmt}] {body}" if fmt else body


def convert(in_path, include_kakao):
    out_rows = []
    skipped = 0
    with open(in_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = (row.get("channel") or "").strip().lower()
            if ch in MANUAL_ONLY and not include_kakao:
                skipped += 1
                continue
            out_rows.append(
                {
                    "Date": (row.get("date") or "").strip(),
                    "Time": (row.get("publish_time") or "").strip(),
                    "Account": ACCOUNT_MAP.get(ch, ch),
                    "Content": build_content(row),
                    "Media URL": "",
                    "Labels": f"day:{row.get('day', '')};pillar:{row.get('pillar', '')}",
                }
            )
    return out_rows, skipped


def main(argv=None):
    p = argparse.ArgumentParser(description="콘텐츠 캘린더 -> Publer 호환 CSV")
    p.add_argument("--in", dest="in_path", required=True, help="입력 캘린더 CSV")
    p.add_argument("--out", dest="out_path", required=True, help="출력 CSV")
    p.add_argument("--include-kakao", action="store_true", help="카카오 행 포함(검수용)")
    args = p.parse_args(argv)

    rows, skipped = convert(args.in_path, args.include_kakao)
    fields = ["Date", "Time", "Account", "Content", "Media URL", "Labels"]
    with open(args.out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"변환 완료: {len(rows)}행 -> {args.out_path}")
    if skipped:
        print(f"  카카오 {skipped}행 제외(관리자센터 수동 발행). 포함하려면 --include-kakao")
    return 0


if __name__ == "__main__":
    sys.exit(main())
