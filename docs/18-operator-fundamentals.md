# 18. 운영자 기본기 (사람용 — 에이전트 규율은 .claude/rules/10-methodology.md)

> 작성 2026-07-04. 목적: 1인 운영자가 AI 에이전트(Claude/Codex)와 함께 고객 PII 를 다루는 유료
> 상품을 운영할 때 필요한 기본기를, 권위 출처 기반으로 sajugen 실무에 바로 연결한다.
> 각 절 형식: 원칙 -> 출처 -> "sajugen 에서는 이렇게".

## 1. 대원칙: 코드 건강 우선 + AI 산출물도 사람이 책임 리뷰
- 리뷰/승인의 기준은 "완벽"이 아니라 "코드베이스 건강이 명확히 개선되는가"다. 진행과 품질의 균형.
- AI 가 만든 코드·계산·문서도 최종 책임은 사람(운영자)에게 있다. 무비판 채택 금지.
- 출처: https://google.github.io/eng-practices/review/reviewer/standard.html
- sajugen: 에이전트의 "완료" 보고는 증거(테스트 출력 passed 수 + exit 0 + 커밋 SHA)를 확인하기
  전까지 미완료로 취급한다. 증거가 없으면 "다시 실측해서 보여달라"고 요구한다.

## 2. 코드 리뷰
- 설계 결정은 취향이 아니라 원칙·데이터로 판단. 스타일은 스타일 가이드가 우선(개인 취향 금지).
- 사소한 것으로 무한정 붙잡지 않는다. 갈등 시 사실·원칙으로 합의, 안 되면 결정권자(운영자) 판단.
- 출처: https://google.github.io/eng-practices/review/reviewer/
- sajugen: Codex 리뷰는 AGENTS.md "Codex 운영 계약" 형식(diff + summary.json 근거)으로 받는다.
  리뷰 지적이 "게이트를 완화하자"면 그 자체가 반려 사유다(절대규칙 12).

## 3. 테스트
- 회귀 우선: 버그를 고치기 전에 그 버그를 재현하는 테스트부터 만든다.
- 단언은 좁게(동작만), 구현 세부에 붙는 change-detector 테스트는 유해하다.
- 테스트 피라미드: 단위 다수, 통합 소수, E2E 최소(느리고 깨지기 쉬움).
- 스냅샷/골든은 사람이 diff 를 실제로 검수해야 의미가 있다. 무비판 갱신 금지.
- 출처: https://martinfowler.com/articles/practical-test-pyramid.html ,
  https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html ,
  https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html
- sajugen: 완료 근거는 항상 `./.venv/Scripts/python.exe -m pytest tests/ -q` 전체 실행(기준선
  2026-07-04: 512 passed / 4 skipped). 골든(test_golden_sweep 22건)이 줄거나 바뀌는 diff 는
  반드시 직접 읽고 승인한다. E2E 는 `SAJUGEN_RUN_E2E=1` opt-in(주 1회 권장).

## 4. 사고 대응 (무비난 포스트모템)
- 사람을 탓하지 않고 시스템·정보 격차의 구조적 원인을 찾는다. 관련자 전원이 선의로 행동했다고 가정.
- 일정 기준 이상 사고(고객 노출, 잘못된 계산 발송, PII 유출 근접)는 반드시 기록한다.
- 재발방지 액션 아이템은 담당·기한·상태를 추적한다 — 작성으로 끝나지 않는다.
- 출처: https://sre.google/sre-book/postmortem-culture/
- sajugen: `docs/16-quality-incident-ledger.md` 가 이 모델의 구현체다. 새 사고는 템플릿(§4)으로
  추가하고, "재발 방지" 항목에는 완료 여부를 체크한다(미완이면 다음 세션 지시문에 포함).

## 5. 개인정보 (법적 의무)
- 최소수집: 처리 목적에 필요한 최소한만(개인정보 보호법 제3조·제16조).
- 파기: 보유기간 경과·목적 달성 시 지체 없이 파기(제21조, 표준지침상 통상 5일 이내 권고).
  전자파일은 복구 불가능한 방식으로. 다른 법령상 보존 의무분은 분리보관.
- 출처: https://www.law.go.kr/LSW/lsInfoP.do?lsId=011357 , https://www.pipc.go.kr
- sajugen: 발송 완료 + 환불 분쟁 가능 기간 경과 주문은
  `./.venv/Scripts/python.exe -m sajugen.delete_order <order_id> --yes` 로 하드삭제(파기 전
  `--extract-insight` 로 익명 통계만 보존 가능). `tmp/`·`render/out/` 의 고객 파생 파일(PDF·
  content.json)도 파기 대상에 포함하는 것을 잊지 말 것 — DB 만 지우고 파일을 남기면 파기가 아니다.

