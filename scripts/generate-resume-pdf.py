#!/usr/bin/env python3
"""Generate the privacy-safe public resume used by the website."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#15181C")
MUTED = colors.HexColor("#58616B")
ACCENT = colors.HexColor("#9A692C")
PAPER = colors.HexColor("#FCFAF5")
PANEL = colors.HexColor("#F3EEE4")
LINE = colors.HexColor("#D8D0C2")
ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "_data" / "metrics.yml"


SITE_URL = ""
SITE_HOST = ""


def site_host() -> tuple[str, str]:
    """Return (url, bare_host) from _config.yml.

    Read rather than hardcoded, for the same reason the IndexNow step reads
    CNAME: this document outlives the hostname. The old value sat in one string
    at the bottom of this file and survived a domain move, so the PDF a
    recruiter downloads would have pointed at a host that only 301s.
    """
    config = METRICS_PATH.parent.parent / "_config.yml"
    command = [
        "ruby", "-ryaml", "-rjson", "-e",
        "puts JSON.generate(YAML.safe_load_file(ARGV.fetch(0), aliases: true))",
        str(config),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    url = json.loads(result.stdout).get("url", "").rstrip("/")
    return url, url.replace("https://", "").replace("http://", "")


def load_clouds() -> list[dict]:
    """Cloud platforms and services, from the same file the site renders."""
    skills = METRICS_PATH.parent / "skills.yml"
    if not skills.exists():
        return []
    command = [
        "ruby", "-ryaml", "-rjson", "-e",
        "puts JSON.generate(YAML.safe_load_file(ARGV.fetch(0)))",
        str(skills),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout).get("clouds", [])


def load_metrics() -> dict[str, dict[str, str]]:
    """Load the shared Jekyll metrics source through Ruby's YAML parser."""
    command = [
        "ruby",
        "-ryaml",
        "-rjson",
        "-e",
        "puts JSON.generate(YAML.safe_load_file(ARGV.fetch(0)))",
        str(METRICS_PATH),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def metric(metrics: dict[str, dict[str, str]], key: str) -> str:
    """Return one approved public metric value."""
    return str(metrics[key]["value"])


# Two callbacks, and the order of each is the whole point.
#
# The background draws BEFORE the frame, because it fills the page. Run it after
# and it paints over every word — a page of perfectly extractable, perfectly
# invisible text. That is exactly what happened when this was one function moved
# to onPageEnd to fix the parse order, and neither `rake privacy` nor pypdf
# noticed, because the text layer was intact the whole time.
#
# The footer draws AFTER, because reportlab writes onPage output first into the
# content stream and pypdf extracts in stream order — so a footer drawn first
# made the site domain line one of the document and the name line three. A
# parser that treats line one as the candidate name files you under your own
# hostname. `rake resume` now asserts both properties.
def page_background(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(0.68 * inch, height - 0.47 * inch, width - 0.68 * inch, height - 0.47 * inch)
    canvas.restoreState()


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = letter
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.68 * inch, 0.38 * inch, SITE_HOST.upper())
    canvas.drawRightString(width - 0.68 * inch, 0.38 * inch, f"BASANT BHATTARAI  /  {doc.page}")
    canvas.restoreState()


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        # Left, not centred. `base["Title"]` is centre-aligned, so the name sat
        # on a different axis from every other element and the page had no spine.
        "name": ParagraphStyle(
            "Name",
            parent=base["Title"],
            alignment=TA_LEFT,
            fontName="Times-Bold",
            fontSize=25,
            leading=27,
            textColor=INK,
            spaceAfter=3,
        ),
        "role": ParagraphStyle(
            "Role",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            tracking=1.1,
            textColor=ACCENT,
            spaceAfter=7,
        ),
        "contact": ParagraphStyle(
            "Contact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=12,
            textColor=MUTED,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            tracking=1.25,
            textColor=ACCENT,
            spaceBefore=13,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.65,
            leading=12.6,
            textColor=INK,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=11.2,
            textColor=MUTED,
            spaceAfter=3,
        ),
        "job": ParagraphStyle(
            "Job",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.3,
            leading=12,
            textColor=INK,
            keepWithNext=True,
        ),
        "date": ParagraphStyle(
            "Date",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.25,
            leading=11.8,
            textColor=INK,
            leftIndent=11,
            firstLineIndent=-11,
            spaceAfter=3.5,
        ),
        "card_title": ParagraphStyle(
            "CardTitle",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=INK,
            spaceAfter=2,
        ),
        "card_body": ParagraphStyle(
            "CardBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.6,
            leading=10.6,
            textColor=MUTED,
        ),
        "note": ParagraphStyle(
            "Note",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.8,
            leading=11.3,
            textColor=MUTED,
        ),
    }


