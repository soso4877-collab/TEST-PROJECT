# 00. Research Ledger (조사 원장)

> 갱신 규칙: 새 출처를 근거로 정책·코드가 바뀔 때마다 행 추가. 확인 시점 필수. 공식/학술/실무관행/비공식 구분 필수. README 주장은 코드 확인 전까지 "주장"으로만 기재.
> 최초 작성: 2026-06-10 (리서치 에이전트 5종 결과)

## A. Claude Code / Codex / MCP (전부 공식, 확인 2026-06-10)

| 출처 | 핵심 확인 내용 | 프로젝트 적용 |
|---|---|---|
| https://code.claude.com/docs/en/permission-modes | Plan Mode = permission mode, 승인 게이트 | 민감 리팩토링은 플랜 승인 후 실행 |
| https://code.claude.com/docs/en/hooks | hooks 28종, PostToolUse/Stop decision:block, exit 2=차단 | 가드를 hook으로 강제 (docs/08) |
| https://code.claude.com/docs/en/skills | .claude/skills/SKILL.md, frontmatter, 커맨드 통합 | 검증 루틴 스킬화 |
| https://code.claude.com/docs/en/sub-agents | .claude/agents/*.md, tools/model 제한 | 기존 sg-* 6종 유지 |
| https://code.claude.com/docs/en/memory | CLAUDE.md 로드 체인, @AGENTS.md import 공식 권장 | CLAUDE.md/AGENTS.md 단일 소스 |
| https://code.claude.com/docs/en/mcp | claude mcp add, .mcp.json, 프로젝트 스코프 승인 | MVP MCP 0개 결정 |
| https://developers.openai.com/codex/cli/ 외 | AGENTS.md, skills=.agents/skills, CI=API 키, @codex review | 2차 리뷰 게이트(보류) |
| https://modelcontextprotocol.io/specification/2025-11-25/index | 현행 스펙 2025-11-25, tool=임의코드 취급, 동의 MUST | MCP 도입 판단 기준 |

## B. KASI 공공데이터 (확인 2026-06-10)

| 출처 | 구분 | 핵심 확인 내용 |
|---|---|---|
| https://www.data.go.kr/data/15012679/openapi.do | 공식 | 음양력 API(LrsrCldInfoService): 양↔음, lunLeapmonth(윤달), lunSecha/lunWolgeon/lunIljin(간지), solJd(율리우스적일). 무료, 자동승인, 개발 10,000건/일 |
| https://www.data.go.kr/data/15012690/openapi.do | 공식 | 특일 API(SpcdeInfoService): get24DivisionsInfo 24절기 |
| https://astro.kasi.re.kr/information/pageView/31 | 공식 | KASI Open API 6종 목록. 절기 시각 별도 API 없음 |
| 다음카페 과학역연구소(실응답 인용) | 비공식(신뢰도 중상) | get24DivisionsInfo의 kst 필드 = 절입시각 분 단위(HHmm). 예: 소한 "0120" |
| https://github.com/OOPS-ORG-PHP/KASI-Lunar | 비공식 | 음양력 범위 1391-02-05~2050-12-31, 절기 데이터 범위 의문(2004~2026 기술) |

미확정(Phase 1에서 실호출 검증): kst 필드 공식 존재 여부, 과거 연도(1905/1950) 절기 커버리지, 음양력 범위.

## C. 만세력 라이브러리 (npm/PyPI/GitHub 코드 직접 확인, 2026-06-10)

| 후보 | 분류 | 핵심 근거 |
|---|---|---|
| lunar-python 1.4.8 (6tail) | 조건부 채택 유지(현행) | 최성숙. 한계=중국 절기시각(UTC+8)·중국 음력. 1.4.8(2025-11) 이후 수정 미릴리스. 이슈 #26(2025 망종, open), #32(23시 일주, 닫힘·방식 미확정) |
| korean-lunar-calendar (usingsky) | 교차검증용(음양력 한정) | 한국 기준 표준 레퍼런스(1000~2050). 1727 윤달 이슈 #8 open. 휴면 |
| ssaju (golbin) | 교차검증용 | 절입시각 자체계산(저차 근사)+대운+경계 테스트. 음력 테이블은 중국 출처 |
| @fullstackfamily/manseryeok | 교차검증용 | KASI DB 덤프 주장. 절기시각 2020~2030만. 출시 초기 버그 4연속 |
| manseryeok (yhj1024) | 배제 | "KASI 출처" 허위(중국 비트마스크 테이블), 라이선스 공백 |
| sajupy | 참고용 | 출처 확정 불가, 단발성 |

교훈: "KASI 기반" README 주장 3건 중 2건 허위/과장. 외부 엔진 바로 채택 불가 → 기존 sajugen 유지 + KASI 골든소스 교차.

## D. 자미두수 라이브러리 (확인 2026-06-10)

| 후보 | 분류 | 핵심 근거 |
|---|---|---|
| iztro (SylarLong) | 기준 구현(바로 채택) | MIT, 3,787★, 2026-05 활성. config.mutagens/fixLeap/yearDivide/dayDivide/algorithm:'zhongzhou'. ko-KR 내장, jest |
| iztro-py (spyfree, 현행) | 조건부 채택 | MIT, 순수 파이썬 0.3.4(2026-03). 신생(2025-11) → iztro(JS) 동등성 CI 검증 조건 |
| fortel-ziweidoushu (airicyu) | 교차검증용 | MIT, 중주파 명시, Jest. 한국어 미지원 |
| Renhuai123/ziwei-doushu | 참고(데이터) | 51.8만 샘플 명반 — 대량 대조 소스 |
| py-iztro (x-haose) | 참고용 | 라이선스 미명시, 2025-08 이후 정체 |
| Wolke/ziwei-doushu | 배제 | CC BY-NC-SA = 상업 불가 |

