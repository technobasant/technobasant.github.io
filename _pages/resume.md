---
title: Résumé
seo_title: "Basant Bhattarai Résumé — Senior Big Data & Agentic AI Engineer"
eyebrow: Career
headline: "Nine years across big data pipelines, platforms, and production AI systems."
hero_code: "CAREER / LOG"
page_class: page-resume
permalink: /resume/
description: "Senior Data & AI Engineer across Spark/PySpark, Kafka, Airflow, lakehouse architecture, distributed serving, and governed agentic AI systems."
redirect_from:
  - /experience/
  - /skills/
---

<p class="page-actions"><a class="btn btn--primary" href="{{ '/assets/basant-bhattarai-resume.pdf' | relative_url }}">Download the PDF</a> <a class="btn btn--ghost" href="{{ '/work/' | relative_url }}">Read the case studies</a> <a class="btn btn--link" href="mailto:{{ site.author.email }}">Email Basant</a></p>

<div class="resume-proof" aria-label="Selected professional outcomes">
  {% assign proof_keys = "professional_platform_scale,professional_event_volume,professional_uptime,professional_cost_reduction" | split: "," %}
  {% for key in proof_keys %}
    {% assign proof = site.data.metrics[key] %}
    <div class="resume-proof__item">
      <strong>{{ proof.value }}</strong>
      <span>{{ proof.label }}</span>
    </div>
  {% endfor %}
</div>

## Experience at a glance

| Role | Period | Scope |
|---|---|---|
| Senior Data Engineer, UXCam | 2024 – present | Big-data platform and agentic AI reliability, governance, architecture review, and technical leadership |
| Data Engineer, UXCam | 2020 – 2024 | Spark batch and streaming pipelines, orchestration, lakehouse storage, analytical serving, and operations |
| Project Leader, SVCET | 2019 – 2020 | Planning and delivery of an NLP dialogue-system project with a small team |
| Software Developer, SV Technology | 2017 – 2019 | Python backend services, PostgreSQL schema work, reporting, and CI |

## Senior Data Engineer · UXCam

**February 2024 – present** · Working with a global team

- Own reliability and governance for a {{ site.data.metrics.professional_platform_scale.value }} platform processing {{ site.data.metrics.professional_event_volume.value }} events daily, with {{ site.data.metrics.professional_uptime.value }} uptime, explicit service objectives, incident-ready runbooks, and reviewable data contracts.
- Build production agentic AI workflows where model output becomes governed product state: typed schemas, provenance, retrieval, evaluation, bounded tools, and honest fallback paths.
- Delivered {{ site.data.metrics.professional_analytics_delivery.value }} faster analytics workflows with {{ site.data.metrics.professional_manual_effort.value }} less manual effort while retaining review and fallback paths.
- Mentor {{ site.data.metrics.professional_mentoring.value }} engineers through pairing, code review, and written design feedback; team delivery time improved {{ site.data.metrics.professional_team_delivery.value }}.

## Data Engineer · UXCam

**February 2020 – February 2024**

- Rebuilt core Spark/PySpark processing for {{ site.data.metrics.professional_daily_processing.value }} per day, improving processing time by {{ site.data.metrics.professional_processing_improvement.value }}.
- Made schema evolution, replay, late data, and backfills designed interfaces with idempotent loads and explicit watermarks.
- Reduced p95 query latency by {{ site.data.metrics.professional_query_latency.value }} across {{ site.data.metrics.professional_query_volume.value }} analytical queries per day through partitioning, clustering, and model redesign.
- Led a Kubernetes migration that lowered infrastructure cost by {{ site.data.metrics.professional_cost_reduction.value }} while sustaining {{ site.data.metrics.professional_uptime.value }} uptime.

## Capability map
{: #skills }

<ol class="principle-list capability-map is-wide">
  <li>
    <h3>Platform ownership</h3>
    <p>Batch and streaming ingestion, Spark/PySpark processing, Airflow orchestration, Iceberg and dbt modeling, Kubernetes capacity, contracts, lineage, and cost. <a href="/work/data-platform-practice/">Evidence: production platform case study</a>.</p>
  </li>
  <li>
    <h3>Database reliability</h3>
    <p>PostgreSQL, ClickHouse, Trino, Citus, TimescaleDB, Redis, and MongoDB across modeling, partitioning, replication, backup, recovery, and query performance. <a href="/work/multi-engine-ha-lab/">Evidence: measured failover lab</a>.</p>
  </li>
  <li>
    <h3>Agentic AI systems</h3>
    <p>Production agent workflows with typed outputs, provenance, retrieval, evaluation, bounded tools, human review, tracing, and fallback paths using Python, Pydantic, LangGraph, LangChain, MCP, Milvus, and MLflow. <a href="/work/governed-ai-delivery/">Evidence: governed AI case study</a>.</p>
  </li>
  <li>
    <h3>Technical leadership</h3>
    <p>Architecture review, mentoring, runbooks, incident readiness, and distributed delivery. The goal is transferable ownership: a system the team can operate and change without depending on one person.</p>
  </li>
</ol>

## Education and languages

**Bachelor of Technology, Computer Science and Engineering** — JNTUA College of Engineering, Anantapur, India, 2015–2019.

English: C1 · Nepali: native

## Contact

[{{ site.author.email }}](mailto:{{ site.author.email }}) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [GitHub](https://github.com/technobasant)
