---
title: Résumé
eyebrow: Career
headline: "Nine years from backend systems to data and AI platforms."
hero_code: "CAREER / LOG"
page_class: page-resume
permalink: /resume/
description: "Nine years in software, six in production data engineering: platform ownership, database reliability, governed AI delivery, leadership, and evidence for every major claim."
redirect_from:
  - /experience/
  - /skills/
---

<p><a class="btn btn--primary" href="{{ '/assets/basant-bhattarai-resume.pdf' | relative_url }}">Download PDF</a></p>

## Career shape

A résumé lists what I did. This is the part it cannot show: what changed about the job.

- **2017–2019 · SV Technology, India.** Backend APIs in Python and the PostgreSQL schemas underneath them. I learned that most bugs reported as API bugs are data-model bugs wearing a costume.
- **2019–2020 · SVCET, India.** Led four developers on an NLP dialogue system. First time I was accountable for an estimate that was not mine.
- **2020–2022 · UXCam, Data Engineer.** I wrote pipelines. The brief was to make the numbers arrive: rebuild the ETL layer in Spark, orchestrate it with Airflow, keep the DAG green.
- **2022–2024 · UXCam, Data Engineer.** The brief widened to storage, serving and cost — Iceberg underneath, query engines in front, then the migration onto Kubernetes. Making the numbers arrive stopped being enough; they had to stay correct and stay affordable.
- **Feb 2024 · UXCam, Senior Data Engineer.** Took the platform end to end — ingestion, transformation, serving, governance, and the pager that comes with all four.
- **2024–2026 · UXCam, Senior Data Engineer.** Built and now own the AI layer on top of the platform, under the same rule as everything below it: agent output lands in typed, validated tables or it does not ship.
{: .career-timeline }

## Scope

| Role | Years | What I owned | Team | Systems under management |
|---|---|---|---|---|
| Senior Data Engineer, UXCam | 2024 – present | The data platform end to end, plus the agent layer built on it | IC; mentor to {{ site.data.metrics.mentored.value }} engineers | Kafka → Spark on self-managed Kubernetes at {{ site.data.metrics.daily_volume.value }}/day, Iceberg, dbt + Airflow, Trino and ClickHouse serving, Databricks + Unity Catalog, Milvus. {{ site.data.metrics.apps.value }} integrated apps upstream. |
| Data Engineer, UXCam | 2020 – 2024 | Ingestion, transformation, and the serving layer in front of them | IC on the data team | Spark/PySpark, Airflow, Iceberg, Kinesis, Trino, ClickHouse, Citus, TimescaleDB, AWS and EKS. |
| ClickHomes — Founder & Lead Engineer | 2024 – present | All of it, alone: schema, pipelines, backend, frontend, deploys | Solo | PostgreSQL (OLTP) and ClickHouse (OLAP), FastAPI, Celery, Next.js, Docker on a VPS. |
| Multi-engine HA lab — personal | 2026 | The test plan, the rig, and the write-up | Solo | MongoDB, ScyllaDB, SolrCloud, MariaDB + Galera, Redis, PostgreSQL 18, on one host. |
| Project Leader, SVCET | 2019 – 2020 | Delivery of an NLP dialogue system | 4 developers | Python NLP and deep-learning stack. |
| Software Developer (Backend & Data), SV Technology | 2017 – 2019 | Backend APIs and the PostgreSQL schemas behind them | IC | Python, FastAPI, PostgreSQL, Jenkins. |

## Senior Data Engineer · UXCam

**February 2024 – present** · Kathmandu, working with a global team

- A data platform can be fully up and still be wrong, which makes availability the wrong first SLI. I gave every published dataset a freshness and latency objective with a named owner, wired burn-rate alerts to Prometheus and Grafana, and put contract checks directly on the streaming path — {{ site.data.metrics.data_quality.value }} {{ site.data.metrics.data_quality.label }}, with serving holding {{ site.data.metrics.uptime.value }} availability. [How the platform is put together](/work/uxcam-data-platform/)
- Recurring analytics questions across {{ site.data.metrics.apps.value }} integrated apps queued behind a small analyst team. Rather than put a chat box in front of the warehouse, I built a multi-agent platform (Google-ADK, LangGraph, CrewAI, MCP) whose tools write structured, validated rows into governed tables — {{ site.data.metrics.analytics_delivery.value }} {{ site.data.metrics.analytics_delivery.label }} and {{ site.data.metrics.analyst_effort.value }} {{ site.data.metrics.analyst_effort.label }}. [The agent platform in detail](/work/app-analytics-agent-platform/)
- Session video was the largest corpus in the product and the only one nobody could query. I built a RAG ingest path on Milvus with metadata filters, a chunking strategy tied to session structure, and a retention policy so the index does not grow without bound — {{ site.data.metrics.videos.value }} {{ site.data.metrics.videos.label }}. [Retrieval design and trade-offs](/work/app-analytics-agent-platform/)

## Data Engineer · UXCam

**February 2020 – February 2024** · Kathmandu

