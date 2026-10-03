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


def coding_agents_review() -> str:
    """Agent output is a candidate; the repo's gates decide merge."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">AGENT GOVERNANCE</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Agents write the diff.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The repo decides merge.</text>',
        node_box(150, 520, 520, 210, "agent session", "Cursor · Claude Code · Codex", "untrusted draft"),
        node_box(820, 520, 520, 210, "candidate PR", "types · tests · scans", "evidence attached"),
        node_box(1490, 520, 560, 210, "named owner", "CODEOWNERS + CI", "merge or refuse", accent=True),
        arrow(680, 625, 810, 625, ""),
        arrow(1350, 625, 1480, 625, ""),
        f'<line x1="150" y1="830" x2="{W - 150}" y2="830" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="905" font-family="{MONO}" font-size="29" fill="{MUTED}">AGENTS.md</text>',
        f'<text x="620" y="905" font-family="{MONO}" font-size="29" fill="{MUTED}">skills</text>',
        f'<text x="980" y="905" font-family="{MONO}" font-size="29" fill="{MUTED}">hooks</text>',
        f'<text x="1320" y="905" font-family="{MONO}" font-size="29" fill="{ACCENT}">CI is policy</text>',
        f'<text x="150" y="975" font-family="{MONO}" font-size="29" fill="{MUTED}">nested per package</text>',
        f'<text x="820" y="975" font-family="{MONO}" font-size="29" fill="{MUTED}">plan before code</text>',
        f'<text x="1450" y="975" font-family="{MONO}" font-size="29" fill="{ACCENT}">author must explain</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'generation is candidate state \u2014 same rule as product agents</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">review the evidence</text>',
    ]
    return "".join(body)


def agent_guardrails() -> str:
    """Where the bottleneck moved."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">AGENTS IN A REAL REPOSITORY</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Writing code got cheap.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Believing it did not.</text>',
        node_box(150, 520, 560, 190, "produce", "anyone, any hour", "cheap"),
        node_box(700, 520, 560, 190, "review", "one human, finite", "the bottleneck", accent=True),
        node_box(1250, 520, 560, 190, "gate", "deterministic", "names the defect"),
        arrow(640, 615, 690, 615, ""),
        arrow(1190, 615, 1240, 615, ""),
        f'<line x1="150" y1="850" x2="{W - 150}" y2="850" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="925" font-family="{MONO}" font-size="28" fill="{MUTED}">build failed</text>',
        f'<text x="900" y="925" font-family="{MONO}" font-size="28" fill="{ACCENT}">suite reported 12/12</text>',
        f'<text x="150" y="978" font-family="{MONO}" font-size="28" fill="{MUTED}">token audit halved</text>',
        f'<text x="900" y="978" font-family="{MONO}" font-size="28" fill="{ACCENT}">printed ok</text>',
        f'<text x="150" y="1031" font-family="{MONO}" font-size="28" fill="{MUTED}">resume unreadable</text>',
        f'<text x="900" y="1031" font-family="{MONO}" font-size="28" fill="{ACCENT}">text layer perfect</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'ten gates \u00b7 each one exists because something got through</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">green is a claim</text>',
    ]
    return "".join(body)


