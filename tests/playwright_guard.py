# -*- coding: utf-8 -*-
"""Helpers for tests that need Playwright subprocess support."""

from __future__ import annotations

from functools import lru_cache

import pytest


@lru_cache(maxsize=1)
def _playwright_subprocess_error() -> str | None:
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
