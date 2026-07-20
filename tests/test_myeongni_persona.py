# -*- coding: utf-8 -*-
"""명리 일간 성격 정본 배선(docs/25) 테스트 — 전수 커버·오라클·데이터 순정·다단 인과·비단정.

검증: (1) 10천간 전수 커버 + docs/25 §1 상징 오라클, (2) 정본 데이터에 길흉·예측·성별 토큰 0
(비공허성 포함), (3) 신강/신약/중화 modifier 분기, (4) 없는 오행 결핍↔갈망 양가, (5) character
챕터에 일간 성격 + 신강 방향 인과가 실린다(비-no-op) + 기존 가드 통과, (6) 내 성격 문안 style 격리
clean, (7) 물상 성격이 법칙 단정이 아니라 비단정 톤, (8) 정본 밖 일간 fail-closed.
비검증: 실모델 서술 품질·실 PDF 육안·비용(운영자 승인 유료 재run 몫).
"""

from sajugen.calc import engine
from sajugen.content import (
    client_tone_lint,
    customer_meta_lint,
    quality_lint,
    rules,
    safe_lint,
    style_lint,
)
from sajugen.content import myeongni_persona as mp

_GAN10 = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
_GAN_KO = dict(zip(_GAN10, ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]))


def test_all_10_gan_covered():
    assert set(mp.GAN_PERSONA) == set(_GAN10)
    for g in _GAN10:
        assert mp.has_gan(g)
        p = mp.GAN_PERSONA[g]
        assert p["symbol"].strip() and p["core"].strip() and p["shadow"].strip()


# docs/25 §1-1 코드 렌더 계약 = 오라클(코드 축약값 반복이 아니라 문서 계약을 독립 동결).
_RENDER_CONTRACT = {
    "甲": {"symbol": "큰 나무", "core": ["정직", "개척", "이끄"], "shadow": ["고집", "과신", "융통"]},
    "乙": {"symbol": "화초와 덩굴", "core": ["섬세", "적응", "아름다움"], "shadow": ["예민", "기대"]},
    "丙": {"symbol": "태양", "core": ["공명정대", "열정", "밀고"], "shadow": ["충동", "산만", "지속력"]},
    "丁": {"symbol": "촛불과 별빛", "core": ["헌신", "통찰", "문예"], "shadow": ["의심", "근심", "지치"]},
    "戊": {"symbol": "큰 산", "core": ["든든", "시야", "책임"], "shadow": ["고집", "경직", "더딘"]},
    "己": {"symbol": "너른 논밭", "core": ["실용", "조율", "자원"], "shadow": ["갈등", "주관", "휘둘"]},
    "庚": {"symbol": "무쇠와 칼", "core": ["결단", "의리", "실행"], "shadow": ["강경", "얽매임", "부딪"]},
    "辛": {"symbol": "보석", "core": ["예리", "섬세", "자존"], "shadow": ["까다", "비판", "고고"]},
    "壬": {"symbol": "바다와 강", "core": ["대범", "유연", "기지"], "shadow": ["산만", "정착", "휩쓸"]},
    "癸": {"symbol": "이슬비와 샘물", "core": ["총명", "직관", "강함"], "shadow": ["기복", "감추", "위축"]},
}


def test_render_contract_symbol_and_axes_frozen():
    # docs/25 §1-1 코드 렌더 계약 전수 동결: 표시 상징 + core/shadow 필수 축을 코드가 모두 보존한다.
    # (오라클이 코드 축약값을 반복하지 않고 문서 계약 축을 독립으로 검사 — 축 삭제 시 회귀 실패.)
    assert set(_RENDER_CONTRACT) == set(mp.GAN_PERSONA)
    for g, c in _RENDER_CONTRACT.items():
        p = mp.GAN_PERSONA[g]
        assert p["symbol"] == c["symbol"], f"{g} 표시 상징 불일치"
        for ax in c["core"]:
            assert ax in p["core"], f"{g} core 필수 축 '{ax}' 누락"
        for ax in c["shadow"]:
            assert ax in p["shadow"], f"{g} shadow 필수 축 '{ax}' 누락"


def test_data_purity_no_fortune_or_gender_verdicts():
    forbidden = [
        "부귀", "빈천", "요절", "단명", "수명", "적중", "반드시", "틀림없이",
        "운명", "횡재", "길흉", "불리하", "재물운", "관운", "여성", "남성",
    ]
    blobs = []
    for p in mp.GAN_PERSONA.values():
        blobs += [p["symbol"], p["core"], p["shadow"]]
    blobs += list(mp.SINGANG_MODIFIER.values())
    blobs += list(mp.ELEM_LACK.values())
    text = " ".join(blobs)
    hits = [w for w in forbidden if w in text]
    assert not hits, f"정본에 금칙 토큰 유입: {hits}"
    planted = "이 일간은 여성에게 불리하고 반드시 부귀합니다"
    assert [w for w in forbidden if w in planted], "금칙 스캔 무력(비공허성 실패)"


