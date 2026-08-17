# 구현 상태 기록 — 2026-07-10 질문 적응형 풀이

## CLAUDE_IMPLEMENTATION_REPORT — solar-term-axis-fix-20260817 (명리 절입 시각축 교정, Claude 직접 구현)

- 판정: **구현 완료 / 별도 신선 세션 read-only 검증 요청**(운영자 승인 2026-08-17, 패킷 §0 — Codex 토큰 부재
  예외). base HEAD `0e09a35`, 미커밋. commit·push·LLM·PDF 재생성 0. manifest `review_requested / next_actor=claude`.
- 배경(결함 2개가 상쇄 중이었다): (A) lunar-python 1.4.8 절기표가 **CST(UTC+8)** 라 시민 KST 투입 시 −60분,
  (B) 진태양시를 시민시각처럼 투입해 +45.9분(2월 서울) → 합계 **−14분**. B만 고치면 −60분으로 악화된다.
- 구현(`sajugen/calc/myeongni.py` 1파일):
  - `LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS = 8` 명명 상수 + 근거 주석(매직넘버 금지, 패킷 §5-1).
  - **`_SplitAxisLunar` 프록시** — 연·월·절입(`getYear*`·`getMonth*`·`getJieQiTable`·`getPrevJie`·`getNextJie`·
    `getSolar`)은 절대축 Lunar(=`ct.utc + 8h`), 일·시(`getDay*`·`getTime*`)는 국지축 Lunar(=`ct.true_solar`)로
    위임. 미분류 이름은 `RuntimeError`(fail-closed). `EightChar(_SplitAxisLunar(...))` **한 개**를 만들고
    `build()`의 나머지 코드는 그대로 둔다.
  - ★ **패킷 §5-1 골격(두 EightChar 에서 기둥을 골라 담기)을 그대로 쓰지 않은 이유**: 십성·지세·명궁은 전부
    '일간 기준' 파생값이라, 연·월주만 다른 인스턴스에서 가져오면 **그 인스턴스의 일간**으로 십성이 계산된다.
    자시 정책(day_offset)·날짜 경계에서 두 축의 일간이 갈리므로(실측 2000-06-15 23:33 → 국지 乙 / 절대 甲)
    연주 십성이 正官↔七杀, 월주 正印↔偏印, 지세 冠带↔衰 로 조용히 뒤바뀐다(23시대 출생 ≈ 4%).
    Lunar 층에서 축을 합치면 EightChar 가 언제나 국지축 일간으로 파생값을 계산해 이 사각이 구조적으로 닫힌다.
  - 자시 `setSect(1)` 는 그대로 유지(국지축 일간에만 작용). **실측 재확인**: 4케이스×남녀 8건에서
    setSect 유무가 `getYun` 起運·대운 간지를 바꾸지 않음(기존 주석의 전제 검증).
  - 부수: 기존 Ruff 부채 `F401 datetime.timezone`(미사용 import)이 `timedelta` 교체로 해소됨.
- 검증(전부 기계 측정, 무LLM·무PDF·무과금):
  - 전체 `./.venv/Scripts/python.exe -m pytest tests/ -q` = **1227 passed / 4 skipped / exit 0**(200.69s).
    기준선 1136/4 + 신규 91 = 1227 정확 일치, 기존 감소 0, skip 불변.
  - golden `-k golden` = **28 passed / exit 0**. 골든 격자 21건의 연·월주·대운수 변경 **0건**(사전 실측으로
    §8 stop_condition 미발동 확인 후 착수).
  - `handoff/evidence/20260817-postteller-chart-survey/eot-window-measure.py` →
    `width_min_max = 0`, `width_min_mean = 0.0`, `terms_with_window = 0` (36개 절입 전수. 교정 전 최대 41+·평균 27.7).
  - 신규 `tests/test_solar_term_axis.py` **91 passed**. 교정 전 코드 대조 = **21 failed / 70 passed**
    (그중 12건은 순수 거동 RED, 9건은 신규 상수·헬퍼 부재로 인한 AttributeError — 정직 분리 보고).
  - Ruff `All checks passed!` · py_compile exit 0 · `git diff --check` exit 0.
- 영향 범위 **재실측**(재현 조건: `random.Random(20260817)`, N=3,000, 1950-01-01~2020-01-01 균등, 성별 50%):
  연주 0건 · 월주 **2건(0.067%)** · 일주 0 · 시주 0 ·
  **대운수 21건(0.700%)**. 패킷 §2-5 `fix-impact.json` 은 `N=3000 / daewoon_start_changed=17`(0.57%)이고
  **표본 추출 조건이 기록돼 있지 않아 동일 표본 재현은 불가**하다. 두 값 차이는 Poisson σ≈4.1 안(21 = 17+1σ) —
  §8 의 "0.57% 를 크게 벗어남"에 해당하지 않는다고 판단하되 **수치는 숨기지 않고 보고**한다. 월주 2건은
  경계 폭 이론치(연 0.063%)와 일치하며, 축 교정이 의도한 바로 그 구간이다.
  `data/orders.sqlite` APPROVED 0 · 발송 0(패킷 §10-2 운영자 실측)이라 소급 영향은 없다.
- **파생 결과(운영자 인지 필요) — 명리↔자미 불일치 창은 넓어지지 않고 '이동'했다**:
  `crosscheck.bazi_consistent=False` → `pipeline.calc_consistent=False` → `order_flow` **CALC_MISMATCH 주문 차단**
  (절대규칙 7). 자미(iztro)는 이번 패킷 forbidden 이라 교정 대상이 아니므로, 명리만 정확해지면 경계에서 둘이
  갈린다. **같은 스크립트로 교정 전/후를 재측정**: 3개 절입 ±40분(243분) 중 불일치 = **교정 전 47분 → 교정 후 48분**
  (총 폭 사실상 불변). 위치만 실제 절입에 맞게 이동했다(예: 2000 입춘 −13..+5분 → +1..+5분).
  즉 차단 부담이 새로 생긴 게 아니라, **fail-closed 가 이제 올바른 지점에서 자미 결함을 표면화**한다.
- 축 혼합 지점 확인: `shinsal_mod.gongmang(년주 ganzhi=절대축, 일주 ganzhi=국지축)` 은 lunar-python API 가 아니라
  **보고된 기둥 간지로 자체 산술**하므로(docs/03 line 24 결정) 리포트에 표시되는 기둥과 자기정합적이다.
  `pytest -k "shinsal or gongmang or advanced or p2"` = **34 passed / exit 0**.
- 사각 인접 탐색(방법론 A-4 — **둘 다 allowed_files 밖이라 수정하지 않고 측정만**):
  - `sajugen/calc/partner.py:154-160`(궁합 상대 명식)은 **같은 −14분 결함이 그대로 남아 있다**. 경계 5케이스 중
    **2건 오답**(2000-02-04 21:39 → 庚辰 戊寅, 정답 己卯 丁丑 / 2000-06-05 17:58 → 庚辰 壬午, 정답 庚辰 辛巳).
    ⚠ 이번 교정으로 **본인(교정됨)과 상대(미교정)가 서로 다른 축**을 쓰게 됐다 — 같은 생년월일시라도 경계에서
    결과가 갈린다(발생률 ≈ 0.06%). **후속 패킷 1순위 후보.**
  - `sajugen/calc/three_pillar.py:163-167`은 시민 KST 정오를 투입해 −60분 프레임이지만, `ensure_unambiguous_civil_date`
    가드가 절입 포함일을 먼저 차단하므로 실제 오차로 이어지지 않는다. 실측: 2000년 366일 중 **가드 차단 12일 /
    검사 354일 / 월지 불일치 0일**. 결함 아님(구조적으로 닫혀 있음) — 다만 프레임이 우연히 안전한 것이므로 후속
    패킷에서 축을 명시하는 편이 낫다.
- 미검증·미수행(정직 보고):
  - 자미두수 입춘 해상도 결함(iztro 분 미수용, 최대 103분) — 패킷 §11 범위 밖, 별도 패킷.
  - 대운수 관례(포스텔러 대비 항상 +1) — 패킷 §5-3·§10-3, 이번에 바꾸지 않음.
  - `docs/16` 품질사고 등재는 allowed_files 밖이라 하지 않았다(패킷 §10-4 운영자 결정 대기).
  - 실 PDF·실모델·육안 검수·hrun 0.
- 경계·절차: 수정 = `sajugen/calc/myeongni.py`·`tests/test_solar_term_axis.py`(신규)·`docs/03` 1행.
  추가로 패킷 §6 실행 명령이 요구한 `handoff/evidence/.../eot-window.json`(추적 파일, allowed_files 밖)이
  재생성돼 갱신됐다 — 증거 산출물이며 제품 코드 아님. `tests/test_p1.py`는 허용됐으나 변경 불요로 무수정.
- **handoff 정합**: 착수 시 `handoff.mjs validate` = `HANDOFF_VALID`(packet/notes/review SHA·base ancestor 전부 정합).
  주의 — `Get-FileHash`(원시 바이트)로 notes SHA 를 대조하면 manifest 값과 달라 보이는데, `manifest-lib.sha256File`
  이 git 과 같은 기준으로 **CRLF→LF 정규화 후 해싱**하기 때문이다(2026-07-26 실측 주석). 원시 해시로 인계 SHA 를
  대조하지 말 것. `handoff.mjs`는 repo root 가 아니라 `C:\Users\pc\.ai-harness\handoff.mjs` 에 있다.
- 검증 세션 확인 포인트: ① §6 표 5행 ② `width_min_max==0` ③ 골든 28·전체 1227/4 ④ 교차검증 완화·삭제 0
  (`month_branch_crosscheck_ok`·`year_branch_crosscheck_ok` 로직 무변경, 통과하게 만든 방향) ⑤ 십성이
  국지축 일간 기준인지 ⑥ 경계 밖 비회귀(축 분리 no-op) ⑦ 프록시 축 배정표가 lunar-python 실제 호출 전수를 덮는지.

## CLAUDE_IMPLEMENTATION_REPORT — ilgan-personality-wiring-20260720 (1e, Claude 직접 구현)

- 판정: **구현 완료 / 신선 Codex read-only 검증 요청**. base HEAD `4837605`, commit·push·LLM·PDF 없음.
  manifest `review_requested / next_actor=codex`.
- 배경: 명리 성격이 라벨 위주, 10천간 일간별 고유 성격 테이블 부재·다단 인과 부재. ★일간 물상 성격은 **B급**
  (자미 化氣 A급과 다름) → 비단정 배선.
- 구현:
  - 신규 `content/myeongni_persona.py` = docs/25 단일 소스: `GAN_PERSONA`(10천간 상징·core·shadow)·
    `SINGANG_MODIFIER`(신강/신약/중화 결 발현 방향)·`ELEM_LACK`(오행 결핍↔갈망 양가). 정본 밖 성격어 생성 0.
  - `rules.py`: `_ilgan_persona_parts` 헬퍼(문형 `_pick` 3종·`_J` 조사). `character`를 다단 인과로 재배선
    (일간 성격 lead → 신강 modifier가 '이 결'을 방향으로 → 겉/속 십성 → 신살). `strength` 없는 오행을 정본 양가로.
  - `llm_sections.py`: `_COMPOSE_GUIDE["nature"]` 다단 인과+없는오행 양가+물상 비단정 지시. `_LAYER_WEAVE`
    사실특정 확증으로.
- advisor 교차점검 2건 선제 수정: (1) **신약 재서술 중복**(character modifier↔strength) → modifier는 결
  방향만, '약함 아님' 재서술은 strength 전담(무중복 회귀 테스트). (2) core/shadow가 docs/25 §1 축 일부 생략
  (자미 B-1 패턴) → docs/25 §1에 **코드 배선 매핑 승인**(core/shadow=축의 관형형 대표 서술) 명시 + core 보강
  (甲 정직·乙 섬세) + core 축 앵커 테스트.
- 검증(round-2): 전체 `pytest tests/ -q` = **1136 passed / 4 skipped / exit 0**(기준선 1126/4 +10 신규·감소 0·
  skip 불변), golden **28**. 변경 3파일 + 신규 2파일 Ruff·py_compile·diff-check exit 0. calc/input diff 0.
  GATE_KEYS·factcheck·render 무변경. 프롬프트(가이드·weave) 변경이 바이트 핀 테스트 미파손.
- 신규 테스트 10(tests/test_myeongni_persona.py): 10천간 전수·**docs/25 §1-1 렌더 계약 전수 오라클(표시상징+
  core/shadow 필수축)**·데이터 순정+비공허성·신강 modifier 분기+승인 방향·**신약 강약 프레임 0·무중복 회귀**·
  없는오행 양가·character 다단 인과 비-no-op·**persona 가드 전수(style+register+raw_calc+safe) 격리**·비단정 톤·fail-closed.
- **round-2 수정(Codex CHANGES_REQUESTED B-1/B-2/B-3 해소)**: (B-1) symbol이 §1 보조 상징 누락 → docs/25
  §1-1 **코드 렌더 계약** 신설(표시 상징 1개 style-safe + §1 전통 상징 보존, 등불=style_lint라 촛불로 승인
  매핑). (B-2) core/shadow가 §1 축 다수 생략 → core/shadow를 §1 축 손실 없이 담게 보강(자기과신·심미·공명정대·
  문예·대국관·휘둘림·구속·관찰력·기지·직관 등) + **전수 오라클**(`test_render_contract_symbol_and_axes_frozen`이
  docs/25 §1-1 표시상징+core/shadow 필수축을 독립 동결). (B-3) 신약 modifier "여린 편" 약함 프레임 ↔ strength
  "나약함 아님" 충돌 → modifier에서 강약 프레임 제거(발현 방향만: 신강=주도 / 신약=조율·수용·신중 / 중화=균형),
  회귀를 exact count → 강약 프레임 0 + 승인 방향 존재로 강화. 신규 테스트 11→10(오라클 통합).
- **round-2 회귀 사고(근본원인 2층)**: core 축 보강 중 戊 core에 `큰 그림`을 넣었는데 이는 `register_lint`
  하드 금칙(`big_picture`)이라, 戊 일간 차트의 consult(nature base_text 소비)가 guard-fail→폴백해 compose
  개수 계약 테스트 19건 실패. (결함) `큰 그림`→`넓은 시야`(대국관, clean). (감지 갭) persona 격리 테스트가
  style_lint만 돌려 register 금칙을 못 잡음 → **성격 문안이 guarded 챕터로 흐르므로** 테스트를 register/
  raw_calc/safe까지 검사하도록 강화(`test_persona_output_passes_customer_guards`). 전 persona 정본 가드 전수 스캔=1건뿐.
- 미검증: 실모델 서술 품질·실 PDF 육안·비용(운영자 승인 유료 재run 몫).
- Codex 검증 포인트(round-2): docs/25 §1-1 렌더 계약↔persona 정합(표시상징·core/shadow 필수축 전수), 사실 슬롯
  불변, 정본 밖 성격어 유입 0, 가드/게이트/calc 완화 0, 신약 강약 프레임 0·무중복, 비단정 톤.

## CLAUDE_IMPLEMENTATION_REPORT — ziwei-temperament-wiring-20260717 (Claude 직접 구현)

- 판정: **구현 완료 / 신선 Codex read-only 검증 요청**(운영자가 Claude 직접 구현 승인 2026-07-17).
  base HEAD `461a0e9`, commit·push·LLM·PDF 없음. manifest `review_requested / next_actor=codex`.
- 배경: 자미 별이 이름·밝기·사화만 나열되고 기질 의미가 없어 성격 서술이 얕음(최대 결손).
- 구현:
  - 신규 `sajugen/content/ziwei_temperament.py` = docs/24 §1~§3 단일 소스 테이블. 14주성×{化氣,
    핵심기질(관형형),그늘(관형형)} + 밝기 3단(廟旺=뚜렷 / 得利=무난 / 陷=눌림, 平閒不=중립 생략) +
    사화 4방향(록/권/과/기). 정본 밖 별-의미 생성 0(fail-closed). 化氣 한자 미노출(순한글).
  - `rules.py`: import + `_palace_temperament(p)` 헬퍼(별 이름·밝기·사화 사실 슬롯은 `_stars_full`이
    그대로, 기질 '의미'만 정본에서 덧붙임). core 문형 3종 + 밝기 프레임 3종 + 사화 프레임 3종을 전부
    `_pick`(md5 결정론, 별 이름 키)으로 다양화 → verbatim 반복 방지. 소비처 = `_palace_para`(핵심 궁).
    `ziwei_summary`는 오리엔테이션만(주성 상세는 palaces 전담) → 한 챕터(NT["ziwei"]=summary+palaces)
    안 명궁 기질 이중 서술 방지.
  - advisor 교차점검으로 2건 수정: (1) summary×palaces 명궁 기질 중복 제거, (2) 밝기·사화 고정 문구
    verbatim 반복 → 별별 `_pick` 문형 분산(운영자 반려 사유였던 "AI틱 반복" 선제 차단).
