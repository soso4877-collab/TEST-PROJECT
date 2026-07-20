# TASK_PACKET — 명리 일간 성격 정본(docs/25) 배선 + 다단 인과 (1e)

- task_id: `ilgan-personality-wiring-20260720`
- base_commit: 활성화 시점 HEAD `4837605`
- 구현자: **Claude 직접 구현**(운영자 승인) — Codex는 신선 read-only 검증자
- 상태: `review_requested / next_actor=codex`
- 정본: `docs/25-ilgan-personality-research.md`(운영자 canon 승인 2026-07-20)
- 로드맵: 말투 개편 Stage 1 항목 1e(성격 다단 인과 + 명리↔자미 사실특정 겹쳐읽기)

## 0. 역할·금지 경계
- Codex read-only(수정·구현 금지). 상시 금지: PDF 재생성·LLM/API·commit·push·deploy.
- 검색은 ignored 제외 글롭. 실행은 `.\.venv\Scripts\python.exe -m ...`. calc/input 무변경.

## 1. 배경
명리 성격 서술이 라벨 위주이고 **10천간 일간별 고유 성격 테이블이 없었다**(오행 수준만). 예시(사람
상담가)의 "일간+신강 → 기질 → 반복 행동" 다단 인과가 부재. ★ 자미 化氣(A급)와 달리 **일간 물상 성격은
B급**(물상론 통속 해석)이라 문안은 비단정("경향·갈래")이어야 한다(docs/25 신뢰도 고지).

## 2. 목표(관측 가능)
1. 명리 성격을 **다단 인과**로: 일간 성격 → 신강/약이 그 결을 어느 방향으로 → 십성 겉/속 → 신살 색 → 적성.
2. **없는/약한 오행 = 결핍↔갈망 양가**(중립 여백 아님).
3. **명리↔자미 사실특정 겹쳐읽기** 강화(`_LAYER_WEAVE` 제네릭 → 구체 결론 대조).
4. 물상 성격 B급 → **비단정** 톤. 사실 슬롯(간지·십성·신강)·factcheck·GATE_KEYS·calc 불변.

## 3. 구현(실측 대상)
- 신규 `sajugen/content/myeongni_persona.py` = docs/25 단일 소스: `GAN_PERSONA`(10천간 상징·core·shadow)·
  `SINGANG_MODIFIER`(신강/신약/중화 결 발현 방향)·`ELEM_LACK`(오행 결핍↔갈망 양가). 정본 밖 성격어 생성 0.
- `rules.py`: import + `_ilgan_persona_parts(dm, dm_ko, singang)` 헬퍼(문형 `_pick` 3종·`_J` 조사). `character`
  골격을 다단 인과로 재배선(일간 성격 lead → 신강 modifier가 '이 결'을 방향으로). `strength` 골격의 없는 오행
  중립 처리를 정본 양가로 교체.
- `llm_sections.py`: `_COMPOSE_GUIDE["nature"]`에 다단 인과 + 없는 오행 양가 + 물상 비단정 지시. `_LAYER_WEAVE`
  사실특정 확증으로.
- `docs/03` 결정표(자미 행 아래) + `docs/25`.

## 4. 계약(불변 — 검증 포인트)
- **사실 슬롯 불변**: 간지·십성·신강·오행분포는 엔진 계산. 성격 '의미'만 content. factcheck 로직·토큰 완화 0.
- **비단정(B급)**: 물상 성격을 법칙으로 단정 금지("~한 경향·갈래·보곤"). safe/style/quality/customer_meta 완화 0.
- **GATE_KEYS·render/verify·calc/input 무변경**. golden count 비감소(성격 서술 바이트 변경 예상·허용).
- docs/25 §1 → 코드 매핑: `symbol`은 1:1 동결, `core/shadow`는 §1 축의 **관형형 대표 서술**(docs/25 §1
  '코드 배선 매핑' 승인) — 축 삭제·왜곡 금지.
- **신약 '약함 아님' 재서술은 strength 골격 전담** — modifier가 침범해 한 챕터에서 이중 서술 금지(회귀 테스트).

## 5. 검증(구현자 실측 — Codex 재확인)
- 전체 `pytest tests\ -q` exit 0·**기준선 1126/4 비감소**+신규, golden 28. 변경/신규 파일 Ruff·py_compile·
  diff-check exit 0. calc/input diff 0.
- 신규 `tests/test_myeongni_persona.py`(11): 10천간 전수·docs/25 상징 오라클·**core 축 앵커**·데이터 순정+
  비공허성·신강 modifier 분기·**신약 재서술 무중복 회귀**·없는오행 양가·character 다단 인과 비-no-op·persona
  문안 style 격리·비단정 톤·fail-closed.

## 6. Codex 검증 포인트
- docs/25↔myeongni_persona 정합(symbol 동결·core/shadow 승인 매핑 범위). 사실 슬롯 불변. 정본 밖 성격어 유입 0.
- 가드/게이트/calc 완화 0. **신약 재서술 무중복**(nature=character+strength). 비단정 톤. golden·기준선 비감소.

## 7. 후속
Codex read-only PASS → 운영자 commit → **1c**(폴백 골격 품질) → 1b(회고 검증, 보상 lint 선행) → Stage 1
완료 → 유료 1회 재측정 → Stage 2 판단. (§3 십성 성격 심화 `SS_PERSONA`는 docs/25 §8대로 후속.)
