# scripts

Tooling for editing glyphs by script instead of in Glyphs.app, used here to
add a curved tail to the lowercase `l`.

Editing a glyph in a variable font is only tricky because the change must be
made *identically* across every master or interpolation breaks. Scripting the
edit guarantees that — the same nodes are inserted in the same order in all 9
masters — which is why this is done in Python rather than by hand.

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install glyphsLib fontmake fonttools brotli Pillow matplotlib streamlit
```

## Interactive explorer (recommended for tuning)

Same explorer in two flavours — pick whichever you have installed:

```sh
.venv/bin/streamlit run scripts/tail_explorer.py          # Streamlit
.venv/bin/marimo edit scripts/tail_explorer_marimo.py     # marimo (or: marimo run …)
```

Opens a browser page with live sliders for `overhang`, `terminal`, `dip`, and
the `weight`/`width` instance. It draws the `l` outline directly (no font
build), so it updates in real time. When you settle on a shape it prints the
exact `add_l_tail.py` command to bake it in. Files involved:

- `l_tail.py` — the tail geometry (shared, single source of truth)
- `preview.py` — draws the live `l` + the surrounding letters from the font
- `tail_explorer.py` — the Streamlit UI
- `tail_explorer_marimo.py` — the same UI as a marimo notebook

## Baking it into the source

`add_l_tail.py` retails the `l` stem in `l`, `lacute`, `lcaron`, `ldot`,
`lcommaaccent`, `lslash`, `fl` and `f_f_l`, across all 9 masters, in both the
upright and italic sources (it reads each master's italic angle and slants the
tail to match). It finds the full-height stem contour and replaces only that,
leaving accents / the ł slash / the ligature `f` untouched.

```sh
# preview on copies first
.venv/bin/python scripts/add_l_tail.py sources/Archihuahua.glyphs build/up.glyphs \
    --overhang 0.39 --terminal 0.78 --dip 0.10
.venv/bin/fontmake -g build/up.glyphs -o variable --output-path build/up-VF.ttf

# bake into the real sources (the values currently in the source)
.venv/bin/python scripts/add_l_tail.py sources/Archihuahua.glyphs        --inplace \
    --overhang 0.39 --terminal 0.78 --dip 0.10
.venv/bin/python scripts/add_l_tail.py sources/Archihuahua-Italic.glyphs --inplace \
    --overhang 0.39 --terminal 0.78 --dip 0.10
```

`lj` is deliberately excluded: its stem butts straight against the `j`, so a
rightward tail would collide. Override the set with `--glyphs ...` if needed.

> **Diff note.** glyphsLib re-serializes the whole file on save, which rewrites
> the feature/header sections (collapsing OpenType feature code to one line).
> After an `--inplace` bake, restore the header so the diff stays limited to the
> changed glyphs — splice the original header (everything before `glyphs = (`)
> back on. See the git history of this change for the one-liner.

## Subsetting for the web (`subset.sh`)

`subset.sh` pins whichever axes you want fixed (leaving the rest variable) and
subsets to a character set, emitting woff2. Its default is **width pinned to
92%, weight variable, Latin-1** (~29 KB vs ~172 KB for the full font).

```sh
scripts/subset.sh                        # width 92%, variable weight, Latin-1
WIDTH=75 scripts/subset.sh               # Condensed (75), variable weight
WIDTH=92 WEIGHT=700 scripts/subset.sh    # fully static: width 92, weight 700
WIDTH= scripts/subset.sh                 # keep BOTH axes variable
UNICODES="U+0020-007E" scripts/subset.sh # ASCII only
```

The default feature set is kept (kerning, the `fl`/`ffl` ligatures, fractions,
localized forms). Archihuahua has no stylistic sets; what gets dropped is the
alternate figure styles (oldstyle/tabular/lining, slashed zero), super/
subscripts, ordinals, the `.case` punctuation forms, and the alternate ampersand
(`aalt`). Add any back with `FEATURES=tnum,onum,zero` (or `FEATURES='*'` for
all). For a multi-range web setup, run it per range and declare each file with a
CSS `unicode-range`.

## README specimens (`specimens.py`)

Regenerates the four specimen images in the repo root from the built static
fonts (run a build first):

```sh
.venv/bin/python scripts/specimens.py          # writes Archihuahua-{0,1,2,3}.png
```

0 — the "AI" vs "Al" hero comparison the tailed `l` is for (top of the README);
1 — weights waterfall (Thin→Black, original Archivo words); 2 — widths waterfall
(six widths in Thin, roman + italic, fixed size with the shown letters/numbers
truncated to fit); 3 — "abcde" roman + italic across the nine weights (mirrored:
roman Black→Thin left, italic Thin→Black right).

## Tuning the tail

`add_l_tail.py` expresses the tail as ratios of each master's stem width:

| flag | meaning | `t` value | current source |
|------|---------|-----------|----------------|
| `--overhang` | reach past the stem | 0.75 | 0.39 |
| `--terminal` | height of the upturned tip | 0.72 | 0.78 |
| `--dip` | dip below the baseline | 0.10 | 0.10 |

Pass `--overhang 0.75 --terminal 0.72` to match the `t` exactly.

## Not yet handled

- **Kerning:** confirmed *not* needed — the right side of `l` carries no kern
  pairs (the only side the tail changes). Default spacing is set per glyph.
- **`lj` digraph:** left untailed (collision); revisit if you want it.
- **Regenerating `fonts/`:** the baked change is in the sources only. Rebuild
  the output binaries with `gftools builder sources/config.yaml` as a release
  step.
