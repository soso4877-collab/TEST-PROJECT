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
import hprofile_check  # noqa: E402
import hstate  # noqa: E402
import hsummary  # noqa: E402
import hverify_pdf  # noqa: E402

from sajugen.refdate import default_ref_date_iso  # noqa: E402
from sajugen.render.verify import GATE_KEYS  # noqa: E402  게이트 키 SSOT(수동 목록 복제 금지)


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
        passed_match = re.search(r"(\d+)\s+passed\b", tail)
        skipped_match = re.search(r"(\d+)\s+skipped\b", tail)
        return {
            "returncode": r.returncode,
            "passed": int(passed_match.group(1)) if passed_match else None,
            # pytest는 skip이 0이면 summary 토큰 자체를 생략한다. passed 요약을 읽은 경우
            # 부재를 0으로 확정하고, 출력 형식 자체를 못 읽은 경우에만 None으로 둔다.
            "skipped": (
                int(skipped_match.group(1))
                if skipped_match
                else 0
                if passed_match
                else None
            ),
            "tail": tail.splitlines()[-3:],
        }
    except Exception as e:  # noqa: BLE001
        return {"returncode": -1, "passed": None, "error": type(e).__name__}


def _regen_allowed(args) -> bool:
    # 3중 잠금 — 전부 충족해야 재생성/LLM 시도
    return bool(
        args.regen and args.allow_llm and os.environ.get("SAJUGEN_HARNESS_ALLOW_REGEN") == "1"
    )


def _regen_command(profile: dict, python: str) -> list[str]:
    """재생성용 argv만 결정론적으로 구성한다(API/PDF 실행 없음).

    모듈 선택 프로파일은 hverify와 같은 원자 계약을 통과한 경우에만 제품 CLI의 반복
    ``--module`` 인자로 정규 순서 전달한다. 레거시는 플래그를 넣지 않아 기존 기본값을
    유지한다.
    """
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
        if profile.get("brand"):
            cmd += ["--brand", str(profile["brand"])]
        if profile.get("product"):
            cmd += ["--product", str(profile["product"])]
        if profile.get("concern"):
            cmd += ["--concern", str(profile["concern"])]
    elif profile["type"] in ("integrated", "integrated_full"):
        cmd = [python, "-m", "sajugen.integrated", "--llm"]
        for p in profile["people"]:
            b = p["birth"].split()
            t = b[1] if len(b) > 1 else ""
            cmd += ["--person", f"{p['name']},{b[0]},{t},{p.get('gender', '남')}"]
        cmd += ["--ref-year", str(profile.get("ref_year", 2026)), "--out", out_name]
        # Phase 0(2026-07-06): 운영자 대면 regen 이라 프로파일 ref_date 부재 시 '오늘'을
        # 명시 주입(관측성 — CLI 내부 기본에 맡기지 않고 실행 명령에 날짜를 기록한다).
        # 프로파일에 ref_date 를 고정하면 재렌더가 그 날짜로 결정론 유지(픽스처 권장).
        cmd += ["--ref-date", str(profile.get("ref_date") or default_ref_date_iso())]
        if profile.get("receiver"):
            cmd += ["--receiver", str(profile["receiver"])]
        if profile.get("brand"):
            cmd += ["--brand", str(profile["brand"])]
        if profile.get("situation") or profile.get("concern"):
            cmd += ["--situation", str(profile.get("situation") or profile.get("concern"))]
        module_contract = hprofile_check.module_contract(profile)
        if not module_contract["ok"]:
            errors = ",".join(module_contract["errors"])
            raise ValueError(f"invalid module contract: {errors}")
        if module_contract["explicit"]:
            for module_id in module_contract["selected_modules"]:
                cmd += ["--module", module_id]
    else:
        cmd = [python, "-m", "sajugen.gunghap", "--llm"]
        for p in profile["people"]:
            b = p["birth"].split()
            t = b[1] if len(b) > 1 else ""
            cmd += ["--person", f"{p['name']},{b[0]},{t},{p.get('gender', '남')}"]
        cmd += ["--ref-year", str(profile.get("ref_year", 2026)), "--out", out_name]
        # Phase 0(2026-07-06): integrated 분기와 동일 — 부재 시 '오늘' 명시 주입(관측성).
        cmd += ["--ref-date", str(profile.get("ref_date") or default_ref_date_iso())]
        if profile.get("brand"):
            cmd += ["--brand", str(profile["brand"])]
        if profile.get("mode"):
            cmd += ["--mode", str(profile["mode"])]
        if profile.get("situation") or profile.get("concern"):
            cmd += ["--situation", str(profile.get("situation") or profile.get("concern"))]
    return cmd


