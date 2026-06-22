# sajugen Project Context + Harness Brief for ChatGPT

> 목적: 다른 대화방의 ChatGPT가 (1) 이 프로젝트를 정확히 이해하고, (2) 현재 변경(diff)과 남은 PDF 품질 이슈를 검토하고, (3) 향후 "하네스 엔지니어링" 방향을 판단할 수 있도록 만든 단일 핸드오프 문서.
> 작성: Claude Code, 2026-06-15, **읽기 전용**(코드 수정·커밋·외부 API 호출 없음). 민감정보(.env·키·생년월일·PDF 바이너리) 미포함 — §20 체크리스트 참조.
> 측정값은 측정 시점을 명시. 검증 안 된 것은 "미확인"으로 표기.

---

## 1. 프로젝트 한 줄 요약

**sajugen** = 운영자 1인 내부 도구. 생년월일시·출생지·고민 입력 → 진태양시 보정 → **명리(메인) + 자미두수(보완) 결정론 계산** → 룰 NLG + 부분 LLM 산문(챕터별 근거 슬롯 기반) → 3단+α 가드 → tagged PDF → 관리자 검수 후 수동 발송.

**현재 핵심 상품 유형**
- 개인 종합 사주 PDF (명리+자미) — **가동 중**
- 3인 사업 궁합 PDF (`gunghap.py`) — **가동 중**
- 2인 궁합 — 예정(궁합 경로 N=2로 흡수 가능)
- 월별운세 / 신년운세 / 단품운세 — 예정(기존 결정론 출력 재패키징)

**가장 중요한 품질 기준(우선순위 순)**
1. 계산값 일관성 — 같은 입력=같은 결과, 한 PDF 안에서 명식·대운·세운이 충돌 0
2. LLM 산문 드리프트 차단 — 계산 안 한 사실(간지·별·연도) 생성 금지(factcheck 하드 차단)
3. 마크다운/한자/템플릿 잔재 차단 — 본문에 `---`·`**`·`#`·비간지 한자·`[핵심 궁]` 등 노출 0
4. 고객용 문장 품질 — 오타·모순문장·시제오류·중복괄호 없는 사람 같은 카피
5. PDF 본문 품질 — orphan page·깨진 레이아웃 없음, tagged/폰트임베드 게이트 통과

---

## 2. 기술 스택과 실행 환경

| 항목 | 내용 |
|---|---|
| 언어 | Python (올인). 프런트 프레임워크 없음(React/TS 등 **미사용** — 전역 선호와 무관) |
| 주요 라이브러리 | lunar-python 1.4.8(고정), iztro_py(자미), Skyfield(절기 de440s.bsp), KASI 캐시(음양력·절기 교차), Jinja2, Playwright(Chromium), PyMuPDF(fitz), pydantic, Instructor, Typer, FastAPI |
| PDF 렌더 | Jinja2 HTML → Playwright Chromium `tagged` PDF(텍스트레이어+아웃라인). PyMuPDF로 배경/낙관 합성·검사. veraPDF(포터블 Java21)로 PDF/UA 측정(빌드 불차단) |
| LLM 사용 | Anthropic 공식 API만(웹 UI 자동화 금지). 챕터 단위 compose(근거 슬롯 기반). **계산은 LLM 위임 절대 금지** |
| 테스트 | pytest (22개 파일, 마지막 측정 전체 `tests/` 180 PASS; 신규 2테스트 추가 후 182) |
| OS/셸 | Windows 11 / PowerShell 기본 + Git Bash. 콘솔 cp949 → 한글 깨짐 이력, 측정은 `PYTHONIOENCODING=utf-8` 또는 파일 덤프 후 Read |
| 가상환경 | `./.venv/Scripts/python.exe` (프로젝트 루트 기준) |

**주요 실행 명령**
- 개인 CLI: `./.venv/Scripts/python.exe -m sajugen.cli --birth "YYYY-MM-DD HH:MM" --gender 남 --horoscope 2026-06-01 --out x.pdf [--llm] [--name 이름]`
- 궁합 CLI: `./.venv/Scripts/python.exe -m sajugen.gunghap gen --person '이름,YYYY-MM-DD,HH:MM,성별' --person ... --out g.pdf`
- 웹폼/검수: `./.venv/Scripts/python.exe -m uvicorn sajugen.app:app --port 8765` (`/admin` 검수 UI)
- 테스트: `./.venv/Scripts/python.exe -m pytest tests/ -q`

**LLM 실호출 vs 룰 폴백**
- `ANTHROPIC_API_KEY` 있으면 `use_llm=True` 경로에서 챕터 compose 실호출(개인 1건 ~$0.5, 궁합 ~$0.1).
- 키 없거나 `use_llm=False`면 **룰 골격 그대로**(무비용·결정론). 가드 실패 시에도 룰 폴백.
- 테스트/CI는 키를 제거해 룰 경로로 결정론 검증(과금·비결정 회피).

**Windows 셸 주의**: Bash 도구로 PowerShell/cmd 실행 금지(deny). 파일탐색은 Read/Glob/Grep. CRLF↔LF 정규화 경고는 무해. 긴 명령은 백그라운드 + 모니터.

---

## 3. 현재 git 상태

