#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""소스 후킹 1개를 채널별 드래프트(1->11)로 펼치는 라이트 글루.

외부 API 의존 없음. 파일 in/out만. LLM 윤문 전의 '뼈대'를 생성한다.
컴플라이언스: 입력 후킹에 금지어가 있으면 경고하고 표시한다(표시광고법/banned-terms).

사용 예:
  python repurpose.py --hook "경오일주는 왜 돈이 새는가" --out drafts/
  python repurpose.py --hook "..." --pillar 1   # 표준출력으로
"""

import argparse
import os
import sys

# 금지어(보장/시기 단정, 자격증, 브랜드) — research/kakao-compliance-notes.md 와 일치
BANNED = [
    "반드시",
    "100% 적중",
    "100%적중",
    "한 달 안에",
    "한달 안에",
    "확실히 풀립니다",
    "확실히 좋아집니다",
    "무조건",
    "심리상담사",
    "명리상담사",
    "심리분석사",
    "사주허브",
    "SAJUHUB",
]


def check_banned(text):
    """텍스트에서 금지어를 찾아 리스트로 반환."""
    return [w for w in BANNED if w in text]


def build_drafts(hook, pillar, topic=None):
    """큰틀 후킹 1개 -> 채널별 11개 산출물 뼈대(markdown 문자열).

    hook = 큰틀 공감 첫 줄(많은 사람이 겪는 Pain). 일주·요소는 첫 줄 금지 → 본문 심화로만.
    topic = 주제 식별자(추적 연결용). 미지정 시 hook에서 슬러그 생성.
    """
    topic_id = topic or slugify(hook)
    # 권위 톤 CTA(자기비하·"무료로 봐준다" 금지, 확신 톤·결과보장 아님)
    cta_soft = "당신은 어느 쪽인가요? 댓글에 생년(또는 일주)을 적어주시면 흐름을 짚어드립니다."
    cta_direct = "가장 궁금한 한 가지, 큰 구조와 시기를 교차해 짚어드려요. 신청은 프로필 채팅."
    cta_close = "재오픈 첫 주 접수는 기간 안에만 받습니다. 신청은 프로필 채팅."

    lines = []
    lines.append(f'# 리퍼포징 드래프트 — "{hook}"')
    lines.append(
        f"> topic_id: `{topic_id}`  ·  기둥(pillar): {pillar}  ·  추적: tracking/daily-tracker.xlsx 의 topic 열에 `{topic_id}` 기록"
    )
    lines.append(
        "> 톤: 권위·확신 / 첫 줄=큰틀 공감(일주특정 금지) / 보장표현 금지 / 첫 줄 250자 이하 / 원본성 유지\n"
    )

    lines.append("## Threads (3개) — 첫 줄=큰틀, 일주·구조는 본문 심화")
    lines.append(f"1. (큰틀 공감) {hook}\n   -> 본문 심화: 사주 구조로 좁히기(예: 일주·십성)\n   -> 오픈루프: {cta_soft}")
    lines.append(
        f"2. (숫자·구조형) {hook}\n   -> 본문: 핵심 패턴 3가지 중 2번이 제일 흔해요.\n   -> 오픈루프: 본인 같으면 ㅇ, 아니면 ㄴ 댓글 주세요. 패턴별로 짚어드릴게요."
    )
    lines.append(
        f"3. (자기관련) {hook}\n   -> 본문: 특정 사주만의 얘기가 아니에요. 같은 고민, 의외로 많아요.\n   -> 오픈루프: 댓글에 생년(또는 일주) 적어주세요. (게시 후 30분 자기답글 필수)\n"
    )

    lines.append("## Instagram 캐러셀 (카드뉴스 5~7장)")
    lines.append("- 1장: 후킹 — " + hook)
    lines.append("- 2~5장: 근거/패턴 (명식 요소로 설명)")
    lines.append("- 6장: 오픈루프 + CTA(소프트) — " + cta_soft)
    lines.append("- 7장(옵션): 미니 리포트 안내(참고용 해석)\n")

    lines.append("## Instagram Reel (30초 스크립트)")
    lines.append("- [0-3초] 후킹 자막: " + hook)
    lines.append("- [3-8초] 호기심 갭 확장")
    lines.append("- [8-22초] 핵심 패턴 2~3개")
    lines.append("- [22-27초] 자기관련성: 당신은 몇 번?")
    lines.append("- [27-30초] CTA: 프로필 링크\n")

    lines.append("## Instagram Story (3프레임)")
    lines.append("- 프레임1: 후킹 + 투표 스티커(나도 그래/난 반대)")
    lines.append("- 프레임2: 미니 인사이트")
    lines.append("- 프레임3: 질문 스티커 + 링크 스티커\n")

    lines.append("## YouTube Shorts (스크립트)")
    lines.append(f"- 제목(검색용): {hook} #사주 #운세")
    lines.append("- 9:16 자막 흐름, 첫 3초 후킹 고정, 끝에 오픈루프(다음 편)\n")

    lines.append("## TikTok (스크립트)")
    lines.append(f"- 후킹 변형: {hook}")
    lines.append("- 해시태그: #사주 #운세 #일주 · 트렌드 사운드 · 엔터/성찰 톤(보장 금지)\n")

    lines.append("## 카카오 (광고) 메시지")
    lines.append("(광고) 사주도령")
    lines.append(f"{hook}")
    lines.append("큰 흐름(명리)과 세부 타이밍(자미)을 교차해 방향을 짚어드립니다.")
    lines.append("궁금한 한 가지가 생기면 이 채팅으로 적어주세요. 문의: 이 채팅")
    lines.append("* 참고용 해석 자료이며 결과를 보장하지 않습니다. 무료 수신거부: [카카오 자동]\n")

    lines.append("## CTA 3종")
    lines.append(f"- 소프트: {cta_soft}")
    lines.append(f"- 직접: {cta_direct}")
    lines.append(f"- 마감임박: {cta_close}")

    return "\n".join(lines)


def slugify(text):
    keep = [c if c.isalnum() else "_" for c in text]
    s = "".join(keep).strip("_")
    return s[:40] or "draft"


def main(argv=None):
    p = argparse.ArgumentParser(description="큰틀 후킹 1개 -> 채널별 드래프트(1->11)")
    p.add_argument("--hook", required=True, help="큰틀 공감 후킹 첫 줄(일주특정 금지)")
    p.add_argument("--pillar", default="1", help="콘텐츠 기둥 번호 1~4")
    p.add_argument("--topic", default=None, help="주제 식별자(추적용, 미지정시 hook에서 생성)")
    p.add_argument("--out", default=None, help="출력 디렉토리(미지정시 표준출력)")
    args = p.parse_args(argv)

    hits = check_banned(args.hook)
    if hits:
        sys.stderr.write("[경고] 후킹에 금지어 발견: " + ", ".join(hits) + "\n")
        sys.stderr.write("       표시광고법/banned-terms 위반. 수정 후 사용하세요.\n")

    md = build_drafts(args.hook, args.pillar, args.topic)

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, slugify(args.hook) + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md + "\n")
        print("생성: " + path)
    else:
        print(md)

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
