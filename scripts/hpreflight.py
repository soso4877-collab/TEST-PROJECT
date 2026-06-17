# -*- coding: utf-8 -*-
"""하네스 preflight — 읽기 전용 환경 점검(sajugen 검증 하네스).

오직 점검만 한다: git branch/status/diffstat, calc/ diff 없음, .env·render/out 미추적,
local profile·reports ignore, staged+working diff 내 API key 패턴 존재 여부.
절대 하지 않는다: secret 값/.env 내용 출력, 파일 수정, git add/commit/push.
secrets 결과는 값 없이 {path, rule, line_no, count} 만 보고(redacted).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# API key 패턴 — '존재 여부'만 본다. 값은 절대 출력하지 않는다.
_SECRET_RULES = [
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    (
        "env_assign_key",
        re.compile(r"(?i)(api[_-]?key|secret|token)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    ),
    ("long_hex", re.compile(r"\b[0-9a-fA-F]{40,}\b")),
]


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        ).stdout
    except Exception as e:  # noqa: BLE001
        return f"__git_error__:{type(e).__name__}"


def _tracked(path: str) -> bool:
    out = _git("ls-files", path).strip()
    return bool(out) and not out.startswith("__git_error__")


def _is_ignored(path: str) -> bool:
    # git check-ignore: 종료코드 0 = ignored. 값 노출 없음.
    try:
        r = subprocess.run(
            ["git", "check-ignore", path], cwd=ROOT, capture_output=True, text=True, timeout=15
        )
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _secret_scan() -> list[dict]:
    """staged+working diff 텍스트에서 키 패턴 '존재 여부'만(값 미출력)."""
    diff = _git("diff", "HEAD") + "\n" + _git("diff", "--cached")
    hits: list[dict] = []
    cur_file = "?"
    for ln in diff.splitlines():
        if ln.startswith("+++ b/"):
            cur_file = ln[6:]
            continue
        if not ln.startswith("+") or ln.startswith("+++"):
            continue
        for rule, rx in _SECRET_RULES:
            if rx.search(ln):
                hits.append({"path": cur_file, "rule": rule, "redacted_preview": "[REDACTED]"})
                break
    # 중복 (path,rule) 합산
    agg: dict[tuple, int] = {}
    for h in hits:
        agg[(h["path"], h["rule"])] = agg.get((h["path"], h["rule"]), 0) + 1
    return [
        {"path": p, "rule": r, "count": c, "redacted_preview": "[REDACTED]"}
        for (p, r), c in agg.items()
    ]


def run() -> dict:
    branch = _git("rev-parse", "--abbrev-ref", "HEAD").strip()
    status = [ln for ln in _git("status", "--short").splitlines() if ln.strip()]
    diffstat = _git("diff", "--stat", "HEAD").strip()
    calc_diff = _git("diff", "--stat", "HEAD", "--", "sajugen/calc/").strip()
    secrets = _secret_scan()
    r = {
        "branch": branch,
        "status_short_count": len(status),
        "status_short": status[:50],
        "diffstat_present": bool(diffstat),
        "calc_diff_empty": (calc_diff == ""),
        "env_tracked": _tracked(".env"),
        "render_out_tracked": _tracked("sajugen/render/out"),
        "local_profiles_ignored": _is_ignored("harness/profiles/local/x.yml"),
        "reports_ignored": _is_ignored("harness/profiles/local/../../../handoff/reports/x.json")
        or _is_ignored("handoff/reports/x.json"),
        "secret_hits": secrets,  # 값 없음(redacted), count만
        "secret_hit_count": sum(h["count"] for h in secrets),
    }
    # preflight 통과 조건: calc clean + .env/render/out 미추적 + local/reports ignore + secrets 0
    r["preflight_ok"] = bool(
        r["calc_diff_empty"]
        and not r["env_tracked"]
        and not r["render_out_tracked"]
        and r["local_profiles_ignored"]
        and r["reports_ignored"]
        and r["secret_hit_count"] == 0
    )
    return r


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="sajugen 하네스 preflight(읽기 전용)")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    a = ap.parse_args(argv)
    r = run()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"branch={r['branch']} preflight_ok={r['preflight_ok']}")
        print(
            f"  calc_diff_empty={r['calc_diff_empty']} env_tracked={r['env_tracked']} "
            f"render_out_tracked={r['render_out_tracked']}"
        )
        print(
            f"  local_profiles_ignored={r['local_profiles_ignored']} reports_ignored={r['reports_ignored']}"
        )
        print(f"  secret_hit_count={r['secret_hit_count']} (값 미출력)")
        print(f"  status_short_count={r['status_short_count']}")
    return 0 if r["preflight_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
