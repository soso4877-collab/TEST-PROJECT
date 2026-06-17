# H1.5 클라이언트 톤 품질 게이트 체크포인트 (2026-06-17)

> 민감정보 미포함(.env·API key·secrets·PDF 바이너리·cache/log 본문 없음). 작업 연속성용 스냅샷.

## 범위 / 베이스라인
- 브랜치: `feat/sajugen-h1-5-client-tone`(이 커밋들로 H1.5 계열 베이스라인 고정).
- calc/ 무수정. 외부 발송·report_type/order_flow/admin/단품/토정/택일/작명 미접촉.

## 적용된 품질 게이트 (client_tone_lint + verify)
- **H1.5**: 외래어 hard-ban 43어(`loanword_lint`/`normalize_loanwords`), 날것 계산표현(`raw_calc_lint`, 표제형 게이트 — 오행 분포/오행의 분포/십성축/신강약), 구두점 깨짐 정규화(postprocess), 전문용어 밀도 보고(`term_hits`).
- **H1.5.2**: '오행의 분포' 변형 추가, 궁합 목차/장제목 단축(reflow), CSS keep-all/overflow-wrap.
- **H1.5.2-final**: 궁합 timing 폴백 슬롯 자연화(내부 메모형 '호기 해/용신 기준 참고' 제거).
- **H1.5.3**: 궁합 이름 호칭 정책(`name_policy_lint`/`normalize_names` — 본문 전체이름 첫 소개 1회, 이후 '태수 씨'·쌍 '태수와 태성'), 일간 role(`identity_role_lint` — 잘못된 일간/중심 글자 차단, 운·지장간 문맥 허용).
- **H1.5.3.1**: `normalize_names_pdfwide` — _person_slot 다섹션 재사용에도 PDF 전체 'FULL 씨' 첫 소개 1회 보증(render 직전).
- **H1.5.3.2**: `singang_role_lint` — 신강약 group/role. 섞인 신약·신강을 '세 사람 모두 신약/신강'으로 일반화 차단(전체-3인 표지일 때만; 2인 '모두'는 허용), 사람별 신강약 뒤집기 차단('의 사주/명식/힘의 강약/신강약' 프레임 포함).
- verify 게이트(본문 페이지 한정, spec 있을 때만): `name_policy_clean`·`identity_role_clean`·`singang_role_clean` + 기존(loanword/raw_calc_head/markdown/quality/temporal/orphan). spec 미전달 시 back-compat clean.

## 결정론 spec 출처
- 개인: `builder.personal_identity_spec(saju, name)`(일간) — pipeline→verify.
- 궁합: `gunghap._identity_spec`(일간)·`_singang_specs`(신강약) — `p["day_master"]`/`p["singang"]` 결정론값. _compose 가드 + build_gunghap→verify.

## 검증 실측 (H153, LLM 실호출)
- 개인 `final_taesoo_llm_H153.pdf`: 41p, gate_pass=True, 전 게이트 clean, daewoon_current=['정미'], fallback 0.
- 궁합 `gunghap_llm_H153.pdf`: 16p, gate_pass=True, 전 게이트 clean(singang/name/identity 포함), 신강약 group/role 0, 전체이름 반복 0(FULL 씨 사람당 1회), 호칭/쌍 정상, fallback 0. 표지 'A · B · C'는 name_policy_allowed_hits(허용).
- 전체 tests/ 237 passed.

## 다음 (별도 승인)
- 하네스 구축(`chore/sajugen-harness` 브랜치, Plan 우선) — repo 내 JSON/MD 리포트·역할분리·단일 검증 명령·PDF/LLM 승인 게이팅.
- 산출물 PDF·임시 `_*.py/_*.txt`는 .gitignore로 커밋 제외 유지.