def _regen_pdf(profile: dict, python: str) -> dict:
    """승인된 경우에만 호출(3중 잠금 통과 후). 기존 cli/gunghap 으로 재생성."""
    cmd = _regen_command(profile, python)
    r = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=1800,
        # 자식 프로세스 stdout/stderr 를 UTF-8 로 강제(Windows 기본 cp949 에서 진단 print 의
        # 특수문자(em dash 등)로 서브프로세스가 UnicodeEncodeError 크래시하던 것 차단, 2026-07-02).
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    # 실패 시 원인 추적용 — 그동안 returncode 만 반환해 CLI 에러가 가려졌다(관측 갭). stderr tail 보존.
    # getattr: 테스트가 subprocess.run 을 stdout/stderr 없는 mock 으로 대체해도 안전.
    tail = ((getattr(r, "stderr", "") or "") + (getattr(r, "stdout", "") or ""))[-3000:]
    # 사용량 관측(2026-07-05): 빌드 CLI 가 남긴 "LLM usage:" 줄을 파싱해 summary 로 올린다
    # (PII 0 — 토큰 수·호출 수만). 줄이 없으면 None(구 빌드/무LLM).
    from sajugen.content import llm_usage

    stdout = getattr(r, "stdout", "") or ""
    # 구 3합계 줄은 그대로 지원하고, 새 detail 줄이 있으면 cache/event 필드만 병합한다.
    usage = llm_usage.parse_output(stdout)
    # 챕터별 폴백 관측(P0 2026-07-05): cli 의 "chapters: polished=... fallback=..." 줄 파싱
    # (QI-2026-07-05-03 — consult 골격 폴백이 summary 에서 안 보이던 갭). 챕터 id 만이라 PII 0.
    fallback_chapters = None
    m = re.search(r"chapters: polished=\S* fallback=(\S+)", stdout)
    if m:
        fallback_chapters = [] if m.group(1) == "-" else m.group(1).split(",")
    return {
        "returncode": r.returncode,
        "stderr_tail": tail,
        "llm_usage": usage,
        "fallback_chapters": fallback_chapters,
    }