- 실측(계산 프로브·무LLM·무과금): 실 엔진 14주성 이름(거문·무곡·염정·자미·천기·천동·천량·천부·천상·
  칠살·탐랑·태양·태음·파군)이 정본 키와 정확 일치. 14주성 렌더 문장 육안 자연스러움 확인.
  joined `chapters["ziwei"]`에 safe/quality/customer_meta_lint = clean, 명궁 주성 core 중복 count=1.
  내 기질 문안 14주성 style_lint = clean(em dash·가운뎃점·시적비유·반복 유입 0). 챕터 기존 불릿 `· `·
  구분자 ` — `는 이 배선과 무관한 골격 조판(내 추가분 아님).
- 검증(round-2): 전체 `pytest tests/ -q` = **1126 passed / 4 skipped / exit 0**(기준선 1114/4 +12 신규·
  감소 0·skip 불변), golden **28**. 변경 3파일 + 신규 2파일 Ruff `All checks passed!`·py_compile·diff-check
  exit 0. calc/input diff 0. calc/ziwei·factcheck·GATE_KEYS 무변경(사실 슬롯 불변).
- 신규 테스트 12(tests/test_ziwei_temperament.py): 14주성 전수 커버·**化氣 docs/24 오라클**·**사화 4축
  동결**·엔진 이름 정합·데이터 순정(길흉/예측/성별 토큰 0·비공허성)·기질+밝기+사화 비-no-op·**밝기/사화
  문형 분산(반복 방지)**·공궁/정본밖 fail-closed·joined 챕터 가드·내 문안 style 격리·**명궁 기질 무중복 회귀**.
- **round-2 수정(Codex CHANGES_REQUESTED B-1/B-2 해소)**: (B-1a) `hwagi`를 docs/24 §1 化氣 그대로
  보존 — 천부 `印·庫`(庫 복원)·태양 `貴(官祿主)`·칠살 `將(肅殺)` 등 축약 제거. (B-1b) `SIHUA_DIRECTION`을
  docs/24 §3 4방향 축 손실 없이 확장(화록 기회·화권 경쟁/강화·화과 품격·화기 결핍/막힘 복원). (B-2)
  `test_hwagi_matches_docs24`(14 化氣 오라클)·`test_sihua_direction_preserves_docs24_axes`(4축 동결) 신설,
  데이터 순정에 hwagi·성별(여성/남성) 토큰 + 비공허성(심은 금칙 검출) 추가. 신규 테스트 10→12.
- 미검증: 실모델 자미 서술 품질·실 PDF 육안·비용(운영자 승인 유료 재run 몫).
- 검토 포인트(Codex round-2): docs/24↔ziwei_temperament 化氣·사화 손실 0 정합, 사실 슬롯 불변, 정본 밖
  별-의미 유입 0, 가드 완화 0, joined 챕터 중복 0.

## CODEX_IMPLEMENTATION_REPORT — temporal-retry-format-feedback-20260717

- 판정: **EVIDENCE_SPLIT_PASS / 구현 완료·Claude 기준환경 교차리뷰 요청**. 시작 manifest는
  `HANDOFF_VALID`, packet SHA `8af5937e…666b`·notes/review SHA 일치,
  `status=planned / next_actor=codex`였고 HEAD `d55a006`에서 base `0c93f98` ancestor를 확인했다.
  시작 워킹트리는 clean이었으며 commit·push는 실행하지 않았다.
- RED 실증: 변경 전 `tests/test_temporal_month.py` 집중 실행은 **6 passed / 5 failed**였다.
  `AnthropicBackend.compose`의 `feedback_fix` 부재, helper 단일 set 반환, known-time 재시도가
  `"신사월"`을 회피형 `feedback`으로 전달하는 현행 오되먹임을 각각 직접 재현했다.
- 구현:
  - `builder._retry_feedback_labels`를 `(avoid, fix)` 두 set 반환으로 바꿨다. known-time의
    `month_notation`·`temporal`·`relative_month_boundary`는 `why`가 있을 때 fix로 보내고,
    safe/style/factcheck 및 `why` 없는 예외 finding은 기존 raw label을 avoid로 유지한다.
  - 재시도 루프는 avoid 8개·fix 6개를 독립 누적하고 `_compose_one`이 지원 백엔드에만
    `feedback_fix`를 전달한다. 기존 backend 호환 가드는 유지했다.
  - `llm_sections`의 Protocol·RuleBackend·AnthropicBackend 시그니처에 `feedback_fix`를 추가하고,
    기존 회피 블록 뒤에 `형식 교정 … 고쳐 다시 써라` 블록을 신설했다. 값이 없는 첫 호출의
    user prompt는 불변이며 회피·교정 블록은 한 재시도에서 공존할 수 있다.
  - 삼주는 기존 고정 라벨만 avoid에 두고 fix는 빈 set으로 유지해 raw 토큰·`why` 누출 0이다.
    temporal/factcheck/safe/style 및 render 게이트 로직은 수정하지 않았다.
- 양방·비-no-op 테스트: 프롬프트에서 교정 정답 형식이 fix 블록에만 있고 `쓰지 말고` 블록에는
  없음을 고정했다. temporal 3타입→fix, safe+fact→avoid, `why` 누락→avoid, 삼주 고정 라벨·누출 0,
  builder 실제 attempt=2가 `feedback=None / feedback_fix=why`로 호출되는 팬텀 배선 방지 테스트를 추가했다.
- 검증:
  - 관련 회귀 5파일: **69 passed / exit 0**.
  - 전체 `.\.venv\Scripts\python.exe -m pytest tests\ -q`: **1086 passed / 32 skipped / exit 0**.
    현재 Codex 환경의 직전 기준 1082/32에 신규 4개가 정확히 더해졌고 총 수집은 1118이다.
    기준환경 기대는 기존 1110/4 + 신규 4 = **1114 passed / 4 skipped**이며 Claude가 확정한다.
  - golden: **28 passed / exit 0**.
  - 변경 Python Ruff `All checks passed!`, py_compile·`git diff --check` exit 0,
    calc/input diff 0. 구현 diff는 제품 2파일+테스트 1파일, **197 insertions / 19 deletions**다.
- 금지·미검증: API/LLM·PDF 재생성·local profile·ignored 고객 산출물·commit·push·deploy 접근 0.
  실모델 폴백률 감소와 기준환경 1114/4는 각각 운영자 승인 유료 재run·Claude 교차리뷰 몫이다.

## CLAUDE_REVIEW — offdomain-zodiac-guard-20260715 (2026-07-15, 라운드2 = CODE_PASS)

- 판정 = **CODE_PASS, 미해결 블로커 0**(정본 = REVIEW-FEEDBACK 라운드2 절). B-1 해소: `followup/answer_gate.py`에 `western_astrology_lint` 배선(+7), 라운드1 유출 입력 재실행 → **ok=False·rule=western_astrology**(비-no-op), 자미 정상어 오탐 0. 변경 2파일 순수 추가, **라운드1 19파일 SHA 불변**. 전체 **1110 passed / 4 skipped / exit 0**(1108+2·감소 0·skip 불변), golden 28, Ruff/py_compile/diff-check GREEN, calc/input 0, 경계 무변경. manifest `verified/user`. Codex 라운드1+2 구현 18파일 미커밋 = 운영자 checkpoint 대기.

## CLAUDE_REVIEW — offdomain-zodiac-guard-20260715 (2026-07-15, 라운드1)

- 판정 = **CHANGES_REQUESTED, 블로커 1건**(정본 = REVIEW-FEEDBACK 2026-07-15 절). 핵심 가드·개인/궁합/최종 PDF 배선은 사양 충족 GREEN(전체 1108/4·golden 28·SHA 핀 독립 일치·오탐 0·경계 무변경)이나, **followup 텍스트 발급 게이트(`answer_gate.check`)에 `western_astrology_lint` 미배선** → pdf=False followup 답변이 프롬프트 억제만으로 유출 가능(실행 확증: 통과 픽스처 `_DIRECT`에 `사자자리` 주입해도 ok=True). 수정 = answer_gate 배선+양방(생성 측, 완화 0). manifest `changes_requested/codex`.
- 비블로커: `verify._verapdf_ua1` 범위 밖 죽은코드(F841) 정리(동작 보존, checkpoint scope 인지). 발주 `098b737` 메시지↔manifest 레이스는 이 판정에서 정리.

## CODEX_IMPLEMENTATION_REPORT — offdomain-zodiac-guard-20260715

- 판정: **EVIDENCE_SPLIT_PASS / 구현 완료·Claude 기준환경 교차리뷰 요청**. 시작 manifest의 packet/notes/review SHA가 모두 일치했고 HEAD·base ancestor는 `da0a6368260fcc07c5aaf5c018a9625bb2fd6a59`였다. 시작 dirty 3개는 활성화 파일(manifest·packet·`sajugen/STATE.md`)뿐이며 구현 파일과 겹침 0이었다. commit·push는 실행하지 않았다.
- 루트커즈 RED:
  - 합성 프로브 3종은 수정 전 모두 `safe=0`·`style=0`·`external_domain=0`이었고, `safe_lint.RULES` 9개에 별자리·황도·점성 토큰 규칙은 0개였다. 문제는 기존 룰 완화가 아니라 전용 도메인 가드 미커버다.
  - 유료 run의 우연 catch는 허용된 기록에 `safe=1` 카운트만 남고 raw match가 영속되지 않아 정확한 패턴은 **확정 불가**다. ignored 산출물은 열지 않았다. 합성 `별자리가 운명이 정해졌다는 뜻은 아닙니다`는 `운명론/운명이 정해졌`에 걸려, 별자리와 무관한 이웃 안전표현이 우연히 잡을 수 있음을 재현했다.
- 구현:
  - 신규 `western_astrology_lint.py`에 황도 12궁 12종(사수/궁수 별칭 포함 13표기) + `별자리`·`황도`·`점성`·`점성술` 고정 토큰 hard finding을 추가했다. `관록궁 자리`·`자리를 잡다`·`사자(獅子)`·`게`·`처녀궁`·`물고기`·자미 `주성/별`은 clean이다.
  - 개인 builder 후보·재작성·룰 골격·최종 집계와 궁합 후보·룰 폴백에 전용 lint를 배선했다. `_COMPOSE_SYSTEM`과 closing guide에 생성 금지를 추가했고 known SHA 핀을 `76e1645d…fa32d`로 갱신했다. 삼주 full-request factcheck도 GREEN이다.
  - 최종 PDF 전 페이지(표지·목차·본문·부록) 스캔 `western_astrology_clean`을 `GATE_KEYS` 23번째 키로 추가했다. hverify/hsummary 관측, integrated/relationship 레이아웃 재시도 판정, docs/20·docs/22·골격 매트릭스를 함께 동기화했다. 실제 PyMuPDF 임시 PDF 텍스트층에서 `western_astrology_clean=False`·`gate_pass=False`를 확인했다.
  - 사소한 발견: 변경 Python Ruff GREEN 검사에서 `render/verify.py`의 기존 미사용 변수 `base`(F841) 1건이 드러나 동작을 보존하며 대입만 제거했다. 가드 의미·기준과 무관한 기계 정리다.
- 검증:
  - 집중 양방·배선: **213 passed / 1 skipped / exit 0**.
  - 전체 `.\.venv\Scripts\python.exe -m pytest tests\ -q`: **1080 passed / 32 skipped / exit 0**. 동일 환경 직전 1043/32 대비 신규 +37·기존 감소 0·skip 불변, 총 수집 1112다. 기준환경 기대는 1071/4+37=`1108/4`이며 Claude가 확정한다.
  - golden **28 passed**, 변경 Python Ruff `All checks passed!`, py_compile·`git diff --check` exit 0, calc/input diff 0.
- 금지·미검증: API/LLM·운영 PDF 재생성·local profile·ignored 고객 산출물·commit·push·deploy 접근 0. pytest의 PII-free 임시 PDF 외 PDF 생성 0. 기준환경 `1108/4`와 실모델 억제 효과는 각각 Claude 교차리뷰·운영자 승인 유료 재run 몫이다.

## CODEX_IMPLEMENTATION_REPORT — beta-1-hverify-module-contract-20260712

- 판정: **EVIDENCE_SPLIT_PASS / 구현 완료·Claude 기준환경 교차리뷰 요청**. 활성 packet §2~§7.1의
  하네스 원자 배선과 합성 양방·경계 회귀를 완료했다. commit·push는 실행하지 않았다.
- 기준/HEAD 경계: 시작 시 manifest 고정 base와 HEAD는 `2d91933`이었고 packet SHA
  `15030847…2720ce8b`, notes/review SHA, `next_actor=codex`가 일치했다. 작업 중 외부에서 시작 시 이미
  dirty였던 활성화 3파일(manifest·packet·`sajugen/STATE.md`)만 `519fc61`로 commit/push해 HEAD가
  이동했다. 구현 허용 파일과 겹침 0, 고정 SHA·manifest 내용 불변이며 이 커밋은 Codex 작업으로
  주장하지 않는다. 현재 구현 diff는 `519fc61` 위 미커밋 8파일이다.
- 근본원인 실측:
  - `hverify_pdf.py`의 `V.verify()` 호출이 제품에 이미 존재하는 `selected_modules`·
    `module_sections`·`premerge_section_ids` 세 인자를 전달하지 않아, 명시 4모듈도 제품 레거시
    기본 5모듈로 복원됐다.
  - `hrun.py` 재생성 argv에 `--module` 소비처가 없고, `hsummary.py`는 적용 모듈/하한 4종과
    pytest skipped를 버려 부분 배선을 사후 증거로도 발견할 수 없었다.
- 수정 파일과 이유:
  - `scripts/hprofile_check.py`: 제품 `sajugen.modules` 정본으로 `modules` 명시 계약을 검증한다.
    현재 schema, `module_sections`, `premerge_section_ids`가 한 원자로 없거나 빈/미등록 모듈이면
    PII-free 오류 코드로 fail-closed한다. `modules` 미지정은 세 verify 인자를 None으로 유지한다.
  - `scripts/hverify_pdf.py`: PDF 존재 검사보다 먼저 계약을 닫고, 세 모듈 원자를 함께 `V.verify`로
    전달한다. verify 응답의 선택/schema 역불일치도 gate 실패로 닫고 적용 하한 4종을 올린다.
  - `scripts/hrun.py`: 실행 없는 `_regen_command()`를 분리해 명시 모듈을 반복 `--module` argv로
    구성한다. 계약 오류면 3중 잠금이 열려도 `_regen_pdf`/subprocess 전에 차단한다. pytest quiet
    summary에서 passed와 skipped를 함께 파싱한다.
  - `scripts/hsummary.py`: 제품 enum으로 제한한 `selected_modules`와 비음수 정수
    `module_schema_version`·`minimum_pages`·`minimum_text_chars`를 JSON/MD에 보존한다.
  - `tests/test_harness.py`: 29쪽 4모듈(하한 28) 통과/레거시(하한 30) 실패, gunghap 혼입,
    증거 누락, 빈/미등록 모듈, schema 불일치, regen 사전 차단, 반복 argv/레거시 무플래그,
    pytest skipped, hsummary 4종을 합성 PII 0으로 고정했다.
  - `harness/profiles/integrated_full.example.yml`: 저장 주문 meta에서 복사할 4모듈 원자 예시를 추가했다.
  - `docs/20-gate-coverage.md`, `docs/16-quality-incident-ledger.md`: 하네스 경계 계약과
    HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP의 표면/감지 시스템 2층 원인을 기록했다.
- 실행 검증:
  - 집중: `tests/test_harness.py + tests/test_gate_registry.py` = **37 passed / 1 skipped / exit 0**.
  - 전체 `.\.venv\Scripts\python.exe -m pytest tests\ -q` = **1043 passed / 32 skipped / exit 0**.
    동일 환경 직전 notes 기준 1033/32 대비 신규 +10·기존 감소 0, 총 수집 1075다. 기준환경
    1061/4에는 신규 10을 합친 **1071/4**가 기대값이며 Claude 환경이 확정한다.
  - golden `-k golden` = **28 passed / exit 0**.
  - 예시 프로파일 검사 = `ok=true`, 4모듈/schema 1/커버리지 증거 count 관측.
  - 변경 Python 5파일 Ruff `All checks passed!`, py_compile exit 0, `git diff --check` exit 0,
    `git diff --exit-code -- sajugen` 및 `git status -- sajugen` 출력 0(제품 구현 diff 0).
