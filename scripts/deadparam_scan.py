# -*- coding: utf-8 -*-
"""dead-param 정적 스캐너 (Phase 2, C2 자동화 — stdlib-only AST).

목적: 함수/메서드 서명에 선언됐지만 본문에서 한 번도 참조되지 않는 파라미터를 검출한다.
동기(팬텀 파라미터 3연속 QI-2026-07-04-01): day_offset(계산만·미소비)·verify spec·본인
생일 제외 인자가 "받기만 하고 안 쓰는" 상태로 방치돼 존재하지 않는 상대 궁합 서술이
개인 풀이에 주입됐다. 파라미터를 만들면 소비처 배선까지가 한 단위 — 그 불변식을 게이트한다.

무의존(stdlib ast 만) = 하드 게이트의 결정론·이식성(ruff 버전 드리프트로 게이트가 깨지지
않음). ruff --select ARG 는 크로스체크 오라클로만 사용(정본은 이 스캐너).

내장 제외(오탐 축소 — 이 방향만, 완화 아님):
  - self/cls, *args/**kwargs, _접두(관례상 의도적 미사용).
  - stub 본문(docstring only / pass / ... / raise) — 인터페이스·추상·프로토콜 선언.
  - 단일 `return <param>` 패스스루 — duck-typed 백엔드(RuleBackend.compose 등)가 다른
    백엔드 시그니처를 미러링하되 룰 전용이라 인자를 구조적으로 못 쓰는 정상 패턴.
  - @overload/@abstractmethod/@override/@abc.abstractmethod 데코레이터.
그 외 의도적 미사용은 tests/deadparam_allowlist.txt 에 사유와 함께 등재(전수 분류).
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]

# 비소스 서브트리 제외(gitignored 빌드 산출물·번들·캐시 — ruff 가 .gitignore 로 스킵하는 것과
# 동치). 정본 소스만 스캔한다: render/out(렌더 산출)·tools(288MB 번들)·캐시·임시.
_EXCLUDE_SEGMENTS = {"__pycache__", ".venv", "node_modules", "synthetic-tmp"}
_EXCLUDE_SUBPATHS = ("sajugen/render/out/", "sajugen/tools/", "tmp/", "data/")

_SKIP_PARAM_NAMES = {"self", "cls"}
_SKIP_DECORATORS = {"overload", "abstractmethod", "override", "abstractproperty"}


class Finding(NamedTuple):
    path: str  # ROOT 기준 상대경로(POSIX)
    lineno: int
    func: str  # 함수/메서드명(중첩은 outer.inner)
    param: str

    def key(self) -> str:
        return f"{self.path}::{self.func}::{self.param}"


def _decorator_names(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for d in getattr(node, "decorator_list", []):
        cur = d.func if isinstance(d, ast.Call) else d
        if isinstance(cur, ast.Name):
            out.add(cur.id)
        elif isinstance(cur, ast.Attribute):
            out.add(cur.attr)
    return out


def _is_stub_body(body: list[ast.stmt]) -> bool:
    """docstring only / pass / ... / raise 만 있는 본문(인터페이스·추상 선언)."""
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]  # 선두 docstring 제거
    if not body:
        return True
    if len(body) == 1:
        s = body[0]
        if isinstance(s, ast.Pass):
            return True
        if isinstance(s, ast.Raise):
            return True
        if (
            isinstance(s, ast.Expr)
            and isinstance(s.value, ast.Constant)
            and s.value.value is Ellipsis
        ):
            return True
    return False


def _is_trivial_passthrough(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """본문이 (docstring 제외) 단일 `return <이름>` 뿐 — 미러링 인터페이스 구현.

    duck-typed 전략(RuleBackend.compose→return base_text)이 다른 백엔드 시그니처를
    맞추느라 나머지 인자를 구조적으로 못 쓰는 정상 패턴. 실제 팬텀 결함(다중행 본문에서
    인자를 잊는 것)과 구분된다 — 한 줄 패스스루는 미사용이 곧 그 함수의 본질이다.
    """
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return (
        len(body) == 1 and isinstance(body[0], ast.Return) and isinstance(body[0].value, ast.Name)
    )


def _param_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    a = node.args
    names: list[str] = []
    for arg in (*a.posonlyargs, *a.args, *a.kwonlyargs):
        names.append(arg.arg)
    return names


def _names_used_in_body(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """본문(중첩 함수·컴프리헨션·f-string 포함) 전체에서 참조되는 이름(over-approx —
    하드 게이트라 오탐을 줄이는 방향으로 Load/Store 모두, 중첩 스코프도 사용으로 계산)."""
    used: set[str] = set()
    for stmt in node.body:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Name):
                used.add(sub.id)
    return used


def _scan_tree(tree: ast.AST, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    # 중첩 함수명 경로(outer.inner) 부여
    stack: list[str] = []

    class _V(ast.NodeVisitor):
        def _visit_func(self, node):
            if _decorator_names(node) & _SKIP_DECORATORS:
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()
                return
            if not _is_stub_body(node.body) and not _is_trivial_passthrough(node):
                used = _names_used_in_body(node)
                qual = ".".join([*stack, node.name])
                for p in _param_names(node):
                    if p in _SKIP_PARAM_NAMES or p.startswith("_"):
                        continue
                    if p not in used:
                        findings.append(Finding(rel, node.lineno, qual, p))
            stack.append(node.name)
            self.generic_visit(node)
            stack.pop()

        visit_FunctionDef = _visit_func
        visit_AsyncFunctionDef = _visit_func

    _V().visit(tree)
    return findings


def scan_paths(paths: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    files: list[Path] = []
    for p in paths:
        pp = (ROOT / p) if not Path(p).is_absolute() else Path(p)
        if pp.is_dir():
            files.extend(sorted(pp.rglob("*.py")))
        elif pp.suffix == ".py":
            files.append(pp)
    for f in files:
        rel = f.relative_to(ROOT).as_posix()
        if _EXCLUDE_SEGMENTS & set(f.parts) or any(s in rel for s in _EXCLUDE_SUBPATHS):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError:
            continue
        findings.extend(_scan_tree(tree, rel))
    return sorted(findings, key=lambda x: (x.path, x.lineno, x.param))


def load_allowlist(path: Path) -> dict[str, str]:
    """key(path::func::param) -> 사유. 각 항목은 '#' 뒤 사유 필수(빈 사유는 미등재 취급)."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("##"):
            continue
        key, _, reason = line.partition("#")
        key = key.strip()
        reason = reason.strip()
        if key and reason:
            out[key] = reason
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="dead-param 정적 스캐너(C2)")
    ap.add_argument("paths", nargs="*", default=["sajugen", "scripts"])
    ap.add_argument("--allowlist", default="tests/deadparam_allowlist.txt")
    args = ap.parse_args(argv)
    findings = scan_paths(args.paths or ["sajugen", "scripts"])
    allow = load_allowlist(ROOT / args.allowlist)
    unresolved = [f for f in findings if f.key() not in allow]
    for f in findings:
        tag = "ALLOW" if f.key() in allow else "DEAD "
        print(f"{tag} {f.path}:{f.lineno} {f.func}({f.param})")
    print(
        f"\n총 {len(findings)}건 · allowlist {len(findings) - len(unresolved)} · 미해결 {len(unresolved)}"
    )
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
