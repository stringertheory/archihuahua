#!/usr/bin/env bash
#
# subset.sh — produce a web-ready Archihuahua subset (woff2).
#
# Default: width pinned to 92%, weight left VARIABLE, Latin-1 character set.
# Pinning an axis fixes it; any axis you don't pin stays variable in the output.
#
# Override with environment variables:
#   WIDTH=92        wdth value to pin (62–125). Set WIDTH= (empty) to keep it variable.
#   WEIGHT=         wght value to pin. Empty (default) keeps weight variable.
#   UNICODES=...    character set (default: Latin-1 = ASCII + Latin-1 Supplement).
#   INPUT=...       source font (default: the [wdth,wght] variable font).
#   OUT=...         output path (default: build/subset/Archihuahua-w<WIDTH>-latin1.woff2).
#   FLAVOR=woff2    output flavor (woff2 or woff).
#   FEATURES=       EXTRA OpenType features to keep, comma-separated, on top of
#                   the kept baseline. The baseline is pyftsubset's defaults
#                   (kern, liga, ccmp, locl, frac/numr/dnom, rvrn) PLUS tnum
#                   (tabular figures — always kept here so number columns align).
#                   Add e.g. FEATURES=onum,zero for oldstyle figures + slashed
#                   zero, or FEATURES='*' for everything (sups/subs, .case forms,
#                   the alt ampersand, …).
#
# Examples:
#   scripts/subset.sh                        # width 92%, variable weight, Latin-1
#   WIDTH=75 scripts/subset.sh               # Condensed (75), variable weight
#   WIDTH=92 WEIGHT=700 scripts/subset.sh    # fully static: width 92, weight 700
#   WIDTH= scripts/subset.sh                 # keep BOTH axes variable
#   UNICODES="U+0020-007E" scripts/subset.sh # ASCII only
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FT="$ROOT/.venv/bin/fonttools";    [ -x "$FT" ]    || FT="fonttools"
PYBIN="$ROOT/.venv/bin/python";    [ -x "$PYBIN" ] || PYBIN="python3"

INPUT="${INPUT:-$ROOT/fonts/variable/Archihuahua[wdth,wght].ttf}"
WIDTH="${WIDTH-92}"                                  # ${WIDTH-92}: WIDTH= keeps it variable
WEIGHT="${WEIGHT-}"
UNICODES="${UNICODES:-U+0020-007E,U+00A0-00FF}"      # Latin-1
FLAVOR="${FLAVOR:-woff2}"
FEATURES="${FEATURES-}"
OUT="${OUT:-$ROOT/build/subset/Archihuahua-w${WIDTH:-var}-latin1.${FLAVOR}}"

mkdir -p "$(dirname "$OUT")"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 1) pin the axes we want fixed; leave the rest variable
pins=()
if [ -n "$WIDTH" ];  then pins+=("wdth=$WIDTH");  fi
if [ -n "$WEIGHT" ]; then pins+=("wght=$WEIGHT"); fi

src="$INPUT"
if [ "${#pins[@]}" -gt 0 ]; then
  echo "Instancing: ${pins[*]}   (axes not listed here stay variable)"
  "$FT" varLib.instancer "$INPUT" "${pins[@]}" -o "$TMP/inst.ttf" >/dev/null
  src="$TMP/inst.ttf"
fi

# 2) subset to the character set and compress.
# pyftsubset keeps a default feature set (kern, liga, ccmp, locl, frac/numr/dnom,
# rvrn) so kerning and the fl/ffl ligatures survive. It drops the rest, which for
# Archihuahua means alternate figure styles (oldstyle .osf, tabular .tf/.tosf, lining,
# slashed zero), super/subscripts, ordinals, the .case punctuation forms, and the
# alt ampersand (aalt). Add any back with FEATURES=... (see header).
# tnum (tabular figures) is always kept on top of the default set; FEATURES adds more.
if [ "$FEATURES" = "*" ]; then
  keep='*'
elif [ -n "$FEATURES" ]; then
  keep="tnum,$FEATURES"
else
  keep="tnum"
fi
# Keep the copyright + OFL license name records (IDs 0/13/14) so the OFL travels
# with the file; pyftsubset would otherwise drop the license text (IDs 13/14).
echo "Subsetting → [$UNICODES] as $FLAVOR  (features +$keep)"
lf="--layout-features+=$keep"; [ "$keep" = '*' ] && lf="--layout-features=*"
"$FT" subset "$src" --unicodes="$UNICODES" "$lf" \
  --name-IDs+=0,13,14 --flavor="$FLAVOR" --output-file="$OUT"

# 3) report size + which axes remain
sz=$(stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT")
axes=$("$PYBIN" - "$OUT" <<'PY' 2>/dev/null || true
import sys
from fontTools.ttLib import TTFont
f = TTFont(sys.argv[1])
print(",".join(a.axisTag for a in f["fvar"].axes) if "fvar" in f else "static (no axes)")
PY
)
awk -v s="$sz" -v o="$OUT" -v a="$axes" \
  'BEGIN{ printf "Wrote %s\n  %.1f KB, axes: %s\n", o, s/1024, a }'
