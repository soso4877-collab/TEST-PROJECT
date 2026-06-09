# saju-growth-system

사주/명리 콘텐츠 비즈니스의 **7일 매출 회복 시스템**.
목표: 기존 자산만으로 **일 매출 KRW 200,000 이상**을 7일 내 회복.

- 검증일: 2026-06-08
- 원본 계획: `C:\Users\pc\.claude\plans\claude-code-plan-hazy-pumpkin.md`
- 운영자 내부 도구. 장기 브랜딩이 아니라 **빠르고·컴플라이언스 준수·측정 가능한 현금흐름 복구**가 1순위.

---

## 한 줄 진단

오디언스와 카피 역량은 살아있으나, **트래픽이 단일 플랫폼(Threads)에 의존했고 수동이었으며
오퍼·결제 퍼널로 시스템화되지 않아** 매출이 붕괴했다.

---

## 7일 운용 순서 (요약)

1. **D1** — 퍼널 구축: 오퍼/가격 확정 → 구글폼 주문서 → 결제안내 → sajugen 입문 템플릿 점검 → 콘텐츠/메트릭 시트 + Metricool 연결.
2. **D2** — 카톡 4,000 친구 재활성화: (광고) 브랜드메시지 1회 발송 → 입문 29,000 판매 개시.
3. **D3** — 포맷 테스트: 카드뉴스 vs 자막릴스 A/B, 후킹 3종 변형.
4. **D4** — 승자 더블다운: 상위 포맷·후킹 확장 → 코어 59,000 집중.
5. **D5** — 코어 전환 강화: 후기/사례(동의) 콘텐츠.
6. **D6** — 확장·재타겟: 미응답 리드 재안내(컴플라이언스 내).
7. **D7** — 측정·시스템 고정: 7일 결산, 효과 포맷·채널·오퍼 고정.

상세: `strategy/7-day-revenue-plan.md`

---

## 폴더 구조

```text
research/     검증된 플랫폼·카카오 정책 출처맵 (실행 근거)
strategy/     매출 수학·7일 캘린더·오퍼 사다리·채널 운영체계
content/      콘텐츠 기둥·후킹 라이브러리·1→11 리퍼포징 프롬프트·캘린더 CSV
templates/    카카오 메시지·스토리·릴스/숏츠/틱톡 스크립트·CTA 뱅크
automation/   자동화 아키텍처·툴 비교·CapCut 워크플로 + 라이트 글루 3종(.py)
tracking/     메트릭 스키마·일일 리뷰 템플릿
checklists/   D1 체크리스트·일일 실행·컴플라이언스 게이트
```

---

## 재사용하는 기존 자산 (바퀴를 다시 만들지 않는다)

| 자산 | 경로 | 용도 |
|---|---|---|
| Threads 액션플랜 | `reports/threads/threads_action_plan.md` | 검증된 승리 포맷(반증형 후킹+오픈루프+자기답글) |
| 계정 진단 | `output/02_account_diagnosis.md` | 후킹 전환 레버 3종 + 알고리즘 8항목 체크 |
| 사주 PDF 생성기 | `sajugen/` | 입문 상품(미니 리포트) 반자동 배송 엔진 |
| 데이터 수집 | `scripts/common/` | 메트릭 정형화 패턴 차용 |

---

## 신규 코드 (라이트 글루 3종만)

`automation/` 내 Python 3종. 외부 API 의존 없음(파일 in/out):

- `repurpose.py` — 소스 후킹 1개 → 채널별 드래프트(1→11) 생성.
- `calendar_to_csv.py` — 콘텐츠 입력 → Publer 임포트 호환 CSV.
- `daily_metrics_summary.py` — 메트릭 CSV → 일일 요약.

```powershell
# 사용 예 (test-project 루트에서)
python saju-growth-system/automation/repurpose.py --hook "경오일주는 왜 돈이 새는가" --out saju-growth-system/content/drafts/
python saju-growth-system/automation/calendar_to_csv.py --in saju-growth-system/content/7-day-content-calendar.csv --out publer_import.csv
python saju-growth-system/automation/daily_metrics_summary.py --in saju-growth-system/tracking/metrics-2026-06-08.csv
```

---

## 컴플라이언스 핵심 (반드시 준수)

- **결과·시기 보장 표현 금지** (표시광고법 §3): "반드시/100% 적중/한 달 안에" 등 금지. "참고용 해석/학문적" 프레이밍.
- **카카오 (광고) 메시지**: (광고) 표기 + 발신자 연락처 + 무료 수신거부 3요소 필수, **21:00~08:00 발송 금지**, 친구당 1통/24h.
- **자격증 명시 금지**, **브랜드는 "사주도령"만** 사용(서담선생은 당근 별개 프로젝트 — 혼동 금지).
- **IG 원본성**: 워터마크/타플랫폼 클립/재탕 금지(비팔로워 추천 제한).
- **영상 AI 라벨**: 현실적 합성·기만 가능 시 라벨(원본이면 도달 중립).

상세 게이트: `checklists/compliance-checklist.md`