def _profile_concern(profile: dict) -> str | None:
    """고객 질문(고민) 정규화 — integrated/궁합 프로파일은 고민을 `situation` 필드로 담고
    personal 은 `concern` 필드로 담는다(integrated.py 의 concern=situation 매핑과 일치).
    hverify_pdf.verify_profile 은 `concern` 만 읽으므로, situation 을 concern 으로 정규화하지
    않으면 delivery_quality 질문축 검사가 조용히 no-op 된다(2026-07-01 P1 배선 갭)."""
    return profile.get("concern") or profile.get("situation")


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
    retry_blocked = False
    retry_reasons: list[str] = []
    pdf_rendered = False
    for prof_path in profiles:
        prof = hverify_pdf.load_profile(prof_path)
        # integrated/궁합 프로파일의 고민(situation)을 concern 으로 정규화 —
        # verify_profile 이 concern 만 읽어 질문축 검사가 no-op 되던 갭 차단(P1).
        prof["concern"] = _profile_concern(prof)
        module_contract = hprofile_check.module_contract(prof)
        regen_result = None
        if regen_ok and not module_contract["ok"]:
            # 잘못된 모듈 증거로 API/PDF 경로에 진입하지 않는다. verify_profile도 같은
            # 오류 코드를 반환해 summary에 차단 사유가 남는다.
            retry_blocked = True
            retry_reasons.append("invalid_module_contract")
            regen_result = {
                "returncode": None,
                "blocked": True,
                "block_reason": "invalid_module_contract",
            }
        elif regen_ok and not retry_blocked:
            regen_result = _regen_pdf(prof, python)  # 승인 시에만(3중 잠금)
            if regen_result.get("returncode") != 0:
                retry_blocked = True
                retry_reasons.append("pdf_regen_failed")
            else:
                pdf_rendered = True
        elif regen_ok and retry_blocked:
            regen_result = {"returncode": None, "blocked": True}
        # 재생성 여부와 무관하게 항상 '읽기 전용 검증'
        res = hverify_pdf.verify_profile(prof)
        if regen_result and regen_result.get("blocked"):
            res["regen"] = (
                "blocked_invalid_module_contract"
                if regen_result.get("block_reason") == "invalid_module_contract"
                else "blocked_after_failure"
            )
        elif regen_ok:
            # rc!=0 인데 "done" 으로 표기되던 관측 갭(2026-07-05 h153 실측: 빌드 하드 게이트
            # 실패가 summary 에서 done 으로 보임) — 실패는 실패로 드러낸다(fail-closed 관측).
            res["regen"] = "done" if (regen_result or {}).get("returncode") == 0 else "failed"
        else:
            res["regen"] = "skipped(미승인)"
        if regen_result is not None:
            res["regen_returncode"] = regen_result.get("returncode")
            if regen_result.get("llm_usage"):
                res["regen_llm_usage"] = regen_result["llm_usage"]  # 비용 관측(PII 0)
            if regen_result.get("fallback_chapters") is not None:
                res["regen_fallback_chapters"] = regen_result["fallback_chapters"]  # P0(PII 0)
            # 재생성 실패 시 CLI stderr tail 을 로컬 진단용으로 보존(PII 포함 가능 → gitignored,
            # 채팅/커밋 비출력). 그동안 원인이 가려지던 관측 갭 보강(2026-07-02).
            if regen_result.get("returncode") not in (0, None) and regen_result.get("stderr_tail"):
                res["regen_stderr_tail"] = regen_result["stderr_tail"]
        if res.get("status") != "verified" or not res.get("gate_pass"):
            retry_blocked = True
            retry_reasons.append(_retry_reason(res))
        if retry_blocked:
            res["retry_blocked"] = True
            res["retry_block_reason"] = retry_reasons[-1] if retry_reasons else "pdf_gate_failed"
        pdf_results.append(res)

    state_output = {
        "preflight_ok": pre.get("preflight_ok"),
        "pytest_returncode": pytest_res.get("returncode"),
        "pdfs": [
            {
                "type": p.get("type"),
                "status": p.get("status"),
                "gate_pass": p.get("gate_pass"),
                "regen": p.get("regen"),
                "retry_blocked": p.get("retry_blocked", False),
                "retry_block_reason": p.get("retry_block_reason"),
            }
            for p in pdf_results
        ],
        "retry_reasons": retry_reasons[:10],
    }
    final_status = (
        "BLOCKED"
        if retry_blocked
        else "FAILED"
        if (not pre.get("preflight_ok") or pytest_res.get("returncode") != 0)
        else "PASSED"
    )
    run_state = hstate.build_run_state(
        current_stage="COMPLETE",
        input_payload={
            "profiles": profiles,
            "regen": bool(args.regen),
            "allow_llm": bool(args.allow_llm),
            "no_tests": bool(args.no_tests),
        },
        output_payload=state_output,
        api_calls=0,
        pdf_rendered=pdf_rendered,
        retry_blocked=retry_blocked,
        final_status=final_status,
    )
    summary = hsummary.build_summary(pre, pytest_res, pdf_results)
    _overlay_retry_fields(summary, pdf_results)
    summary.update(run_state)
    summary["run_state"] = run_state
    summary["regen_allowed"] = regen_ok
    summary["retry_blocked"] = retry_blocked
    summary["retry_reasons"] = retry_reasons[:10]
    stamp = args.stamp or time.strftime("%Y%m%d-%H%M%S")
    paths = hsummary.write_report(
        summary, report_dir=common.get("report_dir", "handoff/reports"), stamp=stamp
    )
    report_dir = paths.get("dir")
    if not report_dir:
        json_path = Path(paths["json"]) if paths.get("json") else None
        if json_path and str(json_path.parent) not in ("", "."):
            report_dir = str(json_path.parent)
        else:
            report_dir = str(Path(common.get("report_dir", "handoff/reports")) / stamp)
    state_path = Path(report_dir) / "RUN_STATE.json"
    hstate.write_state(state_path, run_state)
    paths["run_state"] = str(state_path)
    summary["report"] = paths
    return summary


def _overlay_retry_fields(summary: dict, pdf_results: list[dict]) -> None:
    """Keep retry state in hrun output without changing hsummary's generic redaction."""
    for out, raw in zip(summary.get("pdfs") or [], pdf_results):
        if raw.get("retry_blocked"):
            out["retry_blocked"] = True
        if raw.get("retry_block_reason"):
            out["retry_block_reason"] = raw.get("retry_block_reason")


def _retry_reason(res: dict) -> str:
    if res.get("status") != "verified":
        return str(res.get("status") or "pdf_not_verified")
    if res.get("gate_pass"):
        return "none"
    # GATE_KEYS(verify SSOT) 순회 — 수동 목록이 layout_geometry_clean·daewoon_consistent·
    # 구조키(text/font/tag)를 누락해 단독 실패가 pdf_gate_failed 로 뭉개지던 갭(C4) 해소.
    for key in GATE_KEYS:
        if res.get(key) is False:
            return key
    return "pdf_gate_failed"


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
