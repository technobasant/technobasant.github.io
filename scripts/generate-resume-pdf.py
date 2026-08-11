#!/usr/bin/env python3
"""Generate the privacy-safe public resume used by the website."""

from __future__ import annotations

import argparse
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


def build_story(s: dict[str, ParagraphStyle]) -> list:
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
        "Senior data and AI engineer with nine years in software engineering, from Python backend services and PostgreSQL schemas to production data platforms, database reliability, and governed AI workflows. I focus on the seams that decide whether a system remains trustworthy: data contracts, observability, replay, recovery, and typed boundaries for automated decisions.",
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
        "Own reliability and governance outcomes across production data and AI-assisted workflows, including clear service expectations and incident-ready runbooks.",
        "Design typed, validated, traceable boundaries before automated output can change another product workflow.",
        "Lead architecture and operational reviews across processing, storage, serving, observability, and recovery.",
        "Mentor engineers through pairing and review, with an emphasis on transferable ownership and clear decisions.",
    ], s)
    story.append(Spacer(1, 4))
    story.append(job_header("Data Engineer", "UXCam", "Feb 2020 - Feb 2024", s))
    story += bullets([
        "Built and operated batch and streaming pipelines, then expanded into data modeling, orchestration, storage, and analytical serving.",
        "Improved change and recovery safety by designing for schema evolution, replay, late data, and backfills.",
        "Tuned processing and query workloads by starting with access patterns, measurement, and data layout.",
    ], s)
    story.append(Spacer(1, 4))
    story.append(job_header("Project Leader", "SVCET, India", "2019 - 2020", s))
    story += bullets(["Led a small team delivering an NLP dialogue-system project across academic and industry stakeholders."], s)
    story.append(Spacer(1, 3))
    story.append(job_header("Software Developer", "SV Technology, India", "2017 - 2019", s))
    story += bullets(["Built Python backend services, PostgreSQL schemas and reports, and contributed to CI and early pipeline work."], s)

    story.append(PageBreak())
    story += section("Independent work", s)
    independent = Table(
        [[
            [Paragraph("ClickHomes - personal product", s["card_title"]), Paragraph("Founder and sole engineer. Public evidence includes 90+ versioned SQL migrations and a documented approach to contracts, idempotency, schema evolution, and reviewable AI-assisted decisions.", s["card_body"])],
            [Paragraph("Multi-engine HA lab", s["card_title"]), Paragraph("Eight reproducible failover scenarios on hardware I control. Published results include PostgreSQL 18 replay-lag and Redis Sentinel promotion measurements, with the rig and limitations stated.", s["card_body"])],
        ]],
        colWidths=[3.11 * inch, 3.11 * inch],
    )
    independent.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(independent)

    story += section("Technical practice", s)
    categories = [
        ("Programming", "Python, SQL, Bash; application and automation work with modern JavaScript/TypeScript stacks."),
        ("Data processing", "Apache Spark / PySpark, Kafka, Airflow, dbt, Iceberg, streaming and change-data-capture patterns."),
        ("Databases", "PostgreSQL, ClickHouse, Trino; production or lab work with Redis, MongoDB, Citus, TimescaleDB, ScyllaDB, MariaDB/Galera, and SolrCloud."),
        ("AI systems", "LangGraph, LangChain, CrewAI, Google-ADK, MCP, Pydantic, retrieval, evaluation, provenance, and structured-output design."),
        ("Infrastructure", "Kubernetes, Docker, Terraform, Helm, GitHub Actions, Prometheus, Grafana, OpenTelemetry."),
        ("Cloud", "Hands-on delivery across AWS, GCP, and Azure services for data, compute, storage, orchestration, and AI workloads."),
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

    story += section("Public disclosure boundary", s)
    story.append(Paragraph(
        "This public resume names employers and responsibilities but intentionally excludes employer architecture, customer information, operating scale, security posture, and internal performance figures. Independent metrics refer only to personal work with a stated measurement method.",
        s["note"],
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        '<a href="https://technobasant.github.io/resume/" color="#9A692C"><b>Full public resume and evidence: technobasant.github.io/resume/</b></a>',
        s["body"],
    ))
    return story


def generate(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.68 * inch,
        leftMargin=0.68 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.58 * inch,
        title="Basant Bhattarai - Privacy-safe public resume",
        author="Basant Bhattarai",
        subject="Senior Data & AI Engineer",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="resume")
    doc.addPageTemplates([PageTemplate(id="resume", frames=[frame], onPage=page_chrome)])
    doc.build(build_story(styles()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=Path("output/pdf/basant-bhattarai-resume.pdf"))
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
