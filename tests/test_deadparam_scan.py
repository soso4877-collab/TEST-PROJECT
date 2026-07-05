# -*- coding: utf-8 -*-
"""Phase 2(2026-07-06) — dead-param 정적 스캐너 양방 + C2 하드 게이트.

양방: 실제 미사용 파라미터를 검출(POSITIVE — 게이트 no-op 아님 증명, 방법론 B-2) +
내장 제외 규칙(self/cls·_접두·*args/**kwargs·stub·passthrough·데코레이터)이 정상을 통과.
하드 게이트: 정본 소스(sajugen+scripts) 스캔 == allowlist 외 0(결정론이라 게이트 가능).
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import deadparam_scan as dp  # noqa: E402


def _params_found(src: str) -> set[str]:
    return {f.param for f in dp._scan_tree(ast.parse(src), "synthetic.py")}


def test_detects_multiline_dead_param():
    # POSITIVE: 다중행 본문에서 선언만 되고 참조 안 된 파라미터를 검출.
    src = "def f(a, b, c):\n    x = a + 1\n    if c:\n        return x\n    return a\n"
    found = _params_found(src)
    assert "b" in found, "미사용 파라미터 b 를 검출해야 한다(게이트 실효성)"
    assert "a" not in found and "c" not in found


def test_detects_param_used_only_in_nested_scope_is_not_flagged():
    # 사각: 중첩 함수·컴프리헨션·f-string 안에서 쓰이면 사용으로 계산(오탐 방지).
    src = (
        "def f(a, b, c):\n"
        "    def inner():\n"
        "        return a\n"
        "    ys = [b for _ in range(3)]\n"
        "    return f'{c}' + str(ys) + str(inner())\n"
    )
    assert _params_found(src) == set()


def test_excludes_self_cls_underscore_and_varargs():
    src = (
        "class K:\n"
        "    def m(self, used, _ignored, cls_unused=None):\n"
        "        y = used + 1\n"  # 다중행(passthrough 아님)이라 미사용 인자 검출 대상
        "        return y\n"
        "def g(a, *args, **kwargs):\n"
        "    z = a + 1\n"
        "    return z\n"
    )
    # self·_ignored(_접두)·*args·**kwargs 제외. cls_unused 는 _접두 아니므로 검출돼야 함.
    found = _params_found(src)
    assert found == {"cls_unused"}


def test_excludes_stub_passthrough_and_decorated():
    src = (
        "from typing import overload\n"
        "def stub_ellipsis(a, b): ...\n"
        "def stub_pass(a, b):\n"
        "    pass\n"
        "def stub_raise(a, b):\n"
        "    raise NotImplementedError\n"
        "def stub_doc(a, b):\n"
        "    'doc'\n"
        "def passthrough(a, b):\n"
        "    return a\n"
        "@overload\n"
        "def ov(a, b): ...\n"
    )
    assert _params_found(src) == set()


def test_scan_repo_clean_against_allowlist():
    # C2 하드 게이트: 정본 소스 스캔의 미해결(allowlist 외)이 0.
    findings = dp.scan_paths(["sajugen", "scripts"])
    allow = dp.load_allowlist(dp.ROOT / "tests/deadparam_allowlist.txt")
    unresolved = sorted(f.key() for f in findings if f.key() not in allow)
    assert unresolved == [], f"미분류 dead-param(수정 또는 allowlist+사유 필요): {unresolved}"


def test_fixed_params_do_not_reappear():
    # 회귀: 이번에 제거한 실결함 2건이 스캔에서 사라졌는지(재발 시 RED).
    keys = {f.key() for f in dp.scan_paths(["sajugen"])}
    assert "sajugen/calc/advanced.py::geukguk::day_master" not in keys
    assert "sajugen/content/delivery_quality.py::analyze::page_texts" not in keys


def test_allowlist_requires_nonempty_reason(tmp_path):
    # 사유 없는 등재는 무효(로더가 드롭) — 거짓/빈 사유 방지(allowlist 는 참인 사유만).
    p = tmp_path / "al.txt"
    p.write_text(
        "## 주석\n"
        "a.py::f::x  # 진짜 사유\n"
        "b.py::g::y\n"  # 사유 없음 → 미등재
        "b.py::g::y  #   \n",  # 공백 사유 → 미등재
        encoding="utf-8",
    )
    allow = dp.load_allowlist(p)
    assert allow == {"a.py::f::x": "진짜 사유"}
