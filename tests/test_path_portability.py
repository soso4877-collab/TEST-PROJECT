# -*- coding: utf-8 -*-
"""천체력 자산 경로의 이식성과 누락 시 fail-closed 계약을 검증한다."""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest


def test_ephemeris_directory_is_package_relative_absolute_path() -> None:
    """상대 조립한 경로는 실행 CWD와 무관한 패키지 내부 절대경로여야 한다."""
    from sajugen import paths

    assets_dir = paths.PACKAGE_DIR / "assets"

    assert paths.EPHEMERIS_DIR.is_absolute()
    assert paths.EPHEMERIS_DIR == assets_dir / "ephemeris"


def test_packaged_ephemeris_file_exists() -> None:
    """새 클론에서도 계산에 필요한 추적 천체력 파일이 패키지 안에 있어야 한다."""
    from sajugen import paths

    assert (paths.EPHEMERIS_DIR / paths.EPHEMERIS_BSP).is_file()


def test_ephemeris_consumers_share_the_same_directory_constant() -> None:
    """두 계산 소비처가 별도 경로를 복제하지 않고 같은 Path 객체를 참조해야 한다."""
    from sajugen import paths
    from sajugen.calc import solarterms
    from sajugen.input import time_correction

    assert solarterms.EPHEMERIS_DIR is paths.EPHEMERIS_DIR
    assert time_correction.EPHEMERIS_DIR is paths.EPHEMERIS_DIR


def test_path_refactor_preserves_pillars_and_solar_term_time() -> None:
    """경로 리팩터 전의 명식과 절기 계산값을 회귀 앵커로 고정한다."""
    from sajugen.calc import engine, solarterms

    result = engine.build(
        2000,
        1,
        1,
        12,
        0,
        is_male=True,
        horoscope_date="2026-06-01",
    )
    myeongni = result.myeongni

    assert (
        myeongni.year.ganzhi,
        myeongni.month.ganzhi,
        myeongni.day.ganzhi,
        myeongni.hour.ganzhi,
    ) == ("己卯", "丙子", "戊午", "戊午")
    assert solarterms.solar_term_time(2000, 315) == datetime(
        2000,
        2,
        4,
        12,
        40,
        22,
        732545,
    )


def test_tracked_sajugen_python_has_no_absolute_path_literals() -> None:
    """git 추적 제품 코드만 스캔해 로컬 절대경로 재유입을 차단한다."""
    repository = Path(__file__).resolve().parents[1]
    absolute_path = re.compile(r"(?:[A-Za-z]:\\|/Users/|/home/)")

    # 정규식 자체의 양성 대조로 백슬래시 이스케이프 no-op을 먼저 차단한다.
    assert absolute_path.search(r'C:\example\asset')
    assert absolute_path.search('/Users/example/asset')
    assert absolute_path.search('/home/example/asset')

    tracked = subprocess.run(
        ["git", "ls-files", "--", "sajugen/*.py"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()
    assert tracked

    violations: list[str] = []
    for relative_path in tracked:
        source = (repository / relative_path).read_text(encoding="utf-8")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if absolute_path.search(line):
                violations.append(f"{relative_path}:{line_number}")

    assert violations == []


def test_missing_ephemeris_fails_before_loader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """자산 누락은 네트워크 Loader 호출보다 먼저 기대 경로를 담아 실패해야 한다."""
    import skyfield.api

    from sajugen import paths

    missing_dir = tmp_path / "missing-ephemeris"
    expected_path = missing_dir / paths.EPHEMERIS_BSP

    def loader_must_not_run(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("천체력 누락 상태에서 Loader를 호출하면 안 됩니다")

    # 두 import 소비처를 각각 깨끗한 모듈 상태로 다시 불러 실제 초기화 순서를 검증한다.
    for module_name in ("sajugen.calc.solarterms", "sajugen.input.time_correction"):
        previous_module = sys.modules.pop(module_name, None)
        parent_name, attribute_name = module_name.rsplit(".", maxsplit=1)
        parent_module = sys.modules[parent_name]
        try:
            with monkeypatch.context() as patch:
                patch.setattr(paths, "EPHEMERIS_DIR", missing_dir)
                patch.setattr(skyfield.api, "Loader", loader_must_not_run)
                with pytest.raises(FileNotFoundError) as exc_info:
                    importlib.import_module(module_name)
                assert str(expected_path) in str(exc_info.value)
        finally:
            sys.modules.pop(module_name, None)
            if previous_module is not None:
                sys.modules[module_name] = previous_module
                setattr(parent_module, attribute_name, previous_module)
