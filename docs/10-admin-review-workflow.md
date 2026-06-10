# 10. Admin Review Workflow

> 최초 작성: 2026-06-10. 구현: Phase 4(상태머신)+Phase 6(UI)

## 상태 머신 (강제)
RECEIVED → NORMALIZED → CALC_OK | CALC_MISMATCH(차단) → DRAFTED → IN_REVIEW → APPROVED → DELIVERED
- 규칙: APPROVED 이전 최종 PDF 발급 함수 호출 불가(예외 발생, 테스트 단언). CALC_MISMATCH/NEEDS_INFO는 관리자 해소 액션 전 진행 불가. 모든 전이 audit_log.

## 화면 명세 (FastAPI + Jinja, 1인 운영)
1. 주문 목록: 상태별 필터, 윤달/시진불명/절입경계/불일치 배지.
2. 주문 상세:
   - 고객 입력 원본 + 정규화 결과(음→양 변환 근거 포함)
   - 명리 핵심값: 팔자·대운 방향·격국·신강약·용신(참고 라벨)
   - 자미 핵심값: 명궁·신궁·오행국·생년사화 (시진불명 시 "자미 생략" 표시)
   - 교차검증 패널: 3원 소스별 값, 불일치 적색 경고
3. 섹션별 본문 패널:
   - safe_lint 매치 적색 하이라이트 / 반복 표현(n-gram) 황색 하이라이트 / LLM 생성 섹션 배지 + needs_review 표시
4. 액션:
   - 섹션 재생성: 룰 재빌드 / LLM 재윤문 / 톤 선택(담백형·상담형·고급형)
   - 직접 수정: 저장 시 가드 재검증(위반 시 저장 거부+사유 표시)
   - 승인 → 최종 PDF 렌더+verify 게이트 → DELIVERED 처리(수동 발송 후 클릭)
   - 반려: 사유 기록, DRAFTED로 회귀
5. 이력: 수정·재생성 전부 audit_log, 섹션 버전 diff 표시.

## 검수 체크리스트 (승인 버튼 옆 고정 표시)
- [ ] 교차검증 3원 일치 (불일치 시 사유 확인 완료)
- [ ] 고객 질문 답변이 evidence_slots 근거와 부합
- [ ] safe_lint 하이라이트 0건
- [ ] 윤달/시진불명 고지 문구 삽입 확인
- [ ] 이름·호명 오기 없음
- [ ] PDF 게이트 PASS(텍스트레이어·폰트·태그)
