# -*- coding: utf-8 -*-
"""23섹션 스키마 (보고서 §7 권장 구조) — pydantic 타입 계약."""

from __future__ import annotations

from pydantic import BaseModel, Field

# (id, 한글 제목, 그라운딩 소스 키) — 모든 해석 섹션은 source가 비면 안 됨
# 2026-06-11 재편: 27라벨 섹션 → 주제별 챕터(흐르는 산문). 배치는 피크엔드·계열위치 근거(docs/13):
# 따뜻한 도입(primacy) → 깊이 빌드업 → 신청질문 답변(개인화 피크) → 격려 마무리(recency·peak).
# 챕터 제목은 정보격차 호기심 근거로 질문형. 흡수한 옛 섹션은 주석 참조.
SECTION_SPECS: list[tuple[str, str, list[str]]] = [
    ("cover", "표지", ["input"]),
    ("toc", "목차", []),  # 정적 — 노동착시·호기심격차·책 권위(템플릿/빌더 생성)
    (
        "intro",
        "이 풀이를 읽는 법",
        ["input", "myeongni", "ziwei"],
    ),  # summary+howto+keywords. 제목 줄표(—) 제거(기호 금지, 2026-06-12)
    ("wonguk", "내 사주의 짜임", ["myeongni", "myeongni.elements"]),  # wonguk+ohaeng
    ("nature", "나의 바탕과 기질에 대하여", ["myeongni"]),  # ilgan+sipseong+character+strength
    ("frame", "격국과 신살이 더하는 결", ["myeongni"]),  # geukguk+shinsal
    ("love", "나의 사랑에 대하여", ["myeongni", "ziwei"]),
    ("work", "나의 일과 재물에 대하여", ["myeongni", "ziwei"]),  # job+wealth
    ("health", "몸과 마음을 살피며", ["myeongni", "ziwei"]),
    (
        "flow",
        "시간의 흐름에 대하여",
        ["myeongni.daewoon", "myeongni", "ziwei.yearly"],
    ),  # daewoon+thisyear+seun+monthly
    ("ziwei", "자미두수로 본 삶의 구조", ["ziwei", "ziwei.palaces"]),  # ziwei_summary+ziwei_palaces
    ("together", "두 체계를 함께 읽으며", ["crosscheck"]),  # cross
    ("consult", "신청하신 질문에 대하여", ["input", "myeongni", "ziwei"]),  # 개인화 피크
    ("closing", "마무리하며", ["myeongni.elements", "input"]),  # advice+caution+closing
    ("appendix_terms", "용어 풀이", []),  # 정적 교육(노동착시 가치 장치). 줄표 제거
    ("colophon", "글을 맺으며", []),  # 맺음 서명(절대규칙 18 개정 — 도구·AI 언급 고지 금지)
]
# 그라운딩 면제(정적 안내·교육·판권) — 해석 챕터는 source가 비면 trace 실패
_STATIC_OK = {"toc", "appendix_terms", "colophon"}


class Section(BaseModel):
    id: str
    title: str
    source_keys: list[str]
    rule_text: str  # 결정론 룰 골격(항상 안전·완결)
    final_text: str  # 최종(윤문 통과 시 polished, 아니면 rule_text)
    polished: bool = False
    guard_violations: list[dict] = Field(default_factory=list)


class GuardReport(BaseModel):
    safe_lint_total: int
    factcheck_total: int
    grounding_ok: bool
    polished_sections: int
    fallback_sections: int  # 가드 실패로 룰 원문 사용한 섹션 수
    clean: bool  # 전체 통과 여부


class Report23(BaseModel):
    sections: list[Section]
    guard: GuardReport
    concern_category: str | None = None  # Phase5 구간1: 신청 고민 분류 결과(감사·검수용)
    # factcheck 허용 토큰(set→list 직렬화). 검수 UI의 관리자 수정 재검증용 —
    # saju 객체 없이도 계산 시점과 동일한 허용 집합으로 검사(상대방 간지 포함).
    allow_tokens: dict = Field(default_factory=dict)

    def section(self, sid: str) -> Section:
        return next(s for s in self.sections if s.id == sid)
