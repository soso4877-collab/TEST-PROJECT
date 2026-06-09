"""사주도령 붙여넣기용 HTML 생성기 (클릭 복사 + 글자수 + 시작일 자동치환).

카피 블록을 구조 데이터(BLOCKS)로 보유 → 자체완결 HTML 1장 렌더(외부 의존 0).
주석·근거(심리기법/윤리)는 본문에서 분리 — 근거는 templates/*.md 참고.
{{START}}/{{END}} 토큰은 페이지 상단 '시작일' 입력 시 'M월 D일'로 자동 치환(접수 5일).

사용: python saju-growth-system/automation/paste_html_build.py [출력경로]
기본 출력: saju-growth-system/PASTE-READY.html
"""

import json
import os
import sys

# limit: 카카오 한도(글자). type: text/button/info
BLOCKS = [
    {
        "section": "0. 먼저 고칠 고장(체크만)",
        "title": "관리자센터 토글",
        "type": "info",
        "limit": 0,
        "body": "① 채팅방 > 리스트 메뉴 사용 = ON  /  ② '직업·사업·이동' 자동응답 재연결  /  ③ 웰컴 버튼 2개",
    },
    {
        "section": "1. 웰컴메시지",
        "title": "웰컴 내용",
        "type": "text",
        "limit": 300,
        "body": "안녕하세요, 사주도령입니다.\n지금 가장 마음에 걸리는 건 연애인가요, 직업인가요, 아니면 큰 방향인가요?\n\n저는 명리로 인생의 '큰 구조'를, 자미두수로 '세부 타이밍'을 교차해서 봅니다.\n운명을 단정하는 게 아니라, 지금의 나를 더 깊이 이해하고\n선택의 기준을 함께 찾는 일이에요.\n\n그동안 많은 분들의 고민을 함께 봐 왔습니다.\n\n먼저, 지금 가장 궁금한 한 가지부터 골라볼까요?\n아래 메뉴에서 [나에게 맞는 풀이 고르기]를 눌러주세요 ↓",
    },
    {
        "section": "1. 웰컴메시지",
        "title": "웰컴 버튼1(소식)",
        "type": "button",
        "limit": 10,
        "body": "구성·가격 보기",
    },
    {
        "section": "1. 웰컴메시지",
        "title": "웰컴 버튼2(소식)",
        "type": "button",
        "limit": 10,
        "body": "실제 후기 보기",
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "① 나에게 맞는 풀이 고르기",
        "type": "text",
        "limit": 400,
        "body": "지금 가장 마음이 가는 주제 하나를 골라보세요.\n\n▶ 연애·결혼의 흐름과 타이밍이 궁금하다\n   → 메뉴 [연애·결혼 흐름 보기]\n▶ 이직·사업·이동, 지금 움직여도 될지 궁금하다\n   → 메뉴 [직업·사업·이동 결정 기준]\n▶ 내 사주의 큰 구조부터 알고 싶다\n   → 메뉴 [사주풀이 구성 보기]\n\n고른 주제에 맞춰 명리(큰 구조)와 자미두수(세부 타이밍)를 교차해 해석해 드려요.\n바로 신청은 [신청 방법(필수)]에서 안내합니다.",
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "② 사주풀이 구성 보기",
        "type": "text",
        "limit": 400,
        "body": "[정통 사주 풀이 — 무엇을 보는가]\n1) 사주 원국  2) 오행의 상호작용  3) 십성 분석\n4) 초년·중년·말년운 및 종운  5) 신년운세  6) 용신\n7) 신강·신약  8) 조심할 부분·개운 방향  9) 신살\n10) 합·형·충·파·해 원진  11) 신살과 길성  12) 운세 흐름\n\n여기에 자미두수 교차로 '세부 타이밍'을 더해 봅니다.\n→ 가격은 [가격 보기], 신청은 [신청 방법(필수)]",
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "③ 가격 보기",
        "type": "text",
        "limit": 400,
        "body": "[사주도령 풀이 안내]\n\n■ 심층 교차(프리미엄) · 59,000원\n  명리 × 자미두수 12궁 교차 + 향후 5년 흐름 + 추가질문 1회\n\n■ 교차 리딩(코어) · 29,000원  ★ 가장 많이 선택해요\n  원국 · 2026 대운 · 궁금한 1주제 심화 + 자미 교차 + 추가질문 1회\n  (구성 상당 55,000 → 29,000)\n\n■ 미니 리딩(입문) · 9,900원\n  연애·직업·재물 중 1가지 핵심 요약\n\n옵션) 궁합 추가 +20,000 · 당일 우선납기 +5,000\n[재오픈 첫 주, {{END}}까지만 신청 받아요]\n\n신청은 [신청 방법(필수)]에서.",
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "④ 실제 후기 보기",
        "type": "text",
        "limit": 400,
        "body": '사주도령을 찾아주신 분들의 실제 후기예요. (동의받은 후기만 게시)\n"단순한 몇 줄이 아니라, 제 상황을 깊이 짚어주셨어요."\n\n→ 후기 모음 보기: 아래 [후기 보러가기]\n풀이가 궁금하면 [나에게 맞는 풀이 고르기]부터.',
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "⑤ 신청 방법(필수)",
        "type": "text",
        "limit": 400,
        "body": "[신청 방법]\n아래를 채팅으로 보내주세요.\n▶ 이름 :\n▶ 생년월일 (양력/음력) :\n▶ 태어난 시간 (모르면 '모름') :\n▶ 성별 :\n▶ 가장 궁금한 1가지 :\n▶ 찾아주신 경로 :\n\n입금 계좌는 신청 정보 확인 후 채팅으로 안내드려요 (예금주: 사주도령).\n입금자명은 신청 성함과 같게 적어주시면 바로 확인돼요.\n받는 즉시 '확인되었습니다'를 보내고, 명식 직접 검수 후\n명리×자미 교차로 작성해 24시간 이내(영업시간 기준)에 보내드려요.\n대부분 더 빨리 도착해요.\n늦어지면 이 채팅으로 바로 문의 주세요 — 끝까지 책임지고 보내드려요.\n\n* 결과를 보장하는 점이 아니라, 참고용 해석 자료입니다.",
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "⑥ 연애·결혼 흐름 보기",
        "type": "text",
        "limit": 400,
        "body": "[연애·결혼 풀이 항목]\n▶ 연애운 + 결혼운 — 다가올 사랑·결혼의 흐름\n▶ 연애 + 결혼 + 재물 — 사랑과 돈이 함께 열리는 시기\n▶ 상대와의 궁합 + 결혼운 — 두 사람의 인연과 결혼 후 흐름\n\n명리(구조) × 자미두수(타이밍) 교차로 '선택의 기준'을 함께 봐요.\n→ 가격은 [가격 보기], 신청은 [신청 방법(필수)]",
    },
    {
        "section": "2. 채팅방 메뉴",
        "title": "⑦ 직업·사업·이동 결정 기준",
        "type": "text",
        "limit": 400,
        "body": "[직업·사업·이동 풀이 항목]\n▶ 직업운 — 나에게 맞는 일의 방향·강점\n▶ 직업 + 재물 — 일과 돈의 흐름을 함께\n▶ 이동·이사 — 지금 움직여도 될지, 방향·시기 참고\n▶ 사업 적합도 — 조직형 / 독립형 성향 해석\n\n'결정의 기준'을 명리·자미두수 교차로 짚어드려요(단정 아님).\n→ 가격은 [가격 보기], 신청은 [신청 방법(필수)]",
    },
    {
        "section": "3. 5일 재활성 발송",
        "title": "M1 (D1·유료) 가치+예고",
        "type": "text",
        "limit": 1000,
        "body": "(광고) 사주도령\n\n그동안 채널을 비워뒀습니다. 이제 다시 문을 엽니다.\n\n돌아온 김에, 올해 흐름의 큰 줄기 하나를 먼저 짚어 보내드릴게요.\n[일주로 보는 2026 키워드] — 채팅으로 생년월일시를 남겨주시면\n명리로 큰 구조를, 자미두수로 '때'를 교차해 방향을 짚어드립니다.\n\n이번 재오픈에 맞춰, 5일간만 신청을 받습니다.\n교차 리딩을 다시 엽니다. 자세한 건 모레 안내드릴게요.\n\n문의: 이 채팅 / 무료 수신거부: [카카오 자동]",
    },
    {
        "section": "3. 5일 재활성 발송",
        "title": "M2 (D2·무료소식) 스토리",
        "type": "text",
        "limit": 1000,
        "body": "[사주도령 이야기]\n명리만으로는 '큰 구조'는 보여도 '언제'가 흐릿합니다.\n그래서 저는 자미두수를 교차해 '시기'까지 함께 읽습니다.\n\n같은 사주도 흐름의 '때'를 얹으면 답이 달라져요.\n그 차이를 수많은 분들과 확인해 왔습니다.\n\n내 사주의 큰 구조와 때가 궁금하면 [나에게 맞는 풀이 고르기]부터 보세요.",
    },
    {
        "section": "3. 5일 재활성 발송",
        "title": "M3 (D3·유료) 오퍼 공개",
        "type": "text",
        "limit": 1000,
        "body": '(광고) 사주도령\n\n재오픈 첫 주, 5일간만 신청을 받아요. [{{START}} ~ {{END}}]\n\n■ 심층 교차(프리미엄) 59,000원\n  명리 × 자미두수 12궁 교차 + 향후 5년 흐름 + 추가질문 1회\n■ 교차 리딩(코어) 29,000원  ★ 가장 많이 선택해요\n  원국·2026 대운·궁금한 1주제 + 자미 교차 + 추가질문 1회\n■ 미니 리딩(입문) 9,900원\n\n명리로 큰 구조를, 자미두수로 세부 타이밍을 교차해 봅니다.\n운명을 단정하는 게 아니라, 선택의 기준을 함께 찾는 풀이예요.\n\n이번 기간이 지나면 다음 배치까지 접수를 닫아요.\n신청: 이 채팅에 "재오픈"과 함께 생년월일시를 남겨주세요.\n문의: 이 채팅 / 무료 수신거부: [카카오 자동]',
    },
    {
        "section": "3. 5일 재활성 발송",
        "title": "M4 (D4·무료소식) 후기+이의해소",
        "type": "text",
        "limit": 1000,
        "body": "[자주 받는 질문]\n\"사주는 다 비슷한 말 아닌가요?\"\n\n명리만 보면 큰 틀은 같아 보일 수 있어요.\n그래서 저는 자미두수를 교차해 '내 상황의 세부 타이밍'까지 봅니다.\n같은 일주라도 결론이 달라지는 이유예요.\n\n실제 후기는 [실제 후기 보기]에서 확인하실 수 있어요.\n(동의받은 후기만 게시합니다)\n재오픈 첫 주 접수는 모레까지예요.",
    },
    {
        "section": "3. 5일 재활성 발송",
        "title": "M5 (D5·유료) 마감",
        "type": "text",
        "limit": 1000,
        "body": '(광고) 사주도령\n\n재오픈 첫 주 접수는 오늘까지예요. [{{END}}]\n\n한 분 한 분 명식을 직접 검수해 써 드리느라\n접수를 기간으로 나눠 운영해요. 내일부터는 접수를 잠시 닫습니다.\n(지금 기간에 신청하시면 첫 배치로 받아보실 수 있어요)\n\n망설여진다면, 지금 가장 궁금한 한 가지부터 가볍게 물어보셔도 돼요.\n신청: 이 채팅에 "재오픈"과 함께 생년월일시 / 문의: 이 채팅\n무료 수신거부: [카카오 자동]',
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "동선 안내(먼저 읽기)",
        "type": "info",
        "limit": 0,
        "body": "프로필 링크(IG·Threads 공통) = 카카오 채팅 직링크: pf.kakao.com/_AXbxhn/chat\n하이라이트 커버 3종: ① 어떻게 보나요(구성) ② 이런 분이 봤어요(후기) ③ 신청 전 읽기(신청법) — 각 마지막 장에 채팅 링크 스티커\n게시물당 CTA는 1개만(댓글 또는 채팅 중 택1, 동시 유도 금지)\n※ 아래 '제작 스크립트' 카드(캐러셀/릴스/스토리/Shorts/TikTok)는 그대로 게시용이 아니라 촬영·편집 지시 포함 — 라벨(1장:/[0-3초] 등)은 빼고 사용",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "IG 프로필 bio",
        "type": "text",
        "limit": 150,
        "body": "이직·연애·재물 결정이 흔들릴 때 — 큰 구조와 세부 타이밍을 교차해 봅니다\n명리(큰 구조) × 자미두수(세부 흐름) · 사주도령\n운명 단정 X · 선택의 기준을 함께 찾는 풀이\n↓ 지금 궁금한 한 가지, 채팅으로 가볍게",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "Threads 프로필 bio",
        "type": "text",
        "limit": 150,
        "body": "명리로 큰 구조, 자미두수로 세부 타이밍을 교차해 읽어드려요\n운명 단정이 아니라, 선택의 기준을 함께 찾는 쪽\n프로필 링크 → 채팅으로 지금 궁금한 한 가지부터",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "Threads ① 큰틀공감",
        "type": "text",
        "limit": 500,
        "body": "분명 남들만큼은 버는데, 왜 손에 남는 게 없을까.\n\n사주에서 이건 '버는 자리'와 '지키는 자리'가 따로 노는 구조예요.\n타고난 그릇이 작아서가 아니라, 흐름이 어긋나 있는 거죠.\n(예컨대 경오일주는 그릇이 큰 편인데도 이 구조에 걸리면 손에 안 남아요.)\n\n돈이 들어와도 안 모이는 편이라면, 댓글에 생년(또는 일주)을 적어주세요.\n큰 흐름과 시기를 교차해 방향을 짚어 답을 달아드립니다.",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "Threads ② 숫자형",
        "type": "text",
        "limit": 500,
        "body": "들어오는 돈은 있는데 이상하게 안 모인다면, 이유가 있습니다.\n돈이 새는 명식 패턴은 크게 3가지인데, 2번이 제일 흔해요.\n\n1) 들어오는 길은 넓은데 나가는 길이 더 넓은 경우\n2) 벌이는 좋은데 '관리 자리'가 비어 통제가 약한 경우\n3) 사람·인정에 쓰느라 흐름이 빠지는 경우\n\n본인 같으면 ㅇ, 아니면 ㄴ 댓글 주세요. 패턴별로 짚어드릴게요.",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "Threads ③ 자기관련형",
        "type": "text",
        "limit": 500,
        "body": '"나는 분명 잘 버는데, 왜 통장은 늘 그대로지?"\n이건 특정 사주만의 얘기가 아닙니다. 같은 고민, 의외로 많아요.\n\n본인 얘기 같은 분, 댓글에 생년(또는 일주)을 적어주세요.\n큰 구조와 시기를 교차해 흐름을 짚어드립니다.',
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "IG 캐러셀 6장 (제작 스크립트)",
        "type": "text",
        "limit": 0,
        "body": "1장(표지): 분명 남들만큼은 버는데 / 왜 손에 남는 게 없을까\n2장: 타고난 '재물 그릇'은 큰 편 — 버는 힘은 충분합니다\n3장: 문제는 '지키는 자리'. 버는 자리와 따로 놀면 손에 안 남아요\n4장: 돈 새는 패턴 3가지 ① 나가는 길이 더 넓음 ② 관리 자리 공백 ③ 사람·인정에 과지출\n5장: 예컨대 경오일주는 그릇이 큰데도, '세부 흐름(자미두수)'에 따라 방향이 갈립니다\n6장(마무리): 당신은 어느 쪽인가요? 댓글에 생년(또는 일주)을 적어주시면 흐름을 짚어드립니다",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "IG 릴스 30초 (제작 스크립트)",
        "type": "text",
        "limit": 0,
        "body": "[0-3초] 자막: 분명 남들만큼은 버는데, 왜 손에 안 남을까?\n[3-8초] 자막: 버는 그릇은 큰데 — '지키는 자리'가 비어 있으면\n[8-18초] 자막: ①나가는 길이 더 넓고 ②관리 자리가 공백이고 ③사람한테 다 써요\n[18-25초] 자막: 같은 사주도 세부 흐름(자미두수)에 따라 방향이 갈립니다\n[25-30초] 자막: 내 흐름은 어느 쪽? 프로필 채팅으로 한 가지만 물어보세요",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "IG 스토리 3프레임 (제작 스크립트)",
        "type": "text",
        "limit": 0,
        "body": '프레임1: "잘 버는데 안 모이는 편?" + 투표 스티커 [나도 그래 / 난 반대]\n프레임2: "버는 자리 ≠ 지키는 자리. 둘이 따로 놀면 손에 안 남을 수 있어요. / 같은 사주도 월지·시지·세부 흐름에 따라 또 갈려요" (배경 단색 다크브라운/딥네이비 + 화이트 텍스트)\n프레임3: "내 흐름은 어느 쪽일까?" + 질문 스티커 + 채팅 링크 스티커',
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "YouTube Shorts (제작 스크립트)",
        "type": "text",
        "limit": 0,
        "body": "제목(검색용): 잘 버는데 왜 돈이 안 모일까? (경오일주 예시) #사주 #재물운 #일주\n[0-3초] 분명 남들만큼은 버는데, 왜 통장은 항상 제자리일까요?\n[3-8초] 이유가 있어요. 버는 자리와 지키는 자리가 따로 놀거든요.\n[8-14초] 패턴이 3가지인데. 첫째, 나가는 길이 더 넓은 구조.\n[14-19초] 둘째, 관리 자리 자체가 공백인 경우. 셋째, 사람·인정에 흐름이 빠지는 경우.\n[19-25초] 예컨대 경오일주는 그릇이 큰데도, 이 흐름은 자미두수로 봐야 선명해져요.\n[25-30초] 다음 편에서 어떻게 다른지 이어 풀어드립니다. 구독 눌러두세요.",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "TikTok (제작 스크립트)",
        "type": "text",
        "limit": 0,
        "body": '화면 텍스트 오버레이(0초): "잘 버는데 왜 안 모이지?"\n캡션 첫 줄(TikTok 검색용): 잘 버는데 돈 안 모이는 이유\n본문: 버는 자리 따로, 지키는 자리 따로 — 명식에 답이 있어요. 3가지 패턴 중 어느 쪽?\n마무리(CTA): 본인 얘기 같으면 댓글에 생년(또는 일주) 적어주세요\n해시태그: #사주 #일주 #재물운\n사운드: 잔잔한 성찰·집중형(로파이·피아노 계열). 주제와 괴리되는 밈 사운드는 제외.',
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "카카오 Jab 메시지(무료소식·가치선행)",
        "type": "text",
        "limit": 1000,
        "body": "(광고) 사주도령\n\n분명 남들만큼은 버는데, 왜 손에 남는 게 없을까요?\n\n버는 자리와 '지키는 자리'가 따로 노는 명식 구조 — 3가지 패턴 중\n어느 쪽인지는 일주 하나가 아니라 큰 흐름(명리)과 세부 타이밍(자미)을\n같이 봐야 윤곽이 나옵니다.\n\n궁금한 한 가지가 생기면 이 채팅으로 편하게 적어주세요.\n\n문의: 이 채팅 / 무료 수신거부: [카카오 자동]",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "게시물 CTA 3종 (택1 라벨)",
        "type": "text",
        "limit": 0,
        "body": "소프트: 당신은 어느 쪽인가요? 댓글에 생년(또는 일주)을 적어주시면 흐름을 짚어드립니다.\n직접: 내 재물 흐름이 어느 쪽인지, 프로필 채팅으로 한 가지만 가볍게 물어보세요.\n운영안내: 이번 주 재오픈 기간 중에는 교차 리딩 접수를 같이 받습니다.",
    },
    {
        "section": "4. SNS 게시(Day4)",
        "title": "A/B 대안 후킹 3종 (택1)",
        "type": "text",
        "limit": 0,
        "body": '구조형: "버는 힘은 충분한데, 지키는 자리가 비어 있으면 돈은 손에 안 남습니다."\n교차형: "명리로는 재물운인데, 자미두수로 보면 \'왜 안 쌓이는지\'가 보여요."\n완화형: "큰 그릇은 타고났어도, 흐름이 어긋나 있으면 그 그릇은 채워지기 어렵습니다."',
    },
    {
        "section": "5. 콜드 소식 랜딩(Route B)",
        "title": "소식 랜딩 본문(콜드 신규용)",
        "type": "text",
        "limit": 0,
        "body": "사주를 봐도, 내 얘기 같지 않으셨나요?\n\n흔한 사주풀이가 '큰 틀'에서 멈추기 때문입니다.\n명리로 큰 구조는 보여도 '그래서 지금, 언제'가 흐릿하거든요.\n\n저는 사주도령입니다.\n명리로 인생의 큰 구조를, 자미두수로 세부 타이밍을 교차해\n'때'까지 함께 읽습니다.\n운명을 단정하는 게 아니라, 지금의 나를 더 깊이 이해하고\n선택의 기준을 함께 찾는 일이에요.\n\n\n■ 무엇을 보나요 (정통 풀이 + 자미 교차)\n\n사주 원국 · 오행의 상호작용 · 십성 분석\n초년·중년·말년운 및 종운 · 신년운세 · 용신 · 신강신약\n조심할 부분과 개운 방향 · 신살 · 합충형파해 · 운세 흐름\n\n여기에 자미두수 12궁 교차로 '세부 타이밍'을 더합니다.\n같은 일주라도 결론이 달라지는 이유예요.\n\n\n■ 풀이 안내\n\n심층 교차(프리미엄) · 59,000원\n  명리 × 자미두수 12궁 교차 + 향후 5년 흐름 + 추가질문 1회\n  (구성 상당 110,000 → 59,000)\n\n교차 리딩(코어) · 29,000원   ★ 가장 많이 선택해요\n  원국 · 2026 대운 · 궁금한 1주제 심화 + 자미 교차 + 추가질문 1회\n  (구성 상당 55,000 → 29,000)\n\n미니 리딩(입문) · 9,900원\n  연애 · 직업 · 재물 중 1가지 핵심 요약\n  사주가 처음이거나 한 번만 써보고 정하고 싶다면 여기서 시작하세요.\n  가볍게 확인하고 다음 단계를 정하셔도 돼요.\n\n\n■ 신청 전에 확인하세요\n\n· 받으시는 것: 명리 × 자미두수 교차 해석 자료 + 추가질문 1회(코어·프리미엄)\n· 입금 계좌는 신청 정보 확인 후 채팅으로 안내드려요 (예금주: 사주도령).\n  입금자명을 신청 성함과 같게 적어주시면 바로 확인돼요.\n· 받는 즉시 명식을 직접 검수해 작성하고, 입금 확인 후 24시간 이내\n  (영업시간 기준)에 보내드려요. 대부분 더 빨리 도착해요.\n· 전달이 늦어지면 채팅으로 바로 연락 주세요. 확인 즉시 직접 챙겨드려요.\n\n* 결과를 보장하는 점이 아니라, 참고용 해석 자료예요.\n\n\n■ 신청 방법\n\n아래 [채팅으로 신청하기]를 누르고, \"소식\"과 함께 보내주세요.\n이름 / 생년월일(양력·음력) / 태어난 시간(모르면 '모름') / 성별 / 가장 궁금한 1가지\n\n잘 모르는 항목은 '모름'으로 보내셔도 돼요. 채팅으로 바로 여쭤볼게요.\n먼저 [실제 후기]와 [풀이 구성]을 보고 결정하셔도 괜찮아요.",
    },
    {
        "section": "5. 콜드 소식 랜딩(Route B)",
        "title": "소식 버튼(3개 권장)",
        "type": "info",
        "limit": 0,
        "body": "[채팅으로 신청하기] → 카카오 채팅 pf.kakao.com/_AXbxhn/chat\n[실제 후기 보기] → 후기 모음 소식/하이라이트\n[풀이 구성 자세히] → 구성 소식 또는 채팅 메뉴 ②\n(카카오 소식 버튼 최대 10개 · 3개 권장)",
    },
    {
        "section": "5. 콜드 소식 랜딩(Route B)",
        "title": "후기 블록(동의받은 것만)",
        "type": "info",
        "limit": 0,
        "body": '실제로 받아보신 분들의 이야기예요. (동의받은 후기만 게시합니다)\n\n"단순히 좋은 말이 아니라, 제 상황을 콕 짚어주셔서 정리가 됐어요."\n"명리랑 자미두수를 같이 보니 \'왜\'가 이해됐어요."\n\n— 여기에 실제 후기 2~3개를 캡처/인용으로 교체. 미보유 시 이 블록 생략(창작 금지).',
    },
    {
        "section": "5. 콜드 소식 랜딩(Route B)",
        "title": "IG→소식 유도 동선",
        "type": "info",
        "limit": 0,
        "body": "IG 게시물 CTA(전환글): 더 궁금하면 프로필 링크 → '사주도령 풀이 안내' 소식부터 보세요.\n프로필 링크: 기본은 카카오 채팅 직링크(웜). 콜드 캠페인 기간엔 소식 URL로 임시 교체 A/B 가능.\n측정: '소식' 키워드 신청 수 / 소식 조회 대비 채팅 전환(daily-tracker.xlsx).",
    },
    {
        "section": "6. 2차 팔로업·업셀",
        "title": "R1 문의 미결제(1:1·광고표기 불필요)",
        "type": "text",
        "limit": 0,
        "body": "○○님, 지난번 문의 주셨던 거 편하게 이어서 도와드리려고요.\n\n혹시 결정에 걸리는 부분이 있으셨을까요?\n구성이 궁금하시면 [풀이 구성]을, 어떤 톤인지 보고 싶으시면\n[실제 후기]를 먼저 보셔도 좋아요.\n(비슷한 고민으로 받아보신 분들 후기도 거기 있어요)\n\n가장 궁금한 한 가지만 가볍게 물어보셔도 됩니다.\n지금 결정이 안 되셔도 전혀 괜찮아요.",
    },
    {
        "section": "6. 2차 팔로업·업셀",
        "title": "R1-B 무응답 시 D+2(1:1·1회만)",
        "type": "text",
        "limit": 0,
        "body": "○○님, 며칠 전 여쭤본 게 부담되셨다면 죄송해요.\n딱 하나만 여쭤볼게요 — 구성이 궁금하신 걸까요,\n아니면 가격이나 시작 타이밍이 걸리시는 걸까요?\n\n뭐가 걸리는지만 알려주시면, 거기에 맞춰 짧게 도와드릴게요.",
    },
    {
        "section": "6. 2차 팔로업·업셀",
        "title": "R2 무응답 친구(광고·마감 후 다음안내)",
        "type": "text",
        "limit": 1000,
        "body": '(광고) 사주도령\n\n지난주 재오픈 접수는 예정대로 마감했어요.\n못 보고 지나치신 분들이 계셔서, 짧게만 남겨요.\n\n지금 당장 풀이를 받지 않으셔도,\n[일주로 보는 2026 키워드]는 채팅으로 생년월일시만 주시면\n올해 흐름의 큰 줄기 하나를 짚어 보내드립니다.\n\n다음 접수 열릴 때 가장 먼저 알려드릴까요?\n원하시면 이 채팅에 "다음 알림"이라고만 남겨주세요.\n\n문의: 이 채팅 / 무료 수신거부: [카카오 자동]',
    },
    {
        "section": "6. 2차 팔로업·업셀",
        "title": "U1 구매자 업셀(1:1·만족확인 후)",
        "type": "text",
        "limit": 0,
        "body": "○○님, 보내드린 풀이는 도움이 되셨을까요?\n읽으시다 더 궁금한 부분 있으면 편하게 말씀 주세요.\n\n혹시 더 깊게 보고 싶으신 주제가 있다면,\n· 향후 5년 흐름·세부 타이밍을 자미두수 12궁 교차로 더 깊이 = 심층 교차(프리미엄)\n· 상대와의 인연·궁합이 궁금하시면 = 궁합 추가(+20,000)\n이렇게 이어서 봐드릴 수 있어요.\n\n지금 바로가 아니어도 괜찮아요. 필요할 때 편하게 찾아주세요.",
    },
    {
        "section": "6. 2차 팔로업·업셀",
        "title": "U2 후기 요청(1:1·동의/익명)",
        "type": "text",
        "limit": 0,
        "body": "도움이 되셨다니 저도 기뻐요.\n\n괜찮으시면 짧은 한 줄 후기를 남겨주실 수 있을까요?\n같은 고민을 하는 분들에게 큰 참고가 돼요.\n(공개 시 성함은 익명/이니셜로, 동의해주신 내용만 게시해요)",
    },
]

