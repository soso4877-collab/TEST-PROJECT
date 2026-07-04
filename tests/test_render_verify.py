# -*- coding: utf-8 -*-
"""렌더 검증 — orphan(widow) 페이지 검출 + 짧은 마지막 단락 병합(이슈1, H1-mini)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sajugen.render import pdf as render_pdf  # noqa: E402
from sajugen.render import verify as v  # noqa: E402
from playwright_guard import require_playwright_subprocess  # noqa: E402


def test_orphan_detector_flags_short_standalone_page():
    pages = [
        "표지",  # p1 표지(제외)
        "제 1 장 본문 " + "가" * 200,  # 정상 장
        "있습니다.",  # p3 orphan(짧은 단독 본문)
        "본문이 충분히 긴 페이지입니다. " * 20,  # 정상
        "글을 맺으며 감사합니다.",  # 마지막(제외)
    ]
    orphans = v._orphan_pages(pages)
    assert [o["page"] for o in orphans] == [3], orphans


def test_orphan_detector_excludes_chapter_and_appendix():
    pages = [
        "표지",
        "제 3 장",  # 장 구분(짧아도 제외)
        "용어 풀이",  # 부록(제외)
        "마지막",
    ]
    assert v._orphan_pages(pages) == []


def test_low_density_excludes_chapter_tail():
    # 장마다 새 페이지(chapter_breaks=True)에서 긴 장의 정상 조판 꼬리(다음 페이지가 새 장 +
    # 하한 이상 분량)는 콘텐츠 부족이 아니라 정상 조판 → 저밀도에서 제외.
    pages = [
        "표지",
        "제 1 장 본문 " + "가" * 200,  # 긴 장 본문(정상)
        "가" * 95,  # <120 이나 하한(90) 이상 정상 조판 꼬리, 다음이 새 장 → 면제
        "제 2 장 " + "나" * 200,  # 새 장 시작
        "글을 맺으며",  # 마지막(제외)
    ]
    assert v._low_density_pages(pages) == [], v._low_density_pages(pages)


def test_chapter_tail_below_min_is_flagged():
    # A-2: 다음이 새 장이어도 꼬리가 하한(_CHAPTER_TAIL_MIN=90) 미만이면 흘러넘침 결함으로 hit.
    # 하한 이상은 정상 조판 꼬리로 면제 — 3중 사각(_ORPHAN_MIN 40~120 장꼬리)이 41~89 로 축소됨을 증명.
    def _tail_hits(chars):
        pages = ["표지", "제 1 장 " + "가" * 200, "나" * chars, "제 2 장 " + "다" * 200, "맺음"]
        return [h["page"] for h in v._low_density_pages(pages)]

    for c in (41, 67, 89):  # 하한 미만 → 저밀도 hit(page 3) — 흘러넘침 결함
        assert _tail_hits(c) == [3], (c, _tail_hits(c))
    for c in (90, 119):  # 하한 이상 → 면제(정상 조판 꼬리)
        assert _tail_hits(c) == [], (c, _tail_hits(c))


def test_low_density_keeps_short_page_before_colophon():
    # 맺음('글을 맺으며') 직전의 짧은 본문 말미 = 원래 'PDF 말미 밀도' 회귀 케이스.
    # 다음 페이지가 새 장이 아니므로 챕터꼬리 제외에 걸리지 않고 계속 차단되어야 한다.
    pages = [
        "표지",
        "제 1 장 본문 " + "가" * 200,
        "본문 말미가 너무 짧게 끝납니다.",  # <120, 다음이 맺음(장 아님)
        "글을 맺으며 감사합니다.",  # 마지막(제외)
    ]
    hits = v._low_density_pages(pages)
    assert [h["page"] for h in hits] == [3], hits


def test_toc_threshold_boundary_scopes_body_scanners():
    # N1(2026-07-04 재감사 후속): _TOC_MAX_CHARS=520 경계 코너 고정.
    # '목차' 단어가 든 페이지가 상한 미만이면 목차로 본문 스캐너에서 제외되고,
    # 상한 이상이면 본문으로 포함되어야 한다(긴 본문의 '목차' 언급 오제외 방지).
    # T3.5/B-5 에서 상한이 400→520 으로 넓어진 지점의 완화 감시 앵커.
    def _body_pages(toc_chars):
        toc = "목차 " + "가" * (toc_chars - 3)
        assert len(toc) == toc_chars
        pages = ["표지", toc, "제 1 장 " + "나" * 300]
        return [p for p, _ in v._customer_body_page_items(pages)]

    assert _body_pages(519) == [3], _body_pages(519)  # 상한 미만 → 목차 제외
    assert _body_pages(521) == [2, 3], _body_pages(521)  # 상한 이상 → 본문 포함


def test_chapter_regex_matches_two_digit_spaced_number():
    # A-4: 두 자리 장(제10장~)은 .cnum letter-spacing 으로 "제 1 0 장"처럼 숫자 사이 공백이
    # 추출된다. 이걸 못 잡으면 문서 후반(10장 이후)에서 장 인식이 비어 게이트가 비일관해진다.
    assert v._starts_new_chapter("제 1 0 장 어쩌구")
    assert v._starts_new_chapter("제 1 7 장 본문")
    assert v._CHAPTER_RX.search("제 1 0 장")
    # 한 자리 장·연속 표기도 계속 매칭(회귀 보증)
    assert v._starts_new_chapter("제 3 장 본문")
    assert v._CHAPTER_RX.search("제 17 장")


def test_is_toc_page_single_source():
    # T3.5/B-5: 목차 판정 단일 기준(_customer_body_page_items·_low_density·_orphan 공통).
    # '목차' 단어 + 상한(_TOC_MAX_CHARS=520, 2단 목차 수용) 미만이면 목차 페이지.
    assert v._is_toc_page("목차\n제 1 장 사주의 큰 그림")
    assert v._is_toc_page("목차 " + "가" * 400)  # <520 → 목차(2단 목차 크기)
    assert not v._is_toc_page("목차 " + "가" * 600)  # 상한 이상 → 본문(목차 오분류 방지)
    assert not v._is_toc_page("본문 페이지에는 그 단어가 없습니다.")  # 미포함


def test_toc_criterion_is_unified_across_scanners():
    # 단일화 회귀: 짧은 목차 넘침 꼬리('목차' 포함, <120)는 세 스캐너 모두에서 목차로 제외.
    # 저밀도·오펀 둘 다 넘침 목차를 콘텐츠 결함으로 오탐하지 않는다(behavior-preserving 확인).
    toc_tail = "목차 이어짐 " + "제 5 장 관계의 결"  # '목차' 포함, 짧음
    pages = ["표지", "제 1 장 " + "가" * 200, toc_tail, "제 2 장 " + "나" * 200, "글을 맺으며"]
    assert v._low_density_pages(pages) == [], v._low_density_pages(pages)
    assert v._orphan_pages(pages) == [], v._orphan_pages(pages)
    # 본문 페이지(목차 미포함, <120)는 계속 저밀도로 잡힘(단일화가 게이트를 약화하지 않음)
    pages2 = ["표지", "제 1 장 " + "가" * 200, "본문이 너무 짧게 끝납니다.", "글을 맺으며"]
    assert [h["page"] for h in v._low_density_pages(pages2)] == [3]


def test_split_paragraphs_merges_short_tail():
    # '있습니다.' 같은 짧은 마지막 단락은 직전 단락에 합쳐 단독 페이지화 방지
    text = "앞 단락은 충분히 깁니다. 흐름을 이어 갑니다.\n\n있습니다."
    paras = render_pdf._split_paragraphs(text)
    assert len(paras) == 1
    assert paras[0].endswith("있습니다.")
    # 긴 마지막 단락은 그대로 분리 유지
    text2 = "첫 단락입니다.\n\n두 번째 단락은 충분히 길어서 합쳐지지 않습니다."
    assert len(render_pdf._split_paragraphs(text2)) == 2


def test_report_template_keeps_paragraph_tails_together():
    # Avoid two-line customer-facing tails on an otherwise empty premium page.
    template = Path("sajugen/render/templates/report.html.j2").read_text(encoding="utf-8")
    assert "orphans:4;widows:4" in template


# ───────────────── H1.5.3: 본문 페이지 분리(단어 키워드로 제외 금지) ─────────────────
def test_customer_body_pages_keeps_keyword_pages():
    # '오행/명식/십성'이 있어도 본문 페이지를 제외하면 안 된다(치명 구멍 방지).
    pages = [
        "표지 김태수 · 김태성 · 장순조",  # p1 표지(제외)
        "목차\n제 1 장 ...",  # 목차(제외)
        "오행을 함께 보면, 김태수는 임인일주입니다. " * 5,  # 본문(유지) — 오행 단어 있어도
        "명식과 십성을 보면 태수 씨 일간은 계수입니다. " * 5,  # 본문(유지)
        "본문에 나온 용어 풀이 ...",  # 부록(제외)
    ]
    body, allowed = v._customer_body_pages(pages)
    assert "김태수는 임인일주입니다" in body  # 오행 동반 본문 유지
    assert "태수 씨 일간은 계수입니다" in body  # 명식/십성 동반 본문 유지
    assert "표지" not in body and "목차" not in body and "용어 풀이" not in body
    assert "김태수 · 김태성 · 장순조" in allowed  # 표지는 제외 영역


def _render_sections(secs, out_name, input_civil="테스트"):
    from sajugen import config as cfg
    from types import SimpleNamespace

    require_playwright_subprocess()
    report = SimpleNamespace(sections=secs)
    fake_saju = SimpleNamespace(input_civil=input_civil)
    bp = dict(cfg.brand("seodam"))
    return render_pdf.render_pdf(report, fake_saju, out_name, name="", brand=bp)


_FULL = ["김태수", "김태성", "장순조"]
_IDSPEC = ({"임"}, {"임수"}, [(["김태수", "태수", "태수 씨", "자기 자신"], "임수")])


def test_verify_gate_fails_on_name_and_identity_violation():
    # 단어(오행·명식·십성) 동반 본문에서도 이름·일간 위반을 잡아 gate_pass=False.
    secs = [
        _sn("a", "각자의 결", "오행을 함께 보면, 김태수는 임인일주입니다. " * 25),
        _sn("b", "중심 글자", "오행과 명식을 함께 보면, 태수 씨 일간은 계수입니다. " * 25),
    ]
    path = _render_sections(secs, "test_h153_violation.pdf")
    r = v.verify(path, ref_year=2026, names=_FULL, name_full=_FULL, identity=_IDSPEC)
    assert r["name_policy_clean"] is False, r["name_policy_hits"]
    assert r["identity_role_clean"] is False, r["identity_role_hits"]
    assert r["gate_pass"] is False


def test_verify_gate_allows_cover_middot_names():
    # 본문은 호칭만(위반 0), 표지에 'A · B · C' 전체이름 → 허용(allowed_hits)·gate_pass 영향 없음.
    body = "태수 씨는 차분한 사람입니다. 태성 씨와 순조 씨가 곁에서 받쳐 줍니다. " * 30
    secs = [_sn("a", "세 사람", body), _sn("b", "함께", body)]
    path = _render_sections(secs, "test_h153_cover.pdf", input_civil="김태수 · 김태성 · 장순조")
    r = v.verify(path, ref_year=2026, names=_FULL, name_full=_FULL, identity=_IDSPEC)
    assert r["name_policy_clean"] is True, r["name_policy_hits"]
    assert r["identity_role_clean"] is True, r["identity_role_hits"]
    assert set(r["name_policy_allowed_hits"]) >= {"김태수", "김태성", "장순조"}
    assert r["gate_pass"] is True, r


def test_verify_backcompat_no_spec():
    # spec 미전달 시 이름·일간 게이트는 skip(clean True 기본).
    secs = [_sn("a", "장", "김태수는 좋은 사람입니다. " * 40)]
    path = _render_sections(secs, "test_h153_backcompat.pdf")
    r = v.verify(path)  # name_full·identity 미전달
    assert r["name_policy_clean"] is True
    assert r["identity_role_clean"] is True


def _sn(sid, title, text):
    from types import SimpleNamespace

    return SimpleNamespace(id=sid, title=title, source_keys=["m"], final_text=text)


# ───────────────── H1.5.3.2: 신강약 group/role 게이트 ─────────────────
_SG = [
    {"full": "김태수", "given": "태수", "honor": "태수 씨", "singang": "신약"},
    {"full": "김태성", "given": "태성", "honor": "태성 씨", "singang": "신약"},
    {"full": "장순조", "given": "순조", "honor": "순조 씨", "singang": "신강"},
]


def test_verify_gate_fails_on_singang_group():
    secs = [_sn("a", "결", "세 사람 모두 신약입니다. 그래서 안정 쪽에 무게가 실립니다. " * 25)]
    path = _render_sections(secs, "test_h1532_group.pdf")
    r = v.verify(path, ref_year=2026, names=_FULL, name_full=_FULL, singang=_SG)
    assert r["singang_role_clean"] is False, r["singang_role_hits"]
    assert r["gate_pass"] is False


def test_verify_gate_fails_on_singang_subject():
    secs = [_sn("a", "결", "순조 씨는 신약입니다. 차분하게 흐름을 봅니다. " * 25)]
    path = _render_sections(secs, "test_h1532_subject.pdf")
    r = v.verify(path, ref_year=2026, names=_FULL, name_full=_FULL, singang=_SG)
    assert r["singang_role_clean"] is False, r["singang_role_hits"]
    assert r["gate_pass"] is False


def test_verify_gate_allows_singang_split():
    body = "태수 씨와 태성 씨는 신약이고, 순조 씨는 신강입니다. 역할을 나눠 맡으면 좋습니다. " * 25
    secs = [_sn("a", "결", body)]
    path = _render_sections(secs, "test_h1532_split.pdf")
    r = v.verify(path, ref_year=2026, names=_FULL, name_full=_FULL, singang=_SG)
    assert r["singang_role_clean"] is True, r["singang_role_hits"]


def test_verify_singang_backcompat_no_spec():
    secs = [_sn("a", "결", "세 사람 모두 신약입니다. " * 40)]
    path = _render_sections(secs, "test_h1532_backcompat.pdf")
    r = v.verify(path)  # singang 미전달
    assert r["singang_role_clean"] is True


# ───────────────── T3.2/B-2: 실렌더 결함주입 회귀(기하 게이트) ─────────────────
def test_real_render_inset_loss_fails_gate(monkeypatch):
    # 실 PDF 로 기하 게이트를 검증하는 첫 회귀(그동안 합성 fake doc 만 존재).
    # .body 인셋(max-width) 무효화 → 본문이 콘텐츠박스를 대칭으로 채움(20/20) → body_inset_lost
    # → gate_pass=False. 좌우 여백은 대칭이라 margin_asymmetry 로는 못 잡던 사각이다.
    long_body = "이 사람은 생활의 속도를 고르게 잡고 하루를 차분히 이어 갑니다. " * 40
    secs = [_sn("a", "결", long_body), _sn("b", "흐름", long_body)]

    # 정상 렌더 → 인셋 결함 0(false fail 0).
    ok_path = _render_sections(secs, "test_t32_ok.pdf")
    r_ok = v.verify(ok_path)
    assert all(h["kind"] != "body_inset_lost" for h in r_ok["layout_geometry_hits"]), r_ok[
        "layout_geometry_hits"
    ]

    # 결함 주입 — 단일 소스 상수(pdf._BODY_MAXW_MM)를 페이지폭 이상으로 올려 max-width 무효화.
    monkeypatch.setattr(render_pdf, "_BODY_MAXW_MM", 999.0)
    bad_path = _render_sections(secs, "test_t32_inset_lost.pdf")
    r_bad = v.verify(bad_path)
    kinds = {h["kind"] for h in r_bad["layout_geometry_hits"]}
    assert "body_inset_lost" in kinds, r_bad["layout_geometry_hits"]
    assert r_bad["gate_pass"] is False


# ───────────────── T3.5(a): 목차 재넘침 방어(2단 목차) ─────────────────
_T35_TITLES = [
    "사주의 큰 그림",
    "타고난 기질과 성향의 결",
    "오행의 균형",
    "십성의 무늬",
    "신강약의 결",
    "격국과 용신 풀이",
    "대운의 흐름",
    "올해의 운",
    "관계와 인연의 결",
    "재물의 결",
    "직업과 방향",
    "건강 관리의 결",
    "가족 인연",
    "이동과 변화의 시기",
    "학업과 성취",
    "심리 기질",
    "길신과 흉살",
    "시기 선택",
    "마음 다스리기",
    "선택의 길",
    "맺음 방향",
    "덧붙이는 말",
]


def test_toc_two_column_keeps_22_chapters_one_page():
    # 실측: 단일 열 목차는 14행/페이지라 15장부터 2페이지로 넘쳐 희소 목차 페이지가 생겼다.
    # 장 22개 → 2단 목차로 1페이지 유지(표지 p1·목차 p2·첫 장 p3). 목차 오버플로 페이지가
    # 본문으로 오분류돼 기하·저밀도 게이트를 깨지 않는지 함께 확인(회귀).
    body = "이 장은 충분한 분량의 본문입니다. " * 30
    secs = [_sn(f"s{i}", _T35_TITLES[i], body) for i in range(22)]
    path = _render_sections(secs, "test_t35_22ch.pdf")
    import fitz

    doc = fitz.open(path)
    pages = [doc.load_page(i).get_text() for i in range(doc.page_count)]
    doc.close()
    assert v._is_toc_page(pages[1]), len(pages[1].strip())  # 목차는 p2 하나(<상한)
    first_body = next(i for i, t in enumerate(pages) if "충분한 분량" in t and i >= 1)
    assert first_body == 2, first_body  # index 0 표지·1 목차·2 첫 장 → 목차 1페이지
    r = v.verify(path)
    assert r["layout_geometry_clean"] is True, r["layout_geometry_hits"]
    assert r.get("low_density_pages") == [], r.get("low_density_pages")


def test_toc_two_column_threshold_boundary():
    # 임계(_TOC_SINGLE_COL_MAX=14): 이하 단일 열(기존 동작 보존), 초과 2단 목차.
    from types import SimpleNamespace

    from sajugen import config as cfg

    def _html(n):
        secs = [
            SimpleNamespace(id=f"s{i}", title=f"장 제목 {i}", final_text="본문 문장. " * 20)
            for i in range(n)
        ]
        return render_pdf.render_html(
            SimpleNamespace(sections=secs),
            SimpleNamespace(input_civil="테스트"),
            name="",
            brand=dict(cfg.brand("seodam")),
        )

    # 'toc-2col' 은 <style> 안 CSS 정의(.toc-2col ...)에도 있으므로 적용된 클래스 문자열로 판정.
    assert 'class="toc-list toc-2col"' not in _html(14)  # 임계 이하 = 단일 열
    assert 'class="toc-list toc-2col"' in _html(15)  # 초과 = 2단
