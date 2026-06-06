#!/usr/bin/env python3
"""Add a curved tail (foot) to the lowercase `l` and its accented forms.

Works on both the upright and italic sources (it reads each master's italic
angle and slants the tail to match). For every target glyph it finds the
*stem* contour -- the full-height 4-node rectangle -- and replaces only that,
leaving accents, slashes and ligature partners untouched. The stem is rebuilt
with an identical 14-node structure in every master so interpolation stays
valid. The tail is expressed as ratios of the stem width, so it scales across
the weight/width axes on its own.

    python scripts/add_l_tail.py sources/Archihuahua.glyphs build/out.glyphs \
        --overhang 0.39 --terminal 0.78 --dip 0.10

Pass --inplace to overwrite the source instead of writing a separate file.
"""
import argparse
import math

import glyphsLib
from glyphsLib import GSNode, GSPath

from l_tail import l_tail_points

# Glyphs whose `l` stem should get the tail. `lj` is deliberately excluded: its
# stem butts directly against the `j`, so a rightward tail would collide.
DEFAULT_GLYPHS = ["l", "lacute", "lcaron", "ldot", "lcommaaccent", "lslash",
                  "fl", "f_f_l"]


def find_stem(layer):
    """Index of the stem contour: a 4-node rectangle from baseline to top."""
    hits = []
    for i, p in enumerate(layer.paths):
        if len(p.nodes) != 4:
            continue
        ys = [n.position.y for n in p.nodes]
        if abs(min(ys)) <= 10 and max(ys) >= 600:
            hits.append(i)
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one stem contour, found {hits} "
                         f"in layer {layer.layerId}")
    return hits[0]


def build_stem(stem_path, overhang, terminal, dip, slant):
    """Replace a (possibly slanted) stem rectangle with the tailed outline.

    Returns (new GSPath, x of the tail tip) so the caller can set the advance.
    `slant` is tan(italic angle); 0 for upright.
    """
    # un-slant the 4 corners to recover an upright rectangle
    xs_u = [n.position.x - n.position.y * slant for n in stem_path.nodes]
    ys = [n.position.y for n in stem_path.nodes]
    xL, xR, yt, sw = min(xs_u), max(xs_u), max(ys), max(xs_u) - min(xs_u)

    pts = l_tail_points(xL, xR, yt, sw, overhang, terminal, dip)
    path = GSPath()
    path.closed = True
    for x, y, t in pts:                       # re-slant each generated point
        n = GSNode()
        n.position = (round(x + y * slant), round(y))
        n.type = t
        path.nodes.append(n)
    tip_x, tip_y = pts[7][0], pts[7][1]       # the tail-tip node
    return path, tip_x + tip_y * slant


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="input .glyphs file")
    ap.add_argument("out", nargs="?", help="output .glyphs file (default: src)")
    ap.add_argument("--overhang", type=float, default=0.39,
                    help="tail reach past the stem, in stem-widths (t=0.75)")
    ap.add_argument("--terminal", type=float, default=0.78,
                    help="height of the upturned tip, in stem-widths (t=0.72)")
    ap.add_argument("--dip", type=float, default=0.10,
                    help="dip below the baseline, in stem-widths")
    ap.add_argument("--glyphs", nargs="+", default=DEFAULT_GLYPHS,
                    help="glyphs to modify")
    ap.add_argument("--inplace", action="store_true", help="overwrite src")
    args = ap.parse_args()
    out = args.src if args.inplace else (args.out or args.src)

    font = glyphsLib.GSFont(args.src)
    slant = {m.id: math.tan(math.radians(m.italicAngle)) for m in font.masters}

    def slant_for(layer):  # bracket/brace layers aren't keyed by master id
        return slant.get(layer.layerId, slant.get(layer.associatedMasterId, 0.0))

    for name in args.glyphs:
        g = font.glyphs[name]
        if g is None:
            print(f"  ! {name}: not found, skipping")
            continue
        widths = []
        for L in g.layers:
            if not L.paths:                     # skip empty / non-outline layers
                continue
            s = slant_for(L)
            i = find_stem(L)
            xs_u = [n.position.x - n.position.y * s for n in L.paths[i].nodes]
            sw = max(xs_u) - min(xs_u)
            new_path, tip_x = build_stem(L.paths[i], args.overhang,
                                         args.terminal, args.dip, s)
            L.paths[i] = new_path
            # widen the advance only if the tail would otherwise crowd the next
            # glyph; never narrower than the original (keeps italic overhang)
            L.width = max(L.width, round(tip_x + max(20, 0.20 * sw)))
            widths.append(L.width)
        print(f"  {name:14s} stem retailed in {len(g.layers)} masters, "
              f"widths {min(widths)}–{max(widths)}")

    font.save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