| 항목 | 결과 | 비고 |
|---|---|---|
| 브랜치 | `feat/sajugen-develop3` | main은 안정 베이스라인 |
| 변경 통계 | `262 insertions(+), 73 deletions(-)`, 10 modified + 4 new | `git diff --stat HEAD` |
| 수정 파일(10) | STATE.md, calc/myeongni.py, content/{builder,llm_sections,rules,sections_schema}.py, gunghap.py, render/verify.py, tests/{test_gunghap,test_p2}.py | 전부 소스/테스트 |
| 신규 파일(4) | content/postprocess.py, content/consistency.py, tests/test_postprocess.py, tests/test_consistency.py | 추적 안 됨(`??`) |
| 삭제 파일 | 0 | |
| PDF/render-out | **git 제외(IGNORED)** | 추적 0건 |
| .env / 키 / secrets | **git 제외(IGNORED)** | `.env.example` 템플릿만 추적(비밀 없음) |
| 캐시(`data/*.sqlite`,`*.jsonl`) | **git 제외** | |
| `sajugen/tools/`(288MB) | **git 제외** | |
| 임시(`_*.txt/json/png`) | **git 제외(`!!`)** | |
| STATE.md | 수정됨 | 1·2단계 작업 내역 24줄 기록. **코드 필수 아님 = 별도 `docs(sajugen):` 커밋 분리 권장** |

→ 이번 변경에 민감/산출물 파일 0. 커밋 대상은 순수 소스/테스트(+선택적 STATE).

---

## 4. 프로젝트 디렉터리 지도 (역할 중심)

```
test-project/
├─ sajugen/
│  ├─ input/         입력 정규화 — 진태양시 보정·음/양력·윤달·자시·상대방 파싱
│  │   ├─ time_correction.py  시민시각→UTC(표준시 역사·DST)→진태양시→시지/일주경계, ZasiPolicy
│  │   ├─ normalize.py        음/양력+윤달 → 양력 통일(KASI 1차)
│  │   └─ partner.py          고민 텍스트에서 타인 생년월일 감지(스팬)
│  ├─ calc/          결정론 계산(truth source) — LLM 절대 미관여
│  │   ├─ solarterms.py  Skyfield 24절기 정밀 시각·월주 경계
│  │   ├─ crosscheck.py  3원 교차(lunar↔Skyfield↔KASI)
│  │   ├─ kasi.py        KASI 캐시 리더(음양력·절기, 실시간 API 금지)
│  │   ├─ myeongni.py    사주팔자·지장간·십성·오행·대운·세운/월운 + current_daewoon
│  │   ├─ advanced.py    격국·억부용신·세운/월운 산출
│  │   ├─ shinsal.py     신살 레지스트리·기둥별·12신살·공망
│  │   ├─ ziwei.py       자미두수 명반(iztro_py 래퍼)
│  │   ├─ partner.py     상대방 명식·쌍 관계(십성·합충·오행보완)
│  │   └─ engine.py      통합 SajuResult(명리+자미+교차) — 단일 계산 진입점
│  ├─ content/       문안 생성 + 가드(LLM 전 룰 골격 / LLM 후 정제·검증)
│  │   ├─ rules.py            결정론 NLG(~16 챕터 골격, 사실 슬롯)
│  │   ├─ sections_schema.py  섹션 스키마·Section·GuardReport·Report23
│  │   ├─ builder.py          오케스트레이션: 룰→compose→가드→정제→일관성→Report
│  │   ├─ llm_sections.py     Anthropic compose·분류(_COMPOSE_SYSTEM 프롬프트)
│  │   ├─ question_router.py  고민 카테고리 분류
│  │   ├─ factcheck.py        사실 토큰(간지·별) 하드 차단
│  │   ├─ safe_lint.py        §12 안전표현(보장·적중·의료·운명론)
│  │   ├─ style_lint.py       AI틱 표현(기호 난발·시적 비유·반복)
│  │   ├─ trace.py            그라운딩(빈 본문·근거 없는 섹션)
│  │   ├─ repetition.py       크로스챕터 반복(일주 자기소개) 억제
│  │   ├─ masking.py          고민 원문 PII 마스킹(절대규칙 17)
│  │   ├─ postprocess.py      [신규] 공통 마크다운/한자 정제(개인·궁합 단일 소스)
│  │   └─ consistency.py      [신규] 교차챕터 대운 일관성 검사
│  ├─ render/        HTML→PDF·차트·검증
│  │   ├─ pdf.py        Jinja2→Playwright tagged PDF, 배경/낙관/광곽
│  │   ├─ charts.py     결정론 인라인 SVG(오행바·대운타임라인·명식표·자미명반)
│  │   └─ verify.py     PyMuPDF 게이트(텍스트레이어·폰트·태그·markdown·대운일관성)+veraPDF
│  ├─ models/report.py  Unified JSON 직렬화 스키마(주문 1건 전체)
│  ├─ store/            주문 상태머신(orders.py)·검수 오케스트레이션(order_flow.py)·admin.py
│  ├─ gunghap.py        다인 사업 궁합 리포트(별도 산출 경로)
│  ├─ pipeline.py       개인 리포트 단일 오케스트레이션(CLI/FastAPI 공통)
│  ├─ cli.py / app.py   Typer CLI / FastAPI
│  ├─ config.py / config/(rule_profile.yaml, brands.yaml)  유파·브랜드 외부화
│  └─ STATE.md          SSOT 진행상태(세션 시작 시 훅이 자동 주입)
├─ tests/             pytest(p1~p8·kasi·normalize·ziwei_parity·orders·shinsal·golden_sweep·
│                      gunghap·postprocess·consistency·admin_ui·safe_lint·style_lint·partner·
│                      repetition·llm_sections·insight)
├─ docs/              00~15 결정원장·유파결정·LLM정책·로드맵·톤스펙·신살리서치 등
├─ .claude/           rules/*.md(규칙) + settings.json(STATE 주입 훅)
├─ handoff/           [신규] 이 문서
├─ data/(gitignore)   KASI 캐시·insight jsonl
└─ .venv/, sajugen/tools/(gitignore, 288MB veraPDF/JRE)
```
(대용량/민감 폴더는 무시. 전체 파일 나열 아님.)

---

## 5. Claude Code 규칙·메모리·권한 구조

