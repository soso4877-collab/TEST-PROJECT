# -*- coding: utf-8 -*-
"""repetition.dedup_ilju_intro — 크로스챕터 일주 자기소개 중복 제거(2026-06-14 베타 지적).

소유 챕터(wonguk)는 보존, 다른 챕터의 짧은 '일주 자기소개 줄'만 제거하되 내용 문장은 보존.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen.content import repetition  # noqa: E402


def _sec(sid, text):
    return SimpleNamespace(id=sid, final_text=text)


def test_owner_keeps_nonowner_drops():
    secs = [
        _sec("wonguk", "순조님은 기미일주예요.\n네 기둥을 봅니다."),
        _sec("nature", "순조님은 기미일주입니다.\n토 기운이 강해요."),
    ]
    removed = repetition.dedup_ilju_intro(secs, owner_id="wonguk")
    assert removed == 1
    assert "기미일주" in secs[0].final_text  # 소유 챕터 보존
    assert "일주입니다" not in secs[1].final_text  # 비소유 자기소개 줄 제거
    assert "토 기운이 강해요." in secs[1].final_text  # 내용 줄은 보존


def test_content_bearing_sentence_preserved():
    # 일주를 풀이에 활용한 '긴 내용 문장'은 자기소개가 아니므로 보존(길이 상한 초과)
    long_line = (
        "태성님은 무오일주라, 안으로 단단하고 밖으로는 부드럽게 보이는 결이 함께 있어요 그래서"
    )
    secs = [
        _sec("wonguk", "태성님은 무오일주예요."),
        _sec("nature", long_line),
    ]
    repetition.dedup_ilju_intro(secs, owner_id="wonguk")
    assert secs[1].final_text == long_line  # 내용 문장은 손대지 않음


def test_no_intro_no_change():
    secs = [_sec("nature", "토 기운이 강하고 추진력이 있어요.")]
    removed = repetition.dedup_ilju_intro(secs, owner_id="wonguk")
    assert removed == 0
    assert secs[0].final_text == "토 기운이 강하고 추진력이 있어요."