def test_singang_modifier_branches():
    for sg in ("신강", "신약", "중화"):
        assert mp.singang_modifier(sg).strip()
    assert mp.singang_modifier("판정 불가") == ""
    assert mp.singang_modifier("") == ""
    # 셋이 서로 다른 방향 문구(고정 한 벌 아님).
    assert len({mp.singang_modifier(s) for s in ("신강", "신약", "중화")}) == 3
    # modifier는 앞서 말한 일간 결(이 결)의 발현 '방향'만 잇는다.
    for sg in ("신강", "신약", "중화"):
        assert "이 결" in mp.singang_modifier(sg)
    # docs/25 §2 승인 방향 축(신강=주도 / 신약=조율·수용·신중 / 중화=맞춤).
    assert "주도" in mp.singang_modifier("신강")
    assert any(k in mp.singang_modifier("신약") for k in ("조율", "수용", "신중", "받아들이"))
    assert "맞추" in mp.singang_modifier("중화") or "맞춰" in mp.singang_modifier("중화")


def test_singang_modifier_has_no_strength_frame_and_no_duplication():
    # B-3(Codex): modifier는 강약 프레임(강한/여린/약한/나약)을 만들지 않는다 — 신약 '약함 아님'
    # 재서술은 strength 골격 전담. 한 챕터(nature=character+strength)에서 약함 프레임을 이중으로 만들지 않는다.
    for mod in mp.SINGANG_MODIFIER.values():
        for frame in ("강한", "여린", "약한", "나약"):
            assert frame not in mod, f"modifier에 강약 프레임 '{frame}'"
    r = engine.build(1990, 5, 20, 14, 30, is_male=True)  # 신약
    zw = rules.build_all(r, ref_year=2026).get("nature", "")
    assert zw.count("나약하다는 뜻이 아니라") == 1  # 약함 재서술은 strength 한 곳만
    assert mp.singang_modifier("신약") in zw  # 승인 방향은 존재
    for frame in ("여린 편", "약한 편"):
        assert frame not in zw  # modifier가 약함 프레임 재생성 안 함


def test_elem_lack_is_ambivalent():
    for elem in ("목", "화", "토", "금", "수"):
        assert mp.elem_lack_phrase(elem).strip()
    assert mp.elem_lack_phrase("") == ""
    # 화·수는 결핍↔갈망 양가('오히려 ~').
    assert "오히려" in mp.elem_lack_phrase("화")
    assert "오히려" in mp.elem_lack_phrase("수")


def test_persona_output_passes_customer_guards():
    # 성격 문안(일간 lead + 신강 modifier)은 guarded 챕터(nature·consult)로 흘러가므로 style 뿐 아니라
    # register/raw_calc 하드 금칙까지 clean이어야 한다(예: '큰 그림'=big_picture register 금칙 재발 방지).
    for g in _GAN10:
        for sg in ("신강", "신약", "중화"):
            lead, mod = rules._ilgan_persona_parts(g, _GAN_KO[g], sg)
            for t in (lead, mod):
                if not t:
                    continue
                hits = (
                    style_lint.lint(t)
                    + client_tone_lint.register_lint(t)
                    + client_tone_lint.raw_calc_lint(t)
                    + safe_lint.lint(t)
                )
                assert hits == [], f"{g}/{sg} 가드 위반: {hits}"


def test_off_canon_gan_fail_closed():
    lead, mod = rules._ilgan_persona_parts("戀", "련", "신강")  # 존재하지 않는 일간
    assert lead == "" and mod == ""


def test_character_chapter_carries_persona_and_causal_chain():
    # 통합 골격: nature(=ilgan+sipseong+character+strength) 챕터에 일간 성격 + 신강 방향 인과가 실리고
    # 기존 고객정책 가드를 통과한다(사람이 받는 챕터 단위).
    r = engine.build(1990, 5, 20, 14, 30, is_male=True)  # 乙일간·신약
    zw = rules.build_all(r, ref_year=2026).get("nature", "")
    assert zw
    p = mp.GAN_PERSONA["乙"]
    assert p["core"] in zw  # 일간 성격 실림
    assert p["shadow"] in zw  # 그늘도
    assert "힘의 강약을 겹치면" in zw  # 신강→기질 방향 인과(다단 연결)
    assert mp.singang_modifier("신약") in zw  # 신약 modifier
    assert safe_lint.lint(zw) == []
    assert quality_lint.lint(zw) == []
    assert customer_meta_lint.lint(zw) == []


def test_persona_tone_is_nondogmatic():
    # 물상 성격은 B급 → 법칙 단정이 아니라 '경향/갈래/보곤' 비단정 톤.
    joined = " ".join(
        rules._ilgan_persona_parts(g, _GAN_KO[g], "중화")[0] for g in _GAN10
    )
    for g in _GAN10:
        lead = rules._ilgan_persona_parts(g, _GAN_KO[g], "중화")[0]
        assert any(k in lead for k in ("경향", "갈래", "보곤")), f"{g} 단정 톤"
    assert "반드시" not in joined and "틀림없" not in joined
