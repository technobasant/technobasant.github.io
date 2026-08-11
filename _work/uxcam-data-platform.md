---
title: "Ten terabytes a day: the UXCam data platform"
hook: "Cron-shaped ETL → Spark on Kubernetes without a freeze window"
description: "How I moved UXCam's mobile-analytics ETL from cron-shaped batch jobs to Spark on Kubernetes at 10 TB a day, with no freeze window and a smaller bill."
kind: production
order: 1
featured: true
role: "Data Engineer, then Senior Data Engineer"
org: "UXCam"
period: "2020 – present"
team: "Small data team inside a globally distributed engineering org; US and EU stakeholders, me in Kathmandu"
scale: "10 TB+ and hundreds of millions of events a day from 25,000+ integrated mobile apps"
stack: [Apache Kafka, Amazon Kinesis, Apache Spark, PySpark, Apache Airflow, dbt, Apache Iceberg, Kubernetes, Amazon S3, Trino, Databricks, Prometheus, Grafana, OpenTelemetry]
metrics: [daily_volume, processing_speed, infra_cost, uptime]
tags: [spark, kubernetes, cost-finops]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

UXCam is a mobile product-analytics company. An SDK sits inside a customer's app and emits sessions, screens, gestures, custom events and session-replay artifacts. Those events land on our ingest edge, get shaped into tables, and come back out as funnels, retention curves, heatmaps and replays. The platform that does the shaping is what I own.

When I joined in 2020, the data layer worked the way most do before someone is paid to think about them full time. Transformation was cron-shaped: scheduled jobs on fixed EC2 capacity, sized for peak so they would not fall over at peak, idle the rest of the day. Jobs were long, sequential and mostly un-restartable — a failure at hour four meant re-running from hour zero. Failures were found by a human noticing a stale dashboard. Adding a metric meant editing a job that also computed nine others.

None of that was anyone's fault; it was a data layer that had grown as a side effect of shipping a product. But volume was compounding and the shape did not survive it. Today the same platform ingests and transforms **10 TB+ per day** — hundreds of millions of events — from **25,000+ integrated apps**, on Spark running on Kubernetes.

## Constraints

The interesting part of this project is not what I built. It is the list of things I was not allowed to do.

**No freeze window.** SDKs in tens of thousands of apps emit continuously. There is no hour of the week when global mobile usage is low enough to stop accepting data. Any cutover had to be a dual-write, not a switch.

**I could not change the producers.** The producer is an SDK compiled into an app in an app store. I cannot recall a version or ask a customer to upgrade before Tuesday. Whatever payload shape shipped in 2019 still arrives today alongside whatever shipped last month, so every downstream schema decision has to assume permanently heterogeneous input.

**The migration had to pay for itself.** There was no budget line for "modernize the data platform" — the business case was the existing spend. That ruled out running both estates at full size indefinitely and put a hard limit on the dual-write period.

**Same people, same on-call.** There was no platform SRE team to hand the result to. Whoever built it operated it. That is a strong argument against any design whose steady state requires a specialist to babysit it.

**Timezone.** I am in Kathmandu (UTC+5:45). Stakeholders are in the US and Europe. A design that requires me to be awake during the US evening for routine operations is a design that fails within a month.

**GDPR-aware retention.** Event payloads and replay artifacts can carry personal data. Deletion has to be possible, provable and bounded in time — which constrains physical layout, because you cannot pick a scheme that turns per-subject deletion into a full-table rewrite.

**Downstream contracts.** Product dashboards and internal reporting already read specific tables, and those consumers could not be rewritten in step with the pipeline. The new platform had to produce comparable output for the tables that already existed before it was allowed to produce anything new.

## Architecture

