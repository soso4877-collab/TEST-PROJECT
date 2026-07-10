# [Codex 지시문] Q7 1단계 — 모듈 레지스트리 + 조립/게이트 (CLI/admin 배선 없음)

> 형식: 승인된 TASK_PACKET(산문판). 실행 기준 = 이 문서 + 승인된 설계 `handoff/codex-q7-design.md`(B안).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude /cross-review(라운드9). 커밋 = 리뷰 PASS 후.

## 0. 역할·금지 (기존과 동일)
- Codex 상시 금지: git commit·push·deploy·LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역
  (`render/out/`·`tmp/`·`synthetic-tmp/`·`data/`·`*.content.json`) 접근.
- `sajugen/calc/`·`sajugen/input/` 무변경(골든 불변). 가드 완화 금지 — 게이트는 사각 축소 방향만 + 양방 회귀.
- **1단계 범위 한정**: 레지스트리·조립·게이트·테스트만. CLI `--module` 옵션·admin 추천 UI(2단계)는 이번에 만들지
  않는다. 상태머신·발송 차단 무변경.
- 모순 발견 시 임의 해석 말고 정지·보고(선례: 웨이브1 v1·E10 §4 정지 — 둘 다 타당했음).

## 1. 상태(전제) — 2026-07-10 실측
- 브랜치 `codex/gunghap-relationship-quality`, 시작 HEAD = `a376f5f`(E10 라운드8 PASS까지 완료).
- 기준선(기준환경): **728 passed / 4 skipped / exit 0**. 감소 = 회귀. 샌드박스 skip 상이 가능.
- **완료(재발주 금지)**: 웨이브1 Q1~Q3(라운드6)·웨이브2 R6-1+Q4~Q6(라운드7)·E10 익명화(라운드8). 실명 잔존은
  tracked 0(학술 인용 예외 1건 — docs/00, 건드리지 말 것).
- **운영자 승인 완료(재질의 불요)**: 설계 B안 / 분량 공식 `pages=min(30,12+4N)`·`text_chars=min(10000,1000+2000N)` /
  RELATION 추천 규칙(2단계 소관) / `--module` 미지정=5모듈 전체(하위호환).
- 실측 앵커: `content/rules.py:1748` — `"work": _join("job", "wealth")` = work 섹션이 이미 job/wealth 결합.
  B안의 제공자 분리 지점. `integrated.py:197 _assemble_sections`·`:116 _compact_sparse_sections`(sparse 병합) =
  조립 일반화 지점. `delivery_quality._min_pages`(345)·`_min_text_chars`(354) = Q4 상품 매핑(모듈 공식 편입 지점).

## 2. 구현 (설계 문서의 1단계 그대로)
1. **모듈 레지스트리**: `sajugen/integrated.py`(또는 신규 `sajugen/modules.py` — 순환 import 없으면 integrated 내부 권장)에
   결정론 레지스트리 — `core`(intro·wonguk·nature·frame·flow·ziwei·together) / `love` / `job` / `wealth` / `health` /
   `gunghap`(relationship_* 전부, 2인 이상 전제) / `tail`(personal consult·closing 등). `module_schema_version` 상수 포함.
2. **work 제공자 분리**: `rules.py:1748`의 `_join("job","wealth")`를 유지하되 T["job"]·T["wealth"]를 독립 노출해
   `job`/`wealth` 모듈이 따로 선택 가능하게. **기존 work 섹션 출력 바이트 불변**(5모듈 전체=현행과 동일 문자열 —
   회귀로 고정).
