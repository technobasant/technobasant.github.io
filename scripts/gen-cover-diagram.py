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


def pgbackrest_patroni() -> str:
    """One repo, two cluster members, and the two places config lives."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">BACKUP INTO A MOVING CLUSTER</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The primary moves.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The repo has to not care.</text>',
        node_box(150, 520, 620, 210, "pgBackRest repo", "192.168.105.140", "pg1-host + pg2-host", accent=True),
        node_box(1000, 470, 600, 195, "pgn1", "192.168.105.141", "replica"),
        node_box(1000, 755, 600, 195, "pgn2", "192.168.105.142", "leader"),
        arrow(780, 590, 990, 555, "archive-push", dashed=True, up=True),
        arrow(780, 660, 990, 840, "backup", dashed=True, up=True),
        f'<text x="1680" y="545" font-family="{MONO}" font-size="27" fill="{MUTED}">archive_mode</text>',
        f'<text x="1680" y="583" font-family="{MONO}" font-size="27" fill="{ACCENT}">\u2192 the DCS</text>',
        f'<text x="1680" y="835" font-family="{MONO}" font-size="27" fill="{MUTED}">create_replica</text>',
        f'<text x="1680" y="873" font-family="{MONO}" font-size="27" fill="{ACCENT}">\u2192 local yml</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'stanza \u00b7 full backup \u00b7 replica rebuild \u00b7 point-in-time restore</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">pgBackRest 2.59 \u00b7 PostgreSQL 18.6</text>',
    ]
    return "".join(body)


def lakehouse_spine() -> str:
    """Who holds the credential, and for how long."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">LAKEHOUSE SPINE</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Trino never holds a key.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The catalog lends one.</text>',
        node_box(150, 520, 640, 200, "Trino 483", "coordinator + worker", "no s3 credential"),
        node_box(1010, 470, 620, 200, "Polaris 1.7.0", "iceberg REST catalog", "grant chain + STS", accent=True),
        node_box(1010, 760, 620, 200, "MinIO", "s3://warehouse", "AssumeRole"),
        arrow(800, 590, 1000, 560, "OAuth2", dashed=True, up=True),
        arrow(1320, 680, 1320, 750, ""),
        f'<text x="1350" y="722" font-family="{MONO}" font-size="26" fill="{MUTED}">sts</text>',
        f'<text x="1700" y="560" font-family="{MONO}" font-size="28" fill="{MUTED}">vended</text>',
        f'<text x="1700" y="600" font-family="{MONO}" font-size="28" fill="{ACCENT}">scoped</text>',
        f'<text x="1700" y="640" font-family="{MONO}" font-size="28" fill="{MUTED}">expiring</text>',
        f'<text x="1700" y="880" font-family="{MONO}" font-size="26" fill="{MUTED}">sibling table</text>',
        f'<text x="1700" y="920" font-family="{MONO}" font-size="26" fill="{ACCENT}">AccessDenied</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'native arm64 \u00b7 nothing emulated \u00b7 one laptop</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">Apache Iceberg \u00b7 Apache Polaris</text>',
    ]
    return "".join(body)


def lakehouse_medallion() -> str:
    """Three layers, and the one file an incremental run actually touched."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">BRONZE / SILVER / GOLD</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">dbt said MERGE.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The manifest says one file.</text>',
        node_box(150, 540, 560, 190, "bronze", "1,500,000 rows", "raw landing"),
        node_box(880, 540, 560, 190, "silver", "incremental MERGE", "80 partitions", accent=True),
        node_box(1610, 540, 560, 190, "gold", "12,030 rows", "rebuilt each run"),
        arrow(720, 630, 870, 630, "dbt", dashed=True, up=True),
        arrow(1450, 630, 1600, 630, "ref()", dashed=True, up=True),
        f'<line x1="150" y1="880" x2="{W - 150}" y2="880" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="960" font-family="{MONO}" font-size="30" fill="{MUTED}">snapshot 1</text>',
        f'<text x="620" y="960" font-family="{MONO}" font-size="30" fill="{MUTED}">+80 files</text>',
        f'<text x="1100" y="960" font-family="{MONO}" font-size="30" fill="{MUTED}">1,500,000 rows</text>',
        f'<text x="150" y="1020" font-family="{MONO}" font-size="30" fill="{ACCENT}">snapshot 2</text>',
        f'<text x="620" y="1020" font-family="{MONO}" font-size="30" fill="{ACCENT}">+1 file</text>',
        f'<text x="1100" y="1020" font-family="{MONO}" font-size="30" fill="{ACCENT}">25,000 rows</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'dbt-trino \u00b7 Airflow 3 \u00b7 verified from $snapshots</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">1 of 81 data files</text>',
    ]
    return "".join(body)


def lakehouse_maintenance() -> str:
    """Compaction, and the snapshot window that is your recovery window."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">TABLE MAINTENANCE</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Twenty files into one.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">909,968 rows back.</text>',
        node_box(150, 520, 600, 200, "before", "20 files \u00b7 1,006 KB", "184 ms"),
        node_box(1010, 520, 600, 200, "after optimize", "1 file \u00b7 430 KB", "69 ms", accent=True),
        arrow(760, 620, 1000, 620, "compact", dashed=True, up=True),
        f'<text x="1700" y="580" font-family="{MONO}" font-size="30" fill="{ACCENT}">2.7x</text>',
        f'<text x="1700" y="630" font-family="{MONO}" font-size="26" fill="{MUTED}">same rows</text>',
        f'<line x1="150" y1="830" x2="{W - 150}" y2="830" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="905" font-family="{MONO}" font-size="30" fill="{MUTED}">DELETE</text>',
        f'<text x="560" y="905" font-family="{MONO}" font-size="30" fill="{MUTED}">-909,968</text>',
        f'<text x="1060" y="905" font-family="{MONO}" font-size="30" fill="{ACCENT}">rollback 589 ms</text>',
        f'<text x="1760" y="905" font-family="{MONO}" font-size="30" fill="{MUTED}">restored</text>',
        f'<text x="150" y="985" font-family="{MONO}" font-size="30" fill="{MUTED}">expire_snapshots</text>',
        f'<text x="700" y="985" font-family="{MONO}" font-size="30" fill="{ACCENT}">\u2192 the window closes</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'optimize, then expire \u2014 never the other way round</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">retention IS recovery</text>',
    ]
    return "".join(body)


