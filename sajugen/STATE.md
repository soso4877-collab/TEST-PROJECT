# sajugen 진행 상태 (SSOT) - 세션 시작 시 이 파일 먼저 읽기

> ===== 압축/새세션 재개 앵커 (2026-08-19 시각 미상 경계 패킷 발주 — 이 블록 먼저 읽기) =====
>   [활성] `partner-unknown-time-boundary-20260818` **rev2 · 발주 완료, 구현 대기**.
>     manifest `status=planned / next_actor=claude`, base `c9a5a1f`. 지시문 정본 = `handoff/tasks/partner-unknown-time-boundary-20260818.md`.
>   [역할 3단 분리 — 운영자 승인 2026-08-19] 설계=이 세션(완료) / 구현=**별도 신선 Claude 세션** / 검증=**또 다른 신선 세션 read-only**.
>     Codex 토큰 부재로 Claude 구현 예외(선행 2건과 동일 조건). Codex 상시 금지(PDF·LLM·commit·push·배포)는 Claude 구현에도 동일 적용.
>   [결함] 사연 파싱 상대가 시각 미상이면 `calc/partner.py:157-158` 이 정오를 대입하고, 그 연·월주가
>     `content/rules.py:2146-2153` 에서 "OO년 OO월 OO일생"으로 **단정**된다. `hour_note` 는 시주만 면책.
>     본인은 같은 상황에서 `NEEDS_INFO_TIME_BOUNDARY` 차단(`order_flow.py:598-603`), 구조화 상대 입력은 시각 필수(`:577-578`) — 사연 파싱 상대만 예외.
>   [노출 폭 실측] 경계일 **852일/1960~2030 = 연 12.0일 = 3.29%**, 경계일 시간대의 24.9% 어긋남, 오단정 확률 ≈0.82% [추정].
>     **"18일"은 폐기** — 그건 축 교정이 정오 판정을 뒤집은 날이다(위 2026-08-17 앵커 정정 참조).
>   [운영자 결정 3건] (나)비단정+(다)고지 흡수 / 절대규칙 8-1 = **비단정 원칙만 확장**(차단·provenance·후보 축약 비확장) / 파생 오행 일주 기준 축소.
>     접수 차단(가-1)·인물 생략(가-2)은 **미채택**.
>   [소급 영향] `orders_total=5`, 상대 감지 0건, 최종 발급·DELIVERED 0회 = 피해 0건. 확인 불가 = 삭제 3주문(PII 파기)·store 우회 직접 렌더.
>   [설계 세션 경계] 제품 코드·테스트 수정 **0**. 프로브는 scratchpad(`PYTHONPATH` + `-m`)에서만. commit 1건(문서)·push 0·LLM 0·PDF 0.
>   [다음] 신선 구현 세션이 패킷 §6 구현 + §7 양방 테스트 → 또 다른 신선 세션 read-only 교차리뷰 → 운영자 checkpoint.

> ===== 압축/새세션 재개 앵커 (2026-08-17 상대 명식 시각축 교정 Claude 구현 완료) =====
>   [활성] `partner-axis-fix-20260817` **교차리뷰 CODE_PASS(2026-08-18) · 운영자 checkpoint 커밋 완료**.
>     base `fae34f7` → 커밋 2건: 제품 `1151483`(fix/partner) · 문서 `f357eba`(docs/handoff).
>     **push 0**(사용자 지시 대기), LLM·PDF 재생성 0. 선행 패킷 이월 **F-2 단독** 범위(운영자 승인 2026-08-17).
>   [발주 이력] 이 후속 패킷은 **미발주** 상태였다(handoff/tasks 에 없었고 manifest 는 완료된 선행 태스크를 가리켰다)
>     → 신규 작성 `handoff/tasks/partner-axis-fix-20260817.md`, base=fae34f7. 운영자 확인 2건 응답: 범위 F-2 단독 / myeongni 헬퍼 공개.
>   [결함] `calc/partner.py` 가 진태양시 단일축이라 상대 연·월주가 −14분 이르게 전환(경계 5건 중 2건 오답).
>     `fae34f7` 이후 **본인=교정축 / 상대=미교정축** — 궁합 리포트 한 편 안에서 축이 갈리는 상태였다.
>   [수정] 2파일. myeongni `_split_axis_eight_char` → **공개 `split_axis_eight_char`**(로직·상수·분류표 무변경, 호출부 1행),
>     partner 는 `Solar` 직접 호출·`ct.true_solar` 제거 후 그 헬퍼 호출 + `setSect(1)` 유지 + docstring 을 축 분리 사실로 교정.
>     `ct.utc+8h` 복제 0 — 축 불변식은 myeongni 단일 소스(방법론 B-1).
>   [검증] 전체 **1255 passed / 4 skipped / exit 0**(2026-08-18 재실행 204.7s. 기준선 1227/4 + 신규 28, 감소 0, skip 불변),
>     golden `-k golden` **28**(1231 deselected), 관계 4파일 묶음 **74 passed / 0 skipped**(기준선 불변), Ruff·py_compile exit 0.
>     **교정 전 신규테스트 RED 6 / 20 passed** 는 **rev1 시점(20건 구성) 측정치**이며 rev2 28건 기준 재측정이 아니다
>     (되돌려야 재측정 가능). 검출력 독립 확인은 REVIEW-FEEDBACK 2026-08-18 §3 legacy 대조 4행이 대신한다.
>   [감지 구멍 — 근본원인 2층] partner 에는 교차검증 플래그가 없어(myeongni 의 36/36 False 가 partner 엔 부재)
>     같은 결함이 탐지 신호 없이 잔존했다 → 재발방지 = 본인↔상대 축 일치 불변식 상시 회귀(신규 테스트).
>     `PartnerFacts` 플래그 신설은 문안·factcheck 파급으로 이번 범위 밖.
>   [인접 사각 해소] 시각 미상(정오 대입) × 절입 경계 교집합 — 1960~2030 절입 **1704건 전수에서 18건** 판정 갈림.
>     대표 2건 회귀 고정: 1986-02-04(立春 12:07:41, 교정 전 丙寅 庚寅 → 정답 乙丑 己丑 — 연주까지) · 2011-04-05(淸明 12:11:58).
>     **[2026-08-19 정정 — 이 18건은 노출 집합이 아니다]** 18건 = *이번 축 교정이 정오 대입 판정을 뒤집은 날*(회귀 앵커용).
>     시각 미상이면 연·월주가 갈리는 날 **전체 = 852일/1960~2030 = 연 12.0일 = 3.29%**(오단정 확률 ≈0.82%, [추정] 균등분포).
>     판별 술어는 새 상수표가 아니라 본인 경로와 같은 `three_pillar.ensure_unambiguous_civil_date` 하나다.
>     18일 목록을 키로 삼는 게이트는 **틀린 게이트**. 근거·수치 정본 = REVIEW-FEEDBACK 2026-08-18 §5-정정.
>   [이월] **F-1 대운 start_year 앵커**(0.53~0.83% 이동) 미해결 — 유파 판단+docs/03 변경 필요, 정책 결정 전 회귀 핀은
>     change-detector 라 별도 패킷. `three_pillar.py` −60분 프레임 실오차 0은 **선행 세션 측정 승계**(이번 재측정 아님).
>   [운영자 판단 필요] `docs/16` QI-2026-08-17-01 의 이월 목록이 아직 F-1·F-2 둘 — F-2 해소 반영은 allowed_files 밖이라 미조치.
>   [다음] 별도 신선 세션 read-only 검증(경계 5행·축 일치·74 불변·golden 28·1255/4·헬퍼 복제 0) **완료 = CODE_PASS**
>     (2026-08-18, REVIEW-FEEDBACK 최상단 정본. 비블로커 소견 2) → 운영자 checkpoint 커밋 **완료**(`1151483`·`f357eba`)
>     → 다음 = **F-1 패킷**(대운 start_year 앵커, 유파 판단 선행) · **소견② 패킷 = 발주 완료**(아래 최상단 앵커).
>   [docs/16] QI-2026-08-17-01 이월 목록 갱신 — **F-2 해소(`1151483`) 표기, F-1 만 미해결**로 정리(2026-08-18).

> ===== 압축/새세션 재개 앵커 (2026-08-17 명리 절입 시각축 교정 Claude 구현 완료 · 커밋 fae34f7) =====
>   [활성] `solar-term-axis-fix-20260817` **구현 완료 · 별도 신선 세션 read-only 검증 대기**.
>     base HEAD `0e09a35`, 미커밋. commit·push·LLM·PDF 0. manifest `review_requested / next_actor=claude`.
>   [결함] 상쇄된 두 결함 — (A) lunar-python 절기표가 CST(UTC+8)라 시민 KST 투입 시 −60분,
>     (B) 진태양시를 시민시각처럼 투입 +45.9분 → 합계 −14분. **B만 고치면 −60분으로 악화**.
>   [수정] `calc/myeongni.py` 1파일. `LUNAR_PYTHON_TERM_FRAME_UTC_OFFSET_HOURS=8` + `_SplitAxisLunar` 프록시로
>     **연·월·대운·세운=절대축(ct.utc+8h) / 일·시·자시=국지축(진태양시)**. 두 EightChar 골라담기를 쓰지 않은
>     이유 = 십성·지세·명궁이 '일간 기준' 파생이라 축이 갈리면 正官↔七杀 로 조용히 뒤바뀐다(23시대 ≈4%).
>   [검증] 전체 **1227 passed / 4 skipped / exit 0**(기준선 1136/4 + 신규 91·감소 0), golden **28**,
>     `eot-window-measure.py` **width_min_max = 0**(36절입 전수, 교정 전 최대 41+·평균 27.7),
>     교정 전 코드 대조 신규테스트 **21 failed**(순수 거동 RED 12 + 헬퍼 부재 9). Ruff·py_compile·diff-check exit 0.
>   [영향 재실측] 결정론 3,000건: 연주 0 · 월주 2(0.067%) · 일주/시주 0 · **대운수 21(0.700%)**.
>     패킷 §2-5 는 0.57%(다른 표본, +1σ 범위). APPROVED 0·발송 0이라 소급 영향 없음.
>   [파생 — 운영자 인지] 명리↔자미 불일치(`bazi_consistent=False`)는 `CALC_MISMATCH` 주문 차단으로 이어진다.
>     교정 전/후 동일 측정: 3절입 ±40분 243분 중 **47분 → 48분**(총 폭 불변, 위치만 실제 절입으로 이동).
>     차단 부담 신규 증가 아님 — fail-closed 가 올바른 지점에서 자미 결함을 표면화한다.
>   [인접 사각 — 미수정, 후속 패킷] `calc/partner.py`(궁합 상대)는 **같은 −14분 결함 잔존**(경계 5건 중 2건 오답)
>     → 본인(교정)과 상대(미교정)가 다른 축. `calc/three_pillar.py` 는 −60분 프레임이나 가드가 절입일을 차단해
>     실오차 0(2000년 354일 검사 불일치 0).
>   [다음] 별도 신선 세션 read-only 검증(§6 표 5행·width_min_max==0·골든 28·1227/4·교차검증 완화 0·십성 일간 정합)
>     → PASS 시 운영자 commit 결정 → `docs/16` 등재 여부(패킷 §10-4) → partner.py 후속 패킷.

> ===== 압축/새세션 재개 앵커 (2026-07-20 1e 명리 일간 성격 배선 Claude 구현 완료 — 이 블록 먼저 읽기) =====
>   [진행] 말투 개편 Stage 1: ✅1a(재시도 형식교정) ✅자미 정본 배선 ✅**1e 명리 일간 성격 배선(구현 완료·Codex 검증 대기)**
>     → ⬜1c(폴백 골격 품질) → ⬜1b(회고 검증, 보상 lint 선행) → Stage 1 완료 → 유료 재측정 → Stage 2.
>   [1e Claude 직접 구현] `ilgan-personality-wiring-20260720`. 신규 `content/myeongni_persona.py`(docs/25 단일 소스:
>     10천간 GAN_PERSONA + SINGANG_MODIFIER + ELEM_LACK 양가) + `rules.py` `_ilgan_persona_parts`(문형 _pick·_J) →
>     `character` 다단 인과(일간 성격→신강이 '이 결'을 방향으로→십성 겉/속→신살)·`strength` 없는오행 양가.
>     `llm_sections` nature 가이드 다단 인과+비단정, `_LAYER_WEAVE` 사실특정. ★일간 물상 성격 **B급→비단정**("경향·갈래").
>   [1e 정본] `docs/25-ilgan-personality-research.md`(운영자 canon 승인 2026-07-20). 자미(A급)와 달리 물상론 통속(B/C급)이라
>     문안 톤을 경향/참고로 눌러 배선. docs/03 결정표 행 추가. §3 십성 성격(SS_PERSONA)은 후속.
>   [1e 검증 round-2] 전체 **1136 passed / 4 skipped / exit 0**(기준선 1126/4 +10 신규·감소 0), golden **28**, Ruff·
>     py_compile·diff-check GREEN, calc/input·GATE_KEYS·factcheck 무변경. 신규 10테스트(전수·docs/25 §1-1 렌더 계약
>     전수 오라클·데이터순정+비공허성·신강 modifier+승인 방향·신약 강약프레임0·무중복·양가·다단 인과 비-no-op·persona 가드 전수 격리·비단정·fail-closed).
>   [1e advisor+Codex 수정] advisor 2건(신약 재서술 중복·core 축 생략) + Codex round-1 CHANGES_REQUESTED B-1/B-2/B-3
>     (symbol 보조상징 누락·core/shadow 축 생략·신약 modifier 약함 프레임) 해소: docs/25 §1-1 코드 렌더 계약 신설(표시상징+
>     필수축 전수 동결)·core/shadow §1 축 손실 없이 보강·신약 modifier 강약 프레임 제거. round-2 회귀 사고: 戊 core `큰 그림`
>     =register 금칙(big_picture)→`넓은 시야`로 교체 + persona 격리 테스트를 register/raw_calc/safe까지 강화(감지 갭 봉합).
>   [핸드오프] manifest `review_requested/next_actor=codex`(round-2 재검). base HEAD `4837605`, 미커밋. commit·push·LLM·PDF 0.
>   [다음] Codex round-2 재검(docs/25 §1-1 렌더 계약↔persona 전수·사실슬롯 불변·신약 강약프레임0·비단정·기준선 비감소) → PASS·운영자 commit → 1c.

> ===== 압축/새세션 재개 앵커 (2026-07-17 말투 개편 로드맵 착수 — 이 블록 먼저 읽기) =====
>   [방향 전환] 베타 1호 드래프트(`ord_19f6a87d…`) 육안 검수 결과 톤이 "AI틱"으로 반려 → **베타 발급 보류**.
>     발송은 톤 개선 → 운영자 승인 유료 1회 재측정 → 육안 Z=0 뒤에만. 활성 = **말투 개편 단계형 로드맵**.
>   [플랜 정본] `C:\Users\pc\.claude\plans\virtual-drifting-pond.md`(운영자 승인). 진단(4탐색+2설계 에이전트, 코드 대조):
>     톤 문장 규칙 자체는 목표와 정합, 갭 = **구조(12챕터 독립 병렬 조립·callback 억제) + 폴백 골격 템플릿티 +
>     성격 추론 얕음(자미 별-트레잇 테이블 부재가 최대 결손)**. `builder.py:455-481`(병렬), `report_context.py:40-53,244-249`
>     (anti-callback), `builder.py:640-654`(폴백 강등), `rules.py:1608`(세운 forward-only 필터).
>   [단계형 결정] Stage 1(병렬 유지·저위험) 먼저 → 유료 1회 재측정 → Stage 2(연속서사 아키텍처) 근거 기반 결정.
>     Stage 1 순서: **S0 자미정본 ∥ 1a → 1e/1d → 1c → 1b**. 반드시 살릴 4요소 = 연속서사·대운 연도별 회고검증·
>     명리+자미 겹쳐읽기·폴백 템플릿 제거 + 성격·심리 추론 깊이.
>   [★안전 제약(1b)] `temporal_lint`은 "과거를 미래처럼"만 잡고 "과거를 현재처럼(지금은 2025년)"은 못 잡음 →
>     forward-only 필터가 2026-06-12 QI의 **유일 방어선**. 필터 해제 전 **보상 lint 신설 필수**(완화 아닌 게이트 강화).
>   [★안전 제약(S0)] 자미 별-트레잇은 factcheck가 못 잡는 영역(간지·별·연도만 대조) → **큐레이션 정본 테이블만**
>     (Claude 조사·초안 → 운영자 canon 승인 → Codex 배선). 즉흥 별-의미 = 할루시네이션.
>   [1a 교차리뷰 CODE_PASS 2026-07-17] `temporal-retry-format-feedback-20260717` = **CODE_PASS(Claude 신선), 블로커 0**.
>     정본 = REVIEW-FEEDBACK 2026-07-17 절. manifest verified/next_actor=user 전환. HEAD `d55a006` 유지, 구현 미커밋(운영자 commit 결정 대기).
>     known-time temporal 3타입(month_notation/temporal/relative_month_boundary)은 가드 `why`(정답 형식)를 형식교정 블록으로,
>     safe/style/fact는 회피형 유지. format_types type은 temporal_lint.py만 emit(충돌 0). 삼주는 고정 라벨만 avoid·fix 빈 set(raw/why 누출 0).
>     가드(temporal/factcheck/safe/style)·GATE_KEYS 완화 0, 첫 호출 prompt 불변(비용중립).
>   [1a 검증 실측(기준환경)] 전체 **1114 passed / 4 skipped / exit 0**(기준선 1110/4 +4·감소 0·skip 불변), golden **28**,
>     변경 3 py Ruff All checks passed·py_compile·diff-check GREEN, calc/input diff 0. 테스트 5종 양방·비-no-op·**E2E 팬텀 배선 차단**
>     (실 build_report flow 재시도가 feedback=None·feedback_fix=why 실수신). 미검증 = 실모델 폴백률(운영자 승인 유료 재run 몫).
>   [S0 자미 정본 승인·확정 2026-07-17] 운영자 canon 승인(化氣 뼈대 채택 + 밝기/사화 배정=엔진값·의미만 정본화 + 그늘=대표경향).
>     확정본 스크래치패드 스테이징(→ repo `docs/24-ziwei-star-temperament.md`로 드롭 예정). 1e/1d 배선의 단일 소스.
>   [1a 종결 2026-07-17] 커밋 `222ec1d`(feat content)·`c9396f4`(docs handoff), origin push(`0c93f98..c9396f4`). manifest verified→다음 발주로 교체.
>   [자미 정본 배선 Claude 직접 구현 완료 2026-07-17] `ziwei-temperament-wiring-20260717`(운영자가 Claude 직접 구현 승인).
>     신규 `content/ziwei_temperament.py`(docs/24 §1~§3 단일 소스: 14주성×化氣/기질/그늘 + 밝기 3단 + 사화 4방향) +
>     `rules.py` `_palace_temperament` 헬퍼(문형 _pick 3종) → `_palace_para`(핵심 궁) 배선. ziwei_summary는 오리엔테이션만
>     (명궁 기질 이중 서술 방지 — advisor 발견 수정). 별 이름·밝기·사화 사실 슬롯·factcheck·GATE_KEYS·calc 불변.
>   [자미 배선 검증 실측 round-2] 전체 **1126 passed / 4 skipped / exit 0**(기준선 1114/4 +12 신규·감소 0·skip 불변), golden **28**,
>     변경/신규 5파일 Ruff·py_compile·diff-check GREEN, calc/input diff 0. 신규 12테스트(전수커버·化氣 docs/24 오라클·사화 4축
>     동결·데이터순정+비공허성·비-no-op·밝기/사화 문형 분산·fail-closed·joined 챕터 가드·style 격리·명궁 무중복). advisor 2건
>     +Codex CHANGES_REQUESTED B-1/B-2 수정(명궁 중복·verbatim 반복→_pick / 化氣 印·庫 손실·사화 4축 생략 복원+오라클 테스트).
>   [Codex round-1 = CHANGES_REQUESTED→수정] B-1(docs/24 化氣·사화 손실)·B-2(hwagi/성별 미검) 해소. 사실 슬롯·fail-closed·
>     가드완화0·명궁무중복·문형분산은 round-1에서 이미 PASS 확인됨(CODEX_VERIFICATION_REPORT). Codex 환경 1096/32(sandbox Playwright +28 skip)=split.
>   [핸드오프] manifest `review_requested/next_actor=codex`(Codex round-2 재검). base HEAD `461a0e9`, 미커밋. commit·push·LLM·PDF 0.
>   [다음] Codex read-only 검증 → PASS·운영자 commit 뒤 **1e**(nature/character 다단 인과 + 명리↔자미 사실특정 겹쳐읽기, 이 정본을 프롬프트 근거로)
>     → 1c(폴백 골격 품질) → 1b(회고 검증, 보상 lint 선행) → Stage 1 완료 → 유료 1회 재측정 → Stage 2 판단.
>   [불변 경계] factcheck·temporal_lint 완화 0(1b는 lint 추가). GATE_KEYS 23키 비악화. calc/input 무변경. PII 0.
>     골든 28 count 비감소(1b/1c 바이트 변경 허용). 기준선 1110 passed/4 skipped 비감소.
>   [보류 자산] 베타 주문 `ord_19f6a87d1441cbf1a2a`는 DB 영속(발급 안 함). uvicorn :8766 운영자 터미널 유지.
>     베타 리허설 발견 이슈 6건(admin 폼 integrated_full 누락 등)은 톤 개편 후 별도 fix 배치.

> ===== 압축/새세션 재개 앵커 (2026-07-17 베타 발급 진행 중 — 이 블록 먼저 읽기) =====
>   [활성 작업] 지인 베타 1호 발급 진행 중. 도구 = 관리자 웹 UI(운영자 터미널 uvicorn `sajugen.app:app` :8766, 독립 프로세스·컴팩트 무관).
>   [활성 주문] `ord_19f6a87d1441cbf1a2a` (data/orders.sqlite) = **DRAFTED·gate_pass=True·34쪽·integrated_full(love/job/wealth/health)·별자리0·module_coverage 정상·needs_review=False**.
>     실 LLM 생성됨(calls=18·in51920/out28497·~$1). 폴백 4챕(intro·love·flow·consult)=기존 룰폴백 패턴(게이트 통과, 육안 대상).
>   [다음 = 운영자] ① 상세화면 "드래프트 PDF 다운로드"로 육안 검수(handoff/beta-send-review-checklist.md; 폴백 4챕·금칙·별자리·consult 직답) ② "승인"(APPROVED) ③ "최종 PDF 발급" → DELIVERED.
>     integrated_full 발급 경로는 무과금 룰전용 테스트로 이미 DELIVERED 검증됨(정상). 발급은 운영자 버튼(제 세션엔 LLM 키 없음).
>   [베타 리허설 발견 이슈 = 후속 fix 배치 후보(코드)] (1) admin 접수 폼(`web_templates/admin_list.html.j2:34-35`)에 **integrated_full 옵션 누락**(홈 폼 app.py:56엔 있음) → 베타 제품 admin 접수 불가.
>     (2) 주문 상세 자동새로고침(5s)이 **모듈 확정 체크박스 리셋** → 조작 불가(NORMALIZED blocked 때 "생성 중" 오표시). (3) "모듈 확정 저장"↔"확정 모듈로 재시도" 버튼 혼란.
>     (4) 폼 **LLM 체크박스 미체크→use_llm=False→룰전용→4모듈 26p<28p 하한 미달**(무과금이나 실패·오해 소지; 룰전용 N≥3는 구조적 미달=기존 제약). (5) **레거시 `integrated` 발급 경로 결함**:
>     `final_render_fn`이 integrated_full_meta 미영속(레거시)·모듈 계약 미전달→범용 render_pdf(37p)→`delivery_quality_clean` 실패(integrated_full은 메타 영속되어 정상). (6) 관측 갭: delivery_quality_clean=False인데 delivery_failures=None(레거시 케이스).
>   [비용 실측 2026-07-16~17] 룰전용 생성 2회=$0(calls=0). 실 LLM 생성 1회=~$1(calls=18). 앞선 유료 억제측정 2회 ~$1.8(docs/16 기록). 삭제된 오접수 주문 3건(음력오입력·레거시 오선택×2)은 전부 무과금 룰전용/NORMALIZED.
>   [정리 대기(gitignored·무해)] tmp/deliver_test.py·tmp/deliver_test_orders.sqlite·render/out/final_ord_*·deliver_test PDF. commit=현 세션 코드변경 없음(STATE 이 기록만). repo HEAD `0c93f98`(clean, 서양 가드 종결).

> ===== 압축/새세션 재개 앵커 (2026-07-15 서양 점성술 off-domain 가드 라운드2 재검 CODE_PASS — 이 블록 먼저 읽기) =====
>   [판정] `offdomain-zodiac-guard-20260715` 라운드2 재검 = **CODE_PASS, 미해결 블로커 0**. 정본 = REVIEW-FEEDBACK 라운드2 절.
>     manifest를 `verified / next_actor=user`로 전환. commit·push·API·PDF 없음, HEAD `0325ce7` 유지(Codex 라운드1+2 구현 18파일 미커밋).
>   [B-1 해소 확증] `followup/answer_gate.py check()`에 `western_astrology_lint`가 다른 고객정책 lint와 동일 패턴으로 배선(+7). 라운드1 유출 입력
>     `_DIRECT + 사자자리`을 재실행 → **ok=False·실패 rule=`western_astrology`**(라운드1=ok=True 유출 → 실차단, 우연 아님·비-no-op). 자미 주성/별·관록궁 자리 오탐 0.
>   [경계·회귀] 변경 = `answer_gate.py`+`test_followup_gate.py` 2파일 순수 추가(기존 15종 lint 완화 0). **라운드1 19파일 SHA 전수 불변**(재작업·회귀 0).
>   [기준환경 실측] 전체 **1110 passed / 4 skipped / exit 0**(212.41s, 라운드1 1108/4 +2·감소 0·skip==4 불변), golden **28 passed**.
>     변경 2 py Ruff `All checks passed!`·py_compile·diff-check exit 0, calc/input diff 0. 경계 스냅샷(허용4 제외 21) 시작=종료 무변경.
>   [태스크 종합] 전용 가드가 개인 builder(후보·재작성·룰·최종)+궁합(후보·폴백)+followup 텍스트 게이트+최종 PDF verify() 23키(전 페이지)에 배선 =
>     명리+자미 전용 상품 어느 발급 표면에서도 별자리 off-domain 유출 0(fail-closed). packet §2 목표1·§4·§5 충족.
>   [비블로커 관찰(checkpoint 인지)] verify._verapdf_ua1 범위 밖 죽은코드(F841) 정리(동작 보존). 황도/점성 동음이의어=고정 토큰 계약·fail-closed(무해).
>   [미검증] 실모델 폴백률(closing·followup 별자리 미생성)·실 PDF·300dpi·비용 = 운영자 승인 유료 재run 몫(packet §6, CODE_PASS 밖).
>   [커밋·전진 완료] 제품 `eb112b4`(feat 21파일)·문서 `2908900`(docs handoff 4파일) 커밋+origin push. main `763ed73`→`2908900` fast-forward 전진·push(선형).
>   [억제 재측정 완료 2026-07-15 운영자 승인 유료·합성·PII 0] 4모듈 love/job/wealth/health × known-time integrated_full × 실 Sonnet LLM-on 재현.
>     실 run 2회 모두 **compose 별자리 발화 0**(실모델이 새 프롬프트 억제로 별자리 미생성), 정상 run(concern 포함) **gate_pass=True·33쪽·최종 PDF 별자리 토큰 0**(전수 스캔).
>     잔여 폴백 4챕(intro·work·health·flow)=별자리 아닌 근거밖 간지·맨몸월·완곡어(safe/fact 정상 차단, 기존 패턴). 비용 정상run calls=18·~$0.9. docs/16 QI-2026-07-15-01 추기.
>     → 프롬프트 억제(생성 차단)+하드 가드(유출 차단) 실모델 동시 작동 확정. 첫 run(빈 concern) 게이트 실패는 측정 셋업 산물(별자리 무관).
>   [종결 커밋·전진·정리 완료] 재측정 기록 `b40320d`(docs handoff) 커밋+push, main `2908900`→`b40320d` fast-forward 전진·push. 측정 산출물·tmp 스크립트 삭제(운영자, gitignored). feat=main=origin `b40320d` 동기.
>   [known-time 4챕 폴백 조사 결과 = 수용(비태스크)] intro·work·health·flow 룰 폴백의 원인은 맨몸월(신사월·을미월)·근거밖 간지(경술·임술)로, `llm_sections.py:467-470` temporal 지시가 **이미 맨몸월·서수 표기를 금지**하는데도 실 Sonnet이 종종 생성 → 가드가 잡아 폴백. = 버그 아닌 LLM 불완전 준수의 fail-closed 특성(가드+폴백 안전 담보, gate_pass=True). 개선은 반복 유료 프롬프트 튜닝(ROI 불확실)이라 필수 아님 — 운영자 품질 디벨롭 선택지로 기록.
>   [다음 = 운영자 몫] 코드 백로그 0. 릴리스 준비 완료(1110/4·golden 28·실 4모듈 렌더 gate_pass=True·별자리 0). 다음 = 베타 발급 트랙(docs/23: 지인 N=3 무료) — 표준 게이트→검수 체크리스트(handoff/beta-send-review-checklist.md)→Z=0→APPROVED→수동 발송. 전부 운영자 액션(Claude 육안/발송 불가). Claude/Codex 착수할 코드 태스크 없음.

> ===== 압축/새세션 재개 앵커 (2026-07-15 서양 점성술 off-domain 가드 Claude 교차리뷰 CHANGES_REQUESTED — 이 블록 먼저 읽기) =====
>   [판정] `offdomain-zodiac-guard-20260715` Claude 신선 교차리뷰 = **CHANGES_REQUESTED, 블로커 1건**.
>     manifest를 `changes_requested / next_actor=codex`로 전환. commit·push·API·PDF 없음, HEAD `098b737` 유지(Codex 미커밋 20파일).
>   [기준환경 실측] 전체 **1108 passed / 4 skipped / exit 0**(217.12s, 기준선 1071/4 +37·감소 0·skip 불변, Codex 기대 1108/4 정확 일치),
>     golden **28 passed**. 변경 16 py Ruff `All checks passed!`·py_compile·diff-check exit 0. calc/input diff 0. 경계 스냅샷(허용 4파일 제외 19) 시작=종료 SHA 무변경.
>   [블로커 B-1] **followup 텍스트 발급 게이트가 신규 하드 가드 우회 = 유출 가능**. `followup/answer_gate.py:179-204 check()`가
>     15종 고객정책 lint(external_domain 포함)를 돌리면서 `western_astrology_lint`만 누락. `compose.py:229`가 followup 답변의 유일 텍스트 게이트,
>     `:256 if not pdf: return`으로 pdf=False(텍스트 전용) 답변은 이 게이트만 통과하면 발급(`run_followup` 기본 pdf=False → `cli gen-followup`이 answer emit+order 생성).
>     **실행 확증**: 통과 픽스처 `test_followup_gate._DIRECT`(ok=True)에 `사자자리 기질` 문장 주입해도 **ok=True/failures=[]**(유출), `western_astrology_lint`는 잡음·`answer_gate`는 못 잡음.
>     PDF 경로는 `_render_followup_pdf`→verify() 23키로 안전하나 텍스트 경로는 render 백스톱 없어 answer_gate가 최종 게이트 = 현재 **프롬프트 억제만**(태스크가 부족하다 선언한 구성).
>     수정 = `answer_gate.check`에 `western_astrology_lint.lint` 추가(다른 _add_hits 패턴 동일, rule=western_astrology·hard) + test_followup_gate 양방(별자리 차단·자미 주성/별 오탐 0). 완화 0.
>   [사양 충족(재작업 불필요)] 전용 `western_astrology_lint`(최장토큰 우선 정규식·컴파운드 12종+사수/궁수·별자리/황도/점성) 로직·프로브 차단 3/3·오탐 0/6,
>     개인 builder 4소비처·궁합 후보+폴백 배선, GATE_KEYS 23키(동결 22→23)·전 페이지 실PDF 게이트(clean=False·gate_pass=False 실측), integrated/relationship 재시도 판정,
>     hverify/hsummary PII-free 관측, `_COMPOSE_SYSTEM` SHA 핀 독립 재계산 `76e1645d…fa32d` 정확 일치(known·삼주 파생 금지 보존). docs/16 QI·docs/20 23키 레지스트리 정확.
>   [비블로커 관찰] (1) `verify._verapdf_ua1` packet §7 범위 밖 죽은코드(base=None F841) 정리 — 동작 보존·Ruff GREEN, checkpoint 시 scope 인지.
>     (2) 황도/점성 동음이의어는 고정 토큰 계약 대상·fail-closed(무해). 의미적 우회는 계약 밖(미검증).
>   [미검증] 실모델 폴백률·실 PDF·300dpi·비용 = 운영자 승인 유료 재run 몫(packet §6 분리). B-1 수정 후 followup 텍스트 실차단 = 라운드2.
>   [정리] 발주 커밋 `098b737` 메시지 '발주(planned)'↔커밋 manifest review_requested 레이스는 이 판정에서 changes_requested/codex로 정리(정본=REVIEW-FEEDBACK 2026-07-15 절).
>   [다음] Codex가 REVIEW-FEEDBACK B-1만 수정(followup answer_gate 배선+양방) → Claude 라운드2 재검. 그 전 commit·push·유료 run 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-15 서양 점성술 off-domain 가드 Codex 구현 완료) =====
>   [판정] `offdomain-zodiac-guard-20260715` = **EVIDENCE_SPLIT_PASS / review_requested / next_actor=claude**.
>   [루트커즈] 기존 `safe_lint` 9규칙에 별자리·황도·점성 토큰 0. 프로브 3종은 수정 전 safe/style/external-domain 전부 0으로 유출 가능. 유료 run의 `safe=1` raw match는 기록 부재·ignored 비열람으로 확정 불가(합성 `운명이 정해졌` 우연 catch만 재현).
>   [구현] `western_astrology_lint`(황도 12궁 12종+사수/궁수 별칭, 별자리/황도/점성) → 개인 후보·재작성·룰·최종 집계 + 궁합 후보·폴백 배선. `_COMPOSE_SYSTEM`/closing 억제. 최종 전 페이지 `western_astrology_clean`을 GATE_KEYS 23번째 AND 키로 추가하고 hverify/hsummary·integrated/relationship 재시도·docs/20/22 동기화.
>   [양방] 프로브 3종·12궁 전부 차단. `관록궁 자리`·bare 자리/사자/게/처녀궁/물고기·자미 주성/별 오탐 0. 실제 PyMuPDF 임시 PDF에서 해당 clean=False·gate_pass=False.
>   [검증] 집중 **213/1**, 전체 **1080 passed / 32 skipped / exit 0**(직전 1043/32 +37·기존 감소 0·skip 불변, 총 1112), golden 28, Ruff/py_compile/diff-check GREEN, calc/input diff 0. 기준환경 기대 **1108/4**는 Claude 확정.
>   [금지] API/LLM·운영 PDF·local profile·ignored 고객 산출물·commit·push·deploy 접근 0. 다음 = Claude 신선 교차리뷰.

