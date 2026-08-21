# -*- coding: utf-8 -*-
"""외부 의존성 없이 패키지 내부 자산 경로를 한곳에서 정의한다."""

from pathlib import Path


# 실행 CWD가 아니라 이 모듈 위치를 기준으로 패키지 자산의 절대경로를 조립한다.
PACKAGE_DIR = Path(__file__).resolve().parent
EPHEMERIS_DIR = PACKAGE_DIR / "assets" / "ephemeris"
EPHEMERIS_BSP = "de440s.bsp"
