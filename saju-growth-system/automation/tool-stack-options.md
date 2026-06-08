# 툴 스택 비교 (검증본)

> 검증일 2026-06-08. 근거: `research/verified-source-map.md`

## 스케줄러 (멀티채널 자동발행)

| 툴 | 자동발행 지원 | 무료티어 | 강점 | 비고 |
|---|---|---|---|---|
| **Metricool** ⭐ | IG·TikTok(공식파트너)·YT Shorts·Threads·FB | 1브랜드/네트워크 | 최광역 + 무료티어 | **1순위** |
| Publer | IG·TikTok·YT·Threads·FB·Pinterest·GBP | 3계정/10포스트 | **CSV 벌크 스케줄링** | 배치 강점, 보조 |
| Buffer | IG·TikTok·YT·Threads(2025)·FB·X | 제한적 | 단순 | 배치 약함 |
| Later | IG 중심 + Threads | 제한적 | IG 비주얼 | 멀티채널 약함 → 스킵 |

→ **권장**: Metricool 무료로 시작, 채널 늘면 유료. CSV 벌크 원하면 Publer 병행.

## 영상 (CapCut)
- **공식 공개 렌더/배치 API 없음.** Open Platform=인앱 플러그인, AI API=단일기능.
- 현실적 경로: **인앱 템플릿 + 배치 export**(수동). 또는 카드뉴스→인스타 릴스툴.
- 비공식 "CapCutAPI"(오픈소스)는 fragile → 매출 핵심작업에 사용 금지.
- 진짜 API 렌더가 필요해지면 json2video 등 별도 툴(7일 내 불필요).

## 게시 API (직접)
| 플랫폼 | 자동발행 | 제약 |
|---|---|---|
| Instagram | Graph Content Publishing | **비즈니스 계정** 필요, 24h 100건, 네이티브 스케줄 없음 |
| Threads | Publishing API(2024 GA) | 24h 250건, 앱심사 |
| TikTok | Content Posting(Direct Post) | **미감사 앱=비공개**, 감사 필요 |
| YouTube | 스케줄러 경유 | 커스텀 썸네일·관련영상 제어 없음 |

→ raw API 직접 구축 대신 **감사 통과 스케줄러(Metricool/Publer) 사용**이 "바퀴".

## iPaaS (n8n / Make / Zapier)
- 깔끔한 네이티브 IG/Threads/TikTok 발행 없음 → 게시는 스케줄러가 우월.
- 용도 한정: 시트→스케줄러 글루, AI 텍스트 생성 트리거.
- 비용: Zapier(최다앱·최고가) / Make(저렴 비주얼) / n8n(셀프호스트 최저·기술 필요).

## 카카오
- iPaaS 네이티브 카톡 **없음**. 자동발송 필요시 **SOLAPI** 브리지(AlimTalk).
- 7일 내: 관리자센터 수동 브랜드 메시지로 충분. SOLAPI는 검증 후.

## 콘텐츠 DB
- Google Sheets / Airtable / Notion 모두 공식 API. Publer는 CSV 임포트.
- → Sheets/Airtable 캘린더 → `calendar_to_csv.py` → Publer/Metricool.

## 7일 최종 스택 (노코드 우선)
```
Google Sheets/Airtable (캘린더)
   → CapCut 템플릿 (수동 배치 export) / 인스타 릴스툴
   → Metricool (무료→유료) : Reels + Threads + TikTok + Shorts 자동발행
   → (옵션) Publer : CSV 벌크
카카오 : 관리자센터 브랜드 메시지 (수동) / 필요시 SOLAPI
결제 : Google Form + 카카오 송금/계좌 + 정산 시트
입문배송 : sajugen PDF + 본인 LLM 보조 해석
```
