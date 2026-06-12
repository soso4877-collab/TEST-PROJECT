# -*- coding: utf-8 -*-
"""콘텐츠 빌더 — SajuResult → 23섹션 룰 골격 → (옵션)LLM 윤문 → 가드 → Report23.

가드: §12 안전 린트 + 사실일치 린트 + 그라운딩. 윤문이 가드 실패 시 룰 원문 폴백.
"""

from __future__ import annotations

import re

from ..calc import partner as calc_partner
from ..input import partner as input_partner
from . import (
    factcheck,
    llm_polish,
    llm_sections,
    masking,
    question_router,
    rules,
    safe_lint,
    style_lint,
    trace,
)
from .sections_schema import _STATIC_OK, SECTION_SPECS, GuardReport, Report23, Section

# LLM 챕터 작성 구간(docs/06, 절대규칙15 개정). 키+use_llm+anthropic 일 때만 compose(사실 슬롯 기반
# 흐르는 산문), 그 외엔 룰 골격. intro·wonguk 등 사실 위주 챕터는 윤문(polish). 어떤 경우든 가드
# 재검증 후 실패 시 룰 폴백. 결정론 룰은 고객마다 동일 패턴 → 사람 목소리는 챕터 작성으로만 확보(docs/13).
_COMPOSE_SECTIONS = {
    "intro",
    "wonguk",
    "nature",
    "frame",
    "love",
    "work",
    "health",
    "flow",
    "ziwei",
    "together",
    "consult",
    "closing",
}


_HR_RX = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,}|={3,})\s*$")  # 마크다운 수평선('---' 누출)
_LIST_MARK_RX = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")  # 줄머리 불릿/번호 마커