def spark_committer() -> str:
    """The protocol decides whether the committer ever sees the data."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">SPARK 4.2 · HADOOP-AWS 3.5</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The batch succeeded.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Nothing was written.</text>',
        # before: default protocol bypasses the committer
        f'<text x="150" y="468" font-family="{MONO}" font-size="26" letter-spacing="3" '
        f'fill="{MUTED}">DEFAULT PROTOCOL</text>',
        node_box(150, 490, 600, 200, "task output", "newTaskTempFile", "not a FileOutputCommitter"),
        node_box(900, 490, 600, 200, "table path", "case _ => new Path(path)", "committer bypassed"),
        node_box(1650, 490, 600, 200, "pending upload", "read 9,029 · wrote 0", "never completed", accent=True),
        arrow(750, 590, 890, 590, ""),
        arrow(1500, 590, 1640, 590, ""),
        # after: PathOutputCommitProtocol routes output through magic
        f'<text x="150" y="788" font-family="{MONO}" font-size="26" letter-spacing="3" '
        f'fill="{MUTED}">PATHOUTPUTCOMMITPROTOCOL</text>',
        node_box(150, 810, 600, 200, "task output", "committer work path", "routed"),
        node_box(900, 810, 600, 200, "magic committer", "__magic_job-<id>/", "job-scoped"),
        node_box(1650, 810, 600, 200, "job commit", "upload completed", "object lands", accent=True),
        arrow(750, 910, 890, 910, ""),
        arrow(1500, 910, 1640, 910, ""),
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'no failed task · 25 rows counted · 65 uploads pending</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">count objects, not rows</text>',
    ]
    return "".join(body)


def workload_identity() -> str:
    """One ordered chain: what resolves, what is ranked below, what is left out."""

    def chain_row(y, n, title, status, accent=False, excluded=False):
        x, w, h = 820, 1430, 118
        edge = ACCENT if accent else LINE
        dash = ' stroke-dasharray="12 10"' if excluded else ""
        ink = MUTED if excluded else INK
        out = [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PANEL}" '
            f'stroke="{edge}" stroke-width="{3 if accent else 2}"{dash}/>',
            f'<text x="{x + 34}" y="{y + 74}" font-family="{MONO}" font-size="30" '
            f'fill="{ACCENT}">{n}</text>',
            f'<text x="{x + 100}" y="{y + 76}" font-family="{SERIF}" font-size="46" '
            f'font-weight="600" fill="{ink}">{escape(title)}</text>',
            f'<text x="{x + w - 34}" y="{y + 74}" font-family="{MONO}" font-size="27" '
            f'fill="{ACCENT if accent else MUTED}" text-anchor="end">{escape(status)}</text>',
        ]
        if excluded:
            out.append(
                f'<line x1="{x + 96}" y1="{y + 62}" x2="{x + 470}" y2="{y + 62}" '
                f'stroke="{MUTED}" stroke-width="3"/>'
            )
        return "".join(out)

    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">REMOVING STATIC AWS KEYS</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Delete the keys.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Find out what they were hiding.</text>',
        node_box(150, 560, 520, 330, "Spark pod", "driver + executors", "one shared chain"),
        arrow(680, 725, 800, 725, ""),
        chain_row(480, "1", "Pod Identity", "rejected: endpoint mode IPv4"),
        chain_row(618, "2", "IRSA", "resolves: token file, no host check", accent=True),
        chain_row(756, "3", "Static keys", "accepted, ranked below roles"),
        chain_row(894, "—", "Instance profile", "excluded: node role, false 403s", excluded=True),
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'Spark · Trino · Hive Metastore → IRSA</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">shared chain closed → crash at 6h49m–6h59m</text>',
    ]
    return "".join(body)


def hms_upgrade() -> str:
    """Five SUCCESS lines, zero constraints, and the script that dominates the window."""
    segs = [("3.1→3.2", 2.9), ("→4.0-α1", 6.4), ("α1→α2", 59.3), ("→β1", 6.4),
            ("→4.0", 8.4), ("→4.1", 6.7), ("→4.2", 7.5)]
    total = sum(s for _, s in segs)
    x0, span, y0, bh = 150, W - 300, 850, 90
    bars, x = [], float(x0)
    for i, (label, sec) in enumerate(segs):
        w = span * sec / total
        hot = i == 2
        bars.append(
            f'<rect x="{x:.1f}" y="{y0}" width="{w - 6:.1f}" height="{bh}" '
            f'fill="{ACCENT if hot else PANEL}" stroke="{ACCENT if hot else LINE}" stroke-width="2"/>'
        )
        if hot:
            bars.append(
                f'<text x="{x + 34:.1f}" y="{y0 + 58}" font-family="{MONO}" font-size="30" '
                f'fill="{PAPER}">4.0.0-alpha-1 → alpha-2 · 59.3 s</text>'
            )
        else:
            bars.append(
                f'<text x="{x + (w - 6) / 2:.1f}" y="{y0 + bh + 44}" font-family="{MONO}" '
                f'font-size="24" fill="{MUTED}" text-anchor="middle">{sec}</text>'
            )
        x += w
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">HIVE METASTORE 3.1 → 4.2 · CLONE REHEARSAL</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Validate said SUCCESS.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The schema had no constraints.</text>',
        node_box(150, 470, 620, 210, "-validate", "5 checks, all [SUCCESS]", "tables exist"),
        node_box(870, 470, 620, 210, "live clone", "constraints 0 · indexes 0", "reference: 133 / 48",
                 accent=True),
        node_box(1590, 470, 660, 210, "upgradeSchema", "script 1 committed", "script 2 failed"),
        arrow(780, 575, 860, 575, ""),
        arrow(1500, 575, 1580, 575, ""),
        f'<text x="150" y="815" font-family="{MONO}" font-size="26" fill="{MUTED}">'
        f'after cleanup: seven upgrade scripts, seconds, measured on the clone</text>',
        f'<text x="{W - 150}" y="815" font-family="{MONO}" font-size="26" fill="{ACCENT}" '
        f'text-anchor="end">97.6 s · wall 115 s</text>',
        *bars,
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'write stop ≈ 4 min · blue/green, rollback is a URI</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">server 4.2.1 · client 4.1.0</text>',
    ]
    return "".join(body)


def agent_remote_tools() -> str:
    """No pod owns the user. The laptop pulls."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">AGENT TOOLS ON A USER’S MACHINE</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The laptop is not a server.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">It is a queue consumer.</text>',
        node_box(150, 520, 530, 190, "agent, any pod", "XADD jobs:{user}", "no registry lookup"),
        node_box(790, 520, 560, 190, "per-user stream", "consumer group + PEL", "at-least-once", accent=True),
        node_box(1460, 520, 790, 190, "pod holding the socket", "drain 0 → read > → XAUTOCLAIM", "ack after reply"),
        node_box(1460, 800, 790, 190, "the user’s laptop", "outbound only · dedupe on key", "comes and goes"),
        node_box(150, 800, 1200, 190, "presence:{user}", "heartbeat 10 s · TTL 30 s · read by every pod",
                 "one answer cluster-wide"),
        arrow(690, 615, 780, 615, ""),
        arrow(1360, 615, 1450, 615, ""),
        arrow(1855, 720, 1855, 790, ""),
        f'<text x="1885" y="764" font-family="{MONO}" font-size="26" fill="{MUTED}">job frame</text>',
        arrow(1450, 895, 1360, 895, "", dashed=True),
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'XADD · XREADGROUP · XAUTOCLAIM · idempotency_key</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">delivered twice, executed once</text>',
    ]
    return "".join(body)


