# Verified Source Map — 검증 출처 맵

> 검증일: 2026-06-08 · WebSearch/WebFetch 라이브 검증(공식 도메인 우선).
> "Official" = 플랫폼 소유 도메인 / "Secondary" = 제3자.

## 플랫폼 도달·랭킹·AI 라벨

| Area | Source | Off/Sec | Key Finding | Business Implication | Conf | Verified |
|---|---|---|---|---|---|---|
| IG Feed/Reels 랭킹 | transparency.meta.com/features/explaining-ranking/ig-feed-recommendations/ | Official | Reels 도달은 예측 완시청 중심(<3초 시청 패널티, >95% 시청 보상) + 댓글·리셰어·외부공유·팔로우 확률 | 첫 3초 강한 후킹, 짧은 루프 완시청 설계, "친구에게 공유" 유도 | High | 2026-06-08 |
| IG Explore | creators.instagram.com/grow/algorithms-and-ranking | Official | Explore는 내 Explore 활동(좋아요/저장/댓글/공유) + 비팔로우 인기콘텐츠로 랭킹. 최대 3분 Reels도 Explore 노출 | Explore가 주요 콜드도달면 — 낯선 이의 저장·공유 최적화 | High | 2026-06-08 |
| IG 원본성/추천적격 | creators.instagram.com/original-content-guidelines | Official | 테두리·워터마크·속도변경·크레딧은 원본 아님. 비원본 위주 계정은 비팔로워 추천 제한, 최근 30일 원본 다수면 회복 | 재탕/타플랫폼 워터마크(틱톡 export) 클립 금지, 자기 내레이션·고유 프레이밍 추가 | High | 2026-06-08 |
| IG 계정상태 | help.instagram.com/653964212890722 | Official(Unverified—JS) | 설정>계정 상태에서 추천 적격성 확인 | 월 1회 계정 상태 점검(추천 제한 조기 감지) | Med | 2026-06-08 |
| Threads 피드 랭킹 | transparency.meta.com/features/explaining-ranking/ig-threads-feed/ | Official | 공개+팔로우 콘텐츠를 예측 관심도로 랭킹. 사려깊은 답글·체류시간 > 수동 조회. 대화유발 우대 | 질문형 후킹으로 답글 유도(예: "당신 일주는?") | High | 2026-06-08 |
| YouTube Shorts 추천 | YT Creators(via hootsuite) | Secondary | 소규모 테스트 후 유지율·만족도(좋아요/공유/댓글)로 확장. 2025-03-31 "view" 재생시 카운트, 품질지표 "Engaged views"로 개명 | Engaged views·완시청 추적, 백카탈로그 유지(과거 숏츠 재부상) | Med | 2026-06-08 |
| TikTok For You | newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you | Official | 상호작용(좋아요/공유/팔로우/댓글/완시청)+영상정보(캡션/사운드/해시태그). 디바이스/국가 저가중. **팔로워수·과거히트 직접요인 아님** | 팔로워 무관 콜드도달 가능, 완시청·공유 우선, 트렌드 사운드/니치 해시태그 | High | 2026-06-08 |
| TikTok FYF 적격 | tiktok.com/community-guidelines/en/fyf-standards | Official | 안전/모더레이션 통과 영상만 FYF 적격. 위반 콘텐츠는 추천 제외(섀도캡) | 건강·운세 "보장" 주장 회피, 사주는 엔터/성찰 프레이밍 | High | 2026-06-08 |
| Meta AI 공개 | transparency.meta.com/policies/other-policies/meta-AI-disclosures | Official | 오인 가능 현실적 AI 이미지/영상/오디오는 "AI Info" 라벨. C2PA 자동라벨. AI 음악/텍스트/명백 창작물은 대체로 불필요 | 포토리얼 사주영상은 라벨 토글, 일러스트/스타일 아트는 면제 | High | 2026-06-08 |
| YouTube AI 공개 | YT Help(via onewrk) | Secondary | 2025-05-21부터 현실적 변형/합성 콘텐츠는 Studio 토글 공개 의무. 제작보조(스크립트/편집/색보정) 면제. 2025-07-15 YPP는 "유의미하게 독창·진정성" 요구 | 현실적 AI 장면은 토글, 각 숏츠에 고유 코멘트/음성 추가해 YPP 수익화 유지 | Med | 2026-06-08 |
| TikTok AI 공개 | newsroom.tiktok.com/en-us/new-labels-for-disclosing-ai-generated-content | Official | 완전 AI생성/중대 변형 현실적 콘텐츠 공개 의무, 경미 편집 면제. C2PA 자동라벨(2025-01). **AI 라벨이 비위반 콘텐츠 인게이지먼트 감소 안 시킴(명시)** | AI 사주영상 라벨 안전(도달 무패널티), 미공개 시 삭제 위험, 실존인물 likeness 금지 | High | 2026-06-08 |

