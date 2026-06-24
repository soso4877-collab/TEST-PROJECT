# -*- coding: utf-8 -*-
"""Helpers for tests that need Playwright subprocess support."""

from __future__ import annotations

import os
from functools import lru_cache

import pytest


@lru_cache(maxsize=1)
def _playwright_subprocess_error() -> str | None:
    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED"):
        return "Playwright subprocess skipped in Codex sandbox"
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright():
            return None
    except PermissionError as exc:
        return f"Playwright subprocess blocked in this environment: {exc}"


def require_playwright_subprocess() -> None:
    reason = _playwright_subprocess_error()
    if reason:
        pytest.skip(reason)
