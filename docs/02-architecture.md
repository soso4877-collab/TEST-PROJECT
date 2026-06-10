# 02. Architecture

> 최초 작성: 2026-06-10. 전문: C:\Users\pc\.claude\plans\role-claude-distributed-hellman.md §4

## 파이프라인 (12층)

```
[주문 접수(외부 채널)]
   v
(1) Order Intake + Normalizer      sajugen/input/normalize.py (신규)   실패: NEEDS_INFO(추정 금지)
(2) Calendar Verification          calc/kasi.py(신규) + crosscheck.py  불일치: CALC_MISMATCH 차단
(3) Saju Engine                    calc/myeongni.py + advanced.py (기존, 무변경)
(4) Ziwei Engine                   calc/ziwei.py (기존 + 윤달 정책 옵션)  실패: ENGINE_ERROR, 폴백 없음
(5) Unified Fortune JSON           sajugen/models/report.py (신규)
(6) Question Router                content/question_router.py (신규)   실패: domain=기타 폴백
(7) Rule-based NLG                 content/rules.py + builder.py (기존)
(8) Partial LLM (4구간)            content/llm_sections.py (신규)      실패: 룰 폴백 + NEEDS_REVIEW
(9) Safety Filter                  safe_lint + factcheck + trace (기존, LLM 구간에도 적용)
(10) PDF Renderer                  render/pdf.py + verify.py (기존)
(11) Admin Review UI               sajugen/admin/ (신규)               승인 전 발송 물리 불가
(12) Approval & Delivery           store/orders.py 상태머신 + 수동 발송
```

공통 원칙: 계산층 폴백 없음(차단) / 생성층 룰 폴백 / 발송은 승인 게이트.

## 기존 sajugen 모듈 매핑

| 기존 모듈 | 역할 | 이번 변경 |
|---|---|---|
| input/time_correction.py | 표준시역사·DST·진태양시·자시정책(기본 JST_2300) | 무변경 |
| calc/solarterms.py, crosscheck.py | Skyfield 절기, lunar↔Skyfield 교차 | KASI 3원 확장 |
| calc/myeongni.py, advanced.py | 팔자~세운·월운 | 무변경 |
| calc/ziwei.py | iztro-py 래퍼 | 윤달 정책 옵션 추가 |
| calc/engine.py | SajuResult 통합 | Unified JSON으로 확장 |
| content/* (27섹션+3단 가드) | 룰 NLG | question_router/llm_sections/repetition 추가 |
| render/* | tagged PDF + veraPDF 게이트 | 무변경(고지 문구 슬롯만) |
| cli.py / app.py | 운영자 도구 | 음력 입력 + admin 라우트 확장 |

## 상태 머신
RECEIVED → NORMALIZED → CALC_OK | CALC_MISMATCH(차단) → DRAFTED → IN_REVIEW → APPROVED → DELIVERED
- APPROVED 이전 최종 PDF 발급 불가. 모든 전이는 audit_log 기록.