- 금지/미검증: API·LLM·PDF 재생성·hsweep·local profile·ignored 고객 산출물·commit·push·발송 접근 0.
  실제 합성 모듈 제한 PDF의 hrun/hverify 1회는 packet §7.3에 따라 Claude PASS 뒤 운영자 별도 지시
  대상이며 이번 EVIDENCE_SPLIT_PASS에 포함하지 않는다.

## 하네스 모듈 계약 교차리뷰 — 2026-07-14 (검증 세션, 리뷰어 Claude 신선 컨텍스트)

- 판정: **승인(CODE_PASS)** — 미해결 블로커 0. 정본 = `REVIEW-FEEDBACK.md` 최상단 절.
- 기준환경 전체 pytest **1071 passed / 4 skipped / exit 0**(226.51s), golden **28 passed** — 기준선 1061/4 +10·감소 0·skip 불변. Codex 기대값 정확 일치.
- **제품 diff 0**(하드 경계): `git diff -- sajugen/` 0 + untracked 0. 변경 10파일 전부 하네스·테스트·문서·handoff.
- 배선: hverify가 3원자(`selected_modules`·`module_sections`·`premerge_section_ids`)를 `V.verify` 전달, 레거시 None→제품 5모듈 복원(회귀 0). 계약은 제품 `sajugen.modules` 정본 fail-closed(PDF 검사보다 먼저·조용한 보정 없음).
- **자문 사각 확인(소스)**: 테스트가 `V.verify` mock이라, 실 `verify.py:484-485` 시그니처·`719-720` analyze 전달을 소스로 확인 → A-5 팬텀 재발 아님. 런타임은 §7.3.
- §4 양방·비-no-op: 4모듈=28p / 레거시=30p(captured kwargs로 전달 실증·제품 module_minimums 실호출), fail-closed(3중잠금 열려도 regen 차단=pytest.fail), gunghap 혼입 차단, argv, pytest.skipped 보존, hsummary 4종.
- 정적: Ruff 5 py All checks passed·py_compile·diff-check exit 0. 경계 read-only 8파일 시작=종료 불변.
- HEAD 경계: base `519fc61`은 리뷰어(Claude) 재활성 커밋, Codex는 그 위 미커밋 8파일뿐(commit·push 0 실측).
- 미검증(판정 밖): 실 V.verify 통과 합성 픽스처 hrun 1회 = §7.3 운영자 몫. 다음 manifest `verified/next_actor=user`.

---

## CODEX_IMPLEMENTATION_REPORT — three-pillar-real-model-quality-followup-20260714

- 현재 상태: 활성 packet §2~§5 구현과 Codex 자체 검증 완료. 실제 HEAD는 활성화 커밋
  `74e94e59d5803c4249a4a373cace65f078003627`이며 시작 워킹트리는 깨끗했다. commit·push는 만들지 않았다.
- 구현 전 루트커즈 실측(no-LLM/mock, PII 0):
  - `intro`: 삼주 파생 system에도 금칙 예시 `운명이 정해졌다`와 섹션 예고 예시 `이 풀이는 …`가 남고,
    공용 기준시점도 `이 풀이의 …`로 시작해 관측 메타 어간을 최종 요청에 직접 재노출했다.
  - `nature`·`consult`: 삼주 override가 시간 의존 내용을 “제외했다는 범위를 짧게 설명”하라고 요구하면서
    누락된 시간 자리를 호명하지 말라는 출력 계약은 없어 `시주` 발화를 유도·미억제했다.
  - `flow`·`consult`: 삼주 기준시점 user 블록이 `오늘은 … 7월 …`, `7월부터 12월`을 직접 넣었지만
    삼주 분기에는 맨몸 숫자 월 금지가 없었다. mock 캡처에서 `7월` 3회·`12월` 1회를 재현했다.
  - 조사: 삼주 `nature`의 `연주 {year_gz}와 월주 {month_gz}가 … 일주 {day_gz}가` 한 문형만
    기존 `_josa/_J` 소비처를 우회했다. 합성 정축·임신 값에서 `정축가`·`임신가`를 RED로 재현했다.
- 수정 파일과 이유:
  - `sajugen/content/llm_sections.py`: known 원문은 유지하고 삼주 파생 system에서 관측 금칙 예시를
    중립화했다. override에 내부 범위 안내 비복제·누락 자리 비호명 계약을 추가하고, 삼주 temporal 분기는
    기준일 숫자 월을 넣지 않으며 근거 없는 달을 해 단위로만 말하게 했다.
  - `sajugen/content/rules.py`: intro·nature·consult의 메타 유도 문구를 직접 화법으로 바꾸고,
    일간·연주·월주·일주 조사를 `_J`로 결정했다. Ruff 완료 조건을 위해 같은 허용 파일의 기존
    F541 16건과 F841 1건도 출력 바이트·로직 불변인 기계 정리로 함께 제거했다.
  - `sajugen/render/templates/report.html.j2`: advisory 표지 h1에 keep-all 3종만 추가했다.
  - 테스트 3파일: 폴백 4장 SDK 경계 캡처, known SHA 핀, 받침 유무 조사 표·실골격 양방,
    병기/mojibake 부재, h1 HTML CSS 계약을 추가했다. 기존 `test_three_pillar_fallback_axes` 3종은 유지했다.
- 실행 검증:
  - 구현 전 RED: prompt 4건, 실제 nature 조사 1건, h1 CSS 1건 실패; 조사 헬퍼 표 6건 통과.
  - 수정 후 핵심 `17 passed`, 인접 5파일 `81 passed`, 전체
    `.\.venv\Scripts\python.exe -m pytest tests\ -q` = **1033 passed / 32 skipped / exit 0**.
    이 환경 직전 1021/32 대비 +12·기존 감소 0이며, 기준환경 기대 1061/4와 총 수집 1065가 일치한다.
  - 골든 **28 passed**, 변경 Python 5파일 Ruff `All checks passed!`, py_compile exit 0,
    `git diff --check` exit 0. known `_COMPOSE_SYSTEM` SHA·known user bytes 핀 GREEN.
- 불변·미검증: calc/input·factcheck/safe/style·`render/verify.py`·`GATE_KEYS` 변경 0.
  API/LLM·운영 PDF 재생성·local profile·고객/ignored 산출물·commit/push/deploy 접근 0.
  실모델 폴백률 감소와 실제 PDF 조사·표지 육안 개선은 운영자 승인 유료 재run/Claude 환경 몫이며
  이번 CODE_PASS에 포함하지 않는다.

---

## 삼주 실모델 품질 후속 교차리뷰 — 2026-07-14 (검증 세션, 리뷰어 Claude 신선 컨텍스트)

- 판정: **승인(CODE_PASS — no-LLM/mock 층)** — 미해결 블로커 0. 정본 = `REVIEW-FEEDBACK.md` 최상단 절.
- 기준환경 전체 pytest **1061 passed / 4 skipped / exit 0**(241.31s), golden **28 passed** — 기준선 1049/4 대비
  +12·감소 0·skip 4 불변(passed→skip 은닉 0). Codex 기대값 1061/4와 정확 일치.
- 정적: 변경 5 py Ruff **All checks passed**(rules.py 부채 완전 해소) · py_compile 5 exit 0 · diff-check 0 · calc/input 무변경.
- 억제 강화는 **생성 측 한정**: `llm_sections.py` 전 변경이 삼주 게이팅/삼주 파생 system 전용이고 known
  `_COMPOSE_SYSTEM`·temporal else-branch 바이트 불변(SHA 핀 GREEN). factcheck/safe/style·`render/verify.py`·`GATE_KEYS` 미변경.
- §5 양방·비-no-op: 억제 지시 SDK 경계 realized 캡처(누락자리 비호명 소비 증명·A-5 팬텀 아님), 조사 `_J`
  production `build_all` 실골격 양방(`정축이`/`무는` vs `정축가`/`무은`·병기·mojibake 부재), 표지 h1 CSS 계약. Codex 구현 전 RED 재현.
- **비차단 scope 플래그**: rules.py 기존 Ruff 부채(F541 16+F841 1) packet scope 밖 정리 — 바이트 불변 검증됨
  (F541 자명·`day_sg` 미사용·golden 28), "변경 Python Ruff GREEN" 완료 조건 충족. checkpoint 시 운영자 scope 인지.
- 경계 스냅샷: 리뷰어 read-only 7파일 시작/종료 SHA 전수 일치(무변경). 리뷰어 편집은 허용 4파일만.
- 미검증(판정 밖): 실모델 4챕터 폴백률 감소·실 PDF 조사 육안·표지 개행 조판 = 운영자 승인 유료 재run(§6·§8) 몫.
- 다음: manifest `verified / next_actor=user`. 운영자 checkpoint = scope 확인·commit 여부·**유료 재run 재측정**. 통과 전 발송 금지.

---

## CODEX_IMPLEMENTATION_REPORT — three-pillar-llm-grounding-fix-20260713

- 현재 상태: 승인 packet 구현과 Codex 자체 검증 완료. manifest를 `review_requested / next_actor=claude`로 전환해 신선 교차리뷰를 요청한다. commit은 금지 계약에 따라 만들지 않았고 HEAD는 `c4cd93b17421c408a1757b387a772a7f2365c2f3` 그대로다. <!-- Claude 교차리뷰 정정 2026-07-14: 원본 보고의 full SHA(c4cd93b17421f781…)는 short prefix만 정확했고 뒤가 불일치라 실제 HEAD로 교체 -->
- 근본원인 실측:
  - 삼주 compose system·override·공용 시간 닻에 현재 근거와 무관한 고정 예시 간지·금칙 개념·월간지 형식 요구가 들어 있었고, 장별 근거 슬롯보다 공통 출처 목록이 넓었다.
  - 가드가 거부한 원시 토큰을 retry feedback에 다시 넣어 다음 요청의 유도원으로 만들었다.
  - 삼주 룰 폴백은 `concern_text`를 받지 않아 복합 고민 축을 잃었고, 시기 축을 보장할 결정론 문장이 없었다.
  - `run_generation` usage snapshot은 성공 저장 뒤에만 있어 생성 예외·provenance·계산 불일치의 조기 반환에서 collector와 함께 유실됐다.
  - 사고의 `InstructorRetryException` 내부 원인은 사후 확정 불가다. 합성 실측상 schema 오류와 일시 API 오류가 같은 외부 예외로 래핑됐고, 기존 요청에는 strict schema가 없었다.
- 수정 파일과 이유:
  - `sajugen/content/llm_sections.py`: 삼주 고정 예시 제거, 긍정형 근거 계약, 삼주 전용 시간 닻, 장별 source scope API 전 fail-closed, direct strict classifier와 응답 직후 usage 기록.
  - `sajugen/content/report_context.py`: 장별 삼주 fact source 단일 매핑과 “출처 ID는 근거 밖 사실 생성 권한이 아님” 계약.
  - `sajugen/content/builder.py`: 장별 source 전달과 삼주 retry feedback 고정 사유화. 거부된 토큰 원문은 재전송하지 않는다.
  - `sajugen/content/rules.py`: `concern_text` 배선, 기존 축 추출기 재사용, 실제 세운 연도 기반 시기·행동 최소 골격. 월운 값은 새로 노출하지 않는다.
  - `sajugen/order_flow.py`: 생성 시작 뒤 모든 종료 경로에서 최신 report에 PII-free usage만 병합하고 성공 중복 저장을 생략.
  - `tests/test_unknown_time_provenance_gate.py`, `tests/test_three_pillar_fallback_axes.py`, `tests/test_integrated_order_flow.py`, `tests/test_sdk_retry_policy.py`: 프롬프트·금칙/정상 양방·복합/단일/무축·오류 usage·strict parse 경계 회귀.
  - `docs/16-quality-incident-ledger.md`, `sajugen/STATE.md`: 사고 액션 상태와 실모델 미검증 경계 갱신.
- 실행 검증:
  - 집중: SDK `14 passed`, order flow `11 passed`, unknown-time provenance `34 passed`, fallback axes `3 passed`; 인접 회귀 `60 passed / 1 skipped`.
  - 전체 `.\.venv\Scripts\python.exe -m pytest tests\ -q`: **1021 passed / 32 skipped / exit 0**. 이 환경 기준선 1008/32 대비 +13, passed 감소 0. Claude 기준환경 1036/4와 skip 수는 분리 증거다.
  - `.\.venv\Scripts\python.exe -m pytest tests\ -q -k golden`: **28 passed / exit 0**.
  - 변경 Python 8파일 Ruff GREEN. `rules.py` 전체는 기존 부채 F841 1건+F541 16건으로 exit 1이며 HEAD 원본과 코드별 개수가 동일해 신규 위반 0이다.
  - 변경 Python 9파일 `py_compile`: exit 0. `git diff --check`: exit 0.
- 불변·미검증: calc/input·factcheck·safe/style·`render/verify.py`·게이트 기준 변경 0. API/LLM·PDF 재생성·고객 데이터·local profile·commit/push/deploy 접근 0. 실모델 `gate_pass=True`, 실제 PDF, 300dpi 육안과 비용 재측정은 운영자/Claude 후속이다.
- 사소한 절차 기록: 초기 `handoff/` 파일명 탐색 1회가 필수 제외 글롭 없이 실행됐으나 검색 범위가 안전한 `handoff/`로 한정돼 금지 데이터 접근은 0이었다. 이후 모든 `rg`에 네 제외 글롭을 적용했다. Windows wildcard·인용 파서 실패는 파일을 읽기 전 종료됐고 다른 방식으로 전환했다.

---

## 표지 keep-all·낙관 안전 여백 checkpoint 종결 — 2026-07-13

- 최종 판정: **EVIDENCE_SPLIT_PASS / checkpoint 완료**. Claude 라운드23 기준환경 실렌더와 Codex의 동일 tree 전체·정적 검증을 합성했다.
- 제품 commit `2fc7309`: `.cover .sub`에 keep-all 3종과 `max-width:var(--maxw)`를 적용하고, 실제 PDF 고지 line bbox와 후처리 낙관 image bbox 사이 수평 여백 `>=2mm`를 `test_p8.py` E2E로 고정했다.
- 역할 계약 commit `7ff7f56`: `AGENTS.md`를 `Claude 설계·최종 리뷰 / Codex 구현·자체 검증 / 사용자 checkpoint` 기본 1회 사이클과 환경별 분리 증거 계약으로 정리했다.
- 최종 검증: Codex 전체 **1008 passed / 32 skipped**, golden **28 passed**, 실제 Playwright `test_p8` **3 passed**, 최종 unknown-time 좌표 E2E **1 passed**, Ruff·py_compile·diff-check GREEN. Claude 기준환경 증거는 **1036 passed / 4 skipped**, `test_p8` 3 passed다.
- 시각검수: 합성 표지 PDF를 PDFium PNG로 확인해 음절 분리·잘림·낙관 겹침·깨진 글자 0. 실제 수평 여백 약 **4.16mm**(하한 2mm). 임시 PNG는 삭제했다.
- 권위 계약: 활성 packet은 manifest가 SHA로 고정한 `handoff/tasks/cover-sub-keepall-20260713.md` 하나다. 미고정 `cover-sub-keepall-codex-confirm-20260713.md`는 commit·후속 실행에서 제외한다.
- 과거 누적 확인 2종(라운드18 범위 밖 2변경·삼주 delivery 하한)은 beta-2 checkpoint 3커밋에 이미 포함된 역사 항목이며 이번 표지 태스크의 미해결 조건으로 재이월하지 않는다.
- 미검증/금지 유지: 실고객 PDF·300dpi·API·hrun·hsweep·APPROVED·발송·push 없음. 다음은 handoff `done / next_actor=none` 종결이며, push·실고객 작업은 별도 승인 대상이다.

---

## 라운드23 교차리뷰 — 2026-07-13 (검증 세션, 리뷰어 Claude)

- 판정: **승인(CODE_PASS)** — 표지 keep-all 수정분 신선 재검증, 미해결 블로커 0. 정본 = `REVIEW-FEEDBACK.md` 라운드23 절.
- 기준환경 전체 pytest **1036 passed / 4 skipped / exit 0**(215.66s), golden 28, test_p8 3/3 Playwright 실렌더
  PASSED(unknown_time 포함 skip 아님, `_assert_gate`로 세 상품 `gate_pass=True` — 전 상품 표지 변경 비악화 근거).
  변경 = 제품/테스트 2파일뿐(`report.html.j2` `.cover .sub` keep-all 3종 +1줄 · `test_p8.py` 공백 보존 단언
  +1줄·검증/비검증 도크스트링).