def lakehouse_engines() -> str:
    """One catalog, two engines, neither holding a key."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">ONE CATALOG, TWO ENGINES</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Nobody copied the data.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Nobody holds a key.</text>',
        node_box(150, 520, 600, 200, "Trino 483", "1,645,100 rows", "99 ms"),
        node_box(150, 790, 600, 200, "StarRocks 4.1.4", "1,645,100 rows", "34 ms", accent=True),
        node_box(1120, 640, 620, 210, "Polaris", "iceberg REST catalog", "vends to both", accent=True),
        arrow(770, 610, 1110, 700, "oauth2", dashed=True, up=True),
        arrow(770, 880, 1110, 790, "oauth2", dashed=True, up=True),
        f'<text x="1810" y="700" font-family="{MONO}" font-size="27" fill="{MUTED}">no aws keys</text>',
        f'<text x="1810" y="742" font-family="{MONO}" font-size="27" fill="{ACCENT}">in either</text>',
        f'<text x="1810" y="784" font-family="{MONO}" font-size="27" fill="{MUTED}">engine config</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'one aggregate, one partition \u2014 not a federation benchmark</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">server-side medians</text>',
    ]
    return "".join(body)


def rag_lakehouse() -> str:
    """The refusal is the feature."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">SCRAPE TO RAG, ON DELTA</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">It answered three questions.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Declining one was the point.</text>',
        node_box(150, 520, 480, 190, "bronze", "187 sections", "raw, nothing dropped"),
        node_box(700, 520, 480, 190, "silver", "170 rows", "17 duplicates gone"),
        node_box(1250, 520, 480, 190, "gold", "170 chunks", "deterministic id", accent=True),
        arrow(640, 615, 690, 615, ""),
        arrow(1190, 615, 1240, 615, ""),
        f'<text x="1800" y="600" font-family="{MONO}" font-size="27" fill="{MUTED}">384-dim</text>',
        f'<text x="1800" y="642" font-family="{MONO}" font-size="27" fill="{ACCENT}">64.8/s</text>',
        f'<line x1="150" y1="830" x2="{W - 150}" y2="830" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="905" font-family="{MONO}" font-size="29" fill="{MUTED}">list vs tuple</text>',
        f'<text x="900" y="905" font-family="{MONO}" font-size="29" fill="{MUTED}">d=0.234</text>',
        f'<text x="1450" y="905" font-family="{MONO}" font-size="29" fill="{ACCENT}">answered, cited</text>',
        f'<text x="150" y="975" font-family="{MONO}" font-size="29" fill="{MUTED}">capital of Nepal</text>',
        f'<text x="900" y="975" font-family="{MONO}" font-size="29" fill="{MUTED}">d=0.923</text>',
        f'<text x="1450" y="975" font-family="{MONO}" font-size="29" fill="{ACCENT}">refused, 0 tokens</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'Spark 4.0.4 \u00b7 Delta 4.0.0 \u00b7 MinIO \u00b7 Chroma \u00b7 llama3.2:1b</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">no JAR downloaded</text>',
    ]
    return "".join(body)


DIAGRAMS = {"patroni-pg18": patroni_pg18, "pgbackrest-patroni": pgbackrest_patroni,
            "lakehouse-spine": lakehouse_spine,
            "lakehouse-medallion": lakehouse_medallion,
            "lakehouse-maintenance": lakehouse_maintenance,
            "lakehouse-engines": lakehouse_engines,
            "rag-lakehouse": rag_lakehouse}

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
