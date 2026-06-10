# sajugen 진행 상태 (SSOT) - 세션 시작 시 이 파일 먼저 읽기

> 컨텍스트가 비워져도 이 파일만 읽으면 그대로 이어갈 수 있다.
> 계획 전문(현행): C:\Users\pc\.claude\plans\role-claude-distributed-hellman.md (상용화 플랜, 2026-06-10 승인)
> 계획 전문(구): C:\Users\pc\.claude\plans\quirky-wibbling-wind.md
> 정책 문서: C:\Users\pc\test-project\docs\00~10 (research ledger·유파 결정·LLM 정책·검수 워크플로우)
> 영속 메모리: ~/.claude/projects/C--Users-pc-test-project/memory/ (MEMORY.md 인덱스)
> 최종 갱신: 2026-06-10  (상용화 플랜 승인 + Phase 0 문서화 완료)

## 한 줄 상태
사주 PDF 생성기(sajugen) 핵심 빌드 + 디벨롭1·2·3 완료(pytest 34 PASS).
2026-06-10 상용화 플랜(Phase 0~8) 승인: KASI 3원 검증층 + 음력/윤달 입력
+ 자미 유파 정책 + 부분 LLM 4구간(공식 API) + 주문 상태머신 + 검수 UI.
Phase 0(docs 11종·정책 고정) 완료. Phase 1(KASI 검증층)·Phase 2(음력/윤달 입력) 완료.
P1(2026-06-10): 키 발급·전수 캐싱(음양력 1900~2050 + 절기 2000~2027)·3원 교차·KASI 결함 3건 문서화.
P2(2026-06-11): input/normalize.py 음력→양력(KASI 역조회 1차)·윤달·한·중 상이 경고, CLI/웹폼 --lunar/--leap.
전체 회귀 53 PASS. 다음 = Phase 3(자미 유파 정책 + iztro 동등성, calc/ziwei.py·config/rule_profile.yaml).
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
- 테스트: ./.venv/Scripts/python.exe -m pytest tests/test_p1.py tests/test_p2.py tests/test_p3.py tests/test_p4.py tests/test_p5.py tests/test_kasi.py tests/test_normalize.py
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
