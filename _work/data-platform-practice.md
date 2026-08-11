---
title: "Running a data platform people can depend on"
hook: "Contracts at the boundary, freshness as an objective, replay as a designed path, one named owner per dataset"
description: "How I approach data-platform ownership: contracts at the boundary, freshness as an objective, replay as a designed path, and one named owner per dataset."
kind: practice
order: 1
featured: true
role: "Senior Data Engineer"
org: "UXCam"
period: "2020 – present"
team: "Global team, working US and EU hours"
scale: "Mobile analytics, six years of platform ownership"
stack: [Python, SQL, "Apache Spark", "Apache Kafka", "Apache Airflow", dbt, "Apache Iceberg", PostgreSQL, ClickHouse, Trino, Kubernetes, Prometheus, Grafana]
tags: [data-quality, observability-slo, iceberg-lakehouse]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

Data platforms fail differently from services. A service that breaks pages someone. A dataset that breaks stays silent, keeps serving, and is discovered three weeks later by an analyst who no longer trusts anything. Most of what follows exists to shorten that gap.

The other structural fact is that a data platform sits downstream of producers it does not control. In a mobile-analytics product the producer is an SDK embedded in applications shipped by other companies, on versions they choose to keep. You cannot reject a bad producer and you cannot make it upgrade. That single constraint drives more design than any other.

## Constraints I design against

- **Producers I cannot control or reject.** Old SDK versions keep sending. Payload shapes drift without notice. Backfills arrive out of order.
- **Correctness matters more than latency, until it doesn't.** Nobody thanks you for fresh wrong numbers, but a correct dataset that lands too late for the morning review is also a failure.
- **The bill is a design constraint, not a report.** Storage layout and compaction cadence move cost more than instance choice does, and both are schema decisions.
- **Small team, broad surface.** Anything that only I can operate is a liability, not an achievement.

## The method

### Contracts at the boundary, tolerant readers behind it

Validate at the point data enters a governed store, not scattered through the pipeline. Null, type, range and referential checks at the load boundary; quarantine rather than drop, because a rejected record you cannot inspect is a bug you cannot fix. Behind that boundary, read tolerantly — unknown fields pass through rather than failing the batch.

The trade-off: quarantine tables need an owner and a review habit, or they silently become a landfill. I have seen that happen.

### Freshness as a stated objective, not a job-success metric

"Did the job succeed" is the wrong question. A DAG can go green while emitting an empty partition. The signal worth alerting on is **event time to queryable**, measured per dataset, at a percentile, with a stated window — and an objective that someone agreed to.

The trade-off: per-dataset objectives are real work to define and real work to keep honest. The alternative is an alert nobody trusts, which is worse than no alert.

### Replay and backfill as designed interfaces

Treat re-running as a first-class path, not an incident procedure. Idempotent loads, explicit watermarks, and partitions you can rewrite without touching neighbours. If a backfill requires a person to reason carefully at 2 a.m., the design is incomplete.

The trade-off: idempotency costs write amplification and some schema rigidity. Worth it every time.

### One named owner per dataset

Not a team — a person. An unowned dataset is an outage with a delay fuse. Ownership means the freshness objective, the quarantine queue, the schema changes, and the cost line.

### Schema evolution planned in advance of needing it

Additive by default. Renames go through a period where both names exist. Deprecation has a date and a consumer list, and the list is derived from lineage rather than memory.

## What I would do differently

**Instrument the consumers earlier.** I have repeatedly known the freshness of a dataset better than I knew whether anyone was reading it. Retention and deprecation arguments are easy when you can name the consumers and hard when you cannot.

**Write the runbook before the first incident, not after the second.** The version written calmly is materially better than the version written at 2 a.m., and the difference persists for years.

**Be slower to add a tool and faster to delete one.** Every engine in the estate is a version-upgrade obligation, a backup story and an on-call surface. Some of the best decisions I have made were removals.

## Related writing

The [failover lab](/work/multi-engine-ha-lab/) is where I test the recovery half of this — six engines, eight injected faults, on hardware I control.
