# sajugen 진행 상태 (SSOT) - 세션 시작 시 이 파일 먼저 읽기

> 컨텍스트가 비워져도 이 파일만 읽으면 그대로 이어갈 수 있다.
> 계획 전문: C:\Users\pc\.claude\plans\quirky-wibbling-wind.md
> 영속 메모리: ~/.claude/projects/C--Users-pc-test-project/memory/ (MEMORY.md 인덱스)
> 최종 갱신: 2026-05-19  (디벨롭3 = 디자인 정교화 + 말투 상담화법 개편 완료)

## 한 줄 상태
사주 PDF 생성기(sajugen) 핵심 빌드 + 전면개편 + 디벨롭1·2·3 완료.
pytest test_p1..p5 34 PASS, 가드 6케이스 clean. 운영자 내부 도구
CLI/FastAPI 작동. 디자인(편집형)·말투(2인칭 상담체)·조사 후처리까지
정교화됨. 남은 레버는 LLM 윤문(경로1 Max헤드리스, 비용·한도 결정 보류).

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
- 테스트(레거시 test_parsers 제외): ./.venv/Scripts/python.exe -m pytest tests/test_p1.py tests/test_p2.py tests/test_p3.py tests/test_p4.py tests/test_p5.py
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
- 레거시 tests/test_parsers.py(구 arbisignal, 무관) 수집에러 -> 위 명령처럼
  test_p1..p5 만 지정 실행.

## RESUME HERE - 다음 즉시 작업
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
