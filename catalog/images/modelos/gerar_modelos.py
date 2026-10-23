"""Gera as 2 imagens modelo do #32 (caixa de remédio com receita / genérico). Texto vira contorno (Noto Sans Bold)."""
import pathlib, subprocess, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from PIL import Image

FONT = TTFont("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf")
GS, CMAP, UPM = FONT.getGlyphSet(), FONT.getBestCmap(), FONT["head"].unitsPerEm
OUT = pathlib.Path(sys.argv[1]); TMP = pathlib.Path(sys.argv[2])

def text_path(s, cx, baseline, size, spacing, fill, max_w):
    names = [CMAP[ord(c)] for c in s]
    adv = [GS[n].width for n in names]
    w = (sum(adv) + spacing * UPM / size * (len(s) - 1)) * size / UPM
    k = min(1.0, max_w / w); size *= k; w *= k            # encolhe se não couber
    sc = size / UPM; x = cx - w / 2; d = []
    for n, a in zip(names, adv):
        pen = SVGPathPen(GS, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))   # 1 casa basta
        GS[n].draw(TransformPen(pen, (sc, 0, 0, -sc, x, baseline)))
        d.append(pen.getCommands()); x += a * sc + spacing * k
    return f'<path d="{" ".join(d)}" fill="{fill}"/>'

def svg(generic):
    W, H, DX, DY = 560, 740, 150, 88                  # frente da caixa e profundidade
    x0 = (1000 - W - DX) / 2; y0 = 80 + DY; x1, y1 = x0 + W, y0 + H
    blk = 116; yel = 92
    yb = y1 - blk; yy = yb - yel
    top_white = yy if generic else yb
    cx = x0 + W / 2
    side = lambda ya, yb_, c: f'<polygon points="{x1},{ya} {x1+DX},{ya-DY} {x1+DX},{yb_-DY} {x1},{yb_}" fill="{c}"/>'
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">',
         '<defs><radialGradient id="sh" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".18"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient></defs>',
         '<rect width="1000" height="1000" fill="#ffffff"/>',
         f'<ellipse cx="{cx + DX/2}" cy="{y1 + 18}" rx="{(W + DX)/2 + 10}" ry="30" fill="url(#sh)"/>',
         f'<polygon points="{x0},{y0} {x0+DX},{y0-DY} {x1+DX},{y0-DY} {x1},{y0}" fill="#f4f6f9" stroke="#c9d0da" stroke-width="2" stroke-linejoin="round"/>',
         side(y0, y1, "#dde2ea"), side(yb, y1, "#000000")]
    if generic:
        p.append(side(yy, yb, "#e0aa00"))
    p.append(f'<polygon points="{x1},{y0} {x1+DX},{y0-DY} {x1+DX},{y1-DY} {x1},{y1}" fill="none" stroke="#c9d0da" stroke-width="2" stroke-linejoin="round"/>')
    p.append(f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="#ffffff" stroke="#b8c0cc" stroke-width="3"/>')
    p.append(f'<rect x="{x0}" y="{yb}" width="{W}" height="{blk}" fill="#141414"/>')
    p.append(text_path("NECESSITA DE RECEITA", cx, yb + blk / 2 + 13, 38, 2, "#ffffff", W - 60))
    if generic:
        p.append(f'<rect x="{x0}" y="{yy}" width="{W}" height="{yel}" fill="#ffc400"/>')
        p.append(text_path("MEDICAMENTO GENÉRICO", cx, yy + yel / 2 + 12, 34, 1, "#141414", W - 60))
    s = 6.5; mid = (y0 + top_white) / 2                 # símbolo no meio da parte branca
    p.append(f'<g transform="translate({cx - 20*s},{mid - 20*s}) scale({s})"><rect width="40" height="40" rx="9" fill="#F23F5F"/><path d="M16 8h8v8h8v8h-8v8h-8v-8H8v-8h8z" fill="#fff"/></g>')
    p.append(f'<line x1="{x1}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="#b8c0cc" stroke-width="2"/>')
    p.append("</svg>")
    return "\n".join(p)

for name, g in (("remedio-receita", False), ("remedio-receita-generico", True)):
    f = OUT / f"{name}.svg"; f.write_text(svg(g))
    raw = TMP / f"{name}-raw.png"
    subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--hide-scrollbars", f"--screenshot={raw}",
                    "--window-size=1000,1000", f.resolve().as_uri()], check=True, capture_output=True)
    im = Image.open(raw).convert("RGB").resize((600, 600), Image.LANCZOS)
    im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(OUT / f"{name}.png", optimize=True)
    print(name, (OUT / f"{name}.svg").stat().st_size, (OUT / f"{name}.png").stat().st_size)
