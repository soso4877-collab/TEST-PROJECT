# TASK_PACKET — brain-health 근거 감사 옵트인 구멍 (brainhealth-evidence-audit-optin-gap-20260822)

- **task_id**: `brainhealth-evidence-audit-optin-gap-20260822`
- **owner**: **Codex 구현자** (운영자 지정 2026-08-22)
- **next_reviewer**: **Claude Code 교차리뷰** (read-only, 구현 세션과 분리)
- **base_commit**: `07e8ca9`
- **rev**: 1

> ★ **대상이 이 저장소 밖이다.** 수정 파일은 `C:\Users\pc\AI-Brain\_scripts\brain-health.ps1` 하나이며
> sajugen 저장소에 커밋되지 않는다. §0 의 접근성 확인을 **가장 먼저** 하라.

---

## 0. 착수 전 필수 확인 — 실패 시 즉시 정지

`AI-Brain` 은 별도 vault 이고 Codex 샌드박스가 워크스페이스 밖 쓰기를 막을 수 있다.

1. `C:\Users\pc\AI-Brain\_scripts\brain-health.ps1` **읽기** 가능한지 확인한다.
2. 같은 경로에 **쓰기** 가능한지 확인한다(무해한 방법으로: 임시 파일 생성 후 원복, 또는 권한 조회).
3. 하나라도 불가하면 **구현하지 말고 `BLOCKED_ENV` 로 정지 보고**한다. 우회하지 않는다.

Codex 상시 금지(PDF 재생성 · LLM/API 호출 · git commit · push · 배포)는 그대로다.
**vault 는 git repo 이므로 특히 commit·push 금지가 중요하다.** 파일 수정까지만 하고 멈춘다.

## 1. Goal (관측 가능한 결과 하나)

**정본 노트에 외부 URL 이 있는데 원문 인용도 없고 근거 태그도 없는 절을, 감사기가 실제로 잡는다.**
지금은 `[공식확인]` 리터럴 태그를 단 절만 검사하므로 태그를 안 달면 영구 면제된다.

## 2. Background — 실측 (2026-08-22, read-only)

### 2-1. 구멍의 위치

`brain-health.ps1`:

```
113행   $tagPattern = '\[공식확인(?:[^\]]*)\]'
```

`Get-EvidenceAudit` 는 `Test-TextUsesOfficialTag` 가 참인 절만 평가한다(256-259행에서 URL·인용 요구).
**태그가 없으면 절 자체가 평가 대상에서 빠진다** — 옵트인 검사다.

### 2-2. 규모 측정 (정본 8폴더 전수)

| 항목 | 건수 |
|---|---|
| 정본 노트 총계 | 88 |
| 외부 URL 보유 | 16 |
| **URL 있고 Markdown 인용 없음** | **6** |
| 근거 태그(`[공식확인]`/`[로컬실측]`/`[로컬정본]`/`[추론]`/`[확인불가]`) 보유 | 13 |

→ **75건이 무태그 = 현재 검사 면제.** URL 기준으로 바꿔도 신규 적발은 **6건뿐**이라 홍수가 아니다.

### 2-3. 가설이 아니라 **실현된 누출** 1건

`70_AI-Collab/컨텍스트-엔지니어링-삭감기준.md` 는 이미 승격을 통과했다:

```yaml
grade: 확정
evidence: 공식문서
verified: 2026-07-26
```

본문에 외부 URL 1건(`claude.com/blog/...`)이 있고 **Markdown 인용 0건**이다.
근거 규율은 *"인용을 못 달면 `[추론]`으로 내린다"* 인데, **태그를 안 달았다는 이유로 검사를 통과**했다.
`brain-health` 는 이 노트를 `official_without_quote` 에 넣지 않았고 `errors` 는 비어 있었다.

### 2-4. 적발 대상 6건 (구현자가 §5-3 에서 전수 분류할 것)

```
20_Coding-Style/Windows-Credential-Generic-토큰-저장.md
50_Decisions/2026-07-29-사주도령-공개가격-노출전략.md
70_AI-Collab/2026-07-13-환경-능력별-검증-계약.md
70_AI-Collab/컨텍스트-엔지니어링-삭감기준.md          <- 이미 grade: 확정
75_Content-Domain/소셜-시각-QA와-도구-라우팅.md
75_Content-Domain/Meta-자동화-안전-경로.md
```

---

## 3. 변경 설계

### 3-1. URL 기반 신규 검사 (기존 검사는 무수정)

정본 노트의 절에 **외부 URL 이 있으면**, 다음 중 하나를 요구한다:
- 같은 절에 Markdown 인용(`^\s*>\s*\S`), **또는**
- 명시적 비공식 태그(`[로컬실측]`·`[로컬정본]`·`[추론]`·`[확인불가]`) — 이미
  `Test-TextDeclaresAlternativeEvidenceTag`(119-125행)가 있으니 **재사용**한다(복제 금지).

둘 다 없으면 신규 키에 담는다.

### 3-2. 신규 키는 **warning** 으로 낸다 (error 아님)

- 신규 키 이름 예: `external_url_without_quote_or_tag`(이름은 구현자 재량, 기존 키와 구분되면 된다).
- 이유: 지금 적발 6건이라 error 로 내면 **`exit 0` 이 즉시 깨진다.** 2026-08-22 기준 `errors: []` ·
  `exit 0` 상태를 유지한 채 관측부터 시작한다(veraPDF 를 "측정만·빌드 불차단"으로 둔 선례와 같은 계열).
- **에스컬레이션 조건을 코드 주석에 남긴다**: 적발 6건이 0 이 되면 error 로 승격. 그 판단은 운영자 몫이다.

