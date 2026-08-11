#!/usr/bin/env python3
"""Generate the privacy-safe public resume used by the website."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
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


def page_chrome(canvas, doc) -> None:
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.2)
    canvas.line(0.68 * inch, height - 0.47 * inch, width - 0.68 * inch, height - 0.47 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.68 * inch, 0.38 * inch, "TECHNOBASANT.GITHUB.IO")
    canvas.drawRightString(width - 0.68 * inch, 0.38 * inch, f"BASANT BHATTARAI  /  {doc.page}")
    canvas.restoreState()


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "Name",
            parent=base["Title"],
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
            leftIndent=9,
            firstLineIndent=-7,
            spaceAfter=2.5,
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
    )
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return table


def bullets(items: list[str], s: dict[str, ParagraphStyle]) -> list[Paragraph]:
    return [Paragraph(f"- {item}", s["bullet"]) for item in items]


def build_story(
    s: dict[str, ParagraphStyle],
    metrics: dict[str, dict[str, str]],
) -> list:
    story: list = [
        Spacer(1, 2),
        Paragraph("BASANT BHATTARAI", s["name"]),
        Paragraph("SENIOR DATA & AI ENGINEER  /  DATA PLATFORM & DATABASE SYSTEMS", s["role"]),
        Paragraph(
            'Kathmandu, Nepal &nbsp;&nbsp;|&nbsp;&nbsp; '
            '<a href="mailto:technobasant9@gmail.com" color="#58616B">technobasant9@gmail.com</a> &nbsp;&nbsp;|&nbsp;&nbsp; '
            '<a href="https://www.linkedin.com/in/technobasant" color="#58616B">linkedin.com/in/technobasant</a> &nbsp;&nbsp;|&nbsp;&nbsp; '
            '<a href="https://github.com/technobasant" color="#58616B">github.com/technobasant</a>',
            s["contact"],
        ),
    ]

    story += section("Profile", s)
    story.append(Paragraph(
        f"Senior data and AI engineer with {metric(metrics, 'experience')} in software engineering, six of them owning production data platforms. Open-source first — Kafka, Spark, Iceberg, Trino, dbt and Airflow on Kubernetes — across ingestion, transformation and analytical serving, with the governance, observability and reliability that production data products demand. Also ships production AI systems and administers the databases underneath them. Track record: {metric(metrics, 'professional_cost_reduction')} lower infrastructure cost, {metric(metrics, 'professional_processing_improvement')} faster processing, {metric(metrics, 'professional_analytics_delivery')} faster analytics delivery.",
        s["body"],
    ))

    strengths = [
        ("Platform ownership", "Consumer-facing reliability, governance, recovery, and operational readiness."),
        ("Data engineering", "Batch and streaming pipelines, orchestration, modeling, and change-safe processing."),
        ("Database systems", "Transactional and analytical modeling, replication, recovery, and performance work."),
        ("Governed AI", "Structured output, provenance, evaluation, bounded tools, and human review paths."),
        ("Technical leadership", "Design review, mentoring, runbooks, and making system ownership transferable."),
        ("Distributed work", "Long-term collaboration across European and US time zones from Kathmandu."),
    ]
    cells = []
    for index in range(0, len(strengths), 2):
        row = []
        for title, body in strengths[index:index + 2]:
            row.append([Paragraph(title, s["card_title"]), Paragraph(body, s["card_body"])])
        cells.append(row)
    grid = Table(cells, colWidths=[3.11 * inch, 3.11 * inch], hAlign="LEFT")
    grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += section("Core strengths", s) + [grid]

    story += section("Experience", s)
    story.append(job_header("Senior Data Engineer", "UXCam", "Feb 2024 - present", s))
    story += bullets([
        f"Own reliability and governance for a platform handling {metric(metrics, 'professional_platform_scale')} "
        f"and {metric(metrics, 'professional_event_volume')} events daily: freshness and latency objectives per "
        f"dataset, {metric(metrics, 'professional_uptime')} uptime, incident-ready runbooks, reviewable data "
        "contracts, and a named owner for every published table.",
        "Design the boundary where automated output becomes product state — typed schemas validated at the load "
        "edge, provenance on every generated record, evaluation before rollout, and a fallback path that degrades "
        "honestly rather than guessing.",
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
    story.append(job_header("Project Leader", "SVCET, India", "2019 - 2020", s))
    story += bullets([
        f"Led {metric(metrics, 'professional_project_team')} developers building an intelligent dialogue system "
        "on an NLP and deep-learning stack, reaching the client's acceptance threshold for intent recognition and "
        f"delivering {metric(metrics, 'professional_project_delivery')} ahead of schedule.",
        "Coordinated requirements, planning and review across academic and industry stakeholders, and introduced "
        "the code-review and version-control discipline the department kept afterwards.",
    ], s)
    story.append(Spacer(1, 3))
    story.append(job_header("Software Developer", "SV Technology, India", "2017 - 2019", s))
    story += bullets([
        f"Built Python and FastAPI backend services carrying "
        f"{metric(metrics, 'professional_backend_users')} users at "
        f"{metric(metrics, 'professional_test_coverage')} test coverage.",
        "Designed and maintained PostgreSQL schemas, stored procedures and reporting paths, and set up CI with "
        "Jenkins alongside the early pipeline work that moved me into data engineering.",
    ], s)

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
            "Database reliability",
            "PostgreSQL, ClickHouse, Trino, Citus, TimescaleDB, Redis and MongoDB; transactional and analytical "
            "modeling, partitioning, replication, backup, restore, high availability and query performance.",
        ),
        (
            "Governed AI delivery",
            "Pydantic, LangGraph, LangChain, MCP, Milvus and MLflow; structured output, provenance, retrieval, "
            "evaluation, bounded tools, human review and honest fallback paths.",
        ),
        (
            "Technical leadership",
            "Architecture and operational review, mentoring, incident-ready runbooks, service and freshness "
            "objectives, observability with Prometheus and Grafana, and distributed delivery across time zones.",
        ),
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
        '<a href="https://technobasant.github.io/" color="#9A692C"><b>Selected work, writing and case studies: technobasant.github.io</b></a>',
        s["body"],
    ))
    return story


def generate(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
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
    doc.addPageTemplates([PageTemplate(id="resume", frames=[frame], onPage=page_chrome)])
    doc.build(build_story(styles(), metrics))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=Path("output/pdf/basant-bhattarai-resume.pdf"))
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
