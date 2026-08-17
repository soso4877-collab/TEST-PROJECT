# -*- coding: utf-8 -*-
"""룰 100% 전략의 유일한 약점 실측 — 고객마다 같은 문장이 얼마나 나오는가.

AGENTS.md 우려: "결정론 룰은 고객마다 동일 패턴이라 그 자체가 AI 출력 신호".
서로 다른 사주 30명분을 룰만으로 생성해 문장 단위 중복률을 잰다. LLM 미호출.
"""
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.calc import engine  # noqa: E402
from sajugen.content import rules  # noqa: E402

random.seed(20260817)
N = 30
people = []
while len(people) < N:
    people.append((
        random.randint(1960, 2005), random.randint(1, 12), random.randint(1, 28),
        random.choice([2, 4, 6, 8, 10, 12, 14, 16, 18, 20]), random.choice([10, 30, 50]),
        random.choice([True, False]),
    ))

NAMES = ["가온", "나린", "다솜", "라온", "마루", "바다", "사랑", "아라", "자몽", "차민"]
docs = []
for i, (y, mo, d, h, mi, male) in enumerate(people):
    r = engine.build(y, mo, d, h, mi, is_male=male, horoscope_date="2026-08-17")
    sk = rules.build_all(r, ref_year=2026, name=NAMES[i % len(NAMES)] + "수",
                         concern_category="전반")
    docs.append(sk)

# 이름 치환 제거 후 문장 분리 (호명 차이를 중복 아님으로 오판하지 않도록)
NAME_RX = re.compile("|".join(n + "수" for n in NAMES) + "|님")


def sentences(text: str) -> list[str]:
    t = NAME_RX.sub("", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if len(s.strip()) >= 12]


section_ids = sorted({k for d in docs for k in d})
per_section = {}
all_sents_per_doc = []

for sid in section_ids:
    doc_sets = []
    for d in docs:
        if sid in d:
            doc_sets.append(set(sentences(d[sid])))
    if not doc_sets:
        continue
    cnt = Counter()
    for s in doc_sets:
        cnt.update(s)
    total_unique = len(cnt)
    # 30명 중 절반 이상에게 똑같이 나오는 문장 = '판박이 문장'
    boiler = [s for s, c in cnt.items() if c >= len(doc_sets) * 0.5]
    # 문서당 평균: 내 문장 중 판박이 비율
    ratios = []
    for s in doc_sets:
        if s:
            ratios.append(len(s & set(boiler)) / len(s))
    per_section[sid] = {
        "docs": len(doc_sets),
        "unique_sentences": total_unique,
        "boilerplate_sentences": len(boiler),
        "avg_boilerplate_ratio_pct": round(sum(ratios) / len(ratios) * 100, 1) if ratios else 0,
    }

# 전체 문서 기준
for d in docs:
    ss = set()
    for v in d.values():
        ss |= set(sentences(v))
    all_sents_per_doc.append(ss)
gcnt = Counter()
for s in all_sents_per_doc:
    gcnt.update(s)
gboiler = {s for s, c in gcnt.items() if c >= N * 0.5}
gratios = [len(s & gboiler) / len(s) for s in all_sents_per_doc if s]

out = {
    "people": N,
    "total_unique_sentences": len(gcnt),
    "sentences_shared_by_half_or_more": len(gboiler),
    "avg_boilerplate_ratio_pct": round(sum(gratios) / len(gratios) * 100, 1),
    "avg_sentences_per_doc": round(sum(len(s) for s in all_sents_per_doc) / N, 1),
    "per_section": per_section,
}
Path("tmp/_repeat_rate.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "per_section"}, ensure_ascii=True))
