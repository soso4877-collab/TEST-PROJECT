# TASK_PACKET — 베타 1호 Z>0 문체·조언·가독성·hsweep/비용 개선 교차리뷰

- task_id: `beta-1-register-harness-20260712`
- base_commit: `5ebd3b6eb78f238747e5b4ae18f4f49c138973fc`
- 구현자: Codex
- 다음 작업자: Claude 신선 컨텍스트
- 상태: `review_requested`
- 제품 판정 범위: `CODE_PASS`만. 새 replacement PDF·비용 절감·Z=0 판정은 포함하지 않는다.

## 0. 리뷰 권한·금지 경계

- 제품 코드·테스트·정책 문서는 read-only로 전량 검토한다. 발견 사항은 `REVIEW-FEEDBACK.md`에 기록하고
  제품 코드를 직접 고치지 않는다.
- 검증 기록이 필요하면 `REVIEW-FEEDBACK.md`, `sajugen/STATE.md`, `implementation-notes.md`,
  `handoff/current/manifest.json`만 수정한다.
- 고객/ignored 산출물, `harness/profiles/local/**`, `.env`, secrets를 열지 않는다.
- Anthropic API, PDF 재생성, LLM-on hrun, commit, push, APPROVED, 발송을 실행하지 않는다.
- 기준환경 테스트와 정적 분석은 `.\.venv\Scripts\python.exe -m ...` 경로만 사용한다.

## 1. 배경과 구현 목표

베타 1호는 기존 전 게이트와 hsweep N=29/M=0/K=0을 통과했지만 운영자 육안에서 Z>0였다. 확인된 결함은
문서체·AI틱 register, 외부 시험/직업 실무 사실·절차 조언, 어려운 용어의 설명 부족이다. 동시에 기존 hsweep는
raw 후보와 단계별 trace를 보존하지 않아 “렌즈 미탐”과 “동일 모델 judge의 과반박”을 사후 구분할 수 없었다.
12개 Sonnet 장은 서로 독립이라 문맥 반복이 생기고, 공통 정적 prefix를 매번 보내 비용도 중복됐다.

이번 후보는 모델을 낮추지 않고 다음을 구현한다.

1. 기존 `docs/14-tone-spec.md` SSOT 확장과 문서↔코드 기계 계약.
2. 고객 가시 전역 register 게이트와 고정밀 외부 도메인 조언 게이트.
3. consult action/work_career 직답 축, 쉬운 용어·기능적 비유·골격/프롬프트 순화.
4. PII 없는 공통 `ReportContext`, 현재 장 ID, 활성 장 용어 소유권, 5분 explicit prompt cache.
5. cache usage 실측 후에만 병렬 호출하는 비용 fail-closed와 run 단위 PII-safe usage 관측.
6. hsweep schema v2 비파괴 후보 보존·전수 judge·운영자 K/Z·PII manifest·canonical atomic review.

## 2. 핵심 수용 기준

### A. 문체 register

- `client_tone_lint.py`의 외래어와 분리된 `REGISTER_RULES/register_lint()`가 존재한다.
- 결과지, 고객용 참고, 구간/준비 구간, 정보 수집 활용형, 커트 라인, 큰 그림/그림을 잡다 활용형
  (`잡으세요`, `잡으십시오` 포함)은 hard finding이다. 다의어 6종은 warning이다.
- cover·toc·본문·appendix 합성 주입이 `client_register_clean=False`, `gate_pass=False`가 된다.
- finding에는 승인된 `rule/token/count/page/severity`만 있고 고객 문장 원문이 없다.
- 개인 builder 최초/재시도/폴백, gunghap, relationship, followup, 최종 verify와 하네스가 동일 판정을 쓴다.
- 최종 룰 골격에 register/외부 조언을 합성 주입하면 `customer_policy_lint_total>0`과
  `GuardReport.clean=False`가 되어 pre-render aggregate도 false-PASS하지 않는다.

### B. 외부 도메인 조언·질문 직답

- 시험·직업 주제 단독 언급과 사주 근거의 시기·완급·방향·우선순위·사람/역할/관계 조율은 허용한다.
- 같은 문장/시각 블록에서 시험·직업 등과 외부 일정·마감·점수·연령·요건·자격·비용·법/제도 또는
  원서·서류 제출/접수·행정 절차를 결합한 사실·지시는 `external_domain_advice`로 차단한다.
- 간지·대운·세운 연도/숫자는 오탐하지 않는다. 질문 미러링만은 허용하되 뒤에 실무 지시가 붙으면 차단한다.
- `먼저/확인`만으로 consult action이 통과하지 않고, `work_career` 축은 직업/시험 질문에서 독립 근거를 요구한다.

### C. 가독성·공통 문맥·비용

- `ReportContext`는 허용된 ID만 받고 이름·생년월일·시각·질문 원문·이전 LLM 산문을 받을 필드가 없다.
- 12개 compose가 같은 context 객체/직렬화 system prefix를 공유하며, 호출별 user 메시지에 `[현재 장 ID]`가 있다.
- glossary owner는 실제 활성 장만 가리킨다. `ziwei` 상품처럼 선호 장이 빠진 경우 결정론 재배정된다.
- 최초 Anthropic 호출에서 `cache_creation_input_tokens` 또는 `cache_read_input_tokens`가 관측된 경우만 나머지
  호출을 3병렬로 실행한다. marker 없는 문자열·False·예외는 warm 1회에서 닫히고 룰 폴백한다.
