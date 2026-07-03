import os
import shutil
from pathlib import Path
from types import MethodType

import pytest


Path("pytest-cache").mkdir(exist_ok=True)


@pytest.fixture(autouse=True)
def _block_live_anthropic(request, monkeypatch):
    """T5.1/E-4: 모든 테스트에서 ANTHROPIC_API_KEY 를 기본 삭제해 실 API 실호출·과금·비결정을
    구조적으로 차단한다(과거 test_p3 가 키 상존 시 실호출하던 사고 방지). 실호출이 필요한
    테스트만 @pytest.mark.llm_live 로 명시 opt-in. 테스트 본문에서 setenv 로 가짜 키를 넣는
    경우는 이 fixture 이후 실행되어 그대로 유효(가짜 키로 백엔드 선택 로직만 검증)."""
    if request.node.get_closest_marker("llm_live"):
        return
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    # 실 Anthropic API 실호출 방지 opt-in 마커(T5.1/E-4) — 위 autouse fixture 참조.
    config.addinivalue_line(
        "markers", "llm_live: 실제 ANTHROPIC_API_KEY 로 실호출을 허용(과금) — 기본은 키 삭제"
    )
    if os.name != "nt":
        return

    factory = getattr(config, "_tmp_path_factory", None)
    if factory is None:
        return

    workspace = Path.cwd().resolve()

    def getbasetemp(self):
        if self._basetemp is not None:
            return self._basetemp

        if self._given_basetemp is None:
            basetemp = workspace / "pytest-basetemp"
        else:
            basetemp = Path(self._given_basetemp)

        if not basetemp.is_absolute():
            basetemp = workspace / basetemp
        basetemp = basetemp.resolve()

        if basetemp != workspace and workspace not in basetemp.parents:
            raise RuntimeError(f"refusing pytest basetemp outside workspace: {basetemp}")

        if basetemp.exists():
            shutil.rmtree(basetemp, ignore_errors=True)
        basetemp.mkdir(parents=True, exist_ok=True)
        self._basetemp = basetemp
        return basetemp

    def mktemp(self, basename, numbered=True):
        basename = self._ensure_relative_to_basetemp(basename)
        root = self.getbasetemp()

        if not numbered:
            path = root / basename
            path.mkdir()
            return path

        for index in range(10000):
            path = root / f"{basename}{index}"
            try:
                path.mkdir()
            except FileExistsError:
                continue
            return path
        raise RuntimeError(f"could not allocate pytest tmp path for {basename}")

    factory.getbasetemp = MethodType(getbasetemp, factory)
    factory.mktemp = MethodType(mktemp, factory)
