#!/usr/bin/env python3
"""Render the three README specimen sheets from the built Archihuahua fonts.

Reproduces the original Archivo specimens (same words, widths and weights),
rendered in Archihuahua:

  1  weight waterfall  — the nine weights, each a word sized to the column.
  2  width waterfall   — the six widths in Thin, roman + italic, at a FIXED
                         size, the shown letters/numbers truncated to fit.
  3  abcde, roman + italic across the nine weights — a mirrored layout (roman
                         Black→Thin on the left, italic Thin→Black on the right)
                         at a fixed size, widths varying naturally.

Only the small title line differs from the originals (it names Archihuahua and
shows the tailed l). Run a build first, then:

    .venv/bin/python scripts/specimens.py            # writes Archihuahua-{1,2,3}.png
    .venv/bin/python scripts/specimens.py OUTDIR
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TTF = os.path.join(REPO, "fonts", "ttf")
OUT = sys.argv[1] if len(sys.argv) > 1 else REPO

W = 841                      # original sheet width
ML, CONTENT = 71, 697        # left margin / content width (right edge 768)
INK, LBL, RULE, BG = 0, 150, 195, 255
TITLE = "archihuahua  ·  a superfamily of 108 styles"


def load(style, size):
    return ImageFont.truetype(os.path.join(TTF, f"Archihuahua{style}.ttf"), size)


def tight(text, style, target_w=None, size=None):
    """Black text cropped to its ink, either fit-to-width or at a fixed size."""
    if size is None:
        size = max(8, round(100 * target_w / load(style, 100).getlength(text)))
    size = int(round(size))
    f = load(style, size)
    pad = size
    img = Image.new("L", (round(f.getlength(text)) + 2 * pad, 3 * size), BG)
    ImageDraw.Draw(img).text((pad, pad), text, font=f, fill=INK)
    return img.crop(ImageOps.invert(img).getbbox()), size


def tracked(text, size=13, fill=LBL, track=1.4, style="-Medium"):
    """Small letter-spaced text (labels, title, footer), cropped to ink."""
    f = load(style, size)
    ws = [f.getlength(c) for c in text]
    asc, desc = f.getmetrics()
    img = Image.new("L", (int(sum(ws) + track * len(text)) + 6, asc + desc), BG)
    d = ImageDraw.Draw(img)
    x = 3.0
    for c, w in zip(text, ws):
        d.text((x, 0), c, font=f, fill=fill); x += w + track
    box = ImageOps.invert(img).getbbox()
    return img.crop(box) if box else img


def size_to_fit(text, style, target_w, cap=400):
    """Largest integer point size at which `text` still fits in target_w."""
    s = 10
    while s < cap and load(style, s + 1).getlength(text) <= target_w:
        s += 1
    return s


def page(rows, footer, top=92, gap=24, label_gap=8, bottom=78):
    """Compose a dynamic-height sheet: header rule, stacked (big, label) rows, footer."""
    h = top + bottom + sum(c.height + (label_gap + l.height if l else 0) + gap
                           for c, l in rows)
    c = Image.new("L", (W, h), BG)
    d = ImageDraw.Draw(c)
    ht = tracked(TITLE, 13)
    c.paste(ht, ((W - ht.width) // 2, 26)); d.line(((ML, 54), (W - ML, 54)), fill=RULE)
    y = top
    for big, label in rows:
        c.paste(big, (ML, y)); y += big.height
        if label:
            y += label_gap; c.paste(label, (ML, y)); y += label.height
        y += gap
    ft = tracked(footer, 12)
    c.paste(ft, ((W - ft.width) // 2, h - 42)); d.line(((ML, h - 54), (W - ML, h - 54)), fill=RULE)
    return c


# ---- 1: weight waterfall (original words, sized to the column) ----------------
def specimen1():
    rows = [
        ("Black", "-Black", "Underweight"),
        ("Extra Bold", "-ExtraBold", "Bilateralismo"),
        ("Bold", "-Bold", "Imperfections"),
        ("Semi Bold", "-SemiBold", "Wellstructured"),
        ("Medium", "-Medium", "Licentiousness"),
        ("Regular", "-Regular", "Depoliticisation"),
        ("Light", "-Light", "Condescension"),
        ("Extra Light", "-ExtraLight", "Unquestioningly"),
        ("Thin", "-Thin", "Disproportionate"),
    ]
    out = [(tight(word, style, target_w=CONTENT)[0], tracked(name.upper()))
           for name, style, word in rows]
    return page(out, "archihuahua  thin · extralight · light · regular · medium · semibold · bold · extrabold · black")


# ---- 2: width waterfall (fixed size, content truncated to fit) ----------------
def specimen2():
    UC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    LC = "abcdefghijklmnopqrstuvwxyz1234"
    rows = [
        ("ExtraCondensed Thin", "ExtraCondensed-Thin", False),
        ("ExtraCondensed Thin Italic", "ExtraCondensed-ThinItalic", True),
        ("Condensed Thin", "Condensed-Thin", False),
        ("Condensed Thin Italic", "Condensed-ThinItalic", True),
        ("SemiCondensed Thin", "SemiCondensed-Thin", False),
        ("SemiCondensed Thin Italic", "SemiCondensed-ThinItalic", True),
        ("Thin", "-Thin", False),
        ("Thin Italic", "-ThinItalic", True),
        ("SemiExpanded Thin", "SemiExpanded-Thin", False),
        ("SemiExpanded Thin Italic", "SemiExpanded-ThinItalic", True),
        ("Expanded Thin", "Expanded-Thin", False),
        ("Expanded Thin Italic", "Expanded-ThinItalic", True),
    ]
    # one fixed size for every row: calibrate so Expanded Thin shows A–L (the
    # widest variant shows the fewest glyphs; the narrowest shows the most).
    size = size_to_fit("ABCDEFGHIJKL", "Expanded-Thin", CONTENT)

    def prefix(seq, style):
        f = load(style, size)
        k = len(seq)
        while k > 1 and f.getlength(seq[:k]) > CONTENT:
            k -= 1
        return seq[:k]

    out = []
    for name, style, ital in rows:
        seq = LC if ital else UC
        text = prefix(seq, style)
        out.append((tight(text, style, size=size)[0], tracked(name.upper())))
        print(f"  {name:28s} {text}")
    return page(out, "archihuahua  extracondensed · condensed · semicondensed · regular · semiexpanded · expanded",
                gap=14)


# ---- 3: abcde, roman + italic across weights (mirrored, pixel-faithful) -------
def specimen3():
    H = 1190
    R_MARGIN = 768
    baselines = [155, 272, 390, 506, 624, 741, 858, 975, 1092]
    roman = ["-Black", "-ExtraBold", "-Bold", "-SemiBold", "-Medium",
             "-Regular", "-Light", "-ExtraLight", "-Thin"]
    rlabel = ["BLACK", "EXTRABOLD", "BOLD", "SEMIBOLD", "MEDIUM",
              "REGULAR", "LIGHT", "EXTRALIGHT", "THIN"]
    italic = ["-ThinItalic", "-ExtraLightItalic", "-LightItalic", "-Italic",
              "-MediumItalic", "-SemiBoldItalic", "-BoldItalic",
              "-ExtraBoldItalic", "-BlackItalic"]
    ilabel = ["THIN ITALIC", "EXTRALIGHT ITALIC", "LIGHT ITALIC", "ITALIC",
              "MEDIUM ITALIC", "SEMIBOLD ITALIC", "BOLD ITALIC",
              "EXTRABOLD ITALIC", "BLACK ITALIC"]

    # one fixed size for all: calibrate so "abcde" ink HEIGHT == 85px (the
    # original band height). Height is weight-independent, so once the size
    # matches, every column width matches the original too.
    lo, hi = 100.0, 400.0
    for _ in range(26):
        mid = (lo + hi) / 2
        h = tight("abcde", "-Regular", size=mid)[0].height
        lo, hi = (mid, hi) if h < 85 else (lo, mid)
    size = round((lo + hi) / 2)

    c = Image.new("L", (W, H), BG)
    d = ImageDraw.Draw(c)
    ht = tracked(TITLE, 13); c.paste(ht, ((W - ht.width) // 2, 26))
    d.line(((ML, 54), (W - ML, 54)), fill=RULE)
    for i, base in enumerate(baselines):
        rc = tight("abcde", roman[i], size=size)[0]
        ic = tight("abcde", italic[i], size=size)[0]
        c.paste(rc, (ML, base - rc.height))                  # roman left-aligned
        c.paste(ic, (R_MARGIN - ic.width, base - ic.height))  # italic right-aligned
        c.paste(tracked(rlabel[i]), (ML + 2, base + 14))
        il = tracked(ilabel[i])
        c.paste(il, (R_MARGIN - il.width, base + 14))         # italic label right-aligned
    ft = tracked("abcde — roman & italic across the nine weights  ·  archihuahua, a fork of archivo", 12)
    c.paste(ft, ((W - ft.width) // 2, H - 40)); d.line(((ML, H - 52), (W - ML, H - 52)), fill=RULE)
    return c


# ---- 0: AI vs Al — the tailed l disambiguates them (the hero specimen) -------
def specimen0():
    title = TITLE + "  ·  better for people named Al"
    style = "-Bold"
    size = 230
    ai, _ = tight("AI", style, size=size)
    al, _ = tight("Al", style, size=size)
    gap = 90
    group = ai.width + gap + al.width
    sent, _ = tight("Hi, I'm Al, not AI.", "-Medium", target_w=CONTENT)

    # this sheet is shown small in the README (≈half width), so its small text
    # is sized up to stay legible there.
    top, lab_gap, mid_gap, bottom = 96, 18, 64, 80
    la, lb = tracked("artificial intelligence", 22), tracked("Alexander", 22)
    hero_h = max(ai.height, al.height)
    H = top + hero_h + lab_gap + max(la.height, lb.height) + mid_gap + sent.height + bottom

    c = Image.new("L", (W, H), BG)
    d = ImageDraw.Draw(c)
    ht = tracked(title, 16)
    c.paste(ht, ((W - ht.width) // 2, 26)); d.line(((ML, 56), (W - ML, 56)), fill=RULE)

    gx = (W - group) // 2
    base = top + hero_h
    c.paste(ai, (gx, base - ai.height))
    alx = gx + ai.width + gap
    c.paste(al, (alx, base - al.height))
    c.paste(la, (gx + (ai.width - la.width) // 2, base + lab_gap))
    c.paste(lb, (alx + (al.width - lb.width) // 2, base + lab_gap))

    sy = base + lab_gap + max(la.height, lb.height) + mid_gap
    c.paste(sent, (ML, sy))
    ft = tracked("in archihuahua the tailed l keeps Al clear of the AI", 18)
    c.paste(ft, ((W - ft.width) // 2, H - 42)); d.line(((ML, H - 54), (W - ML, H - 54)), fill=RULE)
    return c


for n, fn in ((0, specimen0), (1, specimen1), (2, specimen2), (3, specimen3)):
    out = os.path.join(OUT, f"Archihuahua-{n}.png")
    fn().save(out)
    print("wrote", out)
