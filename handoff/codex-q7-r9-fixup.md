# [Codex 지시문] Q7 1단계 R9-1 수정 라운드 — module_coverage 소유권 교차검증 (2026-07-10 운영자 승인)

> 형식: TASK_PACKET(산문판). 실행 기준 = 이 문서 + `REVIEW-FEEDBACK.md` 라운드9 절(판정 정본).
> repo: `C:\Users\pc\test-project`. 구현 = Codex. 검증 = Claude 라운드9 재검. 커밋 = 재검 PASS 후 운영자.
> 이 라운드는 **R9-1 단건 수정**이다. v3 본 구현(라운드9에서 전 항목 GREEN 판정)은 재작업하지 않는다.

## 0. 역할·금지 (기존과 동일)
- Codex 상시 금지: git commit·push·deploy·sajugen 런타임 LLM 호출·PDF 재생성·`harness/profiles/local/**`·ignored 영역
  (`render/out/`·`tmp/`·`synthetic-tmp/`·`data/`·`*.content.json`) 접근.
- `sajugen/calc/`·`sajugen/input/` 무변경(골든 불변). 가드 완화 금지 — 게이트는 사각 축소 방향만 + 양방 회귀.
- **수정 범위 한정**: `sajugen/modules.py` + `tests/test_integrated_modules.py` 2파일. 그 외 Q7 동결 7파일
  (integrated.py·builder.py·rules.py·delivery_quality.py·verify.py·기존 테스트 2)은 비수정. 범위 초과가
  필요해 보이면 임의 확장하지 말고 정지·보고(선례: 웨이브1 v1·Q7 v1/v2 정지 — 전부 타당했음).
- `render/verify.py`의 `GATE_KEYS` 신설·변경 금지. R9-1 검출은 기존 `missing_module_sections`/
  `unexpected_module_sections` 룰과 `unknown_section_ids` 관측으로만 나타나야 한다(우회 경로 신설 금지).

## 1. 상태(전제) — 2026-07-10 라운드9 실측
- 브랜치 `codex/gunghap-relationship-quality`, HEAD `0b3134f`. Q7 1단계 구현 후보는 미커밋 워킹트리
  (tracked 7 + 신규 2, SHA 동결 = `handoff/tasks/q7-stage1-modules-20260710.md`).
- **라운드9 판정 = changes_requested, 미해결 R9-1 1건뿐.** manifest `status=changes_requested / next_actor=codex`.
- 기준선(기준환경, 라운드9 확정): **745 passed / 4 skipped / exit 0**. 감소 = 회귀. 샌드박스 skip 수 상이 가능
  (직전 샌드박스 실측 718/31, 총 수집 749 동일).
- **완료(재발주 금지)**: v3 §2 전 항목 — 레지스트리·work 분리·현행 순서 필터링·병합 전 커버리지·N 하한·
  게이트 편입·메타 영속/복원·신규 17건 테스트. Ruff 신규 위반 0.
- 실측 앵커: `sajugen/modules.py` `module_coverage()`(189행 근방) — 구조화 맵을 평면 목록과 교차하지만
  **맵이 주장한 (모듈, 섹션ID) 쌍 자체는 레지스트리와 대조하지 않는다**. `_modules_for_unmapped_section()`
  (173행 근방)이 소유권 SSOT 조회를 이미 구현하고 있으나 맵 미배정 ID에만 적용된다.

## 2. 결함 (라운드9 합성 프로브로 확정 — REVIEW-FEEDBACK ③ 참조)
맵이 평면 목록에 실존하는 ID를 아무 선택 모듈 소유로 선점 주장하면 검증 없이 커버리지로 인정된다.
- P1: `["love"]` 선택 + 맵 `love=[personal_love, personal_health]`(premerge 동일) → missing/unexpected/unknown 전부 [] = 세탁 통과.
- P2 대조군(정직 맵, health 미배정): unexpected=`['health']` 정상 차단 — 복원 경로만 작동한다는 증거.
- P3: 미등록 `fake_zone`을 맵이 주장 → unknown 미탐. P4: `relationship_overview`를 love가 주장 → unexpected 미탐.
- 파생: 가짜 ID 주장으로 선택 모듈의 missing까지 우회 가능 = 커버리지 게이트 양쪽 룰 전체 무력화.
발현 경로는 content.json 손상/변조/미래 구현 버그의 재렌더 — verify가 잡으라고 있는 대상이다(팬텀 파트너 QI-2026-07-04-01 계열).