- 양방 증거: keep-all 1줄 임시 제거 → `test_e2e_unknown_time` line 111(공백보존) RED(`assert 0==1`) /
  line 110(무공백) GREEN — 새 단언이 no-op 아님·라운드21 음절 중간 개행("해석\n은") 재현. 복원 후 template
  diff = keep-all +1줄뿐(정확 복원). 표지 추출 실측: 고지 유일 개행 = `세부\n해석은`(어절 경계), 무공백·공백보존
  count 각 1.
- 정적: Ruff(test_p8.py) `All checks passed!` · py_compile exit 0 · `git diff --check` exit 0.
- 미검증: 표지 좌우 균형·시각 조판 품질(layout_geometry 이 환경 skip → 자동 게이트 밖, 운영자 육안 몫) ·
  실API·고객 PDF·비용·hsweep·300dpi·육안 Z=0. 합성 산출물 외 PDF 0. commit·push·API 없음.
- 다음: manifest `review_requested / next_actor=codex` → Codex 신선 read-only 확인
  (지시문 `handoff/tasks/cover-sub-keepall-codex-confirm-20260713.md`) → PASS 시 운영자 checkpoint commit 결정.

---

## 표지 고지 음절 중간 개행 수정 — 2026-07-13 (Codex)

- 상태: **패킷 §1~§2 구현 및 Codex 환경 검증 완료 / Claude 실렌더 신선 재검증 요청**.
  정본은 `handoff/tasks/cover-sub-keepall-20260713.md`다.
- 수정: `report.html.j2`의 기존 `.cover .sub`에 `word-break:keep-all`,
  `overflow-wrap:normal`, `line-break:strict`만 추가하고 기존 속성을 유지했다.
  `test_p8.py::test_e2e_unknown_time`에는 공백 보존 정규화 기준 고지 원문 1회 단언을 기존
  무공백 단언에 추가하고, 도크스트링에 검증·비검증 경계를 기록했다.
- 검증: 시작과 종료 전체 pytest가 모두 **1008 passed / 32 skipped / exit 0**로 기존 passed 감소 0,
  golden **28 passed**, test_p8 **3 skipped**다. test_p8은 통과로 간주하지 않으며, 수정 전 RED와
  수정 후 GREEN은 이 환경에서 실측하지 못했다. 변경 Python Ruff·py_compile GREEN,
  `git diff --check` exit 0이다.
- 범위·불변: 제품·테스트 변경은 위 2파일뿐이다. `verify.py`·게이트·lint·고지 문안·`@page`·
  다른 셀렉터와 테스트·`REVIEW-FEEDBACK.md`는 불변이다. API·LLM·고객/실상품 PDF·hrun·hsweep·
  commit·push·APPROVED·발송 없음. pytest가 허용 범위에서 만드는 합성 산출물 외 재생성은 없다.
- 미검증·다음: Claude 기준환경 Playwright 실렌더의 공백 보존 일치, `gate_pass`·
  `layout_geometry` 비악화, 표지 1쪽 육안 조판은 미검증이다. manifest를
  `review_requested / next_actor=claude`로 전환·validate한 뒤 신선 재검증을 요청한다.

---

## 라운드22 교차리뷰 — 2026-07-13 (검증 세션, 리뷰어 Claude)

- 판정: **승인(CODE_PASS)** — 미해결 블로커 0. 정본 = `REVIEW-FEEDBACK.md` 라운드22 절.
- 기준환경 전체 pytest **1036 passed / 4 skipped / exit 0**(229.8s) — beta-2 삼주 태스크 최초
  전체 GREEN. test_p8 3건 전부 Playwright 실렌더 PASSED(unknown_time 포함, skip 아님), golden 28.
- 변경 집합 SHA 증명: 라운드21 종료 스냅샷 대비 경계 54파일 중 변경 = `tests/test_p8.py` 1개뿐.
  수정 내용은 패킷 §1 사양 그대로(무공백 판정 + fail-closed 주석), 제품/게이트/조판 무변경.
- 정적: Ruff 부채 rules.py 17 + verify.py 1(구성 동일·신규 0), py_compile 38 exit 0, diff-check 0.
- 미검증: 실LLM·고객 PDF·비용·hsweep·300dpi·육안 — CODE_PASS 범위 밖. 합성 산출물 외 PDF 0.
- 다음: manifest `review_requested / next_actor=codex` → Codex 신선 read-only 확인 → 운영자
  checkpoint commit(확인 3건: 스코프 밖 2건 · delivery 하한 12쪽/3,500자 · 표지 개행 keep-all advisory).

---

## 라운드21 잔존 블로커 1건 수정 — 2026-07-13 (Codex)

- 상태: **테스트 전용 수정·자체 검증 완료 / Claude 라운드22 신선 재검증 요청**. 정본은
  `handoff/tasks/beta-2-round21-blocker-fix-20260713.md`
  (SHA-256 `db54f027…dd46`)와 `REVIEW-FEEDBACK.md` 라운드21 절이다.
- 수정: `tests/test_p8.py`의 삼주 E2E 후단 판정만 변경했다. PyMuPDF가 한국어 음절 사이에서
  만든 개행을 공백 보존 정규화가 `해석 은`처럼 복원하지 못하므로, 추출 텍스트·고정 고지·
  양성 3토큰·금지 9토큰을 모두 `re.sub(r"\s+", "", …)` 기준으로 비교한다. 금지 스캔은
  어절 경계 결합 과탐 가능성을 fail-closed로 수용하고 RED 시 조판 오탐과 실제 누출을 구분하도록
  주석에 기록했다. 생성 인자·게이트 단언·제품 코드·조판·다른 테스트는 수정하지 않았다.
- 검증: `tests/test_p8.py` 단독은 **3 skipped**(이 환경 Playwright E2E — 통과로 간주하지 않음),
  전체 **1008 passed / 32 skipped / exit 0**(시작치와 동일, 기존 passed 감소 0), golden
  **28 passed**. 변경 파일 Ruff·py_compile GREEN, `git diff --check` exit 0이다.
- 범위·불변: 이번 라운드 변경은 `tests/test_p8.py`와 인계 3종뿐이다. 제품 코드·게이트·lint·
  `THREE_PILLAR_NOTICE`·표지 조판·`REVIEW-FEEDBACK.md`는 불변이며, 동결 패킷 5종 SHA도 일치한다.
  API·LLM·고객/실상품 PDF·hrun·hsweep·commit·push·APPROVED·발송 없음. pytest 합성 산출물만
  허용 범위에서 생성됐다.
- 미검증·다음: 실제 E2E 실렌더에서 무공백 고지 1회·양성 3종·금지 9종 판정이 GREEN인지는
  Claude 라운드22 기준환경에 위임한다. 표지 음절 중간 개행의 조판 품질은 checkpoint 시 운영자
  advisory로 판단한다. PASS 뒤 Codex 신선 read-only 확인과 운영자 checkpoint commit 결정을 기다린다.

---

## 라운드21 교차리뷰 — 2026-07-13 (검증 세션, 리뷰어 Claude)

- 판정: **수정 요청(changes_requested)** — 잔존 1건, 테스트 전용. 정본 = `REVIEW-FEEDBACK.md` 라운드21 절.
- 라운드20 블로커 3건(style·quality·delivery)은 **제품 수준 전부 해소 실측**: E2E 동일 입력 verify
  `gate_pass=True`(False 키 = 비게이트 2개뿐)·delivery failures 0·final_text 14섹션 lint 0·
  PDF 표지 고지 외 가운뎃점 0. 3방 delivery 회귀·배선 spy·QI 기록·게이트 비악화 전부 확인.
- 잔존: `test_p8.py:102` 고지 카운트 `assert 0 == 1` — 표지 고지의 음절 중간 개행("해석\n은")을
  공백 보존 정규화가 복원 못 함. 무공백 기준 실측은 고지 1회·금지 9종 0(제품 정상, 계약 위반 없음).
  게이트 통과 후에만 실행되는 단언이라 라운드18 작성 이후 처음 도달한 잠복 테스트 결함.
- 실측: 전체 **1 failed / 1035 passed / 4 skipped / exit 1**(+3, 감소 0), golden 28, 집중 82+1f,
  Ruff 부채 구성 동일(신규 0), py_compile 38·diff-check 0, lint 4파일 무수정, 동결 핀 4종 불변.
- 다음: 수정 패킷 발주 `handoff/tasks/beta-2-round21-blocker-fix-20260713.md`(test_p8 101-115행
  무공백 정규화, 테스트 1파일만) → Codex 구현 → Claude 라운드22 재검증(전체 GREEN 기대).
  표지 개행 조판(keep-all)은 advisory로 checkpoint 시 운영자 판단.

---

## 라운드20 잔존 블로커 3건 수정 — 2026-07-13 (Codex)

- 상태: **패킷 v2 §1~§5 구현·자체 검증 완료 / Claude 라운드21 신선 재검증 요청**. 정본은
  `handoff/tasks/beta-2-round20-blockers-fix-20260713.md`
  (SHA-256 `04d5ee5f…d59d`)와 `REVIEW-FEEDBACK.md` 라운드20 절이다. v1 §4의 raw 골격
  매트릭스 모순으로 한 차례 무수정 정지한 뒤, 운영자가 빌더 `final_text` 층으로 교정한 v2에서 재개했다.
- style·quality 수정: `three_pillar_table`의 지장간·지지십성 구분자를 공백으로 바꾸고,
  삼주 부록의 `세운·월운`을 `세운과 월운`으로 재서술했다. 부록 첫머리에 verify 규약인
  `본문에 나온` 마커 문장을 추가했다. frame의 `이 장에서 말하지 않습니다`는
  `이번 풀이에서 다루지 않습니다`로 바꿔 시간 의존 정보를 제외한다는 의미를 유지했다.
  lint·게이트·고정 고지·known용 `manse_table`은 수정하지 않았다.
- delivery 수정: `delivery_quality.analyze`에 기본값 `None`인 `birth_time_mode`를 추가하고,
  verify가 정규화한 모드를 기존 호출 1곳에서 전달하도록 배선했다. 명시적 `three_pillar`에만
  12쪽/3,500자 하한과 `missing_usable_ziwei` 면제를 적용하고, 분량 외 보장 표현·외부 조언·반복 등
  다른 failure는 유지했다. `None`과 `known` 결과 dict 완전 동일 회귀로 기존 경로 비악화를 고정했다.
- 하한 여유율: 라운드20 E2E 실측 14쪽/4,615자 대비 새 하한은 각각 2쪽/1,115자 낮다.
  실측을 분모로 한 정상 변동 여유율은 **페이지 14.3%**, **본문 글자 24.2%**이며,
  실측은 하한의 116.7%/131.9%다. 자미 요구 면제는 삼주에서 자미 서술이 금지되는 구조적 계약이다.
- 근본원인 2층 회귀: 기존 raw 골격 3종 lint 테스트는 그대로 보존하고, no-LLM 빌더 전 섹션
  `final_text` × quality/style lint, 수정 전 문장 2건 차단, 삼주 차트 가운뎃점 0을 별도 테스트로
  추가했다. verify→delivery 모드 전달도 real-wrapper spy로 고정했다. `docs/16`에는
  `QI-2026-07-13-01`로 복합 게이트 과소 진단과 전체 False 키 덤프 절차를 기록했다.
- 검증: 신규 핵심 회귀 **3 passed**. 패킷 집중 4파일 **80 passed / 3 skipped**이며,
  `test_p8` Playwright E2E 3건은 이 환경에서 skip이라 통과로 간주하지 않고 라운드21에 위임한다.
  전체 **1008 passed / 32 skipped / exit 0**(시작 1005/32 대비 +3, 기존 감소 0), golden
  **28 passed**. 변경 Python 합집합 38개 중 부채 제외 36개 Ruff GREEN, 기존 부채는
  `rules.py` 17 + `verify.py` 1 = 18건으로 구성 동일, py_compile 38개·`git diff --check` exit 0이다.
- 범위: 이번 라운드 제품·테스트·문서 변경은 `charts.py`, `rules.py`, `delivery_quality.py`,
  `verify.py`, 테스트 2파일, `docs/16`과 인계 3종뿐이다. calc/input에는 쓰기 0이다. 다만
  HEAD 대비 calc/input 명령은 시작부터 있던 `calc/engine.py` 수정과 `calc/three_pillar.py`·
  `input/birth_time.py` 미추적으로 인해 0이 아니며, 시작·종료 status 항목은 동일하다.
  동결 패킷 4종과 `REVIEW-FEEDBACK.md` SHA는 불변이다.
- 금지·미검증: API·고객/실상품 PDF·hrun·hsweep·commit·push·APPROVED·발송 없음.
  pytest 합성 PDF/HTML만 허용 범위에서 생성됐다. 실제 E2E 실렌더·300dpi 조판·실LLM 문안/비용·
  hsweep K/Z·운영자 육안 Z=0은 미검증이다.
- 다음: manifest를 `review_requested / next_actor=claude`로 전환한 뒤, Claude 라운드21이
  기준환경 전체 pytest·test_p8 실렌더와 verify 전체 False 키 덤프를 재검증한다. PASS 뒤
  Codex 신선 read-only 확인과 운영자 checkpoint commit 결정을 기다린다.

---

## 라운드20 교차리뷰 — 2026-07-13 (검증 세션, 리뷰어 Claude)

- 판정: **수정 요청(changes_requested)** — 잔존 블로커 3건. 정본 = `REVIEW-FEEDBACK.md` 라운드20 절.
- 패킷 이행: Codex의 라운드19 잔존 수정(wonguk "살핍니다" 치환 + 골격×meta/loanword/raw_calc
  비Playwright 회귀)은 **사양 충족 실측** — 독립 프로브 17키 전수 TOTAL_HIT_RULES=0, 차단측 재현,
  E2E verify에서 customer_meta_clean=True. lint/게이트 코드 무수정 확인.
- 잔존: E2E(test_p8)는 라운드19 리뷰가 열거하지 못한 별개 게이트 3키로 여전히 gate_pass=False.
  전체 **1 failed / 1032 passed / 4 skipped / exit 1**(+1, 감소 0), golden 28.
  ① style_clean=False — 삼주 명식표 가운뎃점(charts.py:317·321, known PDF는 전 페이지 0 대조)
  + 부록 "세운·월운"(rules.py:1088)·부록 마커 "본문에 나온" 부재로 부록 제외 미적용.
  ② quality_clean=False — frame "이 장에서 말하지 않습니다"(rules.py:1013-1015) internal_meta_label.
  ③ delivery_quality_clean=False — premium_pages 14<20·premium_text_chars 4615<10000·
  missing_usable_ziwei(자미 마커 0, 삼주는 구조적 충족 불가) → **운영자 delivery 프로파일 정책 결정 선행**.
- 근본원인 2층: 라운드19 리뷰가 pytest repr 절단만 보고 첫 실패 축만 열거(리뷰 절차 구멍) —
  E2E 게이트 실패 시 verify 전체 False 키 덤프를 표준화. 매트릭스 회귀는 style_lint·quality lint로
  확장 필요(비Playwright 가능).
- 미검증: 라운드19 종료 스냅샷 부재로 변경 집합 SHA 증명 불가(보완 증거로 대체·Codex 보고와 정합),
  실LLM·고객 PDF·비용·hsweep·육안. 합성 테스트 산출물 외 PDF 생성 0. commit·push·API 없음.
- 다음: 운영자 결정 완료(2026-07-13, 삼주 전용 delivery 프로파일 신설 승인) → 수정 패킷 발주:
  `handoff/tasks/beta-2-round20-blockers-fix-20260713.md`(블로커 1·2 골격/차트/부록 마커 +
  블로커 3 delivery 분기·배선·양방 + 매트릭스 회귀를 quality/style lint로 확장 + docs/16 QI 1건)
  → Codex 구현 → Claude 라운드21 재검증.

---

## 라운드19 잔존 블로커 수정 — 2026-07-13 (Codex)

- 상태: **구현·자체 검증 완료 / Claude 라운드20 신선 재검증 요청**. 정본은
  `REVIEW-FEEDBACK.md` 라운드19 절과
  `handoff/tasks/beta-2-round19-blocker-fix-20260713.md`다.
- 제품 수정은 `sajugen/content/rules.py`의 삼주 wonguk 골격 1문장뿐이다.
  `함께 읽습니다`를 `살핍니다`로 최소 치환해 "세 자리를 따로 떼어 길흉을 단정하지 않고
  서로 보태는 방향을 본다"는 의미를 유지하면서 `guided_structure_walkthrough` 충돌을 제거했다.
  `customer_meta_lint.py`를 포함한 게이트·lint 코드는 수정하지 않았다.
