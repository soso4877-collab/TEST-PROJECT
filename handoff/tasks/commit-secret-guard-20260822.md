# TASK_PACKET — 커밋 비밀정보 가드 실재화 + 문서 정정 (commit-secret-guard-20260822)

- **task_id**: `commit-secret-guard-20260822`
- **owner**: **Codex 구현자** (AGENTS.md 기본 사이클)
- **next_reviewer**: **Claude Code 교차리뷰** (read-only, 구현 세션과 분리)
- **base_commit**: `570dee7` (현재 HEAD, branch `codex/gunghap-relationship-quality`)
- **근거**: 2026-08-21~22 도구 설정 전수조사 + 별도 Codex 적대적 검토(판정 `CHANGES_REQUESTED`)
- **rev**: 1

---

## 1. Goal (관측 가능한 결과 하나)

**저장소 문서가 주장하는 "비밀정보 커밋 차단"이 실제로 존재하고, Claude Code 경로뿐 아니라
터미널·Codex·다른 Git 클라이언트에서도 동일하게 작동한다.**

수용 지표: 합성 비밀값을 스테이징한 커밋이 훅에서 **차단**되고, 평범한 커밋은 **통과**하며,
`CLAUDE.md`·`AGENTS.md`·`docs/18`·`.env.example` 의 서술이 실제 구성과 일치한다.

---

## 2. Background — 실측 (2026-08-21~22)

### 2-1. 문서가 보장하는 방어가 존재하지 않는다

`CLAUDE.md:54` 와 `docs/18-operator-fundamentals.md:56` 은 이렇게 적는다.

> 커밋 훅(`block-env-commit.js`·`pre-commit-security.js`)이 비밀정보 커밋을 **이중 차단**.

실측 결과 **세 겹으로 틀렸다**:

1. **git 훅이 아니다.** `docs/global-claude-settings.snapshot.json:93,103` 을 보면 두 스크립트는
   **Claude Code 훅**으로 등록돼 있었다.
2. **이 프로젝트 것이 아니다.** 경로가 `c:/Users/pc/OneDrive/Desktop/crypto-signal/scripts/hooks/`
   — **다른 프로젝트**의 스크립트다.
3. **현재 배선돼 있지 않다.** 전역 설정의 `PreToolUse` 훅은 `~/.ai-harness/security-guard.mjs` 로
   교체됐다.

### 2-2. 다른 방어층도 없다 (전수 확인)

| 후보 | 결과 |
|---|---|
| `.git/hooks/` | `.sample` 파일만 |
| `core.hooksPath` (local·global·system) | 전부 미설정 |
| `init.templateDir` | 미설정 |
| `.gitattributes` filter | 파일 자체 없음 |
| `.github` (CI) | 디렉터리 없음 |
| `.git` 하위 심볼릭/하드링크 훅 | 없음 |

### 2-3. 실재하는 방어와 그 한계

현재 유효한 층은 셋이고 **전부 Claude Code 실행 경로 한정**이다.

- `~/.ai-harness/security-guard.mjs` (`PreToolUse` 훅) — 민감 경로·개인키·파괴적 명령
- 전역 `settings.json` 의 `deny` / `ask` 규칙
- `.gitignore:23` 의 `.env`

**Codex 나 터미널에서 직접 커밋하면 이 셋 중 무엇도 걸리지 않는다.**

### 2-4. `.gitignore` 가 못 막는 구멍 (이 태스크의 표적)

1. **강제 추가** — `git add -f` 로 무시 목록 파일을 스테이징
2. **추적 파일 본문의 비밀값** — 개인키·API 키를 `.py`·`.md`·픽스처에 붙여넣는 경우.
   `.gitignore` 는 여기 아무 역할을 못 한다.

**2번이 이 태스크의 핵심 표적**이다.

---

## 3. 변경 설계

### 3-1. 훅 위치와 배선