- usage는 role/model/section/attempt/cache/thinking/stop을 PII 없이 기록하고, 동시 run과 주문 사이에 섞이지 않는다.
- 모델은 `claude-sonnet-4-6` 그대로다. API 미실행 상태에서 비용 절감 성공을 단언하지 않는다.

### D. hsweep schema v2

- raw 후보는 원형의 opaque ID/구조만 보존하고 ranker는 제거 권한 없는 advisory다. 모든 후보를 judge한다.
- 단계 status/partial과 usage role/model/stage가 기록된다. malformed 출력과 유효 빈 목록이 구분된다.
- 운영자 `review_status=complete`와 후보 전수 판정 전에는 K/Z가 null이다. K는 후보 확인, Z는 후보 밖 발견이며
  v1 model-confirmed 수를 K로 자동 이관하지 않는다.
- raw PII CLI 인자는 PDF/API 전에 거부하고, gitignored 로컬 PII manifest만 허용한다. 한국어 생년·시각 변형을
  정밀 마스킹한다.
- review subcommand는 입력의 임의 top/nested/rationale/verbatim 필드를 출력에 보존하지 않고 canonical 구조만
  쓴다. target과 `.hsweep-review-*.json` temp를 각각 git-ignore 확인하며 모든 실패에서 temp를 제거한다.

## 3. 범위와 파일

정확한 전체 목록과 기존 Claude Phase A 파일 구분은 `implementation-notes.md` 최상단을 따른다. 큰 묶음은:

- 정책/운영 문서 10개 + hsweep 렌즈 2개
- 기존 제품/게이트/LLM/주문 관측 코드 18개 + 신규 `report_context.py` 1개
- 하네스 코드 4개
- 기존 테스트 17개 수정 + 신규 계약 테스트 3개
- 계산·입력 SSOT `sajugen/calc/**`, `sajugen/input/**` diff 0

신규 필수 파일 5개(`handoff/tasks/beta-1-register-harness-20260712.md`, `report_context.py`, 신규 테스트 3개)는
운영자 commit 승인 전이라 의도적으로 untracked다. 승인 시 경로를 명시해 함께 추가해야 하며 `git commit -am`만
사용하면 import/계약 파일이 빠지므로 금지한다.

## 4. Codex 검증 증거

```text
.\.venv\Scripts\python.exe -m pytest tests\ -q
→ 913 passed / 32 skipped / exit 0 (기존 Codex 환경 803/32 대비 +110, 감소 0)

.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden
→ 28 passed / exit 0

register/context/tone/hsweep/PII 핵심 합성
→ 116 passed

변경 Python(기존 부채 3파일 제외) Ruff
→ All checks passed

전체 변경 Python py_compile / git diff --check / calc·input scope
→ exit 0 / exit 0 / diff 0
```

변경 파일 전체 Ruff의 19건은 HEAD 기존 부채다: `rules.py` F841 1+F541 16,
`render/pdf.py` F401 1, `render/verify.py` F841 1. 이번 후보의 신규 Ruff 악화는 0으로 판정했다.

## 5. Claude 교차리뷰 순서

1. HEAD가 `5ebd3b6`인지, diff가 `implementation-notes.md` 목록과 일치하는지 확인한다.
2. 제품 diff 전량을 A~D 수용 기준에 매핑한다. 특히 새 게이트 키의 GATE_KEYS/집계/하네스/최종 verify 누락,
   ReportContext PII 자유 텍스트 유입, cache fail-open, usage run 혼합, hsweep unknown 필드 보존을 우선 본다.
3. 기준환경 전체 pytest와 golden을 직접 실행한다. 기존 기준 831 passed/4 skipped와 총 수집 수 차이를 분리한다.
   산술 예상은 신규 110을 더한 941/4지만 직접 실행 전 확정값으로 쓰지 않는다.
4. 변경 Python Ruff를 실행하고 기존 3파일 부채와 신규 위반을 구분한다. py_compile·diff-check·calc/input diff 0을 확인한다.
5. PASS면 `verified/next_actor=user/checkpoint commit 결정`, 수정 필요면
   `changes_requested/next_actor=codex/REVIEW-FEEDBACK 미해결만 수정`으로 manifest를 handoff 도구로 갱신한다.

## 6. 정직한 미검증·후속 게이트

- 고객·ignored 파일, local profile, 실제 Anthropic API, 새 PDF, hrun은 이번 CODE_PASS 근거에 없다.
- prompt cache hit와 실제 비용 감소, 새 Sonnet 문안·조판·게이트·hsweep K/Z·운영자 Z=0은 **확정 불가**다.
- 교차리뷰 PASS와 운영자 checkpoint 뒤, 별도 과금 승인으로 replacement 주문 1회만 생성한다.
- 최종 성공은 새 PDF 표준 게이트 통과 + hsweep + 운영자 전문 육안 Z=0이다.
