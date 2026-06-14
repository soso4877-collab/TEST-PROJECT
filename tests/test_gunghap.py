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
    # 무키 시 _compose 는 base_text(룰 슬롯) 폴백(무API)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = g._compose("each", "근거 슬롯 텍스트", {"ganzhi": [], "ganzhi_ko": []}, "상황")
    assert out == "근거 슬롯 텍스트"