## 3. 구현 (불변식 1문장 + 배선)
**불변식: 커버리지로 인정되는 (모듈, 섹션ID) 쌍은 레지스트리 소유권과 일치하는 것만이다.**
1. `module_coverage()`에서 맵이 주장한 각 섹션 ID의 소유자 집합을 레지스트리로 조회(`_modules_for_unmapped_section`
   상당 — 같은 정규화 경로 재사용, 로직 복제 금지)하고, 주장 모듈이 소유자 집합에 없으면 그 쌍을 인정하지 않는다.
2. 불인정 ID의 처분은 기존 미배정 경로와 동일: 실소유자가 있으면 실소유자로 귀속(→ 미선택 모듈이면 unexpected),
   소유자가 없으면 `unknown_section_ids`(→ unexpected 룰 실패). 이중 계상 없이 한 경로로만 흐르게 한다.
3. 정당 주장은 전부 유지: work의 job/wealth 이중 소유, `relationship_*` prefix = gunghap 전속,
   core/tail의 자기 소유 ID(예: personal_intro→core, personal_consult→tail), legacy 대표맵
   (`legacy_full_module_sections`) 무오탐.
4. 관측 가능성(선택): 원인 분리를 위해 coverage dict에 불인정 쌍 목록(예: `misattributed_section_ids`)을
   추가해도 좋다. 단 판정은 기존 두 룰로만 — 새 GATE 키·새 failure 룰 금지.

## 4. 수용 기준 (양방)
- (차단) P1 시나리오 → `unexpected_module_sections` 실패. P3(미등록 ID 주장) → unknown 검출 + 동 룰 실패.
  P4(관계 섹션을 love가 주장) → gunghap 귀속 + 동 룰 실패(gunghap 미선택).
- (차단) missing 우회: `["love"]` 선택 + 맵 `love=[fake_zone]` + premerge에 fake_zone 실존 →
  `missing_module_sections`(love 실커버리지 0)와 `unexpected_module_sections`(unknown) 동시 실패.
- (통과) 조립기 산출 맵(기존 test_module_coverage_uses_premerge_ids_not_compacted_ids), legacy 대표맵,
  work 이중 소유(job+wealth 선택 시 personal_work를 양쪽이 주장), core/tail 정당 주장 — 오탐 0.
- (경계 이웃, A-4) `personal_` prefix 유무 정규화가 교차검증에도 동일 적용되는지 1건 이상 고정
  (legacy 대표맵은 `personal_*` 형식, 레지스트리는 raw ID 형식).
- `delivery_quality.analyze` 경유 1건: P1 시나리오가 failures에 나타남(모듈 레이어 단독 아님을 증명).
- 전체 pytest exit 0, **기준선 745/4 대비 감소 0** + 신규 증가분 명시. calc/input diff 0. 수정 2파일 Ruff GREEN.

## 5. 완료 보고 (여기서 멈춤)
실행 명령+출력(passed 수/exit code), diff 요약(2파일 한정 확인), P1~P4·missing 우회 차단 증거,
통과측 무오탐 증거, 미검증(실렌더 등 기존 승계) 명시. **커밋 없이 워킹트리 유지** → Claude 라운드9 재검.

## 범위 밖
Q7 2단계(CLI `--module`·admin UI), 실렌더, 레거시 손상 번들의 실누락 증명(대표맵 복원의 구조적 한계 —
R9-1이 부분 축소할 뿐 완전 해소 아님), 다른 파일의 Ruff 기존 부채 29건, push.
