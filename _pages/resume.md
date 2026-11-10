---
title: Résumé
last_modified_at: 2026-11-10
seo_title: "Basant Bhattarai — Senior Data Engineer · AI Engineer · Data & AI Architect résumé"
eyebrow: Career
headline: "Senior Data Engineer · AI Engineer · Data & AI Architect — 9+ years in industry, nearly 7 full-time."
hero_code: "CAREER / LOG"
lede: "From backend services and PostgreSQL schemas to owning the architecture of a data platform handling 100M+ events a day: its data model, databases, governance and SOC 2 controls, and the AI built into it."
page_class: page-resume
permalink: /resume/
description: "Senior Data Engineer, AI Engineer and Data & AI Architect: 9+ years in industry, nearly 7 full-time. Roles, measured outcomes, and the stack behind each."
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

## Profile

Senior data engineer and data and AI architect with 9+ years in industry, nearly 7 of them full-time. I set the target architecture, choose platforms on measured evidence, design the data model with the governance and SOC 2 controls around it, then lead the build: Kafka, Spark, Iceberg, Trino, dbt and Airflow on Kubernetes, the databases underneath, and AI built into the platform with isolation, evaluation and review designed in. My current title is Senior Data Engineer at UXCam, where I led the move from an OLTP warehouse to an Iceberg lakehouse and design the agentic AI platform built into it. I am open to Senior or Lead Data Engineer, AI Engineer and Data & AI Architect roles, long-term contract or full-time. I work remotely from Kathmandu, Nepal, with teams in the US and Europe.

## Experience at a glance

| Role | Period | Scope |
|---|---|---|
| Senior Data Engineer, UXCam | 2024 – present | Platform architecture, reliability, governance and SOC 2; the database layer beneath it; the agentic AI and LLM video-analysis platforms; architecture review and mentoring |
| Data Engineer, UXCam | 2020 – 2024 | Moved analytics from an OLTP warehouse to an Iceberg lakehouse; rebuilt the Spark processing; led the Kubernetes migration; tuned the multi-engine serving layer |
| Project Leader and Research Developer, SVCET | 2018 – 2019 | Final-year research: a deep-learning dialogue system in TensorFlow, with a team of four |
| Software Developer Intern (part-time), SV Technology | 2017 – 2019 | Python backend services in Flask and Django, PostgreSQL schema work, reporting, and CI |

## Senior Data Engineer · UXCam

**February 2024 – present** · California, US and Berlin, Germany · remote from Kathmandu, Nepal

- Own the architecture, reliability, data quality and governance of a {{ site.data.metrics.professional_platform_scale.value }} platform processing {{ site.data.metrics.professional_event_volume.value }} events daily, with {{ site.data.metrics.professional_uptime.value }} uptime, explicit service objectives, monitoring and alerting, incident-ready runbooks, reviewable data contracts, and a named owner for every published table; responsible for meeting the SOC 2 criteria for the data platform and its infrastructure through every audit.
- Operate the database layer the platform depends on: clustering and replication, backup and recovery, access control, query and index tuning, and upgrade windows across SQL and NoSQL engines.
- Design and build the agentic AI platform — RAG pipelines, MCP servers, and LangGraph and Google ADK agent workflows with evaluation — built into the existing platform so model output lands as typed, provenanced rows rather than a transcript. Analytics delivery {{ site.data.metrics.professional_analytics_delivery.value }} faster with {{ site.data.metrics.professional_manual_effort.value }} less analyst effort, with review and fallback paths kept in place.
- Designed and built an LLM-based video-analysis platform that processes videos at high daily volume.
- Lead architecture and schema reviews before new stores, pipelines, and agent workflows reach production; mentor {{ site.data.metrics.professional_mentoring.value }} engineers through pairing, code review, and written design feedback; team delivery time improved {{ site.data.metrics.professional_team_delivery.value }}.

## Data Engineer · UXCam