def _strip_artifacts(text: str) -> str:
    """LLM 출력의 메타 누출 제거 — 섹션 표시·마크다운(제목/굵게/수평선/리스트/
    인용) 등 AI틱 표식을 걷어낸다. '---' 본문 인쇄 실사고(2026-06-12) 재발 방지."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("[섹션:") or s.startswith("[섹션 "):
            continue
        if s.startswith("#"):  # 마크다운 제목(# 일과 직업…) 누출 제거
            continue
        if _HR_RX.match(ln):  # 수평선 구분선 라인 통째 드롭
            continue
        ln = _LIST_MARK_RX.sub("", ln)  # 줄머리 리스트 마커만 제거(내용 보존)
        ln = ln.replace("**", "").replace("##", "").replace("`", "")  # 굵게/코드 잔재
        if ln.lstrip().startswith("> "):  # 인용 머리
            ln = ln.lstrip()[2:]
        out.append(ln)
    return "\n".join(out).strip()


# CJK 한자(통합·확장A·호환) — 본문은 한글 전용이므로 표시 직전 제거(AI/기술티 제거).
# factcheck(환각 간지 차단)는 이 제거 이전에 이미 수행되므로 그라운딩은 유지된다.
_CJK_RX = re.compile(r"[㐀-䶿一-鿿豈-﫿]+")


_CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def _hanja_clean(text: str) -> str:
    # 한자 제거 + 기호 산문화. '수면·식사'(무간격) 보존, 불릿용 ' · '(양옆 공백)만 환원.
    t = _CJK_RX.sub("", text)
    t = t.replace("[원국]", "").replace("[기운 분포]", "")
    t = t.replace("[자미 구조]", "").replace("[읽는 방향]", "")
    t = re.sub(rf"^\s*[{_CIRCLED}]\s*", "", t, flags=re.M)  # 줄머리 원문자
    t = re.sub(r"^\s*·\s*", "", t, flags=re.M)  # 줄머리 불릿
    # '첫째→먼저' 류 치환은 폐기(2026-06-12 운영자 지적 — '먼저/그리고/끝으로'
    # 나열 잔재 자체가 AI틱). 나열은 룰 골격·프롬프트에서 원천 제거.
    t = re.sub(r"\s*→\s*", ", ", t)  # 화살표 → 쉼표(서사화)
    t = re.sub(r"\s*[—–]\s*", ", ", t)  # em/en dash(AI 시그니처) → 쉼표(이중 방어)
    t = re.sub(r"\s*·\s*", ", ", t)  # 가운뎃점 전부 → 쉼표(기호 난발 금지 2026-06-12)
    t = re.sub(r" · ", ", ", t)  # 불릿 구분(양옆 공백) → 쉼표
    t = re.sub(r"\(\s*\)", "", t)  # 빈 괄호
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" +([,.)])", r"\1", t)  # 구두점 앞 공백 정리
    return t.strip()


# 3단 상품 토글 — 제외할 챕터. integrated=전부, myeongni=명리만, ziwei=자미만.
_PRODUCT_DROP = {
    "integrated": set(),
    "myeongni": {"ziwei", "together"},
    "ziwei": {"wonguk", "nature", "frame", "flow", "together"},
}


def build_report(
    saju,
    *,
    use_llm: bool = False,
    ref_year: int | None = None,
    name: str | None = None,
    unknown_time: bool = False,
    product: str = "integrated",
    concern: str | None = None,
    closing_sign: str | None = None,
) -> Report23:
    # 기준 연도 방어(2026-06-12 버그: ref_year 미전달 시 골격이 seun 첫 해(과거)를
    # '기준 해'로 폴백 → LLM이 "지금은 2025년" 오서술). 우선순위:
    # 인자 > saju.ref_year(horoscope_date 연도) > 오늘.
    if ref_year is None:
        ref_year = getattr(saju, "ref_year", None)
    if ref_year is None:
        import datetime

        ref_year = datetime.date.today().year

    # Phase5 구간1: 고민 분류. use_llm+키면 LLM 분류, 아니면 결정론 룰(무키·재현성).
    backend = llm_sections.get_backend()
    if concern and use_llm:
        category = backend.classify(concern)
    else:
        category = question_router.classify(concern)

    # 상대방·가족 사주(2026-06-12 다인 확장): 고민 원문의 생년월일 전부 감지 →
    # 결정론 calc(음력=KASI 1차 변환, 시각 있으면 4주) → consult 사실 슬롯.
    # 미감지·계산 실패 = 해당 인물 생략(안전 기본값).
    partner_text = ""
    partner_gz: frozenset[str] = frozenset()
    partner_spans: list[tuple[int, int]] = []
    if concern:
        try:
            matches = input_partner.find_partner_births(concern)
            partner_spans = [(pm.start, pm.end) for pm in matches]
            partner_spans += [pm.time_span for pm in matches if pm.time_span]
            blocks: list[str] = []
            gz_all: set[str] = set()
            _m = saju.myeongni
            for pm0 in matches[:4]:  # 가족 케이스 상한 4인
                try:
                    y, mo, d = pm0.year, pm0.month, pm0.day
                    lunar_note = False
                    if pm0.is_lunar:
                        from ..input import normalize as _norm

                        nd = _norm.normalize_date(y, mo, d, is_lunar=True, is_leap=False)
                        y, mo, d = nd.year, nd.month, nd.day
                        lunar_note = True
                    pf = calc_partner.partner_pillars(
                        y,
                        mo,
                        d,
                        pm0.hour,
                        pm0.minute,
                        my_day_gan=_m.day.gan,
                        my_day_zhi=_m.day.zhi,
                        my_elements=_m.elements,
                        my_yongshin=getattr(_m, "yongshin_eokbu", "") or "",
                    )
                    label = " ".join(x for x in (pm0.relation, pm0.name) if x).strip()
                    blocks.append(
                        rules.partner_block(pf, saju, label=label, lunar_input=lunar_note)
                    )
                    gz_all |= {
                        p.ganzhi for p in (pf.year, pf.month, pf.day, pf.hour) if p is not None
                    }
                except Exception as e:
                    import sys

                    print(
                        f"[partner-skip-one] {type(e).__name__}: {str(e)[:120]}",
                        file=sys.stderr,
                        flush=True,
                    )
            partner_text = "\n\n".join(blocks)
            partner_gz = frozenset(gz_all)
        except Exception as e:
            import sys

            print(f"[partner-skip] {type(e).__name__}: {str(e)[:120]}", file=sys.stderr, flush=True)
            partner_text, partner_gz, partner_spans = "", frozenset(), []

    # consult 인용 블록(절대규칙 17 a~b·d): 결정론 마스킹본만 LLM 전달·기록.
    masked_concern = (
        masking.mask_concern(
            concern,
            self_civil=getattr(saju, "input_civil", None),
            partner_spans=partner_spans,
        )
        if concern
        else ""
    )

    skeletons = rules.build_all(
        saju,
        ref_year=ref_year,
        name=name,
        unknown_time=unknown_time,
        concern_category=category.value,
        closing_sign=closing_sign,
    )
    drop = _PRODUCT_DROP.get(product, set())
    sections: list[Section] = []
    safe_total = fact_total = polished_n = fallback_n = 0

    # 목차(toc): 보이는 챕터 제목을 나열(노동착시·호기심격차·책 권위, docs/13). 빌더가 생성.
    visible_titles = [t for s, t, _ in SECTION_SPECS if s not in drop and s not in ("cover", "toc")]
    toc_text = "이 풀이는 다음 순서로 이어집니다.\n" + "\n".join(visible_titles)

    # 챕터별 룰 골격 텍스트 + 룰 가드 결과 선계산
    rule_texts: dict[str, str] = {}
    rule_viol: dict[str, list] = {}
    title_of: dict[str, str] = {}
    for sid, title, src in SECTION_SPECS:
        if sid in drop:
            continue
        rt = (toc_text if sid == "toc" else skeletons[sid]).strip()
        if sid == "consult" and partner_text:
            rt = rt + "\n\n" + partner_text  # 상대방 명식 사실 슬롯(룰 폴백에도 포함)
        rule_texts[sid] = rt
        rule_viol[sid] = safe_lint.lint(rt) + factcheck.check(rt, saju, partner_gz)
        title_of[sid] = title

    # consult(신청 질문)는 카테고리 라우팅 골격만으론 사실이 없어 LLM이 답을 거부한다.
    # 명식 사실(기질·시간 흐름)을 근거로 합쳐 넣어 개인화 답변이 가능하게 한다.
    def _base_for(sid: str) -> str:
        if sid == "consult":
            return "\n\n".join(
                rule_texts[k] for k in ("nature", "flow", "consult") if k in rule_texts
            )
        return rule_texts[sid]

    # LLM 챕터 작성은 챕터당 ~60초라 병렬 실행(독립 호출) — 12챕터 12분 → 1~2분.
    # 무키/룰백엔드면 compose 가 원문 반환하므로 호출 자체를 생략(비용·시간 0).
    cand_map: dict[str, str] = {}
    if use_llm and backend.name == "anthropic":
        targets = [
            sid
            for sid in rule_texts
            if sid in _COMPOSE_SECTIONS and sid not in _STATIC_OK and not rule_viol[sid]
        ]
        if targets:
            import concurrent.futures

            _call = rules.call_name(name)

            def _compose_one(sid: str) -> str:
                return backend.compose(
                    section_id=sid,
                    title=title_of[sid],
                    category=category.value,
                    base_text=_base_for(sid),
                    quoted_concern=(masked_concern if sid == "consult" else None),
                    ref_year=ref_year,
                    call_name=_call,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                futs = {ex.submit(_compose_one, sid): sid for sid in targets}
                for f in concurrent.futures.as_completed(futs):
                    sid = futs[f]
                    try:
                        cand_map[sid] = f.result()
                    except Exception:
                        cand_map[sid] = rule_texts[sid]  # API 실패 시 룰 폴백

    for sid, title, src in SECTION_SPECS:
        if sid in drop:
            continue
        rule_text = rule_texts[sid]
        rule_violations = rule_viol[sid]

        final = rule_text
        polished = False
        applied_violations = list(rule_violations)

        # 정적 챕터(목차·부록·판권)는 LLM 미적용 — 참고/법적 문안 그대로 유지(룰 원문).
        if use_llm and not rule_violations and sid not in _STATIC_OK:
            # 해석 챕터 = 병렬 생성분(compose), 그 외 = 윤문(polish). 무키/룰백엔드면 변화 없음.
            if sid in _COMPOSE_SECTIONS and backend.name == "anthropic":
                cand = cand_map.get(sid, rule_text)
            else:
                cand = llm_polish.polish(rule_text, title)
            llm_changed = bool(cand) and cand != rule_text  # 정규화 '이전'에 판정
            if cand and llm_changed:
                cand = _strip_artifacts(cand)  # 섹션 제목 누출 등 메타 제거
                # 기계적 기호는 가드 전에 결정론 정규화(— · → 쉼표) — 같은 변환을
                # 표시 단계(_hanja_clean)에도 적용하므로 우회가 아니라 선반영.
                # 비유·메타발화·반복 남발은 변환 불가 → style_lint 하드 차단 유지.
                # 룰 패스스루(무키)는 변형하지 않는다(결정론·폴백 판정 보존).
                cand = re.sub(r"\s*[—–]\s*", ", ", cand)
                cand = re.sub(r"\s*·\s*", ", ", cand)
            if cand and llm_changed:
                csv = safe_lint.lint(cand)
                cfv = factcheck.check(cand, saju, partner_gz)
                # 스타일 린트(2026-06-12 신설) — LLM 후보에만: 규칙 누설·시적 비유·
                # em dash·기호·반복 남발 = AI 신호를 검증 가능하게(가드 추가).
                csv = csv + (style_lint.lint(cand) if sid in _COMPOSE_SECTIONS else [])
                # 가드 실패(주로 §12 단정어 1개)면 1회 재작성 — 샘플링 변동으로 통과 가능.
                # 가드는 그대로 전수 적용(우회·완화 아님). compose 챕터·anthropic 일 때만.
                if (csv or cfv) and sid in _COMPOSE_SECTIONS and backend.name == "anthropic":
                    retry = _strip_artifacts(
                        backend.compose(
                            section_id=sid,
                            title=title,
                            category=category.value,
                            base_text=_base_for(sid),
                            quoted_concern=(masked_concern if sid == "consult" else None),
                            ref_year=ref_year,
                            call_name=rules.call_name(name),
                        )
                        or ""
                    )
                    # 가드는 한자 정리 이전에(환각 한자 간지 탐지 유지). 표시정리는 아래 _hanja_clean 에서.
                    if retry and retry != rule_text:
                        rsv = safe_lint.lint(retry) + style_lint.lint(retry)
                        rfv = factcheck.check(retry, saju, partner_gz)
                        if not rsv and not rfv:
                            cand, csv, cfv = retry, rsv, rfv
                if not csv and not cfv:
                    final, polished = cand, True
                    polished_n += 1
                else:
                    fallback_n += 1  # 재작성도 실패 → 룰 원문 유지
                    import sys

                    _bad = [v.get("match") or v.get("token") for v in (csv + cfv)][:5]
                    print(
                        f"[compose-fallback] {sid}: guard-fail safe={len(csv)} fact={len(cfv)} {_bad}",
                        file=sys.stderr,
                        flush=True,
                    )

        # 표시 직전 한자 제거(정적 챕터 제외 — 부록 용어집의 한자 병기는 교육용으로 유지).
        if sid not in _STATIC_OK:
            final = _hanja_clean(final)

        safe_total += len(safe_lint.lint(final))
        fact_total += len(factcheck.check(final, saju, partner_gz))
        sections.append(
            Section(
                id=sid,
                title=title,
                source_keys=src,
                rule_text=rule_text,
                final_text=final,
                polished=polished,
                guard_violations=applied_violations if not polished else [],
            )
        )

    grounding_ok, _bad = trace.check(sections)
    clean = safe_total == 0 and fact_total == 0 and grounding_ok
    # 허용 토큰 영속(검수 UI 수정 재검증용) — 계산 시점 집합 그대로, set→list 직렬화
    allow_ser = {k: sorted(v) for k, v in factcheck.allowed_tokens(saju, partner_gz).items()}
    return Report23(
        sections=sections,
        concern_category=category.value,
        allow_tokens=allow_ser,
        guard=GuardReport(
            safe_lint_total=safe_total,
            factcheck_total=fact_total,
            grounding_ok=grounding_ok,
            polished_sections=polished_n,
            fallback_sections=fallback_n,
            clean=clean,
        ),
    )
