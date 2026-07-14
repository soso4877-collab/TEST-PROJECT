# 20. 게이트 커버리지 매트릭스 + 프록시 레지스트리 (Phase 3, C3/C5)

> 이 문서는 **테스트된 산출물**이다(prose 가 아님). `tests/test_gate_registry.py` 가 아래
> "GATE_KEYS 레지스트리" 표를 live `sajugen.render.verify.GATE_KEYS` 와 **양방** 대조한다:
> 모든 GATE_KEY 는 표에 행이 있어야 하고(미문서화 → RED), 표의 모든 게이트 행은 live
> GATE_KEY 여야 한다(팬텀 행 → RED). 게이트 키를 추가/제거하면 이 표를 함께 고쳐야 한다.
>
> 배경(C3 사각·C5 프록시-물리 괴리): gate_pass=true 인데 육안 불합격이 반복된 실사고
> (QI-2026-07-02-01/02). 원인 = (a) 어느 문서 부위가 어떤 게이트로 덮이는지 지도가 없어
> 사각을 못 봄, (b) 대다수 게이트가 '추출 텍스트'라는 프록시를 재므로 물리(시각) 결함을
> 놓침. 이 문서가 (a) 커버리지 지도와 (b) 물리/프록시 분류를 명문화한다.

## GATE_KEYS 레지스트리 (verify.gate_pass AND-체인 SSOT — 22키)

각 행: 게이트 키 · 검증 대상 · 유형 · 측정면(물리/프록시) · 알려진 괴리/스코프.
유형 = structural(PDF 구조) / lint-text(추출 본문 텍스트) / lint-specs(런타임 스펙 필요) /
geometry(레이아웃 기하) / calc(계산 정합) / aggregate(복합).

