# TASK_PACKET — 자미 별-트레잇 정본 배선 (성격 깊이 1차: 골격이 기질을 말한다)

- task_id: `ziwei-temperament-wiring-20260717`
- base_commit: 활성화 시점 HEAD `c9396f4`(운영자가 manifest SHA로 고정)
- 구현자: Codex
- 검증자: Claude 신선 컨텍스트 교차리뷰
- 상태: `planned`(활성 시 manifest가 `packet_path`+SHA로 고정, `next_actor=codex`)
- 로드맵: 말투 개편 Stage 1 — 성격 추론 깊이(자미 정본 배선). 정본 = `docs/24-ziwei-star-temperament.md`
  (운영자 canon 승인 2026-07-17).

## 0. 역할·금지 경계 (YOU MUST)

- Codex 상시 금지(구현 승인 뒤에도): PDF 재생성, LLM/Anthropic API 호출, git commit, push, deploy.
- 데이터 경계: `.env`·secret·실고객 데이터·`harness/profiles/local/**`·ignored 산출물 비열람. 합성 입력만·PII 0.
- 검색은 ignored 제외 글롭 필수: `--glob '!**/render/out/**' --glob '!**/tmp/**' --glob '!**/synthetic-tmp/**' --glob '!**/data/**'`.
- 모든 실행은 `.\.venv\Scripts\python.exe -m ...`. 계산(`sajugen/calc/**`·`input/**`) **무변경**(자미 Star는 사실 슬롯만).

## 1. 배경 (실측 — 코드 대조 2026-07-17)

성격 풀이의 최대 결손 = **자미 별이 이름만 나열되고 기질 의미가 없다**.
- `rules.py:602-619` `_star_one`/`_stars_full`는 `"주성은 자미(묘)·화록, 보좌성은 …"`처럼 **별 이름 +
  밝기 + 사화만** 출력한다. 그 별이 어떤 기질인지는 어디에도 없다.
- `rules.py:633-693` `_palace_para` 꼬리는 `"별의 밝기와 사화는 … 세기와 방향을 읽는 단서"`라는 **제네릭
  설명**뿐 — "어떤 별이 있다"까지만 말하고 그 별의 성정을 서술하지 않는다.
- 결과: 자미 성격 서술이 명리보다도 얕은 "이름 나열"에 머문다. 이상형(사람 상담가)은 "이 별은 어떤
  기질이고, 밝기가 그걸 어떻게 증폭/약화하며, 사화가 어느 방향으로 색을 입힌다"까지 서술한다.

## 2. 목표 (관측 가능한 결과)

자미 별 서술이 **docs/24 정본 기질을 담게** 배선한다: 별 이름 나열 → (별 이름·밝기·사화는 그대로 유지하되)
그 별의 **핵심 기질/그늘**을 서술하고, 밝기는 발현 세기, 사화는 방향 modifier로 읽는다. 폴백(룰) 경로에서도
자미가 기질을 말하게 되어, 실 LLM이 없거나 가드 폴백 시에도 성격 서술이 얕아지지 않는다.

## 3. 접근 (설계 — 구현 세부는 Codex 재량, 계약은 §4)

- **신규 canon 모듈** `sajugen/content/ziwei_temperament.py`(또는 동등): docs/24 §1~§3을 **단일 소스**로
  옮긴 결정론 테이블 —
  - `STAR_TEMPERAMENT`: 14주성(한글명) → {化氣, 핵심기질(구), 그늘(구)}. docs/24 §1 표 그대로.
  - `BRIGHTNESS_DIRECTION`: 밝기 등급 → 발현 방향 문구(밝음=적극·건설적 발현 / 어두움=소극·그늘 전면).
    docs/24 §2. (등급값은 엔진 `_BRIGHT_KO` 키와 정합.)
  - `SIHUA_DIRECTION`: 화록/화권/화과/화기 → 방향 문구. docs/24 §3.
  - **docs/24 밖 별-의미 즉흥 생성 금지**(이 테이블이 유일 소스 — factcheck가 못 잡는 영역이라 정본 이탈 =
    할루시네이션). 테이블 주석에 docs/24 SSOT 명시.
- **소비처 배선**(`rules.py`): `_star_one`/`_stars_full`(602-619) 또는 `_palace_para`(633-693)·
  `_palace_brief`(622-630)·`ziwei_summary`(1681+)·`ziwei_palaces`(1736+)가 별 이름 옆/뒤에 그 별의 기질을
  **상담 화법**으로 덧붙이도록. 밝기·사화는 modifier 문구로. 문형 다양화는 `_pick`(md5 결정론) 유지.
- **표기 형태**(권고, Codex 재량): 별 이름·밝기·사화(사실 슬롯)는 현행 그대로 두고, 기질 서술을 **덧붙이는**
  방식(사실 슬롯 제거·변형 금지 — factcheck 정합 보존). 공궁(주성 없음)·주성 없는 궁은 기존 자연 표현 유지.

