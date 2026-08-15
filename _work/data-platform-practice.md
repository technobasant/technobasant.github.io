---
title: "Rebuilding a production data platform for scale and recovery"
hook: "A six-year platform story: faster processing, lower cost, safer change, and recovery designed before the incident."
description: "How I rebuilt core processing, led a Kubernetes migration, evolved the lakehouse boundary, and made recovery a designed path."
date: 2020-02-01
last_modified_at: 2026-08-15
kind: practice
order: 1
featured: true
role: "Data Engineer → Senior Data Engineer"
org: "UXCam"
period: "2020 – present"
team: "Global team, working US and EU hours"
scale: "Production mobile-analytics workloads across ingestion, processing, storage, and analytical serving"
problem: "Processing and serving had to scale without making schema change, replay, cost, or on-call work progressively less safe."
decision: "Rebuild the core processing path, move orchestration onto Kubernetes, and make contracts, ownership, and replay part of the platform interface."
flow: platform
metrics: [professional_processing_improvement, professional_cost_reduction, professional_uptime, professional_query_latency]
stack: [Python, SQL, "Apache Spark", "Apache Kafka", "Apache Airflow", dbt, "Apache Iceberg", PostgreSQL, ClickHouse, Trino, Kubernetes, Prometheus, Grafana]
tags: [data-quality, observability-slo, iceberg-lakehouse]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

The platform sits downstream of producers it cannot control. Payloads drift, old clients keep sending, late data arrives after a partition looks complete, and a successful job can still publish an empty or misleading dataset. At this scale, the technical problem is not merely moving bytes. It is keeping every boundary understandable while volume, schemas, consumers, and cost all change.

## My role

I grew from pipeline delivery into end-to-end system ownership: processing, orchestration, storage layout, the databases underneath serving, observability, recovery, and the design reviews connecting them. I led the core ETL rebuild and Kubernetes migration, set reliability and governance expectations, and mentored engineers so the operating model did not depend on one person.

## Constraints

- **Uncontrolled producers.** The platform must accept old and new payload shapes without silently changing meaning.
- **Correct and on time.** Fresh wrong data and correct late data are both product failures.
- **Replay under pressure.** Backfills and late arrivals must be routine paths, not bespoke incident work.
- **Cost follows data design.** Partitioning, compaction, and retention decisions move the bill before instance tuning does.
- **A small team owns a broad surface.** Every added engine creates another upgrade, backup, and on-call obligation.

## Architecture and operating model

The path is intentionally legible: ingest events, validate and govern them at a clear storage boundary, serve models designed around real read paths, and preserve a recovery route that can replay without duplicating state.

The processing layer moved to Spark/PySpark with Airflow orchestration. Lakehouse tables used explicit partition and schema-evolution rules instead of letting each job invent them. Kubernetes provided a common scheduling and scaling boundary. PostgreSQL, Trino, ClickHouse, Citus, and TimescaleDB were operated as part of the same system: query shape, data layout, replication, and recovery—not infrastructure knobs treated in isolation.

Reliability was defined at the dataset boundary. The meaningful signal is event time to queryable, measured per dataset with a named owner—not whether a DAG turned green.

## Decisions and rejected alternatives

| Decision | Alternative rejected | Why | Cost accepted |
|---|---|---|---|
| Validate at the governed write boundary | Scatter checks through every job | One enforceable contract and one place to quarantine failures | Quarantine queues require ownership |
| Make loads idempotent with explicit watermarks | Treat replay as an incident procedure | Backfills converge on the same state | More write amplification and stricter keys |
| Evolve schemas additively with dated deprecation | Coordinate breaking renames | Consumers can migrate without a synchronized release | Temporary duplicate fields |
| Design tables around read paths | Scale infrastructure first | Layout removes more work than larger clusters hide | More up-front modeling |
| Standardize scheduling on Kubernetes | Keep workload-specific deployment paths | One capacity and operating model across the platform | Migration and platform learning cost |
{: .case-decisions aria-label="Data platform decisions and rejected alternatives" }

## Outcomes

- Core processing for {{ site.data.metrics.professional_daily_processing.value }} per day became **{{ site.data.metrics.professional_processing_improvement.value }} faster**.
- The Kubernetes migration and capacity work reduced infrastructure cost by **{{ site.data.metrics.professional_cost_reduction.value }}** while sustaining **{{ site.data.metrics.professional_uptime.value }} uptime**.
- Serving-path redesign reduced p95 latency by **{{ site.data.metrics.professional_query_latency.value }}** across {{ site.data.metrics.professional_query_volume.value }} analytical queries per day.
- Ownership, contracts, freshness objectives, and runbooks made failures attributable and recovery transferable rather than dependent on memory.

## Recovery model

Replay is a first-class interface: stable keys, explicit watermarks, partitions that can be replaced without touching neighbours, and a record of rejected input with the reason attached. Runbooks state the decision points and validation queries, not only commands. A person returning months later should be able to tell what is safe to rerun and what result proves recovery.

## Reflection

I would instrument consumers earlier. I have often known a dataset's freshness better than whether anyone still depended on it. Consumer evidence makes retention and deprecation decisions much easier.

I would also write the runbook before the first incident and remove tools sooner. Every engine is a permanent operational obligation. Some of the strongest architecture decisions are deletions.

The [multi-engine failover lab](/work/multi-engine-ha-lab/) is where I keep testing the recovery half of this practice on hardware I control.
