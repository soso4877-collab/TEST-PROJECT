# README-ops — sajugen 운영자 런북

사주(명리 메인) + 자미두수(보완) 종합 PDF 리포트 생성기. **운영자 1인 내부 도구.**
입력 → 진태양시 보정 → 결정론 계산 → 룰 NLG + 부분 LLM → 3단 가드 → tagged PDF →
관리자 검수 후 **수동 발송**. (정책·불변규칙: `CLAUDE.md`, `.claude/rules/`, `docs/`)

---

## 1. 설치 (최초 1회)

```
# 가상환경 + 의존성
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt   # 또는 pyproject 기준 설치
./.venv/Scripts/python.exe -m playwright install chromium       # tagged PDF 렌더 엔진
```

**별도 설치 자산(레포 미포함 = .gitignore):**
- `sajugen/tools/` — 포터블 veraPDF + JRE 21 (약 288MB). PDF/UA 검증 측정용(빌드 불차단).
  미설치여도 PyMuPDF 게이트로 대체 동작.
- `sajugen/assets/ephemeris/de440s.bsp` — Skyfield 절기 계산용 천체력.
- `data/kasi_cache.sqlite` — KASI 음양력·절기 캐시. 아래 명령으로 생성:
  ```
  ./.venv/Scripts/python.exe scripts/kasi_dump.py     # data.go.kr 인증키 필요(음양력 15012679)
  ```
  음력/윤달 입력의 1차 기준. **미구축 시 음력 변환은 lunar-python(중국 기준) 폴백 + 경고.**

**환경변수(선택):**
- `ANTHROPIC_API_KEY` — LLM 윤문/챕터 작성용. **없으면 자동 룰 폴백(비용 0·결정론).**
  공식 Anthropic API만 사용(웹 UI 자동화 금지 — 절대규칙 14).

---

## 2. 기동

```
# 웹폼 + 검수 화면
./.venv/Scripts/python.exe -m uvicorn sajugen.app:app --host 127.0.0.1 --port 8765
#   홈:        http://127.0.0.1:8765/
#   검수 화면: http://127.0.0.1:8765/admin   (접수·검수·승인·발급)

# CLI 단건 생성
./.venv/Scripts/python.exe -m sajugen.cli gen \
  --birth "1990-05-20 14:30" --gender 남 --name 홍길동 \
  --horoscope 2026-06-01 --out report.pdf
#   음력: --lunar  /  음력 윤달생: --lunar --leap  /  생시 미상: 시각 생략("YYYY-MM-DD")
```

산출 PDF/HTML: `sajugen/render/out/` (재생성 가능 = .gitignore).

---

## 3. 일상 운영 루프 (검수 화면 기준)

```
접수(RECEIVED) → 정규화 → 계산(CALC_OK) → 초안(DRAFTED) → 검수(IN_REVIEW)
  → 승인(APPROVED) → 발급(DELIVERED)
```

- **APPROVED(관리자 승인) 전 최종 발급 불가** — 상태머신이 물리 차단(절대규칙 16).
- 계산 3원 교차 불일치 시 `CALC_MISMATCH`로 차단 — 임의 진행 금지.
- 모든 전이·발급·수정은 `audit_log`에 기록.
- **발송은 수동.** 발급된 PDF를 운영자가 직접 고객에게 전달.

---

## 4. 주문 파기 (개인정보 — 필수)

주문에는 생년월일·출생지·고민 원문(개인정보)이 저장된다. **발송 완료·보유기간 경과 시
개인정보보호법 제21조에 따라 지체 없이 복구불가 파기**해야 한다(미이행 과태료 최대 3천만원).

```
# 미리보기(삭제 안 함)
./.venv/Scripts/python.exe -m sajugen.delete_order --order-id ord_XXXX
# 실제 파기(되돌릴 수 없음)
./.venv/Scripts/python.exe -m sajugen.delete_order --order-id ord_XXXX \
  --reason "발송 완료 파기" --yes
```

- orders 행을 하드 삭제(PII 복구불가), `audit_log`에는 PII 없이 파기 사실만 보존.
- `--reason`에 개인정보(이름·생일 등) 기재 금지.
- 고객의 삭제 요구(제36조) 대응 경로도 동일.

**엔진 개선용 데이터 = 익명 추출(파기와 병행).** 원본 PII 보존이 아니라 식별자를 제거한
계산특이점만 보존한다(제28조의2 연구·통계 / 제58조의2 익명 적용제외).

```
# 단건 추출(기본: 경계 케이스만, --all 로 전수)
./.venv/Scripts/python.exe -m sajugen.insight extract --order-id ord_XXXX
# 전체 스윕
./.venv/Scripts/python.exe -m sajugen.insight sweep --all
# 파기와 동시에(extract-then-purge)
./.venv/Scripts/python.exe -m sajugen.delete_order --order-id ord_XXXX \
  --extract-insight --reason "발송 완료 파기" --yes
```

산출: `data/calc_insights.jsonl`(이름·출생지·고민·order_id 미포함). 입력(분단위)·4주·경계
플래그만 담겨 기존 골든 케이스와 동형 — 엔진 회귀/개선 후보로 사용.

---

## 5. 테스트 · 백업

```
# 전체 회귀(커밋 전 GREEN 필수)
./.venv/Scripts/python.exe -m pytest tests/ -q
```

- git 브랜치/커밋/푸시 규칙은 `CLAUDE.md`의 **"## Git 컨벤션"** 절 참조
  (main=안정 베이스라인 / feat=작업, Phase 완료 시 fast-forward, 한국어 Conventional Commit).
- DB(`data/orders.sqlite`)는 .gitignore 대상 — 백업은 파일 복사로 별도 관리.