```text
              25,000+ integrated apps (SDK)
                          |
                          v
                  ingest edge (HTTPS)
                          |
            +-------------+--------------+
            v                            v
      Apache Kafka                Kinesis Data Streams
    (event firehose)            (session / replay payloads)
            |                            |
            |                            v
            |                Spark Structured Streaming
            |                  - contract checks
            |                  - dedupe on event key
            |                  - late-event windows
            |                            |
            v                            v
     Spark batch (PySpark) <-------------+
     scheduled by Airflow
     dbt for the modeled marts
                          |
                          v
        Amazon S3 + Apache Iceberg
        bronze  ->  silver  ->  gold
                          |
        +---------+-------+--------+-------------+
        v         v                v             v
      Trino   ClickHouse   Citus / TimescaleDB   Databricks
                                                 + Unity Catalog
        |         |                |             |
        +---------+-------+--------+-------------+
                          v
             product dashboards, reverse-ETL,
             internal analytics, agent tools
```

The pieces, in the order data meets them:

**Ingest.** Kafka carries the event firehose. Kinesis Data Streams carries the session and replay payloads, which have a different size distribution and failure profile. Splitting them was deliberate: a backlog in one should not stall the other.

**Streaming.** Spark Structured Streaming reads Kinesis, applies the data-quality contract (null, type, range and referential checks), deduplicates on the event key, and holds a bounded window for late arrivals. Records that fail are quarantined rather than dropped, reason attached — you can only fix what you kept.

**Batch.** PySpark jobs run the heavy transformations. Airflow schedules and sequences them; it does not do the work. dbt models the gold marts on top, where analysts read SQL rather than Spark.

**Storage.** Everything lands in S3 as Iceberg tables in a bronze/silver/gold progression — its own case study, [the Iceberg lakehouse](/work/iceberg-lakehouse-scd/).

**Compute.** Spark executors run on Kubernetes with autoscaling node pools. Batch runs on spot capacity; streaming on on-demand. Airflow, the streaming drivers and the supporting services share the cluster, so the platform is one thing to upgrade, not five.

**Serving.** Four engines read the gold layer, each matched to an access pattern — also its own case study, [the serving layer](/work/serving-layer-100m-queries/).

**Governance.** Databricks with Unity Catalog runs alongside the self-managed estate for governed sharing and lineage. RBAC, encryption in transit and at rest, and retention rules are enforced there for the datasets humans touch directly.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost us |
|---|---|---|---|
| Self-managed Spark on Kubernetes | EMR or Databricks Jobs for the whole batch estate | We already ran EKS. Most of our jobs are small, and per-job cluster provisioning wastes minutes and money on every one. Bin-packing onto shared autoscaling node pools is where the cost reduction actually came from. | We own the Spark operator, the shuffle configuration, the base images and every CVE patch. Some of our worst incidents are scheduler-level rather than data-level: the failure surface moved from "the query is wrong" to "the pod never got a node." |
| Airflow schedules; Spark does the work | Airflow operators performing transformation inline | Keeps DAGs small, restartable and cheap. Airflow workers stop being a resource bottleneck and become what they should be: a state machine. | Lineage is split across two systems. To debug you read the DAG to find the task and the Spark UI to find the failure, and nothing joins those views for you. |
| Dual-write cutover with daily reconciliation | Big-bang switch during a maintenance window | There was no maintenance window. Running old and new side by side and diffing the outputs was the only way to earn the right to turn the old one off. | Two pipelines for roughly a quarter, plus a reconciliation job that became permanent infrastructure — it is still what catches silent divergence after a refactor. |
| Tolerant readers, schema-on-read at bronze | Strict schema at the edge, reject non-conforming events | With producers we cannot recall, rejecting at the edge destroys data we can never get back. Better to accept, quarantine and repair. | Bronze is genuinely messy and every silver job carries defensive code. The quality framework stopped being a project and became a permanent component with its own maintenance cost. |
| Databricks and Unity Catalog alongside self-managed Spark, not instead of it | Move everything to Databricks | Governed sharing, lineage and RBAC are worth paying for where humans collaborate. They are not worth it on the 10 TB/day machine path, which is cost-dominated. | Two compute planes and two access-control models. When a number disagrees between them there are two places to look and no authority on which is right. |
| Spot for batch, on-demand for streaming | On-demand everywhere | Batch is retryable; a reclaimed executor costs a stage. Streaming is not, and a reclaimed executor costs a consumer-group rebalance. | Reclamation mid-shuffle is expensive, so we tuned for smaller stages and more frequent checkpoints than we would otherwise have chosen — a slightly slower happy path bought for a much better bad path. |