- 근본원인 2층 회귀: `tests/test_unknown_time_provenance_gate.py`에 실제 삼주 계산 결과로 만든
  골격 17키 전체를 `customer_meta_lint`·`loanword_lint`·`raw_calc_lint`와 대조하는
  비Playwright 테스트를 추가했다. 수정 전 합성 문장은 정확히
  `guided_structure_walkthrough` 1건으로 차단됨을 반대편 단언으로 고정했다.
  수정 후 골격 전수 결과는 **`TOTAL_HIT_RULES=0`**이다. 이 테스트는 LLM 후보·PDF 조판을
  검증하지 않는다.
- Codex 실측: 신규 회귀 **1 passed**, 패킷 집중 **37 passed / 3 skipped**(3건은 이 환경의
  Playwright E2E — 통과로 간주하지 않고 Claude 라운드20에 위임), 전체
  **1005 passed / 32 skipped / exit 0**(1004/32 대비 +1, 기존 passed 감소 0), golden
  **28 passed**. 변경 Python 36개 중 기존 부채 파일 2개를 제외한 34개 Ruff GREEN,
  전체 py_compile·`git diff --check` exit 0. 기존 부채는 `rules.py` 17건 + `verify.py` 1건으로
  라운드19 구성과 동일해 신규 위반은 0이다.
- 범위: 이번 라운드 제품·테스트 변경은 위 2파일뿐이며 B2·B3·B4, advisory 3건,
  `REVIEW-FEEDBACK.md`, 동결/보류 패킷은 건드리지 않았다. commit·push·API·고객 PDF·hrun·
  hsweep 없음(전체 pytest의 합성 테스트 PDF/HTML만 허용 범위에서 생성).
- 미검증: Claude Playwright 기준의 `test_p8` 실렌더, 실제 고객 PDF·300dpi 조판·실LLM 문안/비용·
  hsweep K/Z·운영자 육안 Z=0.
- 다음: manifest `review_requested / next_actor=claude` → 라운드20 기준환경 전체 재검증.
  PASS 뒤 Codex 신선 read-only 확인 → 운영자 checkpoint commit 결정.

---

## 라운드19 교차리뷰 — 2026-07-13 (검증 세션, 리뷰어 Claude)

- 판정: **수정 요청(changes_requested)** — 잔존 블로커 1건. 정본 = `REVIEW-FEEDBACK.md` 라운드19 절.
- 라운드18 블로커 처리: **B2(원국표 배선)·B3(compose 중립화+SHA 핀+캡처 양방)·B4(경계 3건) 완결**.
  B1은 테스트 갱신 자체가 올바르고, 복구된 E2E가 라운드18부터 잠복한 제품 결함을 새로 적발했다.
- 잔존 블로커: `sajugen/content/rules.py:999` wonguk 골격 "함께 읽습니다"가 customer_meta
  `guided_structure_walkthrough`(`함께\s*읽습니다`)와 충돌 → E2E `gate_pass=False`.
  전체 **1 failed / 1031 passed / 4 skipped / exit 1**(+9, 감소 0). 리뷰어 전수 프로브(골격 17키 ×
  meta 8룰) 결과 충돌은 이 1건뿐 — 수정 = 문장 1곳 재서술 + **골격×customer_meta_lint 비Playwright
  단위 회귀 동반**(Codex 환경 E2E skip이라 이 회귀 없이는 같은 클래스 재발).
- GREEN 실측: golden 28, 집중 124(+동일 1 failed), 변경 36파일 py_compile exit 0·Ruff 신규 0·
  diff-check exit 0. 수정 파일 집합 = 자진 보고 8파일과 SHA 대조 일치, 동결/보류 패킷 불변.
- 플래그: 스코프 밖 변경 2건(rules.py 문구 순화·order_flow enum 정본화)은 최소·비악화 실측 GREEN이나
  "운영자 추가 승인" 주장은 리뷰어 확인 불가 — checkpoint commit 시 운영자 확인 필요.
- 미검증: 실제 API·고객 PDF·비용·hsweep K/Z·육안 Z=0. pytest 합성 산출물 외 PDF 생성 0.
- 다음: Codex 잔존 1건 수정 → Claude 라운드20 재검증 → PASS 시 Codex 신선 read-only 확인 →
  운영자 checkpoint commit. API·유료 재생성·commit·push 금지 유지.

---

## 라운드18 블로커 1~4 수정 — 2026-07-13 (Codex)

- 상태: **구현·자체 검증 완료 / Claude 라운드19 신선 재검증 요청**. 정본은
  `REVIEW-FEEDBACK.md` 라운드18 미해결 4건과
  `handoff/tasks/beta-2-round18-blockers-fix-20260713.md`다.
- B1: `test_p8` 생시 미상 E2E를 비절입일 `2000-01-15`로 옮기고 레거시
  `12:00 + unknown_time=True`가 삼주로 정규화되는 계약을 유지했다. 정확 고지 1회와
  `추정`·정오·시주·사주팔자·자미 사실 0을 단언했다. 운영자 추가 승인으로 삼주 골격의
  `추정값` 문장을 `짐작해서 채우지 않고 뺐습니다`로 순화하고 비Playwright 회귀도 고정했다.
- B2: 삼주 3열 원국표 anchor를 `wonguk/personal_wonguk` 우선으로 잡고, integrated sparse
  병합으로 ID가 사라지면 첫 `personal_*` 장(그마저 없으면 첫 고객 장)에 정확히 1회 삽입한다.
  실제 no-LLM build와 content.json 저장→복원 재렌더 경로에서 표 1회·고지 1회·`時柱` 0,
  known integrated에서는 표 0을 고정했다. `sajugen/integrated.py`의 이번 수정 라운드 추가 변경은 0이다.
- B3: known `_COMPOSE_SYSTEM` 전체를 보존하고, 삼주와 충돌하는 자미·궁·대운 긍정 지시만
  정확히 1회 일치할 때 결정론 치환한다(원문 드리프트 시 import-time fail-closed). 삼주/known의
  최종 system·user·guide·cache block을 Anthropic SDK 더블로 캡처했으며 known 시스템 SHA
  `a17f90fb0aa09ebf86adbac0efe6e1b2fc406ea7a7de46c2757fa626c7c4380a`를 고정했다.
- B4: 비입춘 소서 `1995-07-07` 차단과 07-06/08 통과, explicit three_pillar+시각 주문 0,
  mode 키 없는 레거시 known(시계 필드 유지, legacy false 유무 양방)의 최종 발급 통과를 추가했다.
  정확 경계 테스트가 사용자가 주지 않은 `unknown_time=False`를 내부에서 합성하던 접점을 드러내,
  운영자 추가 승인으로 `order_flow.py`가 명시 enum을 정본으로 쓰고 enum 없는 구 호출에서만
  legacy boolean을 복원하도록 최소 수정했다.
- 이번 수정 라운드 파일: `tests/test_p8.py`, `sajugen/render/pdf.py`,
  `sajugen/content/llm_sections.py`, `sajugen/content/rules.py`, `sajugen/order_flow.py`,
  `tests/test_three_pillar_calc.py`, `tests/test_unknown_time_order_contract.py`,
  `tests/test_unknown_time_provenance_gate.py`, 이 기록과 `sajugen/STATE.md`, manifest.
  `REVIEW-FEEDBACK.md`·동결 패킷·advisory 3건은 수정하지 않았다.
- 검증: 패킷 집중 **94 passed / 3 skipped**(Codex 환경 Playwright E2E 3건 skip), 전체
  **1004 passed / 32 skipped / exit 0**(시작 995/32 대비 +9, 기존 감소 0, skipped 유지),
  golden **28 passed**. 변경 Python 36개 중 기존 부채 `rules.py`·`verify.py`를 제외한 34개 Ruff GREEN,
  전체 py_compile exit 0, `git diff --check` exit 0. 기존 Ruff 부채 18건(17+1)은 라운드18 구성과 동일하다.
- 경계: API·고객 PDF·실상품 재생성·hrun·hsweep·commit·push 없음. pytest 합성 산출물만 생성.
  실제 고객 PDF·300dpi 조판·실LLM 문안/비용·hsweep K/Z·육안 Z=0은 **미검증**이다.
- 다음: Claude 신선 컨텍스트가 라운드18 수정분 diff와 기준환경 전체 pytest를 재검증한다.
  PASS 뒤 Codex 신선 read-only 확인 → 운영자 checkpoint commit 결정 순서를 유지한다.

---

## 라운드18 교차리뷰 — 2026-07-13 (검증 세션, 리뷰어 Claude)

- 판정: **수정 요청(changes_requested)**. 정본 = `REVIEW-FEEDBACK.md` 라운드18 절. 블로커 4건:
  1. 기준환경 전체 pytest **1 failed / 1022 passed / 4 skipped / exit 1** — `tests/test_p8.py::test_e2e_unknown_time`
     구계약 테스트 미갱신(1995-07-07=소서 절입일 차단 + `추정` 고지 단언 무효). Codex 환경 32 skip에 가려짐.
  2. integrated_full 삼주 원국표 팬텀 배선 — `render/pdf.py:128`의 `id=="wonguk"` 조건이 조립 후
     `personal_wonguk`과 불일치, `fake_saju.three_pillar`·`three_pillar_chart` 영속/복원이 미소비.
  3. 삼주 compose 상충 시스템 지시(`_COMPOSE_SYSTEM` 46/108/154행 자미·궁 긍정 지시 vs override 금지)
     + `_THREE_PILLAR_SYSTEM_OVERRIDE` 배선 캡처 테스트 0.
  4. 필수 경계 테스트 누락 3건 — 비입춘 절입 당일/전날·다음날, three_pillar+시각 동시 입력 접수 차단,
     레거시 known(mode 키 없음+시각 존재) 오분류 방지.
- GREEN 실측: golden 28, 신규/집중 176 passed, 변경 Python 35 py_compile exit 0, Ruff 신규 위반 0
  (rules.py·verify.py 18건 = HEAD 동일 구성), diff-check exit 0, 경계 스냅샷 47파일·보류 패킷 SHA 불변.
  계산·주문·게이트·문서 정합의 광범위 GREEN 항목은 라운드18 절 표 참조 — 재작업 불필요.
- advisory(비블로커): ziwei_fact 궁 목록 12궁 중 6개 부재(주성 14종은 factcheck 커버), engine 표면
  hour=None+minute 조용 무시(접수 경로 발생 불가), 야자시 23시 변형은 docs/03 결정대로 스윕 범위 밖.
- 미검증: 실제 API·고객 PDF·비용·hsweep K/Z·육안 Z=0. pytest 합성 테스트 PDF/HTML 외 PDF 생성 0.
- 다음: Codex가 블로커 1~4만 수정 → Claude 재검증 → 통과 시 Codex 신선 read-only 확인 →
  운영자 checkpoint commit. 유료 재생성·API·commit·push는 계속 금지.

---

## 생시 미상 삼주 전환 구현 — 2026-07-12 (Codex)

- 상태: **구현·자체 검증 완료 / Claude 신선 컨텍스트 교차리뷰 요청**.
  정본은 `handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md`이며 base는 `084e04c`다.
- 정책: 날짜-only 입력은 `birth_time_mode=three_pillar`로 정규화한다. 신고 시민 날짜의 연·월·일과
  12개 시지 후보에서 구조화 값이 12/12 동일한 사실만 사용하며, 정오·시주·자미·불안정 파생값을
  계산 결과/LLM/PDF에 노출하지 않는다. 절입 당일은 `NEEDS_INFO_TIME_BOUNDARY`로 접수 전 차단한다.
- 출처·발급: `three_pillar_schema_version=1`, 후보 수/digest, stable/suppressed fact ID를 주문까지
  관통시키고 `unknown_time_provenance_clean`을 22번째 하드 게이트로 추가했다. provenance 없는
  레거시 unknown/정오 주문, 관리자 시주·자미 주입, 최종 발급 재현 불일치는 fail-closed다.
- 고객 표면: 연·월·일 3열 원국표와 고정 고지 1회만 사용한다. 재검토 업셀 문구·정오·진태양시·
  자미 사실은 차단한다. known-time 계산/골든은 유지한다. 생시 미상+상대 입력·gunghap·자미 단독은
  12후보 관계 축약이 없는 v1에서 명시 차단한다.
- 검증: 신규/하네스 집중 **106 passed / 1 skipped**, 전체 **995 passed / 32 skipped / exit 0**
  (이 Codex 환경 시작 기준 921/32 대비 passed +74, 감소 0, skipped 유지), golden **28 passed**.
  변경 Python 35개 py_compile exit 0, 기존 Ruff 부채 파일 2개를 제외한 변경 Python 전부 GREEN,
  `rules.py` 17건 + `verify.py` 1건은 기존 부채 구성(신규 위반 0), `git diff --check` exit 0.
- 기준환경 수치: 직전 Claude 기준선은 949/4다. 신규 +74를 더한 1023/4는 산술 예상일 뿐이며,
  Claude 신선 리뷰에서 직접 실행하기 전까지 **확정 불가**다.
- 미검증: 실제 Anthropic API, 실제/고객 PDF 생성·300dpi 조판, prompt cache/비용, hrun·hsweep K/Z,
  운영자 육안 Z=0. 현재 고객 주문/DB/PDF/ignored 산출물은 이번 구현에서 열거나 수정하지 않았다.
- 보류 승계: `handoff/tasks/beta-1-hverify-module-contract-20260712.md`
  (SHA-256 `b981a99642ed47ca9c78c85733af5d114fd9e872acbb65efd905570754a05819`)는 내용 변경 없이 보존했다.
  삼주 태스크 종결 뒤 새 HEAD 기준으로 재검토해야 한다.

### 이번 구현 파일 전체 목록

- 정책·문서: `.claude/rules/00-immutable.md`, `.claude/rules/calc.md`,
  `.claude/rules/content.md`, `docs/03-engine-validation-plan.md`,
  `docs/07-safety-and-compliance.md`, `docs/16-quality-incident-ledger.md`,
  `docs/20-gate-coverage.md`, `docs/22-issuance-runbook.md`, `docs/23-beta-operation.md`.
- 계산·입력: `sajugen/input/birth_time.py`, `sajugen/calc/three_pillar.py`,
  `sajugen/calc/engine.py`.
- 콘텐츠·오케스트레이션: `sajugen/content/unknown_time_policy.py`,
  `sajugen/content/builder.py`, `sajugen/content/factcheck.py`,
  `sajugen/content/llm_sections.py`, `sajugen/content/report_context.py`,
  `sajugen/content/rules.py`, `sajugen/content/sections_schema.py`, `sajugen/pipeline.py`,
  `sajugen/integrated.py`, `sajugen/gunghap.py`, `sajugen/cli.py`, `sajugen/app.py`.
- 주문·렌더·하네스: `sajugen/order_flow.py`, `sajugen/store/orders.py`,
  `sajugen/render/charts.py`, `sajugen/render/pdf.py`,
  `sajugen/render/templates/report.html.j2`, `sajugen/render/verify.py`,
  `scripts/hverify_pdf.py`, `scripts/hsummary.py`.
- 테스트: `tests/test_three_pillar_calc.py`, `tests/test_three_pillar_orchestration.py`,
  `tests/test_unknown_time_order_contract.py`, `tests/test_unknown_time_provenance_gate.py`,
  `tests/test_cover_semantic_clean.py`, `tests/test_gate_contract.py`,
  `tests/test_generate_legacy_pii.py`, `tests/test_gunghap.py`, `tests/test_harness.py`,
  `tests/test_integrated_product.py`, `tests/test_module_selection_admin.py`,
  `tests/test_orders.py`, `tests/test_skeleton_lint_matrix.py`.
- 인계: `handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md`,
  `handoff/current/manifest.json`, `implementation-notes.md`, `sajugen/STATE.md`.
- 이번 태스크 이전부터 남아 있던 별도 파일: `handoff/tasks/beta-1-hverify-module-contract-20260712.md`
  (보류 패킷, 이번 구현 내용 변경 0).

- 다음: Claude 신선 컨텍스트가 packet 대비 diff 전량·기준환경 pytest·골든·새 게이트/known 회귀를
  독립 검증한다. PASS 뒤 Codex 신선 read-only 최종 확인과 운영자 checkpoint commit 결정을 기다린다.
  유료 replacement·PDF·hsweep은 별도 승인 전 금지한다.

---

## 라운드17 교차리뷰 — 2026-07-12 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. `일정/일정한` 오탐 소수정(제품 2파일, +32/-1) — 승인 범위 밖 변경 0.
  정본 = `REVIEW-FEEDBACK.md` 라운드17 절.