### 규칙(컨텍스트) vs 강제 차단(장치) — **핵심 구분**
> **CLAUDE.md와 `.claude/rules/*.md`는 "컨텍스트"일 뿐 — LLM에게 주입되는 지침이며 물리적으로 차단하지 않는다.**
> **실제 강제 차단은 오직 `settings.json`의 `permissions`(allow/deny)와 `hooks`(PreToolUse 등)로만 가능하다.** 즉 "절대규칙"이라도 hook/permission으로 뒷받침되지 않으면 모델이 어길 수 있는 *권고*다.

### 규칙 파일(컨텍스트)
- 루트 `CLAUDE.md`(프로젝트) + 전역 `~/.claude/CLAUDE.md` — 스택·SSOT 체인·절대규칙 요약·언어/커밋 컨벤션.
- `.claude/rules/` 4종(항상 로드):
  - `00-immutable.md` — 절대 불변 규칙 21항(계산 LLM 위임 금지·KASI 1차·자시 JST_2300·명리 최종권위·가드 3단 우회 금지·APPROVED 전 발송 금지·LLM PII 비전달·검증 안 한 것 "완료" 단정 금지 등).
  - `calc.md` — 계산 레이어(테스트 동반·골든 회귀·lunar 1.4.8 고정·진태양시 날짜 규칙).
  - `content.md` — 콘텐츠 레이어(3단 가드 통과 전 사용 금지·사실 슬롯 외 생성 금지·_pick 결정론).
  - `render.md` — 렌더(게이트 비악화·veraPDF 7.1-3 잔존 허용·폰트 OFL만).

### 강제 차단(장치) — settings.json
- **전역 `~/.claude/settings.json`** (실제 enforcement이 여기 있음):
  - `permissions`: allow 34개 / deny 13개. deny 예: `Bash(rm:*)`,`Bash(del:*)`,`Bash(reg:*)`,`Bash(powershell:*)`,`Bash(cmd /c:*)`,`Bash(curl *|*sh:*)`,`Bash(format/shutdown/reboot/taskkill/net:*)`.
  - `hooks`(PreToolUse): `Edit|Write`→비밀정보 차단·금지어 차단·compact 제안, `Bash`→.env 커밋 차단·pre-commit 보안스캔. PostToolUse: 린트·loop-guard. Stop: 자동 리뷰. (스크립트 본체는 crypto-signal 프로젝트에 위치.)
  - `model: opus[1m]`, `advisorModel`, `env`(모델 라우팅 — 값 비공개), `statusLine`.
- **프로젝트 `test-project/.claude/settings.json`**: `hooks`만 — `SessionStart`/`PreCompact`에서 `STATE.md`를 자동 주입(컨텍스트 보존). **permissions/deny 없음** → 파괴적 명령 차단은 전역 settings에 의존.

### 메모리·운영 원칙
- auto-memory: `~/.claude/projects/.../memory/`(MEMORY.md 인덱스). 사용자 선호·피드백·프로젝트 사실 영속.
- 현재 운영 원칙(이번 세션 실제 적용): **Plan Mode 우선 → 수동 승인 → auto mode 금지 → 커밋 전 PDF 육안 검수 → secrets 접근 금지 → 측정값으로만 "완료" 보고**(사용자 2회 교정 이력).

---

## 6. 명리·자미 계산 파이프라인

| 파일 | 역할 | 주요 함수/클래스 | truth source | LLM 관여 | 최근 변경 |
|---|---|---|---|---|---|
| input/time_correction.py | 시민시각→UTC→진태양시·시지·일주경계 | `correct()`, `ZasiPolicy`, `CorrectedTime` | ✅ | ✗ | ✗ |
| input/normalize.py | 음/양력·윤달→양력 통일(KASI 1차) | `normalize_date()`, `NormalizedDate` | ✅ | ✗ | ✗ |
| input/partner.py | 고민 텍스트 내 타인 생년월일 감지 | `find_partner_births()` | ✅(파생만) | ✗ | ✗ |
| calc/solarterms.py | Skyfield 24절기 정밀 시각·월주 경계 | `solar_term_time()`, `month_pillar_branch()` | ✅ | ✗ | ✗ |
| calc/crosscheck.py | 3원 교차(lunar↔Skyfield↔KASI) | `crosscheck_year()` | ✅ | ✗ | ✗ |
| calc/kasi.py | KASI 캐시 리더(음양력·절기) | `KasiCache` | ✅ | ✗ | ✗ |
| calc/myeongni.py | 사주팔자·지장간·십성·오행·대운·세운/월운 | `build()`, `Myeongni`, `DaYunItem`, **`current_daewoon()`** | ✅ | ✗ | ✅ (current_daewoon 신규) |
| calc/advanced.py | 격국·억부용신·세운/월운 | `geukguk()`, `eokbu()`, `seun_worun()` | ✅ | ✗ | ✗ |
| calc/shinsal.py | 신살·12신살·공망 | `evaluate()`, `twelve_shinsal()`, `gongmang()` | ✅ | ✗ | ✗ |
| calc/ziwei.py | 자미두수 명반(iztro_py) | `build()`, `Ziwei`, `Palace`, `Star` | ✅ | ✗ | ✗ |
| calc/partner.py | 상대방 명식·쌍 관계 | `partner_pillars()` | ✅ | ✗ | ✗ |
| calc/engine.py | 통합 결과 | `build()`, `SajuResult`, `CrossCheck` | ✅ | ✗ | ✗ |
| models/report.py | Unified JSON 스키마 | `UnifiedReport` 외 | (직렬화) | ✗ | ✗ |

