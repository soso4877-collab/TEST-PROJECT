# -*- coding: utf-8 -*-
"""자미두수 동등성 대조 — iztro_py(런타임 엔진) ↔ iztro(JS 원본, 권위 레퍼런스).

docs/03 §3: iztro_py 가 iztro JS 를 충실히 포팅했는지 100건 명반 전수 대조.
대조 축(zh-CN 정규화):
  [구조-핵심] 궁 지지/천간, 신궁, 12궁 성요 배치(major/minor/adj), 사화, 명/신궁 지지, 오행국.
    → 절대규칙 9의 '12궁 영역 서술'을 떠받치는 층. 불일치 0 이어야 함(포팅 충실도).
  [밝기] 성요 밝기(廟旺得利平陷). iztro 버전별 밝기표가 달라 차이가 날 수 있음(유파/판본 영역).
    → 자미 밝기는 강약 수식어(서술용)일 뿐 길흉 판정 근거 아님. 차이는 골든(known-diff)로 기록.

사이드카: sajugen/tools/iztro-bridge (iztro JS, node). 테스트 전용·런타임 비의존.
실행: ./.venv/Scripts/python.exe -m scripts.verify_ziwei_parity
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import iztro_py  # noqa: E402

_BRIDGE = Path(__file__).resolve().parents[1] / "sajugen" / "tools" / "iztro-bridge"
_N = 100

# 브릿지 소스(추적 코드가 정의 → 재생성 가능). 사이드카는 sajugen/tools/(비추적)에 위치.
_IZTRO_VERSION = "2.5.3"
_PACKAGE_JSON = (
    '{\n  "name": "sajugen-iztro-bridge",\n  "version": "0.1.0",\n  "private": true,\n'
    '  "description": "iztro(JS 원본) 사이드카 — iztro_py 동등성 대조 전용(테스트)",\n'
    '  "dependencies": { "iztro": "' + _IZTRO_VERSION + '" }\n}\n'
)
_BRIDGE_JS = r"""// iztro(JS 원본) 동등성 대조 브릿지 — stdin JSON 배열 → stdout JSON 배열(zh-CN 정규화).
// 자동 생성: scripts/verify_ziwei_parity.py. 수정은 그쪽 _BRIDGE_JS 에서.
const { astro } = require('iztro');
function norm(a) {
  return {
    soul: a.soul, body: a.body, fiveElementsClass: a.fiveElementsClass,
    soulBranch: a.earthlyBranchOfSoulPalace, bodyBranch: a.earthlyBranchOfBodyPalace,
    palaces: a.palaces.map(p => ({
      index: p.index, name: p.name, branch: p.earthlyBranch, stem: p.heavenlyStem,
      isBody: !!p.isBodyPalace,
      major: p.majorStars.map(s => [s.name, s.brightness || '', s.mutagen || '']),
      minor: p.minorStars.map(s => [s.name, s.brightness || '', s.mutagen || '']),
      adj: p.adjectiveStars.map(s => s.name),
    })),
  };
}
let buf = '';
process.stdin.on('data', d => buf += d);
process.stdin.on('end', () => {
  const cases = JSON.parse(buf);
  process.stdout.write(JSON.stringify(cases.map(c =>
    norm(astro.bySolar(c.date, c.timeIndex, c.gender, c.fixLeap, 'zh-CN')))));
});
"""


def ensure_bridge() -> None:
    """브릿지 소스(package.json/bridge.js)를 사이드카 디렉토리에 기록(없으면 생성)."""
    _BRIDGE.mkdir(parents=True, exist_ok=True)
    (_BRIDGE / "package.json").write_text(_PACKAGE_JSON, encoding="utf-8")
    (_BRIDGE / "bridge.js").write_text(_BRIDGE_JS, encoding="utf-8")


def _cases(n: int) -> list[dict]:
    out = []
    for i in range(n):
        y = 1940 + (i * 7 % 90)  # 1940~2029
        mo = 1 + (i * 3 % 12)
        da = 1 + (i * 5 % 27)
        ti = i % 13
        g = "男" if i % 2 == 0 else "女"
        out.append(
            {"date": f"{y}-{mo:02d}-{da:02d}", "timeIndex": ti, "gender": g, "fixLeap": True}
        )
    return out


def _run_js(cases: list[dict]) -> list[dict]:
    if not (_BRIDGE / "bridge.js").exists():
        ensure_bridge()
    if not (_BRIDGE / "node_modules" / "iztro").exists():
        raise RuntimeError(f"iztro JS 미설치 — `cd {_BRIDGE} && npm install` 후 재실행")
    r = subprocess.run(
        ["node", str(_BRIDGE / "bridge.js")],
        input=json.dumps(cases),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"iztro JS 브릿지 실패: {r.stderr[:300]}")
    return json.loads(r.stdout)


def _py_norm(c: dict) -> dict:
    a = iztro_py.by_solar(c["date"], c["timeIndex"], c["gender"], c["fixLeap"], "zh-CN")

    def st(lst):
        return [[s.translate_name(), s.brightness or "", s.mutagen or ""] for s in lst]

    return {
        "fiveElementsClass": str(a.five_elements_class),
        "soulBranch": a.get_soul_palace().translate_earthly_branch(),
        "bodyBranch": a.get_body_palace().translate_earthly_branch(),
        "palaces": [
            {
                "branch": p.translate_earthly_branch(),
                "stem": p.translate_heavenly_stem(),
                "isBody": bool(p.is_body_palace),
                "major": st(p.major_stars),
                "minor": st(p.minor_stars),
                "adj": [s.translate_name() for s in p.adjective_stars],
            }
            for p in a.palaces
        ],
    }


def compare(n: int = _N) -> dict:
    cases = _cases(n)
    js = _run_js(cases)
    struct = {
        "branch_stem": 0,
        "isBody": 0,
        "placement": 0,
        "sihua": 0,
        "five": 0,
        "soulbody_branch": 0,
    }
    bright = 0
    bright_samples: list = []
    struct_samples: list = []

    def names(d, k):
        return sorted(x[0] for x in d[k])

    def sih(d, k):
        return sorted((x[0], x[2]) for x in d[k])

    for c, j in zip(cases, js):
        p = _py_norm(c)
        if p["fiveElementsClass"] != j["fiveElementsClass"]:
            struct["five"] += 1
        if p["soulBranch"] != j["soulBranch"] or p["bodyBranch"] != j["bodyBranch"]:
            struct["soulbody_branch"] += 1
        for pp, jp in zip(p["palaces"], j["palaces"]):
            if pp["branch"] != jp["branch"] or pp["stem"] != jp["stem"]:
                struct["branch_stem"] += 1
                if len(struct_samples) < 6:
                    struct_samples.append(
                        (c["date"], (pp["branch"], pp["stem"]), (jp["branch"], jp["stem"]))
                    )
            if pp["isBody"] != jp["isBody"]:
                struct["isBody"] += 1
            for k in ("major", "minor"):
                if names(pp, k) != names(jp, k):
                    struct["placement"] += 1
            if sorted(pp["adj"]) != sorted(jp["adj"]):
                struct["placement"] += 1
            for k in ("major", "minor"):
                if sih(pp, k) != sih(jp, k):
                    struct["sihua"] += 1
            for k in ("major", "minor"):
                pm = {x[0]: x[1] for x in pp[k]}
                jm = {x[0]: x[1] for x in jp[k]}
                diffs = {x: (pm[x], jm.get(x)) for x in pm if jm.get(x) != pm[x]}
                if diffs:
                    bright += 1
                    if len(bright_samples) < 8:
                        bright_samples.append((c["date"], diffs))

    return {
        "n": n,
        "struct": struct,
        "struct_total": sum(struct.values()),
        "brightness_palace_mismatches": bright,
        "bright_samples": bright_samples,
        "struct_samples": struct_samples,
    }


def main() -> int:
    res = compare(_N)
    print(f"=== 자미 동등성 {res['n']}건 × 12궁 (iztro_py 0.3.4 ↔ iztro JS) ===")
    print("[구조-핵심] (불일치 0 이어야 함)")
    for k, v in res["struct"].items():
        print(f"   {k:18s}: {v}")
    print(f"   합계: {res['struct_total']}")
    if res["struct_samples"]:
        print("   표본:", res["struct_samples"])
    print(
        f"\n[밝기] 차이 궁수: {res['brightness_palace_mismatches']} (유파/판본 영역 — known-diff)"
    )
    for s in res["bright_samples"]:
        print("   ", s)

    # 밝기 차이 골든 기록(문서화)
    out = Path(__file__).resolve().parents[1] / "data" / "ziwei_brightness_divergence.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "_note": "iztro_py 0.3.4 ↔ iztro JS 밝기표 차이(known-diff). 구조(배치·사화·명신궁·오행국)는 동일. "
                "자미 밝기는 영역 서술용 강약 수식어로, 길흉 판정 근거 아님(절대규칙9).",
                "struct_mismatch_total": res["struct_total"],
                "brightness_palace_mismatches": res["brightness_palace_mismatches"],
                "samples": res["bright_samples"],
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"\n밝기 차이 기록: {out}")
    ok = res["struct_total"] == 0
    print("\n=> " + ("구조 동등성 통과(불일치 0)" if ok else "구조 불일치 발견 — 조사 필요"))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