- **신설** `.githooks/pre-commit` — POSIX sh. Git for Windows 가 번들 sh 로 실행한다.
- 저장소에 **추적**되므로 내용이 리뷰·버전관리된다(`.git/hooks/` 는 추적 불가).
- 배선은 1회 로컬 설정: `git config core.hooksPath .githooks`
  → **이 설정 누락을 테스트가 검출**한다(§5-3). 문서에만 적고 끝내지 않는다.

### 3-2. 검사 규칙 — **좁게, 대상만**

> **★ 이번 설계의 핵심 제약.** 2026-08-21~22 작업 중 `security-guard.mjs` 와 `deny` 규칙이
> **명령문에 문자열이 들어 있다는 이유만으로 4회 오탐 차단**했다(`SENSITIVE_PATH` 2회,
> `DESTRUCTIVE_COMMAND` 1회, deny 1회). 전부 실제 위험 동작이 아니라 **텍스트 언급**이었다.
> 이 훅은 같은 실수를 반복하면 안 된다 — **스테이징된 경로와 스테이징된 내용만** 검사하고,
> 커밋 메시지·주석·문서의 언급은 검사 대상이 아니다.

**(가) 스테이징된 경로 검사** — 무시 대상이 강제 추가된 경우
`git diff --cached --name-only` 결과가 다음에 해당하면 차단:
`.env` · `.env.*`(단 `.env.example` 은 **허용**) · `.auth/` 하위 · `*.pem` · `*.key` · `id_rsa*`

**(나) 스테이징된 내용 검사** — 고신뢰 패턴만
`git diff --cached -U0` 의 **추가 라인(`+`)** 에서만:
- PEM 개인키 블록 헤더
- `sk-ant-` 로 시작하는 Anthropic 키 형태

고신뢰 2종으로 시작한다. 엔트로피 추정·범용 "key=" 매칭 같은 **고오탐 규칙은 넣지 않는다**
(방법론 B-8 "어설픈 게이트 회피").

**(다) 우회구** — 훅은 `--no-verify` 로 건너뛸 수 있다. 이건 git 의 성질이며 이 태스크의
범위가 아니다. **문서에 그 한계를 명시**한다(§4 문서 정정에 포함).

### 3-3. 하지 않을 것

- CI 도입, secret scanning 서비스 연동 — 별도 판단
- `security-guard.mjs`·전역 `settings.json` 수정 — **이 태스크는 저장소 밖을 건드리지 않는다**
- `deny` 규칙 완화 — 교차검토가 "원인 확정 전 완화 금지" 로 못박았다
- 기존 `docs/global-claude-settings.snapshot.json` 수정 — **과거 상태의 기록**이므로 보존

---

## 4. 문서 정정 (4곳)

현재 서술을 지우고 **실제 구성**으로 바꾼다. 무엇이 왜 바뀌었는지 알 수 있게 쓴다.

| 파일 | 현재 | 정정 방향 |
|---|---|---|
| `CLAUDE.md:54` | "커밋 훅(2종)이 이중 차단" | `.githooks/pre-commit` 1종 + 배선 명령 + `--no-verify` 한계 |
| `docs/18-operator-fundamentals.md:56` | "2종 훅이 이중 차단 중" | 동일. 과거 2종은 **다른 프로젝트의 Claude 훅**이었다는 사실 병기 |
| `.env.example:2` | "block-env-commit 훅으로 이중 차단" | `.gitignore` + `.githooks/pre-commit` |
| `AGENTS.md:3` | "git hook이 강제한다" (일반 서술) | 실제 강제층 목록으로 교체 |

---

## 5. 수용 기준 — 양방 테스트 (작업 규율 3)

`tests/test_commit_guard.py` 신규.

**(가) 정상 통과** — 평범한 텍스트 파일만 스테이징한 상태에서 훅이 exit 0.

**(나) 결함 차단 3종** — 각각 훅이 **비영(非零) 종료**:
1. 합성 PEM 개인키 블록을 담은 파일을 스테이징
2. `sk-ant-` 형태 합성 문자열을 추적 파일에 추가
3. `.env` 를 강제 추가(`git add -f`)

