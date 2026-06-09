#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""매일 큰틀 공감 후킹 ≥5개를 주제(topic) 단위로 뽑는 엔진 — 측정→교정 루프의 입력.

원칙(content/hooks-library.md):
- 첫 줄 = 큰틀 공감(많은 사람이 겪는 Pain) + 호기심 갭 + 부드러운 행동명령. 일주특정 첫줄 금지.
- 톤은 권위·확신. 자기비하·"무료로 봐준다"·결과/시기 보장 금지.
- 매일 ≥5 주제를 돌리고, 파급력 1위 주제 1개를 릴스/Shorts/캐러셀로 확산(repurpose.py).

각 주제에는 topic_id가 붙어 tracking/daily-tracker.xlsx 의 topic 열·주제별성과 시트로 롤업된다.
외부 API 의존 없음. 파일/표준출력만.

사용 예:
  python daily_hooks.py                 # 오늘 날짜로 5개 주제(표준출력)
  python daily_hooks.py --date 2026-06-10 --n 6
  python daily_hooks.py --out ../content/drafts/hooks-2026-06-10.md
  python daily_hooks.py --pick           # 1위(확산) 주제의 repurpose.py 명령까지 출력
"""

import argparse
import datetime as _dt
import os
import sys

try:
    from repurpose import check_banned  # 동일 폴더(automation)
except Exception:  # pragma: no cover - 단독 실행 폴백
    def check_banned(text):
        return []

# 큰틀 주제 뱅크(첫 줄=광범위 Pain, 일주특정 금지). impact: 예상 파급력 가중(높을수록 확산 우선).
# 근거: content/hooks-library.md 큰틀 후킹 5종 + 기둥1·2. 모든 hook은 보장표현 0.
TOPIC_BANK = [
    {
        "topic_id": "money-no-keep",
        "theme": "재물",
        "pillar": 1,
        "impact": 5,
        "hook": "분명 남들만큼은 버는데, 왜 손에 남는 게 없을까.",
        "deepen": "버는 자리 ≠ 지키는 자리 구조 → 본문에서 일주·십성으로 좁히기",
    },
    {
        "topic_id": "move-or-wait",
        "theme": "결정·타이밍",
        "pillar": 1,
        "impact": 5,
        "hook": "지금 움직여야 할지, 더 기다려야 할지 — 매번 이게 제일 어렵죠.",
        "deepen": "큰 구조(명리)와 '때'(자미두수)는 다르다 → 대운·세운 흐름",
    },
    {
        "topic_id": "effort-no-result",
        "theme": "노력·흐름",
        "pillar": 1,
        "impact": 4,
        "hook": "열심히 사는데 이상하게 안 풀리는 시기, 분명히 있어요.",
        "deepen": "흐름이 어긋난 구간 → 무엇을 줄이고 무엇을 밀지",
    },
    {
        "topic_id": "relationship-loop",
        "theme": "관계",
        "pillar": 2,
        "impact": 4,
        "hook": "사람은 바뀌는데 끝은 늘 비슷하게 흘러간다면.",
        "deepen": "관계의 '패턴 자리' → 명리 구조 + 시기 교차",
    },
    {
        "topic_id": "luck-turning-signal",
        "theme": "흐름 전환",
        "pillar": 1,
        "impact": 4,
        "hook": "운이 바뀌기 직전엔, 꼭 먼저 나타나는 신호가 있어요.",
        "deepen": "흐름이 도는 구간의 징후 → 단정 아닌 '참고 신호'",
    },
    {
        "topic_id": "career-fit",
        "theme": "직업·적성",
        "pillar": 2,
        "impact": 3,
        "hook": "잘하는 일과 맞는 일이 다른 것 같아 늘 헷갈린다면.",
        "deepen": "조직형/독립형 성향 → 십성·구조로 방향 짚기",
    },
    {
        "topic_id": "decision-delayed",
        "theme": "결정 회피",
        "pillar": 2,
        "impact": 3,
        "hook": "중요한 결정을 자꾸 미루게 되는 데도, 이유가 있습니다.",
        "deepen": "결정의 '자리'와 흐름 → 지금이 미룰 때인지 밀 때인지",
    },
    {
        "topic_id": "same-saju-diff",
        "theme": "차별·권위",
        "pillar": 3,
        "impact": 3,
        "hook": "같은 사주를 봐도 결론이 갈리는 데는, 이유가 있어요.",
        "deepen": "명리는 큰 틀, 자미두수로 '때'까지 교차 → 차별 시연(동의 사례)",
    },
]


def pick_for_day(date, n):
    """날짜로 결정적 회전 — 매일 다른 ≥n개 주제를 impact 내림차순으로."""
    base = date.toordinal()
    k = len(TOPIC_BANK)
    n = max(5, min(n, k))  # 최소 5개 보장
    idx = [(base + i) % k for i in range(n)]
    # 중복 제거(회전 특성상 n<=k면 유니크)
    seen, order = set(), []
    for j in idx:
        if j not in seen:
            seen.add(j)
            order.append(j)
    chosen = [TOPIC_BANK[j] for j in order]
    chosen.sort(key=lambda t: -t["impact"])
    return chosen


def render(date, n):
    chosen = pick_for_day(date, n)
    out = []
    out.append(f"# 오늘의 큰틀 주제 ({date.isoformat()}) — {len(chosen)}개")
    out.append("> 첫 줄=큰틀 공감(일주특정 금지)·권위 톤·보장표현 0. 일주/구조는 본문 심화로만.")
    out.append("> 추적: 게시 시 tracking/daily-tracker.xlsx 의 topic 열에 topic_id 기록 → 주제별성과로 롤업.\n")
    out.append("| 순위 | topic_id | 주제 | 기둥 | 파급력 | 큰틀 후킹(첫 줄) |")
    out.append("|---:|---|---|---:|---:|---|")
    warned = []
    for rank, t in enumerate(chosen, 1):
        if check_banned(t["hook"]):
            warned.append(t["topic_id"])
        out.append(
            f"| {rank} | `{t['topic_id']}` | {t['theme']} | {t['pillar']} | {t['impact']} | {t['hook']} |"
        )
    out.append("")
    out.append("## 본문 심화 가이드(첫 줄 금지 → 본문에서만)")
    for t in chosen:
        out.append(f"- `{t['topic_id']}`: {t['deepen']}")
    out.append("")
    top = chosen[0]
    out.append(f"**확산(릴스·Shorts·캐러셀) 1위 주제:** `{top['topic_id']}` — {top['hook']}")
    out.append(
        "→ 확산 명령: "
        f'`python repurpose.py --hook "{top["hook"]}" --topic {top["topic_id"]} '
        f'--pillar {top["pillar"]} --out ../content/drafts/`'
    )
    if warned:
        out.append("")
        out.append("> [경고] 금지어 발견 주제: " + ", ".join(warned) + " — 수정 후 사용.")
    return "\n".join(out), top, bool(warned)


def main(argv=None):
    p = argparse.ArgumentParser(description="매일 큰틀 주제 ≥5개")
    p.add_argument("--date", default=None, help="YYYY-MM-DD(미지정시 오늘)")
    p.add_argument("--n", type=int, default=5, help="주제 개수(최소 5)")
    p.add_argument("--out", default=None, help="출력 md(미지정시 표준출력)")
    p.add_argument("--pick", action="store_true", help="1위 확산 명령 강조 출력")
    args = p.parse_args(argv)

    date = _dt.date.fromisoformat(args.date) if args.date else _dt.date.today()
    text, top, warned = render(date, args.n)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("생성: " + args.out)
    else:
        print(text)
    if args.pick:
        print(f"\n[1위] {top['topic_id']} → repurpose.py 로 1→11 확산")
    return 1 if warned else 0


if __name__ == "__main__":
    sys.exit(main())
