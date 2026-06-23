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


def test_split_paragraphs_merges_short_tail():
    # '있습니다.' 같은 짧은 마지막 단락은 직전 단락에 합쳐 단독 페이지화 방지
    text = "앞 단락은 충분히 깁니다. 흐름을 이어 갑니다.\n\n있습니다."
    paras = render_pdf._split_paragraphs(text)
    assert len(paras) == 1
    assert paras[0].endswith("있습니다.")
    # 긴 마지막 단락은 그대로 분리 유지
    text2 = "첫 단락입니다.\n\n두 번째 단락은 충분히 길어서 합쳐지지 않습니다."
    assert len(render_pdf._split_paragraphs(text2)) == 2


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