- The core ETL had grown into a set of one-off jobs that no longer fit the volume. I rebuilt it in Spark and PySpark under Airflow orchestration, then moved the whole data estate off fixed instances onto self-managed Kubernetes with autoscaling — {{ site.data.metrics.processing_speed.value }} {{ site.data.metrics.processing_speed.label }} on the daily DAG, and a {{ site.data.metrics.infra_cost.value }} {{ site.data.metrics.infra_cost.label }}. [The rebuild and the migration](/work/uxcam-data-platform/)
- On the old table layout a schema change was a migration project and a late-arriving correction meant rewriting history. I moved storage to Apache Iceberg with slowly-changing-dimension patterns, snapshot expiry and a compaction cadence — multi-petabyte tables, schema evolution that does not break downstream marts, and {{ site.data.metrics.storage_cost.value }} {{ site.data.metrics.storage_cost.label }}. [Iceberg and SCD at petabyte scale](/work/iceberg-lakehouse-scd/)
- Product dashboards were reading straight off the lake, so p95 was set by whatever the largest concurrent scan happened to be. I split serving by access pattern across Trino, ClickHouse, Citus and TimescaleDB and redesigned the models and partitioning behind each — {{ site.data.metrics.query_volume.value }} {{ site.data.metrics.query_volume.label }} at a {{ site.data.metrics.query_latency.value }} {{ site.data.metrics.query_latency.label }}. [Why four engines instead of one](/work/serving-layer-100m-queries/)

## Alongside the day job

### ClickHomes — a personal project

**2024 – present** · [clickhomes.ai](https://clickhomes.ai)

- Real-estate listing feeds arrive dirty, late and in vendor-specific shapes, and every shortcut around that becomes permanent. I made a RESO transformation pipeline mandatory — connector, transformer, gold loader, no raw bypass — with Pydantic validation at every load boundary and {{ site.data.metrics.clickhomes_migrations.value }} versioned {{ site.data.metrics.clickhomes_migrations.label }} behind it. [The build](/work/clickhomes/)
- A single database would have forced a choice between slow listing search and unsafe operational writes, so I refused the choice: PostgreSQL for transactional records, ClickHouse for listings and market analytics, with LLM output persisted as typed operational rows rather than disposable chat. [Dual OLTP/OLAP design](/work/clickhomes/)

### Multi-engine HA lab

**2026** · personal

- Vendor documentation describes failover; it does not tell you how long it takes on hardware you can afford. I wrote a test plan and ran it against six database engines on a single host — {{ site.data.metrics.lab_scenarios.value }} {{ site.data.metrics.lab_scenarios.label }}, PostgreSQL 18 streaming replay lag of {{ site.data.metrics.lab_pg_replay_lag.value }}, Redis Sentinel promotion in {{ site.data.metrics.lab_redis_promotion.value }}. [Every measurement, and the rig](/work/multi-engine-ha-lab/)

## Before data engineering

**Project Leader, SVCET**, India, 2019–2020 — led four developers building an intelligent dialogue system on an NLP and deep-learning stack, reaching {{ site.data.metrics.intent_recognition.value }} {{ site.data.metrics.intent_recognition.label }} against the client's acceptance threshold. Coordinated requirements and sprint planning across academic and industry stakeholders, and delivered two weeks ahead of schedule.

**Software Developer (Backend & Data), SV Technology**, India, 2017–2019 — Python and FastAPI services carrying {{ site.data.metrics.api_users.value }} {{ site.data.metrics.api_users.label }} at {{ site.data.metrics.test_coverage.value }} {{ site.data.metrics.test_coverage.label }}, PostgreSQL schema design and reporting procedures, Jenkins CI, and the first pipeline work that pulled me toward data engineering for good.

## Skills
{: #skills }

{{ site.data.skills.note }}

### {{ site.data.skills.tier1.heading }}

{{ site.data.skills.tier1.blurb }}

| Technology | Since | At what scale | Evidence |
|---|---|---|---|
{% for item in site.data.skills.tier1.items -%}
{%- assign ev = site.work | where: "url", item.evidence | first -%}
| {{ item.name }} | {{ item.since }} | {{ item.scale }} | [{% if ev %}{{ ev.title }}{% else %}{{ item.evidence | remove: "/work/" | remove: "/" | replace: "-", " " }}{% endif %}]({{ item.evidence }}) |
{% endfor %}

### {{ site.data.skills.tier2.heading }}

{{ site.data.skills.tier2.blurb }}
{% for group in site.data.skills.tier2.groups %}
**{{ group.name }}**{% for i in group.items %} <span class="chip">{{ i }}</span>{% endfor %}
{% endfor %}
**Clouds**{% for cloud in site.data.skills.clouds %} <span class="chip">{{ cloud.name }}: {{ cloud.items | join: ", " }}</span>{% endfor %}

### {{ site.data.skills.tier3.heading }}

{{ site.data.skills.tier3.blurb }}

<small>{{ site.data.skills.tier3.items | join: ", " }}.</small>
{: .tier3-list }

## Education, languages, availability

B.Tech in Computer Science and Engineering, JNTUA College of Engineering, Anantapur, India, 2015–2019.

English C1. Nepali native.

Based in Kathmandu, working {{ site.data.availability.coverage }}.

{{ site.data.availability.headline }} at {{ site.data.availability.hours }} — details and what I turn down are on [Work with me](/hire/). Updated {{ site.data.availability.updated | date: "%B %-d, %Y" }}.

<p><a class="btn btn--primary" href="{{ '/assets/basant-bhattarai-resume.pdf' | relative_url }}">Download PDF</a> <a class="btn btn--ghost" href="/work/">Read the case studies</a></p>