The most contested of these was the first. The strongest argument against self-managing Spark is that a managed service converts an operational problem into an invoice, and that a small team should always take that trade. It is a good argument and it is right for a lot of teams. It lost here for one reason: our workload is a long tail of small-to-medium jobs, and per-job cluster lifecycle dominates cost at that shape. Had it been a dozen enormous nightly jobs, I would have argued the other side.

## Results

Here is how each number above was measured.

The Spark and PySpark rewrite cut **wall-clock on the daily ETL DAG by 50%**, before and after on the same DAG, over 2021–2022. Worth stating plainly: at the time of that measurement the platform moved about 5 TB/day, not the 10 TB+/day it moves now. The percentage describes the rewrite, not the growth since.

The Kubernetes migration cut **data-infrastructure spend by 40%**, measured as before-and-after monthly spend on the data platform across the 2023 migration. That is the data-infrastructure line specifically, not the whole cloud bill. The saving came from bin-packing and autoscaling, not from a cheaper instance type.

Serving availability has held at **99.9%**, from Prometheus blackbox probes on a rolling 30-day window, 2022 to today. That is the serving endpoints. It says nothing about freshness, which is tracked as a separate SLI because "up but stale" is the failure mode that actually costs a customer something.

Current throughput is **10 TB+ per day** and hundreds of millions of events per day, from Spark job metrics and Kafka topic throughput. The event count is the number I trust more: bytes vary with payload shape and compression, events do not.

## Running it

**SLOs.** Three, in priority order. Freshness: gold tables for the previous day complete and queryable by a fixed hour, which is the SLI product actually feels. Streaming lag: p95 end-to-end lag on the Kinesis path inside a bounded window. Serving availability: 99.9% rolling 30 days. Freshness is first on purpose — a platform that is technically up but eight hours behind is down as far as its users are concerned.

**On-call.** A shared rotation, alerts routed by class rather than by service. Freshness burn-rate alerts page; individual task failures do not, because a retryable failure at 02:00 is noise. Anything that pages twice without a runbook entry gets one before the next release.

**Three failure modes we actually see:**

*Consumer lag spike after a broker restart or partition rebalance.* Symptom: streaming lag climbing with no change in input rate. Runbook: confirm the rebalance in consumer-group metrics before touching anything, because the reflex to restart the job triggers another rebalance and makes it worse. Bounded lag, wait it out. Unbounded, scale the streaming executors and let the late-arrival window absorb what follows.

*Executor OOM from partition skew.* One integrated app has a heavy day and a single partition dominates a shuffle stage. Symptom: a job that ran for months fails at the same stage. Runbook: find the skewed key in the stage metrics, confirm it is one tenant, salt that key for the run rather than raising executor memory globally. Raising memory works once and hides the problem until the next tenant does it.

*Schema drift from an SDK version.* A field that was an integer arrives as a string, or a nested field appears mid-day. Symptom: quarantine volume rising while the job stays green. Runbook: quarantine rate crossing threshold pages; read the reason codes to identify the field and app, apply the tolerant-reader coercion, replay the quarantined records. That replay path is the whole reason we quarantine instead of dropping.

## What I'd do differently

**I built the reconciliation harness during the migration, not before it.** For the first few weeks of dual-write we compared outputs by hand, which is exactly as reliable as it sounds. The harness that eventually caught the real divergences should have existed before the first Spark job reached production. A week up front, and considerably more than a week of doubt saved.

**I under-priced the operational tax of self-managing Spark.** The cost model was accurate about compute and wrong about people. Bin-packing delivered the saving I predicted; what I left out of the spreadsheet was the recurring cost of owning the operator, the images and the upgrade path. The decision still nets out positive, but I would describe it today as a cost transfer rather than a cost reduction, and I would probably put the long tail of small jobs on a managed control plane while keeping the heavy path self-managed.

**We optimized for wall-clock before cost-per-terabyte.** Those two goals point in different directions more often than you would like: the partitioning that finishes fastest is frequently not the partitioning that is cheapest. Because we measured wall-clock first, several layout decisions had to be revisited once cost-per-TB became a tracked number.
