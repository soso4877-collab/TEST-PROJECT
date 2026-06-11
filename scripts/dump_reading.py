# -*- coding: utf-8 -*-
"""풀이 본문 확인용 1회성 덤프 — compose 적용 리포트를 텍스트(.md)+PDF로 산출.

실행: ./.venv/Scripts/python.exe scripts/dump_reading.py
출력: sajugen/render/out/reading_preview.md (열어보기용), reading_preview.pdf (실제물)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 프로젝트 루트 = sajugen 패키지 위치

from sajugen import pipeline  # noqa: E402,F401  (.env 로드 — ANTHROPIC_API_KEY)
from sajugen.calc import engine  # noqa: E402
from sajugen.content import builder  # noqa: E402
from sajugen.render import pdf as render_pdf  # noqa: E402

# --- 입력(원하면 여기만 바꾸면 됨) ---
Y, MO, DA, HH, MI = 1990, 5, 20, 14, 30
IS_MALE = True
HOROSCOPE = "2026-06-01"
CONCERN = "올해 이직해도 될까요"
USE_LLM = True  # False 면 룰 원문(무비용)으로 미리보기

saju = engine.build(Y, MO, DA, HH, MI, is_male=IS_MALE, horoscope_date=HOROSCOPE)
rep = builder.build_report(saju, use_llm=USE_LLM, ref_year=int(HOROSCOPE[:4]), concern=CONCERN)

# 1) 읽기용 텍스트 덤프
lines: list[str] = []
lines.append(
    f"# 사주 풀이 미리보기 ({Y}-{MO:02d}-{DA:02d} {HH:02d}:{MI:02d}, {'남' if IS_MALE else '여'})"
)
lines.append(f"- 사주팔자: {saju.crosscheck.bazi_myeongni}")
lines.append(f"- 신청 고민 분류: {rep.concern_category}")
lines.append(
    f"- 가드: clean={rep.guard.clean} (§12={rep.guard.safe_lint_total}, "
    f"사실={rep.guard.factcheck_total}, 생성/윤문={rep.guard.polished_sections}, "
    f"폴백={rep.guard.fallback_sections})"
)
lines.append("")
for s in rep.sections:
    mark = "[생성/윤문]" if s.polished else "[룰 원문]"
    lines.append(f"\n## {s.title}  {mark}")
    lines.append(s.final_text)

out_md = "sajugen/render/out/reading_preview.md"
with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# 2) 실제 PDF
age = int(HOROSCOPE[:4]) - Y
pdf_path = render_pdf.render_pdf(rep, saju, "reading_preview.pdf", age=age)

print("TEXT:", out_md)
print("PDF :", pdf_path)
print(
    "총 섹션:",
    len(rep.sections),
    "| clean:",
    rep.guard.clean,
    "| 생성/윤문:",
    rep.guard.polished_sections,
    "| 폴백:",
    rep.guard.fallback_sections,
)
sys.stdout.flush()
