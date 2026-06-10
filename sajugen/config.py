# -*- coding: utf-8 -*-
"""유파·계산 정책 로더 — config/rule_profile.yaml 을 읽는다(절대규칙 6).

하드코딩 분기 금지: 자미 윤달/연경계/유파/언어/사화·밝기 출처를 이 설정에서만 읽는다.
파일이 없거나 키가 비면 _DEFAULTS 로 폴백(런타임 동작 보장). 1회 로드 후 캐시.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_PROFILE = Path(__file__).resolve().parents[1] / "config" / "rule_profile.yaml"

# 파일 부재/손상 시 폴백 = rule_profile.yaml 과 동일한 확정 기본값(docs/03 §1).
_DEFAULTS = {
    "ziwei": {
        "algorithm": "san_he",
        "language": "ko-KR",
        "fix_leap": True,
        "year_divide": "normal",
        "sihua_source": "iztro_default",
        "brightness_source": "iztro_py",
    },
    "myeongni_shinsal": {
        "profile": "default",
        "goegang_scope": "day_only",  # day_only(현행) | all_pillars
        "samhap_axis": "both",  # day_zhi | year_zhi | both
        "twelve_axis": "day_zhi",  # day_zhi(현대 대세) | year_zhi
        "gongmang_display": "year_day",  # year_day | day_only
    },
}


@lru_cache(maxsize=1)
def load() -> dict:
    """정책 dict 반환(캐시). 파일이 있으면 기본값 위에 병합."""
    cfg = {k: dict(v) for k, v in _DEFAULTS.items()}
    try:
        if _PROFILE.exists():
            data = yaml.safe_load(_PROFILE.read_text(encoding="utf-8")) or {}
            for section, vals in data.items():
                if isinstance(vals, dict):
                    cfg.setdefault(section, {}).update(vals)
                else:
                    cfg[section] = vals
    except Exception:
        pass  # 손상 시 기본값 유지(런타임 보장)
    return cfg


def ziwei() -> dict:
    """자미 정책 섹션."""
    return load().get("ziwei", _DEFAULTS["ziwei"])


def myeongni_shinsal() -> dict:
    """명리 신살 학파 정책 섹션(괴강 범위·삼합 축·12신살 축·공망 표기)."""
    return load().get("myeongni_shinsal", _DEFAULTS["myeongni_shinsal"])