def ocr_measurement() -> str:
    """The defect looked expensive until document type was held constant."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">MEASURE THE PREMISE FIRST</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The plan said fix the photos.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The table said fix the forms.</text>',
        node_box(150, 520, 465, 190, "capture", "phone photograph", "suspected"),
        node_box(695, 520, 465, 190, "OCR", "RapidOCR · ONNX", "handwriting ceiling"),
        node_box(1240, 520, 465, 190, "parser", "label → value", "the real loss", accent=True),
        node_box(1785, 520, 465, 190, "scorer", "F0.5 · refusals", "written first"),
        arrow(620, 615, 685, 615, ""),
        arrow(1165, 615, 1230, 615, ""),
        arrow(1710, 615, 1775, 615, ""),
        f'<line x1="150" y1="850" x2="{W - 150}" y2="850" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="925" font-family="{MONO}" font-size="28" fill="{MUTED}">skew, handwritten pages only</text>',
        f'<text x="1240" y="925" font-family="{MONO}" font-size="28" fill="{MUTED}">F1 0.202 vs 0.205</text>',
        f'<text x="150" y="978" font-family="{MONO}" font-size="28" fill="{MUTED}">deskew applied, six pages</text>',
        f'<text x="1240" y="978" font-family="{MONO}" font-size="28" fill="{MUTED}">net +5 of ~3,838 chars</text>',
        f'<text x="150" y="1031" font-family="{MONO}" font-size="28" fill="{INK}">printed form filled in by hand</text>',
        f'<text x="1240" y="1031" font-family="{MONO}" font-size="28" fill="{ACCENT}">F1 0.101 vs 0.543 clean print</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'97 labelled pages · 198 real clinic captures</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">document type was the confounder</text>',
    ]
    return "".join(body)


def short_text_triage() -> str:
    """Label the string, not the row — and only past a margin."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">SHORT-TEXT TRIAGE · SYNTHETIC LAB</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Label the string, not the row.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Assign only past a margin.</text>',
        # the funnel: each box is a unit of work, the badge is what one LLM call
        # per unit would cost
        node_box(150, 500, 380, 210, "rows", "20,000 reports", "20,000 calls"),
        node_box(580, 500, 380, 210, "raw strings", "byte-distinct", "3,018 calls"),
        node_box(1010, 500, 380, 210, "keys", "NFKC + casefold", "1,537 calls"),
        node_box(1440, 500, 380, 210, "clusters", "UMAP → HDBSCAN", "125 calls", accent=True),
        node_box(1870, 500, 380, 210, "labels", "human-approved", "0 per new row"),
        arrow(535, 605, 575, 605, ""),
        arrow(965, 605, 1005, 605, ""),
        arrow(1395, 605, 1435, 605, ""),
        arrow(1825, 605, 1865, 605, ""),
        # the day-2 decision for a string the cache has never seen
        f'<text x="150" y="835" font-family="{MONO}" font-size="28" fill="{MUTED}">new string</text>',
        f'<text x="150" y="875" font-family="{MONO}" font-size="28" fill="{MUTED}">top-1 cosine s1, best other label s2</text>',
        f'<line x1="900" y1="790" x2="900" y2="1060" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="960" y="835" font-family="{MONO}" font-size="28" fill="{ACCENT}">s1 − s2 ≥ m</text>',
        f'<text x="1500" y="835" font-family="{MONO}" font-size="28" fill="{INK}">→ assigned</text>',
        f'<text x="960" y="905" font-family="{MONO}" font-size="28" fill="{ACCENT}">s1 − s2 &lt; m</text>',
        f'<text x="1500" y="905" font-family="{MONO}" font-size="28" fill="{INK}">→ review</text>',
        f'<text x="960" y="975" font-family="{MONO}" font-size="28" fill="{ACCENT}">s1 &lt; floor</text>',
        f'<text x="1500" y="975" font-family="{MONO}" font-size="28" fill="{INK}">→ outlier pool</text>',
        f'<text x="960" y="1045" font-family="{MONO}" font-size="26" fill="{MUTED}">review + outliers are re-clustered weekly</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'synthetic corpus · 5 languages · multilingual-e5-small on CPU</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">one LLM call per cluster</text>',
    ]
    return "".join(body)


