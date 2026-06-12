# -*- coding: utf-8 -*-
"""배경 자산 생성 — hanji.svg + seal.svg → hanji_bg.jpg (결정론·재생성 가능).

Chromium으로 SVG(feTurbulence)를 래스터화하고 낙관을 우하단에 합성해
한 장의 풀블리드 배경(1240x1754, A4 150dpi)을 만든다. PDF에는 PyMuPDF
언더레이로 전 페이지 1회 임베드(XObject 재사용)된다.

실행: ./.venv/Scripts/python.exe -m sajugen.render.assets.make_assets
"""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

_DIR = os.path.dirname(__file__)
_FONT = os.path.join(_DIR, "..", "fonts", "NanumBrushScript-Regular.ttf")
W, H = 1240, 1754  # A4 150dpi
# 낙관 배치(우하단) — page rect 기준 비율은 pdf.py와 무관(이미지에 합성)
SEAL_W, SEAL_H = 66, 176
SEAL_X, SEAL_Y = W - SEAL_W - 56, H - SEAL_H - 78


def build(out_name: str = "hanji_bg.jpg") -> str:
    font_url = "file:///" + os.path.abspath(_FONT).replace(os.sep, "/")
    hanji_url = "file:///" + os.path.join(_DIR, "hanji.svg").replace(os.sep, "/")
    seal_url = "file:///" + os.path.join(_DIR, "seal.svg").replace(os.sep, "/")
    html = f"""<!doctype html><html><head><style>
      @font-face{{font-family:'SealFont';src:url('{font_url}') format('truetype')}}
      *{{margin:0;padding:0}}
      body{{width:{W}px;height:{H}px;overflow:hidden}}
      img.bg{{position:absolute;left:0;top:0;width:{W}px;height:{H}px}}
      img.seal{{position:absolute;left:{SEAL_X}px;top:{SEAL_Y}px;
               width:{SEAL_W}px;height:{SEAL_H}px;opacity:.82}}
      /* seal.svg 의 font-family:SealFont 는 <img> 로는 폰트가 안 먹으므로
         object 로 임베드하지 않고, 동일 마크업을 인라인 SVG 로 직접 둔다. */
      svg.seal{{position:absolute;left:{SEAL_X}px;top:{SEAL_Y}px;opacity:.82}}
    </style></head><body>
      <img class="bg" src="{hanji_url}">
      <svg class="seal" xmlns="http://www.w3.org/2000/svg" width="{SEAL_W}" height="{SEAL_H}"
           viewBox="0 0 120 320">
        <rect x="6" y="6" width="108" height="308" fill="none" stroke="#a23b2c"
              stroke-width="3" rx="2"/>
        <rect x="14" y="14" width="92" height="292" fill="none" stroke="#a23b2c"
              stroke-width="1" rx="1"/>
        <text x="60" y="82" font-family="SealFont" font-size="58" fill="#a23b2c"
              text-anchor="middle">사</text>
        <text x="60" y="152" font-family="SealFont" font-size="58" fill="#a23b2c"
              text-anchor="middle">주</text>
        <text x="60" y="222" font-family="SealFont" font-size="58" fill="#a23b2c"
              text-anchor="middle">명</text>
        <text x="60" y="292" font-family="SealFont" font-size="58" fill="#a23b2c"
              text-anchor="middle">리</text>
      </svg>
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