- 기준환경 확정: **949 passed / 4 skipped / exit 0**(941+8, 감소 0) — 새 기준선. golden 28, 집중 70,
  변경 2파일 Ruff/py_compile/diff-check GREEN. 경계 프로브 14건 전부 기대 일치.
- 비블로커: 인접 `일정하다/일정해서` 잔존 오탐(승인 스코프 밖, fail-closed). 절차 이탈 1건(broad rg →
  render/out 매치, 자진 보고) — 재발 방지 = 이후 패킷 0절에 ignored 제외 글롭 문구 필수.
- 다음: 운영자 checkpoint commit 결정 → (별도 과금 승인 시) Phase C replacement 1회.
- **종결(2026-07-12)**: 제품 checkpoint commit = `e6145fc`(fix, 2파일 +32/-1). **라운드17 PASS**,
  새 기준선 **949 passed / 4 skipped**. `일정하다/일정해서`는 실제 관측 시에만 확장하는 비블로커.
  beta-1-schedule-boundary done + archive 동결. API·PDF·비용·hsweep K/Z·육안 Z=0 미검증.
  다음 = 운영자의 Phase C replacement 1회 과금 승인 결정.

---

## 라운드16 advisory `일정/일정한` 오탐 소수정 — 2026-07-12 (Codex)

- 상태: **구현·자체 검증 완료 / Claude 신선 컨텍스트 교차리뷰 요청**.
- 제품 변경: `sajugen/content/delivery_quality.py` 일정 fact 정규식 1곳을 `일정(?!한|하게|하지)`로 경계화하고,
  `tests/test_register_advice_gate.py`에 수용 기준 명사형 차단 4건·인접 명사형 차단 1건·형용사 활용형 허용 3건을 추가했다.
- 기존 “외부 도메인 + 사실/절차” 계약과 고정 토큰 `일정`, 다른 차단 패턴, 게이트 키는 바꾸지 않았다.
  제품 diff = 2파일, 32+/1-. 정책 문서·다른 게이트 수정 0.
- 실측: 수정 전 차단 5=True/허용 예정 3=True → 수정 후 차단 5=True/허용 3=False. 신규 8 passed,
  관련 집중 70 passed, 전체 **921 passed / 32 skipped / exit 0**(동일 환경 913/32+8), golden 28.
  변경 Python Ruff GREEN, py_compile exit 0, `git diff --check` exit 0.
- 금지 준수: API·PDF·hsweep·유료 재생성·hrun·commit·push·main 전진 없음.
- 절차 기록: 초기 broad `rg`가 비대상 `sajugen/render/out/**`까지 1회 매치했다. 출력 내용을 인용·전재·수정하거나
  PII 확인을 위해 재열람하지 않았고, 이후 탐색 범위를 제품 코드·테스트로 제한했다.
- 인계 정본: `handoff/tasks/beta-1-schedule-boundary-20260712.md`. 다음 = Claude가 diff+검증을 독립 재실행해
  PASS면 운영자 checkpoint commit 결정. replacement는 여전히 별도 과금 승인 전 실행 금지.

---

## 라운드16 교차리뷰 — 2026-07-12 (검증 세션, 리뷰어 Claude)

- 판정: **PASS(CODE_PASS)**. 패킷 `beta-1-register-harness-20260712` A~D 전 항목 diff 근거 확인.
  정본 = `REVIEW-FEEDBACK.md` 라운드16 절.
- 기준환경 확정: **941 passed / 4 skipped / exit 0**(831+110, 감소 0) — 새 기준선. golden 28.
  Ruff 신규 0(HEAD 부채 19건 동일 구성 대조 실측), py_compile 43파일·diff-check GREEN, calc/input diff 0.
- advisory 1건(비블로커): `일정` 외부사실 패턴이 형용사 `일정한`에 오탐(프로브 실측). 골격 무저촉,
  영향은 LLM 후보 룰 폴백(fail-closed). 다음 라운드에서 오탐 축소 방향 개선 후보.
- 리뷰어 수정 = 허용 4파일만(REVIEW-FEEDBACK·STATE·이 파일·manifest는 handoff 도구). read-only 56파일
  SHA-256 시작/종료 스냅샷 전수 일치.
- 다음: 운영자 checkpoint commit 결정 → (별도 과금 승인 시) replacement 주문 1회 → 게이트/hsweep/육안 Z.
- **종결(2026-07-12)**: checkpoint commit = `5b0a88f`. beta-1-register-harness **CODE_PASS 태스크 종결**
  (manifest done + `handoff/archive/beta-1-register-harness-20260712.json` 동결). 실제 API·PDF·prompt cache
  비용·hsweep K/Z·육안 Z=0은 여전히 미검증. 다음 = 유료 재생성 전 라운드16 advisory `일정/일정한` 오탐
  소수정 여부 결정 → 이후 운영자 별도 과금 승인 시에만 Phase C replacement 1회.

---

## 베타 1호 Z>0 개선 구현 후보 — 2026-07-12 (Codex)

### 현재 상태

- 브랜치 `codex/gunghap-relationship-quality`, 시작·현재 HEAD `5ebd3b6`, upstream 대비 ahead 0 / behind 0.
- 베타 1호 육안 Z>0를 계기로 문체 register·외부 실무조언·어려운 용어·hsweep 판정 구조·LLM 비용 관측을 함께
  보완했다. 워킹트리는 미커밋이며 현재 판정은 **CODE_PASS / Claude 교차리뷰 요청**이다.
- 세션 시작 때 이미 수정돼 있던 `docs/16-quality-incident-ledger.md`와 `docs/23-beta-operation.md`의 Claude Phase A
  기록은 보존했다. 그 기록을 구현 계약과 hsweep v2 사실에 맞춰 확장했으며 되돌리지 않았다.

### 완료한 구현

1. `docs/14-tone-spec.md`를 문체 register·외부 도메인 조언·첫 등장 쉬운 풀이의 기계 판독 SSOT로 확장했다.
2. register 하드 게이트를 cover·toc·본문·appendix 전역에 연결하고, 외부 사실/절차 조언을 독립 실패 원인으로
   연결했다. builder 최초 후보·재시도·룰 폴백, 개인·궁합·관계·followup·최종 PDF가 같은 판정을 사용한다.
   최종 섹션을 다시 집계해 룰 골격 위반도 `GuardReport.clean=False`가 되도록 pre-render false-PASS를 닫았다.
3. consult의 의미 없는 action 표지를 제거하고 `work_career` 축을 추가했다. 7개 질문 카테고리와 followup 골격,
   질문 미러링 허용/후속 조언 차단을 양방 테스트로 고정했다.
4. PII 없는 `ReportContext`를 추가했다. 12개 Sonnet 장은 같은 결정론 context/cache prefix를 공유하되 현재 장
   ID는 호출별 user 블록으로 받는다. 상품별 비활성 용어 소유 장은 활성 장으로 결정론 재배정한다.
5. Anthropic explicit cache를 fail-closed로 배선했다. 첫 호출에서 cache usage가 관측된 경우에만 나머지 호출을
   3병렬로 실행한다. 모델은 Sonnet 4.6을 유지하고 role/model/section/attempt/cache/thinking/stop usage를 PII 없이
   run 단위로 격리·주문 메타에 저장한다.
6. hsweep를 비파괴 schema v2로 개편했다. raw→rank(advisory)→judge 전수→운영자 review를 분리하고 K/Z를
   운영자 판정으로만 계산한다. PII manifest·정밀 마스킹·partial/stage/usage·v1 migration·canonical review와
   gitignored atomic temp를 추가했다.
7. 게이트 레지스트리·하네스 요약/검증·운영 문서를 새 키와 지표에 맞춰 동기화했다.

### 수정 파일 전체 목록

- 기존 Claude 기록에서 시작: `docs/16-quality-incident-ledger.md`, `docs/23-beta-operation.md`.
- 문서: `docs/01-product-context.md`, `docs/02-architecture.md`, `docs/05-nlg-pdf-generation.md`,
  `docs/06-llm-usage-policy.md`, `docs/07-safety-and-compliance.md`, `docs/09-roadmap.md`,
  `docs/14-tone-spec.md`, `docs/16-quality-incident-ledger.md`, `docs/20-gate-coverage.md`,
  `docs/23-beta-operation.md`.
- 하네스 프롬프트: `harness/prompts/sweep/lens_direct_answer.md`,
  `harness/prompts/sweep/lens_narrator_tone.md`.
- 제품 코드: `sajugen/cli.py`, `sajugen/content/builder.py`, `sajugen/content/client_tone_lint.py`,
  `sajugen/content/delivery_quality.py`, `sajugen/content/llm_polish.py`, `sajugen/content/llm_sections.py`,
  `sajugen/content/llm_usage.py`, `sajugen/content/rules.py`, `sajugen/content/sections_schema.py`,
  `sajugen/followup/answer_gate.py`, `sajugen/gunghap.py`, `sajugen/integrated.py`, `sajugen/order_flow.py`,
  `sajugen/pipeline.py`,
  `sajugen/relationship/context.py`, `sajugen/relationship/delivery_gate.py`, `sajugen/render/pdf.py`,
  `sajugen/render/verify.py`.
- 하네스 코드: `scripts/hrun.py`, `scripts/hsummary.py`, `scripts/hsweep.py`, `scripts/hverify_pdf.py`.
- 기존 테스트 수정: `tests/test_chapter_fallback_observability.py`, `tests/test_consistency.py`,
  `tests/test_consult_gate.py`, `tests/test_delivery_quality.py`, `tests/test_followup_gate.py`,
  `tests/test_gate_contract.py`, `tests/test_harness.py`, `tests/test_hsweep_contract.py`,
  `tests/test_integrated_order_flow.py`, `tests/test_integrated_product.py`, `tests/test_llm_sections.py`,
  `tests/test_llm_usage.py`, `tests/test_myeongni_ziwei_weave.py`, `tests/test_pii_masking.py`,
  `tests/test_postprocess.py`, `tests/test_skeleton_lint_matrix.py`, `tests/test_verify_gate_meta.py`.
- 신규 파일: `sajugen/content/report_context.py`, `tests/test_register_advice_gate.py`,
  `tests/test_report_context.py`, `tests/test_tone_spec_contract.py`.
- 인계 기록: `sajugen/STATE.md`, `implementation-notes.md`,
  `handoff/tasks/beta-1-register-harness-20260712.md`, `handoff/current/manifest.json`.
- 계산·입력 SSOT인 `sajugen/calc/**`, `sajugen/input/**`은 변경하지 않았다.

### 검증 증거

- `./.venv/Scripts/python.exe -m pytest tests/ -q` → **913 passed / 32 skipped / exit 0**(116.48s).
  Codex 환경 기존 803/32 대비 passed 감소 0, 신규 검증 +110.
- `./.venv/Scripts/python.exe -m pytest tests/ -q -k golden` → **28 passed / exit 0**.
- register/context/tone/hsweep/PII 핵심 합성 → **123 passed**.
- 독립 리뷰: register/context/골격 68 passed·최종 PASS, hsweep canonical/temp 보안 57 passed·최종 PASS,
  usage run 격리/cache fail-closed 47 passed·최종 PASS.
- 변경 Python 중 기존 Ruff 부채 파일 3개를 제외한 검사 → `All checks passed!`.
- 전체 변경 Python `py_compile` exit 0, `git diff --check` exit 0, calc/input diff 0.
- 변경 파일 전체 Ruff는 기존 HEAD 부채 19건 때문에 exit 1: `rules.py` F841 1+F541 16,
  `render/pdf.py` F401 1, `render/verify.py` F841 1. 이번 변경의 신규 위반으로 판정된 항목은 0.

### 확인하지 못한 것과 남은 위험

- 실제 Anthropic API를 호출하지 않았으므로 prompt cache hit, 실제 호출 수·비용 절감, Sonnet 문안 품질은
  **확정 불가**다. 모델을 낮추거나 바꾸지 않았다.
- 고객·ignored 산출물과 local profile을 열지 않았고 PDF를 재생성하지 않았다. 새 replacement PDF의 조판,
  표준 게이트, hsweep K/Z, 운영자 육안 Z=0은 미검증이다.
- 정규식은 등재한 register·외부 조언 조합만 막는다. 폐쇄 목록 밖 의미 결함은 hsweep와 육안 Z가 계속 맡는다.
- Claude 기준환경 예상은 총 수집 수 산술상 941 passed / 4 skipped지만 직접 실행 전에는 확정값이 아니다.
- commit·push·APPROVED·발송은 하지 않았다.

### 다음 행동

1. Claude 신선 컨텍스트가 `handoff/tasks/beta-1-register-harness-20260712.md`를 기준으로 diff 전량과 기준환경
   전체 pytest를 교차리뷰한다.
2. PASS 뒤 운영자가 checkpoint commit 여부를 결정한다.
   이때 미추적 필수 파일 5개(packet·`report_context.py`·신규 테스트 3개)를 경로로 명시해 함께 추가한다.
   `git commit -am`만 사용하면 import/계약 파일이 빠지므로 금지한다.
3. 별도 과금 승인 후에만 기존 로컬 접수 절차로 replacement 주문을 1회 생성한다.
4. 새 PDF에서 표준 게이트→hsweep→운영자 전문 육안 검수를 실행하고 Z=0일 때만 승인·수동 발송한다.

---

## 베타 트랙 세션 인계 — 2026-07-12 (Claude)

- 완료: docs/23 확정(N=3 무료·재발급 1인 선행) / A-2 정리(389파일 repo 밖, QI-2026-07-11-01 종결) / 베타 1호 접수·4모듈 확정·LLM 생성(gate_pass=True·36p·DRAFTED) / hsweep 파일럿 1호(N=29·M=0·K=0·$0.41).
- 대기 지점: **운영자 육안 검수 + Z 값 보고**(익명 문서 `DOC_BETA_1`). 인계 정본 = `handoff/tasks/beta-1-issuance-20260712.md`.
- 새 세션은 "이어받아"로 시작 — manifest가 이 패킷을 가리킨다.

---

## 감사 A-1 라운드15 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. 테스트 전용(test_render_verify.py +91, 제품 diff 0) — M1 차단측(text_layer 임계 양방)·M3 이중화(verify 경유 delivery 전용). 정본 = `REVIEW-FEEDBACK.md` 라운드15 절.
- 기준환경 확정: **831 passed / 4 skipped / exit 0**(829+2, 감소 0) — 새 기준선. 변이 재검 직접 재실행으로 M1·M3 격추 실증(원복 완료). **감사 2026-07 생존 변이 0, 코드 후속 종결.**
- 커밋 완료(2026-07-11 운영자 지시): `3f36b39` test(A-1) / docs(기록·manifest). manifest = done + archive. feat push + main ff 전진·push. 감사 코드 후속 종결.
- 다음: 베타 트랙 — docs/23 초안 작성.

---

## Q7 given 가드 라운드14 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. v2 패킷(정지→정정 경유) 그대로 — given_name 출력 동등성 술어, 접수 전 차단, 경계표 차단 5·통과 4 고정. 정본 = `REVIEW-FEEDBACK.md` 라운드14 절.
- 기준환경 확정: **829 passed / 4 skipped / exit 0**(820+9, 감소 0) — 새 기준선. 골든 28, Ruff GREEN, 프로브 실측.
- **Q7 전체 완결** — 알려진 잔여 0. 선택 항목만: LLM-on 정상 쌍 N=5 실측·main 전진·육안 검수.
- 커밋 완료(2026-07-11 운영자 지시): `5519899` feat / docs(기록·manifest). manifest = done + archive. feat push + **main ff 전진·push — Q7 프로젝트 종결.**

---

## Q7 4단계 라운드13 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. 2인 접수·gunghap 주문화(접수 additive·추천 분기·admin/confirm 조건화·생성 2인 분기·partner_present 실소비) 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드13 절.
- 기준환경 확정: **820 passed / 4 skipped / exit 0**(801+19, 감소 0) — 새 기준선. 골든 28, Ruff GREEN, 프로브·합성 실렌더 N=5(2인) 실측.
- 실렌더 N=5: 35p로 분량 하한(30p) 통과 — 관계 조립 실작동. 발견 R13-1(비블로커·기존 경로): 무LLM 관계 문안 수신자 '씨' 호칭 → role 게이트 차단. LLM-on 해소 여부 미검증.
- 커밋 완료(2026-07-11 운영자 지시): `c8cd1cc` feat(4단계 10파일) / docs(기록·manifest). manifest = done + archive. push 완료.
- R13-1 처리: (a)안 실측 완료(2026-07-11) — LLM-on N=5도 GATE FAIL(동일 호칭 룰 17회 + identity_role + 저밀도 1쪽). ~~문안 수정 발주 필요로 확정~~ **[정정 2026-07-11]** 위반 문형 추출로 재판정: 프로브 합성 쌍의 given 동일("합성")이 원인인 입력 엣지. given 상이 쌍(김민준/이서연) 무LLM N=5 = **gate_pass True·35p·전 게이트 clean** → 수정 발주 불필요, 2인 N=5 상품 정상. 잔여 = 동명 given 커플 접수 차단 추가 여부만 결정 대기.