**February 2020 – February 2024** · California, US and Berlin, Germany · remote from Kathmandu, Nepal

- Led the move from an OLTP data warehouse to an Iceberg lakehouse for analytics: Iceberg tables with partition and schema-evolution rules, and a producer and consumer that queue and run Spark compaction jobs on small files, keeping analytical queries fast.
- Rebuilt core Spark/PySpark processing for {{ site.data.metrics.professional_daily_processing.value }} per day, improving processing time by {{ site.data.metrics.professional_processing_improvement.value }}.
- Administered distributed SQL and NoSQL stores used for serving and product state—modelling, partitioning, replication, and query plans rather than treating the database as a black box.
- Made backfills and replays safe to re-run: idempotent loads, explicit watermarks for late data, and schema evolution designed in.
- Reduced p95 query latency by {{ site.data.metrics.professional_query_latency.value }} across {{ site.data.metrics.professional_query_volume.value }} analytical queries per day through partitioning, clustering, and model redesign.
- Led a Kubernetes migration of the data and database infrastructure, Spark clusters included, that lowered cost by {{ site.data.metrics.professional_cost_reduction.value }}, with autoscaling that held under peak load.

## Project Leader and Research Developer · SVCET, JNTU Anantapur

**November 2018 – March 2019** · Final-year research project

- Built an intelligent dialogue system on deep learning and NLP: a sequence-to-sequence model of two recurrent neural networks in TensorFlow and Python, trained on movie-dialogue and Twitter corpora, with a Flask web interface for interacting with it. Led {{ site.data.metrics.professional_project_team.value }} developers and delivered {{ site.data.metrics.professional_project_delivery.value }} ahead of schedule.

## Software Developer Intern · SV Technology

**2017 – 2019** · Part-time, during the degree

- Built Python backend services in Flask and Django serving {{ site.data.metrics.professional_backend_users.value }} users, at {{ site.data.metrics.professional_test_coverage.value }} test coverage.
- Designed and maintained PostgreSQL schemas, stored procedures and reporting paths, and set up CI with Jenkins: the start of the move into data engineering.

## Selected projects

- **Database scale-out and migration.** Postgres scaled out to Citus as workloads outgrew one server, including [an application database and a pgvector store](/work/postgres-scale-out-citus/); an RDS Postgres database moved to a self-managed Citus cluster; a ClickHouse cluster designed to its workload.
- **Reliability and cost.** PostgreSQL and TimescaleDB clusters with replication, pgBackRest backups and PgPool-II pooling; a database recovered from its raw files; [a capacity plan, a managed-or-self-run decision, and an RDS and Aurora fleet tuned and failover-tested](/work/postgres-on-rds/); AWS database spend analysed for savings.
- **Data platforms and AI.** [An analytics lakehouse on S3, Trino, Airflow and Glue](/work/contact-centre-lakehouse/), handed over running with access control, HA and DR; frameworks for LLM applications and agentic workflows, from the architecture to tested Python; [a production classifier that was failing, rebuilt](/work/consulting-short-text-and-alerting/) on a Databricks lakehouse around the unit of work.

## Selected open source