def section(label: str, s: dict[str, ParagraphStyle]) -> list:
    return [Paragraph(label.upper(), s["section"])]


def job_header(role: str, employer: str, period: str, s: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [[Paragraph(f"{role}  |  {employer}", s["job"]), Paragraph(period, s["date"])]],
        colWidths=[4.7 * inch, 1.55 * inch],
        # reportlab's Table defaults to hAlign="CENTER", so every job header was
        # centred in the frame and read as an indent the bullets below did not
        # share. The capability grid set this and the job header did not.
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return table


def bullets(items: list[str], s: dict[str, ParagraphStyle]) -> list[Paragraph]:
    # A real bullet glyph with a proper hanging indent. The hyphen read as a
    # dash in the sentence rather than a marker, and a 2pt hang is not a hang.
    return [Paragraph(f"\u2022&nbsp;&nbsp;{item}", s["bullet"]) for item in items]


def build_story(
    s: dict[str, ParagraphStyle],
    metrics: dict[str, dict[str, str]],
) -> list:
    story: list = [
        Spacer(1, 2),
        Paragraph("BASANT BHATTARAI", s["name"]),
        Paragraph("SENIOR DATA &amp; AI ENGINEER  /  PLATFORMS, DATABASES &amp; AGENTIC SYSTEMS", s["role"]),
        Paragraph(
            # Site first among the links. Location is not in the header: the
            # public pages lead with the work, not the city.
            f'<a href="{SITE_URL}/" color="#9A692C"><b>{SITE_HOST}</b></a><br/>'
            '<a href="mailto:contact@basantbhattarai.com.np" color="#58616B">contact@basantbhattarai.com.np</a> &nbsp;&nbsp;|&nbsp;&nbsp; '
            '<a href="https://www.linkedin.com/in/technobasant" color="#58616B">linkedin.com/in/technobasant</a> &nbsp;&nbsp;|&nbsp;&nbsp; '
            '<a href="https://github.com/technobasant" color="#58616B">github.com/technobasant</a>',
            s["contact"],
        ),
    ]

    story += section("Profile", s)
    story.append(Paragraph(
        f"Senior data and AI engineer with {metric(metrics, 'experience')} in software engineering, six of them owning production data platforms. Open-source first — Kafka, Spark, Iceberg, Trino, dbt and Airflow on Kubernetes — across ingestion, transformation and analytical serving, plus the databases underneath: modeling, replication, backup and recovery, upgrades. Designs and runs the agent workflows on that same stack — LangGraph, Google ADK and MCP tool servers — so model output lands as typed, reviewable rows rather than a transcript. Track record: {metric(metrics, 'professional_cost_reduction')} lower infrastructure cost, {metric(metrics, 'professional_processing_improvement')} faster processing, {metric(metrics, 'professional_analytics_delivery')} faster analytics delivery.",
        s["body"],
    ))

    # The "Core strengths" grid used to sit here, above Experience. It named six
    # categories in prose — Platform ownership, Data engineering, Database
    # lifecycle, Agentic systems, Technical leadership, Distributed work — and
    # the Capability map on page two then named four of the same six again with
    # technologies under them. The same taxonomy, twice, and the first copy cost
    # roughly a third of page one.
    #
    # Page one now runs header, profile, experience. That is the order a
    # recruiter reads in, and the most recent role starts near the top of the
    # page instead of halfway down it. The categories survive once, on page two,
    # where the prose line and the technology line finally sit together.

    story += section("Experience", s)
    story.append(job_header("Senior Data Engineer", "UXCam", "Feb 2024 - present", s))
    story += bullets([
        f"Own reliability and governance for a platform handling {metric(metrics, 'professional_platform_scale')} "
        f"and {metric(metrics, 'professional_event_volume')} events daily: freshness and latency objectives per "
        f"dataset, {metric(metrics, 'professional_uptime')} uptime, incident-ready runbooks, reviewable data "
        "contracts, and a named owner for every published table.",
        f"Design and operate the production agent workflows — LangGraph and Google ADK orchestration, MCP tool "
        f"servers, retrieval and evaluation — against the existing platform, so model output lands as typed, "
        f"provenanced rows rather than a transcript: analytics delivery "
        f"{metric(metrics, 'professional_analytics_delivery')} faster with "
        f"{metric(metrics, 'professional_manual_effort')} less analyst effort, review and fallback paths kept.",
        "Lead architecture and operational review across ingestion, transformation, storage, analytical serving, "
        "observability and recovery, without treating any single tool as the architecture.",
        "Run capacity and cost work as a design input rather than a monthly report, using storage layout, "
        "partitioning and compaction cadence as the primary levers.",
        f"Mentor {metric(metrics, 'professional_mentoring')} engineers through pairing, code review and written "
        f"design feedback; team delivery time down {metric(metrics, 'professional_team_delivery')}, with the "
        "emphasis on making system ownership transferable.",
    ], s)
    story.append(Spacer(1, 4))
    story.append(job_header("Data Engineer", "UXCam", "Feb 2020 - Feb 2024", s))
    story += bullets([
        "Built and operated batch and streaming pipelines, then took on the data models, orchestration, storage "
        "and analytical serving paths around them.",
        "Rebuilt the core ETL layer in Spark and PySpark with Airflow orchestration, cutting processing time for "
        f"{metric(metrics, 'professional_daily_processing')}/day by "
        f"{metric(metrics, 'professional_processing_improvement')} and unblocking real-time product dashboards.",
        "Made change and recovery safe by treating schema evolution, replay, late-arriving data and backfills as "
        "designed interfaces with idempotent loads and explicit watermarks, not as emergency procedures.",
        f"Tuned Trino, ClickHouse, Citus and TimescaleDB serving "
        f"{metric(metrics, 'professional_query_volume')} queries/day for a "
        f"{metric(metrics, 'professional_query_latency')} p95 latency reduction through partitioning, clustering "
        "and model redesign.",
        f"Led the Kubernetes migration of the data infrastructure: "
        f"{metric(metrics, 'professional_cost_reduction')} lower infrastructure cost, "
        f"{metric(metrics, 'professional_uptime')} uptime, and autoscaling that held under peak load.",
        "Worked across European and US time zones to turn product questions into maintainable datasets.",
    ], s)
    story.append(Spacer(1, 4))
    # KeepTogether on the short roles. The two-bullet SV Technology block was
    # split by the page break and left one line stranded at the top of page two,
    # which reads as a rendering accident rather than a layout. The long UXCam
    # blocks are deliberately not wrapped: forcing a five-bullet role to stay
    # whole would push the whole section to the next page to avoid a widow.
    tail: list = []
    tail.append(job_header("Project Leader", "SVCET, India", "2019 - 2020", s))
    tail += bullets([
        f"Led {metric(metrics, 'professional_project_team')} developers building an intelligent dialogue system "
        "on an NLP and deep-learning stack, reaching the client's acceptance threshold for intent recognition and "
        f"delivering {metric(metrics, 'professional_project_delivery')} ahead of schedule.",
        "Coordinated requirements, planning and review across academic and industry stakeholders, and introduced "
        "the code-review and version-control discipline the department kept afterwards.",
    ], s)
    story.append(KeepTogether(tail))
    story.append(Spacer(1, 3))
    tail2: list = [job_header("Software Developer", "SV Technology, India", "2017 - 2019", s)]
    tail2 += bullets([
        f"Built Python and FastAPI backend services carrying "
        f"{metric(metrics, 'professional_backend_users')} users at "
        f"{metric(metrics, 'professional_test_coverage')} test coverage.",
        "Designed and maintained PostgreSQL schemas, stored procedures and reporting paths, and set up CI with "
        "Jenkins alongside the early pipeline work that moved me into data engineering.",
    ], s)
    story.append(KeepTogether(tail2))

    # No forced page break here any more. It existed to give the Independent work
    # panel a clean page; with that section gone it stranded 124 words on page 2.
    story += section("Capability map", s)
    categories = [
        (
            "Platform ownership",
            "Python and SQL; Kafka ingestion; Spark/PySpark processing; Airflow orchestration; Iceberg, dbt and "
            "lakehouse modeling; Kubernetes, Docker and Terraform delivery; contracts, lineage, cost and recovery.",
        ),
        (
            "Database lifecycle",
            "PostgreSQL, ClickHouse, Trino, Citus, TimescaleDB, Redis and MongoDB; transactional and analytical "
            "modeling, partitioning, replication, backup, restore, high availability and query performance.",
        ),
        (
            "Agentic systems",
            "LangGraph, LangChain, Google ADK, MCP servers, Pydantic, Milvus and MLflow; bounded tools, retrieval, "
            "evaluation before rollout, typed output, provenance, human review and honest fallback paths.",
        ),
        (
            "Technical leadership",
            "Architecture and operational review, mentoring, incident-ready runbooks, service and freshness "
            "objectives, observability with Prometheus and Grafana, and distributed delivery across time zones.",
        ),
    ]
    # Cloud belongs in the document. It was absent entirely — no AWS, GCP or
    # Azure anywhere — which is a real gap rather than a stylistic one: cloud is
    # a standard recruiter and ATS filter, and skills.yml has carried the list
    # the whole time. Read from there so it cannot drift from the site.
    clouds = load_clouds()
    if clouds:
        categories = list(categories) + [(
            "Cloud",
            "  |  ".join(f"<b>{c['name']}:</b> {', '.join(c['items'][:8])}" for c in clouds),
        )]

    # One line of what the category means, then the systems it runs on. Splitting
    # those across two sections meant a reader had to hold the first to make
    # sense of the second.
    blurbs = {
        "Platform ownership": "Consumer-facing reliability, governance, recovery and operational readiness.",
        "Database lifecycle": "Modeling, replication, failover, backup and PITR, upgrades and query performance.",
        "Agentic systems": "Model output that lands as typed, reviewable rows rather than a transcript.",
        "Technical leadership": "Design review, mentoring, runbooks, and making system ownership transferable.",
    }
    categories = [
        (label, f'<font color="#5D646D">{blurbs[label]}</font><br/>{body}' if label in blurbs else body)
        for label, body in categories
    ]

    for label, body in categories:
        story.append(KeepTogether([
            Paragraph(label, s["card_title"]),
            Paragraph(body, s["body"]),
        ]))

    story += section("Education and languages", s)
    story.append(Paragraph("Bachelor of Technology in Computer Science and Engineering", s["job"]))
    story.append(Paragraph("JNTUA College of Engineering, Anantapur, India  |  2015 - 2019", s["small"]))
    story.append(Paragraph("English: C1  |  Nepali: native", s["body"]))

    # The link stays; the disclosure-boundary paragraph does not. A document that
    # explains what it withholds draws attention to the withholding, and a
    # recruiter reading a CV is not the audience for a disclosure policy.
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f'<a href="{SITE_URL}/work/" color="#9A692C"><b>Selected work, writing and case studies: {SITE_HOST}/work/</b></a>',
        s["body"],
    ))
    return story


def generate(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    global SITE_URL, SITE_HOST
    SITE_URL, SITE_HOST = site_host()
    metrics = load_metrics()
    doc = BaseDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.68 * inch,
        leftMargin=0.68 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.58 * inch,
        title="Basant Bhattarai - Senior Data and AI Engineer",
        author="Basant Bhattarai",
        subject="Senior Data & AI Engineer",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="resume")
    # `onPageEnd`, not `onPage`. reportlab runs onPage *before* the frame draws,
    # so the running footer landed first in the content stream — and pypdf, which
    # extracts in stream order and is what a great many ATS and document
    # pipelines use, returned the site domain as line 1 and the name as line 3.
    # Any parser taking the first line as the candidate name files you under your
    # own hostname. pdftotext reads visually and never showed it, which is why
    # this needs two parsers to catch.
    doc.addPageTemplates([PageTemplate(
        id="resume", frames=[frame], onPage=page_background, onPageEnd=page_footer
    )])
    doc.build(build_story(styles(), metrics))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=Path("output/pdf/basant-bhattarai-resume.pdf"))
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