---

## Q7 3-B 라운드12 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. admin 모듈 추천·확정 UI(추천 표시 전용·NORMALIZED 한정 확정·정규화 위임·audit 모듈 ID만) 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드12 절.
- 기준환경 확정: **801 passed / 4 skipped / exit 0**(778+23, 감소 0) — 새 기준선. 골든 28, Ruff GREEN, 실경로 프로브 3종 실측.
- 절차 이탈 0 — QI-2026-07-11-01 재발 방지(`!**/` 글롭) 첫 적용 라운드에서 유효 확인.
- **Q7 3단계 완결.** 커밋 완료(2026-07-11 운영자 지시): `8098f84` feat(3-B 7파일) / docs(기록·manifest). manifest = done + archive. push 완료.
- 합성 실렌더 실측 완료(2026-07-11): 무LLM N=1 21p PASS / N=2 22p PASS / N=3 23p FAIL(-1p) / N=4 24p FAIL(-4p) → 룰 전용 분량 모듈당 +1p vs 공식 +4p. LLM-on N=4 = 34p **PASS**(과금 승인분, calls 18).
- 분량 정책 확정(운영자): 공식 유지 + 알려진 제약 "무LLM 폴백 발급은 N≤2만"(N≥3 = LLM-on 전제). 산출 PDF는 render/out 비커밋.
- 다음: 4단계(gunghap·2인 접수) 별도 설계. LLM-on 문안 육안 검수는 운영자 영역 잔존.

---

## Q7 3-A 라운드11 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. 주문 플로우 integrated_full 편입(계산 입력 배선·접수/시진불명 차단·미확정 차단·3지점 분기·후속 차단) 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드11 절.
- 기준환경 확정: **778 passed / 4 skipped / exit 0**(758+20, 감소 0) — 새 기준선. 골든 28, Ruff 8파일 GREEN, 실경로 프로브 P1~P3 차단 실측.
- 절차 이탈 2회차(비블로커): 원인 = 패킷 글롭 예시가 루트 기준으로 불충분 → 이후 패킷 `!**/...` 형식 고정. docs/16 기록 권고.
- 커밋 완료(2026-07-11 운영자 지시, 분리안 2커밋): `ac5d8f2` feat(3-A 8파일) / docs(기록·manifest·QI). manifest = done + archive. push 완료. 절차 이탈 2회 = docs/16 QI-2026-07-11-01 기록.
- 다음: 3-B(admin 추천·확정 UI) 발주 → 라운드12.

---

