# -*- coding: utf-8 -*-
"""유파·계산 정책 로더 — config/rule_profile.yaml 을 읽는다(절대규칙 6).

하드코딩 분기 금지: 자미 윤달/연경계/유파/언어/사화·밝기 출처를 이 설정에서만 읽는다.
파일이 없거나 키가 비면 _DEFAULTS 로 폴백(런타임 동작 보장). 1회 로드 후 캐시.
"""

from __future__ import annotations

from functools import lru_cache
import os
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
    "llm_models": {
        "compose": "claude-sonnet-4-6",
        "relationship_compose": "claude-sonnet-4-6",
        "classify": "claude-haiku-4-5-20251001",
        "polish": "claude-haiku-4-5-20251001",
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


def llm_models() -> dict:
    """LLM 모델 역할별 설정."""
    models = dict(_DEFAULTS["llm_models"])
    configured = load().get("llm_models", {})
    if isinstance(configured, dict):
        models.update({str(k): str(v) for k, v in configured.items() if v})
    env_map = {
        "compose": "SAJUGEN_LLM_COMPOSE_MODEL",
        "relationship_compose": "SAJUGEN_LLM_RELATIONSHIP_COMPOSE_MODEL",
        "classify": "SAJUGEN_LLM_CLASSIFY_MODEL",
        "polish": "SAJUGEN_LLM_POLISH_MODEL",
    }
    for key, env_name in env_map.items():
        val = os.environ.get(env_name)
        if val:
            models[key] = val
    return models


def llm_model(role: str) -> str:
    """역할명에 맞는 모델 ID. 미정의 역할은 compose 기본값으로 안전 폴백."""
    models = llm_models()
    return models.get(role) or models["compose"]


# --- 브랜드 프로필(config/brands.yaml) — 다계정 운영(2026-06-12) ---
_BRANDS = Path(__file__).resolve().parents[1] / "config" / "brands.yaml"
# 내장 프리셋(yaml 부재/손상 시에도 동작 보장). yaml 이 있으면 그 위에 병합.
_PRESETS = {
    "default": {
        "seal": "사주명리",
        "cover_title": "종합 사주 풀이",
        "closing_sign": "사주명리 드림",
    },
    "seodam": {
        "seal": "서담선생",
        "cover_title": "서담선생 종합 사주 풀이",
        "closing_sign": "서담선생 드림",
    },
    "sajudoryeong": {
        "seal": "사주도령",
        "cover_title": "사주도령 종합 사주 풀이",
        "closing_sign": "사주도령 드림",
    },
}
_BRAND_DEFAULT = _PRESETS["default"]
_SEAL_MAX = 24  # 자유 입력 브랜드 문구 길이 상한(표지·낙관 안전)


@lru_cache(maxsize=1)
def _brands() -> dict:
    out = {k: dict(v) for k, v in _PRESETS.items()}
    try:
        if _BRANDS.exists():
            data = yaml.safe_load(_BRANDS.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict):
                        out.setdefault(k, {}).update(v)
    except Exception:
        pass  # 손상 시 프리셋 유지(런타임 보장)
    return out


def brand(profile: str | None = None) -> dict:
    """브랜드 프로필 해석.

    - 미지정 → default 프리셋.
    - 프리셋/yaml 키(예: seodam) → 해당 프로필.
    - 프리셋에 없는 임의 문구 → 그 문구를 브랜드명으로 합성(운영자 자유 입력 지원).
      합성 시 입력은 표지·낙관 텍스트로만 쓰이고 길이 상한(_SEAL_MAX)으로 trim.
    """
    data = _brands()
    key = (profile or "default").strip()
    if key in data and isinstance(data[key], dict):
        p = data[key]
    else:
        name = key[:_SEAL_MAX]  # 자유 입력 문구
        p = {
            "seal": name,
            "cover_title": f"{name} 종합 사주 풀이",
            "closing_sign": f"{name} 드림",
        }
    out = dict(_BRAND_DEFAULT)
    out.update({k: v for k, v in p.items() if v})
    return out