3. **조립 일반화** (v2 정정 2026-07-10 — Codex 정지 보고 타당, 설계 문서의 추상 고정 순서 폐기):
   `_assemble_sections`를 `modules: list[str]` 파라미터(기본 None=5모듈 전체)로 일반화.
   **정규 순서 = 현행 순서의 필터링**: 현행 조립 순서(sections_schema 개인 순서 → relationship 순서 → closing/tail —
   `sections_schema.py:10` 주석의 의도된 독서 곡선 "도입→빌드업→개인화 피크(consult)→마무리")를 그대로 두고,
   선택 모듈에 속하지 않는 섹션만 결정론적으로 제외한다. 재배열 없음 — 설계 문서의
   `core→love→…→gunghap→consult→tail` 추상 순서는 현행과 불일치라 적용하지 않는다(이중 레짐 금지:
   같은 선택은 명시/미지정과 무관하게 같은 문서). 이로써 미지정/5모듈 전체 = 현행 완전 동일이 자동 성립.
   미선택 모듈 섹션 유입·중복 ID = 조립 실패(예외).
   **sparse 병합 (v3 정정 2026-07-10 — Codex 3차 정지 보고 타당·권장안 채택)**: 병합은 **필터링 후 현행 로직
   그대로**(경계 제한 없음). 근거: 필터링이 병합보다 먼저라 병합 입력은 전부 선택 모듈 소속 — "모듈 경계 병합
   금지"의 목적(비선택 콘텐츠 유입 방지)은 필터링이 이미 보장하고, 병합은 얇은 섹션 레이아웃 압축일 뿐이다.
   현행 tail 무조건 병합(integrated.py:132-133)·personal/relationship 그룹 병합(140-144)·기존 회귀
   (test_integrated_product.py:289) 전부 불변. **단, 게이트 모듈 커버리지(missing/unexpected_module_sections)
   판정은 병합 전 섹션 목록 기준**으로 한다(병합 후 ID 소실로 선택 모듈이 누락으로 오탐되는 것 방지 —
   판정 시점을 테스트로 고정).
4. **게이트 연동**: `delivery_quality`에 모듈 수 N 기반 하한(승인 공식) — 기존 `_min_pages/_min_text_chars` 매핑에
   integrated 모듈 프로필 편입. verify에 `selected_modules` 전달·관측. 실패 룰 신설: `missing_module_sections`·
   `unexpected_module_sections`(기존 delivery_quality_clean 안에 편입 — GATE_KEYS 우회 경로 금지). 부재 시 조용한
   통과 금지: modules 미전달 레거시 호출은 5모듈 전체로 해석(skipped 아님을 주석 명시).
5. **파라미터 소비 배선**(방법론 A-5): `build_integrated`(또는 상당 진입점)가 modules를 받아 조립→게이트→
   content.json 영속(`modules`·`module_schema_version` 포함)까지 관통. 소비처 없는 파라미터 금지.

## 3. 수용 기준 (양방)
- (하위호환) modules 미지정/5모듈 전체 → 현행 integrated_full과 **섹션 ID 리스트·본문 동일**(회귀로 고정) +
  30p/10000자 하한 유지.
- (조합) `["love"]` 1모듈 → love 외 job/wealth/health/gunghap 섹션 0 + 하한 16p/3000자. `["job","wealth"]` 2모듈 →
  하한 20p/5000자. 공식 경계 표 테스트(N=1..5, 하한-1 차단/하한 통과).
- (차단) 미선택 모듈 섹션 합성 주입 → `unexpected_module_sections` 실패. 선택 모듈 섹션 누락 → `missing_module_sections` 실패.
- (gunghap 모듈) 1인 입력 + gunghap 선택 → 조립 실패(예외). 2인 → 통과.
- (job/wealth 분리) `["job"]` 선택 시 재물 문단 부재·직업 문단 존재(그 역도) — 분리가 실제 다른 출력을 내는 분기 테스트.
- 전체 pytest exit 0, 기준선 728/4 대비 감소 0 + 신규 증가분 명시. calc/input diff 0.

## 4. 완료 보고 (여기서 멈춤)
실행 명령+출력, diff 요약, 모듈×경계 표, 하위호환 동일성 증거(5모듈 섹션 리스트 비교), 미검증(실렌더) 명시.
커밋 없이 워킹트리 유지 → 교차리뷰 라운드9. 2단계(CLI/admin)는 라운드9 PASS 후 별도.

## 범위 밖
CLI `--module`·admin 추천 UI(2단계), Q6 분류 연동 자동 추천, 실렌더, PII 잔여 3건, push.