**핵심 확정 지점**
- 사주팔자: `myeongni.build()` (lunar-python EightChar, 진태양시 기준) — 1회 확정.
- 대운/세운/월운: `myeongni.build()` + `advanced.seun_worun()`(lunar-python 출력 노출, 추정 금지) — 1회 확정.
- **current_daewoon**: `myeongni.current_daewoon(m, ref_year)` = `start_year <= ref_year`인 마지막 대운(단일 현재 대운). 2026 기준 김태수 → 정미(26~35).
- 자미두수 명반: `ziwei.build()` (iztro_py).
- **LLM이 계산값을 새로 만들 수 없는 구조**: `factcheck`가 본문의 간지·자미 별을 허용 토큰 집합과 대조해 집합 밖이면 하드 차단. 계산은 전부 calc/ 결정론. (절대규칙 1·13)

---

## 7. 콘텐츠 생성 파이프라인

| 파일 | 역할 | LLM 전/후 | guard/fallback/self-heal/hard gate | 최근 변경 | 위험 |
|---|---|---|---|---|---|
| rules.py | 결정론 챕터 골격(사실 슬롯) | **전** | (골격=항상 안전한 폴백 원천) | ✅ 현재대운 단일사실 주입·대운 태그 | 자미 골격에 `[핵심 궁]`·`명궁(명궁)` 잔재 |
| sections_schema.py | 섹션·Section·GuardReport·Report23 | - | - | ✅ `daewoon_consistent` 필드 | 낮음 |
| builder.py | 오케스트레이션 | 전·후 | guard 재검증·**self-heal(대운 폴백)**·룰 폴백 | ✅ postprocess 별칭·일관성 통합 | 중간(흐름 복잡) |
| llm_sections.py | Anthropic compose·분류 | **중** | (프롬프트 지침) | ✅ 현재대운 규칙 1줄 | 프롬프트는 강제 아님 |
| question_router.py | 고민 분류 | 전 | - | ✗ | 낮음 |
| factcheck.py | 간지·별 토큰 하드 차단 | **후** | **hard gate(사실)** | ✗ | 낮음 |
| safe_lint.py | §12 안전표현 | 후 | **hard gate(안전)** | ✗ | 낮음 |
| style_lint.py | AI틱 기호·비유·반복 | 후 | hard gate(스타일) | ✗ | 마크다운 `#`·`**`는 미검출(postprocess가 담당) |
| trace.py | 그라운딩(빈 본문·근거) | 후 | hard gate(그라운딩) | ✗ | 낮음 |
| repetition.py | 일주 자기소개 반복 억제 | 후 | 결정론 백스톱 | ✗ | 낮음 |
| masking.py | 고민 원문 PII 마스킹 | 전(LLM 입력) | (절대규칙 17) | ✗ | 낮음 |
| postprocess.py | 공통 마크다운/한자 정제 | **후** | 정제(개인·궁합 단일 소스) | ✅ 신규 | 낮음 |
| consistency.py | 교차챕터 대운 일관성 | 후 | self-heal 근거 + hard gate 근거 | ✅ 신규 | 후방패턴 과/미탐 가능 |

**흐름 설명**
- **LLM 전 근거 슬롯**: `rules.build_all()`이 계산 사실(간지·오행·십성·신살·궁·세운 연도·현재 대운)을 한글 산문 골격으로 만들고, `builder._base_for()`가 챕터 base_text로 LLM에 전달. consult는 명식 사실 + 마스킹된 고민 인용.
- **LLM 후 정제·검증**: `postprocess.strip_artifacts`(마크다운 제거) → 간지 한자→한글 → `postprocess.hanja_clean`(비간지 한자 제거·기호 산문화) → `safe_lint`+`style_lint`+`factcheck` 통과 시 채택, 실패 시 1회 재작성→그래도 실패면 **룰 골격 폴백**.
- **factcheck vs trace**: factcheck=본문의 *사실 토큰*(간지·자미 별)이 계산 집합에 있는지(환각 차단). trace=섹션이 *근거 소스(source_keys)*를 갖고 본문이 비지 않았는지(그라운딩).
- **safe_lint vs style_lint**: safe_lint=§12 *안전/법적*(보장·적중·의료·운명론). style_lint=*AI틱 문체*(기호 난발·시적 비유·반복). 마크다운 `#`/`**`/`---`은 둘 다 안 잡음 → **postprocess가 전담**.
- **postprocess 양쪽 사용**: builder가 `_strip_artifacts/_hanja_clean = postprocess.*` 별칭으로, gunghap이 `_finalize()`(strip_artifacts→간지변환→hanja_clean)로 동일 함수 호출 → 경로 드리프트 방지.
- **consistency 대운 검사**: `current_framed(text)`가 "현재/지금/올해/초입 + {간지} 대운" 또는 "{간지} 대운 초입/들어서" 패턴으로 *현재로 서술된 간지*를 추출. `check(sections, expected_ko)`=기대값과 다르거나 2종 이상이면 위반.
- **self-heal vs hard gate**:
  - self-heal = builder가 잘못 서술 챕터를 **룰 골격으로 폴백**(결정론 정답). 일상 케이스는 조용히 교정.
  - hard gate = `verify.py`가 최종 PDF에서 현재대운 간지 2종↑이면 `gate_pass=False`로 **빌드 실패**. self-heal이 놓친 경우의 안전망.

---

## 8. 개인 종합 사주 PDF 파이프라인

흐름: `cli/app` → `pipeline.generate()` → `engine.build()`(SajuResult) → `builder.build_report()`(rules 골격 → use_llm시 compose → 가드 → self-heal → Report23) → `render_pdf.render_pdf()`(Jinja2→Playwright tagged) → `verify.verify()`(게이트).

