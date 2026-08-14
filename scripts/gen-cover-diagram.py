#!/usr/bin/env python3
"""Build a schematic cover master from a topology description.

Why this exists: the earlier editorial covers were AI-generated 3D scenes — an
elephant beside a gold-padlocked chest, a Mac mini on a glowing plate. On a site
whose whole proposition is measured evidence and stated method, generated stock
imagery is the one element that reads as unearned, and CHI 2026 found that
disclosure of AI imagery consistently shifts trust toward real imagery.

A schematic is honest: it is the actual topology of the thing the post builds,
drawn in the site's own type and palette, and it costs nothing to regenerate
when the topology changes.

    python3 scripts/gen-cover-diagram.py patroni-pg18

Writes _source/covers/editorial-<name>-v1-master.png at 2400x1350; the derived
1600/840 jpg/webp/avif come from `./scripts/gen-images.sh covers`.

Stdlib only, plus rsvg-convert (brew install librsvg) — same dependency as
scripts/gen-og.py. No Pillow, no ImageMagick.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_source" / "covers"

W, H = 2400, 1350

# Light palette only. A cover is a raster: it cannot follow the theme, and the
# og:image is composited by platforms that assume a light background.
PAPER = "#fbfaf8"
INK = "#15181c"
MUTED = "#5d646d"
ACCENT = "#7c5a18"
LINE = "#d8d0c2"
PANEL = "#ffffff"

SERIF = "Fraunces, Georgia, 'Times New Roman', serif"
MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"


def node_box(x, y, w, h, title, sub, badge=None, accent=False):
    edge = ACCENT if accent else LINE
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PANEL}" '
        f'stroke="{edge}" stroke-width="{3 if accent else 2}"/>',
        f'<text x="{x + 34}" y="{y + 62}" font-family="{SERIF}" font-size="46" '
        f'font-weight="600" fill="{INK}">{escape(title)}</text>',
        f'<text x="{x + 34}" y="{y + 108}" font-family="{MONO}" font-size="27" '
        f'fill="{MUTED}">{escape(sub)}</text>',
    ]
    if badge:
        parts.append(
            f'<text x="{x + 34}" y="{y + h - 30}" font-family="{MONO}" font-size="25" '
            f'letter-spacing="2" fill="{ACCENT}">{escape(badge.upper())}</text>'
        )
    return "".join(parts)


def arrow(x1, y1, x2, y2, label="", dashed=False, up=False):
    dash = ' stroke-dasharray="10 9"' if dashed else ""
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    out = (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTED}" '
        f'stroke-width="3"{dash} marker-end="url(#a)"/>'
    )
    if label:
        out += (
            f'<text x="{mid_x}" y="{mid_y + (-18 if up else 38)}" font-family="{MONO}" '
            f'font-size="26" fill="{MUTED}" text-anchor="middle">{escape(label)}</text>'
        )
    return out


def patroni_pg18() -> str:
    """etcd holds the leader key; two Postgres nodes race for it."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        # eyebrow + title
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">RHEL-FAMILY HA LAB</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Patroni promotes the replica.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">etcd decides who leads.</text>',
        # DCS
        node_box(150, 520, 640, 210, "etcd 3.7.0", "192.168.105.140:2379", "leader key + TTL"),
        # Postgres pair
        node_box(1010, 470, 620, 200, "pgn1", "192.168.105.141:5432", "leader → replica"),
        node_box(1010, 760, 620, 200, "pgn2", "192.168.105.142:5432", "replica → LEADER", accent=True),
        # lease arrows. The lower label sits above its line, not below it —
        # centred-below put it straight through the arrowhead.
        arrow(800, 600, 1000, 560, "lease", dashed=True, up=True),
        arrow(800, 665, 1000, 850, "lease", dashed=True, up=True),
        # replication
        arrow(1320, 680, 1320, 750, ""),
        f'<text x="1350" y="722" font-family="{MONO}" font-size="26" fill="{MUTED}">streaming</text>',
        # timeline note
        f'<text x="1700" y="560" font-family="{MONO}" font-size="30" fill="{MUTED}">TL 1</text>',
        f'<text x="1700" y="600" font-family="{MONO}" font-size="34" fill="{ACCENT}">↓</text>',
        f'<text x="1700" y="650" font-family="{MONO}" font-size="30" fill="{ACCENT}">TL 2</text>',
        f'<text x="1700" y="870" font-family="{MONO}" font-size="26" fill="{MUTED}">pg_rewind</text>',
        f'<text x="1700" y="910" font-family="{MONO}" font-size="26" fill="{MUTED}">rejoin</text>',
        # rule + footer
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'Rocky Linux 8 · amd64 under QEMU on Apple Silicon</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">PostgreSQL 18.6 · Patroni 4.1.5</text>',
    ]
    return "".join(body)


DIAGRAMS = {"patroni-pg18": patroni_pg18}


def svg_for(name: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">'
        f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{MUTED}"/></marker></defs>'
        f"{DIAGRAMS[name]()}</svg>"
    )


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in DIAGRAMS:
        print(f"usage: {sys.argv[0]} [{'|'.join(DIAGRAMS)}]", file=sys.stderr)
        return 2
    if not shutil.which("rsvg-convert"):
        print("rsvg-convert not found (brew install librsvg)", file=sys.stderr)
        return 1

    name = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / ".build.svg"
    dest = OUT / f"editorial-{name}-v1-master.png"
    tmp.write_text(svg_for(name), encoding="utf-8")
    subprocess.run(
        ["rsvg-convert", "-w", str(W), "-h", str(H), str(tmp), "-o", str(dest)],
        check=True,
    )
    tmp.unlink(missing_ok=True)
    print(f"{dest.relative_to(ROOT)}  {dest.stat().st_size:,} B  {W}x{H}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
