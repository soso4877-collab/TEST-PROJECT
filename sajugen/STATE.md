# sajugen 진행 상태 (SSOT) - 세션 시작 시 이 파일 먼저 읽기

> 컨텍스트가 비워져도 이 파일만 읽으면 그대로 이어갈 수 있다.
> 계획 전문(현행): C:\Users\pc\.claude\plans\role-claude-distributed-hellman.md (상용화 플랜, 2026-06-10 승인)
> 계획 전문(구): C:\Users\pc\.claude\plans\quirky-wibbling-wind.md
> 정책 문서: C:\Users\pc\test-project\docs\00~10 (research ledger·유파 결정·LLM 정책·검수 워크플로우)
> 영속 메모리: ~/.claude/projects/C--Users-pc-test-project/memory/ (MEMORY.md 인덱스)
> 최종 갱신: 2026-06-14  (베타 재정비 Phase A+B 완료. A=브랜드 서담선생 기본+자유입력 / 가정어 제거(세운
>   연도 앵커)+style_lint 가드. B=챕터 간 일주 자기소개 반복 해소: 프롬프트(소유권)+rules ilgan 골격 근원수정
>   +결정론 백스톱 content/repetition.py(소유 챕터 wonguk 외 짧은 자기소개 줄 제거). 베타 v5 실측 일주
>   자기소개 2·3회→1회, 가정어 0. pytest 162 PASS. C(저장·재사용, 보존정책 선행)·D(promptfoo) 보류.
>   재정비 플랜: ~/.claude/plans/subprocess-run-recursive-rivest.md)

## 한 줄 상태
사주 PDF 생성기(sajugen) 핵심 빌드 + 디벨롭1·2·3 완료(pytest 34 PASS).
2026-06-10 상용화 플랜(Phase 0~8) 승인: KASI 3원 검증층 + 음력/윤달 입력
+ 자미 유파 정책 + 부분 LLM 4구간(공식 API) + 주문 상태머신 + 검수 UI.
Phase 0(docs)·1(KASI)·2(음력입력)·3(자미 유파/동등성)·4(주문 상태머신) 완료.
P1(2026-06-10): 키 발급·전수 캐싱(음양력 1900~2050 + 절기 2000~2027)·3원 교차·KASI 결함 3건 문서화.
P2(2026-06-11): input/normalize.py 음력→양력(KASI 역조회 1차)·윤달·한·중 상이 경고, CLI/웹폼 --lunar/--leap.
P3(2026-06-11): iztro_py↔iztro JS 100건 동등성 — 구조(배치·사화·명신궁·오행국) 불일치 0, 밝기만 판본차(known-diff).
  config/rule_profile.yaml 유파 외부화(sajugen/config.py 로더), 연경계=正월一일·사화표=iztro기본 확정.
P4(2026-06-11): models/report.py(Unified JSON, docs/04 round-trip) + store/orders.py(상태머신
  RECEIVED→…→DELIVERED·SQLite·audit_log, APPROVED 전 issue_final_pdf 차단=절대규칙16). test_orders 8 PASS.