| gate key | 검증 대상 | 유형 | 측정면 | 알려진 괴리·스코프 |
|---|---|---|---|---|
| `text_layer_ok` | 추출 텍스트 ≥1500자(통이미지 차단) | structural | 물리 | — |
| `fonts_embedded` | 폰트 임베드(번들 OFL) | structural | 물리 | — |
| `tagged` | StructTree/MarkInfo 태그 | structural | 물리 | veraPDF 7.1-3 잔존(별도 추적) |
| `markdown_clean` | md 잔재(#·```·---) 0 | lint-text | 프록시 | 추출 텍스트 기준 |
| `daewoon_consistent` | 대운 나이·간지 정합 | calc | 물리 | 결정론 계산 대조 |
| `quality_clean` | quality_lint(반복·빈말·일반론) | lint-text | 프록시 | — |
| `temporal_clean` | temporal_lint(지난 달 시제) | lint-text | 프록시 | ref_year/ref_date 어댑터 필요 |
| `no_orphan` | 저글자 독립 꼬리 페이지 0 | geometry | 물리 | 페이지 텍스트 기준(<40 orphan·<90 꼬리) |
| `loanword_clean` | 외래어 hard-ban(본문구역) | lint-text | 프록시 | 부록 용어집 제외(allowed_section) |
| `raw_calc_head_clean` | 표제형 날것 계산어(본문구역) | lint-text | 프록시 | 부록 정의 제외; headword 한정 |
| `unknown_time_provenance_clean` | 생시 미상 provenance·시주/자미/정오 잔재 | aggregate | 프록시 | `three_pillar`일 때 cover·toc·본문·appendix 전역 + 최종 발급; known은 비적용 |
| `client_register_clean` | 상담가 화자 register hard 규칙(고객 가시 전역) | lint-text | 프록시 | cover·toc·본문·appendix 포함; warning은 gate 비편입 |
| `customer_meta_clean` | AI/meta/문서 자기지칭(본문 페이지) | lint-text | 프록시 | 표지·목차·부록 제외 |
| `placeholder_residue_clean` | placeholder/마스킹 잔재 | lint-text | 프록시 | — |
| `style_clean` | 시맨틱 style_lint(반복 패턴) | lint-text | 프록시 | 본문 페이지 한정 |
| `role_perspective_clean` | 수신자 관점(integrated_full) | lint-specs | 프록시 | receiver specs 필요 |
| `honorific_consistency_clean` | 존칭 일관(integrated_full) | lint-specs | 프록시 | specs 필요 |
| `name_policy_clean` | 전체 이름 반복(H1.5.3) | lint-specs | 프록시 | full_names 전달 시만 |
| `identity_role_clean` | 일간 role 오서술(H1.5.3) | lint-specs | 프록시 | identity 전달 시만 |
| `singang_role_clean` | 신강약 group/role(H1.5.3.2) | lint-specs | 프록시 | singang 전달 시만 |
| `delivery_quality_clean` | 납품 품질(분량·축·자미·직답) | aggregate | 프록시 | delivery_quality.analyze |
| `layout_geometry_clean` | 좌우 여백·넘침 등 기하 | geometry | **물리** | 시각 결함 반복 차단(QI-2026-07-02-02) |

### 컴포즈 단계 벨트(게이트 AND-체인 밖 — 생성 시 하드 차단, 실패 시 룰 폴백)
| 벨트 | 검증 | 비고 |
|---|---|---|
| `safe_lint` | §12 안전표현(예측 단정·결과 보장) | 룰·LLM·관리자 수정분 전수 |
| `factcheck` | 사실 슬롯 외 간지·별·수치 생성 차단 | allowed_tokens 기준 하드 차단 |
| `trace` | 그라운딩(근거 슬롯 대조) | 근거 밖 사실 금지 |
| `customer_policy_lint` | register hard·외부 도메인 사실/절차 조언 | 후보·재작성·룰 골격과 최종 섹션 재집계; `GuardReport.clean` 편입 |

## 커버리지 매트릭스 (문서 부위 × 게이트)

행 = 고객이 보는 문서 부위, 열 = 그 부위를 실제로 검사하는 게이트/벨트. "제외"는 의도적
스코프 제외(사유 명시) — 사각이 아니라 설계다.

| 문서 부위 | 구조(text/font/tag) | 텍스트 lint(loanword/raw_calc/register/customer_meta/style/quality/temporal) | specs lint(name/identity/singang/honorific/role) | 기하(no_orphan/layout_geometry) | delivery | 벨트(safe/fact/trace) |
|---|---|---|---|---|---|---|
| 표지(cover) | ✓ | register·unknown-time provenance ✓, 나머지 제외 | 제외 | layout ✓ | 제외 | 생성 시 |
| 목차(toc) | ✓ | register·unknown-time provenance ✓, 나머지 제외 | 제외 | layout ✓ | 제외 | 생성 시 |
| intro(1장) | ✓ | ✓ | ✓(전달 시) | ✓ | ✓ | ✓ |
| 각 해석 장 | ✓ | ✓ | ✓(전달 시) | ✓ | ✓ | ✓ |
| consult(질문 답변) | ✓ | ✓ | ✓ | ✓ | ✓(직답 게이트) | ✓ |
| 장 제목 | — | customer_meta ✓ | — | layout ✓ | — | 생성 시 |
| 부록 용어집 | ✓ | register·unknown-time provenance ✓, loanword/raw_calc 등은 **제외**(정의 허용구역) | 제외 | layout ✓ | 제외 | — |
| 기하(전 페이지) | — | — | — | ✓(no_orphan·layout_geometry) | — | — |

## 프록시 레지스트리 (C5 — 신규 검증은 물리 측정 우선)

**원칙**: 위 표의 "측정면=프록시" 게이트는 *추출 텍스트*를 재는 것이지 고객이 보는 *물리
페이지*를 재는 게 아니다. 둘이 어긋나면(표지/목차가 물리 초반을 차지, 시각 넘침, 이미지-텍스트
겹침) 프록시는 PASS 인데 육안 FAIL 이 난다(QI-2026-07-02-01/02 의 실체). **신규 검증을 설계할
때는 물리 측정(레이아웃 기하·페이지 단위·300dpi 시각)을 프록시(텍스트 매칭)보다 우선한다.**

| 분류 | 게이트 | 알려진 괴리 |
|---|---|---|
| 물리(신뢰 높음) | text_layer_ok·fonts_embedded·tagged·daewoon_consistent·no_orphan·layout_geometry_clean | — |
| 프록시(텍스트) | markdown/quality/temporal/loanword/raw_calc_head/unknown_time_provenance/client_register/customer_meta/placeholder/style/specs·delivery | 추출 텍스트↔물리 레이아웃 괴리: 순서·위치·시각 결함 미포착 |
| 최종 방어 | 운영자 육안(300dpi, 다이어트 체크리스트 ≤7항목) | 자동 게이트가 못 재는 미감·몰입·물리 배치 |

## 열린 품질 차원 책임표

GATE_KEYS 양방 일치는 **등록된 게이트의 배선 완전성**만 증명한다. 아직 이름 붙지 않은
품질 차원을 모두 덮었다는 뜻이 아니다. 신규 Z는 아래 표에 새 행을 만들고 생성 제약·하드
게이트·advisory·사람 검수를 함께 연결한다.

| 품질 차원 | 생성 제약 | 하드 게이트 | advisory | 최종 오라클 |
|---|---|---|---|---|
| 상담가 화자 register | docs/14 프롬프트·룰 골격 | `client_register_clean` hard만 | hsweep narrator lens | 운영자 육안 Z |
| 외부 도메인 사실·절차 | docs/14 consult 경계 | `delivery_quality_clean/external_domain_advice` | hsweep direct-answer lens | 운영자 육안 Z |
| 어려운 사주 용어 이해 | 첫 등장 즉석 풀이·기능적 비유 | 하드 게이트 없음(오탐 방지) | warning·합성 holdout | 운영자 육안 Z |
| 생시 미상 사실 출처 | 세 기둥·12/12 불변 사실만 compose | `unknown_time_provenance_clean` | provenance 메타 검토 | 운영자 육안 Z |
| 시각·몰입·물리 배치 | 템플릿·골격 계약 | geometry·structure 게이트 | 300dpi 검수 보조 | 운영자 육안 |

> 폐기된 프록시(참고): `frontloaded_answer`/`physical_frontloaded_answer`(초반 1800자/물리 3쪽
> 직답 프록시)는 2026-07-05 운영자 지시로 폐기 — 1장 직답 문단 제거 + 직답은 consult 장 전담
> (docs/16). 프록시가 실제 품질과 어긋난 사례.

## 하네스 모듈 증거 계약

`integrated_full` 프로파일이 `modules`를 명시하면 아래 필드는 한 원자로 이동한다. 실제 운용값은
저장 주문의 PII-free render/module 메타에서 복사하며 본문이나 고객 식별값으로 재구성하지 않는다.

| 경계 | 필수 입력·출력 | fail-closed 조건 |
|---|---|---|
| profile | `modules`·`module_schema_version`·`module_sections`·`premerge_section_ids` | 빈/미등록 모듈, 현재 스키마 불일치, 두 커버리지 증거 누락·형태 오류 |
| hverify | profile `modules`를 `selected_modules`로 바꾸고 두 커버리지 증거와 함께 `verify()` 전달 | 세 증거 중 일부만 전달, verify 응답의 선택/스키마 불일치 |
| hrun argv | 명시 모듈마다 반복 `--module <id>` | profile 계약 실패 시 subprocess 진입 전 차단 |
| hsummary | `selected_modules`·`module_schema_version`·`minimum_pages`·`minimum_text_chars` | 제품 enum 밖 모듈 ID나 비정수 하한은 요약에서 제외 |

`modules`가 없는 레거시 프로파일만 선택 기능 이전의 5모듈 전체 계약을 사용한다. 이때 hverify는
세 인자를 모두 `None`으로 전달하고 제품 정본이 5모듈·30쪽·10,000자를 복원한다. 명시 프로파일의
증거 누락을 이 레거시 분기로 보정하는 것은 금지한다.