- **Reference architectures**, published in full: [data-platform-architecture](/work/data-platform-architecture/), a SaaS company leaving Postgres — the current state measured, 18 decision records, a Kimball data model, governance and SOC 2 readiness, a cost model and a proof of concept on Databricks; and [ai-platform-architecture](/work/ai-platform-architecture/), its usage assistant, with tenant isolation, accuracy and cost measured on three models and Genie.
- **[spark-sql-kinesis](https://github.com/technobasant/spark-sql-kinesis)** — maintainer of a Kinesis source and sink for Spark 4.2 on AWS SDK v2, published to Maven Central; an idle shard costs one `GetRecords` call instead of a multi-second floor per batch.
- **[evalproof](/work/evalproof/)** — LLM evaluation as measurement: judge calibration, and CI gates that fail only on drops that are both large and significant (paired McNemar and bootstrap).
- **[governed-agent](/work/governed-agent/)** — a LangGraph and MCP agent whose answers become state only after schema, policy, grounding and, where required, a person.
- **[distributed-db-lab](/work/distributed-db-lab/)** — Citus sharding, online rebalance and tenant isolation, measured against TimescaleDB and a replicated ClickHouse cluster.
- Also [data-stack-lab](/work/data-stack-lab/), [streaming-platform](/work/streaming-platform/), [realtime-ml](/work/realtime-ml/), [retrieval-bench](/work/retrieval-bench/), [dataset-registry](/work/dataset-registry/) and [platform-deployments](/work/platform-deployments/), each with its method and measurements in the repository.
- Upstream: a report that led Citus to support unnamed constraints on distributed tables, [citusdata/citus#4776](https://github.com/citusdata/citus/issues/4776) (shipped in 11.2); a minimal reproduction and an offered patch for [citusdata/citus#7333](https://github.com/citusdata/citus/issues/7333); an opt-in early-stop option for [awslabs/spark-sql-kinesis-connector](https://github.com/awslabs/spark-sql-kinesis-connector/pull/99) (in review).

## Capability map
{: #skills }

<ol class="principle-list capability-map is-wide">
  <li>
    <h3>Data &amp; AI architecture</h3>
    <p>Target architectures and platform selection on criteria fixed in advance; conceptual to physical data modelling; Kimball stars with Type 2 history; Iceberg and Delta, ClickHouse and Citus layouts; open data contracts checked in CI; C4 diagrams and decision records; SOC 2 controls and GDPR erasure designed into the model; AI built into the platform, with tenant isolation outside the model, a semantic layer and a release gate; cost models over 36 months. Evidence: <a href="/work/data-platform-architecture/">a reference architecture</a> and <a href="/work/ai-platform-architecture/">its AI stage</a>; <a href="/writing/choosing-where-the-data-lives/">the decision guide</a>.</p>
  </li>
  <li>
    <h3>Data platforms</h3>
    <p>Batch and streaming ingestion, Spark/PySpark processing, Airflow orchestration, Iceberg and dbt modelling, Kubernetes capacity, contracts, lineage, and cost. Databricks: a production classifier rebuilt on a lakehouse, a proof of concept on Unity Catalog under OpenTofu, and AI/BI Genie evaluated against three models. Evidence: <a href="/work/data-platform-practice/">production platform case study</a>; <a href="/work/streaming-platform/">exactly-once streaming, measured</a>.</p>
  </li>
  <li>
    <h3>AI engineering</h3>
    <p>Production agents on LangGraph, LangChain, Google ADK and MCP tool servers: prompt and structured-output design, bounded tools, retrieval, evaluation before rollout, typed output, and a fallback path that fails honestly. Built into the platform already running. Evidence: <a href="/work/governed-ai-delivery/">governed AI case study</a>; <a href="/work/governed-agent/">governed-agent</a> and <a href="/work/evalproof/">evalproof</a>, measured in public.</p>
  </li>
  <li>
    <h3>Database lifecycle</h3>
    <p>PostgreSQL, ClickHouse, Trino, Citus, TimescaleDB, Redis, MongoDB, and MySQL/MariaDB across modelling, HA, replication, backup and PITR, upgrades, access control, and query performance. Evidence: <a href="/work/distributed-db-lab/">Citus sharding and rebalance lab</a>; <a href="/work/multi-engine-ha-lab/">measured failover lab</a>.</p>
  </li>
</ol>

## The stack

{% include skill-tiers.html %}

## Education and languages

**Bachelor of Technology, Computer Science and Engineering** — JNTU Anantapur (SVCET, an autonomous affiliated college), India, 2015–2019.

English: C1 · Nepali: native

## Contact

Kathmandu, Nepal · remote, with US and EU teams

[contact@basantbhattarai.com.np](mailto:contact@basantbhattarai.com.np) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [GitHub](https://github.com/technobasant)
