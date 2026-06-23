import os
import shutil
from pathlib import Path
from types import MethodType

import pytest


Path("pytest-cache").mkdir(exist_ok=True)


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
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