> ===== 압축/새세션 재개 앵커 (2026-07-15 서양 점성술 off-domain 가드 태스크 발주 — 이 블록 먼저 읽기) =====
>   [활성 태스크] `offdomain-zodiac-guard-20260715` = `planned / next_actor=codex`, packet SHA `07f47dac…`.
>     하네스 모듈 계약(직전) = 종결(verified·소스+양방+런타임 3중 확증·커밋 push 완료).
>   [발주 근거·실측] 4모듈 LLM-on 유료 확인에서 closing이 서양 별자리(쌍둥이/게/사자자리+양력) 생성. **전용 가드 부재**
>     (sajugen/content grep 0·factcheck fact=0), 그 인스턴스는 safe_lint 우연 catch. **유출 프로브 확정**: 깨끗한
>     별자리 문장 3종 safe=0·style=0 = 전 가드 통과(유출). → benign 아님, off-domain 미커버 갭.
>   [목표] (1) 서양 점성술 전용 하드 가드 추가(fail-closed·유출 0, compose 체인+최종 게이트 배선) (2) 프롬프트 억제.
>     명리/자미 정상어(관록궁 자리·사자獅子·주성·별) 오탐 0 양방 필수. 기준선 1071/4 비감소.
>   [Codex 구현 도착 2026-07-15 — 레이스] 위 발주 직후 Codex가 zodiac-guard 구현 완료 → manifest
>     **`review_requested / next_actor=claude`**. 신규 `sajugen/content/western_astrology_lint.py` + builder·llm_sections·
>     gunghap·integrated·relationship/context·render/verify·hsummary·hverify_pdf + 테스트(신규 test_western_astrology_guard 등)
>     + docs 16/20/22·implementation-notes 갱신 = **working tree 미커밋**(base HEAD `098b737`).
>   [주의·정리 필요] 발주 커밋 `098b737`은 메시지가 '발주(planned)'이나 커밋 시점 manifest는 이미 Codex의 review_requested였다
>     (레이스). 이 STATE의 구 '[다음] Codex 구현' 문구도 그 시점 것. 실제 = Codex 완료·**Claude 교차리뷰 차례**. 리뷰 커밋에서 정리.
>   [다음 = Claude 신선 교차리뷰] manifest SHA·base 재검증 → diff 전량(이번엔 content 가드 추가라 제품 diff 있음) →
>     기준환경 pytest 1071/4 비감소·golden 28 → **별자리 유출 0 실증**(§1 프로브 차단) + 명리/자미 정상어 오탐 0 +
>     factcheck/safe/style 기존 룰·게이트 비악화. PDF 재생성·LLM·commit·push 금지(리뷰어 편집=허용 4파일).