### 3-3. 하지 않을 것

- 기존 `official_without_quote`(error) · `local_tagged_official`(warning) **완화·이름 변경 금지.**
  게이트 수정은 **사각 축소 방향만** 허용된다.
- 정본 노트 **6건 자체를 수정하지 마라.** 이 패킷은 감사기만 고친다.
  (인용문을 채우는 것은 원 작업 맥락을 아는 쪽의 일이고, 지어내면 안 된다.)
- `Remove-MarkdownCode`·`Remove-MarkdownFences`·경로 판정(`Test-SectionHasLocalEvidence`) **무수정**.

## 4. 파일 경계

**allowed_files**
```
C:\Users\pc\AI-Brain\_scripts\brain-health.ps1        (신규 검사 + 자체테스트 추가)
```
그 외 **전부 금지**. 특히 vault 의 정본 노트·`10_Inbox`·`_templates`·sajugen 저장소 전체.
경계 밖 수정이 필요하면 우회하지 말고 **`BLOCKED_CONTRACT` 로 정지**한다.

## 5. 수용 기준 — 양방 테스트 (작업 규율 3)

`brain-health.ps1` 안에 이미 `Assert-SelfTest` 자체검증 하네스가 있다(417~474행 부근).
**신규 검사도 같은 하네스에 넣는다.** 별도 파일을 만들지 않는다.

**(가) 정상 통과 — 오탐 0**
1. URL + Markdown 인용 있는 절 → 적발 **안 됨**.
2. URL + `[추론]`(또는 `[확인불가]`·`[로컬실측]`) 태그 있는 절 → 적발 **안 됨**.
3. URL 이 코드 펜스·백틱 안에만 있는 절 → 적발 **안 됨**(기존 `Remove-MarkdownCode` 재사용).
4. 기존 `official_without_quote` 자체테스트 3종이 **그대로 통과**(완화 0 실증).

**(나) 결함 차단**
5. URL 있고 인용·태그 **둘 다 없는** 절 → 신규 키에 적발됨.
6. 이 케이스가 **교정 전 코드에서는 적발되지 않음**을 먼저 보인다(구멍의 실재 증명).

**교정 전 RED 실증 의무**: 6번을 교정 전에 돌려 "적발 0"이 나오는 것을 확인하고 그 출력을 보고에 적어라.
그걸 못 보이면 이 수정이 무엇을 고쳤는지 증명되지 않는다.

### 5-3. 실행 결과 대조 (감사기는 스스로를 증명해야 한다)

수정 후 **실제 vault 에 대해 `brain-health.ps1` 을 실행**하고:
- 신규 키 적발 목록이 §2-4 의 **6건과 일치하는지** 대조한다. 다르면 그 차이를 보고한다.
- 6건 각각을 **눈으로 열어** 진짜 위반인지(근거로 쓰인 URL) 오탐인지(단순 참고 링크) 분류해 표로 낸다.
  → 오탐이 있으면 그 유형을 §3-1 조건에서 제외할 수 있는지 판단해 **제안만** 하고 임의 완화는 하지 않는다.
- `status`·`errors`·`exit code` 가 **수정 전과 같은지**(`ok` / `[]` / `0`) 확인한다. 달라지면 §3-2 위반이다.

## 6. 검증 명령 (전부 실행 · 증거 필수)

```
pwsh -NoProfile -File C:\Users\pc\AI-Brain\_scripts\brain-health.ps1
```
- 자체테스트가 스크립트 안에서 돌므로 **실패 시 그 자리에서 드러난다.**
- 통과 기준: 자체테스트 전건 통과 + `status: ok` + `errors: []` + **exit 0** 유지.
- 신규 warning 이 추가된 것 외에 기존 warning 6건 구성이 **비악화**여야 한다.

```
git -C C:\Users\pc\AI-Brain status --short
```
- 통과 기준: **`_scripts/brain-health.ps1` 한 줄만** 나와야 한다(정본 노트 변경 0 실증).
- commit·push **금지**. 변경은 워킹트리에 남긴다.

## 7. 정지 조건 (BLOCKED_CONTRACT / BLOCKED_ENV)

- §0 접근성 확인 실패 → `BLOCKED_ENV`
- allowed_files 밖 수정이 필요해질 때 → `BLOCKED_CONTRACT`
- 기존 자체테스트를 고쳐야 통과할 때 → **고치지 말고 정지**(완화 신호다)
- 신규 검사가 6건을 크게 넘겨 적발할 때 → 오탐 폭발이므로 정지 후 실측 보고
- commit·push·배포가 필요해질 때

## 8. 산출물

- `CODEX_IMPLEMENTATION_REPORT` — 실행 명령 + 출력, **교정 전 RED 실증**, §5-3 대조표(6건 분류),
  exit code 비교, 미검증 항목 분리 명시.
- 커밋 금지. 운영자 checkpoint 대기.
- 보고는 이 저장소 `implementation-notes.md` 최상단에 쓴다(대상은 vault 지만 인계 기록은 여기에 모은다).

## 9. 리스크 메모

- **감사기를 고치는 일이라 리뷰가 이중으로 요구된다** — vault 규칙 *"감사·검증 도구도 스스로를 증명해야
  한다"* + [[게이트는-위반-케이스로만-검증된다]]. 그래서 §5 (나) 6번의 교정 전 RED 가 핵심 증거다.
- 이 태스크는 sajugen 제품 코드와 **무관**하다. `sajugen/**`·`tests/**` 를 건드리지 않는다.
- 적발 6건의 **인용문 보강은 이 패킷 범위 밖**이다. 감사기가 잡게 만드는 것까지가 목표다.
