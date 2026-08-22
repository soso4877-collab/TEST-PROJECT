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
    customer_meta_lint,
    delivery_quality,
    factcheck,
    llm_polish,
    llm_sections,
    llm_usage,
    masking,
    postprocess,
    quality_lint,
    question_router,
    report_context,
    repetition,
    rules,
    safe_lint,
    style_lint,
    temporal_lint,
    trace,
    unknown_time_policy,
    western_astrology_lint,
)
from .sections_schema import _STATIC_OK, SECTION_SPECS, GuardReport, Report23, Section

# LLM 챕터 작성 구간(docs/06, 절대규칙15 개정). 키+use_llm+anthropic 일 때 12개 해석
# 챕터를 사실 슬롯 기반으로 compose하고, 그 외엔 룰 골격을 쓴다. 현재 자동 polish 전용 챕터는
# 없으며 검수자 재윤문 인터페이스만 하위호환한다. 어떤 경우든 가드 실패 시 룰 폴백이다.
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


def _customer_policy_lints(
    text: str,
    *,
    birth_time_mode: str = "known",
    provenance: object | None = None,
    source: str = "content",
) -> list[dict]:
    """생성·재작성·룰 폴백이 공유하는 고객 문체/외부 조언 하드 벨트.

    register warning은 운영자 관측용이므로 후보를 버리지 않는다. 외부 조언 finding은
    승인된 정적 rule/term만 담아 재작성 피드백에도 고객 원문이 섞이지 않는다.
    """

    register_hard = [
        hit for hit in client_tone_lint.register_lint(text) if hit.get("severity") == "hard"
    ]
    return (
        register_hard
        + delivery_quality.external_domain_advice_lint(text)
        + western_astrology_lint.lint(text)
        + unknown_time_policy.unknown_time_provenance_lint(
            text,
            birth_time_mode=birth_time_mode,
            provenance=provenance,
            source=source,
        )
    )


def _normalize_llm_candidate(text: str, *, name: str | None, compose: bool) -> str:
    """최초 후보와 재작성 후보가 공유하는 결정론 전처리.

    두 경로가 다른 전처리를 쓰면 깨끗한 재작성도 기호 lint에 걸려 골격으로 되돌아간다.
    고객 정책을 완화하지 않고, 표시 전에 이미 허용된 기계적 순화만 같은 순서로 적용한다.
    """

    normalized = _strip_artifacts(text)
    normalized = postprocess.strip_document_self_reference(normalized)
    normalized = postprocess.strip_formulaic_conclusion(normalized)
    normalized = postprocess.replace_generic_address(normalized, rules.call_name(name))
    normalized = re.sub(r"\s*[—–]\s*", ", ", normalized)
    normalized = re.sub(r"\s*·\s*", ", ", normalized)
    normalized = postprocess.style_safe_text(normalized)
    if compose:
        normalized = client_tone_lint.normalize_loanwords(normalized)
    return normalized


# 런타임 단일 소스: 마크다운/메타 제거·한자 정제는 content.postprocess 공통 함수로
# (개인 경로·궁합 경로 동일 동작 보장 — 경로별 드리프트 방지). 위 _legacy_* 는 미사용.
_strip_artifacts = postprocess.strip_artifacts
_hanja_clean = postprocess.hanja_clean


def personal_identity_spec(saju, name: str | None, *, birth_time_mode) -> tuple:
    """개인 일간 role 가드/게이트용 (expected_gans, expected_terms, subject_specs). H1.5.3.

    expected = 결정론 일간(saju.myeongni.day_master) 하나뿐. 본문이 다른 천간을 '일간/중심 글자/
    자기 자신'으로 서술하면 위반(예 '일간 계수' — 실제 임수).
    """
    mode = unknown_time_policy.normalize_mode(birth_time_mode)
    m = saju.three_pillar if unknown_time_policy.is_three_pillar_mode(mode) else saju.myeongni
    gan = rules._GAN_KO.get(m.day_master, "")
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

