---
paths:
  - "sajugen/render/**"
---

# 렌더 레이어 규칙 (render/)

- PDF 하드 게이트 비악화: 텍스트레이어(추출 1500자 이상)·폰트 임베드·태그(StructTree/MarkInfo) — 통이미지 PDF 절대 금지.
- veraPDF 잔여 clause 7.1-3 1건(Chromium 한계, 옵션1=측정·보고만) 기준 비악화. 새 실패 clause 추가 금지.
- @page margin 변경 시 pdf.py의 pg.pdf margin과 반드시 동기화.
- 폰트는 번들 OFL만(나눔명조·나눔브러시·Pretendard + Source Han Serif K 한자 폴백). 시스템 폰트(Malgun 등) 의존 금지.
- Chromium @page margin-box(페이지번호) 미지원 — header/footer 미사용 유지(PDF/UA 태그 보존), 아웃라인이 내비게이션.
- SVG 차트는 role=img + title 유지(접근성), 결정론(입력 동일=출력 동일) 유지.
- 리포트 말미 colophon = '맺음 서명 슬롯'(브랜드 서명 + 짧은 맺음 문안)으로 유지. 본문 내 도구·AI 언급 고지는 넣지 않는다(2026-06-12 운영자 지시 개정 — 절대규칙 18 참조). "전문가 직접 풀이" 표현 금지 유지.
