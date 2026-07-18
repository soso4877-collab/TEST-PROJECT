# -*- coding: utf-8 -*-
"""자미 별-트레잇 정본 배선(docs/24) 테스트 — 양방·데이터 순정·전수 커버·가드 비악화.

검증: (1) 별 서술이 이름 나열이 아니라 정본 기질을 담는다(비-no-op), (2) 정본 테이블에
길흉·예측·성별 단정 토큰이 0(데이터 순정), (3) 실 엔진 14주성 전수 커버(누락 시 fail),
(4) 공궁·정본 밖 별은 fail-closed(빈 문자열), (5) 기질 서술이 실린 자미 챕터가 기존
고객정책 가드(safe_lint 등)를 통과한다.
비검증: 실모델 자미 서술 품질·실 PDF 육안(운영자 승인 유료 재run 몫).
"""

import types

from sajugen.calc import engine
from sajugen.calc.ziwei import Star
from sajugen.content import (
    customer_meta_lint,
    quality_lint,
    rules,
    safe_lint,
    style_lint,
)
from sajugen.content import ziwei_temperament as zt

# iztro_py(ko-KR)가 산출하는 14주성 한글명(실 엔진 실측 고정 — 전수 커버 앵커).
_CANON_14 = {
    "자미", "천기", "태양", "무곡", "천동", "염정", "천부",
    "태음", "탐랑", "거문", "천상", "천량", "칠살", "파군",
}


def _palace(*stars):
    return types.SimpleNamespace(major_stars=list(stars))


def _star(name, brightness="", sihua=""):
    return Star(name=name, type="major", brightness=brightness, sihua=sihua)


def test_canon_covers_all_14_major_stars():
    # 정본 테이블이 실 엔진 14주성을 정확히 전수 커버(누락·오타·잉여 시 fail-closed).
    assert set(zt.STAR_TEMPERAMENT) == _CANON_14
    for name in _CANON_14:
        assert zt.has_star(name)
        t = zt.STAR_TEMPERAMENT[name]
        assert t["core"].strip() and t["shadow"].strip()


def test_engine_star_names_match_canon_keys():
    # 실 명반에 나온 주성 이름이 전부 정본 키에 있어야 배선이 fail-closed 되지 않는다.
    r = engine.build(1990, 5, 20, 14, 30, is_male=True)
    seen = set()
    for p in r.ziwei.palaces:
        for s in p.major_stars:
            seen.add(s.name)
    assert seen, "명반에 주성이 하나도 없다(엔진 이상)"
    assert seen <= set(zt.STAR_TEMPERAMENT), f"정본 미커버 주성: {seen - set(zt.STAR_TEMPERAMENT)}"


def test_hwagi_matches_docs24():
    # docs/24 §1 化氣를 손실 없이 보존한다(印·庫·官祿主·肅殺 등 축약 금지). 오라클 = docs/24 §1 표.
    expected = {
        "자미": "尊", "천기": "善", "태양": "貴(官祿主)", "무곡": "財",
        "천동": "福", "염정": "囚", "천부": "印·庫", "태음": "富",
        "탐랑": "桃花", "거문": "暗", "천상": "印", "천량": "蔭",
        "칠살": "將(肅殺)", "파군": "耗",
    }
    assert set(zt.STAR_TEMPERAMENT) == set(expected)
    for name, hwagi in expected.items():
        assert zt.STAR_TEMPERAMENT[name]["hwagi"] == hwagi, f"{name} 化氣 불일치"


def test_sihua_direction_preserves_docs24_axes():
    # docs/24 §3 사화 4방향 축을 손실 없이 보존한다(축약 시 정본 의미 유실 방지).
    axes = {
        "화록": ["재복", "유통", "기회", "인연"],
        "화권": ["주도", "장악", "경쟁", "강화"],
        "화과": ["명예", "이름", "문서", "품격"],
        "화기": ["집착", "결핍", "번민"],
    }
    for sihua, needed in axes.items():
        d = zt.SIHUA_DIRECTION[sihua]
        missing = [a for a in needed if a not in d]
        assert not missing, f"{sihua} 방향 축 누락: {missing}"
    assert "막힘" in zt.SIHUA_DIRECTION["화기"]  # 장애=막힘으로 보존


def test_data_purity_no_fortune_or_gender_verdicts():
    # 정본 데이터(hwagi 포함 모든 canon 필드)는 기질만 — 길흉·예측·성별 단정 토큰 0.
    forbidden = [
        "부귀", "빈천", "요절", "단명", "수명", "적중", "반드시", "틀림없이",
        "운명", "횡재", "길흉", "불리하", "재물운", "관운", "여성", "남성",
    ]
    blobs = []
    for t in zt.STAR_TEMPERAMENT.values():
        blobs += [t["hwagi"], t["core"], t["shadow"]]
    blobs += list(zt.SIHUA_DIRECTION.values())
    blobs += zt.SIHUA_FRAMES
    for frames in zt.BRIGHTNESS_FRAMES.values():
        blobs += frames
    text = " ".join(blobs)
    hits = [w for w in forbidden if w in text]
    assert not hits, f"정본에 금칙 토큰 유입: {hits}"
    # 비공허성: 스캔이 실제로 금칙(성별·길흉)을 잡는지 심어 확인한다.
    planted = "이 별은 여성에게 불리하고 부귀를 준다"
    assert [w for w in forbidden if w in planted], "금칙 스캔이 무력(비공허성 실패)"