**최근 확인된 결과 (final_taesoo_llm.pdf, LLM 실호출, 37p, 2026-06-15 측정)**
- ✅ 현재 대운 = **정미 하나로만** 서술(framed set `{정미}`). 병오는 36~45 미래 대운으로만(p26 타임라인). **대운 모순 해결**.
- ✅ `gate_pass=True`, `markdown_clean=True`, `daewoon_consistent=True`. compose polished 11/fallback 2(ziwei·consult는 §12 폴백, 대운 무관).
- ✅ 본문 한자: 해석 챕터 0, **p36 용어 풀이 부록만 의도적 한자 병기**(`_STATIC_OK` 설계).

**남은 품질 이슈(육안+스캔 확인)**
- p25: `"있습니다."` 한 문장만 단독 페이지로 넘어감 = **orphan page**.
- p29/p30 자미두수 섹션 **템플릿 잔재**: `[핵심 궁]`·`[그 밖의 궁]`·`명궁(명궁)`(라벨 중복)·`주성은 주성 없음(공궁)`(공궁 표현). → ziwei 챕터가 §12로 룰 골격 폴백 시 골격 자체의 대괄호/중복 라벨이 노출됨(postprocess의 `[원국]`류 strip 목록에 미포함).
- p36 한자는 **정상**(부록 표기).

---

## 9. 3인 사업 궁합 PDF 파이프라인

- `gunghap.py`: `person_facts()`(engine 재사용, **person별 is_male**) → `pair_facts()`(calc/partner) → `_person_slot/_pair_slot/_timing_slot`(사실 슬롯) → `_compose()`(LLM, `_finalize` 정제) → `trace.check` 그라운딩 → render → `verify` 게이트.
- `calc/partner.py`: 상대 명식·일간↔일간 십성·천간합·일지 육합/충·삼합 반합·부족 오행 보완(전부 결정론).
- 2인/3인: `combinations`으로 쌍 생성(N=2도 동작). 그룹 레이어는 timing 교집합뿐(진정한 그룹 합성은 후속).
- person별 성별: **`is_male=True` 하드코딩 제거** → CLI 4번째 필드(`,남/여`), 대운 방향(양남음녀) 정상화.
- situation PII: `masking.mask_concern`로 생년월일/시각 마스킹 후 LLM 전달(절대규칙 17).
- trace.check: 섹션에 `source_keys=["gunghap"]` 부여 후 적용.
- postprocess: LLM 출력 **및 폴백 슬롯** 양쪽에 `_finalize` 적용(폴백의 `용신 火` 누출도 차단).
- verify markdown gate: gunghap도 `verify()` 호출, `markdown_clean`/`gate_pass` 실패 시 빌드 예외.

**최근 결과 (gunghap_llm.pdf, LLM 실호출, 17p, 2026-06-15 측정)**

해결: `---`·`**`·`#` 0건 / 본문 비간지 한자 0건 / 성별 반영 / 5장 구조 유지 / situation 날짜 누출 0 / `gate_pass=True`.

남은 품질 이슈(스캔 확인) + 원인 분류:

| 이슈 | 위치 | 원인 후보 | 잡아야 할 레이어 | 추천 수정 위치 |
|---|---|---|---|---|
| `술(술)` 중복괄호 | p5 | 슬롯이 `_gz_ko` 변환 후 `한자(한글)`형을 또 한글화 → `한글(한글)` | postprocess/rules | postprocess에 `X(X)` 축약 규칙 or 슬롯 생성부 점검 |
| `진(진)` 중복괄호 | p7 | 동일 | postprocess/rules | 동일 |
| `신강한 신약의 차이` | p7 | LLM 카피 모순(신강/신약 혼용) | LLM/rules | 프롬프트 강화 + phrase/모순 lint(신규) |
| `김태수, 재수는 …`(오타) | p12 | LLM 오타(재무→재수) | LLM | phrase blacklist lint(신규) + 재작성 |
| `2026년이 오기 전까지` | p17 | ref_year(2026)가 "현재"인데 미래처럼 서술 = 시제 오류 | LLM/rules | ref_year 시제 lint(신규) + 골격 닻 강화 |

---

## 10. PDF 렌더링과 검증 파이프라인

| 파일 | 역할 | 주요 함수 |
|---|---|---|
| render/pdf.py | Jinja2 HTML→Playwright tagged PDF, 광곽·배경·낙관 | `render_html()`, `render_pdf()`, `_apply_background()`, `harden_pdf_ua()` |
| render/charts.py | 결정론 인라인 SVG | `ohaeng_bar()`, `daewoon_timeline()`, `sipseong_card()`, `manse_table()`, `ziwei_chart()` |
| render/verify.py | PyMuPDF 게이트 + veraPDF 측정 | `verify()`, `markdown_artifacts()`, `_verapdf_ua1()` |

- **Playwright**: Chromium으로 tagged PDF(웹폰트 `document.fonts.ready` 대기). **veraPDF**: 포터블 Java21로 PDF/UA-1 측정만(7.1-3 1건 잔존=Chromium 한계, 빌드 불차단). **PyMuPDF**: 텍스트레이어 추출·게이트·배경 합성.
- `markdown_clean` = 본문에 `---`(수평선 라인)·`**`·`# ` 마크다운 흔적 0(`markdown_artifacts()`).
- `gate_pass` = 텍스트레이어(≥1500자) **and** 폰트임베드 **and** tagged **and** `markdown_clean` **and** `daewoon_consistent`.
- `daewoon_consistent` = 최종 PDF에서 "현재로 서술된 대운 간지"가 1종 이하(2종↑=모순=실패). `consistency.current_framed` 재사용.
- 본문 한자 검사: **부록(용어 풀이)은 의도적 한자 병기**라 게이트에 한자 검사를 넣지 않음(개인 PDF 깨짐 방지). 비간지 한자는 섹션 단위 `hanja_clean`으로 차단.
- **orphan/짧은 페이지 검사: 없음.** 현재 p25 `"있습니다."` 같은 orphan page를 **자동 검출 못 함**(미구현 — §14 후보).