def spark_kinesis_connector() -> str:
    """Two read models: one waits out every idle shard, one stops when caught up."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">SPARK-SQL-KINESIS · OPEN SOURCE</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Ten seconds per idle shard,</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">or one round trip.</text>',
        # row 1: background queue, inferred end-of-data
        f'<text x="150" y="478" font-family="{MONO}" font-size="26" letter-spacing="3" '
        f'fill="{MUTED}">DSV2 · BACKGROUND QUEUE</text>',
        node_box(150, 500, 600, 190, "publisher", "fetch into a queue", "one task per shard"),
        node_box(900, 500, 600, 190, "reader", "poll · poll · empty", "end inferred from silence"),
        node_box(1650, 500, 600, 190, "idle shard", "2 × 3 s legal minimum", "≥ 6 s, every batch"),
        arrow(750, 595, 890, 595, ""),
        arrow(1500, 595, 1640, 595, ""),
        # row 2: in-task fetch, explicit end-of-data, unchanged checkpoint
        f'<text x="150" y="788" font-family="{MONO}" font-size="26" letter-spacing="3" '
        f'fill="{MUTED}">DSV1 · IN-TASK FETCH</text>',
        node_box(150, 810, 600, 190, "task", "getRecords inline", "no queue to drain"),
        node_box(900, 810, 600, 190, "caught up", "millisBehindLatest = 0", "stop the shard", accent=True),
        node_box(1650, 810, 600, 190, "checkpoint", "offset JSON unchanged", "resume, no drain", accent=True),
        arrow(750, 905, 890, 905, ""),
        arrow(1500, 905, 1640, 905, ""),
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'read ≈ ceil(shards / slots) × floor</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">Spark 4.2 · AWS SDK v2 · Maven Central</text>',
    ]
    return "".join(body)


def agent_knowledge() -> str:
    """Five kinds of knowledge, five homes — live state is never a document."""
    rows = [
        ("Definitions", "what does it mean?", "concept file", "owner · verified_on · Disputed", False),
        ("Mappings", "which table answers it?", "semantic layer", "a Never use column", False),
        ("Conventions", "how do we query here?", "rule", "always loaded, kept short", False),
        ("Procedures", "how do I investigate?", "skill", "loaded on demand", False),
        ("Live state", "what is it right now?", "tool call", "never a document", True),
    ]
    out = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">AGENTS IN A REAL REPOSITORY · PART 3</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The agent reasoned fine.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Its definitions had no owner.</text>',
    ]
    y, h, gap = 462, 100, 18
    for kind, question, home, note, hot in rows:
        edge = ACCENT if hot else LINE
        sw = 3 if hot else 2
        out += [
            f'<rect x="150" y="{y}" width="820" height="{h}" rx="6" fill="{PANEL}" '
            f'stroke="{LINE}" stroke-width="2"/>',
            f'<text x="184" y="{y + 64}" font-family="{SERIF}" font-size="42" font-weight="600" '
            f'fill="{INK}">{escape(kind)}</text>',
            f'<text x="936" y="{y + 62}" font-family="{MONO}" font-size="25" fill="{MUTED}" '
            f'text-anchor="end">{escape(question)}</text>',
            arrow(985, y + h / 2, 1085, y + h / 2, ""),
            f'<rect x="1100" y="{y}" width="1150" height="{h}" rx="6" fill="{PANEL}" '
            f'stroke="{edge}" stroke-width="{sw}"/>',
            f'<text x="1134" y="{y + 64}" font-family="{SERIF}" font-size="42" font-weight="600" '
            f'fill="{INK}">{escape(home)}</text>',
            f'<text x="2216" y="{y + 62}" font-family="{MONO}" font-size="25" '
            f'fill="{ACCENT if hot else MUTED}" text-anchor="end">{escape(note)}</text>',
        ]
        y += h + gap
    out += [
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'one concept per file · owner · verified_on · status</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">if it changes on its own, generate it</text>',
    ]
    return "".join(out)


def alert_state() -> str:
    """Two writers, one row, and Slack called only after the commit."""
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">WAREHOUSE ALERTS · A DESIGN REVIEW</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">An alert is a state machine.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Slack only renders it.</text>',
        node_box(150, 480, 520, 200, "detector", "scheduled · stateless", "only reader of source"),
        node_box(830, 480, 700, 200, "alert_state", "(alert_id, group_key)", "state_version", accent=True),
        node_box(1690, 480, 560, 200, "Slack", "chat.update by ts", "renders, never holds"),
        node_box(1690, 780, 560, 200, "receiver", "Socket Mode · outbound", "ack within 3 s"),
        arrow(680, 580, 820, 580, "1 commit", up=True),
        arrow(1540, 580, 1680, 580, "2 post", up=True),
        arrow(1685, 860, 1440, 690, "", dashed=True),
        f'<text x="1180" y="790" font-family="{MONO}" font-size="26" fill="{MUTED}">'
        f'click → transition</text>',
        f'<text x="150" y="830" font-family="{MONO}" font-size="26" letter-spacing="3" '
        f'fill="{MUTED}">LIFECYCLE</text>',
        f'<text x="150" y="895" font-family="{MONO}" font-size="30" fill="{INK}">'
        f'OK → ACTIVE → ACKNOWLEDGED → RESOLVED</text>',
        f'<text x="240" y="950" font-family="{MONO}" font-size="30" fill="{INK}">'
        f'└───────────────→ CLOSED</text>',
        f'<text x="150" y="1015" font-family="{MONO}" font-size="26" fill="{MUTED}">'
        f'acknowledged still evaluates · closed waits for healthy</text>',
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'state before Slack · one transition function · one row</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">a design, not a measurement</text>',
    ]
    return "".join(body)


def ocr_engines() -> str:
    """Eight engines, one scorer, three verdicts — and why the best reader is off."""
    rows = [
        ("RapidOCR · PP-OCRv6", "ships", True),
        ("Tesseract 5.5", "fallback", False),
        ("docTR", "half the F1", False),
        ("LightOnOCR-1B Q4", "bands only", False),
        ("LightOnOCR-2 Q4", "weaker", False),
        ("Nanonets-OCR-s Q4", "2.6 GB weights", False),
        ("Surya 2", "≥ 4 GB · licence", False),
        ("PaddleOCR-VL 1.6", "sidecar, off", True),
    ]
    listing = []
    for i, (name, verdict, hot) in enumerate(rows):
        y = 520 + i * 66
        listing.append(
            f'<text x="150" y="{y}" font-family="{MONO}" font-size="28" '
            f'fill="{INK}">{escape(name)}</text>'
        )
        listing.append(
            f'<text x="590" y="{y}" font-family="{MONO}" font-size="26" '
            f'fill="{ACCENT if hot else MUTED}">{escape(verdict)}</text>'
        )
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">OCR ENGINE BAKE-OFF · CLINIC RECORDS</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">The best reader does not ship.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">It cannot say when it is unsure.</text>',
        *listing,
        f'<line x1="960" y1="490" x2="960" y2="995" stroke="{LINE}" stroke-width="3"/>',
        arrow(960, 740, 1020, 740, ""),
        node_box(1030, 610, 560, 260, "one scorer", "same pages · field F0.5", "only the engine changes",
                 accent=True),
        node_box(1700, 470, 550, 190, "ships", "RapidOCR · line confidence", "precision-first"),
        node_box(1700, 680, 550, 190, "fallback", "Tesseract · recall collapses", "if primary fails"),
        node_box(1700, 890, 550, 190, "off", "VL sidecar · no confidence", "~5× slower on target"),
        arrow(1600, 700, 1690, 565, ""),
        arrow(1600, 740, 1690, 775, ""),
        arrow(1600, 780, 1690, 985, ""),
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'11 + 26 labelled pages · one 17-page packet · local only</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">the scorer stays fixed</text>',
    ]
    return "".join(body)


def prevalence_shift() -> str:
    """Counted labels draw a flatter line than the world; the corrected estimate sits on it."""
    # Mean estimates by period from the lab's Scenario A (1,000 replications).
    cc = [0.0795, 0.0879, 0.0966, 0.1050, 0.1141, 0.1221, 0.1310, 0.1392, 0.1480, 0.1568, 0.1650, 0.1736]
    ppi = [0.0999, 0.1133, 0.1268, 0.1410, 0.1547, 0.1683, 0.1814, 0.1961, 0.2085, 0.2226, 0.2362, 0.2507]
    x0, x1, y0, y1, top = 260, 1320, 1040, 480, 0.30

    def px(i):
        return x0 + (x1 - x0) * i / 11

    def py(p):
        return y0 - (y0 - y1) * p / top

    def poly(vals):
        return " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vals))

    truth = [0.10 + 0.15 * i / 11 for i in range(12)]
    body = [
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="150" y="190" font-family="{MONO}" font-size="30" letter-spacing="6" '
        f'fill="{ACCENT}">QUANTIFICATION · SEEDED SIMULATION</text>',
        f'<text x="150" y="300" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Counted labels flatten a trend.</text>',
        f'<text x="150" y="382" font-family="{SERIF}" font-size="86" font-weight="600" '
        f'fill="{INK}">Prevalence has to be estimated.</text>',
        # axes and gridlines
        f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{LINE}" stroke-width="2"/>',
    ]
    for p in (0.10, 0.20, 0.30):
        body.append(f'<line x1="{x0}" y1="{py(p):.1f}" x2="{x1}" y2="{py(p):.1f}" stroke="{LINE}" '
                    f'stroke-width="1.5" stroke-dasharray="4 8"/>')
        body.append(f'<text x="{x0 - 24}" y="{py(p) + 9:.1f}" font-family="{MONO}" font-size="26" '
                    f'fill="{MUTED}" text-anchor="end">{int(p * 100)}%</text>')
    body += [
        f'<text x="{x0}" y="{y0 + 48}" font-family="{MONO}" font-size="24" fill="{MUTED}">period 1</text>',
        f'<text x="{x1}" y="{y0 + 48}" font-family="{MONO}" font-size="24" fill="{MUTED}" '
        f'text-anchor="end">period 12</text>',
        # the world
        f'<polyline points="{poly(truth)}" fill="none" stroke="{INK}" stroke-width="5"/>',
        # counted labels
        f'<polyline points="{poly(cc)}" fill="none" stroke="{MUTED}" stroke-width="5" stroke-dasharray="14 10"/>',
    ]
    # corrected estimate, as points on the true line
    for i, v in enumerate(ppi):
        body.append(f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="11" fill="{ACCENT}"/>')
    body += [
        f'<text x="{x1 - 10}" y="{py(0.25) - 34:.1f}" font-family="{MONO}" font-size="26" fill="{INK}" '
        f'text-anchor="end">true share 10% → 25%</text>',
        f'<text x="{x0}" y="{py(cc[0]) + 58:.1f}" font-family="{MONO}" font-size="26" fill="{MUTED}">'
        f'counted labels 8% → 17%</text>',
        node_box(1500, 470, 750, 190, "classify and count", "slope × 0.63 · coverage 0%",
                 "measures the classifier"),
        node_box(1500, 680, 750, 190, "adjusted (ACC)", "unbiased · coverage 95.0%",
                 "needs fresh error rates"),
        node_box(1500, 890, 750, 190, "gold-corrected (PPI)", "unbiased · 1.83× the labels",
                 "self-correcting", accent=True),
        f'<line x1="150" y1="1120" x2="{W - 150}" y2="1120" stroke="{LINE}" stroke-width="2"/>',
        f'<text x="150" y="1195" font-family="{MONO}" font-size="30" fill="{MUTED}">'
        f'1,000 replications · 12 periods · 5,000 reports + 200 labels each</text>',
        f'<text x="{W - 150}" y="1195" font-family="{MONO}" font-size="30" fill="{ACCENT}" '
        f'text-anchor="end">model upgrade: a +24% that never happened</text>',
    ]
    return "".join(body)


DIAGRAMS = {"patroni-pg18": patroni_pg18, "pgbackrest-patroni": pgbackrest_patroni,
            "lakehouse-spine": lakehouse_spine,
            "lakehouse-medallion": lakehouse_medallion,
            "lakehouse-maintenance": lakehouse_maintenance,
            "lakehouse-engines": lakehouse_engines,
            "rag-lakehouse": rag_lakehouse,
            "agent-guardrails": agent_guardrails,
            "spark-committer": spark_committer,
            "workload-identity": workload_identity,
            "hms-upgrade": hms_upgrade,
            "agent-remote-tools": agent_remote_tools,
            "ocr-measurement": ocr_measurement,
            "short-text-triage": short_text_triage,
            "spark-kinesis-connector": spark_kinesis_connector,
            "agent-knowledge": agent_knowledge,
            "alert-state": alert_state,
            "ocr-engines": ocr_engines,
            "prevalence-shift": prevalence_shift}

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
