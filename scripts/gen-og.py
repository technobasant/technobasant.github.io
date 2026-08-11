#!/usr/bin/env python3
"""Generate the 1200x630 social cards in assets/og/.

Builds each card as SVG and hands it to rsvg-convert. Text is set in Georgia,
which is present on macOS and resolves through fontconfig (verified with
`fc-match Georgia`); rsvg-convert silently substitutes a missing family, so the
build asserts on the output dimensions and a minimum byte size afterwards.

The card names are the ones referenced by `_data/tags.yml` plus the site-wide
fallback named in `_config.yml` (`og_image`). Stdlib only.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "og"

W, H = 1200, 630
BG = "#0D0F12"
INK = "#ECE8E1"
INK_2 = "#A6AEB8"
ACCENT = "#C4A574"
LINE = "#232830"

SITE = "technobasant.github.io"
NAME = "Basant Bhattarai"
ROLE = "Senior Data & AI Platform Engineer"

# The brass B, as a path so no font is involved in the mark itself.
B_PATH = (
    "M9.4 8.2 H16.4 C19.9 8.2 21.7 9.8 21.7 12.4 C21.7 14.2 20.8 15.4 19.1 15.95 "
    "C21.3 16.4 22.6 17.85 22.6 20 C22.6 22.75 20.6 24.3 17 24.3 H9.4 Z "
    "M13 10.8 H16.1 C17.9 10.8 18.8 11.5 18.8 12.7 C18.8 13.9 17.9 14.6 16.1 14.6 H13 Z "
    "M13 17.4 H16.7 C18.6 17.4 19.6 18.1 19.6 19.5 C19.6 20.9 18.6 21.6 16.7 21.6 H13 Z"
)

# filename -> title lines (1 or 2). Keep each line under ~24 characters so it
# clears the 1040px content column at 76px Georgia.
CARDS: dict[str, list[str]] = {
    "og-default.png": ["Data & AI platform", "engineering"],
    "og-spark.png": ["Apache Spark"],
    "og-streaming.png": ["Kafka & streaming"],
    "og-lakehouse.png": ["Iceberg &", "the lakehouse"],
    "og-databases.png": ["Databases at scale"],
    "og-kubernetes.png": ["Kubernetes"],
    "og-agents.png": ["AI agents", "in production"],
    "og-observability.png": ["Observability & SLOs"],
}

MIN_BYTES = 6_000     # anything smaller means the text did not render
MAX_BYTES = 60_000    # budget from the brief


def svg_for(lines: list[str]) -> str:
    if len(lines) == 1:
        baselines = [392]
    else:
        baselines = [348, 440]

    title = "\n".join(
        f'  <text class="title" x="80" y="{y}">{escape(t)}</text>'
        for y, t in zip(baselines, lines)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <style><![CDATA[
    .title  {{ font-family: Georgia, 'Times New Roman', serif; font-size: 76px; fill: {INK}; }}
    .eyebrow{{ font-family: Georgia, 'Times New Roman', serif; font-size: 25px; fill: {ACCENT}; letter-spacing: 2.5px; }}
    .name   {{ font-family: Georgia, 'Times New Roman', serif; font-size: 31px; fill: {INK}; }}
    .role   {{ font-family: Georgia, 'Times New Roman', serif; font-size: 26px; fill: {INK_2}; }}
  ]]></style>

  <rect width="{W}" height="{H}" fill="{BG}"/>

  <!-- mark -->
  <g transform="translate(80 68) scale(1.75)">
    <rect width="32" height="32" rx="7" fill="{ACCENT}"/>
    <path fill="{BG}" fill-rule="evenodd" d="{B_PATH}"/>
  </g>
  <text class="eyebrow" x="164" y="105">{escape(SITE)}</text>

  <!-- accent rule -->
  <rect x="80" y="216" width="104" height="5" fill="{ACCENT}"/>

{title}

  <!-- footer -->
  <rect x="80" y="500" width="1040" height="1" fill="{LINE}"/>
  <text class="name" x="80" y="558">{escape(NAME)}</text>
  <text class="role" x="1120" y="557" text-anchor="end">{escape(ROLE)}</text>
</svg>
"""


def main() -> int:
    if not shutil.which("rsvg-convert"):
        print("::error::rsvg-convert not found (brew install librsvg)", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / ".build.svg"
    failed = False

    for filename, lines in CARDS.items():
        dest = OUT / filename
        tmp.write_text(svg_for(lines), encoding="utf-8")
        subprocess.run(
            ["rsvg-convert", "-w", str(W), "-h", str(H), str(tmp), "-o", str(dest)],
            check=True,
        )

        size = dest.stat().st_size
        dims = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(dest)],
            capture_output=True, text=True, check=True,
        ).stdout
        ok_dims = f"pixelWidth: {W}" in dims and f"pixelHeight: {H}" in dims
        ok_size = MIN_BYTES <= size <= MAX_BYTES

        status = "ok" if (ok_dims and ok_size) else "FAIL"
        if status == "FAIL":
            failed = True
        print(f"{status:4}  {filename:24} {size:>7,} B  {W}x{H}={ok_dims}")

    tmp.unlink(missing_ok=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
