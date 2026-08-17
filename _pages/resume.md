---
title: Résumé
last_modified_at: 2026-08-17
seo_title: "Basant Bhattarai — Senior Data & AI Engineer résumé"
eyebrow: Career
headline: "Nine years across data platforms, databases, and production agentic systems."
hero_code: "CAREER / LOG"
page_class: page-resume
permalink: /resume/
description: "Nine years across data platforms, database lifecycle operations, system architecture, and agentic systems in production. Roles, measured outcomes, and the stack behind each."
redirect_from:
  - /experience/
  - /skills/
---

<p class="page-actions"><a class="btn btn--primary" href="{{ '/assets/basant-bhattarai-resume.pdf' | relative_url }}">Download the PDF</a> <a class="btn btn--ghost" href="{{ '/work/' | relative_url }}">Read the case studies</a> <a class="btn btn--link" href="{{ '/hire/#hire-form' | relative_url }}">Send a briefing</a></p>

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
| Senior Data Engineer, UXCam | 2024 – present | Owns platform reliability and governance, the database layer beneath it, and the production agent workflows; architecture review and mentoring |
| Data Engineer, UXCam | 2020 – 2024 | Built the batch and streaming processing, the lakehouse models, and the multi-engine serving layer |
| Project Leader, SVCET | 2019 – 2020 | Planning and delivery of an NLP dialogue-system project with a small team |
| Software Developer, SV Technology | 2017 – 2019 | Python backend services, PostgreSQL schema work, reporting, and CI |

## Senior Data Engineer · UXCam

**February 2024 – present** · Working with a global team

- Own reliability and governance for a {{ site.data.metrics.professional_platform_scale.value }} platform processing {{ site.data.metrics.professional_event_volume.value }} events daily, with {{ site.data.metrics.professional_uptime.value }} uptime, explicit service objectives, incident-ready runbooks, reviewable data contracts, and a named owner for every published table.
- Operate the database layer the platform depends on: clustering and replication, backup and recovery, access control, query and index tuning, and upgrade windows across SQL and NoSQL engines.
- Design and operate the production agent workflows — LangGraph and Google ADK orchestration, MCP tool servers, retrieval and evaluation — wired into the existing platform so model output lands as typed, provenanced rows rather than a transcript. Analytics delivery {{ site.data.metrics.professional_analytics_delivery.value }} faster with {{ site.data.metrics.professional_manual_effort.value }} less analyst effort, with review and fallback paths kept in place.
- Lead architecture and schema reviews before new stores, pipelines, and agent workflows reach production; mentor {{ site.data.metrics.professional_mentoring.value }} engineers through pairing, code review, and written design feedback; team delivery time improved {{ site.data.metrics.professional_team_delivery.value }}.

## Data Engineer · UXCam

**February 2020 – February 2024**

- Rebuilt core Spark/PySpark processing for {{ site.data.metrics.professional_daily_processing.value }} per day, improving processing time by {{ site.data.metrics.professional_processing_improvement.value }}.
- Administered distributed SQL and NoSQL stores used for serving and product state—modeling, partitioning, replication, and query plans rather than treating the database as a black box.
- Made schema evolution, replay, late data, and backfills designed interfaces with idempotent loads and explicit watermarks.
- Reduced p95 query latency by {{ site.data.metrics.professional_query_latency.value }} across {{ site.data.metrics.professional_query_volume.value }} analytical queries per day through partitioning, clustering, and model redesign.
- Led a Kubernetes migration of the data and database infrastructure that lowered cost by {{ site.data.metrics.professional_cost_reduction.value }} while sustaining {{ site.data.metrics.professional_uptime.value }} uptime.

## Capability map
{: #skills }

<ol class="principle-list capability-map is-wide">
  <li>
    <h3>Data platforms</h3>
    <p>Batch and streaming ingestion, Spark/PySpark processing, Airflow orchestration, Iceberg and dbt modeling, Kubernetes capacity, contracts, lineage, and cost. <a href="/work/data-platform-practice/">Evidence: production platform case study</a>.</p>
  </li>
  <li>
    <h3>Database lifecycle</h3>
    <p>PostgreSQL, ClickHouse, Trino, Citus, TimescaleDB, Redis, MongoDB, and MySQL/MariaDB across modeling, HA, replication, backup and PITR, upgrades, access control, and query performance. <a href="/work/multi-engine-ha-lab/">Evidence: measured failover lab</a>.</p>
  </li>
  <li>
    <h3>Agentic systems</h3>
    <p>Production agents on LangGraph, LangChain, Google ADK and MCP tool servers: bounded tools, retrieval, evaluation before rollout, typed output, and a fallback path that fails honestly. Built against the platform already running. <a href="/work/governed-ai-delivery/">Evidence: governed AI case study</a>.</p>
  </li>
  <li>
    <h3>System architecture</h3>
    <p>Application boundaries, schema design, dual OLTP/OLAP stores, typed contracts, and recovery paths a product can actually replay. FastAPI, PostgreSQL, ClickHouse, and the service layers between them. <a href="/work/clickhomes/">Evidence: independent product case study</a>.</p>
  </li>
</ol>

## The stack

{% include skill-tiers.html %}

## Education and languages

**Bachelor of Technology, Computer Science and Engineering** — JNTUA College of Engineering, Anantapur, India, 2015–2019.

English: C1 · Nepali: native

## Contact

[contact@basantbhattarai.com.np](mailto:contact@basantbhattarai.com.np) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [GitHub](https://github.com/technobasant)
