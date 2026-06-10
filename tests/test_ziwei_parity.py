# -*- coding: utf-8 -*-
"""Phase 3 자미 유파 정책 + iztro 동등성.

- config: 유파 정책이 config/rule_profile.yaml(폴백 기본값)에서 로드되는지.
- build: ziwei.build 가 config 기반으로 정상 명반 생성(스모크).
- parity: iztro_py(런타임) ↔ iztro JS(원본) 구조 동등성 불일치 0(사이드카 있을 때만).
  사이드카(node + sajugen/tools/iztro-bridge/node_modules) 없으면 스킵.
"""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sajugen import config as cfg  # noqa: E402

_BRIDGE = Path(__file__).resolve().parents[1] / "sajugen" / "tools" / "iztro-bridge"


def _sidecar_ready() -> bool:
    return bool(shutil.which("node")) and (_BRIDGE / "node_modules" / "iztro").exists()


# ─────────────────────────── 유파 정책 config ───────────────────────────


def test_ziwei_config_defaults():
    z = cfg.ziwei()
    assert z["fix_leap"] is True
    assert z["language"] == "ko-KR"
    assert z["year_divide"] == "normal"  # 연경계=正月一日(설날), 立春 아님
    assert z["algorithm"] == "san_he"
    assert z["sihua_source"] == "iztro_default"


def test_ziwei_build_uses_config():
    # build 가 config(fix_leap/language) 기반으로 정상 12궁 명반 생성
    from sajugen.calc import ziwei
    from sajugen.input import time_correction as tc

    ct = tc.correct(2000, 8, 16, 4, 0)
    z = ziwei.build(ct, is_male=True)
    assert len(z.palaces) == 12
    assert z.five_elements_class
    assert z.soul_palace and z.body_palace


# ─────────────────────────── iztro 동등성(사이드카) ───────────────────────────


def test_ziwei_structural_parity():
    # 구조-핵심(궁 지지/천간·신궁·배치·사화·명신궁·오행국) 불일치 0 — 포팅 충실도.
    if not _sidecar_ready():
        pytest.skip("node/iztro 사이드카 미설치 — npm i in sajugen/tools/iztro-bridge")
    from scripts.verify_ziwei_parity import compare

    res = compare(60)
    assert res["struct_total"] == 0, res["struct"]


def test_ziwei_brightness_is_known_diff():
    # 밝기는 iztro 판본 차이(known-diff). 구조와 분리되어 surface 되는지 확인(차단 아님).
    if not _sidecar_ready():
        pytest.skip("node/iztro 사이드카 미설치")
    from scripts.verify_ziwei_parity import compare

    res = compare(30)
    assert res["struct_total"] == 0
    # 판본 차이가 실재함을 명시(향후 iztro_py 업데이트로 0 되면 이 단언 갱신)
    assert res["brightness_palace_mismatches"] > 0
