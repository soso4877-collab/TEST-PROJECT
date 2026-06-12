# -*- coding: utf-8 -*-
"""배경 자산 생성 — hanji.svg → hanji_bg.jpg (결정론·재생성 가능).

Chromium으로 SVG(feTurbulence)를 래스터화해 풀블리드 한지 배경(1240x1754,
A4 150dpi)을 만든다. 낙관은 여기 굽지 않는다 — 브랜드 가변(다계정, 2026-06-12)
이라 pdf.py 언더레이 단계에서 PyMuPDF로 런타임에 그린다.

실행: ./.venv/Scripts/python.exe -m sajugen.render.assets.make_assets
"""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

_DIR = os.path.dirname(__file__)
W, H = 1240, 1754  # A4 150dpi


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