def test_palace_temperament_carries_trait_and_modifiers():
    # 비-no-op: 특정 주성 궁을 서술하면 그 별의 정본 핵심 기질이 실린다(이름 나열이 아님).
    out = rules._palace_temperament(_palace(_star("자미", "庙", "화록")))
    assert "질서를 세워 이끄는" in out  # 자미 core 조각
    assert "짊어지고 고집으로 흐르는" in out  # 자미 shadow 조각
    assert "밝" in out  # 밝음(庙) 등급 앵커(프레임 _pick 무관 공통)
    assert "재복과 유통" in out and "인연" in out  # 화록 방향(정본 4축 보존)

    # 밝기 3단 분기(등급 앵커): 함지(陷)=어두, 득/이(得利)=무난, 평(平)=중립 문구 생략.
    dark = rules._palace_temperament(_palace(_star("염정", "陷")))
    assert "어두" in dark
    favor = rules._palace_temperament(_palace(_star("무곡", "得")))
    assert "무난" in favor
    neutral = rules._palace_temperament(_palace(_star("천동", "平")))
    assert "밝" not in neutral and "어두" not in neutral and "무난" not in neutral


def test_brightness_and_sihua_frames_vary_across_stars():
    # 반복 방지(advisor 발견): 밝기·사화 문구가 별마다 verbatim 반복되지 않는다.
    # 14주성을 같은 등급(庙)·같은 사화(화록)로 렌더해도 _pick 이 문형을 분산시킨다.
    bright_sents, sihua_sents = set(), set()
    for name in zt.STAR_TEMPERAMENT:
        out = rules._palace_temperament(_palace(_star(name, "庙", "화록")))
        for frame in zt.BRIGHTNESS_FRAMES["bright"]:
            if frame in out:
                bright_sents.add(frame)
        for frame in zt.SIHUA_FRAMES:
            if frame.format(d=zt.SIHUA_DIRECTION["화록"]) in out:
                sihua_sents.add(frame)
    assert len(bright_sents) >= 2, "밝기 문구가 한 벌로 고정(반복)"
    assert len(sihua_sents) >= 2, "사화 문구가 한 벌로 고정(반복)"


def test_empty_or_off_canon_palace_is_fail_closed():
    # 공궁·정본 밖 별은 빈 문자열(크래시·즉흥 서술 0).
    assert rules._palace_temperament(_palace()) == ""
    assert rules._palace_temperament(None) == ""
    assert rules._palace_temperament(_palace(_star("가상성", "庙", "화록"))) == ""


def test_ziwei_chapter_carries_temperament_and_passes_guards():
    # 통합 골격 경로(joined 챕터): 자미 챕터에 정본 기질이 실리고, 기존 고객정책 가드를
    # 합산 텍스트에서 통과한다(섹션 조각이 아니라 실제 고객이 받는 챕터 단위로 확인).
    r = engine.build(1990, 5, 20, 14, 30, is_male=True)
    chapters = rules.build_all(r, ref_year=2026)
    zw = chapters.get("ziwei", "")
    assert zw, "자미 챕터가 비었다"
    # 기질 서술이 실렸다(정형 어구 중 하나 이상).
    assert ("기질입니다" in zw) or ("결을 지녔고" in zw) or ("쪽이 도드라지되" in zw)
    # 안전·품질·메타 가드 비악화(결과보장·운명론·모순·문서 진행 발화 0).
    assert safe_lint.lint(zw) == []
    assert quality_lint.lint(zw) == []
    assert customer_meta_lint.lint(zw) == []


def test_my_temperament_output_is_style_clean():
    # 내 기여분(기질 문안)은 style_lint 위반 0 — em dash·가운뎃점·시적비유·반복 미유입.
    # (챕터의 기존 불릿 '· '·구분자 ' — '는 이 배선과 무관한 골격 조판이라 격리 검증한다.)
    for i, name in enumerate(zt.STAR_TEMPERAMENT):
        br = ["庙", "旺", "得", "利", "平", "陷"][i % 6]
        sh = ["화록", "화권", "화과", "화기", ""][i % 5]
        out = rules._palace_temperament(_palace(_star(name, br, sh)))
        assert style_lint.lint(out) == [], f"{name} 기질 문안 style 위반: {style_lint.lint(out)}"


def test_ziwei_chapter_has_no_duplicate_soul_temperament():
    # 회귀(advisor 발견): summary 와 palaces 가 명궁 주성 기질을 이중 서술하지 않는다.
    r = engine.build(1990, 5, 20, 14, 30, is_male=True)
    zw = rules.build_all(r, ref_year=2026).get("ziwei", "")
    soul = next((p for p in r.ziwei.palaces if getattr(p, "is_soul", False)), None)
    assert soul is not None, "명궁을 찾지 못했다"
    for s in soul.major_stars:
        frag = zt.STAR_TEMPERAMENT.get(s.name, {}).get("core", "")
        if frag:
            assert zw.count(frag) <= 1, f"명궁 {s.name} 기질이 챕터에 {zw.count(frag)}회 중복"


def test_off_canon_injection_still_blocked_by_guard():
    # 차단측(가드 live): 정본 밖에서 예측·길흉 단정이 섞여 들어오면 safe_lint 가 잡는다.
    assert safe_lint.lint("이 별 풀이는 반드시 적중합니다.") != []  # 예측 정확도 주장(절대규칙11)
    assert safe_lint.lint("이 별은 100% 부귀합니다.") != []  # 보장형