## 6. 보안·시크릿
- .env·API 키는 절대 커밋 금지(git 이력에 영구 잔존). 키는 정기 로테이션(분기 1회 권장).
- 최소권한: 키에 필요한 권한만. 입력 검증은 서버(신뢰 가능한) 측에서.
- 출처: https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/ ,
  https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- sajugen: block-env-commit.js·pre-commit-security.js 훅이 이중 차단 중. ANTHROPIC_API_KEY·
  KASI_API_KEY 로테이션 시 .env 만 갱신하면 된다(코드 무수정). /admin 은 무인증이므로 서버는
  반드시 `--host 127.0.0.1` 로만 기동(0.0.0.0 금지).

## 7. 의존성
- 버전은 핀으로 고정하고 lockfile/requirements 를 커밋한다(재현 가능한 설치).
- 업그레이드 3단: 변경로그 확인 -> 전수 테스트 -> 롤백 계획(이전 버전 번호 기록) 후 반영.
- 출처: https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/ (lockfile 원칙, pip 준용)
- sajugen: lunar-python==1.4.8 고정, iztro-py>=0.3.5, fastapi>=0.136 + starlette==1.0.0(이 조합
  깨면 관리자 UI 크래시 이력). 계산 스택(lunar/iztro/skyfield) 업그레이드는 골든 22건 + parity
  100건 전수 재검증 없이는 금지(절대규칙 2). 새 PC/CI 에서는 .venv 재구축 후 pip 핀 확인.

## 8. 백업/복구
- 3-2-1 원칙: 사본 3개(원본 1 + 백업 2), 2가지 다른 매체, 1개는 오프사이트(클라우드 등).
- 백업은 복원 테스트까지 해야 백업이다(NIST CSF PR.DS-11).
- SQLite 는 운영 중 파일 복사 대신 공식 백업 명령을 쓴다.
- 출처: https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf ,
  https://sqlite.org/backup.html
- sajugen 백업 대상 3종 + 명령(주 1회 권장, 발송 많은 주는 발송 직후):
  - 주문 DB: `./.venv/Scripts/python.exe -c "import sqlite3; s=sqlite3.connect('data/orders.sqlite'); d=sqlite3.connect('backup/orders_$(date +%Y%m%d).sqlite'); s.backup(d); d.close(); s.close()"`
  - KASI 캐시: 동일 방식으로 `data/kasi_cache.sqlite` (유실 시 재구축에 API 재호출 필요).
  - compose 저장본: `sajugen/render/out/*.content.json` (유실 시 재생성에 API 과금 ~$1/건).
  - backup/ 폴더는 gitignore + 클라우드(OneDrive 등)로 오프사이트 1부. 분기 1회 복원 테스트
    (백업 파일을 열어 주문 수 count 확인).

## 9. 발송 전 검수 체크리스트
- 체크리스트는 "빼먹으면 치명적인 소수 항목"에 집중하고, 실제 사용 시점(발송 직전)에 확인한다.
- 출처: Gawande, The Checklist Manifesto (http://atulgawande.com/book/the-checklist-manifesto/),
  WHO 수술 안전 체크리스트 사례 (https://pmc.ncbi.nlm.nih.gov/articles/PMC4953332/)
- sajugen 발송 직전 킬러 5항목 (상세는 handoff/templates/pdf_review_report.md):
  1. 이 PDF 가 이 고객 것인가(이름·질문 축 일치 — 다른 고객 파일 오발송이 최악의 사고).
  2. gate_pass=True + 상태 APPROVED 인가(admin 화면 확인).
  3. 첫 장·consult 장·마지막 두 장 육안 확인(밀도·잘림·기호 누출).
  4. 고객 질문 축이 초반에 답변됐는가.
  5. 예측 보장·AI 티 문구가 없는가.

## 10. AI 협업: 자동화 편향 경계
- 자동화 편향: 자동 시스템의 출력을 과신해 독립 검증을 생략하는 인지 편향. 과의존은 사람의
  검증 능력 자체를 퇴화시킨다 — 인간 감독자의 능동적 검증 유지가 통제 항목.
- 출처: NIST AI RMF Generative AI Profile (https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)
- sajugen 습관 3가지:
  1. 에이전트의 "완료·해결·GREEN" 보고는 증거(명령+출력+SHA) 확인 전까지 믿지 않는다.
  2. 고위험 변경(calc/, 게이트, 주문 경로)은 diff 를 직접 읽거나 별도 검증 세션(Codex Verifier)을
     거친다 — 구현한 에이전트의 자기 검증만으로 승인하지 않는다.
  3. 주기적으로(월 1회 권장) "전수 감사" 세션을 돌려 문서-코드 정합을 재검증한다
     (2026-07-03 감사가 P0 2건을 찾은 전례 — 테스트 GREEN 이 정합을 보장하지 않는다).
