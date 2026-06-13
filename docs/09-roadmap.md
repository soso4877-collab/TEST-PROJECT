# 09. Roadmap

> 최초 작성: 2026-06-10. 원칙: 한 Phase = 한 작업 단위 순차 진행. Phase 완료 시 STATE.md 갱신 + pytest 전체 GREEN.
> 플랜 전문: C:\Users\pc\.claude\plans\role-claude-distributed-hellman.md §13

| Phase | 내용 | 핵심 파일 | 완료 기준 | 상태 |
|---|---|---|---|---|
| 0 | docs 11종 + 정책 고정(윤달 15일분할, 감수 명시형 고지) | docs/00~10 | 정책 명문화 | 완료 2026-06-10 |
| 1 | KASI 검증층: 키 발급(운영자)→실호출 확정→전수 캐싱→3원 교차 | scripts/kasi_dump.py, calc/kasi.py, tests/test_kasi.py | 1900~2050 캐시+불일치 0 또는 전수 문서화 | 완료 2026-06-10 (캐시 55,152일+672절기, KASI결함 3건 문서화, 44 PASS) |
| 2 | 음력/윤달 입력+정규화 (KASI 1차 기준) | input/normalize.py, cli/app 확장 | 음력 E2E PASS+한·중 상이일 목록 | 완료 2026-06-11 (음력→양력 KASI역조회·윤달·한·중상이 경고, CLI/웹폼 --lunar/--leap, test_normalize 7 PASS, E2E 일주 乙酉) |
| 3 | 자미 유파 정책+iztro 동등성 | calc/ziwei.py, config/rule_profile.yaml, tests/test_ziwei_parity.py | 100건 대조 불일치 0 또는 골든셋 | 완료 2026-06-11 (구조 100건 불일치 0, 밝기 known-diff 골든, rule_profile.yaml 유파 외부화, test 4 PASS) |
| 4 | Unified JSON+주문 DB·상태머신 | models/report.py, store/orders.py | 상태 전이 테스트 GREEN | 완료 2026-06-11 (UnifiedReport round-trip, OrderStore 상태머신+SQLite+audit_log, APPROVED 전 발급 차단, test_orders 8 PASS) |
| 5 | Question Router+부분 LLM 4구간 | content/question_router.py, llm_sections.py, prompts/ | 가드 clean+폴백 실증 | 완료 2026-06-11 (compose 4구간·무키 룰폴백·가드 clean, test_llm_sections PASS) |
| 6 | Admin Review UI | sajugen/admin/, content/repetition.py | 주문 1건 풀사이클 리허설 | 완료 2026-06-13 (/admin 접수→검수→승인→발급 루프·실경로 E2E, test_admin_ui 12 PASS) |
| 7 | 안전·반복 필터 보강+테스트 100+ | safe_lint 확장, 골든 자동 케이스 | pytest 100+ GREEN, veraPDF 비악화 | 부분 — 테스트 153 GREEN(100+ 충족)·veraPDF 7.1-3 비악화. safe_lint 추가 확장·골든 자동화는 백로그 |
| 8 | MVP 릴리스 체크리스트 | delete_order.py, README-ops, CLAUDE.md | E2E 3건(평일/윤달/시진불명) PASS | 완료 2026-06-13 (delete_order.py 하드삭제+감사·README-ops·test_p8 E2E 3건 PASS) |

외부 의존(운영자 액션): Phase 1 시작 전 data.go.kr 인증키 발급(음양력 15012679 + 특일 15012690 활용신청, 자동승인·무료), Phase 5 전 ANTHROPIC_API_KEY 준비.