HEAD = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>사주도령 붙여넣기 카피</title>
<style>
:root{--bg:#0f1410;--card:#fff;--ink:#1c241c;--muted:#6b776b;--accent:#2f6b3a;--bad:#c0392b;--chip:#eaf0e6}
*{box-sizing:border-box}
body{margin:0;background:#11160f;color:#e9efe6;font-family:'Pretendard',system-ui,'Malgun Gothic',sans-serif;line-height:1.6}
header{padding:18px 16px;background:#16200f;position:sticky;top:0;z-index:5;border-bottom:1px solid #2a3a24}
h1{font-size:18px;margin:0 0 8px}
.ctrl{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-size:13px}
.ctrl input{padding:6px 8px;border-radius:8px;border:1px solid #3a4a32;background:#0f150c;color:#e9efe6}
.note{color:#9fb097;font-size:12px;margin-top:6px}
main{max-width:760px;margin:0 auto;padding:16px}
h2{font-size:15px;color:#bcd3b0;margin:22px 4px 8px;border-left:3px solid var(--accent);padding-left:8px;scroll-margin-top:140px}
#toc{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
#toc a{font-size:12px;color:#bcd3b0;background:#1b2417;border:1px solid #2f3b30;border-radius:999px;padding:3px 9px;text-decoration:none}
#toc a:hover{background:#2f6b3a;color:#fff}
.card{background:var(--card);color:var(--ink);border-radius:12px;padding:12px;margin:10px 0;box-shadow:0 1px 4px rgba(0,0,0,.3)}
.card.info{background:#fef9e7;color:#5b4b14}
.row{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px}
.t{font-weight:700;font-size:14px}
.cnt{font-size:12px;color:var(--muted)}
.cnt.bad{color:var(--bad);font-weight:700}
pre{white-space:pre-wrap;word-break:break-word;background:#f4f7f2;border:1px solid #e0e8db;border-radius:8px;padding:10px;margin:0;font-family:inherit;font-size:14px}
.btn{border:0;background:var(--accent);color:#fff;border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer}
.btn:active{transform:scale(.97)}
.btn.copied{background:#1d4727}
.acct{background:#eef4ec;border:1px dashed #2f6b3a;border-radius:8px;padding:8px;margin-top:8px;font-size:12px;color:#2f6b3a}
footer{max-width:760px;margin:0 auto;padding:18px 16px;color:#9fb097;font-size:12px}
</style></head><body>
<header>
<h1>사주도령 — 붙여넣기 카피 (클릭 복사)</h1>
<div class="ctrl">
<label>접수 시작일 <input type="date" id="start"></label>
<span id="range" class="cnt">(시작일을 넣으면 날짜가 자동으로 채워져요)</span>
</div>
<div class="note">각 카드의 [복사]를 눌러 카카오 관리자센터에 붙여넣으세요. 글자수는 카카오 한도 기준(초과 시 빨강). 근거·심리기법 주석은 templates/*.md 참고.</div>
<nav id="toc"></nav>
</header>
<main id="app"></main>
<footer>※ 결과·시기 보장 표현 0건 / 가격은 정가(할인 아님) / 계좌번호는 신청 후 1:1 안내. 날짜는 시작일 입력 시 자동(5일).</footer>
<script>
const BLOCKS = __DATA__;
"""

JS = r"""
function fmt(d){return (d.getMonth()+1)+"월 "+d.getDate()+"일";}
function dates(){
  const v=document.getElementById('start').value;
  if(!v){return {s:"○월○일",e:"○월○일",ok:false};}
  const s=new Date(v+"T00:00:00"); const e=new Date(s); e.setDate(e.getDate()+4);
  return {s:fmt(s),e:fmt(e),ok:true};
}
function subst(t){const d=dates();return t.split("{{START}}").join(d.s).split("{{END}}").join(d.e);}
function render(){
  const app=document.getElementById('app'); app.innerHTML="";
  const d=dates();
  document.getElementById('range').textContent = d.ok ? ("접수: "+d.s+" ~ "+d.e+" (5일)") : "(시작일을 넣으면 날짜가 자동으로 채워져요)";
  const seen=[]; BLOCKS.forEach(b=>{if(!seen.includes(b.section))seen.push(b.section);});
  document.getElementById('toc').innerHTML = seen.map((s,i)=>"<a href='#sec"+i+"'>"+esc(s)+"</a>").join("");
  let cur="";
  BLOCKS.forEach((b,i)=>{
    if(b.section!==cur){cur=b.section;const h=document.createElement('h2');h.id="sec"+seen.indexOf(cur);h.textContent=cur;app.appendChild(h);}
    const card=document.createElement('div'); card.className="card"+(b.type==="info"?" info":"");
    const body=subst(b.body);
    if(b.type==="info"){card.innerHTML="<div class='t'>"+b.title+"</div><pre style='background:transparent;border:0;padding:0'>"+esc(body)+"</pre>";app.appendChild(card);return;}
    const row=document.createElement('div'); row.className="row";
    const cnt = b.limit ? ("<span class='cnt' id='c"+i+"'></span>") : "";
    row.innerHTML="<span class='t'>"+b.title+"</span><span>"+cnt+" <button class='btn' data-i='"+i+"'>복사</button></span>";
    const pre=document.createElement('pre'); pre.textContent=body;
    card.appendChild(row); card.appendChild(pre);
    if(b.title.indexOf("신청 방법")>=0){const a=document.createElement('div');a.className="acct";a.textContent="↑ 계좌번호는 여기 적지 말고, 신청 받은 뒤 1:1 채팅으로 안내(보안). 예금주: 사주도령";card.appendChild(a);}
    app.appendChild(card);
    if(b.limit){const c=document.getElementById('c'+i); const n=body.length; c.textContent=n+" / "+b.limit; if(n>b.limit)c.className="cnt bad";}
  });
  document.querySelectorAll('.btn[data-i]').forEach(btn=>{
    btn.onclick=()=>{const i=+btn.dataset.i; const txt=subst(BLOCKS[i].body);
      navigator.clipboard.writeText(txt).then(()=>{btn.textContent="복사됨";btn.classList.add('copied');setTimeout(()=>{btn.textContent="복사";btn.classList.remove('copied');},1200);});};
  });
}
function esc(s){return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
document.getElementById('start').addEventListener('change',render);
render();
</script></body></html>
"""


def build(path):
    html = HEAD.replace("__DATA__", json.dumps(BLOCKS, ensure_ascii=False)) + JS
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[생성] {path}  ({len(BLOCKS)} 블록, {len(html):,} bytes)")


def main():
    default = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PASTE-READY.html"
    )
    build(sys.argv[1] if len(sys.argv) > 1 else default)


if __name__ == "__main__":
    main()