def _retry_feedback_labels(
    style_violations: list[dict],
    fact_violations: list[dict],
    *,
    three_pillar: bool,
) -> tuple[set[str], set[str]]:
    """재작성 프롬프트의 회피 사유와 형식 교정 사유를 분리해 반환한다.

    known-time의 temporal 위반은 금칙 토큰이 아니라 표기 형식 오류이므로 가드가 제공한
    ``why``를 교정 사유로 전달한다. 그 밖의 위반은 기존처럼 구체 표현을 회피한다.
    삼주는 근거 밖 간지·금칙 토큰을 되먹이면 다음 호출의 새 사실 슬롯이 되므로, 원문
    토큰과 ``why``를 복제하지 않고 고정된 사유 ID만 회피 버킷에 전달한다.
    """

    if not three_pillar:
        avoid: set[str] = set()
        fix: set[str] = set()
        format_types = {"month_notation", "temporal", "relative_month_boundary"}
        for violation in (*style_violations, *fact_violations):
            why = str(violation.get("why") or "").strip()
            if violation.get("type") in format_types and why:
                fix.add(why)
                continue
            label = str(
                violation.get("match")
                or violation.get("token")
                or violation.get("rule")
                or ""
            ).strip()
            if label:
                avoid.add(label)
        return avoid, fix

    labels: set[str] = set()
    if fact_violations:
        labels.add("현재 장 근거에 없는 사실")
    for violation in style_violations:
        if violation.get("type") == "consult_direct":
            labels.add("질문 축 직접 답 누락")
        else:
            labels.add("작성 규칙 위반")
    return labels, set()


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
    is_leap: bool = False,
    ref_date: str | None = None,
    work_modules: tuple[str, ...] | list[str] | None = None,
    include_section_ids: set[str] | frozenset[str] | None = None,
    selected_modules: tuple[str, ...] | list[str] | None = None,
    birth_time_mode: str | None = None,
) -> Report23:
    birth_time_mode = unknown_time_policy.normalize_mode(
        birth_time_mode or saju.birth_time_mode,
        unknown_time=unknown_time,
    )
    unknown_time = birth_time_mode == unknown_time_policy.THREE_PILLAR_MODE
    three_pillar_provenance = (
        unknown_time_policy.provenance_from_result(saju) if unknown_time else None
    )
    provenance_hits = unknown_time_policy.provenance_contract_lint(
        three_pillar_provenance,
        birth_time_mode=birth_time_mode,
        source="builder",
    )
    if provenance_hits:
        rules_hit = ",".join(sorted({str(hit["rule"]) for hit in provenance_hits}))
        raise ValueError(f"invalid three-pillar provenance: {rules_hit}")
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
    if concern and not unknown_time:
        try:
            # 본인 생일 제외 가드 배선(2026-07-04 QI 팬텀 파트너 — 가드는 partner.py 에
            # 있었으나 인자 미전달로 사장돼, 원문 속 본인 생일이 상대방으로 둔갑했다).
            _self_solar = None
            _civ = getattr(saju, "input_civil", None)
            if _civ:
                try:
                    from datetime import date as _date

                    _self_solar = _date.fromisoformat(str(_civ)[:10])
                except ValueError:
                    _self_solar = None
            matches = input_partner.find_partner_births(
                concern, self_solar=_self_solar, ref_year=ref_year
            )
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
                    # 절대규칙 8-1: 연·월주가 비단정이면 허용 토큰에서도 뺀다. 문안에서만
                    # 빼고 allow-set 에 남기면 LLM 이 되살려도 factcheck 가 통과시킨다.
                    _allow_pillars = (
                        (pf.day, pf.hour)
                        if pf.ym_time_dependent
                        else (pf.year, pf.month, pf.day, pf.hour)
                    )
                    gz_all |= {p.ganzhi for p in _allow_pillars if p is not None}
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
            self_civil=(
                getattr(saju, "input_civil_date", None)
                if unknown_time
                else getattr(saju, "input_civil", None)
            ),
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
        is_leap=is_leap,
        # Q7: job/wealth 부분 조립도 기존 work 챕터의 동일한 LLM·3단 가드 경로를 탄다.
        # None은 기존 개인 상품의 job+wealth 결합값이라 모든 옛 호출이 그대로 유지된다.
        work_modules=work_modules,
        birth_time_mode=birth_time_mode,
    )
    drop = set(_PRODUCT_DROP.get(product, set()))
    if include_section_ids is not None:
        # Q7 부분 모듈은 최종 조립에서만 버리는 데 그치지 않고, 선택 밖 챕터를 LLM 작성
        # 대상으로도 만들지 않는다. cover/toc는 기존 빌더 구조를 유지하고 조립기가 제외한다.
        known_ids = {section_id for section_id, _title, _source in SECTION_SPECS}
        unknown_includes = set(include_section_ids) - known_ids
        if unknown_includes:
            raise ValueError(f"unknown personal section includes: {sorted(unknown_includes)}")
        drop |= known_ids - set(include_section_ids) - {"cover", "toc"}
    if unknown_time:
        # 삼주는 자미 계산 결과 자체가 없으며, 두 섹션을 생성·LLM 호출 대상으로도 만들지 않는다.
        drop |= {"ziwei", "together"}
    sections: list[Section] = []
    safe_total = fact_total = polished_n = fallback_n = 0
    # P0(2026-07-05): 어느 챕터가 윤문/폴백됐는지 id 추적 — v7 consult 골격 폴백이
    # 카운트만으로는 발송 리포트에서 안 보였던 관측 갭(QI-2026-07-05-03).
    polished_ids: list[str] = []
    fallback_ids: list[str] = []
    _id_spec = personal_identity_spec(
        saju,
        name,
        birth_time_mode=birth_time_mode,
    )  # 일간 role 가드(H1.5.3)

    # 목차(toc): 보이는 챕터 제목을 나열(노동착시·호기심격차·책 권위, docs/13). 빌더가 생성.
    # 리드는 문서 진행/섹션 예고 메타("…다음 순서로 이어집니다")가 아니라 중립 헤딩만 둔다
    # (P4, 2026-07-01 — transition_section_preview 게이트에 걸리는 작성자 진행 안내 제거).
    visible_titles = [t for s, t, _ in SECTION_SPECS if s not in drop and s not in ("cover", "toc")]
    toc_text = "차례\n" + "\n".join(visible_titles)

    # 챕터별 룰 골격 텍스트 + 룰 가드 결과 선계산
    rule_texts: dict[str, str] = {}
    rule_viol: dict[str, list] = {}
    title_of: dict[str, str] = {}
    source_of: dict[str, list[str]] = {}
    for sid, title, src in SECTION_SPECS:
        if sid in drop:
            continue
        rt = (toc_text if sid == "toc" else skeletons[sid]).strip()
        if sid == "consult" and partner_text:
            rt = rt + "\n\n" + partner_text  # 상대방 명식 사실 슬롯(룰 폴백에도 포함)
        rule_texts[sid] = rt
        section_source = (
            report_context.three_pillar_section_fact_source_ids(sid)
            if unknown_time
            else src
        )
        source_of[sid] = list(section_source)
        rule_viol[sid] = (
            safe_lint.lint(rt)
            + factcheck.check(rt, saju, partner_gz)
            + _customer_policy_lints(
                rt,
                birth_time_mode=birth_time_mode,
                provenance=three_pillar_provenance,
                source=f"rule:{sid}",
            )
        )
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
    shared_report_context: report_context.ReportContext | None = None
    if use_llm and backend.name == "anthropic":
        targets = [
            sid
            for sid in rule_texts
            if sid in _COMPOSE_SECTIONS and sid not in _STATIC_OK and not rule_viol[sid]
        ]
        if targets:
            import concurrent.futures
            import inspect

            _call = rules.call_name(name)

            # 고객 원문·이름·생년월일·이전 LLM 산문 없이, 허용된 ID만으로 PDF당 한 번
            # 만든다. 같은 객체/같은 직렬화 prefix를 모든 챕터와 재작성 호출이 공유한다.
            shared_report_context = report_context.build_report_context(
                selected_modules=selected_modules,
                question_category=category.value,
                active_section_ids=targets,
                birth_time_mode=birth_time_mode,
            )

            # LLMBackend 프로토콜은 새 인자를 지원하지만, 외부 테스트 더블/구 확장 백엔드는
            # 예전 compose 시그니처일 수 있다. 실제 AnthropicBackend에는 항상 전달하고,
            # 명시적 구 시그니처에는 지원하는 키만 보내 하위호환을 보존한다.
            compose_params = inspect.signature(backend.compose).parameters
            accepts_kwargs = any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in compose_params.values()
            )

            def _compose_one(
                sid: str,
                attempt: int = 1,
                feedback: str | None = None,
                feedback_fix: str | None = None,
            ) -> str:
                compose_kwargs = {
                    "section_id": sid,
                    "title": title_of[sid],
                    "category": category.value,
                    "base_text": _base_for(sid),
                    "quoted_concern": masked_concern if sid == "consult" else None,
                    "ref_year": ref_year,
                    "call_name": _call,
                    "ref_date": ref_date,
                    "feedback": feedback,
                }
                if accepts_kwargs or "feedback_fix" in compose_params:
                    compose_kwargs["feedback_fix"] = feedback_fix
                if accepts_kwargs or "report_context" in compose_params:
                    compose_kwargs["report_context"] = shared_report_context
                if unknown_time and (
                    accepts_kwargs or "fact_source_ids" in compose_params
                ):
                    # 현재 장의 base_text를 실제로 만든 출처만 전달한다. 공통 문맥의 전체
                    # 출처 목록을 생성 권한처럼 해석하지 못하도록 장별 슬롯을 좁힌다.
                    compose_kwargs["fact_source_ids"] = tuple(source_of[sid])
                if accepts_kwargs or "attempt" in compose_params:
                    compose_kwargs["attempt"] = attempt
                return backend.compose(**compose_kwargs)

            # Anthropic 공식 문서상 동시 요청은 첫 응답이 시작되기 전 캐시를 읽을 수 없다.
            # 첫 챕터 한 건의 usage에서 cache 생성/읽기를 실제 확인한 뒤에만 나머지를 3병렬로
            # 보낸다. 미관측·API 오류면 추가 uncached 호출 없이 이번 PDF의 나머지는 룰 골격으로
            # 닫는다. 캐시는 비용 최적화이므로 실패가 납품 안전성이나 추가 비용으로 번지면 안 된다.
            warm_sid, *parallel_targets = targets
            try:
                warm_result = _compose_one(warm_sid)
                cand_map[warm_sid] = str(warm_result)
            except Exception:
                warm_result = None
                cand_map[warm_sid] = rule_texts[warm_sid]
            cache_observed = getattr(warm_result, "cache_observed", None)
            # name=anthropic인 모든 backend는 ComposeResult로 실제 캐시 생성/읽기를 명시해야
            # 한다. marker 없는 구형·프록시 backend를 성공으로 추정하면 비용 상한이 fail-open 된다.
            cache_ready = cache_observed is True
            if parallel_targets and cache_ready:
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                    # ContextVar 기반 사용량 run을 worker에 명시 복사한다. 각 작업은 별도 Context
                    # 사본을 받아 같은 run collector를 공유하되 Context 자체를 동시 진입하지 않는다.
                    futs = {
                        ex.submit(llm_usage.bind_current(_compose_one, sid)): sid
                        for sid in parallel_targets
                    }
                    for future in concurrent.futures.as_completed(futs):
                        sid = futs[future]
                        try:
                            cand_map[sid] = future.result()
                        except Exception:
                            cand_map[sid] = rule_texts[sid]  # API 실패 시 룰 폴백
            elif parallel_targets:
                cand_map.update({sid: rule_texts[sid] for sid in parallel_targets})

    for sid, title, src in SECTION_SPECS:
        if sid in drop:
            continue
        rule_text = rule_texts[sid]
        rule_violations = rule_viol[sid]

        final = rule_text
        polished = False
        applied_violations = list(rule_violations)

        # 정적 챕터(목차·부록·판권)는 LLM 미적용 — 승인된 룰 원문을 그대로 유지한다.
        # cover 제외(P0-2/T1.2): 표지 룰 텍스트에 생년월일시(입력) 원문이 들어 있어 polish
        # 로 넘기면 API 전송된다(절대규칙 17 위반). 표지는 정형 메타라 윤문 이득도 0 → 룰 원문 사용.
        if use_llm and not rule_violations and sid not in _STATIC_OK and sid != "cover":
            # 해석 챕터 = 병렬 생성분(compose), 그 외 = 윤문(polish). 무키/룰백엔드면 변화 없음.
            if sid in _COMPOSE_SECTIONS and backend.name == "anthropic":
                cand = cand_map.get(sid, rule_text)
            else:
                # mask_civil: 만약 다른 섹션에 생년월일이 섞여도 전송 전 마스킹(방어겹).
                cand = llm_polish.polish(
                    rule_text, title, mask_civil=getattr(saju, "input_civil", None)
                )
            llm_changed = bool(cand) and cand != rule_text  # 정규화 '이전'에 판정
            if cand and llm_changed:
                cand = _normalize_llm_candidate(
                    cand,
                    name=name,
                    compose=sid in _COMPOSE_SECTIONS,
                )
                # 기계적 기호는 가드 전에 결정론 정규화(— · → 쉼표) — 같은 변환을
                # 표시 단계(_hanja_clean)에도 적용하므로 우회가 아니라 선반영.
                # 비유·메타발화·반복 남발은 변환 불가 → style_lint 하드 차단 유지.
                # 룰 패스스루(무키)는 변형하지 않는다(결정론·폴백 판정 보존).
                # 반복어 결정론 선치환(2026-07-04 — integrated 승인 설계의 개인 경로 이식).
                # '또렷하게' 계열이 style_lint 폴백을 유발해 윤문이 유실되던 것(실측 frame
                # 폴백)을 가드 전 선반영으로 흡수. 반복 상한 등 lint 자체는 불변(완화 0).
                # 외래어 1차 자동 순화(H1.5.1): 폴백 전 기본 대체어로 치환해 LLM 산문 보존률↑.
                # 순화 후에도 남은 외래어는 아래 loanword_lint 가 잡아 폴백(hard-ban 유지).
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
                        + temporal_lint.lint(cand, ref_year, ref_date=ref_date)
                        + client_tone_lint.loanword_lint(cand)  # 외래어 hard-ban
                        + client_tone_lint.raw_calc_lint(cand)  # 날것 계산표현
                        + _customer_policy_lints(
                            cand,
                            birth_time_mode=birth_time_mode,
                            provenance=three_pillar_provenance,
                            source=f"candidate:{sid}",
                        )  # register hard + 외부 사실/절차 조언 + 삼주 출처
                        + client_tone_lint.identity_role_lint(  # 일간 role 오서술(H1.5.3)
                            cand, _id_spec[0], _id_spec[1], _id_spec[2]
                        )
                        + delivery_quality.guarantee_lint(cand)  # 보장형(최종 게이트 갭 차단)
                        + customer_meta_lint.lint(cand)  # 문서 진행/섹션 예고 메타 발화(P3)
                        # QI-2026-07-04(F4): placeholder/커플 지칭 — 1인 문서(파트너 부재)면
                        # 커플 지칭 candidate 도 위반(팬텀 파트너 문안이 compose 를 못 통과).
                        + client_tone_lint.placeholder_residue_strict_violations(
                            cand, strict_pair=not partner_text
                        )
                    )
                    # P2(QI-2026-07-05-03): consult 직답성 선검사 — v7 실사고(388자 유보
                    # 골격 폴백)를 compose 단계에서 감지. concern 없으면 skipped(no-op 명시).
                    if sid == "consult":
                        _cd = delivery_quality.consult_direct_result(cand, concern)
                        if not _cd.get("ok", True):
                            csv = csv + [
                                {
                                    "type": "consult_direct",
                                    "match": "질문 직답 미달("
                                    + ",".join(_cd.get("missing", []))
                                    + ")",
                                }
                            ]
                # 가드 실패(주로 §12 단정어 1개)면 재작성 — 샘플링 변동으로 통과 가능.
                # 가드는 그대로 전수 적용(우회·완화 아님). compose 챕터·anthropic 일 때만.
                # P2(2026-07-05): consult 는 질문에 답하는 유일한 챕터라 폴백(골격) 전에
                # 한 번 더 재시도(총 2회, 운영자 승인 +1콜). 그 외 챕터는 기존 1회 유지.
                _max_retry = 2 if sid == "consult" else 1
                _round = 0
                _fb_avoid_pool: set[str] = set()
                _fb_fix_pool: set[str] = set()
                while (
                    (csv or cfv)
                    and _round < _max_retry
                    and sid in _COMPOSE_SECTIONS
                    and backend.name == "anthropic"
                ):
                    _round += 1
                    # 재작성 피드백(2026-07-04): 직전 초안의 위반 표현을 프롬프트로 전달 —
                    # 사유 없이 재시도하면 같은 단어가 재발해 폴백률이 높았다(실측: '쯤' 2회 연속).
                    # 2차 재시도는 라운드별 위반을 누적 전달(같은 실패 반복 방지).
                    _fb_avoid, _fb_fix = _retry_feedback_labels(
                        csv,
                        cfv,
                        three_pillar=unknown_time,
                    )
                    _fb_avoid_pool |= _fb_avoid
                    _fb_fix_pool |= _fb_fix
                    _fb = ", ".join(sorted(_fb_avoid_pool)[:8])
                    _fb_fix_text = ", ".join(sorted(_fb_fix_pool)[:6])
                    retry = _normalize_llm_candidate(
                        _compose_one(
                            sid,
                            attempt=_round + 1,
                            feedback=_fb or None,
                            feedback_fix=_fb_fix_text or None,
                        )
                        or "",
                        name=name,
                        compose=True,
                    )
                    # 가드는 한자 정리 이전에(환각 한자 간지 탐지 유지). 표시정리는 아래 _hanja_clean 에서.
                    if not retry or retry == rule_text:
                        continue
                    rsv = (
                        safe_lint.lint(retry)
                        + style_lint.lint(retry)
                        + quality_lint.lint(retry, names=[name] if name else None)
                        + temporal_lint.lint(retry, ref_year, ref_date=ref_date)
                        + client_tone_lint.loanword_lint(retry)
                        + client_tone_lint.raw_calc_lint(retry)
                        + _customer_policy_lints(
                            retry,
                            birth_time_mode=birth_time_mode,
                            provenance=three_pillar_provenance,
                            source=f"retry:{sid}",
                        )
                        + client_tone_lint.identity_role_lint(
                            retry, _id_spec[0], _id_spec[1], _id_spec[2]
                        )
                        + delivery_quality.guarantee_lint(retry)  # 보장형(재작성도 검사)
                        + customer_meta_lint.lint(retry)  # 문서 진행/섹션 예고 메타(재작성도)
                        + client_tone_lint.placeholder_residue_strict_violations(
                            retry,
                            strict_pair=not partner_text,  # 커플 지칭(재작성도, F4)
                        )
                    )
                    if sid == "consult":  # 직답성(재작성도, P2)
                        _cd_r = delivery_quality.consult_direct_result(retry, concern)
                        if not _cd_r.get("ok", True):
                            rsv = rsv + [
                                {
                                    "type": "consult_direct",
                                    "match": "질문 직답 미달("
                                    + ",".join(_cd_r.get("missing", []))
                                    + ")",
                                }
                            ]
                    rfv = factcheck.check(retry, saju, partner_gz)
                    if not rsv and not rfv:
                        cand, csv, cfv = retry, rsv, rfv
                    else:
                        # 실패 라운드의 위반도 다음 라운드 피드백에 누적(원 csv/cfv 는 유지 —
                        # 최종 폴백 판단·섹션 위반 기록의 기준은 본경로 초안).
                        _fb_avoid, _fb_fix = _retry_feedback_labels(
                            rsv,
                            rfv,
                            three_pillar=unknown_time,
                        )
                        _fb_avoid_pool |= _fb_avoid
                        _fb_fix_pool |= _fb_fix
                if not csv and not cfv:
                    final, polished = cand, True
                    polished_n += 1
                    polished_ids.append(sid)
                else:
                    fallback_n += 1  # 재작성도 실패 → 룰 원문 유지
                    fallback_ids.append(sid)
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
                source_keys=source_of[sid],
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
    cur_dw = None if unknown_time else mod_my.current_daewoon(saju.myeongni, ref_year)
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
                    if sec.id in polished_ids:
                        polished_ids.remove(sec.id)  # 윤문됐다가 대운 일관성 폴백된 챕터
                    if sec.id not in fallback_ids:
                        fallback_ids.append(sec.id)
                    import sys

                    print(
                        f"[daewoon-consistency-fallback] {sec.id}: 현재 대운≠{expected_ko} → 골격 폴백",
                        file=sys.stderr,
                        flush=True,
                    )
        daewoon_consistent, _dbad = consistency.check(sections, expected_ko)

    grounding_ok, _bad = trace.check(sections)
    # 후보·재작성 단계뿐 아니라 실제 반환할 최종 섹션을 다시 전수한다. 룰 골격 자체에
    # register/external-advice 위반이 생긴 경우 LLM을 건너뛰더라도 aggregate guard가
    # GREEN으로 보이는 false-PASS를 막는다. 최종 PDF verify와 독립된 pre-render 차단층이다.
    customer_policy_total = sum(
        len(
            _customer_policy_lints(
                section.final_text,
                birth_time_mode=birth_time_mode,
                provenance=three_pillar_provenance,
                source=f"final:{section.id}",
            )
        )
        for section in sections
    )
    clean = (
        safe_total == 0
        and fact_total == 0
        and customer_policy_total == 0
        and grounding_ok
        and daewoon_consistent
    )
    # 허용 토큰 영속(검수 UI 수정 재검증용) — 계산 시점 집합 그대로, set→list 직렬화
    allow_ser = {k: sorted(v) for k, v in factcheck.allowed_tokens(saju, partner_gz).items()}
    return Report23(
        sections=sections,
        concern_category=category.value,
        allow_tokens=allow_ser,
        partner_present=bool(partner_text),  # QI-2026-07-04: verify 커플 지칭 승격 판정용
        birth_time_mode=birth_time_mode,
        three_pillar_provenance=(
            unknown_time_policy.serialize_provenance(three_pillar_provenance)
            if unknown_time
            else {}
        ),
        fact_source_ids=(
            list(unknown_time_policy.ALLOWED_FACT_SOURCES) if unknown_time else []
        ),
        guard=GuardReport(
            safe_lint_total=safe_total,
            factcheck_total=fact_total,
            grounding_ok=grounding_ok,
            polished_sections=polished_n,
            fallback_sections=fallback_n,
            polished_section_ids=polished_ids,
            fallback_section_ids=fallback_ids,
            daewoon_consistent=daewoon_consistent,
            customer_policy_lint_total=customer_policy_total,
            clean=clean,
        ),
    )
