#!/usr/bin/env bash
# Regenerate every derived image asset. Outputs are committed — there is no
# image step in the Jekyll build, and none of this runs in CI.
#
#   ./scripts/gen-images.sh          everything
#   ./scripts/gen-images.sh portrait
#   ./scripts/gen-images.sh icons
#   ./scripts/gen-images.sh og
#
# Requires: sips (macOS), cwebp + avifenc (brew install webp libavif),
#           rsvg-convert (brew install librsvg). No ImageMagick.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TARGET="${1:-all}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing tool: $1" >&2; exit 1; }
}

report() {
  local f="$1"
  printf '  %-38s %8s B  %s\n' "$f" \
    "$(wc -c <"$f" | tr -d ' ')" \
    "$(sips -g pixelWidth -g pixelHeight "$f" 2>/dev/null | tail -2 | tr -d '\n ' | sed 's/pixelWidth:/ /;s/pixelHeight:/x/')"
}

# ── portrait ───────────────────────────────────────────────────────────────
# _source/portrait-master.jpg (2490x2701) is the archived master and is excluded
# from the build. assets/images/basant_profile.jpg is the 1200x1200 square crop
# that everything below is derived from.
gen_portrait() {
  need sips; need cwebp; need avifenc
  echo "portrait derivatives"
  local src="assets/images/basant_profile.jpg"
  for w in 400 800 1200; do
    sips -Z "$w" -s format png "$src" --out "$TMP/p$w.png" >/dev/null
    cwebp -quiet -q 80 -sharp_yuv "$TMP/p$w.png" -o "assets/images/portrait-$w.webp"
    # avifenc >= 1.3 deprecates --min/--max; it reports `--min 22 --max 32` as
    # equivalent to `-q 57`, which is what we use so this keeps working.
    avifenc -q 57 -s 4 -j all "$TMP/p$w.png" "assets/images/portrait-$w.avif" >/dev/null
  done
  # JPEG fallbacks: 800w for the hero, 400w for the post author card. Both are
  # referenced as <img src>, so a missing one is a hard html-proofer failure.
  for w in 400 800; do
    sips -Z "$w" -s format jpeg -s formatOptions 78 "$src" --out "assets/images/portrait-$w.jpg" >/dev/null
  done
  for f in assets/images/portrait-*; do report "$f"; done
}

# ── icons ──────────────────────────────────────────────────────────────────
# assets/favicon.svg carries a prefers-color-scheme block, and librsvg does not
# evaluate it, so the touch icon is rendered from a flattened dark-only copy of
# the same path. Safari will not accept an SVG for apple-touch-icon.
gen_icons() {
  need rsvg-convert
  echo "icons"
  python3 - "$TMP/touch-icon.svg" <<'PY'
import re, sys, pathlib
svg = pathlib.Path("assets/favicon.svg").read_text()
d = re.search(r'class="mark"[^>]*\sd="([^"]+)"', svg).group(1)
pathlib.Path(sys.argv[1]).write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="180" height="180">'
    '<rect width="32" height="32" fill="#0f1114"/>'
    f'<path fill="#C4A574" fill-rule="evenodd" d="{d}"/></svg>'
)
PY
  rsvg-convert -w 180 -h 180 "$TMP/touch-icon.svg" -o assets/apple-touch-icon.png
  report assets/apple-touch-icon.png
}

# ── social cards ───────────────────────────────────────────────────────────
gen_og() {
  need rsvg-convert
  echo "social cards"
  python3 scripts/gen-og.py
}

case "$TARGET" in
  all)      gen_portrait; gen_icons; gen_og ;;
  portrait) gen_portrait ;;
  icons)    gen_icons ;;
  og)       gen_og ;;
  *) echo "usage: $0 [all|portrait|icons|og]" >&2; exit 1 ;;
esac
