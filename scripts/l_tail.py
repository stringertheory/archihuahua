"""Geometry for the lowercase `l` tail, shared by the editor and the explorer.

`l_tail_points` returns the `l` outline as a list of (x, y, type) nodes, where
type is 'line', 'curve' (on-curve, preceded by two 'offcurve' handles), or
'offcurve'. The shape is defined as ratios of the stem width so it scales
across the weight and width axes. This is the single source of truth: both
add_l_tail.py (which writes it into the .glyphs source) and tail_explorer.py
(which previews it live) call this.
"""


def l_tail_points(xL, xR, yt, sw, overhang, terminal, dip):
    """Build the new `l` contour as (x, y, type) nodes.

    xL, xR    stem left / right edge      sw  stem width (xR - xL)
    yt        top (cap/ascender) of stem
    overhang  tail tip reach past xR, in stem-widths (t = 0.75)
    terminal  height of the upturned tip, in stem-widths (t = 0.72)
    dip       dip below the baseline, in stem-widths
    """
    x_bot = xR + 0.05 * sw           # where the rounded bottom flattens out
    x_tip = xR + overhang * sw       # tail tip
    y_bot = -dip * sw
    y_term = terminal * sw
    term_w = 0.39 * sw               # width of the upturned terminal

    def lerp(a, b, t):
        return a + (b - a) * t

    # Order: top-left, down the left edge, round the bottom, out to the tail
    # tip, up the terminal, notch back onto the stem's right edge, top-right.
    return [
        (xL,                       yt,                 'line'),      # top-left
        (xL,                       0.98 * sw,          'line'),      # bottom-left curve start
        (xL,                       0.45 * sw,          'offcurve'),
        (xL + 0.25 * sw,           y_bot,              'offcurve'),
        (x_bot,                    y_bot,              'curve'),     # bottom (below baseline)
        (lerp(x_bot, x_tip, 0.45), y_bot,              'offcurve'),
        (lerp(x_bot, x_tip, 0.85), y_bot * 0.33,       'offcurve'),
        (x_tip,                    0.03 * sw,          'curve'),     # tail tip, bottom
        (x_tip,                    y_term,             'line'),      # tail tip, top
        (x_tip - term_w,           y_term,             'line'),
        (lerp(x_tip - term_w, xR, 0.55), y_term,       'offcurve'),
        (xR,                       y_term + 0.13 * sw, 'offcurve'),
        (xR,                       y_term + 0.36 * sw, 'curve'),     # notch onto stem
        (xR,                       yt,                 'line'),      # top-right
    ]


def l_advance(xR, sw, overhang):
    """Advance width that leaves the tail clear of the next glyph."""
    x_tip = xR + overhang * sw
    return round(x_tip + max(20, 0.20 * sw))