신살보강(2026-06-11): 만세력 대조(docs/11 케이스#1)에서 발견한 신살 간극을 조사·보강.
  docs/12-shinsal-research.md(권위 출처 교차검증, 간극=정확도 아닌 채택범위·표시구조·기준축 차이,
  엔진 7종 대부분 A등급, 괴강만 고전 4주설과 차이=known-diff). calc/shinsal.py 신설(레지스트리·기둥별·
  공망 자체산술·12신살), 길신 7종 확장(문창·학당·금여·암록·태극·천문·고신·과숙). config myeongni_shinsal
  (괴강범위·삼합축both·12신살축day_zhi·공망표기). content/rules.py 문안 계층(기둥별·상한·공망·12신살 비단정).
  케이스#1 골든: 포스텔러 기둥별 신살 11종 재현·공망 일치. 전체 회귀 79 PASS.
대운수정(2026-06-11): 대운 시작나이 2년차 해결. lunar-python getStartAge()=起運연도 虚岁(케이스마다 +1~2
  드리프트)를 쓰던 버그 → start_age=대운수(getStartYear)+10*순번 으로 도출(calc/myeongni.py). 케이스#1
  6/16/26 레퍼런스 일치·daewoon_count 내부정합. 회귀 2건 추가. 한국관행=대운수=만나이=시작나이.
골든확장(2026-06-11): tests/test_golden_sweep.py 신설(22건). 독립 오라클·속성기반 검증으로 기댓값
  손대조 0 — 공망=lunar LunarUtil.getXunKong(60갑자 전수), 4기둥=iztro↔lunar, 대운방향=양남음녀,
  표=건록·제왕·육합 1차원리 재도출(양인·암록·금여) + 스냅샷, 12신살=독립 재구현. 결정론 격자 21차트 +
  명명 8케이스(순/역·남/여·대운수0·자시·입춘·윤달). 방법론 docs/12 §6. 전체 회귀 103 PASS.
Phase5 착수(2026-06-11): LLM 백엔드 결정 — 내 계정 API 키(상업, 규칙14 만족) 확정, 자체호스팅 로컬은
  제외(하드웨어 필요·의도 아님). 백엔드 2종(rule/anthropic). 1단계 룰폴백 골격 완료:
  content/question_router.py(QuestionCategory enum + 키워드 룰분류) + content/llm_sections.py
  (LLMBackend 프로토콜·RuleBackend·AnthropicBackend·get_backend, 무키→Rule). 기존 llm_polish/builder
  폴백·가드 패턴 재사용(미변경). test_llm_sections 6건. 전체 회귀 109 PASS.
Phase5 2단계(2026-06-11): 고객 고민 입력 배선 완료. cli --concern·웹폼 필드·pipeline·builder 관통.
  builder가 분류(use_llm+키=LLM, 아니면 룰)→카테고리→rules.build_all(concern_category)로 신규 'consult'
  섹션(신청 고민 라우팅, 카테고리→도메인 결, 비단정). 고객 원문은 본문 미주입(주입·PII 회피, 카테고리 enum만).
  Report23.concern_category 저장(감사). SECTION_SPECS +1(consult, source=[input]). test_llm_sections +3.
  전체 회귀 112 PASS. 다음: ANTHROPIC_API_KEY 준비 시 AnthropicBackend 실호출(구간2·3·4 본문 생성)·골든 A/B.
Phase5 3단계 키투입·실호출 스모크(2026-06-11): 운영자 ANTHROPIC_API_KEY 를 .env 에 저장(본인 계정,
  Claude Code 구독과 별개 과금). 코드 수정 0(pipeline 이 .env 자동로드, anthropic SDK가 키 자동인식).
  실측: get_backend()=anthropic, classify('이직')=JOB 실호출 정상. CLI --llm 1990-05-20 통합=게이트 PASS,
  19p·16,620자·tagged. 리포트 1건 윤문 실비용 = 입력45,722·출력18,298토큰 = $0.137(약 192원, Haiku4.5),
  1달러 미만 확정(절대규칙19 측정값). 윤문 23/30 성공·7 폴백. [발견] instructor 도구JSON 래핑이 긴 섹션에서
  max_tokens=1200 초과→IncompleteOutput→재시도후 룰폴백(기능 안전, 비용 약간 낭비)=4단계 보강후보.
  무키 회귀는 키 있어도 실호출 0(test_p3=polish 람다대체, test_llm_sections=delenv 격리).
Phase5 4단계 구간2·3·4 본문생성(2026-06-11): llm_sections 에 compose() 추가(Sonnet 4.6, _COMPOSE_SYSTEM
  +섹션별 _COMPOSE_GUIDE). builder _COMPOSE_SECTIONS={cross,consult,advice,closing} 는 use_llm+anthropic 시
  compose(근거 본문의 사실만, 새 간지·별 생성 금지), 그 외 섹션은 기존 polish. 둘 다 3단 가드 재검증·실패시
  룰 골격 폴백(기존 패턴 그대로). RuleBackend.compose=패스스루(무키 결정론). 고객 원문 미전달(카테고리 enum만,
  절대규칙17·PII). llm_polish max_tokens 1200->2000(긴 섹션 절단 폴백 감소). 실측: 4섹션 전부 생성·가드 통과
  (safe0/fact0), 분량 약 2배(cross225->739·consult252->390·advice480->928·closing259->594), 4구간 비용 99원.
  test_llm_sections +1(compose 패스스루). 전체 리포트(--llm) 실측: 가드 clean·생성20·폴백1(상향효과 7->1)·
  총비용 $0.176=247원(Haiku $0.11 + Sonnet $0.064). 전체 회귀 113 PASS.
풀이재설계(2026-06-12, 커밋 194ec2d): 운영자 "AI가 뽑아낸 것 같다·가독성 최악". 금강산 PDF=하한, 그 이상 목표.
  근본원인=템플릿 우선구조 → 결정론 룰을 '근거 자료'로, LLM이 전 해석 챕터를 사람처럼 작성으로 역전.
  - 한글 간지: _gz_ko '庚午(경오)'→'경오', 지장간·오행(_ELEM_KO)·격국·오행국(_oguk)·일간 한자 제거, 납음 본문 제외.
  - compose 재설계(llm_sections): instructor JSON→순수텍스트(절단·행 회피), _COMPOSE_SYSTEM 강화(한글간지·기호 전면금지·
    메타안내금지·시각자료 언급금지·비유·호명·금강산 이상), 전 해석챕터 가이드, max_tokens 6000, max_retries 8.
  - builder: 해석챕터 병렬 compose(ThreadPool 동시성3, ~수분), consult에 명식 사실 주입(답변거부 버그 해결),
    정적챕터 LLM 미적용, _clean_display 후처리(잔존 한자·줄머리 불릿·원문자·대괄호·화살표·첫째/둘째 산문화;
    '수면·식사' 무간격 가운뎃점 보존; factcheck 이후 적용→그라운딩 유지). "표/그림 보세요" 제거. 판권 후기/CTA 제거.
  - 회귀앵커 테스트(비정적 챕터 한자·기호 0). 무키 폴백도 항상 깨끗. 계산·콘텐츠 93 PASS. calc/ 무수정.
  - 실측(1990-05-20): 본문 한자0·기호0·잘림0. 작성챕터=금강산 이상(비유·호명·한글간지). 비용 ~$0.5~0.9/건.
  [완료 2026-06-12, 커밋 32ef29b] compose 신뢰성 = polished 12/12·fallback 0 달성. 진단 로깅으로 진짜 원인
      규명: 폴백은 API 오류/속도제한이 아니라 §12 가드 실패(LLM이 가끔 '반드시' 단정어 사용)였음 — 내 가설
      (순차/백오프/큐)은 오진. 수정: (1) _COMPOSE_SYSTEM 에 safe_lint 금지어 명시, (2) builder 가드 실패 시
      1회 재작성→재검증→그래도 실패 시 룰 폴백(가드 전수 유지·우회 아님, factcheck 는 한자정리 이전). 실측 폴백0.
  다음 세션: (1) PDF 최종 생성 후 veraPDF/게이트 재측정·운영자 PDF 육안 A/B, (2) 폴백 시 룰 산문 풍부화(보강),
      (3) 검수 UI(store/orders APPROVED) 연결, (4) 다양한 케이스(여성·미성년·자미단독 등) 톤 점검.
  착수 전 필독 메모리: feedback-sajugen-llm-content-pitfalls(반복실수 체크리스트 — '로그로 원인 먼저' 가 이번에 적중).
대개편(2026-06-12, 플랜 quizzical-brewing-hejlsberg 승인·D1~C3 5커밋): 운영자 지시 = 금강산급 디자인 +
  샘플(웹AI 풀이) 수준 직설 말투 필수 하한 + 상대방 사주 포함 + '참고용·전문가와 상의' 류 문구 PDF 금지.
  - D1 폰트·타이포(5078314): 나눔명조 R/B 본문(금강산 동일 패밀리)+나눔브러시 표제(OFL 동반), 한자=
    SourceHanSerifK 스택 폴백. 좌측정렬·행간 1.72·문단 <p> 분할(빈 줄 호흡 보존). 마진 _PAGE_MARGIN 단일
    소스. [중요 발견] Playwright pdf()는 웹폰트 로딩 비대기 → 콜드 캐시에서 본문 글리프 통째 소실
    (13467→606자 실측) → document.fonts.ready 명시 대기로 해결. verify 한글 간지 토큰 인정.
  - D2 한지 배경·표지(0c12011): assets/hanji.svg 절차생성(시드 고정)+make_assets.py 로 낙관('사주명리'
    세로·붉은 이중테두리) 합성 → hanji_bg.jpg. CSS 캔버스 배경은 print 에서 마진·마지막 페이지 미도색
    실측 → PyMuPDF 전 페이지 언더레이(XObject 1회)로 풀블리드. 표지=붓글씨 표제+이름 필수+세로 표제 박스.
    목차=장 칩+대시 리더. 배경 픽셀 회귀앵커(test_p4).
  - C1 가드 완화(44e607d, 운영자 명시 지시=절대규칙12 단서): 단정 부사 단독 허용, 부사+결과동사 결합
    (보장 진술)만 차단. 적중·100%·의료/생사·운명론·보장형은 불변. test_safe_lint 신설(샘플 원문 허용 앵커).
  - C2 말투 재작성(6a1781e): docs/14-tone-spec.md(샘플 익명화+스펙 10항목). _COMPOSE_SYSTEM=단문 호흡
    (한 호흡 줄바꿈+빈 줄)·공감 미러링→핵심 직답→직설 사실→흐름→행동지침→격려·구어체 혼용·헤지 금지.
    rules 일주 동물·빛깔 슬롯(_gz_animal '검은 개'). 실호출 스모크: love 2382자·24문단·가드 0.
  - C3 상대방 사주(db63f88): input/partner.py(생년월일 감지·스팬), calc/partner.py(결정론 — 990118=
    무인 을축 경오 골든, 시미상=시주 제외, 십성=SHI_SHEN·천간합·육합/충·삼합 반합·부족오행 보완),
    rules.partner_block(파생값만, 원본 비전달), masking.py+compose(quoted_concern)=절대규칙17 a~d 구현
    (마스킹 인용블록, consult 한정). factcheck 한글 간지 검사 신설(접미 문맥 필수)+extra_ganzhi.
  - 고지 정비(운영자 지시): '참고용 상담 자료·전문가와 상의' 전면 제거, 감수 명시형(규칙18)은 유지,
    health=의료 비단정+'병원에서 확인' 자연 문구로 대체(test_p3 앵커 갱신).
  - 종합 실측(2026-06-12, 샘플 케이스 1989-01-02 07:40 여+상대 990118 질문): polished 12/12·fallback 0·
    가드 clean, 41p·26,020자·431KB, 게이트 GREEN, veraPDF failed=['7.1-3'] 비악화, 빌드 188s.
    consult=상대 경오일주·술오 삼합(화 살아남)·편인 끌림 설명 재현, 생년월일 비노출. 전체 pytest 125 PASS.
    산출물: sajugen/render/out/final_sample.pdf (운영자 육안 A/B 대기).
  운영자 확인 대기 2건: (1) 표지/낙관 표제 문구(현재 '사주명리'·'종합 사주 풀이' — 상품명 확정 필요),
    (2) 한지 질감 강도(현 SVG 절차생성 — 미달 판정 시 CC0 래스터 교체 경로 준비됨).
  다음 후보: 검수 UI 연결, 다양한 케이스 톤 점검, intro 인사말 1인칭 서명(운영자 브랜드) 추가.
2차 개편(2026-06-12, 운영자 1차 검수 피드백 반영, R1~R7 + 긴급 1건, 8커밋):
  - [긴급·431efbb] "지금은 2025년" 오서술 — m.seun=현재 대운 流年이라 과거 해 시작, ref_year 미전달 시
    골격이 과거 해를 '기준 해'로 폴백. 4중 방어(SajuResult.ref_year 보존→builder 기본값→rules '올해는
    {년}년' 닻+과거 세운 비노출→compose [기준 시점] 블록) + 회귀 앵커. 메모리 9-1 기록.
  - R1(d0d6261) 절대규칙 18 개정(운영자 명시 지시): 본문 산출방식 고지(자동 분석 도구·AI) 금지 —
    colophon='글을 맺으며' 맺음 서명 슬롯으로 재작성, disclaimer 중복 박스 삭제, 역앵커 테스트.
  - R2(7090084) 호명 강제: call_name('김수하'→'수하님' 성 제외·복성 처리), 룰 골격 '당신' 15곳 재작성,
    compose [호칭] 블록, CLI·웹폼 이름 필수화.
  - R3(aa0f4cc) '---' 마크다운 누출 차단(_strip_artifacts 수평선·불릿·인용 확장) + '첫째/먼저' 나열
    잔재 원천 제거(골격 4곳 산문화·치환 폐기) + 프롬프트 금지.
  - R4(cbce5c5) 타이포: 본문 11.5→14.5pt·행간 1.8·잉크 #111 (금강산 실측 15pt/순흑/행송28pt 근거).
    29p로 증가(노동착시 유리).
  - R5(1ecd6e8) 브랜드 가변화: config/brands.yaml 프로필(낙관·표지 표제·맺음 서명) + 낙관을 배경에서
    분리해 PyMuPDF 런타임 드로잉(나눔브러시 fontfile·subset). [돌파구·메모리 기록] PyMuPDF CIDFontType2
    CIDToGIDMap 누락→veraPDF 7.21.3.2-1 신규 실패→/Identity 주입(_fix_cid_to_gid)으로 해결.
  - R6(f21925d) 명리학틱 판식: 사주쌍변 광곽(매 페이지 이중 테두리 11/13mm 먹갈색)·어미(魚尾) 모티프
    (장 시작 인주색 SVG)·표지 정방 낙관(브랜드 2+2자)·--injoo 통일. 계선·능화문 배제(절제).
  - R7 docs/13 §9(바넘 수용 조절변수—Dickson&Kelly 1985)·§10(콜드리딩 구체화—Roe&Roxburgh 2013,
    모호함 차용 배제)·docs/14 11번(강점 선행·사실 토큰 풍부 호명) + 프롬프트 반영. p5 이름 필수화 반영.
  - 종합 실측(1997-10-27 09:46 남 서울, 풀 LLM): 丁丑 庚戌 壬寅 乙巳, polished 12/12·fallback 0·
    가드 clean, 50p·25,463자·560KB, 게이트 GREEN, veraPDF ['7.1-3'] 비악화, 288s.
    금지어 전수 0('당신'·'---'·'자동 분석'·'전문가와 상의'·과거연도 올해 오서술), 호명 '길동님' 확인.
    산출물: sajugen/render/out/final_19971027.pdf (운영자 검수 대기 — 이름은 임시 '홍길동').
  전체 회귀 133 PASS(테스트 14파일). 작업 원칙(메모리 feedback-debug-research-and-record): 오류=공식자료
    조사로 해결, 돌파구=즉시 메모리 기록.
3차 수정(2026-06-12, 운영자 2차 검수 — 낙관 깨짐·말투 하자 원인 보고 포함, F1~F4 + 7커밋):
  [원인 진단] (1) 낙관 깨짐 = PyMuPDF insert_text 텍스트 임베드 자체의 뷰어 호환성 구멍.
    내 검증(MuPDF·PDFium)은 관대한 엔진이라 통과 → 검증 사각. CIDToGIDMap 보정으로도 불충분.
    (2) 말투 하자 = 가드 3단이 사실·안전만 검사, 스타일은 프롬프트 지시뿐 검증 0 → 규칙 누설·
    시적 비유·기호 난발(— 52회·· 49회)·반복(기운 92회)이 통과.
  - F1(1361528) 낙관 이미지화: PyMuPDF 텍스트 임베드 전면 폐기 → make_assets.build_seal
    브랜드별 투명 PNG(Chromium 렌더·캐시) 삽입. 원칙 확립: PDF 텍스트는 Chromium 경로만,
    PyMuPDF는 벡터·이미지만(메모리 기록). 알파 PNG 무압축 저장 실측 → 4x 스케일.
  - F2+F3(5101db5) content/style_lint.py 신설(규칙 누설·em dash·가운뎃점·기호·시적 비유·
    반복 상한) → builder 가드 4번째 검사(재작성→폴백). 프롬프트 재작성(비유=오행 자연물
    하나만·규칙 침묵·반복 금지·줄표 금지), _COMPOSE_GUIDE '결' 어휘 정리(반복 유도 원천).
  - 기호 정규화 선반영(454faea): —·를 가드 전 결정론 변환(폴백 2→0), 구조 상한 12.
  - 기호 잔존 0(915dc5b): intro 제목 줄표·부록 불릿 14줄·합성어 가운뎃점 29곳 제거,
    _hanja_clean 가운뎃점 전부 쉼표화. 회귀 앵커(전 섹션 —·0).
  - 종합 실측(서담선생·태수님·1997-10-27): polished 12/12·fallback 0·clean, 44p·676KB,
    veraPDF ['7.1-3'], 231s. 전수 감사 전 항목 0(줄표/가운뎃점/당신/점수/메타발화/비유어),
    '기운' 92→23·'의 결' 49→2, 호명 103회. 전체 pytest 135+ PASS.
    산출물: sajugen/render/out/final_19971027_seodam.pdf.
4차(2026-06-12, G1~G4 + 오탐 수정 2건):
  - G1 뷰어 진단 종결: MuPDF·PDFium(Edge/Chrome)·pdf.js(Firefox) 3엔진 정상 — 깨짐은 Cursor
    내장 미리보기 한계(고객 영향 없음, 검수는 Edge/Acrobat). pdf.js 검증법 메모리 기록.
  - G2 폰트 업그레이드(c041682): 본문=고운바탕 R/B(OFL), 제목·표제·낙관=본명조 Bold(Adobe OFL).
    마루부리(라이선스 원문 미확보)·KoPub(임베딩 별도 승인) 기각. 송명(OFL)은 동봉만.
  - G3 가족 다중 명식(d775c16): 파서 다중·음력(KASI 변환)·한글 시각(오전/오후)·관계+이름 라벨,
    빌더 전원 주입(상한 4), partner_block 라벨·시주 조건부. 골든: 음1963-10-18→양1963-12-03.
  - 오탐 수정: (1) 반복 상한 길이 비례화(절대값이 4인 consult 정상 밀도 차단),
    (2) factcheck 한글 간지 동형 일상어(계신=癸申 등 7종) 제외 — '들어와 계신 시기' 차단 실사고.
  - G4 비용 계측(usage 토큰 집계)+신순자 생성: 음1972-05-20 09:30 여(양1972-06-30, 壬子 丙午
    壬辰 甲辰)+가족 3인. 최종 실측 polished 12/12·fallback 0·clean, 42p·732KB, 176s,
    Sonnet 12콜 in 56,770/out 22,996 = $0.515/건(약 700원, Haiku 분류 +1원 미만).
    API 외 비용 = 0원(KASI 무료키·폰트 전부 무료 라이선스·Playwright/PyMuPDF(AGPL, 내부도구
    비배포라 무료)/pypdfium2/veraPDF 무료 — 잔여는 전기뿐).
    산출물: sajugen/render/out/final_sinsoonja.pdf (서담선생 브랜드).
Phase6 검수 UI 1차 MVP(2026-06-13, 플랜 sleepy-sleeping-puppy 승인): 운영자 결정 = "완성 우선,
  이후 실주문 돌리며 풀이 디벨롭". 주문 접수→백그라운드 생성→검수→승인→최종 발급 루프를 /admin 으로 완성.
  - 신설: order_flow.py(오케스트레이션 — pipeline 은 store 를 모름, 전이는 전부 여기서.
    create_order=정규화+RECEIVED→NORMALIZED, run_generation=교차불일치 시 CALC_MISMATCH 차단(규칙7)/
    일치 시 CALC_OK→DRAFTED, 게이트실패·가드미클린=DRAFTED+needs_review(검수강화, 우회아님),
    edit_section=IN_REVIEW 한정+가드 재검증(safe_lint+factcheck 허용토큰+빈본문, 위반 시 저장거부),
    final_render_fn=항상 재렌더+verify 게이트(실패 시 예외→APPROVED 에 머묾=규칙16 비우회)),
    admin.py(APIRouter /admin — 목록 필터·상세·review/approve/reject/retry/deliver/섹션수정/PDF 다운로드,
    IllegalTransition·ApprovalRequired→409), web_templates/(admin_list·admin_detail, JS 없음·PRG·
    생성 중 meta refresh 5s. 주의: 최신 Starlette 은 TemplateResponse(request, name, ctx) 신형만).
  - additive 수정: GenResult+report/calc_consistent/input_civil, UnifiedReport+content/render_meta,
    Report23+allow_tokens(builder 가 계산시점 허용토큰 영속 — 검수 수정 재검증용, 상대방 간지 포함),
    factcheck.check_with_allow 추출(기존 check 위임), store busy_timeout=5000+list_orders+add_audit.
    커넥션은 요청마다 새로 열고 닫음(스레드 공유 금지). DB 경로 env SAJUGEN_ORDERS_DB(테스트 격리).
  - 장시간 생성 = FastAPI BackgroundTasks(sync→threadpool, Playwright sync 호환). 기존 POST /generate
    구형 경로 보존(주문 기록 없는 즉시 PDF), 홈에 /admin 링크.
  - tests/test_admin_ui.py 12건(happy path·승인전 발급 409=규칙16 회귀·반려·CALC_MISMATCH 차단·
    수정가드 4종·수정반영 발급 증명·needs_review·목록필터·신규필드 왕복). 전체 회귀 138 PASS.
  - 실경로 E2E(룰 경로 실측): 접수→DRAFTED→금지표현 수정 422→정상 수정 200→승인전 발급 409→
    승인→발급 200→DELIVERED. 최종 PDF 27p·12,655자, 검수 수정문 반영·호명 확인. audit 전체 기록.
  - [해결 2026-06-13] render/verify.py veraPDF subprocess.run에 encoding="utf-8", errors="replace"
    추가. Windows cp949 디코드로 인한 UnicodeDecodeError(리더 스레드) 제거 → veraPDF 측정 안정 복원
    (검증: verify() 반환 verapdf.available=True, 실패 clause는 알려진 7.1-3 1건만=비악화). 게이트
    로직·반환 구조 무변경(측정 영역 한정). 전체 tests/ 150 PASS 유지(회귀 0).
  - [해결 2026-06-13] 테스트 성능·결정성: test_p3::test_llm_fallback_when_polish_hallucinates 가
    ANTHROPIC_API_KEY 미삭제로 build_report(use_llm=True) 시 실제 Anthropic compose 호출(과금·비결정)
    → 137.24s(전체의 40%) 차지. monkeypatch.delenv("ANTHROPIC_API_KEY") 1줄 추가(형제 test_llm_sections
    _no_key 패턴과 통일)로 룰 백엔드 강등. 해당 테스트 137.24s→0.01s, 전체 342.71s→205.54s, 150 PASS
    유지(폴백 의도 보존). 운영 코드 무변경(테스트 전용). 실측 근거 = pytest --durations.
  - [측정·미적용 후보] per-test 실측상 잔여 지렛대: ① engine.build당 ~2.0s 바닥 = solarterms.solar_term_time
    이 (year,황경) 결정론인데 캐시 부재로 빌드마다 36회 재계산 → 모듈 lru_cache 시 스위트·운영 동반 단축
    (calc 레이어=골든 회귀 동반 필수). ② golden_sweep 40s = 21케이스 그리드 최초 빌드(①의 종속, 순서
    아티팩트). ③ KASI 인벤토리 36s = 의도된 전수 스캔(필요시 @pytest.mark.slow 분리). veraPDF/Chromium은
    병목 아님(p5 각 6.4s)으로 실측 확인.
  - [완료 2026-06-13] Phase 8 MVP 릴리스 게이트: ① store/orders.py OrderStore.delete()=하드삭제(PII
    복구불가 파기, 개인정보보호법 제21조)+감사 스텁(audit_log는 PII 비포함 메타만, 행 삭제 후에도 'delete'
    추적 보존), sajugen/delete_order.py Typer CLI(--yes 미지정 시 미리보기만=실수 방지). ② tests/test_p8.py
    E2E 3건(평일 solar / 윤달 2012윤3월1일→2012-04-21 KASI한국·한중상이경고 / 시진불명 unknown_time=추정고지)
    전부 gate_pass·calc_consistent PASS. ③ README-ops.md 운영자 런북. test_orders +2, 전체 153 PASS.
    actor literal 제약으로 삭제 actor='admin' 채택. docs/09 Phase 5·6·8 상태 보정(7은 부분=백로그).
  - [완료 2026-06-13] Phase 9 익명 계산특이점 데이터셋: sajugen/insight.py 신설 — extract_insight()는
    PII 분산(birth·render_meta.gen_params.name/concern·content)을 피해 **안전 필드만 화이트리스트 수집**
    (name·birthplace·concern·order_id·content 미접근). 보존: 입력(분단위)·성별·역법·solar_date·bazi(4주)·
    ziwei유무·경계신호(crosscheck/normalize warnings·needs_review·자시23시·near_term_boundary)·boundary_labels.
    append_insight→data/calc_insights.jsonl(gitignore, 로컬). Typer CLI extract/sweep(기본 경계만·--all 전수).
    delete_order.py --extract-insight=파기 전 추출(extract-then-purge). test_insight 4건(PII 부재 단언 포함).
    법적 근거=제28조의2(가명·연구/통계)·제58조의2(익명 적용제외). 기존 골든 포맷과 동형=익명 골든 후보.
    한계: near_term_boundary는 현 흐름 미충전(기본 False)→절입경계는 crosscheck_warnings로 포착, 충전은 백로그.
  다음 후보: 검수 UI 2차(섹션 재생성·하이라이트·diff), 운영자 확인 2건(표지 표제·한지), 실주문/지인 베타 2~3건,
    성능 ① solar_term_time 캐싱(calc, 골든 회귀 동반), near_term_boundary 충전(절입경계 자동 플래그).
조사대상(미해결): lunar-python sect=2 고정이 JST_2300과 23:00~24:00 출생에서 일주 어긋날 잠재 이슈
  (공망은 자체산술로 회피했으나 일주 자체는 별도 조사).
전체 회귀 79 PASS. 다음 = Phase 5(Question Router + 부분 LLM 4구간, content/question_router.py·llm_sections.py;
  운영자 ANTHROPIC_API_KEY 준비 필요, 무키 시 룰 폴백).
헤드리스(경로1 Max) 폐기 — 런타임 LLM은 Anthropic 공식 API로 확정.

## 목표/스택 (확정)
- 목표: 사주양식 입력 -> 진태양시 보정 -> 명리+자미두수 계산 -> 23섹션 콘텐츠
  +할루시네이션 가드 -> tagged PDF(텍스트레이어/아웃라인) -> 검증 게이트.
  운영자 내부 도구, Python 올인.
- 스택: lunar-python / iztro-py(import명 iztro_py) / Skyfield(절기, de440s.bsp;
  sxtwl 폐기) / KASI(키 확보 시 3원) / Jinja2 + Playwright Chromium tagged
  (Paged.js 대신 네이티브) / veraPDF(포터블 Java 21).
- 문안: 룰 골격 + LLM 윤문(Instructor+pydantic, 사실 슬롯 고정, 사실일치/§12/
  트레이스 린트, 실패 시 룰 원문 폴백; 무키면 자동 폴백 = 비용 0).
- 시간보정: zoneinfo Asia/Seoul(표준시역사·DST 권위) + Skyfield 진태양시
  + 자시정책 enum. 절기 lunar-python<->Skyfield 교차(lunar는 고정 UTF+8).

## 완료 (P0~P5, 전부 [x])
- P0 스파이크: 계산 라이브러리 + Playwright tagged PDF PoC.
- P0.5 도구체인+거버넌스: 도구 설치, ephemeris, .claude/agents 6종 설치 완료
  (opus-4-7=sg-planner/sg-calc-architect/sg-accuracy-verifier/sg-content-guard,
  sonnet-4-6=sg-render-runner/sg-extractor), test-project/.claude/settings.json
  에 SessionStart+PreCompact 훅 설치 완료(STATE.md 자동주입).
- P1 보정: input/time_correction.py, calc/solarterms.py, calc/crosscheck.py.
  test_p1 7/7. 절기 교차 1955~2049 오차 0.02~0.21분.
- P2 계산: calc/myeongni.py, calc/ziwei.py, calc/engine.py(SajuResult).
  test_p2 8/8. 2000-01-01=己卯(절입 연주경계), 명리<->자미 사주팔자 일치.
- P3 콘텐츠: content/ (sections_schema, rules, safe_lint, factcheck, trace,
  llm_polish, builder). test_p3 5/5. 가드/폴백 실증.
- P4 렌더: render/ (charts, templates/report.html.j2, pdf.py, verify.py).
  test_p4 5/5. 샘플 10p·3300+자·tagged·아웃라인23 = 통이미지 결함 해결 입증.
- P5 도구화: pipeline.py, cli.py(Typer), app.py(FastAPI). test_p5 3/3.

## 실행 방법
- CLI: ./.venv/Scripts/python.exe -m sajugen.cli --birth "1990-05-20 14:30" --gender 남 --horoscope 2026-06-01 --out x.pdf
- 웹폼: ./.venv/Scripts/python.exe -m uvicorn sajugen.app:app --host 127.0.0.1 --port 8765
- 테스트: ./.venv/Scripts/python.exe -m pytest tests/test_p1.py tests/test_p2.py tests/test_p3.py tests/test_p4.py tests/test_p5.py tests/test_kasi.py tests/test_normalize.py tests/test_ziwei_parity.py tests/test_orders.py
- 산출 PDF: sajugen/render/out/

## veraPDF / PDF-UA (결정 완료)
- 포터블 Java 21(sajugen/tools/jdk-21.0.11+10-jre) + veraPDF 1.30.1
  (sajugen/tools/verapdf) 설치. render/verify.py 에 연결, 매 PDF 검증/기록.
- 하드게이트(텍스트레이어·폰트·태그) PASS. PDF/UA-1 compliant=False,
  잔여 clause 7.1-3 1건 = Chromium 태그드 구조 한계.
- 결정: 옵션1 현행 유지(veraPDF는 측정·보고만, 빌드 불차단). WeasyPrint/
  GTK·Chromium 후처리 미추진. 추가 코드 변경 없음.

## 터미널 한글 깨짐 (해결됨)
- 진짜 원인(공식 정정): VS Code/Cursor 통합 터미널 GPU xterm.js CJK 렌더
  버그(microsoft/vscode #137047, claude-code #41358) + 폰트 한글 미흡.
  코드페이지 949는 보조였음(이전 "949 1차" 단정은 철회).
- 조치 완료: Cursor settings.json(C:\Users\pc\AppData\Roaming\Cursor\User\
  settings.json)에 gpuAcceleration=off, fontFamily="Consolas, Malgun Gothic",
  fontLigatures=false 추가. ~/.claude/settings.json 에 "tui":"default" 추가.
  사용자 확인: 정상 표시됨.
- 운영 규칙: 답변은 평문 ASCII 위주(이모지/표/특수기호 금지).
  근거 메모리 feedback-terminal-safe-output.

## 알려진 사소 이슈 (기능 영향 없음, 보강 후보)
- iztro soul/body 主星은 원키 노출(soul_star_raw). 한글 매핑 보강 가능.
- 子/午시 命身同宮(신궁=명궁) 정상 동작 — 문구만 "명신동궁"으로 다듬기 여지.
- (정리됨 2026-06-10) ArbiSignal 잔재 삭제: config/·scripts/(capture/collect/recon/
  common 등 8종)·tests/test_parsers.py. .env.example 도 sajugen용으로 정정.
  scripts/ 는 kasi_dump.py·verify_kasi_cache.py 만 남음.

## RESUME HERE - 다음 즉시 작업
>> (완료 2026-06-10) 개발용 모델 라우팅: 전역 model=opusplan + env
   OPUS=claude-fable-5 / SONNET=claude-opus-4-8 + advisorModel=fable
   → 플랜 모드=Fable 5, 실행=Opus 4.8, 중요 결정 시점=Fable 자문.
   sg-* 에이전트: 정확도 4종=claude-opus-4-8 핀, render-runner/extractor=
   claude-sonnet-4-6 핀(서브에이전트 하한선 Sonnet 4.6 — 운영자 확정,
   Haiku는 읽기전용 탐색·분류만). 별칭 주의: opus=Fable, sonnet=Opus 4.8로
   해석되므로 핀은 풀네임 사용. 상세 docs/08. 새 세션부터 적용.
>> (진행 중 2026-06-10) 상용화 플랜 Phase 1 = KASI 검증층.
   [완료] 운영자 키 발급: 활용신청 2건(자동승인) 후 KASI_API_KEY 를 .env 에
   저장(64자 hex, +// 없어 enc/dec 동일). 실호출 활성화 즉시 확인(동기화지연 없음).
   [완료] 가용성 프로브(실측 2026-06-10):
   - 음양력 getLunCalInfo: 월 일괄 조회 가능(solDay 생략 + numOfRows=31 → totalCount=31).
     범위 최소 1900~2050 정상(1900-01-01 → 음력 1899-12 반환, 2051-12-31=0). → 1콜/월.
   - 절기 get24DivisionsInfo: 연 일괄 가능(solMonth 생략 → totalCount=24).
     가용 = 2000~2027 한정(1989~1999=0, 2028+=0 / 정부가 매년 ~2년 앞까지만 갱신).
     응답에 kst(절입 분단위)+locdate 제공. → 절기 3원 교차는 2000~2027만, 그 외 연도는
     lunar↔Skyfield 2원(P1에서 1955~2049 오차 0.02~0.21분 기검증).
   - [주의] 2000-02 dateName 결함 재현: 2/19(우수,17:33) 행이 dateName='입춘' 오기.
     → 캐시 빌더는 dateName 신뢰 금지, locdate/순서로 절기명 도출.
   - 트래픽: 전체 캐시 약 2,000콜(음양력 1812 + 절기 28) → 분할 불필요, 수 분 내 1회 구축
     ('6일 분할' 전제는 월 일괄로 무효화됨). API별 1만건/일 독립 한도.
   [완료] 구현(2026-06-10):
   - scripts/kasi_dump.py: 음양력 월 일괄 + 절기 연 일괄, 재개 가능(기존 월/연 스킵),
     httpx+_type=json, 0.15s 지연. data/kasi_cache.sqlite(.gitignore) 적재.
   - sajugen/calc/kasi.py: 스키마/빌더(lunar·solarterm·meta) + KasiCache 읽기전용 리더
     + crosscheck3_year(2원에 KASI 열 추가, Skyfield↔KASI 허용 2분, 범위밖/무캐시 시 2원 폴백).
     절기 결함 우회: normalize_solarterm_rows 가 dateName 대신 KST→UTC 시각을 Skyfield
     24절기 최근접 매칭해 한자명 부여(2000-02 우수→입춘 오기 정상 흡수, 테스트로 확인).
   - tests/test_kasi.py 8개 PASS + 픽스처 tests/fixtures/kasi_sample.json(실데이터 캡처).
     Skyfield↔KASI 절입차 2000/2026 모두 ≤2분 실측. 전체 회귀 42 PASS(34+8).
   - 교차검증 강도: KASI 일진(2000-01-01)=무오 ↔ 명리 일주 골든 戊午 일치 확인.
   [완료] 전체 캐시 구축 + 전 구간 교차(2026-06-10):
   - data/kasi_cache.sqlite = 음양력 55,152일(1900~2050) + 절기 672행(2000~2027 전 연도 24절기), 3.7MB.
   - 2000~2027 절기 Skyfield↔KASI 전수: 672행 중 3건만 >2분 = KASI 원본오류로 확정·문서화.
     (2011 大寒 1일오타 / 2011 立冬 6h / 2015 夏至 20분) — 두 계산엔진은 ≤0.03분 일치, KASI만 outlier.
     기지결함 목록(KNOWN_KASI_TERM_DEFECTS)으로 코드 고정 + 회귀 테스트(test_full_cache_defect_inventory).
   - 절기 timing 권위=Skyfield(검증 lunar), KASI 절기=3차 참조 → 결함 3건은 사주 계산 영향 0
     (라이브 엔진 월주·세운은 solarterms.py=Skyfield). 불일치 처리 정책 정밀화 = docs/03 §2-1·2-2·4.
   - [전수 무결성 감사] scripts/verify_kasi_cache.py — 음양력 55,152일 전수:
     solJd 연속성 0건 / 일진 60갑자 연속성 0건 / KASI 일진↔lunar-python 100% 일치(0건).
     하드오류 0 = 날짜·간지 무결성 완벽. 한·중 음력 라벨 상이 1,978일/59개년은 오류 아님
     (lunar=중국기준, KASI=한국 권위; 대표 2012 KASI 윤3월 vs 중국 윤4월, 일진 동일).
     카탈로그 data/kasi_kr_cn_divergence.json(Phase 2 자산). 상세 docs/03 §2-3.
   - 테스트 tests/test_kasi.py 12 PASS(일진 표본 무결성·2012 한·중 사례 포함), 전체 회귀 46 PASS(34+12).
   [완료기준 충족] docs/09 Phase1 = "1900~2050 캐시 + 불일치 0 또는 전수 문서화" → 캐시 완비 +
     KASI 결함 3건 전수 문서화. 다음 = Phase 2(음력/윤달 입력 정규화, input/normalize.py).
   계획 전문: ~/.claude/plans/sajugen-phase-1-kasi-crispy-cat.md
   확정 정책(2026-06-10): 자미 윤달 = 15일 분할법, 고지 = 감수 명시형
   ("자동 분석 도구 산출 + 운영자 직접 검수·감수"), 음력 변환 1차 기준
   = KASI(한·중 음력 상이일 존재, lunar-python 은 중국 기준이라 대조용),
   명리 메인·자미 보완(상충 시 명리 우선, '층위 차이' 재서술, 정확도
   주장 전면 금지). 상세 = docs/03(유파 결정표)·docs/06(LLM 정책).
   Phase 목록·완료 기준 = docs/09-roadmap.md.

>> (완료 2026-06-10) Phase 0 = 상용화 플랜 승인 + docs/00~10 11종 작성.
   리서치 5종(KASI API/만세력 라이브러리/자미 라이브러리/Claude Code·
   Codex·MCP 공식문서/명리·자미 통합 학술) 결과를 docs/00 원장에 영속화.
   핵심 발견: (a) KASI 음양력 API 가 세차·월건·일진 간지+윤달 플래그+
   율리우스적일 직접 제공, 특일 API 가 절입시각 분단위(kst) 제공(실호출
   확정 필요). (b) 만세력 외부 라이브러리 "KASI 기반" 주장 3건 중 2건
   허위 → 바로 채택 가능 후보 없음, 기존 lunar-python 1.4.8 고정 유지.
   (c) iztro 가 유파 차이를 config 로 노출(사화표/윤달/연경계/자시),
   iztro-py 는 원본 동등성 검증 조건부. (d) "명리=기세, 자미=영역"
   통설은 학술 근거 없는 실무 관행 → 자미는 12궁 영역 서술 엔진으로
   한정, 시기·길흉 최종 권위는 명리.
>> (완료 2026-05-19) 디벨롭3 = 디자인 정교화 + 말투(상담 화법) 개편(룰만,
   공신력 자료 기반). 플랜: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md
   (F1~F4). 경계 준수: 새 계산 0, LLM 0, 가드 GREEN, veraPDF 7.1-3 비악화.
   - F1 디자인(render/templates/report.html.j2 + pdf.py margin 동기화):
     :root 60-30-10 색 토큰(--bg/--panel/--line/--ink/--mut/--gold/
     --gold-ink), 4px 베이스라인·8pt 스케일(--s1..s7), 본문 행간 1.6·
     제목 1.28, 한글 자간 -0.015em(제목 -0.02em), 모듈러 제목 스케일
     (cover 30pt/chapter 26pt/h2 1.72em/.subhead 1.32em). 섹션 제목을
     박스형 골드채움→편집형(골드 번호 라벨+잉크 제목+하단 헤어라인),
     챕터 마스트헤드 여백 리듬+짧은 골드 룰(crule), 표지 kicker/rule,
     .card 골드 상단 보더, .src 헤어라인 각주화, svg text 자간 0.
     @page 16mm/15mm ↔ pdf.py pg.pdf margin 동기화(tagged/outline 불변).
     WCAG 재검: gold-ink #7d5610≈6.4:1(텍스트), gold #9a6f1e≈4.4:1(룰만).
   - F2 차트(render/charts.py): ohaeng/sipseong 트랙바(흰 트랙+색 채움,
     분포 비교 직관)+굵은 직접 라벨, 라벨색 토큰화(#22262e/#54606e),
     4px 정렬, role=img+title·결정론·객체토큰 불변.
   - F3 말투(content/rules.py, 핵심): 보고서체→2인칭 상담 화법(주어 생략
     자연스러운 곳은 생략, 강조만 '당신/님'). _pick(md5 결정론) 표현
     다양화로 _pillar_line/_pillar_block/_palace_para 문형 반복 제거,
     용어를 라벨나열→서사(간지→특성→제안). 안전 어미·바넘 회피 유지.
   - 독립 톤 검토(general-purpose) 6/10 + #1 결함 지적 → 즉시 수정:
     한국어 조사 자동결합 노출("이(가)/은(는)/을(를)/과(와)")·"결으로"
     비문·"살펴봅니다과(와)" 깨진 변수삽입. 대응: rules.py 에
     _anchor(읽는 마지막 한글음절; 천간/지지/오행 한자 독음 매핑)+
     _jong/_josa/_J/_ro 결정론 조사 헬퍼 추가, 전 플레이스홀더 치환,
     wealth 중복어구·thisyear period_str 명사구화. 재덤프 검증: 두 케이스
     잔여 플레이스홀더 0, 조사 정합("壬(임)을 기준으로","돌파가 살아나는"
     등), _pillar_block 콤마 런온도 비종결 절(-이고/-며/-인데)로 수정.
   - 검증 GREEN: _guard_check 6케이스 clean=True(safe0/fact0/grounding/
     fallback0, health 의료단정0·'의료 전문가' 포함). pytest test_p1..p5
     34 passed(계산 무변경, p2 회귀 무). 재생성 test_1992 통합 18p·추출
     15,595자(원본 3,022 → 약 5.2배), 명리단독 16p·13,164자, 전부
     gate_pass·tagged·fonts_embedded. veraPDF failed_clauses=['7.1-3']
     1건 그대로(악화0). PNG 육안: 표지/챕터/섹션 위계·디바이더·트랙바·
     상담체·조사 정상.
   - 정직 잔여(룰 한계): 통합 ~13.6~13.9k자(추출 ~15.6k)는 경쟁사
     프리미엄(3.9~6.9만)에 여전히 미달. 독립검토 #2(자미 12궁 해석
     문장 단일템플릿 — 별·밝기만 다름)·#3("세 가지 첫째/둘째/셋째"
     골격 love·job·wealth·health 4연속)은 _palace_para 변형 확대로
     일부 완화했으나 잔존. 추가 자연스러움·분량은 다방식 용신·세밀
     격국(정확도 후속) 또는 LLM 윤문(경로1 Max헤드리스, 비용·한도
     결정 보류) 경로. 임시 _f4_*.txt/.json/_tone_case_*.txt/_f4_png/
     _guard_result.txt 는 일회성(deny 규칙상 rm 불가, 무해).

>> (완료 2026-05-19) 디벨롭2 = 각론 서사 분량·깊이 확장(룰만, 이미 계산된
   데이터 소비). 플랜: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md.
   작업목록 #32~#34 완료.
   - rules.py: _pillar_block/_DOMAIN_PALACE 헬퍼 추가. love/job/wealth/
     strength 를 격국·용신·신강약·신살·지장간·지지십성·4주십이운성·납음·
     해당 자미궁(부처/관록/재백/천이)으로 3~5배 심화. thisyear/monthly 에
     세운/월운 간지(_gz_ko, factcheck 이미 allowed) 엮어 대운→세운→월운
     3층 서사.
   - 신설 2섹션: character("성격·기질 종합" — 일간+십성+신강약+신살, ilgan
     중복 회피 자체 디스클레임), health("건강 — 생활 관리의 결(참고)" —
     질액궁+신살+신강약+오행, 의료 단정 절대 금지·"의료 전문가 상의"
     고정). sections_schema 등록, builder._PRODUCT_DROP 에 character 를
     자미단독 제외 추가(health 는 전 상품 유지·질액궁 None graceful).
   - 검증 GREEN: _guard_check 6케이스(성인3·미성년·명리단독·자미단독)
     전부 clean=True(safe0/fact0/grounding/fallback0). pytest test_p1..p5
     34 passed(신규 test_p3 각론/health/상품토글 단언 포함). 재생성
     test_1992 통합 18p·추출 14,846자(원본 3,022 → 약 4.9배), gate_pass,
     fonts_embedded·tagged·시스템폰트 비의존, veraPDF 7.1-3 1건 그대로
     (악화0). 독립 톤 검토(general-purpose): 의료·과장·공포·운명론 없음,
     개인화 실증(케이스별 토큰 차등). 권고 2건 반영 — 체크리스트를
     계산 토큰(십성/격국/신강약)에 연결, 일주 시주 동어반복 제거(패딩↓).
   - 정직 잔여: 통합 ~13~15k자는 경쟁사 프리미엄(3.9~6.9만)에 여전히
     미달. 룰 한계상 그 이상은 반복/바넘 위험. 추가 깊이는 다방식 용신·
     세밀 격국(정확도 후속) 또는 LLM 윤문(비용 경계, 보류) 경로.

>> (완료 2026-05-18) 디벨롭 = 명리 해석 깊이(격국·억부용신·신살·세운/월운).
   플랜: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md. 경계 넘음(새 계산
   추가, LLM 무). 작업목록 #29~#31 완료.
   - 신규 sajugen/calc/advanced.py: geukguk(월령 본기 십성→정격/잡격),
     eokbu(일간 생조 vs 극설 점수→신강/중화/신약 + 억부 참고용신),
     shinsal(전통 표: 천을귀인·도화·역마·화개·양인·괴강·백호),
     seun_worun(lunar-python DaYun.getLiuNian/LiuYue 노출).
   - myeongni.py: Myeongni 에 geukguk/geukguk_note/singang/singang_score/
     yongshin_eokbu/yongshin_axis/yongshin_method/shinsal/seun/worun 추가,
     build(ref_year) 에서 advanced 호출. engine.build 가 horoscope_date→
     ref_year 파싱해 전달.
   - factcheck.allowed_tokens 에 세운·월운 간지 합집합 추가(필수 — 본문
     세운 간지가 위반 안 나게). 신살은 한국어명이라 factcheck 무관.
   - sections_schema 신규 3섹션: geukguk("격국과 용신(참고)"),
     shinsal("신살 풀이(참고)"), seun("세운·월운 흐름") — 27섹션.
   - rules.py: 세 섹션 비단정 문안 + _SHINSAL_MEAN. 용신은 "억부 1방식
     기준 참고, 조후·통관 등은 다를 수 있어 상담 확정 권장" 고정.
   - lunar-python 의 getDayJiShen/XiongSha 는 '일진 택일 신살'(河魁·金匮)
     이라 사주 신살과 다른 체계 → 미사용(왜곡 방지). 전통 사주 신살은
     advanced.py 표로 직접 구현.
   검증 GREEN: pytest test_p1..p5 33 passed(신규 advanced 단언 5 포함, 회귀
   무), 가드 4케이스 clean=True, 최종 PDF 16p·추출 11,851자(원본 3,022 →
   약 3.9배), gate_pass=true, fonts_embedded·tagged, 시스템폰트 비의존,
   veraPDF 7.1-3 1건 그대로(악화0). 독립 정확도 검토(general-purpose)로
   2케이스 손계산 검산 일치 + 학설차 항목은 note/라벨로 단정 회피 확인.
   사후 수정: 괴강 집합 오입력(戊戌→) 발견, 주류 4주설 {庚辰庚戌壬辰壬戌}
   로 정정(advanced.py).
   정직 잔여: 격국 비견/겁재=건록/양인격은 통념 단순화(자평진전 록·인
   별도정의와 차이, note 명시). 도화/역마/화개는 일지 기준(연지설 미반영).
   용신은 억부 1방식만(조후·통관·병약·종격 = 후속). 깊이 더 원하면 다방식
   용신·세밀 격국·신살 학설 옵션화가 다음 후속.

>> (완료 2026-05-18) 전면 종합 개편 P0~P2 (플랜:
   C:\Users\pc\.claude\plans\quirky-wibbling-wind.md, 경계: 룰만·새계산0·LLM무).
   A1~A5·B1~B4·C1~C4 전부 완료(C2 상품토글·C4 이름/생시미상 포함). 검증 GREEN:
   pytest test_p1..p5 28 passed, 가드 4케이스 clean=True(safe0/fact0/grounding/
   fallback0), 최종 PDF 16p·추출 10,680자(원본 3,022 → 3.5배), gate_pass=true,
   fonts_embedded, tagged, 시스템폰트(Malgun/Gulim/SimSun) 비의존,
   veraPDF 7.1-3 1건 그대로(악화0).
   - A1 폰트: sajugen/render/fonts/ = Pretendard(R/SB/B woff2)+
     SourceHanSerifK-Regular.otf(한자, 24.5MB)+OFL 2종(Pretendard-OFL.txt,
     SourceHanSerif-OFL.txt). report.html.j2 @font-face unicode-range 분리
     (한글=Pretendard / 한자=Source Han Serif). pdf.py _FONT_DIR(file:///).
   - A2 교육 부록화: sections_schema "appendix_terms" 추가(24섹션),
     _STATIC_OK 동기화. test_p3 단언을 len(SECTION_SPECS)>=24 로 갱신.
   - A3/A4 콘텐츠 심화+톤: rules.py 의미사전(_SS_MEAN/_ELEM_MEAN/_DISHI_PHASE)
     +헬퍼(_palace_para/_palace_brief/_dishi_phrase/_gz_elem/_age_of), 전 섹션
     근거기반 상담서사, 바넘 회피. final_text 약 9,100자.
   - A5 미성년분기: rules.build_all(saju, ref_year)→is_minor(age<19) 시 love
     섹션 연령적합 치환. pipeline→builder(ref_year)→build_all, pipeline→
     render_pdf(age) 연결.
   - B1/B2 디자인: report.html.j2 디자인토큰·.chapter 마스트헤드, pdf.py
     _CHAPTERS(5챕터) + render_html chapter 필드. 페이지번호는 Chromium
     @page margin-box 미지원+PDF/UA 위해 header/footer 미사용 → 미적용
     (대신 tagged 아웃라인 24개가 접근성 내비. 정직 한계).
   - B3 SVG카드: charts.sipseong_card(5축), daewoon_timeline(current_age
     마커). 템플릿 sipseong_svg hook.
   - B4 심리: closing=개인화 격려 레터(peak-end), advice=If-Then 3개
     (Gollwitzer), next=비강압 CTA('선택'·강요 안 함, NN/g).
   - C1 자미 12궁 전 궁 개별(_PALACE_ROLE_ALL/_PALACE_ORDER). C3 접근성:
     SVG role=img+title 유지, veraPDF 7.1-3 비악화 측정.
   - C2 3단 상품 토글 완료: builder._PRODUCT_DROP, integrated=24 /
     myeongni=21(ziwei_summary·ziwei_palaces·cross 제외) / ziwei=15
     (wonguk·ohaeng·ilgan·sipseong·strength·daewoon·thisyear·monthly·cross
     제외). 전부 guard clean, pipeline gate_pass(myeongni 13p·8,553자 검증).
     v1 한계: 혼합 섹션(summary/love/job/wealth)은 상품별 정제 안 함(보존).
   - C4 이름·생시미상 완료: pipeline/cli/app/builder/rules 에 name·
     unknown_time·product 종단 연결. name → cover/summary/closing 호명.
     unknown_time(날짜만 입력) → 시주 12:00 계산하되 cover·wonguk 에
     '시주 추정' 고지(시주 단정 회피). cli 는 'YYYY-MM-DD' 만 받으면
     자동 unknown_time. 전 케이스 guard clean, pytest 28 passed.
   - 정직한 잔여(계획 외): 분량 ~10,680자(통합)는
     플랜 12~15k 목표·경쟁사 3.9~6.9만자에는 못 미침(룰 경계 한계, 깊이
     완전추월은 후속 계산/LLM 경로 — 사용자 결정으로 보류).
   - 운영 사실: 폰트 unicode-range = Pretendard(U+0000-04FF,AC00-D7A3 등)/
     SourceHanSerif(U+3000-303F,3400-4DBF,4E00-9FFF,F900-FAFF). cp949 콘솔 →
     측정은 UTF-8 파일 덤프 후 Read. 임시 스크립트 _guard_check.py/
     _a1_check.py/_verify_after.py, 렌더 _pdfimg4/ 존재(일회성).

>> (완료 2026-05-18) 고레버리지 콘텐츠/렌더 개선(계산 무추가). 플랜:
   C:\Users\pc\.claude\plans\quirky-wibbling-wind.md. 변경:
   - rules.py: 표시 매핑(_SHISHEN/_GAN/_ZHI/_DISHI/_BRIGHT_KO) + _pillar_line/
     _stars_full 헬퍼 추가, build_all 23섹션 심화(지장간·지지십성·4주 십이운성·
     납음·자미 보좌성/사화/밝기/12궁 = 이미 계산된 미사용 데이터 활용).
   - charts.py: manse_table(만세력 명식표 4x7), ziwei_chart(자미 12궁 4x4 명반)
     신규 2함수. report.html.j2 wonguk/ziwei_summary 에 삽입, pdf.py 변수연결.
   - 레이아웃: @page 15mm14mm, line-height 1.55, _DIVIDERS 8->4챕터, summary
     .card 대시보드(pre-line 4블록). pdf.py pg.pdf margin 15/15/14/14 동기화.
   결과(1992-03-07 재생성): 추출 텍스트 3,022->6,878자(2.3배), 9p, gate_pass
   유지, 가드 clean(safe0/fact0/grounding/fallback0), veraPDF 잔여 7.1-3 1건
   그대로(악화0), 차트 4종 렌더 확인(만세력표/자미명반 정상). pytest
   test_p1..p5 28 passed(회귀 없음, 계산 무변경).
   주의: 추출 6,878자는 플랜의 8,000 목표 미만(과장 금지). 더 늘리려면 thin
   섹션(monthly140/closing174/caution174/thisyear176) 추가 심화 여지.
   후속(범위 밖): 격국·용신·희기신·신살·세운/월운(새 계산, 정확도검증 필요),
   LLM 윤문(--llm 토글, .env 자동로드 완료, 비용 결정으로 보류).

>> (완료 2026-05-18) 실사용 점검 A: 1992-03-07 09:20 여 서울 horoscope 2026-06-01.
   결과: 사주팔자 壬申 癸卯 壬午 甲辰(일간 壬), 진태양시 08:36:48(균시차 -43.2분),
   시지 辰, 오행 水3木2火1土1金1. 대운 역행(여+양년) 1세시작 壬寅→辛丑→庚子→己亥…
   자미 명궁 해/주성 태양(陷)/신궁 재백궁(천량)/金四局/화기 무곡/화과 좌보.
   교차검증 OK(명리=자미 동일, 월지 lunar=Skyfield 모두 卯). 가드 clean(0/0).
   verify: 10p·3021자·text_layer_ok·fonts_embedded·tagged·outline23·gate_pass=true.
   veraPDF compliant=false 잔여 7.1-3 1건(기존 알려진 Chromium 한계, 옵션1대로 보고만).
   부수 수정: cli.py PASS/FAIL 출력 이모지(✅❌) 제거(cp949 콘솔 UnicodeEncodeError
   크래시 원인이었음, 평문으로 교체). 산출물: sajugen/render/out/test_1992.pdf.
   주의: verify.contains_known_ganzhi 는 P4 고정샘플(己卯/戊午) 센티넬일 뿐,
   임의 입력에선 false 가 정상(결함 아님). 보강하려면 verify에 입력 간지 검사 추가 여지.

## 그 외 가능 작업 (사용자 선택 대기)
핵심 빌드 끝남. 다음 중 선택:
 A) 실사용: 실제 고객 생년월일시로 PDF 생성 + 결과 점검/문안 톤 조정.
 B) 콘텐츠 고도화: 23섹션 룰 문안 깊이 보강, 월별운세 상세, 主星 한글 매핑.
 C) 외부배포 대비: 한글폰트 OFL 번들, WeasyPrint pdf/ua 진짜 PASS(여기엔
    Windows GTK 설치 결정 필요), Paged.js 페이지번호 고도화.
 D) LLM 윤문 실연동: ANTHROPIC_API_KEY 설정 시 윤문 품질↑(현재 무키=룰 폴백).
 E) 패키징/문서: README, 운영자 사용설명, 입력검증 강화.
사용자 지시가 없으면 A(실사용 점검)를 추천.