> ===== 압축/새세션 재개 앵커 (2026-07-14 하네스 모듈 계약 Claude 교차리뷰 CODE_PASS — 이 블록 먼저 읽기) =====
>   [판정] `beta-1-hverify-module-contract-20260712` Claude 신선 교차리뷰 = **CODE_PASS**.
>     manifest를 `verified / next_actor=user`로 전환. commit·push·API·PDF 없음, HEAD `519fc61` 유지(Codex 미커밋 8파일).
>   [기준환경 실측] 전체 **1071 passed / 4 skipped / exit 0**(226.51s, 기준선 1061/4 +10·감소 0·skip 불변),
>     golden **28 passed**. 변경 5 py Ruff All checks passed·py_compile·diff-check 0. **제품 diff 0**(sajugen/** 변경 0).
>   [배선] hverify가 3원자(selected_modules·module_sections·premerge_section_ids)를 V.verify 전달, 레거시 None→
>     제품 5모듈/30p 복원(회귀 0). 계약은 제품 sajugen.modules 정본 fail-closed(PDF 검사보다 먼저·조용한 보정 없음).
>   [자문 사각 확인] 테스트가 V.verify mock이라 실 `verify.py:484-485` 시그니처·`719-720` analyze 전달을 **소스로 확인**
>     → A-5 팬텀 재발 아님. 런타임 증명은 §7.3(운영자 hrun) 몫.
>   [§4 양방·비-no-op] 4모듈=28p / 레거시=30p(captured kwargs 전달 실증·제품 module_minimums 실호출), fail-closed
>     (3중잠금 열려도 regen 차단=pytest.fail), gunghap 혼입 차단, argv, pytest.skipped 보존, hsummary 4종. 경계 8파일 불변.
>   [§7.3 런타임 확정 2026-07-14 운영자 지시·무LLM·무과금·합성] rule-only 합성 4모듈 PDF + 제품 module 메타로
>     실 hverify 2회: 모듈 프로파일 **minimum_pages=28·9000·contract_errors=null**, 레거시(같은 PDF) **30·10000**.
>     → 실 V.verify가 3원자 소비해 4모듈 하한 실적용·레거시 5모듈 = 갭 해소 런타임 확증. docs/16 QI-2026-07-14-01 추기.
>   [커밋·push] 구현 `26026ab`(fix harness)·리뷰 `5e61601`(docs handoff) 커밋+origin push 완료. §7.3 doc 갱신(docs/16·STATE)은 미커밋.
>   [표준 발급 회귀 감사 2026-07-15 무과금·합성] rule-only N=2 integrated_full 실렌더→실 verify:
>     **gate_pass=True·실패 게이트 키 0·24p**(N=2 하한 20p). 831→1071 누적 게이트/문안 변경이 결정론 발급
>     경로를 fail-closed로 깨지 않음 확인(실렌더 층).
>   [4모듈 LLM-on 유료 확인 2026-07-15 운영자 승인·합성·PII 0] 실 베타 상품(known-time 4모듈 love/job/wealth/health
>     integrated_full × use_llm) 1회 생성: **gate_pass=True·실패 게이트 키 0·31p**(하한 28p), 비용 19콜·출력 32,406 tok
>     (~$1). → 실 LLM-on 베타 상품이 현재 HEAD에서 발급 가능·회귀 0 확정. 단 compose 9챕 중 4개(love·flow·consult·
>     closing) 룰 폴백(실 Sonnet이 근거밖 간지·맨몸월·단정·**서양 별자리 off-domain** 생성→가드 차단 유출0→폴백 통과).
>     closing 서양 별자리는 benign 신규 관찰(가드 담보)·후속 품질 후보(필수 아님). 실 문안 육안은 운영자 몫.
>   [다음] 태스크 실질 종결(갭 해소 소스+양방+런타임 3중 확증). 코드 백로그 소진 — 대기 Codex 태스크 0.
>     남은 진짜 선택지 = (운영자) 4모듈 LLM-on 유료 확인 or 베타 발급 트랙(육안→APPROVED→발송). 발송은 검수 Z=0 뒤에만.

> ===== 압축/새세션 재개 앵커 (2026-07-14 하네스 모듈 계약 태스크 재활성 — 이 블록 먼저 읽기) =====
>   [활성 태스크 전환] 삼주 실모델 품질 후속(`three-pillar-real-model-quality-followup`) = 종결(verified·커밋 `2d91933`까지 push).
>     보류였던 `beta-1-hverify-module-contract-20260712`를 **재베이스라인 후 재활성**(삼주 라인 종결로 보류 해제).
>     manifest = `planned / next_actor=codex`, packet SHA `15030847…`, base `2d91933`.
>   [갭 실측] HRUN_EVIDENCE_INVALID_MODULE_SPEC_GAP **현재 HEAD에 잔존 재확인**: `hverify_pdf.py:178` `V.verify(...)`에
>     `selected_modules` 미전달·`hrun.py` module 참조 0·비-local 프로파일 modules 필드 0 → 모듈 제한 주문을 5모듈 스펙으로
>     오판(거짓 `premium_pages` FAIL). 제품 경로는 Q7에서 배선됨 — **갭은 하네스 증거 경로 한정**(실 발급 게이트 무관).
>   [재베이스라인] 패킷 §1·§6 기준선 949/4→**1061/4**·base→`2d91933`. §7.3은 소멸한 옛 replacement PDF(SHA `63383335…`)
>     의존을 제거하고 **합성 모듈 제한 픽스처**로 재정의(무과금). 핵심 계약 §2~§5 불변. 제품/calc/input diff 0 계약.
>   [다음] Codex가 §2~§7.1 원자 배선(프로파일 modules→hverify/verify 전달+fail-closed+hrun --module argv+hsummary 관측+
>     pytest.skipped 갭) + §4 양방 테스트 → Claude 교차리뷰. PDF 재생성·LLM·commit·push 금지.
>   [미커밋] 재베이스라인 패킷·manifest·이 STATE 갱신은 working tree(미커밋) — 운영자 commit 지시 대기.

> ===== 압축/새세션 재개 앵커 (2026-07-14 삼주 실모델 품질 후속 Claude 교차리뷰 CODE_PASS — 이 블록 먼저 읽기) =====
>   [판정] `three-pillar-real-model-quality-followup-20260714` Claude 신선 교차리뷰 = **CODE_PASS(no-LLM/mock 층)**.
>     manifest를 `verified / next_actor=user`로 전환. commit·push·API·PDF 없음, HEAD `74e94e5` 유지.
>   [기준환경 실측] 전체 **1061 passed / 4 skipped / exit 0**(241.31s, 기준선 1049/4 대비 +12·감소 0·skip 불변),
>     golden **28 passed**. Codex 기대값 1061/4와 정확 일치. 변경 5 py Ruff All checks passed·py_compile·diff-check 0.
>   [경계] diff=packet §7 정합. calc/input·`render/verify.py` 게이트·factcheck/safe/style·`GATE_KEYS` 변경 0(실측).
>     억제 강화는 **생성 측 한정**(삼주 게이팅/삼주 파생 system 전용, known `_COMPOSE_SYSTEM`·temporal else 바이트 불변·SHA 핀 GREEN).
>     §5 양방·비-no-op: 억제 지시 SDK realized 캡처(누락자리 비호명 소비 증명), 조사 `_J` 실골격 양방(`정축이`/`무는`),
>     표지 h1 CSS 계약. 경계 read-only 7파일 시작/종료 SHA 불변.
>   [비차단 scope 플래그] Codex가 rules.py 기존 Ruff 부채(F541 16+F841 1)를 packet scope 밖에서 정리 —
>     바이트 불변 검증(F541 자명·`day_sg` 미사용·golden 28), "변경 Python Ruff GREEN" 조건 충족. checkpoint 시 운영자 scope 인지.
>   [⚠️ CODE_PASS ≠ 품질해결] no-LLM 층은 프롬프트 금칙 부재·억제 지시 존재·조사 결정론만 증명. **packet 목표 #1(실 Sonnet
>     4챕터 폴백률↓)은 이 층에서 증명 불가** → 운영자 승인 유료 재run(§6·§8)이 폴백률·조사 육안의 게이트다.
>   [유료검증 #2 2026-07-14 운영자 승인·fix 후·합성·PII 0] 동일 조건 재run 1회: **폴백 4개→1개**
>     (nature·flow·consult 해소 = 실 Sonnet `시주`·맨몸월 생성 중단·프롬프트 억제 실모델 작동 확정).
>     잔여 intro 폴백은 원인 전환(§12 메타 아닌 safe_lint 단정 1건·guard 정상·유출 0). `gate_pass=True` 유지.
>     PDF 실측: 금칙 0·mojibake 0·병기 0·고지 1회·3열·18쪽. **조사 교정 확정**(己卯→기묘는·丁丑→정축은·壬→일간 임은,
>     `정축가` 결함 소멸). 비용 12콜·출력 12,859 tok(~$0.30). **표지 h1 개행 육안 해소 확인**(산출 PDF 표지 300dpi
>     렌더 실측 — `사주도령 통합 사주와 / 관계 풀이` 어절 경계 개행·`관계` 온전, 음절 중간 개행 소멸). docs/16 QI-2026-07-13-02 추기.
>   [커밋·push] 제품 `eaf6b62`(fix content)·문서 `fcf9396`(docs handoff) 커밋+origin push 완료(2026-07-14 운영자 지시).
>     유료검증 #2 doc 갱신(docs/16·STATE)은 미커밋 — 운영자 commit 지시 대기.
>   [다음] 태스크 실질 종결(품질 개선 실모델 확정). 실고객 발송은 표준 게이트→검수 Z=0 뒤에만. 통과 전 APPROVED·발송 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-14 삼주 실모델 품질 후속 Codex 구현 완료 — 이 블록 먼저 읽기) =====
>   [현재] `three-pillar-real-model-quality-followup-20260714` 활성 packet 구현·자체 검증 완료.
>     시작 HEAD `74e94e5`, commit·push·API·운영 PDF 재생성 없음. Claude 신선 교차리뷰 요청 단계.
>   [루트커즈] intro는 삼주 system·temporal이 관측 메타 어간을 직접 재노출. nature·consult는
>     “제외 범위 설명” 지시가 빠진 시간 자리를 호명하도록 유도하면서 비호명 계약이 없었다.
>     flow·consult는 기준일 블록이 맨몸 `7월` 3회·`12월` 1회를 직접 주입했다. 조사 오류는
>     삼주 nature 한 문형의 `{month_gz}가`·`{day_gz}가` 하드코딩으로 `_J`를 우회한 것이 원인.
>   [수정] known 바이트는 유지하고 삼주 파생 system·override·temporal만 억제 강화. 삼주 골격의
>     일간·연/월/일주 조사를 `_J`로 결정하며 메타 유도 문구를 직접 화법으로 정리. 표지 h1 keep-all 3종 추가.
>   [검증] 구현 전 prompt 4+nature 조사 1+h1 CSS 1 RED. 수정 후 핵심 **17 passed**, 인접 **81 passed**,
>     전체 **1033 passed / 32 skipped / exit 0**(이 환경 1021/32+신규 12, 감소 0), golden **28 passed**.
>     기준환경 기대 1061/4와 총 수집 1065 일치. 변경 Python Ruff·py_compile·diff-check GREEN,
>     known `_COMPOSE_SYSTEM` SHA와 known user bytes 핀 GREEN.
>   [불변/미검증] calc/input·factcheck/safe/style·verify/GATE_KEYS 변경 0. 고객/local/ignored 비접촉.
>     실모델 폴백률 감소·실 PDF 조사·표지 육안은 운영자 승인 유료 재run/Claude 증거 몫으로 분리.
>   [다음] Claude가 diff 전량·기준환경 1061/4·게이트 비악화를 교차리뷰한다. 그 전 commit·push·유료 run 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-14 삼주 근거화 Claude 교차리뷰 PASS — 이 블록 먼저 읽기) =====
>   [판정] `three-pillar-llm-grounding-fix-20260713` Claude 신선 교차리뷰 = **CODE_PASS(no-LLM/mock 층)**.
>     manifest를 `verified / next_actor=user`로 전환. commit·push·API·PDF 없음, HEAD `c4cd93b` 유지.
>   [기준환경 실측] 전체 **1049 passed / 4 skipped / exit 0**(기준선 1036/4 대비 +13·감소 0·skip 불변),
>     golden **28 passed**, 집중 4+1테스트 **62 passed**. 변경 Python 9파일 py_compile·diff-check exit 0.
>     Ruff: rules.py 기존 17건(F841 1+F541 16) HEAD==worktree 구성 동일=신규 0, 다른 8파일 GREEN.
>   [경계] diff=packet §7 정합. calc/input·verify.py 게이트·factcheck/safe/style lint 변경 0(실측).
>     §4 known-time 바이트 보존은 `_COMPOSE_SYSTEM` SHA 핀 테스트로 고정. §5 6개 필수 테스트 양방·비-no-op
>     (fail-closed는 API 도달 시 pytest.fail, usage 7/2/1 vs 0/0/0, factcheck 전량 부재). concern_text 생산
>     경로 배선 확인(A-5 팬텀 아님). `_retry_feedback_labels` consult_direct 분기 live.
>   [비차단 finding] Codex notes의 full HEAD SHA(c4cd93b17421f781…)가 실제 HEAD(c4cd93b17421c408…)와 12자
>     이후 불일치 → notes에서 정정(short prefix는 정확해 리뷰 대상 영향 0).
>   [정적확인] classify `strict=True`는 유효 GA 필드(top-level, no beta)로 확인, Haiku 4.5 지원 범위 → 400 위험 없음.
>   [유료검증 2026-07-14] 운영자 승인 유료 재run 1회(합성 9축 복합고민 × 삼주 integrated_full × [job,wealth,health]):
>     **gate_pass=True**(사고 delivery/style 실패 해소 실모델 확정). 최종 PDF 금칙토큰 0·고지 1회·3열·12쪽,
>     비용 15콜 약 $0.33. 단 compose 9챕 중 4개(intro·nature·flow·consult) 룰 폴백 — 실모델이 여전히
>     시주·맨몸월표기 생성→guard 차단(유출0)→폴백 통과. 프롬프트 억제 100% 아님(guard+fallback이 담보).
>     육안 nit 2: 표지 h1 관|계 개행, 본문 조사 정축가/임신가. → 후속 품질 packet(draft) 분리.
>   [다음] 운영자: 후속 품질 태스크(three-pillar-real-model-quality-followup) 승인 여부 결정. 실고객 발송은
>     표준 게이트→검수 Z=0 뒤에만. 통과 전 APPROVED·발송 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-13 삼주 LLM 근거화 구현 완료 — 이 블록 먼저 읽기) =====
>   [현재] `three-pillar-llm-grounding-fix-20260713` packet 구현·Codex 자체 검증 완료.
>     manifest는 `review_requested / next_actor=claude`로 전환해 신선 교차리뷰를 요청한다. commit 없음, HEAD `c4cd93b` 유지.
>   [수정] 삼주 compose의 고정 예시·금칙 개념 유도원을 제거하고 장별 fact source scope를 API 전 fail-closed했다.
>     retry에는 거부 원시 토큰 대신 고정 사유만 전달한다. 룰 폴백은 기존 concern 축 추출기와 실제 세운 연도를 써
>     복합 6축·단일 축·무축 경계를 닫는다. 오류 종료도 PII-free `llm_usage`를 최신 report에 영속한다.
>   [classify] 사고 당시 `InstructorRetryException`의 내부 원인은 로그 부재로 확정 불가(schema 오류와 일시 API 오류가
>     같은 외부 예외로 래핑됨). 설정 취약점은 direct strict tool·강제 enum/required·추가필드 금지·SDK retry 0으로 보강했다.
>   [검증] 전체 **1021 passed / 32 skipped / exit 0**(Codex 기준선 1008/32 대비 +13·감소 0), golden **28 passed**.
>     집중 14+11+34+3, 인접 60/1s. 변경 Python 8파일 Ruff GREEN, `rules.py` 기존 17건은 HEAD와 동일해 신규 0,
>     py_compile·diff-check exit 0. calc/input·factcheck·safe/style·verify gate 변경 0.
>   [불변/미검증] API·LLM·PDF·고객 데이터·local profile·commit/push/deploy 접근 0. 실모델 삼주 `gate_pass=True`,
>     실제 PDF·비용·300dpi 육안은 미검증이며 운영자 승인 유료 재run/Claude 환경 증거로 분리한다.
>   [다음] Claude가 diff 전량·기준환경 전체 pytest·게이트 비악화를 교차리뷰한다. PASS 뒤 운영자 승인 전에는
>     유료 재run·APPROVED·발송을 실행하지 않는다.

> ===== 압축/새세션 재개 앵커 (2026-07-13 삼주 replacement 유료 run 게이트 실패 — 이 블록 먼저 읽기) =====
>   [현재] 운영자 승인 유료 파이프라인 1회 실행. 저장 order#2(생시미상 실고객, brand=seodam, 레거시 정오 결함)를
>     원본으로 three_pillar `integrated_full`+[job,wealth,health] replacement 1건 생성(익명 `DOC_1F3817DC9C`).
>     결정(운영자): brand=seodam, 상품/모듈 확정. concern은 저장값(len 889). order#2 불변 실측(DB 3→4, 신규 1건만).
>   [결과] `DRAFTED` 실패·`NORMALIZED` 정지·PDF 미생성. `gate_pass=False`,
>     `failed_clean_flags=[delivery_quality_clean, style_clean]`, `delivery_failures=[missing_question_axes]`(+low_density 절단).
>     classify `InstructorRetryException`→룰폴백; flow·consult·closing LLM출력 가드거부(factcheck 삼주금칙 `시주`·근거밖 월주)→룰폴백.
>   [원인] 삼주 LLM 콘텐츠 경로가 허용출처 밖 토큰 생성→가드 정확 차단→룰폴백 본문이 고민 topic축·style 미충족.
>     게이트 fail-closed 정상(유출 0) = 구현 결함(Codex 영역). `missing_question_axes`는 concern 기반(모듈 독립).
>   [비용] 오류경로 `llm_usage` 미영속(order_flow run_generation 성공 경로만 저장)→호출·토큰·비용 미포착.
>     권위=Anthropic 대시보드. 과금은 발생(classify 재시도+3챕터+모듈 compose).
>   [기록] docs/16 QI-2026-07-13-02 등재. 신규 order = NORMALIZED+모듈확정 상태 = create 없이 `run_generation` 재호출로 재시도 가능(여전히 1건).
>   [다음] 운영자 결정=구현결함 처리. Codex TASK_PACKET(삼주 LLM 근거화·오류경로 usage 영속·실복합 고민 gate_pass 회귀) 발주.
>     hrun/hsweep=PDF부재로 미실행. commit·콘텐츠코드수정=미착수(운영자 승인 시). 유료 재시도=미승인.

> ===== 압축/새세션 재개 앵커 (2026-07-13 표지 keep-all·낙관 안전 여백 checkpoint 종결 — 이 블록 먼저 읽기) =====
>   [최종] `cover-sub-keepall-20260713` = **EVIDENCE_SPLIT_PASS / checkpoint 완료**.
>     제품 `2fc7309`(template+E2E 2파일), 역할 계약 `7ff7f56`(AGENTS 1파일). push 없음.
>   [검증] Claude 기준환경 **1036 passed / 4 skipped**, test_p8 3 passed, golden 28.
>     Codex 환경 **1008 passed / 32 skipped**, golden 28, Playwright test_p8 3 passed,
>     최종 unknown-time 실제 좌표 E2E 1 passed, Ruff·py_compile·diff-check GREEN.
>   [시각] 합성 표지 PDFium PNG 육안 PASS. 음절 분리·잘림·낙관 겹침·깨진 글자 0.
>     고지문 우단↔실제 낙관 image bbox 수평 여백 약 **4.16mm**(계약 하한 2mm).
>   [계약] 권위 packet은 manifest SHA로 고정된 `handoff/tasks/cover-sub-keepall-20260713.md` 하나.
>     미고정 confirm packet은 실행·commit 제외. 과거 beta-2 누적 확인 항목은 이번 태스크로 재이월하지 않는다.
>     아래 라운드23 이하의 `next_actor`·`next_action`은 당시 역사이며 모두 이 최상단 앵커로 대체됐다.
>   [미검증] 실고객 PDF·300dpi·API·hrun·hsweep·APPROVED·발송. 고객 데이터 비접촉.
>   [다음] handoff `done / next_actor=none` 종결. push·실고객 작업은 운영자 별도 승인 시에만.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드23 표지 keep-all 재검증 CODE_PASS — 이 블록 먼저 읽기) =====
>   [판정] 라운드23 재검증(Claude 신선) = **승인(CODE_PASS), 미해결 블로커 0**. 정본 = REVIEW-FEEDBACK 라운드23 절.
>     기준환경 전체 pytest **1036 passed / 4 skipped / exit 0**(215.66s), golden 28, test_p8 3/3 Playwright
>     실렌더 PASSED(unknown_time 포함 skip 아님, `_assert_gate`로 세 상품 gate_pass=True).
>     변경 = 제품/테스트 2파일뿐(`.cover .sub` keep-all +1줄 · test_p8 공백 보존 단언 +1줄·도크스트링).
>   [양방 증거] keep-all 임시 제거 → test_e2e_unknown_time line 111(공백보존) RED / line 110(무공백) GREEN
>     — 새 단언 no-op 아님·라운드21 음절 중간 개행 재현. 복원 후 template diff = keep-all +1줄(정확 복원).
>     표지 추출: 고지 유일 개행 = `세부\n해석은`(어절 경계), 무공백·공백보존 count 각 1.
>   [미검증] 표지 좌우 균형·시각 품질 = layout_geometry 이 환경 skip(자동 게이트 밖·운영자 육안 몫).
>     실API·고객 PDF·hsweep·300dpi·육안 Z=0 — CODE_PASS 범위 밖. 합성 산출물 외 PDF 0. commit·push·API 없음.
>   [다음] manifest review_requested / next_actor=codex → **Codex 신선 read-only 확인**
>     (지시문 `handoff/tasks/cover-sub-keepall-codex-confirm-20260713.md`) → PASS 시 운영자 checkpoint commit 결정.
>     확인 3건: ① 스코프 밖 변경 2건 ② 삼주 delivery 하한 12쪽/3,500자 ③ 표지 고지 좌우 균형 육안.

> ===== 압축/새세션 재개 앵커 (2026-07-13 표지 keep-all 수정 완료 — 이 블록 먼저 읽기) =====
>   [현재] 패킷 §1~§2 구현 및 Codex 환경 검증 완료. 정본 =
>     `handoff/tasks/cover-sub-keepall-20260713.md`. Claude 실렌더 신선 재검증을 요청한다.
>   [수정] `.cover .sub`에 keep-all 3종만 추가하고, test_p8 unknown_time에 공백 보존 고지 원문
>     1회 단언을 기존 무공백 층과 함께 고정했다. 도크스트링에 검증·비검증 경계를 명시했다.
>   [Codex 실측] 시작·종료 전체 **1008 passed / 32 skipped / exit 0**(감소 0), golden **28 passed**,
>     test_p8 **3 skipped**(통과 아님). E2E RED/GREEN·gate_pass·layout_geometry는 미실측이다.
>     변경 Python Ruff·py_compile·diff-check GREEN.
>   [불변] verify/게이트/lint/고지 문안/@page/다른 조판·테스트/REVIEW-FEEDBACK 불변.
>     API·LLM·고객/실상품 PDF·hrun·hsweep·commit·push·APPROVED·발송 없음.
>   [미검증] Claude 기준환경 실렌더 공백 보존 일치와 게이트 비악화, 표지 1쪽 육안 품질,
>     고객 PDF/300dpi·실LLM·비용.
>   [다음] manifest `review_requested / next_actor=claude` → 전체 pytest·test_p8 실렌더 신선 재검증.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드22 재검증 CODE_PASS — 이 블록 먼저 읽기) =====
>   [판정] 라운드22 재검증(Claude 신선) = **승인(CODE_PASS), 미해결 블로커 0**. 정본 = REVIEW-FEEDBACK 라운드22 절.
>     기준환경 전체 pytest **1036 passed / 4 skipped / exit 0** — beta-2 삼주 태스크 최초 전체 GREEN.
>     test_p8 3건 전부 Playwright 실렌더 PASSED(unknown_time 포함), golden 28, Ruff 부채 구성 동일(신규 0).
>   [증명] 변경 집합 SHA 전수 대조: 라운드21 종료 대비 경계 54파일 중 변경 = `tests/test_p8.py` 1개뿐
>     (무공백 판정 교정, 패킷 §1 사양 그대로). 제품/게이트/lint/조판/동결 패킷 5종 불변.
>   [미검증] 실LLM·고객 PDF·비용·hsweep K/Z·300dpi·육안 Z=0 — CODE_PASS 범위 밖. 합성 산출물 외 PDF 0.
>   [다음] manifest review_requested / next_actor=codex → **Codex 신선 read-only 확인** → PASS 시 운영자
>     checkpoint commit 결정. 이때 확인 3건: ① 스코프 밖 변경 2건(rules 문구 순화·order_flow enum)
>     ② 삼주 delivery 하한 12쪽/3,500자 ③ 표지 고지 음절 중간 개행 조판(keep-all, advisory).
>     advisory 3건·유료 replacement·hsweep·300dpi 육안은 별도 운영자 결정 전 착수 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드21 테스트 블로커 수정 완료 — 이 블록 먼저 읽기) =====
>   [현재] 라운드21 잔존 1건을 테스트 전용으로 수정·자체 검증 완료. 제품 코드 변경 0,
>     정본 = `handoff/tasks/beta-2-round21-blocker-fix-20260713.md`(`db54f027…dd46`).
>   [수정] `test_p8.py` 후단 판정을 무공백 기준으로 통일해 음절 중간 개행을 흡수했다.
>     고지 1회·年/月/日柱 양성·금지 9종이 같은 기준을 쓰며 금지 스캔은 fail-closed 과탐 가능성을 명시했다.
>   [Codex 실측] test_p8 **3 skipped**(통과 아님), 전체 **1008 passed / 32 skipped / exit 0**,
>     golden **28 passed**, 변경 파일 Ruff·py_compile·diff-check GREEN. 동결 패킷 5종·리뷰 SHA 불변.
>   [불변] 라운드20 제품 수정·게이트·lint·고지 문안·표지 조판·다른 테스트 재작업 0.
>     API·LLM·고객 PDF·hrun·hsweep·commit·push·APPROVED·발송 없음.
>   [미검증] Claude 기준환경 test_p8 실렌더와 표지 개행 조판 육안 품질.
>   [다음] manifest review_requested / next_actor=claude → 라운드22 전체 GREEN·E2E 최종 확인.
>     PASS 뒤 Codex 신선 read-only 확인 → 운영자 checkpoint commit(표지 keep-all advisory 포함).

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드21 재검증 changes_requested 잔존 1건·테스트 전용 — 이 블록 먼저 읽기) =====
>   [판정] 라운드21 재검증(Claude 신선) = **changes_requested, 잔존 1건(테스트 전용)**. 정본 = REVIEW-FEEDBACK 라운드21 절.
>     라운드20 블로커 3건(style·quality·delivery)은 **제품 수준 전부 해소 실측** — E2E verify
>     `gate_pass=True`(비게이트 False 키 2개뿐), delivery failures 0, final_text 14섹션 lint 0,
>     PDF 표지 고지 외 가운뎃점 0, 3방 delivery 회귀·배선 spy·QI-2026-07-13-01·게이트 비악화 확인.
>   [잔존] test_p8.py:102 고지 카운트 0==1 — 표지 고지 음절 중간 개행("해석\n은")을 공백 보존
>     정규화가 복원 못 함(게이트 첫 통과로 처음 도달한 잠복 테스트 결함). 무공백 기준 실측 =
>     고지 1회·금지 9종 0(제품 정상). 전체 **1 failed / 1035 passed / 4 skipped / exit 1**(+3, 감소 0), golden 28.
>   [다음] 수정 패킷 발주 완료: `handoff/tasks/beta-2-round21-blocker-fix-20260713.md`
>     (test_p8 101-115행 무공백 정규화 — 테스트 1파일만, 제품/조판 수정 금지).
>     manifest changes_requested / next_actor=codex → Codex 구현 → Claude 라운드22 재검증(전체 GREEN 기대)
>     → Codex 신선 read-only 확인 → 운영자 checkpoint commit(스코프 밖 2건 + 하한 12쪽/3,500자 +
>     표지 개행 keep-all advisory 확인).

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드20 잔존 블로커 3건 수정 완료 — 이 블록 먼저 읽기) =====
>   [현재] 패킷 v2 §1~§5 구현·자체 검증 완료. style·quality·delivery 3축 수정분을 Claude
>     라운드21 신선 재검증에 넘긴다. v1 §4 raw 골격 모순 정지 뒤 `final_text` 층으로 교정된 v2로 재개했다.
>   [수정] 삼주 3열 표 가운뎃점 제거, 부록 `세운과 월운` 재서술+`본문에 나온` 구역 마커,
>     frame 내부 메타 문장 재서술. delivery analyze에 모드 인자와 verify 전달 1곳을 배선하고,
>     명시적 three_pillar에만 12쪽/3,500자 하한·missing_usable_ziwei 면제를 적용했다.
>   [재발 방지] no-LLM 빌더 전 섹션 final_text×quality/style, 수정 전 문장 2건 차단,
>     삼주 차트 가운뎃점 0, verify→delivery 모드 전달 spy, 삼주 통과/하한/보장/known 비악화 양방을 고정.
>     `docs/16` QI-2026-07-13-01에 E2E 실패 시 verify 전체 False 키 덤프 절차를 기록했다.
>   [Codex 실측] 핵심 신규 3 passed, 집중 **80 passed / 3 skipped**(test_p8 E2E는 통과 아님),
>     전체 **1008 passed / 32 skipped / exit 0**(1005/32 대비 +3·감소 0), golden **28 passed**.
>     변경 Python 38개 중 36개 Ruff GREEN, 기존 부채 rules.py 17+verify.py 1 구성 동일,
>     py_compile 38·diff-check exit 0. 실측 14쪽/4,615자 대비 하한 여유 = 14.3%/24.2%.
>   [불변] lint·GATE_KEYS·THREE_PILLAR_NOTICE·known manse/기준·동결 패킷 4종·REVIEW-FEEDBACK 불변.
>     calc/input 쓰기 0(HEAD 대비 기존 삼주 미커밋 3항목은 시작·종료 동일). API·고객 PDF·hrun·hsweep·
>     commit·push·APPROVED·발송 없음.
>   [미검증] Claude 기준환경 test_p8 실렌더, 고객 PDF/300dpi, 실LLM 문안·비용, hsweep K/Z, 육안 Z=0.
>   [다음] manifest review_requested / next_actor=claude → 라운드21에서 전체 pytest·E2E 실렌더·
>     verify False 키 전체 덤프 재검증. PASS 뒤 Codex 신선 read-only 확인 → 운영자 checkpoint commit.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드20 재검증 changes_requested 잔존 3건 — 이 블록 먼저 읽기) =====
>   [판정] 라운드20 재검증(Claude 신선) = **changes_requested, 잔존 블로커 3건**. 정본 = REVIEW-FEEDBACK 라운드20 절.
>     Codex의 라운드19 잔존 수정(wonguk `살핍니다` 치환 + 골격×meta 회귀)은 **사양 충족** —
>     독립 프로브 17키 TOTAL_HIT_RULES=0·차단측 재현·customer_meta_clean=True. lint 무수정 확인.
>   [잔존] E2E(test_p8)는 라운드19 리뷰가 열거 누락한 게이트 3키로 여전히 gate_pass=False.
>     전체 **1 failed / 1032 passed / 4 skipped / exit 1**(+1, 감소 0), golden 28, Ruff 부채 구성 동일(신규 0).
>     ① style: 삼주 명식표 가운뎃점(charts.py:317·321) + 부록 `세운·월운`(rules.py:1088)·부록 마커
>     `본문에 나온` 부재(부록 제외 미적용). known PDF는 전 페이지 가운뎃점 0 대조 실측.
>     ② quality: frame `이 장에서 말하지 않습니다`(rules.py:1013-1015) internal_meta_label.
>     ③ delivery: premium_pages 14<20·text_chars 4615<10000·missing_usable_ziwei(삼주 구조적 충족 불가)
>     → **운영자 정책 결정 선행**(삼주 전용 delivery 프로파일 vs 상품 재정의). 게이트 변경 = 승인+양방 필수.
>   [근본원인 2층] 라운드19 리뷰가 pytest repr 절단만 보고 첫 실패 축만 열거 — E2E 게이트 실패 시
>     verify 전체 False 키 덤프 표준화. 매트릭스 회귀를 style_lint·quality lint로 확장(비Playwright 가능).
>   [미검증] 라운드19 종료 스냅샷 부재로 변경 집합 SHA 증명 불가(보완 증거 대체·Codex 보고 정합),
>     실LLM·고객 PDF·비용·hsweep·육안. 합성 테스트 산출물 외 PDF 0. commit·push·API 없음.
>   [다음] 운영자 결정 완료(2026-07-13 "권장사항대로" — 블로커③ = 삼주 전용 delivery 프로파일 신설,
>     권장 하한 12쪽/3,500자 + missing_usable_ziwei 면제, known 비악화 필수). 수정 패킷 발주 완료:
>     `handoff/tasks/beta-2-round20-blockers-fix-20260713.md`. manifest changes_requested / next_actor=codex
>     → Codex가 패킷 §1~§5 구현 → Claude 라운드21 재검증(E2E 실렌더 + verify False 키 전체 덤프).

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드19 잔존 블로커 수정 완료 — 이 블록 먼저 읽기) =====
>   [현재] 잔존 1건만 구현·자체 검증 완료. `rules.py` wonguk 골격의 `함께 읽습니다`를
>     `살핍니다`로 최소 치환했고 lint 완화·예외 추가는 0. `REVIEW-FEEDBACK.md`는 불변.
>   [재발 방지] 실제 삼주 골격 17키 전체 × customer_meta/loanword/raw_calc lint 비Playwright 회귀와
>     수정 전 문장 차단측을 동반. 전수 실측 **TOTAL_HIT_RULES=0**.
>   [Codex 실측] 신규 1 passed, 패킷 집중 **37 passed / 3 skipped**(Playwright E2E 3건은 라운드20 위임),
>     전체 **1005 passed / 32 skipped / exit 0**(1004/32 대비 +1·감소 0), golden **28 passed**.
>     변경 Python 36개 py_compile·diff-check GREEN, clean 대상 34개 Ruff GREEN;
>     `rules.py` 17 + `verify.py` 1 기존 부채는 동일 구성(신규 0).
>   [불변] B2·B3·B4·advisory·게이트/lint·동결/보류 패킷 재작업 0. commit·push·API·고객 PDF·hrun·hsweep 없음.
>   [미검증] Claude Playwright 실렌더, 고객 PDF/300dpi, 실LLM 문안·비용, hsweep K/Z·육안 Z=0.
>   [다음] manifest review_requested / next_actor=claude → 라운드20 기준환경 재검증.
>     PASS 뒤 Codex 신선 read-only 확인 → 운영자 checkpoint commit.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드19 삼주 재검증 changes_requested 잔존 1건 — 이 블록 먼저 읽기) =====
>   [판정] 라운드19 재검증(Claude 신선) = **changes_requested, 잔존 블로커 1건**. 정본 = REVIEW-FEEDBACK 라운드19 절.
>     라운드18 블로커 중 B2(원국표 anchor 단일 삽입+라운드트립)·B3(치환 시스템+known SHA 핀 `a17f90fb…380a`+
>     SDK 캡처 양방)·B4(소서 경계·three_pillar+시각 접수 차단·레거시 known 복원) = **완결**.
>   [잔존] rules.py:999 wonguk 골격 "함께 읽습니다" ↔ customer_meta guided_structure_walkthrough 충돌로
>     복구된 E2E(test_p8)가 gate_pass=False. 전체 **1 failed / 1031 passed / 4 skipped / exit 1**(+9, 감소 0).
>     리뷰어 전수 프로브: 골격 17키 × meta 8룰 충돌 = 이 1건뿐. 수정 = 문장 재서술(게이트 완화 금지) +
>     골격×customer_meta_lint 비Playwright 회귀 동반(근본원인 2층 — Codex 환경 E2E skip이라 회귀 없이는 재발).
>   [플래그] 스코프 밖 변경 2건(rules 문구 순화·order_flow enum 정본화)은 실측 GREEN이나 "운영자 추가 승인"
>     주장은 리뷰어 확인 불가 — checkpoint commit 시 운영자 확인.
>   [GREEN] golden 28·집중 124·Ruff 신규 0·py_compile 36·diff-check 0·수정 8파일 SHA 대조 일치·동결 패킷 불변.
>   [미검증] 실제 API·고객 PDF·비용·hsweep K/Z·육안 Z=0. pytest 합성 산출물 외 PDF 생성 0.
>   [다음] Codex 잔존 1건 수정 → Claude 라운드20 재검증 → PASS 시 Codex 신선 read-only 확인 → 운영자
>     checkpoint commit. manifest = changes_requested / next_actor=codex.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드18 블로커 수정 완료 — 이 블록 먼저 읽기) =====
>   [현재] 라운드18 미해결 B1~B4만 구현·자체 검증 완료. `REVIEW-FEEDBACK.md`는 리뷰어 소유로 불변,
>     수정 정본 = `handoff/tasks/beta-2-round18-blockers-fix-20260713.md`.
>   [수정] test_p8 새 삼주 계약, integrated sparse 포함 3열표 anchor, 삼주 compose 상충 지시 원천 제거,
>     비입춘 절입·explicit three_pillar+시각·legacy known 경계 테스트를 고정했다. 운영자 추가 승인으로
>     `rules.py`의 `추정값` 한 문장을 순화하고 `order_flow.py`의 가짜 legacy boolean 합성을 제거했다.
>   [Codex 실측] 집중 **94 passed / 3 skipped**(Playwright E2E skip), 전체
>     **1004 passed / 32 skipped / exit 0**(995/32 대비 +9·감소 0), golden **28 passed**.
>     변경 Python 36개: clean 대상 34개 Ruff GREEN, py_compile·diff-check GREEN;
>     `rules.py` 17 + `verify.py` 1 기존 부채는 라운드18 구성과 동일.
>   [불변] 게이트 22키·known 프롬프트 바이트·계산/골든·advisory 3건 재작업 0. 동결 패킷 2개와
>     보류 hverify 패킷 내용 불변. commit·push·API·고객 PDF·hrun·hsweep 없음.
>   [미검증] Claude Playwright 기준의 test_p8 실제 렌더, 고객 PDF/300dpi, 실LLM 문안·비용,
>     hsweep K/Z·운영자 육안 Z=0.
>   [다음] manifest review_requested / next_actor=claude → 라운드19 기준환경 재검.
>     PASS 뒤 Codex 신선 read-only 확인 → 운영자 checkpoint commit. 유료 재생성 금지 유지.

> ===== 압축/새세션 재개 앵커 (2026-07-13 라운드18 삼주 교차리뷰 changes_requested — 이 블록 먼저 읽기) =====
>   [판정] 라운드18 교차리뷰(Claude 신선 컨텍스트) = **수정 요청(changes_requested)**. 블로커 4건만 수정.
>     정본 = REVIEW-FEEDBACK.md 라운드18 절, 패킷 = handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md.
>   [기준환경 실측] `pytest tests/ -q` → **1 failed / 1022 passed / 4 skipped / exit 1** — Codex 예상 1023/4 미달성.
>     실패 = tests/test_p8.py::test_e2e_unknown_time(구계약 미갱신: 소서 절입일+`추정` 고지 단언, Codex 32 skip에 가려짐).
>     golden 28·신규/집중 176·py_compile 35·diff-check GREEN, Ruff 신규 0(HEAD 부채 18건 동일 구성).
>   [블로커] 1) test_p8 구계약 갱신 2) integrated_full 삼주 원국표 팬텀 배선(pdf.py:128 `wonguk` vs `personal_wonguk`)
>     3) 삼주 compose 상충 시스템 지시(_COMPOSE_SYSTEM 궁 호명 등) + override 캡처 테스트 0
>     4) 경계 테스트 누락 3건(비입춘 절입·three_pillar+시각 접수 차단·레거시 known 오분류).
>   [GREEN 범위] 계산 12/12 축약·주문/레거시 fail-closed·22키 게이트 양방·known 비악화·문서 정합은 실측 GREEN —
>     재작업 불필요(라운드18 절 표). advisory 3건은 비블로커.
>   [미검증] 실제 API·고객 PDF·비용·hsweep K/Z·육안 Z=0. pytest 합성 테스트 산출물 외 PDF 생성 0.
>   [다음] Codex 블로커 1~4만 수정 → Claude 재검증 → 통과 시 Codex 신선 read-only 확인 → 운영자 checkpoint commit.
>     manifest = changes_requested / next_actor=codex. 유료 재생성·API·commit·push 금지 유지.

> ===== 압축/새세션 재개 앵커 (2026-07-12 생시 미상 삼주 전환 CODE_PASS 후보) =====
>   [현재] base/HEAD `084e04c` 위 미커밋 구현. `birth_time_mode=three_pillar` + 신고 시민 날짜 삼주 +
>     12시지 12/12 불변 사실만 허용. 정오·시주·자미·불안정 파생값은 구조적으로 제외한다.
>   [차단] 절입 당일 `NEEDS_INFO_TIME_BOUNDARY`; provenance 없는 레거시 unknown·관리자 금지 사실 주입·
>     최종 발급 불일치는 fail-closed. 생시 미상+상대/gunghap/자미 단독은 v1 미지원으로 명시 차단.
>   [고객 표면] 연·월·일 3열 원국표 + 고정 고지 1회. `unknown_time_provenance_clean` 포함 GATE_KEYS 22키.
>   [Codex 실측] 전체 **995 passed / 32 skipped / exit 0**(시작 921/32 대비 +74, 감소 0),
>     golden **28 passed**, 신규/하네스 집중 106/1, 변경 Python py_compile·신규 Ruff·diff-check GREEN.
>     Claude 기준환경 1023/4는 산술 예상이며 직접 재실행 전 **확정 불가**.
>   [미검증] 실제 API·PDF/300dpi 조판·비용·hrun·hsweep K/Z·육안 Z=0. 고객 DB/PDF 비접촉.
>   [인계] `handoff/tasks/beta-2-unknown-time-three-pillar-20260712.md` → Claude 신선 교차리뷰.
>     기존 `beta-1-hverify-module-contract-20260712`는 SHA 보존·후순위, 새 HEAD에서 재검토 필요.
>   [다음] 교차리뷰 PASS → Codex 신선 read-only 확인 → 운영자 checkpoint commit 결정. 유료 재생성 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-12 라운드17 일정/일정한 오탐 소수정 PASS — 이 블록 먼저 읽기) =====
>   [판정] 라운드17 교차리뷰(Claude 신선 컨텍스트) = **PASS**. 라운드16 advisory `일정/일정한` 오탐 소수정
>     (delivery_quality.py 정규식 1곳 `일정(?!한|하게|하지)` + 양방 테스트 8건). 승인 범위 밖 변경 0.
>     정본 = REVIEW-FEEDBACK.md 라운드17 절, 패킷 = handoff/tasks/beta-1-schedule-boundary-20260712.md.
>   [기준환경 확정] `pytest tests/ -q` → **949 passed / 4 skipped / exit 0**(941/4 + 신규 8, 감소 0)
>     — **새 기준선 = 949/4**. golden 28·집중 70·변경 2파일 Ruff/py_compile/diff-check GREEN.
>     경계 프로브 14건 전부 기대 일치(차단 유지·허용 3활용형·기존 매트릭스 무손상).
>   [비블로커] 인접 활용형 `일정하다/일정해서`는 승인 스코프 밖 잔존 오탐(fail-closed) — 실측 관측 시 확장.
>     절차 이탈 1건(broad rg가 render/out 매치, 자진 보고·인용 0) — 이후 패킷 0절 글롭 문구 필수, docs/16 여부 운영자 결정.
>   [종결 2026-07-12] 제품 checkpoint commit = **`e6145fc`**(fix, 2파일 +32/-1). **라운드17 PASS** —
>     새 기준선 **949 passed / 4 skipped**. `일정하다/일정해서`는 실제 관측 시에만 확장하는 비블로커.
>     beta-1-schedule-boundary 태스크 done + archive 동결. API·PDF·비용·hsweep K/Z·육안 Z=0 여전히 **미검증**.
>   [다음] 운영자의 Phase C replacement 1회 과금 승인 결정. 승인 시에만 replacement 생성 → 표준 게이트 →
>     hsweep → 육안 Z 재측정.

> ===== 이전 앵커 (2026-07-12 라운드16 교차리뷰 PASS) =====
>   [판정] 라운드16 교차리뷰(Claude 신선 컨텍스트) = **PASS(CODE_PASS)**. 패킷 A~D 전 항목 diff 근거 확인,
>     미해결 블로커 0. advisory 1건(`일정`→`일정한` 오탐, fail-closed 방향·비블로커) = REVIEW-FEEDBACK 라운드16 절.
>   [기준환경 확정] `pytest tests/ -q` → **941 passed / 4 skipped / exit 0**(기존 831/4 + 신규 110, 감소 0)
>     — **새 기준선 = 941/4**. golden 28. Ruff 신규 위반 0(HEAD 부채 19건 동일 구성 대조). py_compile 43파일·
>     diff-check GREEN. calc/input diff 0(tracked+untracked). SHA 3건 MATCH. 리뷰어 수정은 허용 4파일뿐
>     (read-only 56파일 SHA 시작/종료 스냅샷 대조).
>   [종결 2026-07-12] checkpoint commit = **`5b0a88f`**(60파일, 승인 신규 5파일 경로 명시 추가).
>     **beta-1-register-harness CODE_PASS 태스크 종결**(manifest done + archive 동결). 실제 API·PDF·
>     prompt cache 비용·hsweep K/Z·육안 Z=0은 여전히 **미검증**.
>   [다음] 유료 재생성 전에 라운드16 advisory인 `일정/일정한` 오탐 소수정 여부 결정. 이후 운영자
>     별도 과금 승인 시에만 Phase C replacement 1회 진행(→ 표준 게이트 → hsweep → 육안 Z 재측정).

> ===== 이전 앵커 (2026-07-12 베타 1호 Z>0 개선 CODE_PASS·교차리뷰 요청) =====
>   [현재] 브랜치 `codex/gunghap-relationship-quality`, base/HEAD `5ebd3b6`, 원격과 동률. 베타 1호 육안
>     Z>0 원인에 대한 문체 register·외부 도메인 조언·쉬운 용어·hsweep·LLM 비용 관측 개선 후보가 **미커밋
>     워킹트리**에 있다. 코드 검증 단계 판정은 `CODE_PASS`; 새 고객 PDF 품질 PASS나 Z=0은 아직 아니다.
>   [문체·조언] docs/14 기존 SSOT를 확장하고 `client_register_clean` 전역 게이트와
>     `external_domain_advice` 실패 원인을 추가했다. 결과지/참고/구간/정보 수집/커트라인/큰 그림 계열은
>     활용형까지 차단하며, 시험·직업 주제 자체는 허용하되 외부 일정·점수·자격·서류 절차와 결합한 사실·지시는
>     차단한다. consult의 빈 action 표지 제거, `work_career` 질문축, 7개 개인 카테고리+followup 골격 양방을 고정했다.
>   [가독성·비용] 12개 Sonnet compose가 PII 없는 결정론 `ReportContext`를 공유한다. 각 호출에는 현재 장 ID를
>     넣고, 상품 토글로 용어 설명 선호 장이 빠지면 활성 장으로 결정론 재배정한다. 정적 system+context prefix는
>     5분 explicit cache를 쓰되 첫 호출 usage에서 cache 생성/읽기가 **실제 관측된 경우만** 후속 3병렬을 허용한다.
>     모델은 `claude-sonnet-4-6` 그대로이며, 비용 개선 실효는 실제 API 미호출이라 확정 불가다.
>   [하네스] hsweep schema v2는 raw 후보를 보존하고 ranker를 비파괴 advisory로 제한하며, 모든 후보를 judge한다.
>     운영자 review 완료 전 K/Z는 null이고, K(후보 확인)와 Z(후보 밖 신규 발견)를 분리한다. 로컬 PII manifest,
>     정확한 한국어 생년·시각 마스킹, 단계별 partial/usage, canonical review 출력, gitignored atomic temp를 배선했다.
>   [검증] Codex 환경 전체 `pytest tests/ -q` = **913 passed / 32 skipped / exit 0**(기존 803/32 대비
>     passed 감소 0, +110). golden **28 passed**. 핵심 합성 123 passed, 독립 최종 리뷰 register/context 68 passed,
>     hsweep 보안 57 passed. 변경 Python 중 기존 부채 3파일 제외 Ruff GREEN, 전 파일 py_compile·diff-check GREEN,
>     `sajugen/calc`·`sajugen/input` diff 0. 기존 Ruff 부채 19건(rules 17/pdf 1/verify 1)은 별도이며 신규 악화 0.
>   [금지 준수] 고객/ignored 산출물·local profile·`.env` 미열람, 실제 Anthropic API·PDF 재생성·hrun·commit·push
>     미실행. 기존 DRAFTED 베타 1호는 승인·발송하지 않았다.
>   [다음] `handoff/tasks/beta-1-register-harness-20260712.md` 기준 Claude 신선 컨텍스트 교차리뷰. Claude
>     기준환경은 기존 831/4에 신규 수집 110을 더한 **예상 941/4**를 직접 재실행해 확정해야 한다. PASS 뒤
>     운영자 checkpoint commit 여부 결정. 이후에만 별도 과금 승인으로 replacement PDF 1회 생성→게이트→hsweep→
>     전문 육안 Z 재측정. 그 전 실제 상품 PASS·비용 절감·Z=0 단언 금지.

> ===== 압축/새세션 재개 앵커 (2026-07-10 Q7 1단계 라운드9 재검 PASS — 이 블록 먼저 읽기) =====
>   [판정] 라운드9 재검(Claude 신선 컨텍스트) = **PASS**. R9-1(module_coverage 소유권 교차검증) Codex 수정
>     완료·종결, Q7 1단계 미해결 0. 정본 = `REVIEW-FEEDBACK.md` 최상단 "라운드9 재검" 절.
>   [기준환경 확정] `pytest tests/ -q` → **753 passed / 4 skipped / exit 0**(라운드9 745/4 + R9-1 신규 8 완전
>     일치, 감소 0). 골든 28 GREEN. **새 기준선 = 753/4**(감소=회귀). 수정은 승인 2파일(modules.py·
>     test_integrated_modules.py)뿐 — 허용 밖 동결 7파일 SHA 불변 실측. Ruff 수정 2파일 GREEN.
>   [R9-1 종결 증거] 라운드9 동일 프로브 재실행: P1 위조 맵 unexpected=['health']·P3 unknown=['fake_zone']·
>     P4 unexpected=['gunghap']·P5 analyze failure 발생(전부 구 세탁 → 차단 전환). 통과측 G1~G4(legacy·work
>     이중·core/tail·5모듈 조립기 맵) 오탐 0. misattributed_section_ids 관측 필드 추가(게이트 키 신설 없음).
>   [커밋 완료 2026-07-10 운영자 지시] 분리안 3커밋: `065c987` feat(Q7 1단계 제품 9파일, +1175/-43) /
>     `fbdb296` chore(handoff 공존 배선 3파일) / docs(패킷·리뷰·상태·manifest — 이 커밋). manifest = done
>     (archive `handoff/archive/q7-stage1-modules-20260710.json` 동결).
>   [push 완료 2026-07-10] `c8b48ad..6c0d673` → origin, ahead 0.
>   [Q7 2단계 발주 2026-07-10] 패킷 `handoff/tasks/q7-stage2-cli-20260710.md`(승인, SHA `d46581db…`) =
>     **CLI `--module`만**. admin 추천 UI·주문 플로우 integrated_full 편입·Q6 자동 추천은 **3단계 이연**
>     (운영자 결정 — 현행 주문 플로우는 1인 전용이라 상대 입력·modules 소비처 없음 = 지금 저장하면 팬텀
>     메타 A-5 위반). manifest = q7-stage2-cli-20260710 / planned / next_actor=codex. 수정 허용은
>     integrated.py CLI 부분+test_integrated_modules.py 2파일, 기준선 753/4, 검증 = 라운드10.
>   [라운드10 PASS 2026-07-11] Q7 2단계 CLI `--module` 구현(Codex, 2파일 +121/-12) 교차리뷰 승인. 기준환경
>     **758 passed / 4 skipped / exit 0**(753+5, 감소 0) = 새 기준선. 골든 28. 실 프로세스 차단 3종(fake/중복/
>     1인 gunghap) exit 1 실측. 정본 = REVIEW-FEEDBACK.md 최상단 라운드10 절.
>   [절차 이탈 기록(비블로커)] Codex 광역 rg에서 ignored render/out/** 일부가 읽기 전용 검색 결과에 포함
>     (수정·전재 없음, 자진 보고). 재발 방지: 이후 Codex 패킷 0절에 ignored 제외 글롭 필수 명시.
>     docs/16 기록 여부 = 운영자 결정 대기.
>   [2단계 커밋·push 완료 2026-07-11 운영자 지시] `ff002ee` feat(CLI --module 2파일) + docs(기록·manifest —
>     이 커밋). manifest = done(archive 동결). origin push 완료. **Q7 전체(1·2단계) 종결.**
>   [3단계 설계 승인·3-A 발주 2026-07-11] 설계 `handoff/codex-q7-stage3-design.md` A안 승인(①~④, ⑤ 가격·
>     상품명은 운영자 별도). 착수 점검 실측 2건이 3-A에 편입: (a) build_integrated_full 계산 입력 미배선
>     (integrated.py:593 — 경도·자시정책 하드코딩, 주문화 시 진태양시 결함) → 배선+시진불명 접수 차단,
>     (b) followup 근거 장 조용한 skip → integrated_full 부모 후속 차단. 3-A 패킷 =
>     `handoff/tasks/q7-stage3a-order-20260711.md`(승인, SHA `3e18fe89…`), manifest = planned/next_actor=codex.
>     0절에 ignored 제외 글롭 필수 문구 포함(라운드10 재발 방지 이행). 3-B(admin UI)는 3-A 뒤 별도 발주.
>   [라운드11 PASS 2026-07-11] 3-A 구현(Codex, 제품 3 + 테스트 5파일, +751/-33) 교차리뷰 승인. 기준환경
>     **778 passed / 4 skipped / exit 0**(758+20, 감소 0) = 새 기준선. 골든 28. 임시 DB 실경로 프로브로
>     시진불명 접수 차단·미확정 생성 차단(NORMALIZED 불변+감사 PII 0)·하위호환 실측. 정본 = REVIEW-FEEDBACK
>     라운드11 절.
>   [절차 이탈 2회차(비블로커)] ignored 검색 재노출 — 근본원인 = 발주 패킷 글롭 예시가 루트 기준(`!render/
>     out/**`)이라 불충분. 이후 패킷은 `!**/render/out/**` 형식 고정. 2회 반복이라 docs/16 기록 권고(운영자
>     결정 대기).
>   [3-A 커밋·push·QI 기록 완료 2026-07-11 운영자 지시] `ac5d8f2` feat(3-A 8파일) + docs(기록·manifest·
>     QI-2026-07-11-01 — 이 커밋). manifest = done(archive 동결). 절차 이탈 2회는 docs/16
>     QI-2026-07-11-01로 기록(글롭 형식 `!**/` 고정, 근본 완화 = ignored 55파일 정리 운영자 액션).
>   [3-B 발주 2026-07-11] 패킷 `handoff/tasks/q7-stage3b-admin-20260711.md`(승인, SHA `96c42a9c…`) =
>     admin 모듈 추천·확정 UI. 추천 표시만(자동 선택 없음)·확정은 NORMALIZED에서만·저장은
>     gen_params.modules+report_plan.sections·audit 모듈 ID만·생성은 기존 재시도 재사용. manifest =
>     planned/next_actor=codex. 검증 = 라운드12, 기준선 778/4.
>   [라운드12 PASS 2026-07-11] 3-B 구현(Codex, 제품 4 + 테스트 3파일, +184/-18) 교차리뷰 승인. 기준환경
>     **801 passed / 4 skipped / exit 0**(778+23, 감소 0) = 새 기준선. 골든 28. 실경로 프로브로 gunghap/
>     비NORMALIZED 확정 거부·정규 순서 저장·audit 모듈 ID만 실측. 절차 이탈 0(`!**/` 글롭 첫 적용 라운드 —
>     QI-2026-07-11-01 재발 방지 유효 확인). **Q7 3단계(3-A+3-B) 완결** — 접수→모듈 확정→native 생성→검수→
>     발급 전 구간 배선. 정본 = REVIEW-FEEDBACK 라운드12 절.
>   [3-B 커밋·push 완료 2026-07-11 운영자 지시] `8098f84` feat(3-B 7파일) + docs(기록·manifest — 이 커밋).
>     manifest = done(archive 동결). origin push 완료.
>   [합성 실렌더 실측 2026-07-11 — 무LLM 경계표(합성 김합성, 과금 0, 산출 render/out 비커밋)]
>     N=1(love) 21p/12,534자 → PASS(하한 16p, 전 게이트 clean) / N=2 22p/13,440자 → PASS(하한 20p) /
>     N=3 23p → FAIL(하한 24p) / N=4 24p → FAIL(하한 28p). **발견: 룰 전용 실증 분량 = 모듈당 +1p,
>     공식(12+4N)은 +4p 요구 → N≥3 구조적 미달**(문자 하한은 전 구간 여유). 게이트 fail-closed 정상 작동.
>     첫 실행의 name_policy 실패는 프로브 입력(라틴 ID) 문제로 분리 확정 — 한국식 합성명에서 clean.
>   [운영자 결정 2026-07-11] LLM-on N=4 합성 1건 실측 후 분량 정책 결정(과금 승인 완료). 통과 시 "무LLM
>     폴백은 N≤2만 발급 가능"을 알려진 제약으로 문서화, 미통과 시 공식/문안 재론.
>   [LLM-on N=4 실측 2026-07-11 — 과금 승인분] **gate_pass=True, 34p/19,090자**(하한 28p/9,000자 여유 통과),
>     커버리지 clean, dq_failures 0. 비용: calls=18, in 115,889/out 28,790 tok. 관측: love·work·flow 챕터
>     LLM 출력이 가드에 차단돼 룰 폴백 3건 — 가드 정상 방어, 최종 게이트 통과에 영향 없음.
>   [분량 정책 확정 2026-07-11 운영자 결정] 공식(12+4N)·게이트 현상 유지. **알려진 제약: 무LLM 폴백 발급은
>     N≤2 조합만 가능(N≥3는 LLM-on 전제 상품 — LLM 장애 시 N≥3 주문은 fail-closed 대기)**. 실측 근거 =
>     위 무LLM 경계표 + LLM-on N=4 통과.
>   [4단계 설계 승인·발주 2026-07-11] 설계 `handoff/codex-q7-stage4-design.md` A안 승인(①~⑤ — gen_params
>     additive·상대 시진불명 접수 차단·상대 PII는 본인 동일 수준+개별 파기는 주문 삭제로만·RELATION+상대
>     →gunghap 추천 복원·단일 패킷). 패킷 = `handoff/tasks/q7-stage4-partner-20260711.md`(SHA `83634edb…`),
>     manifest = planned/next_actor=codex. 검증 = 라운드13 + 합성 실렌더 N=5(2인, 검증 세션 몫). 기준선 801/4.
>   [라운드13 PASS 2026-07-11] 4단계 구현(Codex, 제품 5 + 테스트 5파일, +692/-57) 교차리뷰 승인. 기준환경
>     **820 passed / 4 skipped / exit 0**(801+19, 감소 0) = 새 기준선. 골든 28. 프로브: 2인 접수·gunghap 확정
>     `(love,gunghap)` 정규 저장·1인 gunghap 거부 유지·비대상 상품 차단. 합성 실렌더 N=5(2인 무LLM) = **35p로
>     분량 하한(30p) 통과**(관계 조립 실작동) — 단 R13-1 발견. 정본 = REVIEW-FEEDBACK 라운드13 절.
>   [발견 R13-1(비블로커·기존 경로)] 무LLM 2인 관계 룰 문안이 수신자를 '씨'로 3인칭 호명 → role/honorific
>     게이트 차단(fail-closed 정상, 발급 불가 = 안전). 4단계 diff 밖 — 무LLM 2인 integrated_full 실렌더 최초
>     실행이 노출. LLM-on 해소 여부 미검증. 처리안: (a) LLM-on N=5 실측 후 결정 (b) 관계 문안 호칭 수정 발주.
>   [4단계 커밋·push 완료 2026-07-11 운영자 지시] `c8cd1cc` feat(4단계 10파일) + docs(기록·manifest —
>     이 커밋). manifest = done(archive 동결). origin push 완료.
>   [R13-1 처리 결정 2026-07-11 운영자] (a)안 채택 — LLM-on N=5 합성 1건 실측(과금 승인)으로 LLM 재작성이
>     '씨' 호칭을 해소하는지 확인 후 문안 수정 발주 여부 결정. 결과는 이 앵커 아래 기록.
>   [LLM-on N=5 실측 2026-07-11 — 과금 승인분] **GATE FAIL** — R13-1(수신자 '씨' 호칭)이 LLM 재작성으로도
>     미해소(동일 룰 17회, 관계 챕터 구간 — 룰 골격 문안이 원인이고 LLM이 보존). 추가 실패: identity_role_clean
>     (일간 role 오서술 — 상세 미조사)·premium_low_density_pages(14쪽 25자 1쪽). 비용: calls=32,
>     in 149,860/out 56,790 tok. **R13-1 승격: 2인 통합(N=5 gunghap 포함) 상품은 룰/LLM 양쪽 발급 불가
>     상태**(게이트 fail-closed 정상 — 유출 위험 0. gunghap 단독 상품·1인 조합 N≤4는 무관).
>   [R13-1 정정 2026-07-11 — 발주 준비 실측] **수정 발주 불필요.** 위반 문형 추출 결과 프로브 입력 엣지로
>     확정: 합성 쌍(김합성/이합성)의 given이 동일해 기존 호칭 변환(gunghap.py:583)이 구분 불가했던 것.
>     **given 상이 쌍(김민준/이서연) 무LLM N=5 재실렌더 = gate_pass True, 35p, 전 게이트 clean.** LLM-on
>     FAIL·identity_role·저밀도도 같은 입력 산물. **2인 통합 N=5 상품 = 정상 발급 가능 상태**(정정).
>   [잔여 이슈 발주 2026-07-11 운영자 결정] 동명 given 커플 = 접수 시점 명확 차단 추가로 확정(호칭 로직
>     개선은 B-8 기각). 패킷 = `handoff/tasks/q7-given-guard-20260711.md`, manifest = planned/next_actor=codex,
>     검증 = 라운드14, 기준선 820/4. LLM-on 정상 쌍 N=5는 미실측(위험 낮음 — 필요 시 별도 과금 승인).
>   [패킷 v2 정정 2026-07-11 — Codex 정지 보고 타당(4번째, 전부 타당 선례 유지)] v1의 "외자 given 1자 충돌
>     차단"은 시스템 실태와 불일치한 과잉 요구로 폐기: given_name은 2자 이하 풀네임을 그대로 반환하고
>     호칭 생성·게이트 스펙(role_perspective_specs:655)이 **같은 함수**를 쓰므로 외자 상이 성 쌍(김민/이민)은
>     충돌 자체가 없음 = 정상 접수가 옳음. v2 술어 = given_name 출력 동등성(교차 케이스 민준/김민준 포함).
>     v2 SHA `8ba9fd29…` manifest 재동결. client_tone_lint.py 수정 금지 유지.
>   [라운드14 PASS 2026-07-11] given 가드 v2 구현(Codex, order_flow+테스트 2파일) 교차리뷰 승인. 기준환경
>     **829 passed / 4 skipped / exit 0**(820+9, 감소 0) = 새 기준선. 골든 28. 경계표 차단 5·통과 4(외자
>     상이 성 김민/이민 정상 접수 포함) 전부 고정, 프로브로 차단·이름 비전재·외자 통과 실측. **Q7 알려진
>     잔여 0 — 전체 완결**(1~4단계 + 실렌더 + given 가드). 정본 = REVIEW-FEEDBACK 라운드14 절.
>   [커밋·push·main 전진 완료 2026-07-11 운영자 지시] `5519899` feat(given 가드 2파일) + docs(기록·
>     manifest — 이 커밋). manifest = done(archive). feat push + **main fast-forward 전진·push**(Q7 완결 +
>     829/4 GREEN = 컨벤션 충족, 선형 유지). **Q7 프로젝트 종결.**
>   [잔존 선택 항목] LLM-on 정상 쌍 N=5 실측(과금, 위험 낮음 — 필요 시 승인). LLM-on 문안 육안 검수는
>     **운영자 완료(2026-07-11)** — 디벨롭 희망 다수이나 완성 우선 결정. PII 잔여 3건은 별도 트랙.
>   [월 감사 2026-07 완료 2026-07-11] 보고서 = handoff/reports/audit-2026-07/audit.md(로컬 전용).
>     기계 게이트 전 GREEN(골든 28·deadparam 0·레지스트리 동기화), 문서-코드 불일치 0, 7월 QI 재발방지
>     전수 닫힘(열림 2 = 55파일 정리·hsweep 파일럿, 둘 다 운영자 액션). **변이 4건 중 M1 생존**:
>     MIN_TEXT_CHARS(통이미지 차단) 1500→0 완화를 전체 829 테스트가 못 잡음 — 차단측 부재.
>     M3(delivery aggregate no-op)는 격추이나 감지 단일점. 후속 A-1 = 차단측 보강 소형 발주(결정 대기).
>   [A-1 발주 2026-07-11] 패킷 = `handoff/tasks/audit-a1-mutation-hardening-20260711.md`(승인, SHA
>     `788fc78f…`) — **테스트 전용**(test_render_verify.py 1파일, 제품 코드 무변경): M1 차단측(text_layer
>     임계 양방, MIN_TEXT_CHARS 상수 참조) + M3 이중화(verify 경유 delivery 차단 전용) + 변이 재검 2건
>     RED 증거 의무. manifest = planned/next_actor=codex, 검증 = 라운드15, 기준선 829/4.
>   [라운드15 PASS 2026-07-11] A-1 구현(Codex, 테스트 1파일 +91·제품 diff 0) 교차리뷰 승인. 기준환경
>     **831 passed / 4 skipped / exit 0**(829+2, 감소 0) = 새 기준선. **변이 재검 리뷰어 직접 재실행:
>     M1(임계→0)·M3(clean→True) 주입 시 신규 테스트가 각각 격추(1 failed) 후 원복** — 감사 생존 변이 0.
>     감사 후속 코드 몫 종결. 정본 = REVIEW-FEEDBACK 라운드15 절.
>   [A-1 커밋·push·main 전진 완료 2026-07-11 운영자 지시] `3f36b39` test(A-1) + docs(기록·manifest —
>     이 커밋). manifest = done(archive). feat push + main ff 전진·push(831/4 GREEN·선형 유지).
>     **감사 2026-07 코드 후속 전부 종결.**
>   [베타 확정 2026-07-11 운영자] docs/23 확정 — **베타 N=3(지인)·무료·재발급 1인 선행**(대상은 별칭
>     관리, 문서·채팅 비기록). 종료 기준 N=3, 발송 전 체크리스트 4단계(게이트→hsweep 파일럿→육안→APPROVED
>     수동), 피드백 처리 규칙(결함=QI·개선희망=백로그 일괄 트리아지).
>   [재발급 경로 실측 2026-07-11] 운영 주문 DB = customers 0·orders 0, content.json 13개 중 대상 매칭 0
>     (익명 패턴 10 + 기타 3, 로마자 변형 매칭 불리언만 확인) → **저장본 부재 확정 = 무과금 재렌더 불가,
>     신규 재생성(주문 접수 경유·LLM-on 과금) 경로**. 재발급본이 hsweep 파일럿(A-3)의 신선 발송물 1호 후보.
>   [A-2 완료 2026-07-12] 비익명 산출물 389파일/105.7MB를 repo 밖 보관 이동(sajugen-archive\pii-cleanup-
>     20260711, 동기화 밖·MANIFEST 보존·가역적). fail-closed 화이트리스트 분류, 이동 후 repo 비익명 잔류 0 +
>     전체 pytest **831/4 무영향**. QI-2026-07-11-01 근본 완화 종결. PII 잔여 = ②(git 이력 실명 rewrite)
>     ③(docs/11 생년월일)만 — 운영자 결정 대기.
>   [베타 1호 생성 완료 2026-07-12] 익명 문서 `DOC_BETA_1`(integrated_full·4모듈 love/job/wealth/
>     health·LLM-on) — 접수는 로컬 입력 파일 경유(채팅 PII 0, 접수 후 파일 삭제). **gate_pass=True, 36p**
>     (하한 28p), 커버리지 clean, DRAFTED. LLM calls=17(~$1.2). love·flow 챕터 가드 폴백 2건(정상 방어).
>   [hsweep 파일럿 1호 2026-07-12 — A-3 실측] N=29 → M=0 → K=0, $0.41, partial=False. Z(운영자 육안 신규
>     발견)가 결정 지표로 잔존 — 육안 검수 후 docs/16에 추기. 상세 = docs/16 hsweep 절.
>   [다음] **운영자 육안 검수**(로컬 ignored draft PDF, docs/23 §2-3 —
>     Z 값 보고) → admin에서 APPROVED → 수동 발송. 이후 베타 2·3호 접수.

> ===== 압축/새세션 재개 앵커 (2026-07-10 Q7 1단계 라운드9 changes_requested — 이 블록 먼저 읽기) =====
>   [판정] 라운드9(Claude 신선 컨텍스트) = **changes_requested**. v3 수용기준·회귀·범위·게이트 비악화 전 항목
>     GREEN이나, 패킷이 위임한 소유권 사각 판정 = 보완 필요 **R9-1 1건**(유일 미해결). 상세 `REVIEW-FEEDBACK.md` 최상단.
>   [기준환경 확정] `pytest tests/ -q` → **745 passed / 4 skipped / exit 0**(기준선 728/4 + 신규 17 완전 일치, 감소 0).
>     골든 28 GREEN. 동결 SHA-256 10건 전부 MATCH(HEAD `0b3134f`). Ruff 신규 2파일 GREEN·수정 7파일 신규 위반 0
>     (기존 부채 3건 해소, 전체 기존 부채 29건 별건).
>   [R9-1] `module_coverage`가 구조화 맵의 소유권 주장을 레지스트리와 교차검증하지 않음 — 위조 맵이 missing/
>     unexpected/unknown 전부 우회(합성 프로브 P1~P5로 확정, 정직 맵 대조군은 정상 차단). 수정 방향: 맵 주장 ID의
>     레지스트리 소유자 대조(불일치=격상) + 양방 회귀. 예상 수정 범위 `sajugen/modules.py`+`tests/test_integrated_modules.py`.
>   [다음] Codex가 REVIEW-FEEDBACK 라운드9 R9-1만 수정 → 재검(라운드9 재검 PASS) → 사용자 checkpoint commit 결정.
>     그 전 commit·Q7 2단계(CLI/admin)·실렌더·sajugen 런타임 LLM 호출 금지. manifest = changes_requested/next_actor=codex.

> ===== 압축/새세션 재개 앵커 (2026-07-10 Q7 1단계 구현 후보·라운드9 요청 — 이 블록 먼저 읽기) =====
>   [현재] 브랜치 `codex/gunghap-relationship-quality`, HEAD `0b3134f`, upstream 대비 ahead 20. 승인 패킷
>     `handoff/codex-q7-stage1.md` v3 기준 Q7 1단계 구현 후보가 미커밋 워킹트리에 존재한다(tracked 7개 + 신규 2개).
>   [범위] 모듈 schema/레지스트리, job·wealth 제공자 분리, 현행 순서 필터링+기존 sparse 병합, 병합 전 커버리지,
>     N별 페이지·문자 하한, missing/unexpected 차단, content 메타 저장·복원. calc/input/CLI/admin/order 경로 diff 0.
>   [검증] Q7 대상 43 passed, 신규 모듈 17 passed, 샌드박스 전체 **718 passed / 31 skipped / exit 0**,
>     `git diff --check` GREEN, 신규 두 파일 Ruff GREEN. 기준환경 예상 **745 passed / 4 skipped**는 라운드9 재실행 전
>     **확정 불가**. 전체 Ruff는 기존 부채 29건으로 GREEN 아님.
>   [판정] `review_requested`. `verified`·`done` 아님. `REVIEW-FEEDBACK.md`에는 아직 Q7 라운드9가 없다.
>   [SHA 인계] `handoff/current/manifest.json` → `handoff/tasks/q7-stage1-modules-20260710.md`. 기존 Phase2A
>     `handoff/current` 런타임과 파일 단위 공존하며 task/LATEST/실행 폴더/log/run-manifest는 계속 ignored다.
>   [다음] 신선 Claude 라운드9 + 기준환경 전체 pytest → PASS 뒤 사용자 checkpoint commit 판단. Q7 2단계
>     CLI/admin, 실렌더, LLM 호출은 별도 승인 전 금지. 라운드9는 잘못된 `module_sections` 소유권을 현재 게이트가
>     탐지하지 못하는 사각도 판정한다. commit/push/deploy도 지시 대기.

> ===== 압축/새세션 재개 앵커 (2026-07-10 E10 익명화 완료·라운드8 PASS — 이 블록 먼저 읽기) =====
>   [E10 커밋] 실명 익명화 전수(Codex 구현·라운드8 PASS) = `5f6413d`. 운영 코드 3파일 주석·도크스트링 +
>     테스트 15파일 픽스처 + 문서 8종 매핑 일관 치환(로직 0 — pytest 증감 0으로 증명). 패킷 자기 정화(N1~N7
>     파기). 리뷰어 보정 2건: R8-1(q1-q7 역사 grep 기준 서술형), R8-2(docs/00 공개 학술 인용 저자명 원복 —
>     출처 위조 방지, 패킷 §4 허용 예외 1건 명시).
>   [검증] 기준환경 pytest → **728 passed / 4 skipped / exit 0**(증감 0), 골든 28 GREEN(partner.py 주석 diff
>     동반 조건 충족). 기준선 = **728/4** 유지. v2 git grep 3종 0건(학술 인용 예외 1).
>   [PII 잔여 3건(운영자 액션·미결)] ① ignored 산출물 55파일(render/out — 파일명에 실명 로마자) 정리
>     ② git 이력 실명(history rewrite 여부) ③ docs/11 실존 생년월일 보관 여부(골든 참조 케이스).
>   [다음 단계] (1) Q7 구현 발주(1단계 레지스트리·조립/게이트 — 설계·4항목 승인 완료 상태) (2) 후속 --pdf
>     실렌더 확인(운영자 승인 시) (3) PII 잔여 3건 운영자 결정 (4) Q7 완료 후 docs/23 베타 저장·지인 베타·
>     지현님 재발급. push는 지시 대기.

> ===== 압축/새세션 재개 앵커 (2026-07-10 질문 적응 웨이브1 완료·라운드6 PASS — 이 블록 먼저 읽기) =====
>   [웨이브1 커밋] Q1~Q3 구현(Codex)·교차리뷰 라운드6 PASS(Claude)·커밋 `6126d7a`. 구성: Q1 궁합 consult
>     이식(폴백 5프레임+LLM 격리인용·출생지 마스킹+최종 하드 게이트, 빈 질문 skipped) / Q2 프레임 적응+
>     gunghap 죽은 코드 삭제+실명 프롬프트 합성명 교체 / Q3 게이트 신규 3축(부모동의·결혼이행·장기관계)+
>     any→all 강화+최초 고객 키워드 일반화. 패킷 이력: v1 `c3653e0` → 정정 v2 `3a30667`(Codex 정지 보고
>     타당 — 통합 grep 3중 결함, 파일 한정으로 교체).
>   [검증] 기준환경 pytest → **715 passed / 4 skipped / exit 0**(기준선 695/4+신규 20, 감소 0), 골든 28
>     GREEN(calc/input 무변경). 새 기준선 = **715/4**(감소=회귀). 실명 grep(파일 한정) 0건.
>   [실명 확정] 실명 7건(익명화됨) = 전부 실제 사람(운영자 확인). 살아있는 경로
>     실명은 웨이브1에서 제거 완료. 주석·도크스트링·테스트 픽스처 ~250행 = **E10 익명화 패킷**(미발주,
>     웨이브1 뒤 발주 확정). git 원격 이력의 실명은 history rewrite 별도 운영자 결정.
>   [발견 R6-1(비블로커)] `_PROVENANCE_CONTEXT_TERMS` 빈 튜플화로 unbacked_context_terms 검사 항구 no-op +
>     차단측 테스트 소실(REVIEW-FEEDBACK 라운드6 ③). 웨이브2 발주에 주입점 회귀 테스트 복원 포함 권고.
>   [실렌더 검증 완료 2026-07-10 운영자 승인] 합성 2인+실질문("3년 만난 남자친구와 결혼하고 싶은데 부모님
>     반대가 있어요") 무LLM 궁합 relationship 재생성(과금 0) → 18p PDF. consult = 제2장(overview 다음) 위치
>     정확, family_commitment 프레임 직답(부모 반대 이유 분해·결혼 조건·1년 시기 3분할·행동 기준) 육안 확인.
>     금칙 스캔: 썸/고백/새 만남 0·실명 0·적중 0·AI 언급 0. 게이트 신규 3축+재회 축 전부 감지·evidence 충족
>     (missing_axes []). gate_pass=False 원인 2건 모두 기지사항: (a) 분량 18p<30p = Q4가 고칠 상품 정합 오류
>     (설계 문서 명시), (b) veraPDF 7.1-3 = 기존 잔여 1건(render.md 기준 비악화, 새 clause 0). **웨이브1 실경로
>     결함 0.** 산출물 render/out/wave1_synth_rel.pdf(비커밋 영역).
>   [미검증] LLM-on 문안 직답성(API 과금이라 별도 승인 시) — 단 폴백이 기본 산출 경로라 상품 기본형은 검증됨.
>   [웨이브2·E10 발주 완료 2026-07-10] `handoff/codex-question-adaptive-wave2.md` = R6-1(no-op 게이트 주입점
>     회귀 복원)+Q4(분량 상품 차등: gunghap 16p/3000자 신설·followup 10p/2000자 예약)+Q5(후속 --pdf 슬림
>     10~15p, 표준 게이트 경유)+Q6(접수 자동분류+GENERAL 미확정 승인 차단)+**Q7은 설계 1페이지만**(구현
>     게이트). `handoff/codex-pii-anonymize-e10.md` = 실명 익명화 전수(매핑표·순조롭 오탐 주의·partner.py
>     주석은 골든 전수 동반·패킷 자기 정화 포함) — **웨이브2 리뷰 PASS 뒤 별도 세션 실행**(파일 충돌 방지).
>   [웨이브2 완료 2026-07-10] Codex 구현·교차리뷰 라운드7 PASS·커밋 `fec5321`. R6-1(no-op 회귀 복원)+
>     Q4(gunghap 16p/3000자·followup 10p/2000자 — **문자 하한 3000/2000은 운영자 확정 필요 플래그**)+
>     Q5(--pdf 슬림, 새 계산 0 증명·최종 발급 동일 게이트)+Q6(자동분류+GENERAL 미확정 승인 409)+Q7 설계만.
>     새 기준선 = **728 passed / 4 skipped**(감소=회귀), 골든 28 GREEN. 관찰 1(비블로커): admin action_error
>     문구 범용화로 APPROVED 잔류 안내 소실 — 다음 라운드 문구 보강 권고.
>   [Q7 설계 승인 완료 2026-07-10 운영자] `handoff/codex-q7-design.md` 4항목 전부 승인: ①B안(모듈
>     레지스트리+work→work_job/work_wealth 분리) ②분량 공식(모듈 N개=min(30,12+4N)쪽/min(10000,1000+2000N)자)
>     ③RELATION 추천 규칙(상대 입력 있으면 gunghap, 없으면 love 추천만) ④--module 미지정=5모듈 전체(현행 동일).
>     구현은 설계 명시 2단계(1단계 레지스트리·조립/게이트, 2단계 CLI/admin 배선) — E10 완료 후 발주.
>   [Q4 하한 확정 2026-07-10 운영자] gunghap 3000자·followup 2000자 확정(플래그 해제).
>   [E10 패킷 v2 정정 2026-07-10] Codex 정지 보고(잔존 grep이 ignored render/out 실고객 산출물까지 읽음 —
>     실측 확인: tracked 0·실명 포함 55파일) 타당 → §4를 `git grep`(tracked 전용)으로 교체 + ignored 영역
>     접근 금지 명시. **운영자 별도 액션(미결)**: render/out 이하 실고객 산출물 55파일(파일명 자체에 실명
>     로마자 `beta_jangsunjo*` 포함) — docs/22 §1-2 보존정책 따라 정리 필요. git 이력 실명(history rewrite
>     미결)과 함께 PII 잔여 2건으로 추적.
>   [다음 단계] (1) E10 익명화 실행(패킷 v2, 기준선 728/4) → 리뷰 → 커밋 (2) Q7 구현 발주(1단계부터)
>     (3) 후속 --pdf 실렌더 확인(운영자 승인 시) (4) render/out 실고객 산출물 정리(운영자) (5) Q 완료 후
>     docs/23 베타 저장·지인 베타·지현님 재발급. push는 지시 대기.

> ===== 압축/새세션 재개 앵커 (2026-07-10 질문 적응 Q1~Q7 발주 — 이 블록 먼저 읽기) =====
>   [방향 전환] 운영자 결정: docs/23 베타 매뉴얼 **보류**, 질문 적응형 풀이가 선행(질문 미반영 = 상품 핵심 결함,
>     베타 고객에게 부실 풀이 방지). 근거 설계 = `handoff/design-question-adaptive.md`(홈 세션 작성).
>   [설계 검증 완료] Claude 세션이 설계의 5개 근본 지점을 코드로 재검증 → **PASS**(구조 전부 일치). 정정 6건
>     (gunghap 로컬 관계 정의 919-929 재할당로 죽은 코드·익명화 전 하드코딩 이름 2건, fallback.build_fallback
>     situation 팬텀 파라미터, _GH_GUIDE:475 익명화 전 실명 3건, delivery_quality·rules에 최초 고객 키워드
>     김포/계양/고유 모임명/실명 1건(익명화됨) 하드코딩, SECTIONS 실명, _min_pages는 이미 상품 차등 구조)는 패킷 §1에 반영.
>   [발주] `handoff/codex-question-adaptive-q1-q7.md` = Codex 실행 TASK_PACKET. 웨이브1 = Q1(궁합 consult 이식)
>     →Q2(프레임 적응+하드와이어 스윕)→Q3(게이트 관계축+키워드 일반화) 완료 후 멈춤·교차리뷰. 웨이브2 = Q4~Q7
>     (분량 차등·재방문 분량형·자동분류 UI·모듈 조합)은 리뷰 PASS+재승인 후.
>   [baseline] HEAD = 지시문·리뷰 기록 정리 커밋(`d2f3a4d`, 6문서+STATE) 이후. 기준선 재실측 2026-07-10:
>     `./.venv/Scripts/python.exe -m pytest tests/ -q` → **695 passed / 4 skipped / exit 0**(222.69s). push는 지시 대기.
>   [다음 단계] (1) Codex가 패킷 웨이브1 실행 → (2) Claude /cross-review → (3) 운영자 커밋 → (4) 웨이브2 →
>     (5) Q 완료 후 docs/23 베타 저장·지인 베타 2건·지현님 재발급(질문 적응 반영 상태로).
>   [불변 유지] 계산 LLM 위임 0·factcheck 하드차단·APPROVED 물리차단·PII 0·calc/input 무변경(골든 불변).

> ===== 압축/새세션 재개 앵커 (2026-07-10 후속·재방문 라인 완결·push + 발급/베타 문서 — 이 블록 먼저 읽기) =====
>   [코드 완결·원격 반영] 후속·재방문 상담 기능 전체가 검증·커밋·push 완료. 원격 HEAD = `c8b48ad`
>     (브랜치 `codex/gunghap-relationship-quality`, 8커밋). 구성: T0 문안규약+T0-④ 메타발화 / T1 orders·customers
>     스키마+멱등 migration / T2 followup 게이트 서브셋 / T3 슬림 compose+범위밖 백스톱 / T4 CLI+상태머신 /
>     customer-purge CLI(E9 식별자 차등 파기) / docs/22 발급 런북.
>   [검증] 기준환경(전 리소스) `./.venv/Scripts/python.exe -m pytest tests/ -q` → **695 passed / 4 skipped / exit 0**,
>     골든 28 GREEN(계산 불변). 교차리뷰 라운드1~5 전부 PASS(Claude 검증, `REVIEW-FEEDBACK.md` 라운드별 기록).
>     기준선=695/4(감소=회귀). Codex 샌드박스는 skip 상이(E3 리소스 부재) — 완료 근거는 기준환경만.
>   [수정 라운드 반영] A=메타발화 면책·의료 보일러 제거(문맥형 775·"병을 진단하는 자리가 아니라"·완화형 1659·1668 유지),
>     B=`.claude/rules/content.md:12` 두 층 분리(의료 단정 금지 유지·"문구 고정" 폐지), C=`followup/compose.py`
>     allowed_years 빈 경계 factcheck 백스톱 명문화.
>   [미커밋(의도 제외)] `HANDOFF.md`·`REVIEW-FEEDBACK.md`·`handoff/codex-*.md` 4종(지시문·리뷰로그 — 운영자 판단).
>   [문서 상태] `docs/22-issuance-runbook.md` = 커밋·push 완료. **`docs/23-beta-operating-manual.md`(초보자 베타 실행
>     매뉴얼) = 플랜 파일에 초안만 있고 repo 미저장(2026-07-10 ExitPlanMode 거부됨 — 저장 여부 운영자 대기).**
>     매뉴얼 초안 위치: `C:\Users\pc\.claude\plans\ai-brain-...-shimmering-popcorn.md`.
>   [결정] main 전진=보류(운영자 선택: 베타 먼저). 발송 베이스라인 불변.
>   [다음 단계] (1) 지인 베타 2건 실발급 = docs/22·23 절차, 운영자 액션(사람 발송). (2) 피드백 3문항(와닿음/불신/가격)
>     → 수정 항목 나오면 Claude가 지시문→Codex→교차리뷰 라운드6. **현재 Codex에 넘길 코드 작업 없음.**
>   [불변 유지] 계산 LLM 위임 0·factcheck 하드차단·APPROVED 물리차단·PII 0.

> ===== 압축/새세션 재개 앵커 (2026-07-07 후속·재방문 상담 T0~T4 구현 완료) =====
>   [TASK_PACKET 실행 완료] `C:\Users\pc\.claude\plans\ai-brain-50-decisions-2026-07-07-sajugen-shimmering-popcorn.md`
>     기준으로 T0→T1→T2→T3→T4 순서 실행. 패킷 재해석 없음. 모순/범위 이탈로 멈춘 항목 없음.
>   [T0] "상담에서" 원천 문구 제거, 월 표기 `간지월(절기명 - 양력 M/D~M/D)` 고정, 상대시제 절기경계 lint
>     및 docs/prompt/tests 갱신. T0 직후 전체 테스트 **631 passed / 31 skipped / exit 0**, `상담에서` grep 0건.
>   [T1~T4] customers 축과 orders additive migration, follow-up answer gate, Report23 기반 follow-up compose,
>     `issue_final_text`, `run_followup`, CLI `customer-find`/`gen-followup` 구현. 최종 전체 테스트
>     `.\.venv\Scripts\python.exe -m pytest tests/ -q` → **660 passed / 31 skipped / exit 0**.
>   [금지 준수] commit/push/PDF 재생성/LLM 호출 없음. `harness/profiles/local/**` 열람 없음. `scripts/hrun.py` 미실행.
>   [교차리뷰 포인트] `sajugen/followup/*`, `sajugen/store/orders.py`, `sajugen/order_flow.py`, `sajugen/cli.py`,
>     `sajugen/content/temporal_lint.py`, `sajugen/calc/advanced.py`, 관련 tests 및 `docs/03-engine-validation-plan.md` 확인.

> ===== 압축/새세션 재개 앵커 (2026-07-06 다층검증 로드맵 P0~P8 전부 완료 — 이 블록 먼저 읽기) =====
>   [다층 검증 시스템 로드맵 완주] "운영자보다 먼저 버그를 잡는" 프로세스 격상 — P0~P8 전 Phase
>     구현·양방 테스트·커밋 완료. [P4 드라이런 완료 2026-07-06] customer2 합성 드라이런(운영자 승인
>     지출) — 후보30→생존0→확정0, 비용 $0.617(상한 $3의 21%·모델 확정), PII 0 실측, advisory 구조
>     확인. 발견·선제수정: 한글 생년월일 마스킹 갭(self_civils 정밀 마스킹). 잔여 = 실 파일럿 계측
>     (검수 전 신선 발송물 필요 — judge 발화+K/M; customer2 는 정제본이라 M=0). docs/16 기록.
>   [age 팬텀 체인 제거 완료 2026-07-06 QI-2026-07-06-01] 도판 제거 잔여 age 4단계 체인
>     (order_flow→pipeline→render_pdf→render_html) 원자 제거. 소비처 order_flow:385 단 하나
>     (render_meta dict 무마이그레이션) 실측 후 시그니처·계산·kwarg·픽스처·allowlist 일괄 삭제.
>     positional-arg 점검 0. 발급 회귀(test_orders·test_final_render_gate) GREEN. deadparam 미해결 0.
>     P0 ref_date·P1 게이트 SSOT(C4)·P2 dead-param(C2)·P3 골격×lint
>     매트릭스+커버리지+프록시(C1/C3/C5)·P4 렌즈 스윕 인프라(L2 advisory)·P5 논쟁 프로토콜·
>     P6 운영 스킬(/audit·/adjacent·/done)·P7 이식 키트(vkit)·P8 플레이북 배선.
>     불변: LLM 판정은 전 구간 advisory(gate_pass AND 체인 편입 금지), API 호출은 운영자 승인 후.
>   [Phase 8 완료 — docs/19 플레이북 다층검증 배선] §2-1 세션 템플릿에 "L0~L4 어느 층 변경" 1줄 +
>     §2-6 주기 루틴에 /audit·발송 전 스윕·mutation·/adjacent·/done 연결 + §2-7 신설 "경고 다이어트
>     원칙"(스윕 ≤10/회·체크리스트 ≤7·advisory 순증 시 폐기 검토·알람:인시던트 1:1, 하드게이트 예외)
>     + §7-1 one-way door↔설계 논쟁 트리거 표(sg-design-critic 발동, two-way 생략). tests/
>     test_playbook_wiring.py 4건(배선 rot 방지).
>   [Phase 7 완료 — 다층 검증 키트(vkit) 이식 규격] docs/21-verification-kit.md(L0~L4 규격 +
>     측정된 이식 경계표 + 채택 안전장치 4대) + 정본 handoff/kit/(README·manifest.template.json·
>     논쟁기록) + .claude/skills/vkit/(스캐폴딩). **Phase 5 논쟁 프로토콜 첫 실전(dogfood)**:
>     sg-design-critic subagent(Opus·114k tok)가 배포 메커니즘 3안(복사/pip/생성기) 적대 비평 →
>     확정=복사-적응+출처 스탬프 벤더링(pip=결정론·무의존 위반 ruff 선례 재현, 생성기=미검증
>     메타코드로 기각). critic 이 드러낸 4 no-op·착시 차단을 규격에 명문화: (1)채택처 no-op
>     자가검증(게이트 CI 배선+양방 회귀) (2)PII 형상 재정의 필수(생년월일→도메인 PII, 미재정의시
>     탐지 no-op) (3)이질성 채택 검증(단일 모델 퇴화 차단) (4)도메인 리터럴 치환. crypto-signal
>     드라이런=계획만(비파괴). tests/test_verification_kit.py 6건. (handoff/reports gitignore로
>     논쟁기록은 handoff/kit/ 로 이동=추적.)
>   [Phase 6 완료 — 운영 자동화 스킬 3종(.claude/skills/)] /audit(월 감사: 회의적 재검증=문서
>     보장↔코드 프로브 + 문서-코드 대조 + docs/16 포스트모템 전수 + mutation testing
>     verify.py·temporal_lint.py[cosmic-ray 온디맨드]) / /adjacent(사각 인접 스캐너 advisory —
>     경계값·동치류·스코프 제외·동일문구 타 골격·미배선 소비처 나열+테스트 존재표) / /done(증거
>     3종 pytest·SHA·명령 정형, 추정 금지). tests/test_ops_skills.py 5건: frontmatter·읽기전용
>     (advisory Write/Edit 부재)·증거계약·mutation/포스트모템 커버. Stop hook 추가 없음(D-3 보류).
>   [Phase 5 완료 — 설계 결정 논쟁 프로토콜] one-way door 결정에만 쓰는 이질 generator-critic
>     분리 프로토콜(자기선호 편향 회피 2404.13076). .claude/agents/sg-design-critic.md(Opus·
>     읽기전용·승자 선택 안 함, 안별 프리모템·실패 시나리오만) + handoff/templates/design_debate.md
>     (트리거 체크리스트 one-way door 한정→2~3안+트레이드오프→비평 1라운드(반박 ≤1)→루브릭 0-1
>     단일 judge 별도 세션→운영자). tests/test_design_debate_protocol.py 3건: 비평 모델 이질
>     (Opus≠Sonnet)·읽기전용(Edit/Write 부재)·템플릿 트리거/judge 분리 계약(산출물 rot 방지).
>   [Phase 4 인프라 완료 — 발송 전 이질 렌즈 스윕(L2 advisory)] scripts/hsweep.py +
>     harness/prompts/sweep/lens_*.md 5종 + config sweep_lens(Sonnet)/sweep_judge(Opus).
>     파이프라인: 이질 렌즈 5(신선 컨텍스트)→적대 반박 1콜→루브릭 judge(순서 스왑 2콜)→
>     sweep.json/md(상한 10건). 불변(구조·테스트): advisory(verify/order 모듈 비import),
>     PII fail-closed(names 필수·전송 전 마스킹+벨트 재검증·날짜 리댁션), 비용 상한 $3
>     pre-call 중단+부분리포트, 렌즈≠judge 모델, 인용 금지·리포트 스키마 고객 자유텍스트 0.
>     tests/test_hsweep_contract.py 12건(전부 API 0 FakeBackend — 전송 PII·캡·advisory·이질성·
>     프롬프트 계약·전 파이프라인). CLI fail-closed 실측(exit 2 무names/3 무잠금).
>   [Phase 4 실측 대기 — 2중 게이트] 실 API 스윕은 (a) 운영자 명시 승인+3중 잠금, (b) 실 발송
>     후보 PDF 필요(customer3 v9 미생성·PII 입력 필요; h153 은 픽스처). 파일럿 지표(N→M→K, Z=0
>     목표, K/M≥0.7)는 docs/16 "파일럿 계측"에 기록 예정. 첫 승인 지출 후보 = 기존 PDF 합성 드라이런.
>   전체 pytest 642 passed / 4 skipped / exit 0 (P4:624, P5:627, P6:632, P7:638, P8:638→642 신규 4건).
>   [세션 누적] 다층검증 로드맵 P0~P8: 세션 시작 610 → 642 passed(+32건, 회귀 0). main 전진 완료.
>   [Phase 3 완료 — 골격×lint 매트릭스(C1) + 게이트 커버리지(C3) + 프록시 레지스트리(C5)]
>     3 서브커밋: (C3/C5 9f9698e) docs/20-gate-coverage.md — GATE_KEYS 레지스트리 표(20키 ×
>     검증·유형·측정면) + 커버리지 매트릭스 + 프록시 절("신규 검증은 물리 우선"). test_gate_
>     registry.py 가 표를 live verify.GATE_KEYS 와 양방 대조(미문서화/팬텀 행 RED).
>     (C1 6b4e7a1) test_skeleton_lint_matrix.py — 골격 6축(personal 3카테고리+gunghap
>     business/relationship+integrated, API 0·무렌더 render=False) × text lint 8종. 스코프
>     미러링(부록 제외·커플 검사 제외·raw_calc=headwords 게이트 동일함수). 완전성 단언:
>     20 GATE_KEYS 전부 enrolled/matrix-excluded(style=렌더 스코프)/specs-excluded/non-lint
>     로 파티션(신규 게이트 lint→미분류 RED). (보너스 603f1fd) test_lint_properties.py —
>     hypothesis 로 전 text lint 무크래시+결정론(max_examples=200).
>   전체 pytest 610 passed / 4 skipped / exit 0 (P3: 604→610 신규 6건).
>   [Phase 2 완료 — dead-param 정적 스캐너(C2 자동화)] 팬텀 파라미터 3연속(QI-2026-07-04-01)
>     구조 차단. scripts/deadparam_scan.py(stdlib-only AST — 하드 게이트 무의존·이식성) +
>     tests/deadparam_allowlist.txt(참 사유 필수). 제외: self/cls·_접두·*args/**kwargs·stub·
>     단일 return 패스스루·@overload/abstractmethod/override. ruff --select ARG(16건)로 크로스체크
>     (스캐너 7건 — 패스스루 제외가 duck-typed 백엔드 클러스터 정확 필터). 전수 분류:
>     - 즉시 제거(출력 불변·골든 28 GREEN): calc/advanced.geukguk(day_master)·delivery_quality.
>       analyze(page_texts, 내 frontload 제거 잔여) + 각 1 호출부.
>     - allowlist(참 사유·소비처 실측): 관계 폴백 situation×3(LLM compose _compose:999 가 소비 →
>       대칭 실재), compose(title, polish 가 소비하는 섹션 인터페이스), render_html(age, 4단계
>       팬텀 체인 order_flow→pipeline→render — docs/16 QI-2026-07-06-01 추적, 별도 세션 제거).
>     tests/test_deadparam_scan.py 7건: POSITIVE 검출(B-2 no-op 방지) + 제외 앵커 + 하드 게이트
>     + 제거분 회귀 + allowlist 사유 강제. ruff 는 오라클로만(정본=스캐너).
>   [Phase 1 완료 — 게이트 키 SSOT + 요약↔원천 정합 계약(C4 관측 갭 자동화)]
>     실결함 RED-first 수확: verify.gate_pass 20키에 layout_geometry_clean·text_layer_ok·
>     fonts_embedded·tagged 가 있으나 hsummary._PDF_GATE·hrun._retry_reason 수동 목록에서 드롭
>     → 단독 실패 시 이유 불명(pdf_gate_failed)·요약 필드 소실. 3건 RED 실측 후 수정:
>     - verify.py GATE_KEYS 모듈 상수(20키 SSOT, 순서=구조→내용→기하). gate_pass=all(r[k] for
>       k in GATE_KEYS) 순수 리팩터(r[k] not .get — 키 부재는 KeyError 로 드러냄). 키집합 불변.
>     - hsummary._PDF_GATE = [gate_pass, *GATE_KEYS] 파생 + _redact_pdf suffix 확장(*_clean·
>       *_hits_count 자동 표면화, PII-safe bool/int만; *_hits 문구는 curated 경로 유지).
>     - hrun._retry_reason = GATE_KEYS 순회(수동 목록 제거).
>     신규 tests/test_gate_contract.py 9건: RED 갭 3 + 20키 동결 + gate_pass 순수성 + summary⊇
>     GATE_KEYS + 키별 retry + 미래필드 자동표면화 + PII 가드(*_hits 문구·문자열 _clean 미노출).
>   [Phase 0 완료 — ref_date 오늘 기본값(운영자 기억 의존 제거)]
>     신규 sajugen/refdate.py default_ref_date_iso()(단일 소스·monkeypatch seam). 소비처 3:
>     gunghap CLI gen·integrated CLI gen(미지정→오늘) + hrun _regen_pdf(integrated/gunghap 분기,
>     부재 시 오늘 명시 주입=관측성). 라이브러리 build_gunghap/build_integrated_full None→6-13
>     폴백 유지(테스트 결정론·재렌더 영속 불변), integrated --content 재렌더는 저장 ref_date 재현.
>     양방 테스트: test_harness.py — hrun regen 의도 변경(미지정→오늘 주입) + gunghap/integrated CLI
>     today 양방(헬퍼 monkeypatch 고정값, 자정 flakiness 회피). docs/19 §11 개정.
>   [비블로킹 플래그(Phase 4 전 처리)] hrun --regen 이 ref_date 부재 프로파일에서 날짜 민감해짐 —
>     로컬 픽스처 프로파일(harness/profiles/local/**, gitignored·PII)에 ref_date 를 고정해야
>     달력일마다 게이트 결과가 드리프트하지 않는다(특히 gunghap_h153.yml). regen 전 운영자 조치.
>   전체 pytest 604 passed / 4 skipped / exit 0 (P0 586→588, P1 588→597, P2 597→604 신규 7건).
>
> ===== 압축/새세션 재개 앵커 (2026-07-05 1장 직답 문단 제거 + frontload 게이트 철거 — 이 블록 먼저 읽기) =====
>   [운영자 실격 판정(v8 육안) → 지시 개정 실행] 1장 도입의 직답 문단(concern_snapshot)이
>     "처음부터 답을 흐린다"고 실격 — 성향 슬롯만으로 만든 결정론 템플릿이라 어떤 문안으로도
>     뭉툭. 신청 질문 직답은 consult 장(고객 원문 기반 LLM + 전용 게이트) 전담으로 회귀
>     (docs/13 back-peak 원 설계). 이번 커밋에서 구현·검증 완료:
>     - 골격 제거(rules.py): T["concern_snapshot"] 3분기 블록 + _love_snapshot_text() 삭제,
>       intro join = summary+howto+keywords(직답 문단 소멸, '사주를 펼쳐 놓고 보면…'로 시작).
>     - frontload 게이트 철거(delivery_quality.py): _frontloaded_result·_FRONTLOAD_CHARS·
>       physical 계열(_page_has_direct_answer·_physical_frontloaded_result·_PHYSICAL_FRONTLOAD_PAGES)
>       + analyze() 산출/판정(missing_frontloaded_answer·physical_frontloaded_answer) 전부 삭제.
>       builder.py intro 선검사 2곳 삭제. llm_sections intro 가이드 = '질문 답은 consult 전담'.
>     - 유지(건드리지 않음): consult_direct_result + pipeline 하드 게이트 + 2차 재시도(답변 품질
>       보증 기계장치), _FRONTLOAD_TERMS·_concern_snapshot_label·_love_context_detail·_cp_line
>       (consult 소비 공유 헬퍼), gunghap frontload_summary(궁합 전용 별개 장치).
>   [양방 테스트] test_frontload_guard.py 삭제(가드 소멸), physical/premium-frontload 테스트 삭제,
>     test_intro_no_direct_answer_answer_lives_in_consult(역방향 앵커) + test_intro_frontload_gate_removed_two_way(신규 양방) 추가.
>   [QI] docs/16 월 시제 사고 항목 (b)에 폐기 후속 1줄 등재.
>   전체 pytest 586 passed / 4 skipped / exit 0 (592 → 삭제 7 + 신규 1 = 586, 정합·회귀 아님).
>   [다음(운영자 입력 대기)] v9 재생성 승인됨(~$0.65) — customer3 입력(PII, 저장소 밖)을
>     운영자에게 요청 → API 0 룰 전용 프로브 PASS 선검증 후에만 v9 LLM 재생성. 실패 시 v9 금지.
>   [프리플라이트 실측(20260705-204000, 재생성/LLM 없음·api_calls=0·무과금)] pytest 586/exit 0.
>     h153 두 픽스처 delivery_quality_clean=True(내 frontload 변경 부분 clean). 단 gate_pass=False —
>     원인은 loanword(3)+raw_calc(2) 히트로 frontload와 무관. 정적 h153 PDF(03:17/03:33 렌더)가
>     이후 P5 loanword/raw_calc lint 등재(8e291aa·332620e)에 걸린 픽스처 노후화. 내 커밋은
>     client_tone_lint diff 0줄·verify 주석 1줄뿐 → 부모 100f4d9에서 이미 False(비악화 실증).
>   [h153 P5 lint 동기화 완료(운영자 승인, 20260705-215457, api_calls=0·무과금·룰 전용 재렌더)]
>     ANTHROPIC_API_KEY 부재 + P5가 골격 스윕(8e291aa) 완료 → 룰 전용 재렌더로 loanword/raw_calc
>     동기화. personal 29p·gunghap 10p 모두 gate_pass=True·loanword_clean=True·raw_calc_head_clean=True,
>     all_gates_pass=True·final=PASSED·pytest 586. 부록 오행국 정의 1건은 verify body/appendix
>     분리로 게이트 제외(허용구역). 픽스처가 LLM 윤문본→룰 전용(짧아짐, 결정론) 전환 — 회귀
>     baseline 로는 적합. PDF는 gitignored(비커밋).
>
> ===== 압축/새세션 재개 앵커 (2026-07-05 품질 총정비 P0~P6 + v8 재검수 대기 — 이 블록 먼저 읽기) =====
>   [운영자 실격 판정(v7) → 총정비 완료 — 승인 계획 7 Phase 전부 구현·커밋(각 양방 테스트)]
>     P0 챕터별 폴백 관측(7c94afa: GuardReport ids+cli chapters 줄+hrun summary) /
>     P1 직답 골격 재작성(7b154fc: [방향 단정→궁 실명 근거→시기→첫 행동], generic 388→900자대) /
>     P2 consult 직답 게이트+2차 재시도(02e7c1d: consult_direct_result, pipeline 하드 게이트) /
>     P3 guarantee 정밀화(a896515: 결과어 결합만 차단·행동/시기 단정 허용, '보겠습니다' 선치환) /
>     P4 명리-자미 층위 통합 B안(61542b9: _palace_para hint·정형 5회 소거·10장 실사실 교차 요약·
>       주제 장 가이드 통합 지시·docs/03 §5 보강) /
>     P5 날것 용어 소멸(8e291aa 골격 스윕 26곳 → 332620e lint 등재: 대운수·오행국·bare 분포·
>       리듬 하드밴 + '결'/'의 색' 필러 카운터 warning + term 밀도 보고) /
>     P6 조판 재시도 확대(1922ef0: orphan 스필 단독 = 무과금 재렌더 — v8 1차 파기 실측 갭).
>   [QI 등재] docs/16 QI-2026-07-05-03(consult 폴백 false-PASS + 발송 리포트 오보 — 관측 갭).
>   [v8 = 발송 후보, 운영자 육안 검수 대기] customer3_money_v8.pdf 40p·sha12 abc234aab5b0·
>     dense 16,138자(v7 +9.5%)·게이트 PASS·consult/closing 윤문 성공·폴백 intro 1(직답 유실
>     반려→직답 골격 보존=의도 동작)·발송 벨트 전부 0(지적 부류 포함)·'오행국' 본문 0(부록
>     정의 1건=허용구역). 반복어 warning(자리 91/26 등)은 보고 전용 — FAIL 승격은 육안 후 결정.
>     리포트: handoff/reports/customer3-money-v6-release/pdf_review_report.md (REVIEW_REQUIRED).
>   [비용] v8 지출 2회(1차 파기 ~$0.63 + 재실행 ~$0.63 ≈ $1.26 — 계획 안내 '2회까지 ~$1.4' 내).
>     1차 파기 원인(orphan 단독 재compose 강제)은 P6 로 구조 해소.
>   [잔여 정리] 2026-07-05 완료: __probe_gunghap_business__ 쌍·__probe_v8_rule__ 쌍·
>     sajudoryeong_layout_probe_13_* 3쌍 삭제(10파일). 보류: customer3 v6/v7/v8 쌍은
>     납품 후보(PII)라 v8 육안 검수·v9 확정 후 운영자 지시 시 삭제(현재 미삭제).
>   전체 pytest 592 passed / 4 skipped / exit 0 (세션 시작 539 → +53).
>
> ===== 압축/새세션 재개 앵커 (2026-07-05 h153 픽스처 교체 + QI-2026-07-05-01 — 이 블록 먼저 읽기) =====
>   [h153 픽스처 교체 완료 — 운영자 승인 regen] 구형 픽스처가 06-25 이후 게이트 강화에 밀려
>     FAIL 되던 것을 최신 게이트 통과본으로 교체. personal 37p·gunghap 17p 모두 gate PASS
>     (리포트 20260705-031710·20260705-033305). 구본 PDF 는 재생성으로 대체(동일 경로 덮어씀).
>   [QI-2026-07-05-01 business 궁합 골격 미동기화 — 수정 완료, 상세 docs/16] gunghap 1차
>     재생성이 하드 게이트에서 실패: 금지어 등재('십성으로' 등) 때 relationship 만 순화 배선되고
>     business 골격 미동기화 + 장 제목 em dash 4건 + hrun 이 regen 실패를 "done" 으로 표기하던
>     관측 갭. 수정 3커밋(전부 양방 테스트): d7dc63c(골격·제목) / 88fb6a1(hrun ref_date 전달
>     +failed 표기) / e9efc7a(integrated CLI --ref-date, 팬텀 파라미터 해소).
>   [비용 교훈] 재생성 실패 = compose 지출 후 파기라 1회분 낭비. 재시도 전 API 0 룰 전용
>     프로브로 게이트 통과 선확인이 표준 순서(docs/16 비용 주의 항목).
>   [백로그 완료 — LLM 사용량 관측 배선(288e464)] content/llm_usage.py 단일소스 신설,
>     gunghap compose·llm_polish·classify 집계 배선, 빌드 CLI 3종 "LLM usage:" stdout 출력,
>     hrun 파싱→summary regen_llm_usage + regen_returncode 화이트리스트 등재(그동안 드롭).
>     테스트 9건. 다음 재생성부터 지출이 summary 에 남는다(과금액은 Console 대조).
>   [v6 발송 취소 → v7 재검수 대기 2026-07-05 — QI-2026-07-05-02, 상세 docs/16] v6 발송
>     직전 운영자 발견: 1장 "압축해 보겠습니다"(작업 예고)·"차례대로 확인하세요"(빈 지시) —
>     둘 다 LLM 아닌 룰 골격(rules.py) 원문이며 1장은 rule-only 라 골격이 곧 고객 표면.
>     규범('~보겠습니다 금지')이 프롬프트에만 있고 골격·lint 미동기화(QI-05-01 개인판).
>     수정(0c91f03): rules.py 9+2+1곳 상담가 화법 + customer_meta_lint 신규 룰 2종
>     (writer_task_announcement·formulaic_empty_instruction) + 전 섹션 실빌드 동기화 앵커.
>   [v7 = 발송 후보] customer3_money_v7.pdf 39p·sha12 06be3fa768ae·게이트 PASS·지적 문구 0·
>     신규 룰 포함 벨트 0·usage 17호출/입력 102,757/출력 26,904 토큰(~$0.7, 관측 배선 첫 실전).
>     ** 전 챕터 LLM 재작성본 — 운영자 전문 육안 검수 후 발송(리포트 REVIEW_REQUIRED:
>     handoff/reports/customer3-money-v6-release/pdf_review_report.md). ** v6 쌍(pdf/html)은
>     발송 보류·검수 완료 후 폐기(수동 삭제 목록).
>   [잔여 정리(수동 삭제)] __probe_gunghap_business__.{pdf,html} + (v7 검수 후) v6 쌍.
>   전체 pytest 566 passed / 4 skipped / exit 0 (기준선 562+신규 4).
>
> ===== 압축/새세션 재개 앵커 (2026-07-05 백로그 2건 완료 — 이 블록 먼저 읽기) =====
>   [백로그 완료 1] '또렷' 변형형 선치환: postprocess._STYLE_REPLACEMENTS 를 어간 캐치올
>     ('또렷'→'분명', '또렷이'만 특례 '분명하게')로 확장 — '또렷해지는/또렷해집니다' 등
>     전 활용형 커버(v6 폴백 원인). style_lint(또렷[가-힣]*) 가드는 불변(완화 0), 양방 2건.
>   [백로그 완료 2] gunghap/integrated ref_date 월 시제 닻 배선(QI-2026-07-04-02 관계 확장):
>     [기준 시점] 닻을 llm_sections.temporal_anchor_block 으로 단일소스화(개인 경로와 공용) →
>     gunghap._compose 프롬프트 주입(그동안 궁합 프롬프트엔 연도 닻조차 없었음) + 가드체인
>     temporal_lint ref_date 전달. build_gunghap/build_integrated_full/_render_integrated 에
>     ref_date 파라미터(미지정 시 기존 verify 하드코딩과 동일한 연중 6-13 기본 = 하위호환,
>     verify 하드코딩 3곳 제거), integrated 는 개인 장 build_report 에도 배선, content.json
>     영속 ref_date 를 재렌더가 소비, CLI --ref-date(cp949-safe). 양방 6건(프롬프트 닻/지난 달
>     폴백/미래 달 통과/build 배선+레거시 기본/integrated 스레딩 2).
>     ** 실주문 생성 시 ref_date=생성 당일 전달할 것(미전달 시 연중 기본이라 6월 이후 주문은
>     지난 달 시기 조언 사각 잔존) — 운영자 플레이북 반영 완료(docs/19 §11, ac371f6). **
>   전체 pytest 547 passed / 4 skipped / exit 0 (170.2s, 기준선 539+신규 8).
>   [main 전진 2026-07-05] main 37bbe12 → ac371f6 fast-forward + push(운영자 지시).
>     포함분 = 이번 백로그 2건(3e8407e·151ef23·cc9abb4·ac371f6) + 브랜치에 쌓여 있던
>     팬텀 파트너 QI(F1~F5)·월 시제 QI 3종(b3cc880·3ceaae8·e195dfd) 등 31파일 +1,216줄.
>     전진 근거 = 브랜치 HEAD 전체 pytest 547 GREEN(마지막 2커밋은 문서 전용).
>     작업 브랜치 codex/gunghap-relationship-quality 도 origin 동기화 완료.
>
> ===== 압축/새세션 재개 앵커 (2026-07-04 월 시제 QI + v6 발송 후보 — 이 블록 먼저 읽기) =====
>   [QI-2026-07-04-02 월 단위 시제 오류 — 수정 완료, 상세 docs/16] 7월 생성 풀이가 지난 4·5월을
>     행동 시기로 권함(운영자 발견). 수정 4종(전부 양방 테스트·커밋): 월 시제 닻+게이트+재작성
>     피드백(b3cc880) / 꼬리 병합 14→90자 스필 소멸(3ceaae8) / intro 직답 유지 가드(e195dfd).
>   [CUSTOMER 시기재물 v6 = 발송 후보] customer3_money_v6.pdf 40p·밀도 15,494자·387자/쪽·
>     gate PASS·월 시제 0·저밀도 0·커플어 0·직답 유지. 폴백 2 = 가드 정당 작동('또렷해지는'
>     변형형·'갑자' factcheck 하드차단). volume 기준(16,000/400) 소폭 미달은 보고 전용.
>     발송은 운영자 육안 검수 후. [완료] 구본 8종(pdf+html 16파일) 파기 — v6 쌍만 보존(운영자 지시).
>   [백로그] (2026-07-05 완료 — 상단 앵커) '또렷해지는' 등 변형형 선치환표 추가 / gunghap 경로
>     ref_date 월 닻 배선(개인 경로만 반영됨 — 관계 상품 시기 조언도 동일 리스크).
>   전체 pytest 539 passed / 4 skipped / exit 0.
>
> ===== 압축/새세션 재개 앵커 (2026-07-04 팬텀 파트너 QI 수정 — 이 블록 먼저 읽기) =====
>   [QI-2026-07-04-01 팬텀 파트너 — 원인 규명·수정 완료] 운영자 발견: 궁합 없는 개인 풀이에
>     궁합·관계 문구 혼입(CUSTOMER_3). 합성 재현으로 확정: 고민 원문의 사건 날짜가 상대 생일로,
>     동사 조각("이사한")이 이름으로 둔갑 → "이사한님"(2020년생) 명식·관계 서술이 consult 주입.
>     원인 2층 = (유입) find_partner_births 가드 인자 미배선+인물 문맥 미요구 / (감지) 커플 지칭
>     룰 부재+verify product dead parameter. "배선됐지만 소비 안 되는 파라미터" 3연속 패턴.
>   수정(F1~F5, 상세 docs/16 QI-2026-07-04-01):
>     F1 인물 문맥 게이트(partner.py _has_person_context)+self_solar/ref_year 배선(builder).
>     F3 couple_pair_reference 룰+partner_present 배선(Report23→verify/pipeline/order_flow/hverify)
>       — 1인 문서에서만 candidate→hard 승격(다인 상품·파트너 개인 풀이 오탐 0, 완화 0).
>     F2 재회 전제 문구는 원문 재회 토큰 시에만(중립 문단 신설, "짧은 안부" 밀도 유지).
>     F4 compose 가드체인 placeholder/커플 지칭 부착(strict_pair=파트너 부재).
>     부수: partner_block "신청자"(hard 금지어) 7곳→"본인"(잠복 hard fail 해소).
>   실측: 결함 입력 재현→수정 후 팬텀 0·strict 위반 0. 전체 pytest **523 passed / 4 skipped /
>     exit 0** (193.1s, 신규 10건 = test_couple_language 8 + test_partner 2). 골든 전수 GREEN.
>   [운영자 참고] 과거 발송물 중 "고민에 날짜가 든 파트너 미포함 개인 풀이"가 있으면 동일 증상
>     육안 1회 권장. CUSTOMER_3 재생성은 입력 재제공 시(LLM compose 는 승인 후).
>   [2026-07-04 후속 — CUSTOMER_3 윤문본 생성 과정에서 결함 2건 추가 발견·수정(운영자 승인 push)]
>     (1) 개인 경로에 저밀도 무과금 재렌더 재시도 부재 → 저밀도 1건에 재compose 과금 강제(실측
>       재시도 2회 ~$1 소모). integrated _LAYOUT_VARIANTS 패턴 이식(pipeline.generate, API 0 재렌더,
>       저밀도 단독 실패만 발동·하한 13.8pt FAIL 유지). 양방 테스트 3건.
>     (2) 기하 게이트 래그드 과탐(감사 B-2 예고 모드 실전 발생): 좌단 31.2mm 정위치인데 짧은 줄
>       페이지가 |좌-우| 비대칭 10.3mm 로 FAIL → 검출기를 column_shift(좌단 기대위치 이탈>5mm)로
>       교체(원 버그 좌20mm=이탈 11mm 는 계속 FAIL, 완화 아님). 래그드 오탐 회귀 앵커 신설.
>     + llm_sections flow 가이드 '어디쯤인지' 자기모순 제거('쯤' 프라이밍 벨트).
>   [CUSTOMER_3 윤문본 v2 = 발송 후보 확정 2026-07-04] customer3_money_v2.pdf **39p·19,494자·
>     14.5pt(기본 크기, 재시도 불필요)·gate_pass=True**. 폴백 1챕터뿐(frame '또렷하게·기운' 반복 —
>     가드 정상)·**consult 윤문 통과**('쯤' 프라이밍 제거 효과, 이전 2회 연속 폴백 → 해소).
>     PII-free 검증: 커플어·팬텀 명식·재회·신청자·쯤 전부 0('의 명식' 1회 = 본인 명식 정상 서술).
>     발송은 운영자 육안 검수(첫 장·consult·마지막 두 장) 후. 이번 재생성 비용 ~$0.5(합계 ~$2).
>   [v3 = 최종 발송 후보 갱신 2026-07-04] customer3_money_v3.pdf 39p·밀도 15,308자·393자/쪽·
>     gate PASS·consult 윤문·'또렷' 폴백 소멸(선치환 적중). 폴백 2(nature '쯤'·love '십성으로').
>     volume 벤치마크(신설, 보고 전용): 기준 16,000자·400자/쪽 대비 -692자(v2 는 -1,371자).
>     다음 개선 후보(미착수): compose 재작성 시 위반 단어를 프롬프트로 피드백(현재 재작성은
>     실패 사유 미전달 -> 같은 단어 재발 확률 높음). 구본 4개(customer3_money*.pdf 중 v3 제외)는
>     운영자 검수 후 파기.
>   [구본 참고] customer3_money_final.pdf 31p·16,442자·13.8pt(재시도 발동) —
>     **gate_pass=True**(교정 게이트 전 플래그 clean). 주의: compose 폴백 2챕터(ziwei '또렷하게'·
>     consult '쯤' — 가드 정상 동작으로 골격 사용). consult 가 골격이므로 완전 윤문본 원하면
>     재생성 1회(~$0.5) 필요 — 운영자 판단. 발송은 육안 검수 후.
>     비용 실측: 이번 건 compose 3회 실행(~$1.5) — 재시도 이식으로 향후 저밀도 재과금은 차단됨.
>     전체 pytest 527 passed / 4 skipped / exit 0.
>
> ===== 이전 앵커 (2026-07-04 재감사·지침 개편) =====
>   [2026-07-04 구현 재감사 완료 — 판정: 로드맵 실행 검증됨] 감사 세션이 완료 보고를 회의적으로 재검증:
>     전체 pytest 재실측 512 passed/4 skipped/exit 0(165.7s, 보고와 일치). P0-1 자시(23:50 프로브 일주
>     익일 전환+정책 분기 실효)·P0-2 표지(builder cover 제외+mask 벨트)·A-1/A-2/A-3/A-4 전부 동일 프로브
>     재현으로 해결 확정. 전 태스크 스팟체크 **완화 의심 0**(전부 강화 방향+양방 회귀 동반).
>     부분 3건 → 후속 소수정 완료: N1 _TOC_MAX_CHARS 520 경계 코너 테스트(test_render_verify), N2 classify
>     max_tokens=256 값+mode 단언(test_sdk_retry_policy), N3 아래 별-궁 판정 표현 교정.
>   [2026-07-04 지침 체계 개편 — 운영자 승인 플랜] 조사 근거(agents.md 표준·code.claude.com/docs 공식):
>     - AGENTS.md = 공유 진실원 재편(프로젝트 성격 6개조 + "세팅이 이런 모양인 이유" 표(규칙↔사고) +
>       작업 규율 YOU MUST 7개조 + Programmatic checks 명령형 섹션). 80줄.
>     - CLAUDE.md 첫 줄 `@AGENTS.md` import 로 단일 소스화(중복 블록 제거, Claude 전용만 잔류). 55줄.
>     - .claude/rules/10-methodology.md 신설(상시 로드): 검증 규율 7개조 + 전문가급 설계 규율 8개조,
>       각 조항에 이 프로젝트 실증 사례+출처. 00-immutable.md 4개조에 IMPORTANT/YOU MUST 마커(내용 불변).
>     - docs/18-operator-fundamentals.md 신설: 운영자 기본기 10영역(리뷰·테스트·포스트모템·개인정보법·
>       시크릿·의존성·백업 3-2-1+SQLite backup·발송 체크리스트·자동화 편향), 전부 권위 출처+실행 명령.
>   [N3 표현 교정] 아래 "별-궁 factcheck feasibility 판정"의 근거는 실측 FP/FN 측정이 아니라
>     **코드 구조 근거(polish 경로 존재) + 파서 취약성 판단**이다. 결정(미구현)은 유지 — 어설픈 게이트
>     회피 원칙(10-methodology B-8). 커밋 7503a2b 메시지의 "측정 기반" 표현은 과대였음을 정정.
>   [운영자 수동 대기 3건 — 도구 준비됨] (1) tmp/ 고객 파생 임시파일 수동 파기(명령은 아래 Phase 1 블록),
>     (2) 기존 customer2 최종 PDF 는 강화된 게이트 기준 미달(p16 꼬리) — content.json 무과금 재렌더+재검수
>     여부 결정, (3) scan_zasi_affected.py 로 과거 발송물 자시 영향 확인.
>   push 는 운영자 지시 시만.
>   [2026-07-04 운영 안전망 마감 — 운영자 선택 실행] (1) main fast-forward 8590d0e->2aa95da + push
>     (발송·복구 기준점 복원, 85커밋 뒤처짐 해소). (2) 첫 백업 실행(docs/18 §8): backup/ 에
>     orders_20260704.sqlite(비어있음 — 주문 0건)·kasi_cache_20260704.sqlite(음양력 55,152일 검증)·
>     content.json 2개, OneDrive/sajugen-backup 오프사이트 1부, 백업 열림/조회 복원 검증 완료.
>     backup/ 는 gitignore(2aa95da). (3) 자시 영향 스캔 = 영향 주문 0건(P0-1 소급 영향 없음 확정).
>     (4) customer2 v2 무과금 재렌더 완료(51p·gate_pass·저밀도 0·13.8pt 축소 변형) — 운영자 육안
>     검수 대기. [완료 2026-07-04] tmp PII 파기 — 운영자 지시로 실행(69개 파기, audit_brief.md 만 보존,
>     synthetic-tmp/ 전체 삭제). 잔여 운영자 수동 = v2 검수/교체 판단 1건뿐.
>   구현 SSOT = `handoff/audit-followup-roadmap.md` (2026-07-03 전수 감사 후속 로드맵 Phase 1~5).
>   진행 상태: **Phase 1·2·3·4·5 전 항목 완료 — 2026-07-03 전수감사 후속 로드맵 완결.**
>     T5.1~T5.10 전부 소진(T5.7 측정 포함). 로컬 clean·전부 push.
>     [E2E 통합 검증 완료 2026-07-04, 커밋 71fd609] 접수→생성(실렌더)→검수→승인→발급(DELIVERED) 전 구간
>       실경로 clean 통과 실측(gate_pass=True·needs_review=False) — Phase 3~5 변경이 함께 동작 확인.
>       opt-in 테스트 test_order_lifecycle_e2e(SAJUGEN_RUN_E2E=1, 기본 스위트 제외 — T5.9 'E2E 정기 실행 방안').
>     [T5.7/D-2 측정 완료 2026-07-04] veraPDF 7.1-3 귀속 = **Chromium 태그드 구조**(실측): 언더레이 전
>       순수 Chromium PDF clauses=['7.1-3','7.1-8'], 최종(underlay+harden)=['7.1-3']. 즉 (a) 7.1-3 은
>       Chromium 원본에 이미 존재(PyMuPDF 한지 언더레이 무혐의), (b) harden 이 오히려 7.1-8 을 제거(순개선).
>       → '아키텍처 변경 없음' 실측 근거 확보, D-2 종결. 코드/아키텍처 변경 없음(측정만).
>     [완료 요약] T5.3 content.json 메타(74128b0), T5.8 G-10 전부 커밋, T5.10 무효 max_retries 없음(실측),
>       T5.7 7.1-3 Chromium 귀속(실측). 모델 업그레이드=톤 A/B 없이 금지(불변).
>   [Phase 4 T4.5 완료 2026-07-03, 커밋 `83467a2`] /generate 구형경로 PII 제거(E-1) + G-10 brand 필수검증.
>     운영자 결정=최소 정리: 파일명 saju_<uuid12>.pdf(DOB 제거)·X-Saju-Bazi 헤더 제거(비-PII X-Gate/X-Pages
>     유지)·경로 유지. G-10(brand 빈값 422 fail-closed)를 함께 커밋(운영자 결정). 회귀 2건. tests/ **501 passed**.
>     [잔여] scripts/dump_reading.py G-10 미커밋(별건).
>   [Phase 4 T4.2 완료 2026-07-03, 커밋 `88c31b8`] safe_lint _OUTCOME 승진/창업/취업류 확장(G-7).
>     결과 동사에 승진/창업/취업/개업(하|합) 추가 — '-합니다' 형 사각 보강('승진된다'는 이미 된다로 커버).
>     C1 완화 원칙(부사 단독 허용, 부사+결과동사 결합 0~14자만 차단) 불변. 실측: 결과보장 4형 차단 +
>     흐름/행동권유/부사단독 오탐0 + 골든 6케이스 clean·safe=0. 앵커 차단4·허용3 추가. tests/ 493 passed.
>   [Phase 4 T4.3 완료 2026-07-03, 커밋 `c5d2e76`] masking 시각 표현 확장(G-6).
>     (2) mask_birth_in_text 를 12시간제(오전/오후 H시 M분·H시 단독)·'H시반'(분=30 한정)까지 확장, 과다
>       마스킹 방지(lookahead — '오전 7시 15분' 부분치환·다른시각 비치환). (1) [finding] 출생지=좌표만 입력
>       (label 기본 '서울' 고정, 이름 미입력) → 마스킹할 출생지 이름 PII 부재, 로드맵 '출생지 문자열 치환'
>       대상 없음. 실측: 마스킹4형·오마스킹4형·반케이스 회귀. tests/ **495 passed**(493+2).
>   [Phase 4 T4.4 완료 2026-07-03, 커밋 `9186358`] 윤달 15일 분할법 산입 기준 고지 자동 삽입(G-8, 절대규칙5).
>     E2E 확인: 현 경로(e2e_p8_leap)에 고지 부재 실측 → 신설(진짜 갭). is_leap 배선(unknown_time 미러):
>     pipeline→builder→rules.build_all, cli·order_flow(gen_params+run_generation)에서 '음력 윤달생'만 전달.
>     고지 위치=ziwei_summary 조건부 append(자미 표시 리포트에만). 실측: integrated/ziwei+leap present,
>     myeongni+leap·non-leap absent, 전부 guard.clean. app.py /generate 는 미배선(G-10 번들 방지, T4.5 정리).
>     회귀 4건. tests/ **499 passed**(495+4).
>   [Phase 4 T4.1 완료 2026-07-03, 커밋 `f579f43`] factcheck 연도 화이트리스트(G-4).
>     (1) 연도 화이트리스트: allowed_tokens.allowed_years(기준·세운·월운·대운시작·출생) + check_with_allow
>       가 허용 밖 'YYYY년'(년 접미 필수) 하드차단. 미제공 시 skip(back-compat). 실측 골든 6케이스 clean·
>       연도오탐0, 결함 2035 차단.
>     (2) [실측 정정] '자미' 오탐 무발생·ziwei_star 검사 사문(14주성 상시 14/14 배치) — 문맥경계 추가 불필요,
>       주석으로 사문 명시. tests/ **493 passed**(487+6).
>       [별-궁 factcheck feasibility 판정 2026-07-04 — 만들지 않음] ziwei 섹션은 _STATIC_OK 아니라 use_llm 시
>       polish(재윤문)됨 → 별을 잘못된 궁에 재배치할 저확률 갭 실재. 그러나 룰 텍스트의 'X궁 주성인 [별들]'
>       구조를 polish 가 재구성하면 궁-별 쌍 파싱이 매우 취약(사화 등 비귀속 언급과 혼동 → 오탐 위험 큼).
>       저확률 오류에 고복잡·고오탐 파서 게이트 = '어설픈 게이트' → **미구현 확정**. 갭 제거가 필요하면
>       'ziwei 섹션 polish 제외(룰 전용화)'가 견고하나 톤 하강 = 운영자 결정 사항(미실행).
>     [문서화된 상호작용, advisor] 연도 가드는 근거 밖 연도를 factcheck 위반 처리 → 이론상 LLM 챕터가 룰
>       폴백될 수 있음(안전, 나쁜 발송 아님). 단 compose 프롬프트가 이미 '근거 자료 연도만'으로 제한
>       (llm_sections.py:84·98-99)해 근거 밖 연도를 안 뱉으므로 실무상 폴백 미발생. worun 은 비-연도 월
>       라벨이 int() 실패로 무해히 skip(스트레이 연도 미주입) — 세운=근접 2025~2029 전부 허용. '왜 이 챕터가
>       룰로 폴백?' 조사 시 이 연도 가드부터 확인.
>   기준선: `tests/ 493 passed / 3 skipped`, 골든 22건·parity 100건 불변·오차단 0·veraPDF ['7.1-3'] 비악화.
>     HEAD=커밋 f579f43(로컬, push 안 함). 브랜치 codex/gunghap-relationship-quality.
>   [환경 주의] iztro-py>=0.3.5 필요 — 이 .venv 만 설치됨. 새 환경/CI 는 `pip install -e .` 또는 재설치.
>   [미결·운영자 판단] (1)T2.1 영향구간=진태양시 23~24시 출생 기존 발송물 재검토 — **식별 도구 제공**
>     `./.venv/Scripts/python.exe scripts/scan_zasi_affected.py --db data/orders.sqlite`(day_offset=1 주문
>     order_id/state 만 출력, PII 없음; 재렌더/재발송은 운영자 승인). (2)tmp/ PII 임시파일 수동 삭제(rm deny).
>     (3)G-10 전부 커밋 완료(app.py T4.5·dump_reading 운영자 지시).
>   [작업 규율] calc/게이트 수정=골든 회귀 동반+양방 테스트. 검증(실측)값으로만 보고. 고객 PII 채팅 비출력.
>     테스트=`./.venv/Scripts/python.exe -m pytest tests/ -q`. push 는 운영자 지시 시만.
> =====================================================

> ★ 활성 워크플로우 (2026-07-03 갱신 — 감사 후속 수정 로드맵 실행 중, 이 줄 먼저):
>   전수 감사(2026-07-03) 후속 수정 로드맵 = `handoff/audit-followup-roadmap.md` (구현 source of truth).
>   프로토콜: 한 세션 = 한 Phase. Phase 1~5 순차. push 는 운영자 지시 시만.
>   [Phase 1 = PII/유출 봉쇄 — 완료 2026-07-03] 3커밋(브랜치 codex/gunghap-relationship-quality, push 안 함):
>   - T1.1 [A-1] `f4766bd`: .gitignore 에 tmp/·synthetic-tmp/·*.content.json 추가(고객 content.json·
>     렌더물 커밋 유출 차단). 추적 PII 파일 0(히스토리 노출 없음). 실제 tmp/ 파일은 rm deny 로 운영자가
>     `! rm -rf synthetic-tmp && find tmp -mindepth 1 -not -name audit_brief.md -exec rm -rf {} +` 수동 파기(운영자 '전부 삭제' 선택).
>   - T1.2 [P0-2] `bce6c27`: 표지(cover) polish 경로로 생년월일 원본이 API 전송되던 결함 차단.
>     builder polish/compose 분기에 cover 명시 제외 + llm_polish 에 mask_civil 방어겹 + masking.mask_birth_in_text
>     헬퍼 추출. 테스트=LLM 아웃바운드(polish+compose) 전수 스캔 생년월일 0건.
>   - T1.3 [A-3·B-3·E-2] `afdce39`: verify _orphan/_low_density hit 의 본문 스니펫(text) 제거(근본) +
>     hverify delivery_quality 를 rule/메타 화이트리스트만 forward(hsummary 계약 정합) + order_flow 생성
>     예외 audit note·orders.delete reason 마스킹. [deviation] order_flow render_meta digest 교체는 미적용
>     (orders DB=정당한 PII 저장소, hit text 제거로 본문 이미 빠짐 → digest 는 검수 신호만 약화, advisor 판단).
>   실측: 착수 기준선 438 → Phase1 후 tests/ **442 passed / 3 skipped / 실패0**.
>   [Phase 2 = 계산 정확도 — T2.1 구현 완료 2026-07-03, 커밋 `0e90048`] 자시 정책(JST_2300) 일주 반영.
>     calc/myeongni.py·partner.py 에 `if ct.day_offset: ec.setSect(1)`(일주만 익일, 시/월/연주·대운 보존).
>     engine·ziwei·docs 무수정(iztro 이미 익일 → 명리 익일 후 자연 일치). 신규 앵커 test_zasi_policy 6건
>     (정책분기·일주익일·consistent회복·대운누수0·비자시불변) + 기존 골든 22건 바이트 동일. tests/ **448 passed**.
>     [영향 구간] 진태양시 23:00~24:00(시민시각 대략 23:32~24:00) 출생 = 일간부터 결과 변경 →
>     기존 발송물 재검토는 운영자 판단(보고만). [YAJASI 잔여] YAJASI_SPLIT 자시(day_offset=0)는 명리 당일 vs
>     자미 익일 불일치 가능 — 실운영 JST_2300 확정이라 우선순위 낮음, T2.x 후보(roadmap 기록).
>   [Phase 2 T2.2 완료 2026-07-03, 커밋 `b5ca872`] 절입 ±2분 관리자 확인 플래그(G-2, 절대규칙7 후단).
>     solarterms.minutes_to_nearest_jie(출생 UTC vs 최근접 12節 차) → engine CrossCheck.near_term_boundary →
>     pipeline GenResult → order_flow CalendarVerification 충전 + needs_review OR. insight 자동 반영.
>     solar_term_time 에 lru_cache(순수함수·결정론) → 전체 스위트 ~410s→138s 단축(부수 개선). 골든 22건 불변.
>     테스트 test_near_term_boundary 6건. tests/ **457 passed**.
>   [Phase 2 T2.3 완료 2026-07-03, 커밋 `a2e65dc`] KASI 3원 교차 런타임 편입(G-1, 절대규칙7 전단).
>     kasi.year_kasi_check(year)[lru_cache] → engine CrossCheck.kasi_consistent/kasi_out_of_range →
>     pipeline calc_consistent 편입 + reasons. 범위 내 미지 불일치=차단, 범위밖/무캐시=폴백(차단 아님),
>     기지결함=비차단. 안전 실측: 범위 내 전 정상연도 all_kasi_ok=True → 오차단 0. 골든 22건 불변.
>     테스트 test_kasi_runtime 5건(무캐시 CI skipif). tests/ **462 passed**.
>   [Phase 2 T2.4 F-1 완료 2026-07-03, 커밋 `228e0c4`] iztro-py 0.3.4→0.3.5 업그레이드(大限/童限 궁배정
>     버그 수정). pyproject 핀 >=0.3.5. ziwei.build horoscope except pass → logging.warning(조용한 오류
>     삼킴 제거). parity 100건 구조 불일치 0 유지 + decadal 골든 앵커 2건. tests/ **464 passed**.
>     [주의] 0.3.5 설치는 .venv(gitignore) — 새 환경/CI 는 `pip install -e .` 또는 iztro-py>=0.3.5 재설치 필요.
>   [Phase 2 T2.4 F-2 완료 2026-07-03, 커밋 `f800dd3`] 연주 입춘 경계 lunar↔Skyfield 교차. myeongni 에
>     연간지 교차(출생 utc 가 입춘 315° 이후면 명리연도=year, 전이면 year-1 → 60갑자 연지 vs lunar) 추가,
>     engine CrossCheck.year_branch_ok + pipeline calc_consistent 편입(월지와 대칭 차단). 실측 정상·경계
>     전 케이스 일치 → 오차단 0. 테스트 test_year_boundary 3건(2000-02-04 卯/02-05 辰). tests/ **467 passed**.
>     → **T2.4 전체(F-1 iztro0.3.5 + F-2 연주경계) 완료.**
>   [Phase 2 T2.5 완료 2026-07-03, 커밋 `a3cc820`] 시진불명 자미 생성 금지(G-3, 절대규칙8). 실측으로
>     unknown_time 에도 자미 섹션 렌더 확인(부록C 미검증 해소) → builder 가 unknown_time 시 자미 전용 섹션
>     (ziwei·together) 드롭 = 명리 단독 강등. test_p8 자미 부재 단언 추가. tests/ 467 passed.
>     (engine ziwei 계산 억제는 낭비절감 백로그 — 섹션 드롭으로 규칙8 문안 이행은 완료.)
>   ★★ **Phase 2(계산 정확도) 전체 완료**: T2.1 자시정책·T2.2 절입플래그·T2.3 KASI3원·T2.4 iztro0.3.5+연주경계·
>     T2.5 시진불명자미금지. 골든 22건·parity 100건 불변, 오차단 0.
>   [Phase 3 착수 — T3.1 A-4 완료 2026-07-03, 커밋 `c494a0e`] 저밀도 게이트 두 자리 장 인식 복원.
>     verify.py _CHAPTER_RX·_CHAPTER_HEAD_RX 정규식 `\d+`→`\d(?:\s*\d)*`(제10장~ "제 1 0 장" 공백 추출
>     대응). 두자리 장 매칭 회귀 테스트. tests/ **468 passed**.
>   [Phase 3 T3.1 완료 2026-07-03 — A-4 `c494a0e` + A-2 `84a1f47`] 저밀도 장꼬리 사각 축소.
>     A-4=정규식 두자리 장(`\d(?:\s*\d)*`), A-2=장꼬리 면제에 글자수 하한 _CHAPTER_TAIL_MIN=90(다음이 새
>     장이어도 꼬리<90자면 흘러넘침 결함으로 hit). 3중 사각(41~119)을 41~89 로 축소, 표 테스트 증명.
>     DOC_A 재검증: 이번 재렌더 <120 장꼬리=118자(>=90 정상 면제). tests/ **469 passed**.
>     [백로그·근본보완] (1) 짧은 스필(50~67자) 자체를 조판으로 방지 = integrated _LAYOUT_VARIANTS 재시도에
>     '짧은 꼬리 시 행간 미세조정 변형'(하한 13.8pt 불변, 열화 발급 금지) — 로드맵 T3.1 근본보완 미구현.
>     (2) 같은 content.json 무료 재렌더가 페이지 분할 흔들림(55↔51p 관찰) = Playwright 렌더 비결정 → 조판
>     안정성 조사 후속(장꼬리 스필 재발과 연관).
>   [Phase 3 T3.2 부분 완료 2026-07-03, 커밋 `bd69f0f`] 기하 게이트 세로 넘침 검사 + skip 표기.
>     verify.py: _PAGE_TB_MARGIN_MM=22, _layout_geometry_hits 세로 넘침(vertical_overflow) 추가,
>     layout_geometry_skipped 표기. 세로넘침 양방 테스트. tests/ **471 passed**.
>   [Phase 3 T3.2 잔여 완료 2026-07-03, 커밋 `7e93c24`] 인셋 상실 검출 + 실렌더 회귀(B-2).
>     - **사각**: 본문 .body max-width(인셋) 상실 시 콘텐츠박스를 대칭 채움(20/20) → margin_asymmetry 는
>       좌우 대칭이라 구조상 못 잡고 content_overflow 는 콘텐츠박스 안이라 통과(advisor 규명: 로드맵 원안의
>       '좌쏠림 주입'은 이미 asymmetry 가 잡아 (2) 증명 불가 — 주입 결함은 '대칭 넓힘'이어야 함).
>     - **단일 소스**: render/layout.py 신설(PAGE_MARGIN_MM·BODY_MAXW_MM). pdf.py·verify 공용, 템플릿
>       --maxw 를 body_maxw_mm 주입(page_margin_css 선례)으로 전환. 148mm 불변(렌더 무변, 순수상수라 verify
>       임포트에 Playwright 미유입).
>     - **body_inset_lost**: 칼럼폭(x1-x0) > BODY_MAXW_MM(148)+10mm(인셋 상실≈170mm)이면 hit. content_overflow
>       (20mm 콘텐츠박스)는 불변 — 새 kind 추가만(완화 0). 좌쏠림은 여전히 margin_asymmetry(폭≈148)로 분리.
>     - **실렌더 회귀**(실 PDF 기하 테스트 최초): max-width 무효화 주입 렌더→body_inset_lost→gate_pass=False /
>       정상→인셋 결함 0. 단일 소스 상수 monkeypatch 로 결함 주입.
>     측정: 합성 실렌더 전 본문 페이지 블록 좌단 31.2mm(=기대 30.9mm) 군집, 차트/표도 .body 내부(near20=0)
>       → 절대/폭 검사 false-fail 0 실증(min(b[0]) 격리 불필요 확인, advisor 지적 해소).
>     양방 회귀: layout 단위 3건 + 실렌더 1건. tests/ **483 passed**(479+4).
>     veraPDF 비악화 = 신규 템플릿 렌더 실측 failed_clauses=['7.1-3'](베이스라인, 테스트는 veraPDF 모의라
>     별도 실측). [불변식] col_width 프록시는 '모든 본문요소 .body 안'(near20=0) 전제 — 풀블리드 이동 시 재검토(주석 명시).
>     → **T3.2 전체(세로넘침+인셋상실+단일소스+실렌더회귀) 완료.**
>   [Phase 3 T3.4 완료 2026-07-03, 커밋 `125414e`] tagged 게이트 항진 해소 — tagged=StructTreeRoot AND
>     MarkInfo(기존 OR 은 harden 이 MarkInfo 항상 삽입해 항진). 정상 Chromium PDF 둘 다 보유(실측 3건).
>     StructTree 유실→FAIL / 정상→PASS 양방 테스트. tests/ **472 passed**. (컨텍스트 극한으로 실렌더 불필요한
>     T3.4 를 먼저 처리 — 순서 조정.)
>   [Phase 3 T3.3 완료 2026-07-03, 커밋 `c4cfeb5`] 최종 발급 게이트 완전화(B-1+G-5).
>     - order_flow.final_render_fn 이 verify 에 이름·일간 스펙 미전달로 name_policy/identity_role 게이트가
>       최종 발급에서 no-op 였다. gen_params 로 saju 재계산(engine.build) → personal_identity_spec →
>       draft(pipeline.generate)와 동일 인자(ref_year/ref_date/names/identity)로 verify 호출.
>       **재계산 무드리프트 근거**: create_order 가 정규화 양력 y/m/d 를 gen_params 에 영속 + engine.build
>       결정론 → 재계산 day_master 는 본문 빌드 시점과 바이트 동일(스펙/본문 드리프트 불가).
>     - **[스펙 정정 — 2차 실측이 1차 정정을 뒤집음]** T3.3 당시 'role_perspective/honorific=아무도 안
>       넘기는 죽은 파라미터, singang=궁합 전용' 기록은 **오류**였다(grep 이 gunghap+order_flow 만 봐
>       integrated.py 누락). T3.5 B-8 착수 시 전수 grep 으로 정정: **integrated.py(integrated_full 상품)가
>       role_perspective·honorific·singang 셋 다 verify 로 전달**(라인 359·364-365, role_perspective_specs
>       파생), gunghap 은 singang(1209) + 호칭 텍스트정규화. 즉 셋 다 다인 상품의 **활성 게이트**(죽은 필드
>       아님). 개인 경로 None 은 여전히 정답(단일 호명·관계역할·다인 신강 비교 없음). 개인 실공백=identity+names
>       2종(결론 불변). **T3.3 코드 정상 — 문서만 정정**(advisor 판정: 롤백·재검증 불요).
>     - **[deviation]** safe_lint·factcheck 재검증 벨트를 verify() 내부가 아니라 final_render_fn 에서 r23
>       섹션(edit_section 과 동일 함수·allow_tokens)에 실행 — verify 는 PDF 추출텍스트(한자정리 등으로 원문과
>       상이) 기반이라 섹션 final_text 재검증이 드리프트 0. 위반 시 카운트만(match 본문 미노출, T1.3/PII) → 발급 차단.
>     - admin approve: needs_review 주문은 confirm 없이 409(원클릭 승인 물리 차단), 정상 주문 오탐 0.
>     - **[E-3 확인]** issue_final_pdf 는 render_fn 반환 시에만 DELIVERED 전이, final_render_fn 은 벨트·게이트
>       실패 시 예외 → DELIVERED 는 이미 verify 통과 요구. 중복 store 게이트 미신설(advisor 판정).
>     - **[의도적 픽스처 변경]** test_delivery_quality 최종렌더 테스트 gen_params 에 생년월일 파라미터 추가
>       (실주문은 create_order 가 항상 채움) + engine.build 스텁.
>     측정: 클린 개인 빌드 3종(integrated/myeongni/ziwei) 전 섹션 safe/fact 위반 0(벨트 false-fail 0).
>     양방 회귀: test_final_render_gate 5건(벨트 safe/fact 차단·PII-free·verify 실패 차단·스펙 복원) +
>     test_admin_ui approve confirm 409/200 2건. tests/ **479 passed / 3 skipped**(472+7, 회귀 0).
>   [Phase 3 T3.5 B-8 완료 2026-07-03] 죽은 필드 결정 소진(advisor 판정): contains_known_ganzhi 제거
>     (verify.py:428 P4 고정샘플 己卯/戊午 센티넬 — gate_pass 미편입 보고필드라 일반 리포트엔 무의미·오해
>     소지. 게이트 아니라 제거=완화 아님). scripts/ 외부노출 0 확인. P4 종단 스모크는 test_p4 인라인화
>     (추출텍스트에 계산 간지 존재 단언). 일반 '기대 간지 렌더' 게이트는 verify 에 계산 간지 전달 필요=신규
>     스코프 → T4.1(factcheck 간지) 후보 이월. role_perspective/honorific/singang 은 **활성 게이트라 유지**
>     (T3.3 스펙 정정 참조). order_flow.py 주석·STATE T3.3 노트 정정 동반.
>   [Phase 3 T3.5 (b)/B-5 완료 2026-07-03, 커밋 `86e5105`] 목차 판정 이중기준 단일화.
>     verify 세 스캐너(_customer_body_page_items·_low_density·_orphan)가 목차를 제각기 판정하던 것을
>     _is_toc_page('목차' 단어 + <400자, _TOC_MAX_CHARS) 헬퍼로 일원화. _low_density(<120)·_orphan(<40)은
>     이미 그보다 짧을 때만 도달 → 상한 400 적용 동작 불변(순수 단일소스화, 완화 0). _ORPHAN_SKIP 에서
>     '목차' 제거(헬퍼로 이동). 회귀 단일기준 4 + 세 스캐너 일관성 2. tests/ **485 passed**(483+2).
>   [Phase 3 T3.5 (a) 완료 2026-07-03, 커밋 `0fc9e03`] 목차 재넘침 방어 — 2단 목차(운영자 결정).
>     실측: 단일 열 목차 14행/페이지 → 15장부터 2페이지 넘침(넘침 목차 페이지가 본문 오분류돼 기하/저밀도
>     오탐). pdf.py: 목차 행수>_TOC_SINGLE_COL_MAX(14) 시 toc_two_col 주입. report.html.j2: .toc-list 래퍼
>     + .toc-2col(column-count:2·break-inside:avoid·좁은 열 제목 줄바꿈 방지로 장번호/대시/간격 축소).
>     verify _TOC_MAX_CHARS 400→520(2단 목차 1페이지 ~330~400자 수용). ≤14장 단일 열 유지(동작 보존).
>     실측 장 20/22/24 전부 목차 1페이지·is_toc·기하·저밀도 clean, veraPDF ['7.1-3'] 비악화(실측).
>     회귀: 22장 실렌더 1페이지 1 + 임계경계(14/15) 1. tests/ **487 passed**.
>     [발동 범위 실측·advisor] 표준 개인 리포트는 단일 열 유지: integrated=14행(임계=), myeongni=12, ziwei=9
>       → 전부 two_col=False(동작 불변, test_p4=integrated 14행=단일열 검증). **2단은 다인 integrated_full/
>       궁합(17~24장, 실제 넘침 케이스)에서만 발동** — 정확히 넘치던 상품만 고침. [주의] integrated=정확히 14
>       (임계선) — 향후 섹션 +1 시 2단 전환됨. 2단 자체 검증=합성 22장 테스트(로드맵 요구 케이스).
>     [참고] 운영자 시각 승인: 합성 샘플 sajugen/render/out/diagN22.pdf(2단 목차) 열람 가능(발송 아님).
>   ★★ **Phase 3(게이트 실효성) 전체 완료**: T3.1 저밀도 장꼬리·T3.2 기하(세로넘침+인셋상실+단일소스+실렌더)·
>     T3.3 최종발급게이트·T3.4 tagged항진·T3.5 목차2단+판정단일화+B-8죽은필드. 다음 = Phase 4.
>   [Phase 2 T2.1 측정 기록(참고)] 자시 정책 fork 를
>     실측 확정(calc 편집은 컨텍스트 안전 위해 새 세션으로 핸드오프 — advisor 판정). 측정 2건:
>     (1) lunar-python setSect(1)=일주만 익일·시/월/연주 보존(23:18 → 甲午→乙未, 시주 丙子 불변).
>     (2) **fork: iztro chinese_date 는 이미 익일(乙未)** — 로드맵 원안의 'iztro 당일 고정 + engine
>     비교자 정정'은 틀린 전제. 현재 명리(sect2 버그 당일 甲午)↔자미(익일 乙未) 불일치로 자시 케이스가
>     이미 CALC_MISMATCH 차단 중. **확정 설계**: myeongni.py:145·partner.py:120 에 `if ct.day_offset:
>     ec.setSect(1)` 한 줄(day_offset 이 정책 반영값). **engine·ziwei·docs 무수정**(자미 이미 익일 →
>     명리 익일 되면 자연 일치. day_ganzhi_civil 비교자 추가 금지=새 버그). 자시 골든은 익일로
>     first-principles 재도출(code-match 금지), 비-자시 22건 영향0(day_offset=0). 상세 설계·신규 앵커·
>     YAJASI 잔여 = handoff/audit-followup-roadmap.md T2.1 '측정 확정 설계' 블록.
>   ★ 다음 세션 = Phase 2 T2.1 구현 (roadmap '측정 확정 설계'대로 setSect one-liner + 자시 골든 재도출
>     + 불변식 앵커, 골든 22건+신규 앵커 전수 GREEN). 이어서 T2.2~T2.5. calc 수정=골든 회귀 동반 필수.
>   [이전 완료] customer2 통합 PDF triage 품질게이트 P1~P5+belt(8012a20), 목차 1페이지화(95c9019),
>     장마다 새 페이지+장꼬리 게이트(d0aa483). 아래는 그 상세 기록.
>
>   customer2 통합 PDF(integrated_full) triage 후속 품질 게이트 보강 P1~P5 + relationship belt = 완료·커밋.
>   커밋: `8012a20` feat(sajugen): 납품 문안 품질 게이트 보강 (브랜치 codex/gunghap-relationship-quality, push 안 함).
>   - P1 concern 배선(situation→concern 정규화·context_required·missing_customer_context)
>   - P2 customer_meta_lint.transition_section_preview(문서 진행/섹션 예고 차단, 생활흐름 오탐 0)
>   - P3 compose 가드(builder/gunghap에 customer_meta_lint 부착)+프롬프트 belt(_COMPOSE_SYSTEM/_GH_SYSTEM)
>   - P4 목차 리드 중립화("…다음 순서로 이어집니다"→"차례")
>   - P5 물리 frontload 보조지표(physical_frontloaded_answer, warning 전용·게이트 불변)+검수 체크리스트
>   - relationship belt(context.SYSTEM), 표지 semantic-clean(render/pdf), 보장형 compose 가드(guarantee_lint)
>   [2026-07-02 PDF 레이아웃 근본수정 = 커밋 `b2143e5`] 육안 "레이아웃 다 틀어짐" 근본원인 2겹 규명·수정:
>   - (즉시결함) 본문 칼럼 좌우 비대칭(좌20/우42mm) = report.html.j2 `.body{margin:0}` 미중앙정렬 →
>     `margin:0 auto`(좌우 ≈31mm 대칭). 실측 20/42 → 31.2/31.6.
>   - (시스템원인) verify가 텍스트/카운트만 검사·기하 검증 0 → 시각결함이 gate_pass=true로 반복통과.
>     verify.py `_layout_geometry_hits`(블록 bbox 좌우여백·넘침) 신설·gate_pass 편입(기존게이트 완화 0).
>   - (비용 근본차단) integrated.py compose결과 `.content.json`(gitignored) 영속 + render-only 재렌더
>     (`render_integrated_from_content`/CLI `render`, `_render_integrated` 추출) → 레이아웃/템플릿 변경 시
>     재compose(API 과금) 없이 재렌더. 실 라운드트립(build→저장→재렌더) 재compose 0 실증.
>   실측: `pytest tests/ -q` = 436 passed / 3 skipped / exit 0. 구템플릿 customer2 PDF는 새 게이트가
>     margin_asymmetry 49건으로 차단. BEFORE/AFTER 시각자료(tmp/layout_BEFORE·AFTER.png, 합성·PII0).
>   [2026-07-02 seed·하네스 fix·저밀도 이슈] 세션 커밋(전부 push됨, HEAD=origin=`e55cca5`):
>     8012a20(P1~P5)·6bb18db·b7a946d(docs)·b2143e5(layout)·cbe75fe(docs STATE/장부)·e55cca5(하네스 fix).
>   - 하네스 fix `e55cca5`: `_regen_pdf` 자식 UTF-8 강제(PYTHONUTF8=1)+stderr 캡처. 서브프로세스 seed 가
>     cp949 크래시/에러 은닉으로 실패하던 것 교정(단, hsummary 가 regen_stderr_tail 필드를 드롭 = 후속 관측 갭).
>   - customer2 교정본 진행: **in-process build(use_llm=True)로 compose 성공·렌더됨·`.content.json` 저장**
>     (`sajugen/render/out/customer2_integrated_full.content.json`, 80KB, gitignored). → 이후 재렌더 **무료**.
>     레이아웃 대칭 확인(좌31.2/우31.5mm)·기하 게이트 clean. **단 gate_pass=False**, 유일 원인 =
>     `delivery_quality → premium_low_density_pages`(page 3, 85자). 원인 = 이번 compose 의 **짧은 관계 섹션들
>     장 표제(제N장)가 한 페이지에 쌓여** 희소 페이지. **폭 문제 아님**(--maxw 162mm $0 재렌더도 동일 page3 실패).
>     나머지 게이트 전부 clean(문안/기하/placeholder/style/honorific/markdown/temporal). warning 만(물리 frontload·단어반복).
>   [주의] verify_result 를 raw 로 출력하면 고객 이름/장표제가 노출됨(이번에 1회 실수) → 반드시 rule/page/count/bool 만 추출.
>   [2026-07-02 저밀도 page3 근본원인 규명·수정 — STATE 가설 정정] 실측(PII-free 진단)으로 page3 진짜 원인 확정:
>     **page3 = 콘텐츠가 아니라 2페이지짜리 목차(TOC)의 넘침 꼬리**(마지막 5줄). 즉 "짧은 관계 섹션 표제
>     쌓임" 가설은 틀렸다(모든 섹션 624~3086자로 건강, 짧은 섹션 없음). 근거: page2·page3 동일 목차 행
>     폰트(13.3pt 장번호 + 15.4pt 장이름), 첫 실제 챕터(10.5pt cnum + 26pt 제목)는 page4 시작. 통합본은
>     장(章)이 17개 → 목차 17행이 2페이지로 넘쳐 마지막 몇 줄만 남는 희소 목차 페이지가 생김.
>     low_density 게이트는 '목차' 단어 든 page2 는 제외하나 넘침 꼬리 page3 는 못 걸러 실패로 잡음(오탐이자
>     동시에 실제 시각 결함=희소 페이지). **수정 = `render/templates/report.html.j2` 목차 CSS 압축**(행 패딩
>     s3→s1, toc-rule 하단여백 s7→s3, toc 상단패딩 14mm→6mm) → 17행이 한 페이지에 → 희소 페이지 소멸.
>     **integrated.py 무수정**(STATE 원래 계획인 `_compact_sparse_sections` 손봄은 오진단이라 폐기).
>     실측: content.json 무료 재렌더 gate_pass=**True**(page2 목차 354자·page3 첫 챕터 455자), 전체 pytest
>     436 passed/3 skipped/실패0, git diff --check clean. 기하 게이트 clean 유지.
>     목차 CSS 수정은 커밋됨(`95c9019` fix: 통합본 목차 1페이지화). 실제 customer2 PDF 도 재렌더 완료(gate_pass True).
>   [2026-07-02 통합본 장(章) 레이아웃 = 새 페이지 — 운영자 선택] 운영자가 최종본 열람 후 '장이 페이지 중간에서
>     시작해 어색'을 지적(제5장 등). 원인 = **통합본만 chapter_breaks=False**(개인 리딩·궁합 리포트·render_pdf
>     기본값은 전부 True). 운영자 결정(AskUserQuestion)='장마다 새 페이지'. 수정 3종:
>     - integrated.py:329 `chapter_breaks=True` (개인·궁합과 일관, 책/프리미엄 표준). 43→55페이지.
>     - 부작용(긴 장 자미두수의 마지막 짧은 조판 꼬리 page=67자)이 저밀도 게이트에 걸림 → verify.py
>       `_starts_new_chapter`(정규식 `^\s*제\s*\d+\s*장`) 신설, `_low_density_pages` 가 '다음 페이지가 새 장인
>       짧은 페이지'만 제외(정상 조판 꼬리). **짧은 장-시작·중간 콘텐츠·맺음 직전 말미밀도는 계속 차단**
>       (회귀 테스트 test_low_density_excludes_chapter_tail / _keeps_short_page_before_colophon).
>     - integrated.py:359 RuntimeError 가 raw verify_result(고객 이름·장표제 PII) 노출하던 것 →
>       `_pii_free_verify_digest`(rule/page/count/bool 만) 로 교체(절대규칙17, advisor 지적).
>     실측: customer2 실 파이프라인 재렌더 gate_pass=**True**·저밀도0·기하clean, 전체 pytest **438 passed**/3 skipped.
>     test_integrated_product.py chapter_breaks 단언 False→True 갱신.
>   미커밋(의도적 제외): sajugen/app.py·order_flow.py·scripts/dump_reading.py = 세션 前 무관 변경 / tmp·render/out = gitignored.
>   ★ 다음 작업: 이 장-레이아웃 수정 커밋(변경 = integrated.py·verify.py·test 2개 + STATE.md). push 는 지시 시만.
>     실제 customer2 PDF 는 이미 chapter_breaks=True 최종본으로 재렌더됨(발송은 운영자 육안검수·APPROVED 후).
>   [핵심] 운영자 지적 "레이아웃 틀어짐" = (a)본문 중앙정렬+기하게이트, (b)목차 1페이지화, (c)장마다 새 페이지 로 해결.
>   [백로그] 장이 ~20개 넘는 초대형 통합본은 목차가 다시 2페이지 될 수 있음 → 그때는 low_density 가 목차
>     넘침 페이지도 제외하도록 게이트 보강 검토(현재는 CSS 압축으로 통상 범위 커버).
>   커밋/push·고객 발송은 운영자 지시 시만. 운영자 전문 검수·APPROVED 전 발송 0.
>
> 컨텍스트가 비워져도 이 파일만 읽으면 그대로 이어갈 수 있다.
> 계획 전문(현행): C:\Users\pc\.claude\plans\role-claude-distributed-hellman.md (상용화 플랜, 2026-06-10 승인)
> 계획 전문(구): C:\Users\pc\.claude\plans\quirky-wibbling-wind.md
> 정책 문서: C:\Users\pc\test-project\docs\00~10 (research ledger·유파 결정·LLM 정책·검수 워크플로우)
> 품질 사고 장부: C:\Users\pc\test-project\docs\16-quality-incident-ledger.md
>   (청마/로타리 맥락 환각, 질문축 누락, 재회 접점, 자산/자식복/위험 시점, PDF 말미 밀도,
>   Playwright sandbox, PS5.1, API 윤문 순서 재발 방지)
> 영속 메모리: ~/.claude/projects/C--Users-pc-test-project/memory/ (MEMORY.md 인덱스)
> 최종 갱신: 2026-06-14  (베타 재정비 Phase A+B 완료. A=브랜드 서담선생 기본+자유입력 / 가정어 제거(세운
>   연도 앵커)+style_lint 가드. B=챕터 간 일주 자기소개 반복 해소: 프롬프트(소유권)+rules ilgan 골격 근원수정
>   +결정론 백스톱 content/repetition.py(소유 챕터 wonguk 외 짧은 자기소개 줄 제거). 베타 v5 실측 일주
>   자기소개 2·3회→1회, 가정어 0. C(저장·재사용, 보존정책 선행)·D(promptfoo) 보류.
>   [신규] sajugen/gunghap.py — 다인(2인+) 사업 궁합 리포트: 결정론 개인 사실(격국·용신 재사용 + 식신생재·
>   재고 신규 탐지) + 쌍별 partner_pillars 관계 + 세운 호기 겹침 → 궁합 전용 compose(3인 허용토큰 factcheck·
>   가정어 가드·반복 백스톱·서담선생) → tagged PDF. 한글 간지 전용(천간지지 한자→한글 변환). CLI
>   `python -m sajugen.gunghap gen --person '이름,YYYY-MM-DD,HH:MM' ...`. 실주문(실명 3건, 익명화됨)
>   gunghap_3in_v3.pdf 13p, 식신생재·재고·포지션·시기 반영. test_gunghap 5건. pytest 167 PASS.
>   재정비 플랜: ~/.claude/plans/subprocess-run-recursive-rivest.md)
> [2026-06-14 PDF 결함 2종 수정 — 플랜 ~/.claude/plans/claude-code-plan-cuddly-petal.md 1·2단계만]
>   실사로 확증한 결함: (1) 개인 PDF 대운 모순(정미 26~35 '현재' vs 병오 '대운 초입' 혼서 — 병오는 그의
>   36~45 대운이자 2026 세운이라 factcheck 토큰검사로 못 막음. 근본=골격이 '현재 대운'을 단일 사실로
>   안 박아 챕터마다 '현재'를 제각기 추론), (2) 궁합 PDF 마크다운/한자 누출(---·**·용신 火 — gunghap
>   경로가 개인 경로의 정제·그라운딩·마스킹을 안 거침).
>   1단계(궁합 경로 통일): content/postprocess.py 신설(strip_artifacts+hanja_clean 단일 소스, builder도
>   이 별칭 사용·legacy 54줄 제거). gunghap _finalize(마크다운 제거+간지 한자→한글+비간지 한자 제거)를
>   LLM출력·폴백 양쪽에 적용, trace.check 그라운딩(섹션 source_keys), masking.mask_concern(situation PII,
>   절대규칙17), is_male 하드코딩 제거→person별 성별(CLI 4번째 필드). render/verify.py 마크다운 게이트
>   (markdown_clean→gate_pass). [버그 자수정] postprocess _CJK_RX 리터럴 豈가 U+8C48로 입력돼 한글
>   삭제→\u 이스케이프(U+F900)로 고정. 실측: 궁합 재생성 마크다운 0·비간지 한자 0·gate_pass.
>   2단계(대운 일관성): calc/myeongni.current_daewoon(ref_year의 단일 현재 대운=start_year<=ref_year 마지막)
>   + rules 대운 섹션에 '현재 대운=정미 하나' 단일 사실 주입·각 대운 (지난/지금/앞으로) 태그 + content/
>   consistency.py(현재로 서술된 간지 추출, 기대값 불일치·2종이상=위반) → builder가 잘못 서술 챕터를 골격
>   폴백 + GuardReport.daewoon_consistent. verify.py 자기완결 게이트(현재 대운 간지 2종↑=빌드실패).
>   llm_sections compose 프롬프트에 '현재 대운은 명시된 하나뿐' 규칙. 실측: 개인 룰경로 현재대운 단일{정미}.
>   신규 테스트 test_postprocess·test_consistency(렌더 PDF 게이트 하드페일·빌더 revert 분기 포함)
>   + test_gunghap/test_p2 확장. 전체 tests/ 182 PASS.
>   주의: 승인 문구는 '재작성→실패 시 빌드 실패'였으나 구현은 (a) 빌더 self-heal(잘못 서술 챕터 골격
>   폴백, 결정론 정답) + (b) 렌더 후 verify 게이트 하드페일(현재대운 2종↑=gate_pass False)의 2중 구조.
>   일상 케이스는 조용히 자가교정되고, 자가교정이 놓친 경우에만 게이트가 빌드를 실패시킨다.
>   알려진 한계(후속): consistency._CUR_AFTER 가 '다음 병오 대운 초입을 준비' 같은 미래 서술도 현재로
>   과탐할 수 있고, 지금/초입 없는 현재 단정('병오 대운은 …')은 놓칠 수 있음 — 문서화된 결함엔 충분.
>   미실행(범위 제외): report_type enum·단품·토정/택일/작명 엔진·order_flow 연결(플랜 3·4단계 참고용))
> [2026-06-15 H1-mini PDF 품질 이슈 6종 검출·수정 — 플랜 claude-code-plan-cuddly-petal.md, calc/ 무수정]
>   육안검수 6이슈(테스트·게이트 미포착분)를 후처리·lint·rules copy·layout로 해결. 신규:
>   content/quality_lint.py(신강↔신약 모순·재무→재수 오타·이름앵커), content/temporal_lint.py(ref_year
>   이하 연도를 '오기 전'으로 쓴 시제오류). 수정: postprocess.hanja_clean에 중복괄호 축약
>   ([가-힣]{1,4}(\1)→\1; '술(술)'·'명궁(명궁)' 해결, '묘(매우 밝음)' 보존); rules 자미 골격 자연화
>   ([핵심 궁]/[그 밖의 궁] 라벨 제거, _palace_para/_palace_brief tag 중복 억제, _stars_full 빈 주성→
>   '주성이 없는 공궁'); builder·gunghap 가드에 quality+temporal lint 연결(위반 시 폴백); render/pdf
>   _split_paragraphs 짧은 마지막 단락(≤14자) 직전 단락 병합(orphan 방지); render/verify에
>   orphan_pages/no_orphan + quality_clean/temporal_clean 필드 + gate_pass 편입(verify(ref_year,names)).
>   신규 테스트 test_quality_lint·test_render_verify + test_postprocess/test_gunghap 확장. 전체 tests/ 193 PASS.
>   룰경로 실측: 개인 PDF 이슈2(자미잔재) 0·이슈3(중복괄호) 0·orphan 0. 이슈1·4·5·6은 LLM 산문 발생분
>   → 단위/모의 검증 완료, LLM 실측 0건 확인은 운영자 승인 후 재생성 대기. 커밋 안 함.)
> [2026-06-19 Phase 1 완료 — Claude Code x Codex 협업 운영 계약 (구현 커밋 504b646, 문서만·calc/ 무수정)]
>   변경: (1) AGENTS.md에 'Codex 운영 계약'(권한 경계) 추가 — 기본 역할=리뷰어·구현권 없음(운영자 사안별
>   승인 필요), Codex 상시 금지(PDF 재생성·LLM 호출·commit·push·deploy), 데이터 접근/인용 경계(.env·실고객
>   데이터·profiles/local 비열람, PII 비인용), 승인 근거 리포트 규정(--no-tests 아닌 hrun 실행본 summary.json
>   pytest.returncode==0). (2) handoff/templates/codex_review.md에 표준 리뷰 체크리스트 추가(권한·재생성·LLM·
>   commit·push·안전·calc/content/render/order 영역별 근거 항목).
>   검증: 전체 pytest 244 passed (358.56s, returncode 0) — 실행본 근거 handoff/reports/h153-baseline/summary.json
>   (--no-tests 아님). 독립 재검증(2026-06-19): 전체 pytest 244 passed (400.89s, exit code 0). Codex 최종 DIFF_VERDICT = APPROVE.
>   안전 확인: PDF 재생성 없음, 애플리케이션 실행 경로 LLM 호출 없음(단 개발 도구인 Claude Code·Codex 사용은
>   이 항목에서 제외), push 없음, deploy 없음.
>   다음 단계: Phase 2A — Claude Plan → Codex Plan Review 자동화 v1.
> [2026-06-27 Phase 1 Scope A 검증 완료]
>   상태: PHASE1_GATE_VERIFIED. clean worktree(test-project-phase1-verify)에서 semantic focused 22 passed,
>   harness focused 2 passed, 7 deselected. FOLLOWUP-A(`scripts/hrun.py` RUN_STATE/retry 배선) 대기,
>   `scripts/hverify_pdf.py` adapter 확장은 NON_BLOCKING_FOLLOWUP 대기. Phase 2는 운영자 명시 승인 전 금지.
>   전체 render/end-to-end 검증은 이번 Scope A에서 미실행.