**교차 결론**: 4개 영상 플랫폼이 2025-26년 **완시청률 + 의미있는 공유** 두 레버로 수렴.
AI 라벨은 원본·비기만이면 도달 중립. 진짜 도달 킬러 = **비원본/재탕(IG) + 대량 저품질 AI(YouTube YPP)**.

**수동 확인 필요**: (a) IG 계정상태·TikTok 추천시스템 페이지는 JS 렌더 → 앱/브라우저 직접 확인.
(b) YouTube 자체 랭킹 문구는 youtube.com/howyoutubeworks 확인.

---

## 카카오채널 컴플라이언스

| Area | Source | Off/Sec | Key Finding | Risk/Implication | Conf | Verified |
|---|---|---|---|---|---|---|
| 무료 vs 유료 | cs.kakao.com/helps_html/1073198348 ; us.business.kakao.com | Official | 웰컴 메시지(채널추가시 자동)는 무료. 친구 대량발송(구 친구톡→2026 **브랜드 메시지 자유형**)은 **수신자당 유료** | 4,000 친구 발송=매회 유료. 무료는 신규친구 웰컴 1회뿐 | High | 2026-06-08 |
| 건당 단가(추정) | channelcan/solapi(2차) | Secondary | 텍스트형 ~15원/이미지형 ~20원/와이드형 ~23원. 4,000명 이미지 ≈ 80,000원/회 | 발송 전 관리자센터 실단가 재확인 | Med | 2026-06-08 |
| 친구당 발송캡 | channelup/KIO(2차) | Secondary | 마케팅 메시지 친구당 **24h당 1통** 한도 | 하루 다중 블라스트 무의미 | Med | 2026-06-08 |
| 친구톡 종료 | channelup/solapi(2차) | Secondary | **친구톡 2025-12-31 종료** → 2026-01-01 브랜드 메시지(자유형) 자동전환 | 신규 용어/UI, 구가이드 stale | Med | 2026-06-08 |
| (광고) 표기 | kakaobusiness.gitbook.io/main/ad/infotalk/operations | Official | 광고성 분류시 프로필명에 **(광고)** 자동 prepend. 3필수: **(광고)표시 + 전송자 연락처 + 수신거부 방법** | 프로모 블라스트는 반드시 광고성 분류 | High | 2026-06-08 |
| 야간발송 금지 | law.go.kr 정보통신망법 §50 ; talk.privacy.go.kr | Official | **21:00~08:00** 영리 광고성 발송은 별도 사전동의 필요(수신시각 기준) | 프로모는 08:00~21:00 KST만 | High | 2026-06-08 |
| opt-out 무료 | law.go.kr 정보통신망법 §50 | Official | 메시지 끝에 수신거부/철회 방법 + **무료** 명시. 카카오 자동 append | 광고성 분류시 카카오가 처리, 제거 금지 | High | 2026-06-08 |
| 사전동의 | law.go.kr 정보통신망법 §50 | Official | 마케팅 메시지는 **사전 수신동의(opt-in)** 필요. 채널추가가 일반적 동의로 간주되나 기록 중요 | 채널추가 친구로 한정, 동의 기록 보관 | High | 2026-06-08 |
| 스팸/이용제한 | business.kakao.com/m/policy ; cs.kakao.com/helps_html/1073199442 | Official(본문 미파싱) | 미인가 광고성/금지방법/망법 위반시 발송제한 **최소 30일~영구**, 이용제한 가능 | 스팸신고 패턴 1회로 ≥30일 동결 위험, KIO 불법스팸 안내서 준수 | High | 2026-06-08 |
| 금지 콘텐츠 | gitbook operations | Official | 음란/사행성/유사수신/불법금융/허위광고 금지 | 사주 OK, 사행성/유사수신 프레이밍 회피 | High | 2026-06-08 |
| 표시광고법-사주 | law.go.kr 표시광고법 §3 ; ftc.go.kr | Official | 거짓·과장·기만·부당비교·비방 광고 금지. 입증불가 보장("반드시/100% 적중/한 달 안에")=거짓·과장 | **결과 보장 금지**, 계정정지+FTC 제재 위험. 기존 banned-terms와 일치 | High | 2026-06-08 |
| 자격증/효과 | 표시광고법 §3 + 자격기본법 | Official | 심리상담사/명리상담사 자격·확정 효과 보장은 부당광고/자격 오인 위험 | 학문적 해석/참고용 프레이밍, 보장 금지 | Med | 2026-06-08 |

