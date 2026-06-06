"""Live preview of the lowercase `l` tail — no font build required.

The `l` is drawn directly from l_tail.l_tail_points(); the surrounding letters
are pulled as outlines from the original variable font, instanced to the chosen
weight/width. Because nothing is recompiled, redraws are instant — fast enough
to drive a slider. Instancing (the only slowish step) is cached per (wght,wdth),
so moving the tail sliders never re-instances.
"""
import os

from functools import lru_cache

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D
import matplotlib.pyplot as plt

from l_tail import l_tail_points, l_advance

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VF = os.path.join(REPO, "fonts", "variable", "Archihuahua[wdth,wght].ttf")


@lru_cache(maxsize=64)
def _instance(wght, wdth):
    f = TTFont(VF)
    instantiateVariableFont(f, {"wght": float(wght), "wdth": float(wdth)}, inplace=True)
    return f


def _glyph_to_path(glyph_set, name):
    """Outline of a font glyph as a matplotlib Path (handles TrueType quadratics)."""
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(pen)
    verts, codes = [], []
    cur = (0, 0)
    start = (0, 0)
    for cmd, args in pen.value:
        if cmd == "moveTo":
            cur = start = args[0]
            verts.append(cur); codes.append(Path.MOVETO)
        elif cmd == "lineTo":
            cur = args[0]
            verts.append(cur); codes.append(Path.LINETO)
        elif cmd == "qCurveTo":
            pts = list(args)
            on = pts[-1] if pts[-1] is not None else start
            offs = pts[:-1]
            if not offs:
                cur = on; verts.append(on); codes.append(Path.LINETO); continue
            for i, c in enumerate(offs):
                nxt = on if i == len(offs) - 1 else (
                    (c[0] + offs[i + 1][0]) / 2, (c[1] + offs[i + 1][1]) / 2)
                verts += [c, nxt]; codes += [Path.CURVE3, Path.CURVE3]
            cur = on
        elif cmd == "curveTo":
            *controls, end = args
            verts += list(controls) + [end]
            codes += [Path.CURVE4] * (len(controls) + 1)
            cur = end
        elif cmd == "closePath":
            verts.append(start); codes.append(Path.CLOSEPOLY)
    if not verts:                    # empty glyph (e.g. space)
        return None
    return Path(verts, codes)


@lru_cache(maxsize=512)
def _context_glyph(wght, wdth, name):
    f = _instance(wght, wdth)
    return _glyph_to_path(f.getGlyphSet(), name), f["hmtx"][name][0]


def l_metrics(wght, wdth):
    """Stem geometry of the original (plain) `l` at this instance: xL, xR, yt, sw."""
    f = _instance(wght, wdth)
    bp = BoundsPen(f.getGlyphSet())
    f.getGlyphSet()["l"].draw(bp)
    xmin, ymin, xmax, ymax = bp.bounds
    return xmin, xmax, ymax, xmax - xmin


def _live_l_path(metrics, overhang, terminal, dip):
    xL, xR, yt, sw = metrics
    pts = l_tail_points(xL, xR, yt, sw, overhang, terminal, dip)
    verts, codes = [(pts[0][0], pts[0][1])], [Path.MOVETO]
    i = 1
    while i < len(pts):
        x, y, t = pts[i]
        if t == "offcurve":          # off, off, on -> cubic
            c1, c2, on = pts[i], pts[i + 1], pts[i + 2]
            verts += [(c1[0], c1[1]), (c2[0], c2[1]), (on[0], on[1])]
            codes += [Path.CURVE4] * 3
            i += 3
        else:
            verts.append((x, y)); codes.append(Path.LINETO); i += 1
    verts.append((pts[0][0], pts[0][1])); codes.append(Path.CLOSEPOLY)
    return Path(verts, codes), l_advance(xR, sw, overhang)


def render_word(text, wght, wdth, overhang, terminal, dip, ax=None):
    """Draw `text` with the live `l`; everything else from the font."""
    f = _instance(wght, wdth)
    cmap = f.getBestCmap()
    metrics = l_metrics(wght, wdth)
    live_path, live_adv = _live_l_path(metrics, overhang, terminal, dip)

    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4))
    pen_x = 0
    for ch in text:
        if ch == "l":
            path, adv = live_path, live_adv
        elif ord(ch) in cmap:
            path, adv = _context_glyph(wght, wdth, cmap[ord(ch)])
        else:
            pen_x += metrics[3]      # unknown char: skip a stem-width
            continue
        if path is not None:         # skip empty glyphs (space) but keep advancing
            ax.add_patch(PathPatch(path.transformed(Affine2D().translate(pen_x, 0)),
                                   facecolor="black", edgecolor="none"))
        pen_x += adv

    ax.axhline(0, color="#d0d0d0", lw=1, zorder=0)      # baseline
    ax.set_xlim(-30, pen_x + 30)
    ax.set_ylim(-260, 820)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax.figure