## 한 줄 상태
사주 PDF 생성기(sajugen) 핵심 빌드 + 디벨롭1·2·3 완료(pytest 34 PASS).
2026-06-10 상용화 플랜(Phase 0~8) 승인: KASI 3원 검증층 + 음력/윤달 입력
+ 자미 유파 정책 + 부분 LLM 4구간(공식 API) + 주문 상태머신 + 검수 UI.
Phase 0(docs)·1(KASI)·2(음력입력)·3(자미 유파/동등성)·4(주문 상태머신) 완료.
P1(2026-06-10): 키 발급·전수 캐싱(음양력 1900~2050 + 절기 2000~2027)·3원 교차·KASI 결함 3건 문서화.
P2(2026-06-11): input/normalize.py 음력→양력(KASI 역조회 1차)·윤달·한·중 상이 경고, CLI/웹폼 --lunar/--leap.
P3(2026-06-11): iztro_py↔iztro JS 100건 동등성 — 구조(배치·사화·명신궁·오행국) 불일치 0, 밝기만 판본차(known-diff).
  config/rule_profile.yaml 유파 외부화(sajugen/config.py 로더), 연경계=正월一일·사화표=iztro기본 확정.
P4(2026-06-11): models/report.py(Unified JSON, docs/04 round-trip) + store/orders.py(상태머신
  RECEIVED→…→DELIVERED·SQLite·audit_log, APPROVED 전 issue_final_pdf 차단=절대규칙16). test_orders 8 PASS.
