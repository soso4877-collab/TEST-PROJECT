# 자동화 아키텍처

> 원칙: **기존 검증 툴 우선, 코딩은 레버리지 있는 곳에만.** 근거: `research/verified-source-map.md`
> 3레벨 분리. 7일 내 Level 3 금지(오퍼 검증 전 오버엔지니어링).

## 작업별 결정 매트릭스

| Task | 기존툴 우선 | 코드 필요 | 권장 도구 | 이유 | 구현일 |
|---|---|---|---|---|---|
| 콘텐츠 DB | 예 | 아니오 | Google Sheets / Airtable | 공식 API·빌드 0 | D1 |
| 프롬프트 라이브러리 | 예 | 아니오 | repo MD (`content/`) | 버전관리 | D1 |
| 소스 아이디어 생성 | 예 | 아니오 | Claude Code + hooks-library | 카피역량 활용 | D1 |
| 채널별 포맷터(1→11) | 부분 | **예** | `repurpose.py` | 반복노동 제거 | D2 |
| CapCut 영상 | 예 | 아니오 | 템플릿 수동 배치 | 공식 API 없음 | D3 |
| 콘텐츠 캘린더 CSV | 부분 | **예** | `calendar_to_csv.py` | 시트→스케줄러 | D4 |
| 멀티채널 예약발행 | 예 | 아니오 | **Metricool**(무료→유료) | 네이티브 자동발행 | D2~3 |
| 메트릭 트래커 | 예 | 부분 | Google Sheet + 스크립트 | scripts/common 재활용 | D2 |
| 일일 리뷰 요약 | 부분 | **예** | `daily_metrics_summary.py` | 측정·교정 루프 | D5 |
| 카카오 메시지 초안 | 예 | 아니오 | 템플릿 MD + 관리자센터 | 네이티브 스케줄러 없음 | D2 |
| 결제/주문 | 예 | 아니오 | Google Form + 송금/계좌 + 정산시트 | 즉시·마찰 최소 | D1 |
| 입문상품 배송 | 예 | 아니오 | **sajugen PDF** + 본인 LLM 해석 | 기존 작동 자산 | D1 |

## 3레벨 자동화

### Level 1 — 즉시 노코드 (7일 내)
Google Sheets/Airtable 콘텐츠 DB · AI 콘텐츠 생성(Claude) · CapCut 템플릿 · Metricool 스케줄러 · 구글폼 결제/주문 · 카톡 메시지 초안 · 메트릭 시트.

### Level 2 — 라이트 글루 (시간 즉시 절약시만)
`repurpose.py`(1→11) · `calendar_to_csv.py`(Publer CSV) · `daily_metrics_summary.py`(일일 요약).
- 각 100줄 내외, 외부 API 의존 없음(파일 in/out). 외부 호출 0 → 안전·재현 가능.

### Level 3 — 나중 (7일 내 금지)
전체 CRM · 완전자동 챗봇 · API 자동게시 시스템 · 복잡 대시보드 · 대용량 파이프라인.
- 카톡 자동발송이 꼭 필요해지면 **SOLAPI**(유일한 카톡 브리지)만 검토.
- iPaaS(n8n/Make/Zapier)는 게시용 아닌 글루(시트→스케줄러·AI생성)로만 한정.

## 데이터 흐름
```
hooks-library → repurpose.py → 채널별 드래프트 → 검수(컴플라이언스)
   → 7-day-content-calendar.csv → calendar_to_csv.py → Metricool/Publer 임포트 → 발행
발행 결과 → metrics CSV → daily_metrics_summary.py → daily-review → 다음날 조정
주문(구글폼) → 입금확인 → sajugen PDF + LLM 해석 → 카톡 전달
```