## E. 도메인(명리·자미 통합) 학술/실무 (확인 2026-06-10)

| 출처 | 구분 | 뒷받침하는 주장 |
|---|---|---|
| KCI 오정우(2018) 자미두수 조선전래 연구 (ART002431369) | 학술 | 17세기 김치 『심곡비결』 전래 — 리포트 내 자미 '역사적 권위' 문구의 유일한 학술 근거 |
| 린성쉬안(국립양명교통대) 술수 양화 연구 | 학술 | 명리·자미 모두 예측력 검증 연구 없음 → 예측 정확도 주장 전면 금지 |
| 김태수(2022) 동방문화대학원대 박사논문 | 학술 | 격국·용신-직업 연관성 — 명리 측 학술 축적 예시 (공개 학술 저작의 저자명 인용 — E10 익명화 대상 아님, 라운드8 원복) |
| 88say 합참론 (許耀焜) | 실무 관행 | 명리 골격 + 자미 영역 보완(이중 스캔) |
| hokming.com 상충 처리 | 실무 관행 | 상충 = 계산·해석 오류 신호, 고객 비노출·합치점 중심 |
| LifeDNA FAQ / 린진랑 / 한국 커뮤니티 | 실무 관행 | 윤달 15일 분할법 다수파, 본월법 소수설, 고전 규정 없음 |
| 역학동 등 | 실무 관행 | 한·중 음력 1일 어긋남 존재 → 음력 변환 한국(KASI) 기준 강제 |
| (미확인) 공주대 자미두수 박사논문(2014) | 확정 불가 | RISS 직접 검색 필요 |

"명리=추상 기세 / 자미=구체 영역·시기" 통설: 학술 근거 없음, 실무 관행 수준. 반대 견해도 존재. → 설계는 "영역 라벨링 구조의 차이"로만 채택 (docs/03 §통합).

## F. 대운 起運 산출 축 (확인 2026-08-22~23, 상세 docs/27)

| 출처 | 구분 | 핵심 확인 내용 | 프로젝트 적용 |
|---|---|---|---|
| 三命通會 卷二 論大運 (古文島 https://m.guwendao.net/guwen/bookv_8dc528e1b59d.aspx · udn 전재 https://blog.udn.com/DejaVu/3146071) | 고전(1차) | 「大運以生日後未來節氣**日時**為數」 · 예시 「二十四日巳時生 … 二十九日申時立春 … 五日三時」 · 「實經歷過」 | 起運 거리 = 출생 時辰(시주와 동일)↔절입 時辰, 日·時 단위. 대운수 = 만 나이. docs/03 起運 행 근거 |
| 淵海子平 起大運法 (ichingtrilogy 卷一 전재 https://ichingtrilogy.com/post/yuan-hai-zi-ping-01/) | 고전(1차, 전재본) | 「凡起大運，俱從所生之日 … 數至未來節 … 折除三日為一歲」 | 同上(日 단위 규칙). 四庫本 직접 대조 미완 |
| 6tail lunar-python 八字 문서 https://6tail.cn/calendar/lunar.bazi.html + `eightchar/Yun.py` 1.4.8 | 공식(구현체) | 流派1(기본)=3天1年·1天4個月·1時辰10天, 流派2=4320分1年. `getSolar()` 가 거리·시진 버킷·앵커 3역할 겸직, 23시=亥 특례 | 현행 시진 버킷이 CST 프레임인 원인. 起運 자체 계산으로 이관 |
| 蘇民峰 命理教室 / 聚賢館 羅量 / udn Franker | 실무 관행(중화권) | 日·時辰 누적 후 3日=1歲·1時辰=10日; 분 단위 사례도 존재 | 折除 규칙 확인 |
| 위키백과 대운 / KNS 제31강(백민 명리학개론) / brunch saju6969 | 실무 관행(한국 가) | 일수÷3, 나머지 1 버림·2 올림 또는 반올림, 만 나이 | 시·분 무시 계열 |
| sajumania FAQ https://sajumania.com/info/faq.php | 실무 관행(한국 나) | 「시간과 분까지 계산」, DE431 입기시각, 8개월 이상 반올림 | 분 단위 정밀 계열 |
| sajustudy https://www.sajustudy.com/155 | 실무 관행(한국) | 三命通會 「實經歷過」 로 대운수 = 만 나이 논증 | 현행 `start_age` 만 나이 주석 근거 |
| sajumanse.com/calculation · 정해 만세력 doc.8-codes.com | 실무 관행(한국) | 「시주에만 진태양시」·「절기는 날짜 단위」 / 「일반 대운수와 다른 개념」 | 한국 서비스의 起運 시제는 공개 문서로 확인 불가(確定) |
| (확인 불가) 포스텔러·더큼·원광 내부 起運 시제 | 확정 불가 | 스토어 설명만 존재 | 근거로 쓰지 않음 |
