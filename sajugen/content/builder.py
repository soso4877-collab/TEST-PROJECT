# -*- coding: utf-8 -*-
"""콘텐츠 빌더 — SajuResult → 23섹션 룰 골격 → (옵션)LLM 윤문 → 가드 → Report23.

가드: §12 안전 린트 + 사실일치 린트 + 그라운딩. 윤문이 가드 실패 시 룰 원문 폴백.
"""

from __future__ import annotations

import re

from ..calc import myeongni as mod_my
from ..calc import partner as calc_partner
from ..input import partner as input_partner
from . import (
    client_tone_lint,
    consistency,
    factcheck,
    llm_polish,
    llm_sections,
    masking,
    postprocess,
    quality_lint,
    question_router,
    repetition,
    rules,
    safe_lint,
    style_lint,
    temporal_lint,
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


# 런타임 단일 소스: 마크다운/메타 제거·한자 정제는 content.postprocess 공통 함수로
# (개인 경로·궁합 경로 동일 동작 보장 — 경로별 드리프트 방지). 위 _legacy_* 는 미사용.
_strip_artifacts = postprocess.strip_artifacts
_hanja_clean = postprocess.hanja_clean


def personal_identity_spec(saju, name: str | None) -> tuple:
    """개인 일간 role 가드/게이트용 (expected_gans, expected_terms, subject_specs). H1.5.3.

    expected = 결정론 일간(saju.myeongni.day_master) 하나뿐. 본문이 다른 천간을 '일간/중심 글자/
    자기 자신'으로 서술하면 위반(예 '일간 계수' — 실제 임수).
    """
    gan = rules._GAN_KO.get(saju.myeongni.day_master, "")
    term = client_tone_lint.gan_to_term(gan)
    aliases = [
        a
        for a in (
            name,
            client_tone_lint.given_name(name) if name else "",
            rules.call_name(name) if name else "",
            client_tone_lint.honor(name) if name else "",
        )
        if a
    ]
    aliases += ["자기 자신", "나 자신", "본인", "자신"]
    return {gan}, {term}, [(aliases, term)]


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
        concern_text=concern,
        closing_sign=closing_sign,
    )
    drop = _PRODUCT_DROP.get(product, set())
    sections: list[Section] = []
    safe_total = fact_total = polished_n = fallback_n = 0
    _id_spec = personal_identity_spec(saju, name)  # 일간 role 가드(H1.5.3)

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
                cand = postprocess.strip_document_self_reference(cand)
                cand = postprocess.strip_formulaic_conclusion(cand)
                cand = postprocess.replace_generic_address(cand, rules.call_name(name))
                # 기계적 기호는 가드 전에 결정론 정규화(— · → 쉼표) — 같은 변환을
                # 표시 단계(_hanja_clean)에도 적용하므로 우회가 아니라 선반영.
                # 비유·메타발화·반복 남발은 변환 불가 → style_lint 하드 차단 유지.
                # 룰 패스스루(무키)는 변형하지 않는다(결정론·폴백 판정 보존).
                cand = re.sub(r"\s*[—–]\s*", ", ", cand)
                cand = re.sub(r"\s*·\s*", ", ", cand)
                # 외래어 1차 자동 순화(H1.5.1): 폴백 전 기본 대체어로 치환해 LLM 산문 보존률↑.
                # 순화 후에도 남은 외래어는 아래 loanword_lint 가 잡아 폴백(hard-ban 유지).
                if sid in _COMPOSE_SECTIONS:
                    cand = client_tone_lint.normalize_loanwords(cand)
            if cand and llm_changed:
                csv = safe_lint.lint(cand)
                cfv = factcheck.check(cand, saju, partner_gz)
                # 스타일 린트(2026-06-12 신설) — LLM 후보에만: 규칙 누설·시적 비유·
                # em dash·기호·반복 남발 = AI 신호를 검증 가능하게(가드 추가).
                if sid in _COMPOSE_SECTIONS:
                    csv = (
                        csv
                        + style_lint.lint(cand)
                        + quality_lint.lint(cand, names=[name] if name else None)
                        + temporal_lint.lint(cand, ref_year)
                        + client_tone_lint.loanword_lint(cand)  # 외래어 hard-ban
                        + client_tone_lint.raw_calc_lint(cand)  # 날것 계산표현
                        + client_tone_lint.identity_role_lint(  # 일간 role 오서술(H1.5.3)
                            cand, _id_spec[0], _id_spec[1], _id_spec[2]
                        )
                    )
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
                    retry = postprocess.strip_document_self_reference(retry)
                    retry = postprocess.strip_formulaic_conclusion(retry)
                    retry = postprocess.replace_generic_address(retry, rules.call_name(name))
                    retry = client_tone_lint.normalize_loanwords(retry)  # 재작성도 1차 순화
                    # 가드는 한자 정리 이전에(환각 한자 간지 탐지 유지). 표시정리는 아래 _hanja_clean 에서.
                    if retry and retry != rule_text:
                        rsv = (
                            safe_lint.lint(retry)
                            + style_lint.lint(retry)
                            + quality_lint.lint(retry, names=[name] if name else None)
                            + temporal_lint.lint(retry, ref_year)
                            + client_tone_lint.loanword_lint(retry)
                            + client_tone_lint.raw_calc_lint(retry)
                            + client_tone_lint.identity_role_lint(
                                retry, _id_spec[0], _id_spec[1], _id_spec[2]
                            )
                        )
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

    # 크로스챕터 반복 억제(결정론 백스톱): 일주 자기소개는 원국(wonguk) 장에만 — 병렬 compose가
    # 프롬프트·골격 수정에도 잔존시키는 중복 도입 줄을 다른 장에서 제거(2026-06-14 베타 지적).
    if use_llm and backend.name == "anthropic":
        repetition.dedup_ilju_intro(sections, owner_id="wonguk")

    # 교차챕터 대운 일관성(실사고 2026-06-14): '현재 대운'은 단일 사실이어야 한다.
    # 다른 대운(미래/과거)을 '지금·현재·초입'으로 서술한 챕터는 결정론 골격으로 되돌린다
    # (우회 아님 — 골격은 현재 대운을 정확히 명시. rules 가 주입). 폴백 후 재검사로 보고.
    daewoon_consistent = True
    cur_dw = mod_my.current_daewoon(saju.myeongni, ref_year)
    if cur_dw is not None:
        expected_ko = factcheck._gz_ko(cur_dw.ganzhi)
        bad_ids = consistency.offending_ids(sections, expected_ko)
        if bad_ids:
            for sec in sections:
                if sec.id in bad_ids:
                    txt = rule_texts.get(sec.id, sec.rule_text)
                    sec.final_text = txt if sec.id in _STATIC_OK else _hanja_clean(txt)
                    sec.polished = False
                    fallback_n += 1
                    import sys

                    print(
                        f"[daewoon-consistency-fallback] {sec.id}: 현재 대운≠{expected_ko} → 골격 폴백",
                        file=sys.stderr,
                        flush=True,
                    )
        daewoon_consistent, _dbad = consistency.check(sections, expected_ko)

    grounding_ok, _bad = trace.check(sections)
    clean = safe_total == 0 and fact_total == 0 and grounding_ok and daewoon_consistent
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
            daewoon_consistent=daewoon_consistent,
            clean=clean,
        ),
    )