## 4. 계약 (불변 경계 — 반드시 준수)

- **계산 무변경**: `calc/ziwei.py` Star는 name·brightness·sihua만(절대규칙 1). 기질은 계산 아님 — content 층.
- **factcheck 사실 슬롯 불변**: 별이름·밝기·사화만 검사(현행). 기질 형용사는 factcheck 대상 아님 — 그러므로
  **정본 테이블(docs/24) 밖 기질어가 유입되지 않도록** 테이블을 단일 소스로 배선. factcheck 로직·allowed
  토큰 **완화/변경 0**.
- **길흉·예측·성별 단정 배제**(docs/24 §6, 절대규칙 3·11): canon 테이블에 富貴貧賤·壽夭·"여성불리" 등
  토큰 0. safe_lint·quality_lint·style_lint **완화 0**.
- **GATE_KEYS·render/verify 무관·무변경**. 3단 가드(safe/factcheck/trace) 우회·완화 0.
- 상품 토글 유지(`myeongni`는 ziwei/together 드롭 — 자미 배선이 명리단독 상품에 새 서술 유입 0).

## 5. 필수 양방·경계 테스트 (합성, PII 0)

1. **정상(비-no-op)**: 특정 주성(예: 자미·태음·칠살) 포함 궁을 서술하면 그 별의 **docs/24 핵심 기질 문구가
   출력에 실린다**(단순 이름 나열이 아님을 증명). 밝기 높음/낮음, 사화 有/無에 따라 방향 문구가 달라진다.
2. **canon 데이터 순정(data purity)**: `STAR_TEMPERAMENT`·`BRIGHTNESS_DIRECTION`·`SIHUA_DIRECTION`의 모든
   값에 길흉·예측·성별 단정 금칙 토큰(부귀·빈천·수명·재물운·"여성"+단정 등) **0** + 14주성 **전수 커버**
   (누락 별 없음, 누락 시 fail-closed).
3. **가드 비악화**: 새 자미 기질 서술이 실린 골격이 safe/factcheck/style/quality/customer_meta 등 기존 lint
   **전수 clean**(`test_skeleton_lint_matrix` 등). 별이름·밝기·사화 factcheck 정합 유지(사실 슬롯 변형 0).
4. 기준선 비악화: 전체 `pytest tests\ -q` exit 0·**1114 passed / 4 skipped 비감소**+신규, golden 28
   (자미 서술 바이트 변경 예상·허용 — count 비감소가 기준).

## 6. 검증·완료 기준

- 전체 `.\.venv\Scripts\python.exe -m pytest tests\ -q` exit 0(기준선 **1114/4** 비감소). golden 28(count).
  변경 Python Ruff·py_compile·`git diff --check` exit 0. calc/input diff 0.
- 실모델 자미 성격 서술 품질·실 PDF 육안은 운영자 승인 유료 재run 몫(CODE_PASS 밖). CODE_PASS 핵심 =
  "자미 골격이 docs/24 정본 기질을 결정론으로 서술하고, 정본 밖 기질어·길흉·가드 완화가 0".
- 완료 시 `implementation-notes.md`·`STATE.md` 갱신 + (권고) `docs/03` 결정표에 "자미 기질 테이블 채택·
  유파 note" 행 추가. commit/push는 운영자 승인 전 금지.

## 7. 예상 수정 범위

- 신규: `sajugen/content/ziwei_temperament.py`(docs/24 단일 소스 테이블).
- `sajugen/content/rules.py`(자미 소비처 `_star_one`/`_stars_full`/`_palace_para`/`_palace_brief`/
  `ziwei_summary`/`ziwei_palaces` 배선).
- 테스트: 신규 양방·데이터 순정·전수 커버 + 골격×lint 매트릭스 재통과.
- 문서: `docs/03`(결정표 행), `implementation-notes.md`·`STATE.md`.
- 금지/불변: `calc/ziwei.py`·calc/input, factcheck/safe/style/quality 로직, GATE_KEYS, docs/24(읽기 전용
  소스), 상품 토글, known-time 계산.

## 8. 후속 순서

1. (운영자) 승인 → 패킷 commit + manifest 고정(`planned/next_actor=codex`).
2. Codex 구현(§2·§3·§4) → 양방 테스트(§5) → 증거 보고(§6, no-LLM/mock 층).
3. Claude 교차리뷰(diff 전량 + 기준환경 1114/4 비악화 + 정본 정합 + 가드/factcheck 비악화 + 데이터 순정).
4. PASS 뒤 로드맵 다음: **1e**(nature/character 다단 인과 + 명리↔자미 사실특정 겹쳐읽기 — 이 정본을 프롬프트
   근거로) → 1c(폴백 골격 품질) → 1b(회고 검증, 보상 lint 선행) → Stage 1 완료 → 유료 재측정 → Stage 2.