---

## 자동화 툴 (기존 툴 우선)

| Task/Tool | Source | Off | Key Capability/Limit | 권장 | Conf | Verified |
|---|---|---|---|---|---|---|
| CapCut API/배치 | capcut.com / developers | Official | **공개 렌더/배치 API 없음**. Open Platform=인앱 플러그인, AI API=단일기능. 현실=인앱 템플릿+배치 export | CapCut 템플릿 수동, API 의존 금지 | High | 2026-06-08 |
| IG Reels 자동발행 | developers.facebook.com/docs/instagram-platform/content-publishing/ | Official | Graph API 발행, **비즈니스 계정 필요**(크리에이터 불가), 24h 100건, 네이티브 스케줄링 없음 | 스케줄러 사용(raw API 직접 X) | High | 2026-06-08 |
| Threads 자동발행 | developers.facebook.com/docs/threads/reference/publishing/ | Official | 2024-06-18 GA. 텍스트/이미지/영상/캐러셀, 24h 250건, 무료, 프로덕션은 앱심사 | 스케줄러 네이티브 발행 | High | 2026-06-08 |
| TikTok 자동발행 | developers.tiktok.com/products/content-posting-api/ | Official | Direct Post(영상/사진), **미감사 앱=SELF_ONLY(비공개)** 감사 통과 전까지 | 감사 통과 파트너 스케줄러 사용 | High | 2026-06-08 |
| YT Shorts 자동발행 | help.metricool.com (네트워크별 옵션) | Official | 자동발행 지원하나 제한(커스텀 썸네일·관련영상 제어 없음) | 허용, 썸네일 수동 | Med-High | 2026-06-08 |
| Metricool | metricool.com/pricing | Official | IG/TikTok(전계정유형, 공식파트너)/YT Shorts/Threads 진짜 자동발행. **무료=1브랜드/네트워크** | **1순위** — 최광역 + 무료티어 | High | 2026-06-08 |
| Publer | publer.com/features/threads | Official | IG/TikTok/YT/Threads 자동발행 + **벌크/CSV 스케줄링**. 무료=3계정/10포스트, 유료~$12/mo | #2 — CSV 벌크 강점 | High | 2026-06-08 |
| n8n/Make/Zapier | n8n.io/integrations + digidop | Official(dir) | 깔끔한 네이티브 IG/Threads/TikTok 발행 없음(API 배관 필요). 게시는 스케줄러가 우월 | 글루(시트→스케줄러·AI생성)로만 한정 | High | 2026-06-08 |
| 카카오 on iPaaS | zapier.com/apps/solapi | Secondary | iPaaS 네이티브 카톡 없음. **SOLAPI** 브리지(AlimTalk) | 필요시 SOLAPI, 7일 내 불필요 | Med-High | 2026-06-08 |
| 콘텐츠 DB | n8n/Zapier dir + publer | Official | Notion/Airtable/Sheets 공식 API + Publer가 CSV 임포트 | Sheets/Airtable→Publer/Metricool | High | 2026-06-08 |

**7일 권장 스택(노코드 우선)**: Google Sheets/Airtable(캘린더) → CapCut 템플릿(수동 배치 export)
→ **Metricool**(무료→유료)로 Reels+Threads+TikTok+Shorts 자동발행. CSV 벌크 원하면 **Publer** 추가.
카카오는 필요시에만 **SOLAPI**.