신살보강(2026-06-11): 만세력 대조(docs/11 케이스#1)에서 발견한 신살 간극을 조사·보강.
  docs/12-shinsal-research.md(권위 출처 교차검증, 간극=정확도 아닌 채택범위·표시구조·기준축 차이,
  엔진 7종 대부분 A등급, 괴강만 고전 4주설과 차이=known-diff). calc/shinsal.py 신설(레지스트리·기둥별·
  공망 자체산술·12신살), 길신 7종 확장(문창·학당·금여·암록·태극·천문·고신·과숙). config myeongni_shinsal
  (괴강범위·삼합축both·12신살축day_zhi·공망표기). content/rules.py 문안 계층(기둥별·상한·공망·12신살 비단정).
  케이스#1 골든: 포스텔러 기둥별 신살 11종 재현·공망 일치. 전체 회귀 79 PASS.
대운수정(2026-06-11): 대운 시작나이 2년차 해결. lunar-python getStartAge()=起運연도 虚岁(케이스마다 +1~2
  드리프트)를 쓰던 버그 → start_age=대운수(getStartYear)+10*순번 으로 도출(calc/myeongni.py). 케이스#1
  6/16/26 레퍼런스 일치·daewoon_count 내부정합. 회귀 2건 추가. 한국관행=대운수=만나이=시작나이.
골든확장(2026-06-11): tests/test_golden_sweep.py 신설(22건). 독립 오라클·속성기반 검증으로 기댓값
  손대조 0 — 공망=lunar LunarUtil.getXunKong(60갑자 전수), 4기둥=iztro↔lunar, 대운방향=양남음녀,
  표=건록·제왕·육합 1차원리 재도출(양인·암록·금여) + 스냅샷, 12신살=독립 재구현. 결정론 격자 21차트 +
  명명 8케이스(순/역·남/여·대운수0·자시·입춘·윤달). 방법론 docs/12 §6. 전체 회귀 103 PASS.
Phase5 착수(2026-06-11): LLM 백엔드 결정 — 내 계정 API 키(상업, 규칙14 만족) 확정, 자체호스팅 로컬은
  제외(하드웨어 필요·의도 아님). 백엔드 2종(rule/anthropic). 1단계 룰폴백 골격 완료:
  content/question_router.py(QuestionCategory enum + 키워드 룰분류) + content/llm_sections.py
  (LLMBackend 프로토콜·RuleBackend·AnthropicBackend·get_backend, 무키→Rule). 기존 llm_polish/builder
  폴백·가드 패턴 재사용(미변경). test_llm_sections 6건. 전체 회귀 109 PASS.
Phase5 2단계(2026-06-11): 고객 고민 입력 배선 완료. cli --concern·웹폼 필드·pipeline·builder 관통.
  builder가 분류(use_llm+키=LLM, 아니면 룰)→카테고리→rules.build_all(concern_category)로 신규 'consult'
  섹션(신청 고민 라우팅, 카테고리→도메인 결, 비단정). 고객 원문은 본문 미주입(주입·PII 회피, 카테고리 enum만).
  Report23.concern_category 저장(감사). SECTION_SPECS +1(consult, source=[input]). test_llm_sections +3.
  전체 회귀 112 PASS. 다음: ANTHROPIC_API_KEY 준비 시 AnthropicBackend 실호출(구간2·3·4 본문 생성)·골든 A/B.
Phase5 3단계 키투입·실호출 스모크(2026-06-11): 운영자 ANTHROPIC_API_KEY 를 .env 에 저장(본인 계정,
  Claude Code 구독과 별개 과금). 코드 수정 0(pipeline 이 .env 자동로드, anthropic SDK가 키 자동인식).
  실측: get_backend()=anthropic, classify('이직')=JOB 실호출 정상. CLI --llm 1990-05-20 통합=게이트 PASS,
  19p·16,620자·tagged. 리포트 1건 윤문 실비용 = 입력45,722·출력18,298토큰 = $0.137(약 192원, Haiku4.5),
  1달러 미만 확정(절대규칙19 측정값). 윤문 23/30 성공·7 폴백. [발견] instructor 도구JSON 래핑이 긴 섹션에서
  max_tokens=1200 초과→IncompleteOutput→재시도후 룰폴백(기능 안전, 비용 약간 낭비)=4단계 보강후보.
  무키 회귀는 키 있어도 실호출 0(test_p3=polish 람다대체, test_llm_sections=delenv 격리).
Phase5 4단계 구간2·3·4 본문생성(2026-06-11): llm_sections 에 compose() 추가(Sonnet 4.6, _COMPOSE_SYSTEM
  +섹션별 _COMPOSE_GUIDE). builder _COMPOSE_SECTIONS={cross,consult,advice,closing} 는 use_llm+anthropic 시
  compose(근거 본문의 사실만, 새 간지·별 생성 금지), 그 외 섹션은 기존 polish. 둘 다 3단 가드 재검증·실패시
  룰 골격 폴백(기존 패턴 그대로). RuleBackend.compose=패스스루(무키 결정론). 고객 원문 미전달(카테고리 enum만,
  절대규칙17·PII). llm_polish max_tokens 1200->2000(긴 섹션 절단 폴백 감소). 실측: 4섹션 전부 생성·가드 통과
  (safe0/fact0), 분량 약 2배(cross225->739·consult252->390·advice480->928·closing259->594), 4구간 비용 99원.
  test_llm_sections +1(compose 패스스루). 전체 리포트(--llm) 실측: 가드 clean·생성20·폴백1(상향효과 7->1)·
  총비용 $0.176=247원(Haiku $0.11 + Sonnet $0.064). 전체 회귀 113 PASS.
풀이재설계(2026-06-12, 커밋 194ec2d): 운영자 "AI가 뽑아낸 것 같다·가독성 최악". 금강산 PDF=하한, 그 이상 목표.
  근본원인=템플릿 우선구조 → 결정론 룰을 '근거 자료'로, LLM이 전 해석 챕터를 사람처럼 작성으로 역전.
  - 한글 간지: _gz_ko '庚午(경오)'→'경오', 지장간·오행(_ELEM_KO)·격국·오행국(_oguk)·일간 한자 제거, 납음 본문 제외.
  - compose 재설계(llm_sections): instructor JSON→순수텍스트(절단·행 회피), _COMPOSE_SYSTEM 강화(한글간지·기호 전면금지·
    메타안내금지·시각자료 언급금지·비유·호명·금강산 이상), 전 해석챕터 가이드, max_tokens 6000, max_retries 8.
  - builder: 해석챕터 병렬 compose(ThreadPool 동시성3, ~수분), consult에 명식 사실 주입(답변거부 버그 해결),
    정적챕터 LLM 미적용, _clean_display 후처리(잔존 한자·줄머리 불릿·원문자·대괄호·화살표·첫째/둘째 산문화;
    '수면·식사' 무간격 가운뎃점 보존; factcheck 이후 적용→그라운딩 유지). "표/그림 보세요" 제거. 판권 후기/CTA 제거.
  - 회귀앵커 테스트(비정적 챕터 한자·기호 0). 무키 폴백도 항상 깨끗. 계산·콘텐츠 93 PASS. calc/ 무수정.
  - 실측(1990-05-20): 본문 한자0·기호0·잘림0. 작성챕터=금강산 이상(비유·호명·한글간지). 비용 ~$0.5~0.9/건.
  [완료 2026-06-12, 커밋 32ef29b] compose 신뢰성 = polished 12/12·fallback 0 달성. 진단 로깅으로 진짜 원인
      규명: 폴백은 API 오류/속도제한이 아니라 §12 가드 실패(LLM이 가끔 '반드시' 단정어 사용)였음 — 내 가설
      (순차/백오프/큐)은 오진. 수정: (1) _COMPOSE_SYSTEM 에 safe_lint 금지어 명시, (2) builder 가드 실패 시
      1회 재작성→재검증→그래도 실패 시 룰 폴백(가드 전수 유지·우회 아님, factcheck 는 한자정리 이전). 실측 폴백0.
  다음 세션: (1) PDF 최종 생성 후 veraPDF/게이트 재측정·운영자 PDF 육안 A/B, (2) 폴백 시 룰 산문 풍부화(보강),
      (3) 검수 UI(store/orders APPROVED) 연결, (4) 다양한 케이스(여성·미성년·자미단독 등) 톤 점검.
  착수 전 필독 메모리: feedback-sajugen-llm-content-pitfalls(반복실수 체크리스트 — '로그로 원인 먼저' 가 이번에 적중).
대개편(2026-06-12, 플랜 quizzical-brewing-hejlsberg 승인·D1~C3 5커밋): 운영자 지시 = 금강산급 디자인 +
  샘플(웹AI 풀이) 수준 직설 말투 필수 하한 + 상대방 사주 포함 + '참고용·전문가와 상의' 류 문구 PDF 금지.
  - D1 폰트·타이포(5078314): 나눔명조 R/B 본문(금강산 동일 패밀리)+나눔브러시 표제(OFL 동반), 한자=
    SourceHanSerifK 스택 폴백. 좌측정렬·행간 1.72·문단 <p> 분할(빈 줄 호흡 보존). 마진 _PAGE_MARGIN 단일
    소스. [중요 발견] Playwright pdf()는 웹폰트 로딩 비대기 → 콜드 캐시에서 본문 글리프 통째 소실
    (13467→606자 실측) → document.fonts.ready 명시 대기로 해결. verify 한글 간지 토큰 인정.
  - D2 한지 배경·표지(0c12011): assets/hanji.svg 절차생성(시드 고정)+make_assets.py 로 낙관('사주명리'
    세로·붉은 이중테두리) 합성 → hanji_bg.jpg. CSS 캔버스 배경은 print 에서 마진·마지막 페이지 미도색
    실측 → PyMuPDF 전 페이지 언더레이(XObject 1회)로 풀블리드. 표지=붓글씨 표제+이름 필수+세로 표제 박스.
    목차=장 칩+대시 리더. 배경 픽셀 회귀앵커(test_p4).
  - C1 가드 완화(44e607d, 운영자 명시 지시=절대규칙12 단서): 단정 부사 단독 허용, 부사+결과동사 결합
    (보장 진술)만 차단. 적중·100%·의료/생사·운명론·보장형은 불변. test_safe_lint 신설(샘플 원문 허용 앵커).
  - C2 말투 재작성(6a1781e): docs/14-tone-spec.md(샘플 익명화+스펙 10항목). _COMPOSE_SYSTEM=단문 호흡
    (한 호흡 줄바꿈+빈 줄)·공감 미러링→핵심 직답→직설 사실→흐름→행동지침→격려·구어체 혼용·헤지 금지.
    rules 일주 동물·빛깔 슬롯(_gz_animal '검은 개'). 실호출 스모크: love 2382자·24문단·가드 0.
  - C3 상대방 사주(db63f88): input/partner.py(생년월일 감지·스팬), calc/partner.py(결정론 — 990118=
    무인 을축 경오 골든, 시미상=시주 제외, 십성=SHI_SHEN·천간합·육합/충·삼합 반합·부족오행 보완),
    rules.partner_block(파생값만, 원본 비전달), masking.py+compose(quoted_concern)=절대규칙17 a~d 구현
    (마스킹 인용블록, consult 한정). factcheck 한글 간지 검사 신설(접미 문맥 필수)+extra_ganzhi.
  - 고지 정비(운영자 지시): '참고용 상담 자료·전문가와 상의' 전면 제거, 감수 명시형(규칙18)은 유지,
    health=의료 비단정+'병원에서 확인' 자연 문구로 대체(test_p3 앵커 갱신).
  - 종합 실측(2026-06-12, 샘플 케이스 1989-01-02 07:40 여+상대 990118 질문): polished 12/12·fallback 0·
    가드 clean, 41p·26,020자·431KB, 게이트 GREEN, veraPDF failed=['7.1-3'] 비악화, 빌드 188s.
    consult=상대 경오일주·술오 삼합(화 살아남)·편인 끌림 설명 재현, 생년월일 비노출. 전체 pytest 125 PASS.
    산출물: sajugen/render/out/final_sample.pdf (운영자 육안 A/B 대기).
  운영자 확인 대기 2건: (1) 표지/낙관 표제 문구(현재 '사주명리'·'종합 사주 풀이' — 상품명 확정 필요),
    (2) 한지 질감 강도(현 SVG 절차생성 — 미달 판정 시 CC0 래스터 교체 경로 준비됨).
  다음 후보: 검수 UI 연결, 다양한 케이스 톤 점검, intro 인사말 1인칭 서명(운영자 브랜드) 추가.
2차 개편(2026-06-12, 운영자 1차 검수 피드백 반영, R1~R7 + 긴급 1건, 8커밋):
  - [긴급·431efbb] "지금은 2025년" 오서술 — m.seun=현재 대운 流年이라 과거 해 시작, ref_year 미전달 시
    골격이 과거 해를 '기준 해'로 폴백. 4중 방어(SajuResult.ref_year 보존→builder 기본값→rules '올해는
    {년}년' 닻+과거 세운 비노출→compose [기준 시점] 블록) + 회귀 앵커. 메모리 9-1 기록.
  - R1(d0d6261) 절대규칙 18 개정(운영자 명시 지시): 본문 산출방식 고지(자동 분석 도구·AI) 금지 —
    colophon='글을 맺으며' 맺음 서명 슬롯으로 재작성, disclaimer 중복 박스 삭제, 역앵커 테스트.
  - R2(7090084) 호명 강제: call_name('김수하'→'수하님' 성 제외·복성 처리), 룰 골격 '당신' 15곳 재작성,
    compose [호칭] 블록, CLI·웹폼 이름 필수화.
  - R3(aa0f4cc) '---' 마크다운 누출 차단(_strip_artifacts 수평선·불릿·인용 확장) + '첫째/먼저' 나열
    잔재 원천 제거(골격 4곳 산문화·치환 폐기) + 프롬프트 금지.
  - R4(cbce5c5) 타이포: 본문 11.5→14.5pt·행간 1.8·잉크 #111 (금강산 실측 15pt/순흑/행송28pt 근거).
    29p로 증가(노동착시 유리).
  - R5(1ecd6e8) 브랜드 가변화: config/brands.yaml 프로필(낙관·표지 표제·맺음 서명) + 낙관을 배경에서
    분리해 PyMuPDF 런타임 드로잉(나눔브러시 fontfile·subset). [돌파구·메모리 기록] PyMuPDF CIDFontType2
    CIDToGIDMap 누락→veraPDF 7.21.3.2-1 신규 실패→/Identity 주입(_fix_cid_to_gid)으로 해결.
  - R6(f21925d) 명리학틱 판식: 사주쌍변 광곽(매 페이지 이중 테두리 11/13mm 먹갈색)·어미(魚尾) 모티프
    (장 시작 인주색 SVG)·표지 정방 낙관(브랜드 2+2자)·--injoo 통일. 계선·능화문 배제(절제).
  - R7 docs/13 §9(바넘 수용 조절변수—Dickson&Kelly 1985)·§10(콜드리딩 구체화—Roe&Roxburgh 2013,
    모호함 차용 배제)·docs/14 11번(강점 선행·사실 토큰 풍부 호명) + 프롬프트 반영. p5 이름 필수화 반영.
  - 종합 실측(1997-10-27 09:46 남 서울, 풀 LLM): 丁丑 庚戌 壬寅 乙巳, polished 12/12·fallback 0·
    가드 clean, 50p·25,463자·560KB, 게이트 GREEN, veraPDF ['7.1-3'] 비악화, 288s.
    금지어 전수 0('당신'·'---'·'자동 분석'·'전문가와 상의'·과거연도 올해 오서술), 호명 '길동님' 확인.
    산출물: sajugen/render/out/final_19971027.pdf (운영자 검수 대기 — 이름은 임시 '홍길동').
  전체 회귀 133 PASS(테스트 14파일). 작업 원칙(메모리 feedback-debug-research-and-record): 오류=공식자료
    조사로 해결, 돌파구=즉시 메모리 기록.
3차 수정(2026-06-12, 운영자 2차 검수 — 낙관 깨짐·말투 하자 원인 보고 포함, F1~F4 + 7커밋):
  [원인 진단] (1) 낙관 깨짐 = PyMuPDF insert_text 텍스트 임베드 자체의 뷰어 호환성 구멍.
    내 검증(MuPDF·PDFium)은 관대한 엔진이라 통과 → 검증 사각. CIDToGIDMap 보정으로도 불충분.
    (2) 말투 하자 = 가드 3단이 사실·안전만 검사, 스타일은 프롬프트 지시뿐 검증 0 → 규칙 누설·
    시적 비유·기호 난발(— 52회·· 49회)·반복(기운 92회)이 통과.
  - F1(1361528) 낙관 이미지화: PyMuPDF 텍스트 임베드 전면 폐기 → make_assets.build_seal
    브랜드별 투명 PNG(Chromium 렌더·캐시) 삽입. 원칙 확립: PDF 텍스트는 Chromium 경로만,
    PyMuPDF는 벡터·이미지만(메모리 기록). 알파 PNG 무압축 저장 실측 → 4x 스케일.
  - F2+F3(5101db5) content/style_lint.py 신설(규칙 누설·em dash·가운뎃점·기호·시적 비유·
    반복 상한) → builder 가드 4번째 검사(재작성→폴백). 프롬프트 재작성(비유=오행 자연물
    하나만·규칙 침묵·반복 금지·줄표 금지), _COMPOSE_GUIDE '결' 어휘 정리(반복 유도 원천).
  - 기호 정규화 선반영(454faea): —·를 가드 전 결정론 변환(폴백 2→0), 구조 상한 12.
  - 기호 잔존 0(915dc5b): intro 제목 줄표·부록 불릿 14줄·합성어 가운뎃점 29곳 제거,
    _hanja_clean 가운뎃점 전부 쉼표화. 회귀 앵커(전 섹션 —·0).
  - 종합 실측(서담선생·민준님·1997-10-27): polished 12/12·fallback 0·clean, 44p·676KB,
    veraPDF ['7.1-3'], 231s. 전수 감사 전 항목 0(줄표/가운뎃점/당신/점수/메타발화/비유어),
    '기운' 92→23·'의 결' 49→2, 호명 103회. 전체 pytest 135+ PASS.
    산출물: sajugen/render/out/final_19971027_seodam.pdf.
4차(2026-06-12, G1~G4 + 오탐 수정 2건):
  - G1 뷰어 진단 종결: MuPDF·PDFium(Edge/Chrome)·pdf.js(Firefox) 3엔진 정상 — 깨짐은 Cursor
    내장 미리보기 한계(고객 영향 없음, 검수는 Edge/Acrobat). pdf.js 검증법 메모리 기록.
  - G2 폰트 업그레이드(c041682): 본문=고운바탕 R/B(OFL), 제목·표제·낙관=본명조 Bold(Adobe OFL).
    마루부리(라이선스 원문 미확보)·KoPub(임베딩 별도 승인) 기각. 송명(OFL)은 동봉만.
  - G3 가족 다중 명식(d775c16): 파서 다중·음력(KASI 변환)·한글 시각(오전/오후)·관계+이름 라벨,
    빌더 전원 주입(상한 4), partner_block 라벨·시주 조건부. 골든: 음1963-10-18→양1963-12-03.
  - 오탐 수정: (1) 반복 상한 길이 비례화(절대값이 4인 consult 정상 밀도 차단),
    (2) factcheck 한글 간지 동형 일상어(계신=癸申 등 7종) 제외 — '들어와 계신 시기' 차단 실사고.
  - G4 비용 계측(usage 토큰 집계)+신순자 생성: 음1972-05-20 09:30 여(양1972-06-30, 壬子 丙午
    壬辰 甲辰)+가족 3인. 최종 실측 polished 12/12·fallback 0·clean, 42p·732KB, 176s,
    Sonnet 12콜 in 56,770/out 22,996 = $0.515/건(약 700원, Haiku 분류 +1원 미만).
    API 외 비용 = 0원(KASI 무료키·폰트 전부 무료 라이선스·Playwright/PyMuPDF(AGPL, 내부도구
    비배포라 무료)/pypdfium2/veraPDF 무료 — 잔여는 전기뿐).
    산출물: sajugen/render/out/final_sinsoonja.pdf (서담선생 브랜드).
Phase6 검수 UI 1차 MVP(2026-06-13, 플랜 sleepy-sleeping-puppy 승인): 운영자 결정 = "완성 우선,
  이후 실주문 돌리며 풀이 디벨롭". 주문 접수→백그라운드 생성→검수→승인→최종 발급 루프를 /admin 으로 완성.
  - 신설: order_flow.py(오케스트레이션 — pipeline 은 store 를 모름, 전이는 전부 여기서.
    create_order=정규화+RECEIVED→NORMALIZED, run_generation=교차불일치 시 CALC_MISMATCH 차단(규칙7)/
    일치 시 CALC_OK→DRAFTED, 게이트실패·가드미클린=DRAFTED+needs_review(검수강화, 우회아님),
    edit_section=IN_REVIEW 한정+가드 재검증(safe_lint+factcheck 허용토큰+빈본문, 위반 시 저장거부),
    final_render_fn=항상 재렌더+verify 게이트(실패 시 예외→APPROVED 에 머묾=규칙16 비우회)),
    admin.py(APIRouter /admin — 목록 필터·상세·review/approve/reject/retry/deliver/섹션수정/PDF 다운로드,
    IllegalTransition·ApprovalRequired→409), web_templates/(admin_list·admin_detail, JS 없음·PRG·
    생성 중 meta refresh 5s. 주의: 최신 Starlette 은 TemplateResponse(request, name, ctx) 신형만).
  - additive 수정: GenResult+report/calc_consistent/input_civil, UnifiedReport+content/render_meta,
    Report23+allow_tokens(builder 가 계산시점 허용토큰 영속 — 검수 수정 재검증용, 상대방 간지 포함),
    factcheck.check_with_allow 추출(기존 check 위임), store busy_timeout=5000+list_orders+add_audit.
    커넥션은 요청마다 새로 열고 닫음(스레드 공유 금지). DB 경로 env SAJUGEN_ORDERS_DB(테스트 격리).
  - 장시간 생성 = FastAPI BackgroundTasks(sync→threadpool, Playwright sync 호환). 기존 POST /generate
    구형 경로 보존(주문 기록 없는 즉시 PDF), 홈에 /admin 링크.
  - tests/test_admin_ui.py 12건(happy path·승인전 발급 409=규칙16 회귀·반려·CALC_MISMATCH 차단·
    수정가드 4종·수정반영 발급 증명·needs_review·목록필터·신규필드 왕복). 전체 회귀 138 PASS.
  - 실경로 E2E(룰 경로 실측): 접수→DRAFTED→금지표현 수정 422→정상 수정 200→승인전 발급 409→
    승인→발급 200→DELIVERED. 최종 PDF 27p·12,655자, 검수 수정문 반영·호명 확인. audit 전체 기록.
  - [해결 2026-06-13] render/verify.py veraPDF subprocess.run에 encoding="utf-8", errors="replace"
    추가. Windows cp949 디코드로 인한 UnicodeDecodeError(리더 스레드) 제거 → veraPDF 측정 안정 복원
    (검증: verify() 반환 verapdf.available=True, 실패 clause는 알려진 7.1-3 1건만=비악화). 게이트
    로직·반환 구조 무변경(측정 영역 한정). 전체 tests/ 150 PASS 유지(회귀 0).
  - [해결 2026-06-13] 테스트 성능·결정성: test_p3::test_llm_fallback_when_polish_hallucinates 가
    ANTHROPIC_API_KEY 미삭제로 build_report(use_llm=True) 시 실제 Anthropic compose 호출(과금·비결정)
    → 137.24s(전체의 40%) 차지. monkeypatch.delenv("ANTHROPIC_API_KEY") 1줄 추가(형제 test_llm_sections
    _no_key 패턴과 통일)로 룰 백엔드 강등. 해당 테스트 137.24s→0.01s, 전체 342.71s→205.54s, 150 PASS
    유지(폴백 의도 보존). 운영 코드 무변경(테스트 전용). 실측 근거 = pytest --durations.
  - [측정·미적용 후보] per-test 실측상 잔여 지렛대: ① engine.build당 ~2.0s 바닥 = solarterms.solar_term_time
    이 (year,황경) 결정론인데 캐시 부재로 빌드마다 36회 재계산 → 모듈 lru_cache 시 스위트·운영 동반 단축
    (calc 레이어=골든 회귀 동반 필수). ② golden_sweep 40s = 21케이스 그리드 최초 빌드(①의 종속, 순서
    아티팩트). ③ KASI 인벤토리 36s = 의도된 전수 스캔(필요시 @pytest.mark.slow 분리). veraPDF/Chromium은
    병목 아님(p5 각 6.4s)으로 실측 확인.
  - [완료 2026-06-13] Phase 8 MVP 릴리스 게이트: ① store/orders.py OrderStore.delete()=하드삭제(PII
    복구불가 파기, 개인정보보호법 제21조)+감사 스텁(audit_log는 PII 비포함 메타만, 행 삭제 후에도 'delete'
    추적 보존), sajugen/delete_order.py Typer CLI(--yes 미지정 시 미리보기만=실수 방지). ② tests/test_p8.py
    E2E 3건(평일 solar / 윤달 2012윤3월1일→2012-04-21 KASI한국·한중상이경고 / 시진불명 unknown_time=추정고지)
    전부 gate_pass·calc_consistent PASS. ③ README-ops.md 운영자 런북. test_orders +2, 전체 153 PASS.
    actor literal 제약으로 삭제 actor='admin' 채택. docs/09 Phase 5·6·8 상태 보정(7은 부분=백로그).
  - [완료 2026-06-13] Phase 9 익명 계산특이점 데이터셋: sajugen/insight.py 신설 — extract_insight()는
    PII 분산(birth·render_meta.gen_params.name/concern·content)을 피해 **안전 필드만 화이트리스트 수집**
    (name·birthplace·concern·order_id·content 미접근). 보존: 입력(분단위)·성별·역법·solar_date·bazi(4주)·
    ziwei유무·경계신호(crosscheck/normalize warnings·needs_review·자시23시·near_term_boundary)·boundary_labels.
    append_insight→data/calc_insights.jsonl(gitignore, 로컬). Typer CLI extract/sweep(기본 경계만·--all 전수).
    delete_order.py --extract-insight=파기 전 추출(extract-then-purge). test_insight 4건(PII 부재 단언 포함).
    법적 근거=제28조의2(가명·연구/통계)·제58조의2(익명 적용제외). 기존 골든 포맷과 동형=익명 골든 후보.
    한계: near_term_boundary는 현 흐름 미충전(기본 False)→절입경계는 crosscheck_warnings로 포착, 충전은 백로그.
  다음 후보: 검수 UI 2차(섹션 재생성·하이라이트·diff), 운영자 확인 2건(표지 표제·한지), 실주문/지인 베타 2~3건,
    성능 ① solar_term_time 캐싱(calc, 골든 회귀 동반), near_term_boundary 충전(절입경계 자동 플래그).
조사대상(미해결): lunar-python sect=2 고정이 JST_2300과 23:00~24:00 출생에서 일주 어긋날 잠재 이슈
  (공망은 자체산술로 회피했으나 일주 자체는 별도 조사).
전체 회귀 79 PASS. 다음 = Phase 5(Question Router + 부분 LLM 4구간, content/question_router.py·llm_sections.py;
  운영자 ANTHROPIC_API_KEY 준비 필요, 무키 시 룰 폴백).
헤드리스(경로1 Max) 폐기 — 런타임 LLM은 Anthropic 공식 API로 확정.

## 목표/스택 (확정)
- 목표: 사주양식 입력 -> 진태양시 보정 -> 명리+자미두수 계산 -> 23섹션 콘텐츠
  +할루시네이션 가드 -> tagged PDF(텍스트레이어/아웃라인) -> 검증 게이트.
  운영자 내부 도구, Python 올인.
- 스택: lunar-python / iztro-py(import명 iztro_py) / Skyfield(절기, de440s.bsp;
  sxtwl 폐기) / KASI(키 확보 시 3원) / Jinja2 + Playwright Chromium tagged
  (Paged.js 대신 네이티브) / veraPDF(포터블 Java 21).
- 문안: 룰 골격 + LLM 윤문(Instructor+pydantic, 사실 슬롯 고정, 사실일치/§12/
  트레이스 린트, 실패 시 룰 원문 폴백; 무키면 자동 폴백 = 비용 0).
- 시간보정: zoneinfo Asia/Seoul(표준시역사·DST 권위) + Skyfield 진태양시
  + 자시정책 enum. 절기 lunar-python<->Skyfield 교차(lunar는 고정 UTF+8).

## 완료 (P0~P5, 전부 [x])
- P0 스파이크: 계산 라이브러리 + Playwright tagged PDF PoC.
- P0.5 도구체인+거버넌스: 도구 설치, ephemeris, .claude/agents 6종 설치 완료
  (opus-4-7=sg-planner/sg-calc-architect/sg-accuracy-verifier/sg-content-guard,
  sonnet-4-6=sg-render-runner/sg-extractor), test-project/.claude/settings.json
  에 SessionStart+PreCompact 훅 설치 완료(STATE.md 자동주입).
- P1 보정: input/time_correction.py, calc/solarterms.py, calc/crosscheck.py.
  test_p1 7/7. 절기 교차 1955~2049 오차 0.02~0.21분.
- P2 계산: calc/myeongni.py, calc/ziwei.py, calc/engine.py(SajuResult).
  test_p2 8/8. 2000-01-01=己卯(절입 연주경계), 명리<->자미 사주팔자 일치.
- P3 콘텐츠: content/ (sections_schema, rules, safe_lint, factcheck, trace,
  llm_polish, builder). test_p3 5/5. 가드/폴백 실증.
- P4 렌더: render/ (charts, templates/report.html.j2, pdf.py, verify.py).
  test_p4 5/5. 샘플 10p·3300+자·tagged·아웃라인23 = 통이미지 결함 해결 입증.
- P5 도구화: pipeline.py, cli.py(Typer), app.py(FastAPI). test_p5 3/3.

## 실행 방법
- CLI: ./.venv/Scripts/python.exe -m sajugen.cli --birth "1990-05-20 14:30" --gender 남 --horoscope 2026-06-01 --out x.pdf
- 웹폼: ./.venv/Scripts/python.exe -m uvicorn sajugen.app:app --host 127.0.0.1 --port 8765
- 테스트: ./.venv/Scripts/python.exe -m pytest tests/test_p1.py tests/test_p2.py tests/test_p3.py tests/test_p4.py tests/test_p5.py tests/test_kasi.py tests/test_normalize.py tests/test_ziwei_parity.py tests/test_orders.py
- 산출 PDF: sajugen/render/out/

## veraPDF / PDF-UA (결정 완료)
- 포터블 Java 21(sajugen/tools/jdk-21.0.11+10-jre) + veraPDF 1.30.1
  (sajugen/tools/verapdf) 설치. render/verify.py 에 연결, 매 PDF 검증/기록.
- 하드게이트(텍스트레이어·폰트·태그) PASS. PDF/UA-1 compliant=False,
  잔여 clause 7.1-3 1건 = Chromium 태그드 구조 한계.
- 결정: 옵션1 현행 유지(veraPDF는 측정·보고만, 빌드 불차단). WeasyPrint/
  GTK·Chromium 후처리 미추진. 추가 코드 변경 없음.

## 터미널 한글 깨짐 (해결됨)
- 진짜 원인(공식 정정): VS Code/Cursor 통합 터미널 GPU xterm.js CJK 렌더
  버그(microsoft/vscode #137047, claude-code #41358) + 폰트 한글 미흡.
  코드페이지 949는 보조였음(이전 "949 1차" 단정은 철회).
- 조치 완료: Cursor settings.json(C:\Users\pc\AppData\Roaming\Cursor\User\
  settings.json)에 gpuAcceleration=off, fontFamily="Consolas, Malgun Gothic",
  fontLigatures=false 추가. ~/.claude/settings.json 에 "tui":"default" 추가.
  사용자 확인: 정상 표시됨.
- 운영 규칙: 답변은 평문 ASCII 위주(이모지/표/특수기호 금지).
  근거 메모리 feedback-terminal-safe-output.

## 알려진 사소 이슈 (기능 영향 없음, 보강 후보)
- iztro soul/body 主星은 원키 노출(soul_star_raw). 한글 매핑 보강 가능.
- 子/午시 命身同宮(신궁=명궁) 정상 동작 — 문구만 "명신동궁"으로 다듬기 여지.
- (정리됨 2026-06-10) ArbiSignal 잔재 삭제: config/·scripts/(capture/collect/recon/
  common 등 8종)·tests/test_parsers.py. .env.example 도 sajugen용으로 정정.
  scripts/ 는 kasi_dump.py·verify_kasi_cache.py 만 남음.

## RESUME HERE - 다음 즉시 작업
>> (완료 2026-06-10) 개발용 모델 라우팅: 전역 model=opusplan + env
   OPUS=claude-fable-5 / SONNET=claude-opus-4-8 + advisorModel=fable
   → 플랜 모드=Fable 5, 실행=Opus 4.8, 중요 결정 시점=Fable 자문.
   sg-* 에이전트: 정확도 4종=claude-opus-4-8 핀, render-runner/extractor=
   claude-sonnet-4-6 핀(서브에이전트 하한선 Sonnet 4.6 — 운영자 확정,
   Haiku는 읽기전용 탐색·분류만). 별칭 주의: opus=Fable, sonnet=Opus 4.8로
   해석되므로 핀은 풀네임 사용. 상세 docs/08. 새 세션부터 적용.
>> (진행 중 2026-06-10) 상용화 플랜 Phase 1 = KASI 검증층.
   [완료] 운영자 키 발급: 활용신청 2건(자동승인) 후 KASI_API_KEY 를 .env 에
   저장(64자 hex, +// 없어 enc/dec 동일). 실호출 활성화 즉시 확인(동기화지연 없음).
   [완료] 가용성 프로브(실측 2026-06-10):
   - 음양력 getLunCalInfo: 월 일괄 조회 가능(solDay 생략 + numOfRows=31 → totalCount=31).
     범위 최소 1900~2050 정상(1900-01-01 → 음력 1899-12 반환, 2051-12-31=0). → 1콜/월.
   - 절기 get24DivisionsInfo: 연 일괄 가능(solMonth 생략 → totalCount=24).
     가용 = 2000~2027 한정(1989~1999=0, 2028+=0 / 정부가 매년 ~2년 앞까지만 갱신).
     응답에 kst(절입 분단위)+locdate 제공. → 절기 3원 교차는 2000~2027만, 그 외 연도는
     lunar↔Skyfield 2원(P1에서 1955~2049 오차 0.02~0.21분 기검증).
   - [주의] 2000-02 dateName 결함 재현: 2/19(우수,17:33) 행이 dateName='입춘' 오기.
     → 캐시 빌더는 dateName 신뢰 금지, locdate/순서로 절기명 도출.
   - 트래픽: 전체 캐시 약 2,000콜(음양력 1812 + 절기 28) → 분할 불필요, 수 분 내 1회 구축
     ('6일 분할' 전제는 월 일괄로 무효화됨). API별 1만건/일 독립 한도.
   [완료] 구현(2026-06-10):
   - scripts/kasi_dump.py: 음양력 월 일괄 + 절기 연 일괄, 재개 가능(기존 월/연 스킵),
     httpx+_type=json, 0.15s 지연. data/kasi_cache.sqlite(.gitignore) 적재.
   - sajugen/calc/kasi.py: 스키마/빌더(lunar·solarterm·meta) + KasiCache 읽기전용 리더
     + crosscheck3_year(2원에 KASI 열 추가, Skyfield↔KASI 허용 2분, 범위밖/무캐시 시 2원 폴백).
     절기 결함 우회: normalize_solarterm_rows 가 dateName 대신 KST→UTC 시각을 Skyfield
     24절기 최근접 매칭해 한자명 부여(2000-02 우수→입춘 오기 정상 흡수, 테스트로 확인).
   - tests/test_kasi.py 8개 PASS + 픽스처 tests/fixtures/kasi_sample.json(실데이터 캡처).
     Skyfield↔KASI 절입차 2000/2026 모두 ≤2분 실측. 전체 회귀 42 PASS(34+8).
   - 교차검증 강도: KASI 일진(2000-01-01)=무오 ↔ 명리 일주 골든 戊午 일치 확인.
   [완료] 전체 캐시 구축 + 전 구간 교차(2026-06-10):
   - data/kasi_cache.sqlite = 음양력 55,152일(1900~2050) + 절기 672행(2000~2027 전 연도 24절기), 3.7MB.
   - 2000~2027 절기 Skyfield↔KASI 전수: 672행 중 3건만 >2분 = KASI 원본오류로 확정·문서화.
     (2011 大寒 1일오타 / 2011 立冬 6h / 2015 夏至 20분) — 두 계산엔진은 ≤0.03분 일치, KASI만 outlier.
     기지결함 목록(KNOWN_KASI_TERM_DEFECTS)으로 코드 고정 + 회귀 테스트(test_full_cache_defect_inventory).
   - 절기 timing 권위=Skyfield(검증 lunar), KASI 절기=3차 참조 → 결함 3건은 사주 계산 영향 0
     (라이브 엔진 월주·세운은 solarterms.py=Skyfield). 불일치 처리 정책 정밀화 = docs/03 §2-1·2-2·4.
   - [전수 무결성 감사] scripts/verify_kasi_cache.py — 음양력 55,152일 전수:
     solJd 연속성 0건 / 일진 60갑자 연속성 0건 / KASI 일진↔lunar-python 100% 일치(0건).
     하드오류 0 = 날짜·간지 무결성 완벽. 한·중 음력 라벨 상이 1,978일/59개년은 오류 아님
     (lunar=중국기준, KASI=한국 권위; 대표 2012 KASI 윤3월 vs 중국 윤4월, 일진 동일).
     카탈로그 data/kasi_kr_cn_divergence.json(Phase 2 자산). 상세 docs/03 §2-3.
   - 테스트 tests/test_kasi.py 12 PASS(일진 표본 무결성·2012 한·중 사례 포함), 전체 회귀 46 PASS(34+12).
   [완료기준 충족] docs/09 Phase1 = "1900~2050 캐시 + 불일치 0 또는 전수 문서화" → 캐시 완비 +
     KASI 결함 3건 전수 문서화. 다음 = Phase 2(음력/윤달 입력 정규화, input/normalize.py).
   계획 전문: ~/.claude/plans/sajugen-phase-1-kasi-crispy-cat.md
   확정 정책(2026-06-10): 자미 윤달 = 15일 분할법, 고지 = 감수 명시형
   ("자동 분석 도구 산출 + 운영자 직접 검수·감수"), 음력 변환 1차 기준
   = KASI(한·중 음력 상이일 존재, lunar-python 은 중국 기준이라 대조용),
   명리 메인·자미 보완(상충 시 명리 우선, '층위 차이' 재서술, 정확도
   주장 전면 금지). 상세 = docs/03(유파 결정표)·docs/06(LLM 정책).
   Phase 목록·완료 기준 = docs/09-roadmap.md.

>> (완료 2026-06-10) Phase 0 = 상용화 플랜 승인 + docs/00~10 11종 작성.
   리서치 5종(KASI API/만세력 라이브러리/자미 라이브러리/Claude Code·
   Codex·MCP 공식문서/명리·자미 통합 학술) 결과를 docs/00 원장에 영속화.
   핵심 발견: (a) KASI 음양력 API 가 세차·월건·일진 간지+윤달 플래그+
   율리우스적일 직접 제공, 특일 API 가 절입시각 분단위(kst) 제공(실호출
   확정 필요). (b) 만세력 외부 라이브러리 "KASI 기반" 주장 3건 중 2건
   허위 → 바로 채택 가능 후보 없음, 기존 lunar-python 1.4.8 고정 유지.
   (c) iztro 가 유파 차이를 config 로 노출(사화표/윤달/연경계/자시),
   iztro-py 는 원본 동등성 검증 조건부. (d) "명리=기세, 자미=영역"
   통설은 학술 근거 없는 실무 관행 → 자미는 12궁 영역 서술 엔진으로
   한정, 시기·길흉 최종 권위는 명리.
>> (완료 2026-05-19) 디벨롭3 = 디자인 정교화 + 말투(상담 화법) 개편(룰만,
   공신력 자료 기반). 플랜: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md
   (F1~F4). 경계 준수: 새 계산 0, LLM 0, 가드 GREEN, veraPDF 7.1-3 비악화.
   - F1 디자인(render/templates/report.html.j2 + pdf.py margin 동기화):
     :root 60-30-10 색 토큰(--bg/--panel/--line/--ink/--mut/--gold/
     --gold-ink), 4px 베이스라인·8pt 스케일(--s1..s7), 본문 행간 1.6·
     제목 1.28, 한글 자간 -0.015em(제목 -0.02em), 모듈러 제목 스케일
     (cover 30pt/chapter 26pt/h2 1.72em/.subhead 1.32em). 섹션 제목을
     박스형 골드채움→편집형(골드 번호 라벨+잉크 제목+하단 헤어라인),
     챕터 마스트헤드 여백 리듬+짧은 골드 룰(crule), 표지 kicker/rule,
     .card 골드 상단 보더, .src 헤어라인 각주화, svg text 자간 0.
     @page 16mm/15mm ↔ pdf.py pg.pdf margin 동기화(tagged/outline 불변).
     WCAG 재검: gold-ink #7d5610≈6.4:1(텍스트), gold #9a6f1e≈4.4:1(룰만).
   - F2 차트(render/charts.py): ohaeng/sipseong 트랙바(흰 트랙+색 채움,
     분포 비교 직관)+굵은 직접 라벨, 라벨색 토큰화(#22262e/#54606e),
     4px 정렬, role=img+title·결정론·객체토큰 불변.
   - F3 말투(content/rules.py, 핵심): 보고서체→2인칭 상담 화법(주어 생략
     자연스러운 곳은 생략, 강조만 '당신/님'). _pick(md5 결정론) 표현
     다양화로 _pillar_line/_pillar_block/_palace_para 문형 반복 제거,
     용어를 라벨나열→서사(간지→특성→제안). 안전 어미·바넘 회피 유지.
   - 독립 톤 검토(general-purpose) 6/10 + #1 결함 지적 → 즉시 수정:
     한국어 조사 자동결합 노출("이(가)/은(는)/을(를)/과(와)")·"결으로"
     비문·"살펴봅니다과(와)" 깨진 변수삽입. 대응: rules.py 에
     _anchor(읽는 마지막 한글음절; 천간/지지/오행 한자 독음 매핑)+
     _jong/_josa/_J/_ro 결정론 조사 헬퍼 추가, 전 플레이스홀더 치환,
     wealth 중복어구·thisyear period_str 명사구화. 재덤프 검증: 두 케이스
     잔여 플레이스홀더 0, 조사 정합("壬(임)을 기준으로","돌파가 살아나는"
     등), _pillar_block 콤마 런온도 비종결 절(-이고/-며/-인데)로 수정.
   - 검증 GREEN: _guard_check 6케이스 clean=True(safe0/fact0/grounding/
     fallback0, health 의료단정0·'의료 전문가' 포함). pytest test_p1..p5
     34 passed(계산 무변경, p2 회귀 무). 재생성 test_1992 통합 18p·추출
     15,595자(원본 3,022 → 약 5.2배), 명리단독 16p·13,164자, 전부
     gate_pass·tagged·fonts_embedded. veraPDF failed_clauses=['7.1-3']
     1건 그대로(악화0). PNG 육안: 표지/챕터/섹션 위계·디바이더·트랙바·
     상담체·조사 정상.
   - 정직 잔여(룰 한계): 통합 ~13.6~13.9k자(추출 ~15.6k)는 경쟁사
     프리미엄(3.9~6.9만)에 여전히 미달. 독립검토 #2(자미 12궁 해석
     문장 단일템플릿 — 별·밝기만 다름)·#3("세 가지 첫째/둘째/셋째"
     골격 love·job·wealth·health 4연속)은 _palace_para 변형 확대로
     일부 완화했으나 잔존. 추가 자연스러움·분량은 다방식 용신·세밀
     격국(정확도 후속) 또는 LLM 윤문(경로1 Max헤드리스, 비용·한도
     결정 보류) 경로. 임시 _f4_*.txt/.json/_tone_case_*.txt/_f4_png/
     _guard_result.txt 는 일회성(deny 규칙상 rm 불가, 무해).

>> (완료 2026-05-19) 디벨롭2 = 각론 서사 분량·깊이 확장(룰만, 이미 계산된
   데이터 소비). 플랜: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md.
   작업목록 #32~#34 완료.
   - rules.py: _pillar_block/_DOMAIN_PALACE 헬퍼 추가. love/job/wealth/
     strength 를 격국·용신·신강약·신살·지장간·지지십성·4주십이운성·납음·
     해당 자미궁(부처/관록/재백/천이)으로 3~5배 심화. thisyear/monthly 에
     세운/월운 간지(_gz_ko, factcheck 이미 allowed) 엮어 대운→세운→월운
     3층 서사.
   - 신설 2섹션: character("성격·기질 종합" — 일간+십성+신강약+신살, ilgan
     중복 회피 자체 디스클레임), health("건강 — 생활 관리의 결(참고)" —
     질액궁+신살+신강약+오행, 의료 단정 절대 금지·"의료 전문가 상의"
     고정). sections_schema 등록, builder._PRODUCT_DROP 에 character 를
     자미단독 제외 추가(health 는 전 상품 유지·질액궁 None graceful).
   - 검증 GREEN: _guard_check 6케이스(성인3·미성년·명리단독·자미단독)
     전부 clean=True(safe0/fact0/grounding/fallback0). pytest test_p1..p5
     34 passed(신규 test_p3 각론/health/상품토글 단언 포함). 재생성
     test_1992 통합 18p·추출 14,846자(원본 3,022 → 약 4.9배), gate_pass,
     fonts_embedded·tagged·시스템폰트 비의존, veraPDF 7.1-3 1건 그대로
     (악화0). 독립 톤 검토(general-purpose): 의료·과장·공포·운명론 없음,
     개인화 실증(케이스별 토큰 차등). 권고 2건 반영 — 체크리스트를
     계산 토큰(십성/격국/신강약)에 연결, 일주 시주 동어반복 제거(패딩↓).
   - 정직 잔여: 통합 ~13~15k자는 경쟁사 프리미엄(3.9~6.9만)에 여전히
     미달. 룰 한계상 그 이상은 반복/바넘 위험. 추가 깊이는 다방식 용신·
     세밀 격국(정확도 후속) 또는 LLM 윤문(비용 경계, 보류) 경로.

>> (완료 2026-05-18) 디벨롭 = 명리 해석 깊이(격국·억부용신·신살·세운/월운).
   플랜: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md. 경계 넘음(새 계산
   추가, LLM 무). 작업목록 #29~#31 완료.
   - 신규 sajugen/calc/advanced.py: geukguk(월령 본기 십성→정격/잡격),
     eokbu(일간 생조 vs 극설 점수→신강/중화/신약 + 억부 참고용신),
     shinsal(전통 표: 천을귀인·도화·역마·화개·양인·괴강·백호),
     seun_worun(lunar-python DaYun.getLiuNian/LiuYue 노출).
   - myeongni.py: Myeongni 에 geukguk/geukguk_note/singang/singang_score/
     yongshin_eokbu/yongshin_axis/yongshin_method/shinsal/seun/worun 추가,
     build(ref_year) 에서 advanced 호출. engine.build 가 horoscope_date→
     ref_year 파싱해 전달.
   - factcheck.allowed_tokens 에 세운·월운 간지 합집합 추가(필수 — 본문
     세운 간지가 위반 안 나게). 신살은 한국어명이라 factcheck 무관.
   - sections_schema 신규 3섹션: geukguk("격국과 용신(참고)"),
     shinsal("신살 풀이(참고)"), seun("세운·월운 흐름") — 27섹션.
   - rules.py: 세 섹션 비단정 문안 + _SHINSAL_MEAN. 용신은 "억부 1방식
     기준 참고, 조후·통관 등은 다를 수 있어 상담 확정 권장" 고정.
   - lunar-python 의 getDayJiShen/XiongSha 는 '일진 택일 신살'(河魁·金匮)
     이라 사주 신살과 다른 체계 → 미사용(왜곡 방지). 전통 사주 신살은
     advanced.py 표로 직접 구현.
   검증 GREEN: pytest test_p1..p5 33 passed(신규 advanced 단언 5 포함, 회귀
   무), 가드 4케이스 clean=True, 최종 PDF 16p·추출 11,851자(원본 3,022 →
   약 3.9배), gate_pass=true, fonts_embedded·tagged, 시스템폰트 비의존,
   veraPDF 7.1-3 1건 그대로(악화0). 독립 정확도 검토(general-purpose)로
   2케이스 손계산 검산 일치 + 학설차 항목은 note/라벨로 단정 회피 확인.
   사후 수정: 괴강 집합 오입력(戊戌→) 발견, 주류 4주설 {庚辰庚戌壬辰壬戌}
   로 정정(advanced.py).
   정직 잔여: 격국 비견/겁재=건록/양인격은 통념 단순화(자평진전 록·인
   별도정의와 차이, note 명시). 도화/역마/화개는 일지 기준(연지설 미반영).
   용신은 억부 1방식만(조후·통관·병약·종격 = 후속). 깊이 더 원하면 다방식
   용신·세밀 격국·신살 학설 옵션화가 다음 후속.

>> (완료 2026-05-18) 전면 종합 개편 P0~P2 (플랜:
   C:\Users\pc\.claude\plans\quirky-wibbling-wind.md, 경계: 룰만·새계산0·LLM무).
   A1~A5·B1~B4·C1~C4 전부 완료(C2 상품토글·C4 이름/생시미상 포함). 검증 GREEN:
   pytest test_p1..p5 28 passed, 가드 4케이스 clean=True(safe0/fact0/grounding/
   fallback0), 최종 PDF 16p·추출 10,680자(원본 3,022 → 3.5배), gate_pass=true,
   fonts_embedded, tagged, 시스템폰트(Malgun/Gulim/SimSun) 비의존,
   veraPDF 7.1-3 1건 그대로(악화0).
   - A1 폰트: sajugen/render/fonts/ = Pretendard(R/SB/B woff2)+
     SourceHanSerifK-Regular.otf(한자, 24.5MB)+OFL 2종(Pretendard-OFL.txt,
     SourceHanSerif-OFL.txt). report.html.j2 @font-face unicode-range 분리
     (한글=Pretendard / 한자=Source Han Serif). pdf.py _FONT_DIR(file:///).
   - A2 교육 부록화: sections_schema "appendix_terms" 추가(24섹션),
     _STATIC_OK 동기화. test_p3 단언을 len(SECTION_SPECS)>=24 로 갱신.
   - A3/A4 콘텐츠 심화+톤: rules.py 의미사전(_SS_MEAN/_ELEM_MEAN/_DISHI_PHASE)
     +헬퍼(_palace_para/_palace_brief/_dishi_phrase/_gz_elem/_age_of), 전 섹션
     근거기반 상담서사, 바넘 회피. final_text 약 9,100자.
   - A5 미성년분기: rules.build_all(saju, ref_year)→is_minor(age<19) 시 love
     섹션 연령적합 치환. pipeline→builder(ref_year)→build_all, pipeline→
     render_pdf(age) 연결.
   - B1/B2 디자인: report.html.j2 디자인토큰·.chapter 마스트헤드, pdf.py
     _CHAPTERS(5챕터) + render_html chapter 필드. 페이지번호는 Chromium
     @page margin-box 미지원+PDF/UA 위해 header/footer 미사용 → 미적용
     (대신 tagged 아웃라인 24개가 접근성 내비. 정직 한계).
   - B3 SVG카드: charts.sipseong_card(5축), daewoon_timeline(current_age
     마커). 템플릿 sipseong_svg hook.
   - B4 심리: closing=개인화 격려 레터(peak-end), advice=If-Then 3개
     (Gollwitzer), next=비강압 CTA('선택'·강요 안 함, NN/g).
   - C1 자미 12궁 전 궁 개별(_PALACE_ROLE_ALL/_PALACE_ORDER). C3 접근성:
     SVG role=img+title 유지, veraPDF 7.1-3 비악화 측정.
   - C2 3단 상품 토글 완료: builder._PRODUCT_DROP, integrated=24 /
     myeongni=21(ziwei_summary·ziwei_palaces·cross 제외) / ziwei=15
     (wonguk·ohaeng·ilgan·sipseong·strength·daewoon·thisyear·monthly·cross
     제외). 전부 guard clean, pipeline gate_pass(myeongni 13p·8,553자 검증).
     v1 한계: 혼합 섹션(summary/love/job/wealth)은 상품별 정제 안 함(보존).
   - C4 이름·생시미상 완료: pipeline/cli/app/builder/rules 에 name·
     unknown_time·product 종단 연결. name → cover/summary/closing 호명.
     unknown_time(날짜만 입력) → 시주 12:00 계산하되 cover·wonguk 에
     '시주 추정' 고지(시주 단정 회피). cli 는 'YYYY-MM-DD' 만 받으면
     자동 unknown_time. 전 케이스 guard clean, pytest 28 passed.
   - 정직한 잔여(계획 외): 분량 ~10,680자(통합)는
     플랜 12~15k 목표·경쟁사 3.9~6.9만자에는 못 미침(룰 경계 한계, 깊이
     완전추월은 후속 계산/LLM 경로 — 사용자 결정으로 보류).
   - 운영 사실: 폰트 unicode-range = Pretendard(U+0000-04FF,AC00-D7A3 등)/
     SourceHanSerif(U+3000-303F,3400-4DBF,4E00-9FFF,F900-FAFF). cp949 콘솔 →
     측정은 UTF-8 파일 덤프 후 Read. 임시 스크립트 _guard_check.py/
     _a1_check.py/_verify_after.py, 렌더 _pdfimg4/ 존재(일회성).

>> (완료 2026-05-18) 고레버리지 콘텐츠/렌더 개선(계산 무추가). 플랜:
   C:\Users\pc\.claude\plans\quirky-wibbling-wind.md. 변경:
   - rules.py: 표시 매핑(_SHISHEN/_GAN/_ZHI/_DISHI/_BRIGHT_KO) + _pillar_line/
     _stars_full 헬퍼 추가, build_all 23섹션 심화(지장간·지지십성·4주 십이운성·
     납음·자미 보좌성/사화/밝기/12궁 = 이미 계산된 미사용 데이터 활용).
   - charts.py: manse_table(만세력 명식표 4x7), ziwei_chart(자미 12궁 4x4 명반)
     신규 2함수. report.html.j2 wonguk/ziwei_summary 에 삽입, pdf.py 변수연결.
   - 레이아웃: @page 15mm14mm, line-height 1.55, _DIVIDERS 8->4챕터, summary
     .card 대시보드(pre-line 4블록). pdf.py pg.pdf margin 15/15/14/14 동기화.
   결과(1992-03-07 재생성): 추출 텍스트 3,022->6,878자(2.3배), 9p, gate_pass
   유지, 가드 clean(safe0/fact0/grounding/fallback0), veraPDF 잔여 7.1-3 1건
   그대로(악화0), 차트 4종 렌더 확인(만세력표/자미명반 정상). pytest
   test_p1..p5 28 passed(회귀 없음, 계산 무변경).
   주의: 추출 6,878자는 플랜의 8,000 목표 미만(과장 금지). 더 늘리려면 thin
   섹션(monthly140/closing174/caution174/thisyear176) 추가 심화 여지.
   후속(범위 밖): 격국·용신·희기신·신살·세운/월운(새 계산, 정확도검증 필요),
   LLM 윤문(--llm 토글, .env 자동로드 완료, 비용 결정으로 보류).

>> (완료 2026-05-18) 실사용 점검 A: 1992-03-07 09:20 여 서울 horoscope 2026-06-01.
   결과: 사주팔자 壬申 癸卯 壬午 甲辰(일간 壬), 진태양시 08:36:48(균시차 -43.2분),
   시지 辰, 오행 水3木2火1土1金1. 대운 역행(여+양년) 1세시작 壬寅→辛丑→庚子→己亥…
   자미 명궁 해/주성 태양(陷)/신궁 재백궁(천량)/金四局/화기 무곡/화과 좌보.
   교차검증 OK(명리=자미 동일, 월지 lunar=Skyfield 모두 卯). 가드 clean(0/0).
   verify: 10p·3021자·text_layer_ok·fonts_embedded·tagged·outline23·gate_pass=true.
   veraPDF compliant=false 잔여 7.1-3 1건(기존 알려진 Chromium 한계, 옵션1대로 보고만).
   부수 수정: cli.py PASS/FAIL 출력 이모지(✅❌) 제거(cp949 콘솔 UnicodeEncodeError
   크래시 원인이었음, 평문으로 교체). 산출물: sajugen/render/out/test_1992.pdf.
   주의: verify.contains_known_ganzhi 는 P4 고정샘플(己卯/戊午) 센티넬일 뿐,
   임의 입력에선 false 가 정상(결함 아님). 보강하려면 verify에 입력 간지 검사 추가 여지.

## 그 외 가능 작업 (사용자 선택 대기)
핵심 빌드 끝남. 다음 중 선택:
 A) 실사용: 실제 고객 생년월일시로 PDF 생성 + 결과 점검/문안 톤 조정.
 B) 콘텐츠 고도화: 23섹션 룰 문안 깊이 보강, 월별운세 상세, 主星 한글 매핑.
 C) 외부배포 대비: 한글폰트 OFL 번들, WeasyPrint pdf/ua 진짜 PASS(여기엔
    Windows GTK 설치 결정 필요), Paged.js 페이지번호 고도화.
 D) LLM 윤문 실연동: ANTHROPIC_API_KEY 설정 시 윤문 품질↑(현재 무키=룰 폴백).
 E) 패키징/문서: README, 운영자 사용설명, 입력검증 강화.
사용자 지시가 없으면 A(실사용 점검)를 추천.