## Q7 2단계 라운드10 — 2026-07-11 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. CLI `--module` 배선(2파일) 수용기준 전 항목 GREEN. 정본 = `REVIEW-FEEDBACK.md` 라운드10 절.
- 기준환경 확정: 전체 pytest **758 passed / 4 skipped / exit 0**(753+5, 감소 0) — 새 기준선. 골든 28, Ruff 2파일 GREEN, 실 프로세스 차단 3종 exit 1 실측.
- 절차 이탈 1건(비블로커): Codex 광역 rg가 ignored render/out/** 일부를 검색 결과에 포함(수정·전재 없음, 자진 보고). 재발 방지 권고 기록, docs/16 여부 운영자 결정 대기.
- 커밋 완료(2026-07-11 운영자 지시, 분리안 2커밋): `ff002ee` feat(CLI 2파일) / docs(기록·manifest). manifest = done + archive. push 완료. Q7 1·2단계 종결.
- 다음: 3단계(admin·주문 플로우 편입)는 별도 설계·승인. 이후 Codex 패킷에 ignored 제외 글롭 필수 문구 포함.

---

## Q7 1단계 라운드9 재검 — 2026-07-10 (검증 세션, 리뷰어 Claude)

- 판정: **PASS**. R9-1 종결, Q7 1단계 미해결 0. 정본 = `REVIEW-FEEDBACK.md` 최상단 "라운드9 재검" 절.
- 기준환경 확정: 전체 pytest **753 passed / 4 skipped / exit 0**(745+8, 감소 0) — 새 기준선. 골든 28. 허용 밖 동결 7파일 SHA 불변 실측, 수정 2파일 Ruff GREEN.
- 프로브: 라운드9 동일 스크립트 재실행으로 P1·P3·P4·P5 전부 차단 전환 확인 + 통과측 G1~G4 오탐 0.
- 이 세션 수정 = 상태·리뷰 4파일만. 제품 코드 비접촉, commit/push/PDF/sajugen LLM 호출 없음.
- 커밋 완료(2026-07-10 운영자 지시, 분리안 3커밋): `065c987` feat(제품 9파일) / `fbdb296` chore(handoff 공존 3파일) / docs(기록·manifest). manifest = done + archive 동결.
- 다음: Q7 2단계(CLI/admin)는 별도 승인·패킷 발주. push는 지시 대기.

---

## Q7 1단계 교차리뷰 라운드9 — 2026-07-10 (검증 세션, 리뷰어 Claude)

- 판정: **changes_requested**. v3 수용기준 전 항목 GREEN이나 R9-1(module_sections 소유권 교차검증 사각) 1건 보완 필요. 정본 = `REVIEW-FEEDBACK.md` 라운드9 절.
- 기준환경 확정: 전체 pytest **745 passed / 4 skipped / exit 0**(728+17, 감소 0), 골든 28, 동결 SHA 10건 MATCH, Ruff 신규 위반 0.
- 이 세션 수정 파일 = 상태·리뷰 4개만(`REVIEW-FEEDBACK.md`·`sajugen/STATE.md`·`implementation-notes.md`·`handoff/current/manifest.json`). Q7 제품 코드·테스트 9개는 SHA 동결 그대로 비수정. commit/push/PDF 재생성/sajugen 런타임 LLM 호출 없음.
- 다음: Codex가 R9-1만 수정(예상 범위 `sajugen/modules.py`+`tests/test_integrated_modules.py`, 양방 회귀 동반) → 라운드9 재검 → PASS 후 사용자 checkpoint commit 결정.

---

## Q7 1단계 구현 후보 검증·SHA 인계 — 2026-07-10

### 현재 상태

- 브랜치 `codex/gunghap-relationship-quality`, HEAD `0b3134fe7ef508dde6f4d45952a132016a687fc8`, upstream 대비 ahead 20 / behind 0.
- 승인 source of truth는 `handoff/codex-q7-stage1.md` v3다. v2 이후 sparse 병합의 현행 유지와 병합 전 커버리지 판정까지 정정된 커밋이 HEAD에 포함돼 있다.
- Q7 1단계 제품 구현 후보는 미커밋 상태다: tracked modified 7개 + 신규 2개. 이전 최상단의 “Q7 코드 미착수” 기록은 과거 정지 시점의 이력이며 현재 상태가 아니다.
- 상태 판정은 `review_requested`다. 라운드9와 기준환경 4-skip 전체 검증 전에는 `verified`·`done`이 아니다.

### 실측한 구현 범위

- `sajugen/modules.py`: schema v1 레지스트리, 5모듈 정규화, 섹션 소유권, 병합 전 커버리지, N별 하한 계산.
- `sajugen/content/rules.py`·`builder.py`: job/wealth 제공자 분리와 선택 밖 개인 장 생성 제외.
- `sajugen/integrated.py`: 현행 순서 필터링 후 sparse 병합, 병합 전 ID/모듈 맵 보존, 선택 메타 저장·복원.
- `sajugen/content/delivery_quality.py`·`render/verify.py`: 모듈 하한과 missing/unexpected fail-closed 게이트 배선.
- 관련 테스트 3파일: 5모듈 완전 동일성, N=1..5 경계, missing/unexpected, gunghap 1인/2인, job/wealth 분리, 메타 재렌더 회귀.
- `sajugen/calc/**`, `sajugen/input/**`, CLI, admin, order/state-machine 변경은 0이다. Q7 2단계는 미착수다.

### 검증 증거

- Q7 대상 3파일: `43 passed`, exit 0.
- 신규 모듈 테스트 단독: `17 passed`, exit 0.
- 전체: `.\.venv\Scripts\python.exe -m pytest tests\ -q` → `718 passed / 31 skipped`, exit 0. Q7 전 기준환경 `728/4` + 신규 17의 예상 `745/4`는 총 수집 수 749로 산술 일치하지만 기준환경 재실행 전이라 확정 불가다.
- 신규 두 파일 Ruff: `All checks passed!`, exit 0. 전체 `ruff check .`는 기존 부채 29건으로 exit 1이므로 전체 Ruff GREEN은 주장하지 않는다.
- `git diff --check` → exit 0(LF→CRLF 안내만). calc/input/CLI/admin/order 경로 diff 0.
- Phase2A 공존 계약 테스트: `tests/test_ai_harness_contract.py` → `25 passed`, exit 0. `git check-ignore --no-index`로 실행 산출물은 ignored(exit 0), 루트 manifest는 추적 가능(exit 1)을 확인했다.
- 로컬 SessionStart relay: `relay-context.mjs --format claude` → exit 0, verified task/status/SHA/next actor/action의 structured JSON 출력. 실제 새 `codex exec` 실주입은 외부 전송 보안 검토에서 차단돼 확정 불가다.

### 이번 SHA 인계 적용과 기존 Q7 변경의 구분

- 이 세션은 위 Q7 제품 코드·테스트 9개의 내용을 수정하지 않았다. 인계 패킷에 적용 전 SHA-256을 동결했다.
- 이번 세션 변경은 `handoff/current/.gitignore`, `handoff/current/README.md`, `tests/test_ai_harness_contract.py`, `handoff/tasks/q7-stage1-modules-20260710.md`, `implementation-notes.md`, `sajugen/STATE.md`, `handoff/current/manifest.json`과 AI-Brain의 sajugen 포인터 정합화다.
- 기존 Phase2A 런타임은 유지한다. 실행 폴더·task/LATEST/log/run-manifest는 계속 ignored이고 루트 `manifest.json`만 SHA 역할 교대 포인터로 추적 가능하다.
- commit, push, PR, deploy, PDF 재생성, LLM 호출은 실행하지 않았다.

### 미완 지점과 다음 행동

1. 신선 Claude 세션이 `handoff/tasks/q7-stage1-modules-20260710.md`와 v3 지시문을 기준으로 라운드9 교차리뷰한다.
2. 기준환경 전체 pytest 예상 `745 passed / 4 skipped`를 직접 확정한다.
3. `module_sections`에 잘못된 모듈↔섹션 소유권을 합성 주입하면 현재 게이트가 탐지하지 못하는 사각을 라운드9에서 판정한다.
4. PASS 뒤 사용자가 Q7 checkpoint commit 여부를 결정한다. 그 전에는 Q7 2단계·실렌더를 시작하지 않는다.
5. 현재 `REVIEW-FEEDBACK.md`는 Q7 이전 이력이며 Q7 라운드9 PASS 근거가 아니다.

---

## Q7 1단계 착수 점검 정지 — 2026-07-10

### 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 시작 HEAD: `7fa5d57` (`Q7 1단계 TASK_PACKET 발주 — 모듈 레지스트리·조립·게이트`). 현재 HEAD: `3be5d96` (`Q7 1단계 착수 점검 정지 기록`).
- 현재 원격 대비: ahead 18. 세션 시작 워킹트리는 깨끗했고 구현 파일 수정·push·deploy는 없다. 상태 기록 중 외부에서 패킷 v2 커밋 `c4443a1`과 상태 기록 커밋 `3be5d96`을 생성했으며, Codex는 commit을 실행하지 않았다.
- Q7 1단계 코드는 미착수다. 레지스트리·work 제공자·조립·게이트·테스트 변경은 모두 0줄이다.

### 이번 세션에서 완료한 태스크

- `handoff/codex-q7-stage1.md`와 승인 설계 `handoff/codex-q7-design.md`를 읽고 1단계 범위와 금지 경계를 대조했다.
- `sajugen/integrated.py`, `sajugen/content/rules.py`, `sajugen/content/delivery_quality.py`, `sajugen/render/verify.py`와 기존 integrated 테스트를 읽어 현행 조립·게이트 소비 경로를 실측했다.
- 합성 2인·무LLM·무렌더 프로브로 현행 섹션 ID 순서를 확인했다: `personal_intro → personal_nature → personal_work → personal_flow → personal_ziwei → personal_consult → integrated_full_depth → relationship_overview`.
- 패킷의 고정 순서(`core → love → job → wealth → health → gunghap → personal_consult → tail`)를 적용하면 `flow/ziwei`와 `personal_consult` 위치가 바뀌어, 동시에 요구된 “modules 미지정/5모듈 전체 = 현행 섹션 ID 리스트·본문 동일”을 만족할 수 없음을 확인했다.
- 결과물이 달라지는 플랜 모순이므로 임의 구현하지 않고 정지 보고했다. 상태 기록 중 패킷 v2가 현행 순서 필터링 방식으로 모순을 해소했지만, 이번 종료 세션에서는 구현을 재개하지 않았다.

### 이번 세션 수정 파일과 기존 잔존 파일 구분

- 이번 Codex 세션 수정 파일: `implementation-notes.md` 1개(현재 상태 기록만). 내용은 외부 프로세스가 `3be5d96`으로 커밋했으며 Codex는 커밋하지 않았다.
- 외부 동시 변경: `handoff/codex-q7-stage1.md`가 `c4443a1`에서 v2로 정정됐다. 설계의 추상 고정 순서를 폐기하고 “현행 순서에서 미선택 모듈만 필터링”하도록 변경해 하위호환 모순을 해소했으며, Codex가 수정하지 않았다.
- 기존 잔존 문서: `handoff/codex-q7-design.md`는 HEAD에 이미 있던 승인 설계이며 수정하지 않았다.
- 구현 후보인 `sajugen/integrated.py`, `sajugen/content/rules.py`, `sajugen/content/delivery_quality.py`, `sajugen/render/verify.py`, 관련 테스트는 수정하지 않았다.
- `sajugen/calc/`, `sajugen/input/`, CLI, admin, 상태머신·발송 차단은 모두 무변경이다.

### 검증·미검증

- 읽기 전용 `git status -sb`와 `git diff --name-only`로 구현 코드 diff 0을 확인했다. 외부 두 커밋 반영 뒤 워킹트리는 깨끗했으며, 이 최종 정합 보정으로 `implementation-notes.md`만 다시 미커밋 상태다.
- 합성 무렌더 조립 프로브는 exit 0이었다. LLM 호출·PDF 재생성·실렌더·ignored 영역 접근은 하지 않았다.
- 코드 변경이 없어 전체 pytest·린트는 실행하지 않았다. Q7 신규 회귀와 기준환경 `728 passed / 4 skipped` 비교도 미실행이다.

### 미완 지점과 다음 스텝

1. 다음 구현 세션은 외부에서 정정된 `handoff/codex-q7-stage1.md` v2 전체를 다시 읽고, 현행 순서 필터링 규칙을 source of truth로 확정한다.
2. 레지스트리·work 제공자·부분 조합 조립·모듈 게이트·content 메타 배선을 구현한다.
3. 5모듈 완전 동일성, N=1~5 분량 경계, missing/unexpected, gunghap 1인 차단/2인 통과, job/wealth 분리 양방 테스트를 추가한다.
4. 대상 테스트와 전체 pytest, Ruff, `git diff --check`, calc/input diff 0을 검증하고 교차리뷰 라운드9에 넘긴다.

### 세션 종료

Codex Q7 1단계 착수 점검·모순 정지 보고·상태 기록 역할을 종료한다. 다음 세션은 정정된 v2 패킷을 기준으로 새 구현 세션에서 재개한다.

---

- E10 인접 탐색: 패킷에 열거되지 않은 `tests/test_relationship_quality_contracts.py` 1줄에서도 대상 이름 잔존을 확인해 tracked 수용 기준에 따라 동일 치환했다.

## 웨이브2 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 현재 HEAD: `fea0e7a` (`Q7 설계 4항목·Q4 문자 하한 운영자 승인 기록`)
- 구현 커밋: `fec5321` (`R6-1 + Q4~Q6 + Q7 설계`)
- 교차리뷰 라운드7 PASS 기록: `a568170`
- 원격 대비: ahead 11. 상태 기록 직전 워킹트리는 깨끗했으며, 이 문서만 현재 세션에서 수정한다.
- 완료 태스크: R6-1, Q4, Q5, Q6 구현. Q7은 승인된 1페이지 설계까지만 완료하고 코드 구현은 하지 않았다.
- 운영자 승인 완료: Q4 문자 하한(gunghap 3000자·followup 2000자), Q7 B안·분량 공식·RELATION 추천·기본 5모듈 전체.

## 웨이브2 완료 내용

- R6-1: `_PROVENANCE_CONTEXT_TERMS=()` 기본 비활성 상태는 유지하면서 합성 용어 monkeypatch로 `unbacked_context_terms` 차단 분기를 고정했다.
- Q4: gunghap 하한을 16쪽/3000자로 분리하고 followup 10쪽/2000자 상품을 추가했다. integrated_full 30쪽/10000자와 premium 10000자는 유지했다.
- Q4: 15쪽·2999자 차단, 16쪽·3000자 통과, 기존 30쪽 하한에서 막히던 18쪽 gunghap 통과를 양방 회귀로 고정했다.
- Q5: `gen-followup --pdf` opt-in 경로를 추가했다. 저장 Report23과 질문 카테고리별 `love/work/health` 근거 장을 재사용하고 새 consult만 조립한다.
- Q5: 연도·주제 범위 밖 질문, 10~15쪽 범위 위반, 저장 일간 부재를 주문 생성 전에 차단한다. 최종 발급도 저장 `bazi` 기반 identity 스펙과 동일 render_verify/delivery_quality를 사용하며 새 계산은 0회다.
- Q5: `--pdf`가 없는 기존 텍스트 주문의 반환·저장 경로는 유지했다.
- Q6: 접수 concern을 7종 QuestionCategory로 자동분류해 주문 메타에 저장하고 관리자 상세에 표시했다.
- Q6: 운영자 확정 POST가 Report23/후속 메타와 audit_log를 갱신한다. concern 있음+GENERAL+미확정 주문은 승인 409, 빈 질문·비GENERAL 주문은 기존 승인 흐름을 유지한다.
- Q6: APPROVED/DELIVERED 상태머신 전이 규칙은 변경하지 않았다.
- Q7: `handoff/codex-q7-design.md`에 모듈 레지스트리 B안, 조립 경계, 분량 공식, 게이트, CLI/admin 계약과 2안 비교를 작성했다. `sajugen/integrated.py` 변경은 0줄이다.

## 웨이브2 구현 파일 전체 목록

- `sajugen/content/delivery_quality.py`: R6-1 주입점 주석, 상품별 페이지·문자 하한, followup 질문 필수 게이트.
- `sajugen/followup/compose.py`: PDF용 저장 섹션 조립, 카테고리별 근거 장 선택, consult 직답·부모 가드 차단.
- `sajugen/order_flow.py`: 후속 PDF 표준 렌더/검증, 저장 일간 identity 복원, 분류 상태·운영자 확정·GENERAL 승인 전제조건.
- `sajugen/cli.py`: `gen-followup --pdf` opt-in 인터페이스.
- `sajugen/admin.py`: 질문 분류 상세 컨텍스트, 확정 POST, 승인 전제조건.
- `sajugen/web_templates/admin_detail.html.j2`: 7종 분류 표시·확정 드롭다운·차단 안내.
- `tests/test_delivery_quality.py`: R6-1 차단 회귀와 Q4 상품별 경계표.
- `tests/test_followup_pdf.py`: PDF 통과/범위 밖/페이지 초과/일간 부재/텍스트 회귀/CLI 배선.
- `tests/test_orders.py`: 접수 자동분류 저장 회귀.
- `tests/test_question_category_admin.py`: GENERAL 차단·운영자 확정·빈 질문/비GENERAL/텍스트 후속 양방 회귀.
- `handoff/codex-q7-design.md`: Q7 승인 전 설계 1페이지.
- `implementation-notes.md`: 현재 웨이브2 상태 기록(이번 사용자 요청으로 추가).

## 기존 잔존 파일과 분리

- `REVIEW-FEEDBACK.md`와 `sajugen/STATE.md`는 구현 파일이 아니라 별도 커밋 `a568170`·`fea0e7a`의 교차리뷰/운영자 승인 기록이다.
- `handoff/codex-question-adaptive-wave2.md`는 시작 HEAD `985031a`에 이미 있던 승인 TASK_PACKET이며 이번 구현 파일이 아니다.
- 웨이브1 Q1~Q3 코드는 커밋 `6126d7a`에 이미 존재했으며 웨이브2에서 재구현하지 않았다.
- `handoff/codex-pii-anonymize-e10.md`와 E10 실명 익명화 대상은 별도 패킷으로 유지했고 웨이브2에서 수정하지 않았다.
- `sajugen/calc/`, `sajugen/input/`, `sajugen/integrated.py`, 상태머신 허용 전이표는 무변경이다.

## 검증 증거

- Codex 샌드박스: `./.venv/Scripts/python.exe -m pytest tests/ -q` -> `701 passed, 31 skipped`, exit 0. 수정 전 688/31 대비 신규 13건 증가, passed 감소 0.
- 기준환경 교차리뷰: 같은 전체 명령 -> `728 passed, 4 skipped`, exit 0. 기준선 715/4 대비 신규 13건 증가, passed 감소 0.
- 기준환경 골든: `pytest -k golden` -> `28 passed`.
- 변경 Python 파일 Ruff -> `All checks passed!`; `py_compile` -> exit 0.
- `git diff --check` -> exit 0(LF→CRLF 안내만).
- `git diff --name-only -- sajugen/calc sajugen/input sajugen/integrated.py` -> 출력 없음.

## 확인하지 못한 것

- 후속 `--pdf`의 실제 10~15쪽 실렌더·조판·다운로드 동선은 미검증이다. 테스트에서는 렌더 엔진을 모의했다.
- 실제 LLM 호출과 LLM-on 문안은 미검증이다.
- Codex는 금지사항에 따라 `harness/profiles/local/**`를 열지 않았고 표준 hrun을 실행하지 않았다.
- 실제 브라우저 수동 UI 검수는 미실행이며 FastAPI TestClient 회귀만 통과했다.

## 남은 위험

- 실제 저장 섹션 길이에 따라 후속 PDF가 15쪽을 넘으면 fail-closed로 차단된다. 운영상 10~15쪽 안에 안정적으로 들어오는지는 승인된 합성 실렌더가 필요하다.
- 저장 `bazi`가 없는 레거시 부모 주문은 identity 게이트를 비활성화하지 않고 후속 PDF를 차단한다. 레거시 처리 정책은 별도 결정이 필요하다.
- admin `action_error` 문구 범용화로 최종 발급 실패 시 “APPROVED 상태 잔류” 안내가 사라진 비블로커가 라운드7에 기록돼 있다.
- Q7 설계는 승인됐지만 구현은 E10 완료 뒤 별도 TASK_PACKET으로 1단계(레지스트리·조립/게이트)와 2단계(CLI/admin)로 나눠야 한다.

## 다음 스텝

1. E10 익명화 패킷을 기준선 `728 passed / 4 skipped`, HEAD `fea0e7a`에서 별도 실행한다.
2. E10 교차리뷰·커밋 뒤 Q7 1단계 구현 패킷을 발주한다.
3. 운영자 승인 시 후속 `--pdf` 합성 실렌더로 실제 페이지 수·조판·게이트를 확인한다.
4. push는 별도 지시 전까지 하지 않는다.

## 웨이브2 세션 종료

Codex 웨이브2 구현·상태 기록 역할을 종료한다. 현재 세션은 `implementation-notes.md`만 미커밋으로 남기고 다음 작업자에게 인계한다.

---

## 웨이브1 기록

## 현재 상태

- 브랜치: `codex/gunghap-relationship-quality`
- 시작·현재 HEAD: `3a30667` (`Q1~Q3 TASK_PACKET v2`)
- 원격 대비: ahead 3. 이번 세션에서 commit·push·deploy 없음.
- 완료 태스크: Q1 관계 consult 이식, Q2 질문별 풀이 분기·실행 경로 PII 제거, Q3 관계 질문축 직답 게이트 강화·고유 키워드 일반화.
- Q4~Q7은 미착수. 패킷 지시대로 웨이브1에서 중단.

## 완료 내용

- Q1: relationship 섹션을 `overview -> consult -> intent` 순서로 조립한다. 빈 질문은 consult를 생략하고 `skipped=True`로 구분한다.
- Q1: 질문 분류를 context·폴백·LLM 작성 방향이 실제 소비한다. consult 원문은 생년월일·시각·출생지 마스킹 뒤 격리 인용한다.
- Q1: consult 후보는 compose 단계에서 검사하고 최대 2회 재작성한다. 모든 후처리 뒤 최종 직답 하드 게이트를 다시 적용한다.
- Q2: 초기 관계·장기/결혼·가족 조율·재회·일반 관계의 5개 결정론 분기를 추가했다. situation에 따라 폴백과 앞부분 요약이 실제로 달라진다.
- Q2: `gunghap.py`에서 재할당으로 죽어 있던 로컬 relationship 구현을 삭제했다. 살아있는 business 시스템 프롬프트·가이드·도크스트링의 타 고객 PII도 합성 예시 또는 일반 서술로 교체했다.
- Q3: 부모 동의·결혼 이행·장기 관계 축을 추가했다. consult는 감지된 질문축 중 하나가 아니라 각 축의 직접 근거를 모두 포함해야 통과한다.
- Q3: 지역 비교·모임/단체·도움을 주는 사람을 일반 트리거로 바꾸고 고객별 고유 키워드 상수를 제거했다.

## 이번 구현 파일

- `sajugen/relationship/context.py`: consult 슬롯, 질문 분류·축·5개 풀이 기준.
- `sajugen/relationship/fallback.py`: 질문별 consult 골격, 겹침축 보강, 앞부분 요약·중립 필러.
- `sajugen/gunghap.py`: 죽은 코드 삭제, PII 제거, 마스킹 인용, LLM 재작성, 최종 consult 게이트.
- `sajugen/content/delivery_quality.py`: 신규 3축과 축별 전수 evidence 판정.
- `sajugen/content/rules.py`: 지역·모임·조력자 일반화.
- `tests/test_question_adaptive_relationship.py`: Q1~Q2 통합·양방·겹침축 신규 회귀.
- `tests/test_delivery_quality.py`: Q3 차단/통과·동치류·기존 축 회귀.
- `tests/test_gunghap.py`: 빈 질문 consult 생략에 맞춘 이웃 회귀.
- `tests/test_llm_sections.py`: 일반화한 합성 맥락 회귀.
- `implementation-notes.md`: 이번 상태 기록.

## 기존 잔존 파일 구분

- 세션 시작 시 워킹트리는 깨끗했다. 위 구현 파일 외 기존 미커밋·미추적 파일은 없었다.
- HEAD에 이미 있던 패킷·설계·리뷰 기록은 이번 세션에서 수정하지 않았다.
- `sajugen/calc/`·`sajugen/input/`은 무변경이다.
- 기존 테스트 픽스처·주석·도크스트링의 PII 전수 익명화는 E10 별도 패킷 범위라 이번 세션에서 건드리지 않았다.

## 검증 증거

- `./.venv/Scripts/python.exe -m pytest tests/ -q` -> `688 passed, 31 skipped`, exit 0.
- 이 샌드박스 직전 기준 `668 passed, 31 skipped` 대비 신규 테스트 20개만 증가, passed 감소 0.
- 기준환경 기준선 `695 passed, 4 skipped`에 대한 예상값은 `715 passed, 4 skipped`; 기준환경 직접 실행은 미완료.
- 관계·질문 적응 관련 대상 테스트 -> 71 passed, exit 0.
- 최초 전체 실행에서 3건 실패를 확인한 뒤 각각 다른 원인으로 수정; 실패 3건 단독 재검증 -> 3 passed, 최종 전체 GREEN.
- Q2 파일 한정 PII 스윕 -> 0건.
- Q3 파일 한정 고객 고유 키워드 스윕 -> 0건.
- `git diff --name-only -- sajugen/calc sajugen/input` -> 출력 없음.
- `git diff --check` -> exit 0. 기존 LF/CRLF 경고만 있음.
- 변경 파일 Ruff 검사(`rules.py` 제외) -> `All checks passed!`.
- 전체 Ruff는 `rules.py`의 이번 diff 밖 기존 오류 17건 때문에 미통과.

## 확인하지 못한 것

- 실렌더 미검증.
- 실제 LLM 호출 미검증. 테스트는 모의 Anthropic 모듈만 사용했다.
- PDF 재생성·`harness/profiles/local/**` 열람·표준 hrun 미실행.
- 기준환경의 `715 passed / 4 skipped` 기대값 미검증.

## 남은 위험

- 실제 LLM 문안과 PDF 조판에서 질문 직답성과 분량이 유지되는지는 신선 컨텍스트 교차리뷰와 합성 실렌더로 확인해야 한다.
- 장기 관계 축은 승인 동치류인 `3년`, `몇 년`, `오래 만난`, `장기`, `오랜 연애`만 자동 분류한다. 다른 숫자 연도 단독 표현은 현재 범위 밖이다.
- 저장소 이력과 기존 테스트 픽스처의 PII 전수 익명화는 E10에서 별도 처리해야 한다.

## 다음 스텝

1. Claude 신선 컨텍스트 `/cross-review`에서 diff와 기준환경 전체 pytest를 검증한다.
2. 합성 실질문으로 표준 실렌더를 실행해 consult 위치·문안·게이트·조판을 확인한다.
3. 교차리뷰 PASS 후 운영자가 웨이브1을 커밋한다.
4. 이후 E10 익명화 패킷을 별도 발주하고, Q4~Q7은 재승인 전 착수하지 않는다.

## 세션 종료

Codex 구현 세션 역할을 종료한다. 워킹트리는 커밋하지 않은 상태로 교차리뷰에 인계한다.

---

# 2026-08-17 — 절입 시각축 결함 규명 · 구현 주체 예외 승인

## 운영자 승인 (AGENTS.md 기본값 이탈)

AGENTS.md 기본 사이클은 `Claude 설계 → Codex 구현 → Claude 교차리뷰` 다.
`solar-term-axis-fix-20260817` 는 **Codex 토큰 소진**으로 그 경로를 쓸 수 없어
운영자가 2026-08-17 예외를 승인했다.

- 구현: **신선 Claude Code 세션** (설계 세션과 분리)
- 검증: **또 다른 신선 Claude Code 세션, read-only**
- 근거 조항: AGENTS.md "운영자가 Claude 구현을 별도로 승인한 경우만 예외다"
- 상세: 패킷 `handoff/tasks/solar-term-axis-fix-20260817.md` §0

Codex 상시 금지(PDF 재생성·LLM 호출·commit·push·배포)는 **Claude 구현에도 동일 적용**한다.

## 이 승인이 성립하는 근거

역할 분리가 노리는 것은 벤더 차이가 아니라 **컨텍스트 독립성**이다. 신선 세션이면 충족된다.
또한 이 패킷의 수용 기준은 전부 기계적으로 측정 가능해 리뷰어 판단력 의존도가 낮다
(기준값 5개 · `eot-window width_min_max == 0` · 골든 22건 · `pytest >= 1136`).

남는 위험은 **같은 모델의 공통 사각**이다. 설계 세션이 실제로 절입 불일치를 처음
"유파 차이"로 오분류했다가 KASI 원본으로 뒤집은 이력이 있다. 이 위험은 패킷이
**KASI 절기 원본을 기준값으로 고정**해 차단했다.

## 함께 해소된 결정

`data/orders.sqlite` 실측: `DRAFTED 3 · IN_REVIEW 1 · NORMALIZED 1`, **APPROVED 0 · 발송 0**.
→ 대운수 0.57% 변동의 **소급 영향 없음**. 결정 2 해소.

## 이 세션이 한 일 / 하지 않은 일

- 한 일: 조사·결함 규명·패킷 작성·증거 이관·커밋·푸시(운영자 승인)
- **하지 않은 일: 코드 변경 0.** `calc/`·`input/` 무수정. 이 세션은 설계자 역할로 종료한다.
- 검증 근거: `pytest tests/ -q` → **1136 passed / 4 skipped / exit 0** (base `444420d` 기준)

## 다음 세션이 할 일

1. 새 Claude Code 세션에서 `이어받아` → manifest·패킷 SHA 검증 후 구현 착수
2. 구현 세션은 **자기 결과를 검증하지 않는다.** 별도 신선 세션이 read-only 검증
3. 커밋·푸시는 운영자 승인 후에만
