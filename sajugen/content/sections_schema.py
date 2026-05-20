# -*- coding: utf-8 -*-
"""23섹션 스키마 (보고서 §7 권장 구조) — pydantic 타입 계약."""

from __future__ import annotations

from pydantic import BaseModel, Field

# (id, 한글 제목, 그라운딩 소스 키) — 모든 해석 섹션은 source가 비면 안 됨
SECTION_SPECS: list[tuple[str, str, list[str]]] = [
    ("cover", "표지", ["input"]),
    ("summary", "내 사주 한 장 요약", ["myeongni", "ziwei"]),
    ("howto", "이 결과지 읽는 법", []),  # 정적 안내(그라운딩 예외 허용)
    ("keywords", "내 사주 핵심 키워드 5", ["myeongni"]),
    ("wonguk", "원국 해설", ["myeongni"]),
    ("ohaeng", "오행 밸런스", ["myeongni.elements"]),
    ("ilgan", "일간과 성향", ["myeongni.day_master"]),
    ("sipseong", "십성 구조", ["myeongni"]),
    ("strength", "강점과 취약점", ["myeongni.elements"]),
    ("character", "성격·기질 종합", ["myeongni"]),
    ("geukguk", "격국과 용신(참고)", ["myeongni"]),
    ("shinsal", "신살 풀이(참고)", ["myeongni"]),
    ("love", "연애·관계", ["myeongni", "ziwei"]),
    ("job", "직업·일", ["myeongni", "ziwei"]),
    ("wealth", "재물·돈", ["myeongni", "ziwei"]),
    ("health", "건강 — 생활 관리의 결(참고)", ["myeongni", "ziwei"]),
    ("daewoon", "대운 흐름", ["myeongni.daewoon"]),
    ("thisyear", "올해·가까운 시기", ["ziwei.yearly", "myeongni.daewoon"]),
    ("seun", "세운·월운 흐름", ["myeongni"]),
    ("monthly", "월별 흐름", ["myeongni.daewoon"]),
    ("ziwei_summary", "자미두수 명반 요약", ["ziwei"]),
    ("ziwei_palaces", "자미두수 핵심 궁", ["ziwei.palaces"]),
    ("cross", "명리×자미두수 교차검증", ["crosscheck"]),
    ("advice", "현실 적용 조언", ["myeongni.elements"]),
    ("caution", "주의할 선택 패턴", ["myeongni"]),
    ("questions", "상담 추천 질문", ["myeongni", "ziwei"]),
    ("closing", "마무리 격려", ["input"]),
    ("appendix_terms", "부록 — 용어 풀이", []),  # 정적 교육(본문 뒤 부록화)
    ("next", "다음 행동·후기·해석 한계", []),  # 정적 안내
]
# 그라운딩 면제(정적 안내·교육) — 교육 콘텐츠는 본문이 아닌 부록으로 분리
_STATIC_OK = {"howto", "appendix_terms", "next"}


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

    def section(self, sid: str) -> Section:
        return next(s for s in self.sections if s.id == sid)
