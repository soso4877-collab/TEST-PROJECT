# 22. 발급 런북 — 주문 접수부터 수동 발송까지 (운영자 실행 절차)

> 작성 2026-07-08. 대상: 운영자 본인. 유형: 하우투(Diátaxis) — "지금 한 건을 발급해 끝낸다".
> 이 문서는 **절차**만 담는다. 왜(정책)는 `docs/03`(유파)·`docs/07`(안전·고지)·`.claude/rules/00-immutable.md`,
> 검수 상세는 `docs/10-admin-review-workflow.md`, 사람의 일반 운전법은 `docs/19`를 본다(중복 기재 안 함).
> 근거: 2026-07-07 출시 판정(AI-Brain `50_Decisions/2026-07-07-sajugen-출시판정.md`) D8~10 체크리스트.

---

## 0. 발급 파이프라인 한눈에

```
접수(경계케이스 확인 + 동의) → 생성(CLI/웹폼) → 다층 게이트 → 검수(육안·전문) → APPROVED → 수동 발송(+ 전달 후 삭제 안내)
```
- 상태머신이 **APPROVED 전 발송을 물리 차단**한다(절대규칙 16). 우회 금지.
- 자동 발송 없음 — 마지막 발송은 항상 사람 손.

---

## 1. 접수 (신규 고객)

### 1-1. 경계 케이스 확인 질문 (E10 — 1차 범위 제외, 접수 시 반드시 확인)
아래 셋은 오답 진입로다(fix 3회 이력). 접수 대화에서 **먼저 확인**하고, 애매하면 진행 말고 되묻는다:
1. **자시(밤 23~01시) 출생?** — 정책 = `ZasiPolicy.JST_2300`(23시부터 자시·일주 익일 전환, 00-immutable §6). 출생 시각이 경계면 관리자 확인 플래그.
2. **음력 생일 / 윤달?** — 음력이면 접수에 '음력' 명시, 윤달생이면 윤달 여부까지. 1차 기준 = KASI(00-immutable §3). 자미 윤달 = 15일 분할법.
3. **해외 출생(한국 외 경도)?** — 진태양시 보정에 출생지 경도 필요. 국내면 기본(서울) 사용.
- 시진 불명(출생 시각 모름): 명리 = 정오 추정 + 고지, 자미 = 생성 금지(00-immutable §8). 접수 시 시각 확보를 우선 시도.

### 1-2. 개인정보 보관 동의 (E9 — 개인정보보호법 15·16조)
재상담(후속·재방문) 참고용으로 명식을 보관하려면 **동의 1줄**을 받는다:
> "풀이 제공 및 재상담 참고 목적으로 명식을 보관합니다. 요청하시면 즉시 파기합니다."
- 동의 시 → 단골 별칭 발급(2계층 보관): 식별자(이름)는 `customers.name_masked`로 분리, 명식·content는 동의 하에 보관.
- 미동의 시 → 별칭 미생성. 식별자는 목적 달성 후 지체 없이 파기(30일).
- **즉시 파기 요청**: `python -m sajugen.delete_order <order_id> --yes`(하드 삭제). 식별자만 파기(명식 보존)는 `purge_identifier(alias)` 경로.

### 1-3. 상담 멘트 지침 (E11 — 표시광고법, 게이트 밖이라 사람이 지킨다)
카카오 상담 대화는 다층 게이트가 검사하지 않는다. **결과·시기 보장 표현 금지**(정본: AI-Brain `75_Content-Domain/표시광고법-결과보장-금지.md`):
- 금지: 시간+결과 결합("한 달 안에 정리됩니다"), 확정어("반드시/확실히/100% 적중").
- 권장: 시기감·판단 지점만. 좋은 예 — "올해 안에 판단할 지점이 한 번 옵니다. 그때 무엇을 기준으로 볼지 짚어드립니다."
- 근거: 표시광고법 8조 + 채널 운영정책(위반 시 계정 정지 가능).

---

## 2. 생성

### 2-1. CLI 생성 (기본 경로)
```
./.venv/Scripts/python.exe -m sajugen.cli gen \
  --birth "1990-05-20 14:30" --gender 남 --name "홍길동" \
  --brand sajudoryeong \
  --horoscope 2026-06-01 --concern "올해 이직 고민" --out out.pdf
```
- **`--brand` = 다계정 스위치**(2계정 예시): `sajudoryeong`(사주도령) / `seodam`(서담선생). 프리셋 키 또는 임의 문구.
- 생시 미상이면 `--birth "1990-05-20"`(시각 생략). 음력이면 `--lunar`(윤달 `--leap`). 해외면 `--longitude/--latitude`.
- 계산 불일치(3원 교차 실패) 시 `CALC_MISMATCH`로 차단 — 임의 진행 금지, 접수 데이터 재확인.

### 2-2. 웹폼 경로 (주문 접수 UI)
```
./.venv/Scripts/python.exe -m uvicorn sajugen.app:app --host 127.0.0.1 --port 8765
```
- 주문이 상태머신에 RECEIVED로 진입 → 생성 → 검수 화면으로.

---

## 3. 게이트 (다층 검증 — 자동)

