#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""일일 메트릭 CSV -> 채널/포맷 요약. 측정->교정 루프용.

외부 API 의존 없음. 파일 in/out만.
입력: tracking/metrics-YYYY-MM-DD.csv
  (열: date,channel,format,topic,hook,reach,completion_rate,shares,comments,clicks,orders,revenue,notes)
  topic = 큰틀 주제 식별자(daily_hooks.py의 topic_id). 없으면 hook으로 폴백.
출력: 표준출력 요약 + (옵션) markdown 파일 — 채널별·포맷별·주제별 + 승자 주제

사용 예:
  python daily_metrics_summary.py --in ../tracking/metrics-2026-06-08.csv
  python daily_metrics_summary.py --in metrics.csv --out summary.md
"""

import argparse
import csv
import sys
from collections import defaultdict


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def summarize(in_path):
    rows = []
    with open(in_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    by_channel = defaultdict(
        lambda: {"reach": 0.0, "shares": 0.0, "clicks": 0.0, "revenue": 0.0, "n": 0}
    )
    by_format = defaultdict(lambda: {"reach": 0.0, "completion": [], "shares": 0.0, "n": 0})
    by_topic = defaultdict(
        lambda: {"reach": 0.0, "shares": 0.0, "comments": 0.0, "clicks": 0.0, "n": 0}
    )
    total_rev = 0.0

    for r in rows:
        ch = (r.get("channel") or "?").strip()
        fmt = (r.get("format") or "?").strip()
        # topic 우선, 없으면 hook(주제 식별자) 폴백
        topic = (r.get("topic") or r.get("hook") or "?").strip() or "?"
        reach, shares = _num(r.get("reach")), _num(r.get("shares"))
        clicks, rev = _num(r.get("clicks")), _num(r.get("revenue"))
        comments = _num(r.get("comments"))
        comp = _num(r.get("completion_rate"))

        c = by_channel[ch]
        c["reach"] += reach
        c["shares"] += shares
        c["clicks"] += clicks
        c["revenue"] += rev
        c["n"] += 1

        ff = by_format[fmt]
        ff["reach"] += reach
        ff["shares"] += shares
        ff["n"] += 1
        if comp:
            ff["completion"].append(comp)

        tt = by_topic[topic]
        tt["reach"] += reach
        tt["shares"] += shares
        tt["comments"] += comments
        tt["clicks"] += clicks
        tt["n"] += 1

        total_rev += rev

    return rows, by_channel, by_format, by_topic, total_rev


def render(in_path, target=200000):
    rows, by_channel, by_format, by_topic, total_rev = summarize(in_path)
    out = []
    out.append(f"# 일일 메트릭 요약 ({in_path})")
    out.append("")
    out.append(f"- 총 게시물: {len(rows)}개")
    out.append(
        f"- 총 매출: {int(total_rev):,}원  (목표 {target:,}원 대비 {total_rev / target * 100:.0f}%)"
    )
    gap = target - total_rev
    out.append(f"- 목표까지: {int(gap):,}원" if gap > 0 else "- 목표 달성 ✅")
    out.append("")

    out.append("## 채널별")
    out.append("| 채널 | 게시 | 도달 | 공유 | 클릭 | 매출 |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for ch, d in sorted(by_channel.items(), key=lambda x: -x[1]["revenue"]):
        out.append(
            f"| {ch} | {d['n']} | {int(d['reach']):,} | {int(d['shares']):,} | {int(d['clicks']):,} | {int(d['revenue']):,} |"
        )
    out.append("")

    out.append("## 포맷별 (완시청 평균)")
    out.append("| 포맷 | 게시 | 도달 | 공유 | 완시청% |")
    out.append("|---|---:|---:|---:|---:|")
    best = None
    for fmt, d in sorted(by_format.items(), key=lambda x: -x[1]["reach"]):
        comp = sum(d["completion"]) / len(d["completion"]) if d["completion"] else 0.0
        out.append(
            f"| {fmt} | {d['n']} | {int(d['reach']):,} | {int(d['shares']):,} | {comp:.0f} |"
        )
        score = d["reach"] + d["shares"] * 10
        if best is None or score > best[1]:
            best = (fmt, score)
    out.append("")
    if best:
        out.append(f"**오늘의 승자 포맷**: `{best[0]}` → 내일 더블다운 검토.")
    out.append("")

    out.append("## 주제별 (큰틀 주제 = topic) — 측정→교정")
    out.append("| 주제(topic) | 게시 | 도달 | 댓글 | 공유 | 클릭 |")
    out.append("|---|---:|---:|---:|---:|---:|")
    best_topic = None
    for tp, d in sorted(by_topic.items(), key=lambda x: -(x[1]["reach"] + x[1]["shares"] * 10)):
        out.append(
            f"| {tp} | {d['n']} | {int(d['reach']):,} | {int(d['comments']):,} | {int(d['shares']):,} | {int(d['clicks']):,} |"
        )
        score = d["reach"] + d["shares"] * 10 + d["comments"] * 5
        if best_topic is None or score > best_topic[1]:
            best_topic = (tp, score)
    out.append("")
    if best_topic and best_topic[0] != "?":
        out.append(
            f"**오늘의 승자 주제**: `{best_topic[0]}` → 내일 릴스·Shorts로 확산(repurpose.py --topic {best_topic[0]})."
        )
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="일일 메트릭 요약")
    p.add_argument("--in", dest="in_path", required=True, help="입력 메트릭 CSV")
    p.add_argument("--out", dest="out_path", default=None, help="출력 md(미지정시 표준출력)")
    p.add_argument("--target", type=int, default=200000, help="일 매출 목표(원)")
    args = p.parse_args(argv)

    text = render(args.in_path, args.target)
    if args.out_path:
        with open(args.out_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("생성: " + args.out_path)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
