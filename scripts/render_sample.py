#!/usr/bin/env python3
"""Render a sample string from one or more fonts for visual comparison.

Each --font is "Label=path". Variable fonts are instanced to the requested
weight/width first; static fonts are used as-is. Rows are stacked top to
bottom with their labels, so you can eyeball design variants side by side.

    python scripts/render_sample.py --out build/compare.png \
        --text "Albert" --wght 700 --wdth 100 \
        --font "Original=fonts/variable/Archihuahua[wdth,wght].ttf" \
        --font "Tail=build/Archihuahua-ltail-VF.ttf"
"""
import argparse
import io

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

LABEL_FONT = "fonts/ttf/Archihuahua-Medium.ttf"


def instanced_bytes(path, wght, wdth):
    f = TTFont(path)
    if "fvar" in f:
        instantiateVariableFont(f, {"wght": wght, "wdth": wdth}, inplace=True)
    bio = io.BytesIO()
    f.save(bio)
    return bio.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--font", action="append", required=True, metavar="LABEL=PATH",
                    help="font to render; repeatable")
    ap.add_argument("--text", default="ALBERT Albert")
    ap.add_argument("--wght", type=float, default=700)
    ap.add_argument("--wdth", type=float, default=100)
    ap.add_argument("--size", type=int, default=180, help="render size in px")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pad = 30
    label_h = 34
    label_font = ImageFont.truetype(LABEL_FONT, 26)

    rows = []  # (label, PIL text image)
    for spec in args.font:
        label, path = spec.split("=", 1)
        data = instanced_bytes(path, args.wght, args.wdth)
        face = ImageFont.truetype(io.BytesIO(data), args.size)
        asc, desc = face.getmetrics()
        # measure
        tmp = Image.new("L", (10, 10))
        w = ImageDraw.Draw(tmp).textlength(args.text, font=face)
        img = Image.new("L", (int(w) + 2 * pad, asc + desc + 2 * pad), 255)
        ImageDraw.Draw(img).text((pad, pad), args.text, font=face, fill=0)
        rows.append((label, img))

    W = max(img.width for _, img in rows)
    H = sum(label_h + img.height for _, img in rows) + pad
    canvas = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(canvas)
    y = pad
    for label, img in rows:
        draw.text((pad, y), label, font=label_font, fill=120)
        canvas.paste(img, (0, y + label_h))
        y += label_h + img.height
    canvas.save(args.out)
    print("wrote", args.out, canvas.size)


if __name__ == "__main__":
    main()