---

## 11. 현재 변경 작업 요약 (1·2단계)

| 파일 | 변경 목적 | 핵심 변경 | 위험도 | 되돌릴 때 영향 |
|---|---|---|---|---|
| content/postprocess.py [신규] | 정제 단일 소스 | strip_artifacts/hanja_clean 이전(`_CJK_RX`는 `\u` 명시) | 낮음 | builder/gunghap 정제 깨짐 |
| content/consistency.py [신규] | 대운 일관성 | current_framed/check/offending_ids | 낮음 | 일관성 검사 사라짐 |
| content/builder.py | 정제 통일 + self-heal | postprocess 별칭, 대운 폴백, daewoon_consistent | 중간 | 개인 리포트 핵심 흐름 |
| content/rules.py | 현재대운 단일사실 | current_daewoon 주입·대운 (지난/지금/앞으로) 태그 | 낮음 | 대운 골격 닻 사라짐 |
| content/llm_sections.py | 프롬프트 규칙 | "현재 대운=명시된 하나뿐" 1줄 | 낮음 | LLM 드리프트 방어 약화 |
| content/sections_schema.py | 가드 필드 | GuardReport.daewoon_consistent | 낮음 | 보고 필드 |
| calc/myeongni.py | 단일 현재대운 | current_daewoon() 헬퍼 | 낮음 | rules/builder/verify 근거 |
| gunghap.py | 경로 통일 | _finalize·trace·masking·person별 성별·verify 게이트 | 중간 | 궁합 결함 재발 |
| render/verify.py | PDF 게이트 | markdown_artifacts + daewoon gate → gate_pass | 낮음 | 누출/모순 빌드차단 사라짐 |
| tests/* | 회귀 | postprocess·consistency 신규, gunghap·p2 확장 | 낮음 | 검증 약화 |

---

## 12. 현재 diff 요약

`git diff --stat HEAD` = 10 modified + 4 new, `262(+)/73(-)`. 삭제 0.

**신규 파일(전문 — 비밀정보 없음, 짧음)**

`sajugen/content/postprocess.py` (요지): `strip_artifacts(text)`=마크다운 제목/수평선/리스트/굵게/코드/인용 제거. `hanja_clean(text)`=CJK 한자 제거(`_CJK_RX = re.compile("[㐀-䶿一-鿿豈-﫿]+")` — **한글 U+AC00-D7A3 비포함 보장**) + em dash·가운뎃점·화살표 산문화 + 줄머리 원문자/불릿 제거.

`sajugen/content/consistency.py` (요지): `_GZ="[갑을병정무기경신임계][자축인묘진사오미신유술해]"`. `_CUR_BEFORE`=`(현재|지금|올해|이번|막|초입|진입)[^.。!?\n]{0,14}?({_GZ})\s*대운`. `_CUR_AFTER`=`({_GZ})\s*대운\s*(초입|진입|에\s*들어|시작|들어서|막)`. `current_framed(text)`→집합. `check(sections, expected_ko)`→(ok, bad). `offending_ids(sections, expected_ko)`→폴백 대상 id.

`tests/test_postprocess.py`: strip_artifacts·hanja_clean(**한글 보존 회귀**)·markdown_artifacts 검증(5케이스).
`tests/test_consistency.py`: current_framed·check(혼서 위반)·offending_ids·**렌더 PDF 하드페일**·**빌더 revert 분기**·룰경로 단일일치(8케이스).

**수정 파일(핵심 변경 요약, 전체 덤프 X)**
- builder.py: import에 `myeongni as mod_my`·`consistency`·`postprocess`. legacy 정제 54줄 제거→`_strip_artifacts/_hanja_clean = postprocess.*` 별칭. dedup 후 `current_daewoon`→`offending_ids`로 잘못 챕터 골격 폴백→`consistency.check`→`daewoon_consistent`. clean에 합산.
- rules.py: daewoon 섹션에 `current_daewoon` import, `cur_line`("기준 {ref_year}년 현재, … {정미} 대운 하나입니다 …'지금·현재·초입'으로 부르지 않습니다") + 각 대운 줄에 `(지난/지금/앞으로)` 태그.
- llm_sections.py: `_COMPOSE_SYSTEM`에 현재 대운 단일 규칙 1줄.
- sections_schema.py: `GuardReport.daewoon_consistent: bool = True`.
- myeongni.py: `current_daewoon(m, ref_year)` 추가.
- gunghap.py: import(postprocess·trace·masking·input_partner·verify), `person_facts(is_male=)`, `_finalize()`, `_compose` 폴백/출력 정제, `build_gunghap` person별 성별·situation 마스킹·source_keys·trace·verify 게이트, CLI 4번째 필드(성별).
- verify.py: `markdown_artifacts()`+`markdown_clean`, `current_framed` 기반 `daewoon_consistent`, 둘 다 `gate_pass`에 합산.
- tests/test_gunghap.py·test_p2.py: _finalize·폴백정제·성별 방향·current_daewoon 골든 추가.

---

## 13. 테스트 현황

- 전체 22개 파일. **마지막 측정: 전체 `tests/` 180 PASS**(legacy 제거 후, 2026-06-15) → 이후 consistency에 2테스트(렌더 하드페일·revert) 추가하여 **182**(부분 실행으로 확인, 전체 재실행은 본 문서 작성 시 미수행).
- 실행: `./.venv/Scripts/python.exe -m pytest tests/ -q`.
- 신규 테스트: `test_postprocess.py`, `test_consistency.py`. 수정: `test_gunghap.py`, `test_p2.py`.
- 각 테스트가 잡는 결함: factcheck=환각 간지, safe_lint=§12, style_lint=AI틱, trace=그라운딩, postprocess=마크다운/한자 누출(+**한글 보존 회귀**), consistency=대운 혼서(+렌더 PDF 하드페일+빌더 revert), gunghap=성별 방향·폴백 정제, golden_sweep/p2=계산 골든.
- 룰 폴백 테스트(키 제거, 결정론) vs LLM 실호출(이번 PDF 재생성 시 수동 1회). PDF 재생성 명령은 §2.

**6 이슈를 현재 테스트가 잡는가?**
| 이슈 | 잡히나 | 비고 |
|---|---|---|
| `김태수, 재수는`(오타) | ❌ | phrase/오타 lint 없음 |
| `신강한 신약`(모순) | ❌ | 모순/의미 lint 없음 |
| `2026년이 오기 전까지`(시제) | ❌ | temporal lint 없음 |
| `있습니다.` 단독 페이지 | ❌ | orphan page 검출 없음 |
| `[핵심 궁]` 템플릿 잔재 | ❌ | postprocess strip 목록에 미포함 |
| `술(술)`/`진(진)` 중복괄호 | ❌ | `X(X)` 정제/검출 없음 |

→ **남은 6 이슈는 현재 테스트/게이트가 전혀 못 잡음**(전부 신규 lint/detector 필요).

---

## 14. 현재 남은 품질 이슈 해결 제안

| 이슈 | 원인 추정 | 가장 낮은 위험 수정 위치 | 테스트 추가 | 이번 커밋 포함? |
|---|---|---|---|---|
| p12 `김태수, 재수는` | LLM 오타(재무) | phrase blacklist lint(신규, content) + 재작성 트리거 | 블랙리스트 단어→재작성/폴백 단위테스트 | 권장 후속(별도) |
| p7 `신강한 신약의 차이` | LLM 모순 | 모순쌍 lint(신강↔신약 동시등장) + 프롬프트 | 합성문장 위반 테스트 | 권장 후속 |
| p17 `2026년이 오기 전까지` | ref_year 시제 | temporal lint(ref_year보다 과거를 미래로/그 반대) + rules 닻 | ref_year 기준 문장 테스트 | 권장 후속 |
| p5/p7 `술(술)`,`진(진)` | `한글(한글)` 중복 | postprocess에 `([가-힣]+)\((\1)\)`→`\1` 규칙(저위험) | 중복괄호 정제 단위테스트 | **이번/근접 커밋 가능(저위험)** |
| p29 `[핵심 궁]`/`명궁(명궁)` | rules 자미 골격 잔재 | rules 골격 문안 정리 + postprocess 대괄호 strip 확장 | 자미 챕터 잔재 0 테스트 | **이번/근접 커밋 가능** |
| p25 `있습니다.` orphan | 페이지 넘침 | verify에 orphan-page detector(짧은 마지막 페이지 경고/실패) + 렌더 page-break 조정 | 짧은 페이지 게이트 테스트 | 권장 후속(렌더 영향 검토) |

원칙: 계산 결함 아님 → calc/ 무수정. lint/detector는 content·render 레이어 추가로 한정.

---

## 15. 하네스 엔지니어링 준비도

목표: 반복 가능한 검수·PDF 품질 자동평가·LLM 드리프트 차단·계산 일관성·report_type별 검증·golden 확장·실패 자동수집·파일 기반 handoff·향후 멀티에이전트.

### 15-1. 이미 있는 하네스 자산
- pytest 22파일·golden(test_p2·golden_sweep 21+케이스·독립 오라클)·`verify.py`(게이트)·`consistency.py`·`postprocess.py`·`factcheck/trace/safe_lint/style_lint`·`STATE.md`(SSOT)·`.claude/rules`·CLAUDE.md·render/out gitignore·KASI/Skyfield/iztro 교차검증 자산·brands/rule_profile 외부화.

### 15-2. 부족한 하네스 자산
- PDF visual QA harness(렌더 이미지/레이아웃 평가)·**orphan/widow page detector**·**phrase blacklist/모순 semantic lint**·**temporal expression lint**·**name/오타 detector**·**report_type별 validation profile**·generated PDF snapshot diff·LLM output corpus 저장/회귀·표준 handoff 프로토콜·subagent role spec·CI 최소/전체 검증 분리.

### 15-3. 로드맵

**Phase H1 — 단일 에이전트 하네스(품질 자동 검출)**
- 목표: 남은 6이슈를 자동 검출하는 lint/detector + report_type별 verify profile.
- 새 파일: `content/phrase_lint.py`(블랙리스트·모순쌍), `content/temporal_lint.py`(ref_year 시제), `render/layout_qa.py`(orphan/widow), `content/verify_profiles.py`(single/gunghap/단품별 기준).
- 테스트: 각 lint 위반/통과 + 6이슈 재현 케이스.
- 위험: 과탐(정상 문장 차단) → 보수적 패턴 + 폴백.
- 승인 지점: lint 추가 전(과탐 위험 검토), gate_pass 편입 전.

**Phase H2 — 파일 기반 handoff 하네스**
- 목표: handoff/*.md 표준화(ChatGPT review packet / Claude execution packet / 결과 schema), STATE.md와 별도 `RUN_LOG.md` 분리, 커밋 전 checklist 자동 생성.
- 새 파일/폴더: `handoff/`(이 문서 포함)·`handoff/templates/`·`RUN_LOG.md`·`scripts/precommit_checklist.py`(읽기전용 점검).
- 테스트: 체크리스트 생성·schema 검증.
- 위험: 문서 표류(코드와 불일치) → 생성 자동화.
- 승인 지점: 표준 포맷 확정.

**Phase H3 — subagent/multi-agent 하네스**
- 목표: §16 worker들을 read-only 감사자로 운용, 수정은 main만, 결과는 handoff append + critic 재검.
- 새 파일: `.claude/agents/*`(worker spec), `handoff/audits/`.
- 테스트: worker 출력 schema·금지행동(커밋/배포/secrets) 차단 시나리오.
- 위험: 비용/컨텍스트 폭증·결과 충돌 → 필요 시에만, critic 게이트.
- 승인 지점: worker별 도입 전.

---

## 16. subagent / worker 설계 초안 (구현 아님, 설계만)

| worker | 목적 | 읽을 파일 | 금지 행동 | 출력 형식 | 사용 시점 |
|---|---|---|---|---|---|
| repo-auditor | 구조·의존·드리프트 감사 | 전역(코드 한정) | 수정/커밋/secrets | handoff/audits/repo.md | 구조 변경 후 |
| astrology-engine-auditor | 명리 계산 정확도 | calc/myeongni·advanced·solarterms·shinsal | 수정/커밋 | 골든 대조표 | calc 변경 후 |
| ziwei-engine-auditor | 자미 명반 정합 | calc/ziwei + iztro 비교 | 수정/커밋 | 동등성 표 | ziwei 변경 후 |
| gunghap-auditor | 쌍/그룹 관계 정확도 | gunghap·calc/partner | 수정/커밋 | 관계 검증표 | 궁합 변경 후 |
| pdf-render-auditor | 레이아웃/orphan/마크다운/한자 | render/* + 산출 텍스트 | 바이너리첨부/커밋 | 품질 리포트 | PDF 생성 후 |
| copy-quality-auditor | 오타·모순·시제·헤지·반복 | 산출 텍스트 + content/* | 수정/커밋 | 문장 이슈 표 | PDF 생성 후 |
| security-auditor | secrets·권한·hook·.gitignore | settings 구조·.gitignore | secrets 값 출력/커밋 | 보안 점검표 | 릴리스 전 |
| test-planner | fixture/회귀 설계 | tests/* + 변경 diff | 수정/커밋 | 테스트 계획 | 구현 전 |
| release-checker | 커밋/발송 전 종합 게이트 | git 상태·verify 결과·체크리스트 | 커밋/배포 실행 | go/no-go | 커밋 직전 |

원칙: worker는 기본 read-only / 수정은 main agent만 / 결과는 handoff/*.md append / secrets 읽으면 실패 / 커밋·배포 제안하면 실패 / critic이 한 번 더 검토.

---

## 17. 커밋 전략 제안

| 선택지 | 장점 | 단점 |
|---|---|---|
| A. 6이슈까지 고친 뒤 커밋 | 한 번에 깨끗한 상태 | 커밋 지연·변경 누적·롤백 단위 큼 |
| B. 1·2단계만 먼저 커밋, 6이슈 후속 | 회귀0·182 PASS로 안전, 작은 롤백 단위 | 6이슈가 잠시 잔존 |
| C. 커밋 안 하고 스냅샷 후 ChatGPT 검토 | 외부 검토 반영 가능, 방향 확정 후 진행 | 진행 멈춤 |

**Claude Code 추천: C → 그다음 B.** 지금은 운영자 육안검수 + ChatGPT 검토 단계이므로 **C(이 문서로 검토)** 우선. 검토 후, 1·2단계 수정은 회귀0이므로 **B로 먼저 커밋**(권장 분리: ① `fix(sajugen): 궁합 PDF 마크다운·한자 누출 차단+경로 가드 통일` ② `fix(sajugen): 대운 교차챕터 일관성(현재 대운 단일화)` ③ `docs(sajugen): STATE 갱신`), 6이슈는 H1 lint와 함께 후속 커밋. (A는 6이슈 수정이 길어지면 1·2단계 안전 변경까지 미커밋 상태로 묶여 위험.)

---

## 18. 이번에 절대 하지 말아야 할 것

- report_type enum 정식화 / 단품운세 출시 / 토정비결·택일·작명 신규 엔진 / order_flow·admin 연결
- 커밋 / 배포 / 외부 API 호출(이 문서 작성 시) / secrets·.env 접근 / 대규모 리팩터링 / auto mode
- PDF 바이너리 커밋 / render/out 커밋 / **STATE.md와 코드 변경을 무조건 한 커밋에 섞기**(docs는 분리)

---

## 19. ChatGPT에게 물어볼 질문

1. 남은 PDF 품질 이슈 6개를 **이번 커밋 전에 모두** 고치는 게 맞는가, 아니면 1·2단계를 먼저 커밋하고 후속으로 빼는 게 맞는가?
2. 현재 **self-heal + verify hard gate** 2중 구조를 유지할지, **순수 hard fail**(폴백 없이 무조건 빌드 실패)로 바꿀지?
3. STATE.md는 **별도 `docs(sajugen):` 커밋**으로 분리하는 게 맞는가?
4. 하네스 엔지니어링 **H1을 지금 바로** 시작할지, **6이슈 수정 후** 시작할지?
5. subagent(§16) 설계는 **언제** 도입할지(H3 시점? 더 일찍?)?

---

## 20. 민감정보 점검 체크리스트

- [x] .env 내용 없음
- [x] API key 없음(설정 값은 마스킹·구조만)
- [x] secrets/credentials 없음
- [x] 고객/지인 생년월일·시각·출생지 원문 없음(이름은 테스트 라벨로만)
- [x] 고민 원문 없음
- [x] render/out PDF 바이너리 없음(텍스트 구조 사실만 인용)
- [x] cache/log/temp 파일 본문 없음
- [x] 외부 API 호출 없음(문서 작성 과정)
- [x] 커밋 없음
- [x] 배포 없음
- [x] 코드 수정 없음(이 문서 1개만 생성)
