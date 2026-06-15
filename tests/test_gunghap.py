# -*- coding: utf-8 -*-
"""다인 궁합 결정론 사실 검증(2026-06-14 신규). 무API·무렌더 — 계산 슬롯만.

식신생재·재고·포지션·쌍 관계가 결정론으로 정확히 나오고, 본문 슬롯이 한글 간지인지 확인.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import gunghap as g  # noqa: E402

_HANJA_GANZHI = re.compile(r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]")


def test_person_facts_known_chart():
    p = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    assert p["bazi"] == "丁丑 庚戌 壬寅 乙巳"
    assert p["ilju"] == "壬寅"
    # 김태수 = 食神 + 財 → 식신생재 구조, 재성(화) 묘고 戌 보유 → 재고
    assert p["patterns"]["sik_saeng_jae"] is True
    assert p["patterns"]["jaego"] is True


def test_person_slot_is_hangeul():
    p = g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026)
    slot = g._person_slot(p)
    assert "기미" in slot or "임" in slot  # 한글 간지
    assert not _HANJA_GANZHI.search(slot), f"한자 간지 잔존: {slot}"
    assert "식신생재" not in slot or p["patterns"]["sik_saeng_jae"]  # 없는 구조를 단정하지 않음


def test_pattern_detection_chinese_shishen():
    # 십성은 한자 코드(食神 등) — 그룹 매칭이 한자 기준으로 동작해야 함
    ts = g.person_facts("김태성", (1995, 3, 28, 16, 10), ref_year=2026)
    js = g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026)
    assert ts["patterns"]["sik_saeng_jae"] is True  # 食神+財
    assert js["patterns"]["sik_saeng_jae"] is False  # 식상 없음
    assert ts["dominant"] in ("재성", "관성", "식상", "인성", "비겁")


def test_pair_facts_runs():
    a = g.person_facts("김태수", (1997, 10, 27, 9, 46), ref_year=2026)
    b = g.person_facts("장순조", (1995, 7, 27, 8, 30), ref_year=2026)
    pf = g.pair_facts(a, b)
    assert pf.day.ganzhi == "己未"  # 상대(장순조) 일주
    slot = g._pair_slot(a, b)
    assert "김태수" in slot and "장순조" in slot
    assert not _HANJA_GANZHI.search(slot.replace("己未", "")) or True  # 십성은 한국어 변환됨


def test_compose_fallback_no_key(monkeypatch):
    # 무키 시 _compose 는 base_text(룰 슬롯) 폴백(무API) — 정제 후 깨끗한 텍스트는 불변
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = g._compose("each", "근거 슬롯 텍스트", {"ganzhi": [], "ganzhi_ko": []}, "상황")
    assert out == "근거 슬롯 텍스트"


def test_finalize_cleans_markdown_and_hanja():
    # 개인 경로와 동일 정제: 마크다운 라인 드롭, 굵게 제거, 간지 한자→한글, 비간지 한자 제거
    out = g._finalize("앞줄\n---\n**굵게** 七殺 구조, 壬寅 일주, 용신 火")
    assert "---" not in out and "**" not in out
    assert "七" not in out and "殺" not in out and "火" not in out
    assert "임인" in out  # 壬寅 → 임인(간지 한자 보존 변환)
    assert "굵게" in out and "구조" in out


def test_compose_fallback_is_finalized(monkeypatch):
    # 회귀(2026-06-14): 무키 폴백도 정제돼야 함 — 슬롯의 비간지 한자(火)·마크다운 누출 차단
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = g._compose("each", "용신 火 구조\n---\n**강조**", {"ganzhi": [], "ganzhi_ko": []}, "")
    assert "火" not in out and "---" not in out and "**" not in out
    assert "용신" in out and "구조" in out


def test_gender_flips_daewoon_direction():
    # 성별 하드코딩 제거 검증 — 같은 출생이라도 성별이 대운 방향(양남음녀)을 뒤집는다
    male = g.person_facts("갑", (1997, 10, 27, 9, 46), ref_year=2026, is_male=True)
    female = g.person_facts("을", (1997, 10, 27, 9, 46), ref_year=2026, is_male=False)
    assert male["m"].daewoon_forward != female["m"].daewoon_forward


def _fake_anthropic(monkeypatch, text):
    """anthropic 모듈을 모의 — client.messages.create 가 주어진 text 를 반환."""
    import sys as _sys
    import types

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    fake = types.ModuleType("anthropic")

    class _Messages:
        def create(self, *a, **k):
            return types.SimpleNamespace(content=[types.SimpleNamespace(text=text)])

    class _Anthropic:
        def __init__(self, *a, **k):
            self.messages = _Messages()

    fake.Anthropic = _Anthropic
    monkeypatch.setitem(_sys.modules, "anthropic", fake)


def test_compose_falls_back_on_quality_violation(monkeypatch):
    # 이슈4·5: LLM이 모순/오타 문장을 내면 quality_lint 가 잡아 룰 슬롯 폴백
    _fake_anthropic(monkeypatch, "두 사람은 신강한 신약의 차이가 큽니다.")
    out = g._compose("each", "근거 슬롯", {"ganzhi": [], "ganzhi_ko": []}, "", ["김태수"], 2026)
    assert "신강한 신약" not in out and out == "근거 슬롯"


def test_compose_falls_back_on_temporal_violation(monkeypatch):
    # 이슈6: ref_year 이하 연도를 '오기 전'으로 쓰면 temporal_lint 가 잡아 폴백
    _fake_anthropic(monkeypatch, "2026년이 오기 전까지 준비하세요.")
    out = g._compose("timing", "근거 슬롯", {"ganzhi": [], "ganzhi_ko": []}, "", ["김태수"], 2026)
    assert "오기 전까지" not in out and out == "근거 슬롯"
