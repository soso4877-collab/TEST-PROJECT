# 13. 풀이 설계 — 검증된 심리·마케팅 근거

> 작성 2026-06-11. 운영자 지시: "AI 어플 출력"이 아니라 "사람 상담가가 쓴 책" 느낌. 검증된 심리·마케팅 기법을
> 풀이 톤·PDF 디자인·목차·배치에 적용. 말투 느낌만 참조(예측 주장 차용 금지 — §11·§12 가드 유지).

## 적용 원칙 (근거 + sajugen 적용)

1. 내러티브 트랜스포테이션 (Green & Brock 2000; Wiley/ScienceDirect 메타분석)
   - 흐르는 이야기는 반론(counterarguing)을 줄여 몰입·믿음↑. 단 판매 의도가 노골적이면 신뢰 붕괴.
   - 적용: 전 챕터 상담체 산문, 독자를 주인공으로 이름 호명, 광고 톤 배제.

2. 처리 유창성 (Reber·Schwarz; renascence.io·tandfonline)
   - 유창하게 읽히면 진정성·신뢰↑. 명조(serif)=전통·권위, 넉넉한 여백=신뢰, 빽빽함=과부하.
   - 적용: 본문 명조 + 넓은 여백·행간 + 균일 서체. 기술 메타·각주 노출 최소화.

3. AI가 로봇처럼 느껴지는 이유 (Paperpal·NaturalWrite)
   - 예측가능·단조 구조, 불릿 리스트, 고유 목소리 부재가 'AI' 신호.
   - 적용: 불릿·번호·대괄호 라벨 전면 제거, 문장 길이·리듬 변주, 챕터 LLM 작성으로 고유 목소리 확보
     (결정론 룰은 고객마다 동일 패턴 → 그 자체가 AI 신호 → §15 개정으로 챕터 작성 확대).

4. 피크엔드 + 계열위치 (Kahneman·Fredrickson; yukaichou.com)
   - 처음·끝이 기억을 지배, 약한 끝은 두 배 페널티.
   - 적용: 따뜻한 이름 호명 도입(primacy) → 신청 질문 답변을 후반 강한 위치(감정 피크) → 격려로 마무리(recency·peak).

5. 바넘효과 역이용 (Forer; thedecisionlab)
   - "나를 위해 쓴 것"이라 믿으면 정확하다 느낌. 점쟁이의 모호함이 아니라 실제 명식+실제 상황의 구체성으로 윤리적 개인화.
   - 적용: consult 챕터에 고객 실제 상황을 사실 슬롯과 함께 녹임. §11 적중 주장 금지는 유지.

6. 노동착시 (Buell·Norton, HBS 2011)
   - 노력·깊이 신호가 가치 인식↑.
   - 적용: 서론(사주란)·목차·용어 부록은 필러가 아니라 가치 장치. 깊이 있는 챕터 구성.

7. 정보격차 호기심 (Loewenstein 1994, CMU)
   - 답을 모르는 질문이 활성화되면 끌림.
   - 적용: 목차의 챕터 제목을 작은 질문형("나의 사랑에 대하여"·"시간의 흐름에 대하여"·"신청하신 질문에 대하여").

8. 직접반응 카피 (2인칭·권위·스토리)
   - 확신 있는 상담가 목소리·"~님"·서사가 신뢰·몰입↑.
   - 적용: 톤 가이드에 반영. 단정·보장은 §12 safe_lint로 차단(권위 톤 ≠ 단정).

## 출처
- Green & Brock; Wiley(Thomas 2024)·ScienceDirect(Green & Appel 2024) — 내러티브 트랜스포테이션
- renascence.io(fluency heuristic)·tandfonline(disfluent typography) — 처리 유창성·서체
- Paperpal·NaturalWrite — AI 텍스트 로봇성
- yukaichou.com·Wikipedia — peak-end/serial position(Kahneman·Fredrickson)
- thedecisionlab·Forer 1949 — 바넘효과
- HBS Buell & Norton 2011, Management Science — 노동착시
- CMU Loewenstein 1994 — 정보격차 호기심

## 가드와의 관계 (완화 아님)
이 기법들은 '표현·구조·배치'에만 적용한다. 사실(간지·계산)은 결정론 엔진 산출만 사용하고, 모든 LLM 출력은
3단 가드(safe_lint §12 / factcheck 사실슬롯·연도 / trace 그라운딩) 재검증 + APPROVED 게이트를 통과해야 발송된다.
권위·확신 톤은 단정·보장·적중 주장과 구별된다(전자 허용, 후자 §11·§12 하드 차단).