- 하드 게이트 AND-체인 = `GATE_KEYS` 20키(`sajugen/render/verify.py`, `docs/20-gate-coverage.md`). `gate_pass=false`면 발급 불가.
- 컴포즈 시점 벨트: safe_lint(§12) → factcheck(간지·별 토큰) → trace(그라운딩) + 확장 린트군.
- **게이트 통과는 발급의 필요조건일 뿐, 충분조건이 아니다** — 반드시 4단계 육안·전문 검수를 거친다(QI-2026-07-02: gate_pass=true인데 육안 불합격 반복).

---

## 4. 검수 (사람 — 상세는 docs/10)

- 검수 화면에서 IN_REVIEW 주문을 연다. 관리자 수정분도 3단 가드 재통과해야 반영된다.
- 육안 체크리스트 ≤ 7항목(docs/19 §2-7 경고 다이어트). 표준 양식: `handoff/templates/pdf_review_report.md`.
- 발송 전 이질 렌즈 스윕(advisory, 운영자 승인·3중 잠금·상한 $3)은 육안 전 후보 발굴용(docs/19 §2-6).
- 계산·문안·PII·레이아웃 이상 발견 시 반려 → 수정 → 재검수. 통과 시에만 승인.

---

## 5. 승인 & 수동 발송

- 검수 통과 → 상태 `APPROVED`로 전이. `APPROVED` 전에는 발급 함수가 `ApprovalRequired` 예외로 물리 차단.
- 발급: PDF = `issue_final_pdf`(상태머신 경유), 후속 텍스트 = `issue_final_text`. 발급 시 `DELIVERED`로 전이.
- **수동 발송**: 카카오로 PDF/텍스트 전달. 전달 후 **삭제 안내**(E13): 고객 보관용임을 명시, 채널 서버 보관본은 전달 후 삭제 권고. 운영자 보관본은 E9 정책(동의·별칭).

---

## 6. 후속·재방문 발급 (단골 재상담 — 신규 경로)

원 리포트를 재생성하지 않고 **저장된 사실(report_json)만 재사용**해 짧은 카카오 텍스트 답변을 낸다(새 명리 판정 금지).

```
# 1) 단골 조회 (별칭 또는 마스킹 이름)
./.venv/Scripts/python.exe -m sajugen.cli customer-find --alias SD-0007
#    (또는 --name 으로 마스킹 식별자 검색)

# 2) 후속 답변 생성 (저장 사실 재사용 → 게이트 서브셋 → 새 주문)
./.venv/Scripts/python.exe -m sajugen.cli gen-followup \
  --alias SD-0007 --question "올해 이직해도 될까요" --kind followup   # 또는 revisit
```
- 게이트 = **후속 답변 서브셋**(텍스트 린트만, PDF 레이아웃 게이트 부적용). 통과 못 하면 주문이 생성되지 않는다.
- **범위 밖 연도/주제는 거부**된다(fail-closed): 저장된 기준연도(`allowed_years`) 밖을 물으면 "신규/재방문 정식 리포트 필요"로 안내 → 신규 발급(1~5장) 경로로.
- 후속 답변도 상태머신 재사용: `RECEIVED→…→IN_REVIEW→(운영자)APPROVED→수동 발송`. 검수·발송은 위 4·5장과 동일.

---

## 7. 발급 후 — 기준 환경 & 회귀 (E3)

- **완료 근거는 항상 기준 환경(전 리소스) pytest**: `./.venv/Scripts/python.exe -m pytest tests/ -q` → exit 0.
  - 기준선(2026-07-08 후속·재방문 반영): **692 passed / 4 skipped**. passed 감소 = 회귀.
  - Codex 샌드박스 등 리소스 부족 환경은 skip 수가 다르다(veraPDF/Chromium/API키 부재) — skip 차이는 코드 문제 아님, 완료 근거로는 기준 환경 수치만 인정.
- 계산(`calc/`·`input/`) 변경이 있었다면 골든 회귀 필수: `pytest -q -k golden`.
- 발송·파기·push된 비밀은 되돌리기 불가 3종(docs/19 §7-1) — 이 셋만 의식적으로 느리게.

---

## 부록 A. 상태 전이표 (요약)
`RECEIVED → NORMALIZED → CALC_OK(또는 CALC_MISMATCH 차단/NEEDS_INFO) → DRAFTED → IN_REVIEW → APPROVED → DELIVERED`
- 정의: `sajugen/store/orders.py`(`OrderState`·`ALLOWED`). 오케스트레이션: `sajugen/order_flow.py`.

## 부록 B. 자주 쓰는 명령
| 목적 | 명령 |
|---|---|
| 전체 테스트(완료 근거) | `./.venv/Scripts/python.exe -m pytest tests/ -q` |
| 신규 생성(CLI) | `... -m sajugen.cli gen --birth ... --gender ... --name ... --brand ...` |
| 웹폼(접수/검수) | `... -m uvicorn sajugen.app:app --host 127.0.0.1 --port 8765` |
| 단골 조회 | `... -m sajugen.cli customer-find --alias SD-0007` |
| 후속 답변 | `... -m sajugen.cli gen-followup --alias SD-0007 --question "..."` |
| 즉시 파기 | `python -m sajugen.delete_order <order_id> --yes` |

## 다음 단계 (D10~14)
지인 베타 2건 실발급 + 피드백 폼 3문항(어디가 와닿았나/어디가 안 믿겼나/얼마면 사겠나) → 첫 유료 1건. 상세: `docs/15-beta-plan.md`.
