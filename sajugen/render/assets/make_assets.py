# -*- coding: utf-8 -*-
"""배경·낙관 자산 생성 — Chromium 래스터화(결정론·재생성 가능).

- hanji.svg → hanji_bg.jpg: 풀블리드 한지 배경(1240x1754, A4 150dpi).
- build_seal(text) → seal_cache/seal_<text>.png: 브랜드별 세로 낙관(투명 PNG).
  PyMuPDF insert_text 로 글자를 써넣으면 일부 뷰어에서 글리프가 깨진다
  (운영자 실증 2026-06-12) — 텍스트 임베드는 Chromium 경로만 신뢰하고,
  낙관은 이미지로 삽입한다(전 뷰어 동일 렌더).

실행: ./.venv/Scripts/python.exe -m sajugen.render.assets.make_assets
"""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

_DIR = os.path.dirname(__file__)
_FONT_BOLD = os.path.join(_DIR, "..", "fonts", "SourceHanSerifKR-Bold.otf")  # 본명조 Bold(낙관)
_SEAL_DIR = os.path.join(_DIR, "seal_cache")
W, H = 1240, 1754  # A4 150dpi

# 낙관 PNG 스펙 — PDF에서 ~32pt 폭으로 축소 배치. 4x = 배치 기준 약 288dpi
# (인쇄 충분). PyMuPDF가 알파 PNG를 무압축 RGB+SMask로 저장하므로(실측 8x=933KB)
# 스케일을 키우면 PDF가 그대로 커진다 — 4x 고정.
_SEAL_SCALE = 4
_SEAL_FS = 17  # pt 기준 글자 크기(픽셀 환산은 scale 곱)


def seal_png_path(seal_text: str) -> str:
    safe = "".join(ch for ch in seal_text.strip() if ch.isalnum())[:8] or "default"
    return os.path.join(_SEAL_DIR, f"seal_{safe}.png")


def build_seal(seal_text: str) -> str:
    """세로 낙관 투명 PNG 생성(캐시) — 이중 테두리 + 명조 Bold 글자, 인주색."""
    out_path = seal_png_path(seal_text)
    if os.path.isfile(out_path):
        return out_path
    os.makedirs(_SEAL_DIR, exist_ok=True)
    chars = list(seal_text.strip())[:4] or list("사주명리")
    s = _SEAL_SCALE
    fs = _SEAL_FS * s
    pad_x, pad_top = 7.5 * s, 10 * s
    step = fs + 6.5 * s
    w = int(fs + pad_x * 2)
    h = int(pad_top * 2 + step * len(chars))
    font_url = "file:///" + os.path.abspath(_FONT_BOLD).replace(os.sep, "/")
    rows = "".join(
        f'<div class="ch" style="top:{pad_top + step * i:.0f}px">{ch}</div>'
        for i, ch in enumerate(chars)
    )
    html = f"""<!doctype html><html><head><style>
      @font-face{{font-family:'SealFont';src:url('{font_url}') format('truetype')}}
      *{{margin:0;padding:0}}
      body{{width:{w}px;height:{h}px;background:transparent;position:relative}}
      .bo{{position:absolute;left:{1.5 * s}px;top:{1.5 * s}px;right:{1.5 * s}px;
          bottom:{1.5 * s}px;border:{1.1 * s}px solid #a23b2c;opacity:.92}}
      .bi{{position:absolute;left:{4.2 * s}px;top:{4.2 * s}px;right:{4.2 * s}px;
          bottom:{4.2 * s}px;border:{0.45 * s}px solid #a23b2c;opacity:.92}}
      .ch{{position:absolute;left:0;width:{w}px;text-align:center;
          font-family:'SealFont';font-weight:700;font-size:{fs}px;line-height:{step}px;
          color:#a23b2c;opacity:.92}}
    </style></head><body><div class="bo"></div><div class="bi"></div>{rows}</body></html>"""
    stage = os.path.join(_SEAL_DIR, "_seal_stage.html")
    with open(stage, "w", encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto("file:///" + stage.replace(os.sep, "/"))
        pg.evaluate("document.fonts.ready")
        pg.screenshot(
            path=out_path, omit_background=True, clip={"x": 0, "y": 0, "width": w, "height": h}
        )
        b.close()
    os.remove(stage)
    return out_path


def build(out_name: str = "hanji_bg.jpg") -> str:
    hanji_url = "file:///" + os.path.join(_DIR, "hanji.svg").replace(os.sep, "/")
    html = f"""<!doctype html><html><head><style>
      *{{margin:0;padding:0}}
      body{{width:{W}px;height:{H}px;overflow:hidden}}
      img.bg{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}
    </style></head><body>
      <img class="bg" src="{hanji_url}">
    </body></html>"""
    html_path = os.path.join(_DIR, "_assets_stage.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    out_path = os.path.join(_DIR, out_name)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto("file:///" + html_path.replace(os.sep, "/"))
        pg.evaluate("document.fonts.ready")
        pg.screenshot(
            path=out_path, type="jpeg", quality=82, clip={"x": 0, "y": 0, "width": W, "height": H}
        )
        b.close()
    os.remove(html_path)
    return out_path


if __name__ == "__main__":
    p = build()
    print(p, os.path.getsize(p) // 1024, "KB")