**(다) 배선 검출** — `core.hooksPath` 가 `.githooks` 를 가리키는지 단언.
`.git` 이 없는 환경에서는 사유를 붙여 skip 한다(다른 환경의 예정된 skip = `EVIDENCE_SPLIT_PASS`).

**(라) 오탐 회귀** — **이 항목을 반드시 넣어라.** 다음이 **통과**해야 한다:
- 커밋 메시지·문서 본문에 `.env`·개인키·삭제 명령을 **언급만** 하는 변경
- `.env.example` 자체를 수정하는 변경
§3-2 의 오탐 4건이 이 테스트의 존재 이유다.

### 테스트 구현 시 주의 (함정 3건)

1. **실제 저장소 인덱스를 오염시키지 마라.** 임시 디렉터리에 `git init` 한 throwaway 저장소를
   만들고 훅을 복사해 검사해라. 현재 작업 트리를 스테이징하는 방식은 금지.
2. **합성 비밀값 리터럴이 스캐너에 걸린다.** 오늘 4회 오탐의 원인이다. 테스트 안에서
   문자열을 **런타임 결합**으로 만들어라(소스에 완성된 형태로 박지 마라).
3. **PII 0.** 실제 키·실제 고객 데이터 절대 금지. 전부 합성.

---

## 6. 파일 경계

**allowed_files**
```
.githooks/pre-commit            (신설)
tests/test_commit_guard.py      (신설)
CLAUDE.md                       (54행 부근만)
AGENTS.md                       (3행 부근만)
docs/18-operator-fundamentals.md (56행 부근만)
.env.example                    (2행만)
implementation-notes.md         (구현 보고)
sajugen/STATE.md                (진행 기록, 마지막에)
```

**forbidden_files** — 위 밖 전부. 특히:
```
sajugen/**  ·  docs/global-claude-settings.snapshot.json  ·  handoff/current/manifest.json
~/.claude/**  ·  ~/.ai-harness/**  ·  .gitignore  ·  data/**  ·  harness/profiles/local/**
```
저장소 밖(홈 디렉터리) 설정은 **읽기도 이 태스크의 일이 아니다.**

---

## 7. 검증 명령

```
./.venv/Scripts/python.exe -m pytest tests/ -q
```
- 통과 기준: **exit 0**, passed 감소 0(기준선 1266 passed / 4 skipped), 신규분만 증가.
- 이 태스크는 `calc/`·`input/` 을 건드리지 않으므로 골든 재도출은 불필요하나,
  **전체 GREEN 은 필수**다.

```
git diff --check
git status --short
./.venv/Scripts/python.exe -m ruff check tests
```

추가 증거 — **훅이 실제로 무는지 손으로 1회 실증**:
throwaway 저장소에서 합성 비밀값 커밋을 시도해 차단되는 출력을 보고서에 첨부해라.

---

## 8. 정지 조건 (BLOCKED_CONTRACT)

- allowed_files 밖 수정이 필요해질 때
- 훅이 Windows Git 환경에서 실행되지 않아 설계 변경이 필요할 때
- 오탐 회귀(§5-라)를 통과시키려면 검사 규칙을 넓혀야 할 때 — **넓히지 말고 정지·보고**
- commit·push·PDF·LLM 호출이 필요해질 때

## 9. 산출물

- `CODEX_IMPLEMENTATION_REPORT` (implementation-notes.md) — 실행 명령 + 출력(passed 수/exit code),
  교정 전 신규 테스트 RED 실증, 훅 실증 출력, 미검증 분리 명시
- `sajugen/STATE.md` 재개 앵커 갱신
- **커밋 금지.** 운영자 checkpoint 대기.

## 10. 리스크 메모

- 이 훅은 **최후 방어선이 아니라 실수 방지선**이다. `--no-verify` 로 우회 가능하고,
  이미 커밋된 이력은 다루지 않는다. 문서에 그렇게 쓰고, 그 이상으로 홍보하지 마라 —
  **없는 보호를 있다고 적은 것이 애초에 이 태스크가 생긴 이유다.**
- 규칙을 넓히고 싶은 유혹이 있을 것이다. 오탐 4건의 기록(§3-2)을 먼저 읽어라.
