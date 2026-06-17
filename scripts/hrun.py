# -*- coding: utf-8 -*-
"""하네스 단일 진입(orchestrator) — preflight + pytest + PDF 검증 + 요약 리포트.

강제 안전장치(문서가 아니라 이 코드):
- git 변경/커밋/push/deploy 절대 안 함.
- PDF 재생성/LLM 호출은 3중 잠금: --regen AND --allow-llm AND env SAJUGEN_HARNESS_ALLOW_REGEN=1.
  셋 중 하나라도 없으면 재생성/LLM 미실행 → 기존 PDF만 검증(없으면 missing_pdf).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import hpreflight  # noqa: E402
import hsummary  # noqa: E402
import hverify_pdf  # noqa: E402


def _load_common() -> dict:
    import yaml

    p = ROOT / "harness" / "profiles" / "common.yml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {} if p.is_file() else {}


def _run_pytest(python: str) -> dict:
    try:
        r = subprocess.run(
            [python, "-m", "pytest", "tests/", "-q"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )
        tail = (r.stdout or "")[-2000:]
        m = re.search(r"(\d+) passed", tail)
        return {
            "returncode": r.returncode,
            "passed": int(m.group(1)) if m else None,
            "skipped": None,
            "tail": tail.splitlines()[-3:],
        }
    except Exception as e:  # noqa: BLE001
        return {"returncode": -1, "passed": None, "error": type(e).__name__}


def _regen_allowed(args) -> bool:
    # 3중 잠금 — 전부 충족해야 재생성/LLM 시도
    return bool(
        args.regen and args.allow_llm and os.environ.get("SAJUGEN_HARNESS_ALLOW_REGEN") == "1"
    )


def _regen_pdf(profile: dict, python: str) -> dict:
    """승인된 경우에만 호출(3중 잠금 통과 후). 기존 cli/gunghap 으로 재생성."""
    out_name = Path(profile["pdf"]).name
    if profile["type"] == "personal":
        cmd = [
            python,
            "-m",
            "sajugen.cli",
            "--birth",
            profile["birth"],
            "--gender",
            str(profile.get("gender", "남")),
            "--name",
            profile["name"],
            "--horoscope",
            str(profile.get("horoscope") or f"{profile.get('ref_year', 2026)}-06-01"),
            "--llm",
            "--out",
            out_name,
        ]
    else:
        cmd = [python, "-m", "sajugen.gunghap"]
        for p in profile["people"]:
            b = p["birth"].split()
            t = b[1] if len(b) > 1 else "12:00"
            cmd += ["--person", f"{p['name']},{b[0]},{t},{p.get('gender', '남')}"]
        cmd += ["--ref-year", str(profile.get("ref_year", 2026)), "--out", out_name]
    r = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
    )
    return {"returncode": r.returncode}


def run(profiles: list[str], args) -> dict:
    common = _load_common()
    python = common.get("python", "./.venv/Scripts/python.exe")

    pre = hpreflight.run()
    pytest_res = (
        {"returncode": 0, "passed": None, "skipped": "pytest 생략(--no-tests)"}
        if args.no_tests
        else _run_pytest(python)
    )

    regen_ok = _regen_allowed(args)
    pdf_results = []
    for prof_path in profiles:
        prof = hverify_pdf.load_profile(prof_path)
        if regen_ok:
            _regen_pdf(prof, python)  # 승인 시에만(3중 잠금)
        # 재생성 여부와 무관하게 항상 '읽기 전용 검증'
        res = hverify_pdf.verify_profile(prof)
        res["regen"] = "done" if regen_ok else "skipped(미승인)"
        pdf_results.append(res)

    summary = hsummary.build_summary(pre, pytest_res, pdf_results)
    summary["regen_allowed"] = regen_ok
    stamp = args.stamp or time.strftime("%Y%m%d-%H%M%S")
    paths = hsummary.write_report(
        summary, report_dir=common.get("report_dir", "handoff/reports"), stamp=stamp
    )
    summary["report"] = paths
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="sajugen 하네스 단일 진입(검증만, 커밋·push 안 함)")
    ap.add_argument("--profile", action="append", default=[], help="프로파일 YAML(반복 가능)")
    ap.add_argument("--no-tests", action="store_true", help="pytest 생략(빠른 검증)")
    ap.add_argument("--regen", action="store_true", help="(3중 잠금 1/3) PDF 재생성 시도")
    ap.add_argument("--allow-llm", action="store_true", help="(3중 잠금 2/3) LLM 호출 허용")
    ap.add_argument("--stamp", default=None, help="리포트 스탬프(테스트 재현용)")
    a = ap.parse_args(argv)
    s = run(a.profile, a)
    pf = s["preflight"]
    print(
        f"preflight_ok={pf['preflight_ok']} pytest_passed={s['pytest'].get('passed')} "
        f"regen_allowed={s['regen_allowed']} all_gates_pass={s['all_gates_pass']}"
    )
    for p in s["pdfs"]:
        print(f"  [{p['type']}] {p['pdf']} status={p['status']} gate_pass={p.get('gate_pass')}")
    print(f"리포트: {s['report']['md']}")
    ok = (
        pf["preflight_ok"]
        and (s["pytest"].get("returncode") == 0)
        and (s["all_gates_pass"] in (True, None))
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
