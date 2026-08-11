---
title: "Four engines, 100M+ queries a day"
hook: "Four query engines, 100M+ queries a day, and the schema decisions that made them fast"
description: "Trino, ClickHouse, Citus and TimescaleDB serving 100M+ queries a day: partition keys, tenant sharding, materialized views, and a 50% p95 latency cut."
kind: production
order: 4
featured: false
role: "Data Engineer"
org: "UXCam"
period: "2022 – 2024"
team: "Owned by me, with the product engineers who write against these engines as the people I had to keep honest"
scale: "100M+ queries a day across four engines, serving dashboards for 25,000+ integrated apps"
stack: [Trino, ClickHouse, Citus, TimescaleDB, PostgreSQL, Apache Iceberg, Apache Spark, Amazon S3, Prometheus, Grafana]
metrics: [query_volume, query_latency]
tags: [clickhouse, postgres, distributed-databases]
image: /assets/og/og-default-v2.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

Every number a UXCam customer sees comes out of one of four engines. Trino serves ad-hoc and federated queries against the Iceberg gold tables. ClickHouse serves the high-cardinality dashboard aggregates. Citus serves the app-scoped, multi-tenant workload where each query belongs to exactly one tenant. TimescaleDB serves the time-series rollups. Together they handle **100M+ queries a day**.

The first thing to understand about that number is where the queries come from. They are not analysts typing SQL. The overwhelming majority are machine-generated: a dashboard panel opens and fires a dozen queries, a scheduled report fans out across an account's apps, a product surface polls for a counter. This changes the optimization problem completely. Human queries are diverse and infrequent and you tune the engine. Machine queries are repetitive and constant and you tune the *shape of the data*, because the same twenty query templates account for most of the volume and each one of them will run a million times.

By 2023 the serving layer had grown the way these things grow: each engine had been added for a good reason at the time, each had accumulated tables shaped by whoever needed them first, and p95 latency had drifted to the point where dashboard panels felt slow. The work in this case study is the repartitioning and model redesign that took **50% off p95 query latency**, and the decisions about which engine owns which workload that made the four-engine estate defensible rather than accidental.

## Constraints

**I could not consolidate onto one engine.** This is the constraint people push back on hardest, so it is worth being precise. Trino's value is federation and scanning cold Iceberg data cheaply; it is not built for a p95 of tens of milliseconds on a dashboard panel. ClickHouse is superb at exactly that, and awkward at per-tenant isolation with thousands of tenants and frequent small writes. Citus gives single-shard routing when every query carries a tenant key — a completely different physical problem. Consolidating means picking one and losing the others.

**I could not rewrite the callers.** Queries come from product code owned by other teams, from scheduled jobs, and from the agent platform's tool layer. Whatever I did had to make existing queries faster without asking anyone to rewrite them.

**No maintenance window that mattered.** Dashboards are used continuously across every timezone, so repartitioning years of data had to happen behind a read path that stayed up.

**Latency budget, not throughput budget.** Nobody complains about a dashboard's throughput; they complain that a panel took four seconds. The target was p95 rather than p50, because the median was already fine and was not what people were feeling.

**Tenant skew is a fact, not a bug.** The largest integrated apps generate orders of magnitude more data than the median. Any design assuming an even distribution across 25,000+ tenants is wrong on day one.

**Same small team, same on-call.** Four engines means four upgrade paths, four failure-mode sets and four query-log formats — a real cost carried by few people, which constrained how exotic any individual engine's configuration was allowed to get.

## Architecture

```text
             Iceberg gold tables on S3 (see the lakehouse case)
                                |
        +-----------+-----------+-----------+------------+
        |           |                       |            |
        v           v                       v            v
     Trino      ClickHouse              Citus       TimescaleDB
   federated    dashboard             multi-tenant   time-series
   + ad-hoc     aggregates            app-scoped     rollups
     scans                            reads/writes

   Trino          ClickHouse             Citus          TimescaleDB
   ------         ----------             -----          -----------
   reads Iceberg  MergeTree              sharded by     hypertables,
   directly,      ORDER BY               app_id         continuous
   no copy        (app_id, day, event)   (tenant),      aggregates
                  PARTITION BY day       single-shard
   federation     materialized views     routing
   across         for the top panels     hot tenants
   sources                               pinned to
                  TTL is the only        dedicated
                  sanctioned delete      nodes

        +-----------+-----------+-----------+------------+
                                |
                                v
              product dashboards · scheduled reports ·
              reverse-ETL · agent platform tool layer

   concurrency control: per-engine query queues, capped
   observability: engine query logs -> Prometheus -> Grafana
```

**Trino** reads the Iceberg gold tables in place. Nothing is copied for it. Its job is the query that touches a lot of cold data or joins across sources, and it is deliberately not on the interactive dashboard path.

**ClickHouse** carries the dashboard aggregate workload. The tables are MergeTree with `ORDER BY (app_id, day, event)` and day-level `PARTITION BY`. That ordering is not arbitrary: it matches the dominant predicate shape of the dashboard queries, which always filter by app, almost always filter by a date range, and often filter by event. Matching the ordering key to the predicate shape is the single most consequential decision in a ClickHouse deployment, and it is very hard to change later.

**Citus** handles the multi-tenant workload, sharded on `app_id`. Because every query in this workload carries the tenant key, the coordinator can route to a single shard rather than scatter-gathering. The largest tenants are pinned to their own nodes, because tenant sharding without a hot-tenant escape hatch is just a slower way to have a hot spot.

**TimescaleDB** holds the time-series rollups as hypertables with continuous aggregates.

**Materialized views** in ClickHouse pre-compute the panels that dominate read volume. A small number of query templates account for most of the queries, so pre-computing them converts a large read cost into a small, predictable write cost.

**Concurrency is capped and queued** on every engine rather than autoscaled. A queued query is slower. A thrashing cluster is down. That is the trade, made explicitly.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost us |
|---|---|---|---|
| Keep four engines, each matched to an access pattern | Consolidate everything onto ClickHouse | Each workload maps to a genuinely different physical layout: federated cold scans, dense per-tenant aggregates, single-shard tenant routing, time-series rollups. Consolidation loses at least two of those properties. | Four upgrade paths, four failure modes, four query-log formats, four sets of alerts. This is the single largest ongoing cost in the estate and I would not defend it for a smaller team. |
| Repartition the underlying data to match the dominant predicate | Add indexes and tune the engines | The scan was the cost. Matching physical layout to predicate shape moves latency by a factor no amount of engine tuning matches, and it required no caller changes. | A rewrite of years of history behind a live read path — plus a permanent asymmetry: any query that does *not* use the dominant predicate is now slower. We made the common case fast by making the uncommon case worse. |
| Shard Citus by `app_id` (tenant), not by time | Time-based sharding | Every query in that workload is app-scoped, so tenant sharding gives single-shard routing. Time sharding would scatter-gather every query. | Skew. The biggest apps make hot shards, which forced us to build tenant pinning and rebalancing — machinery a time-sharded design would not need. |
| ClickHouse `ORDER BY (app_id, day, event)` with day-level partitions | Finer partitioning, or an ordering key led by time | Fewer, larger parts keeps merges cheap and matches how dashboards actually filter. Leading with `app_id` makes per-app scans read a contiguous range. | Mutations and deletes became expensive enough that TTL expiry is the only sanctioned way to remove data. Deleting a slice outside the TTL policy is a project, not a query. |
| Materialized views for the top dashboard panels | Compute everything on read | A small set of query templates dominates read volume. Pre-computing them is the cheapest latency win available and the only one that scales with tenant count rather than data volume. | Every new panel needs a view plus a backfill. The MV set became a dependency graph to schedule and monitor — a second pipeline pretending to be a schema. |
| Cap concurrency and queue | Autoscale the engines under load | A predictable queue beats an unpredictable cluster. Autoscaling a stateful analytical engine under a query flood usually makes the flood worse first. | Tail latency for the heaviest queries got worse, and we had to tell stakeholders that on purpose. Right trade, uncomfortable conversation. |

The consolidation argument keeps coming back and it deserves a fair hearing, because the people making it are not wrong about the cost. Their case: four engines is four things to patch, four ways to get paged, and a new engineer needs months to be useful on all of them, whereas one engine with more nodes is boring and boring is good. I agree with all of that. Where I disagree is the assumption that one engine can hold all four access patterns without one becoming a special case worse than a separate system. Every time I have modeled it, the consolidated version keeps the operational simplicity and loses either federation or per-tenant routing, and both are load-bearing.

## Results

The serving estate handles **100M+ queries a day**, taken from engine-side query counters across Trino, ClickHouse, Citus and TimescaleDB over 2023–2024. That is a sum across four engines and it counts machine-generated queries, which is most of them — I would not present it as a measure of human analytical activity, because it isn't one.

Repartitioning and model redesign delivered a **50% reduction in p95 query latency**, measured from the engines' own query logs, before and after, in 2023. p95 rather than p50 is deliberate: the median was acceptable before the work started, and the tail is what users experience as "the dashboard is slow." The gains came from three sources — layout matching the dominant predicate, materialized views absorbing the highest-volume panels, and single-shard routing on the tenant workload — and I cannot cleanly split the credit between them, because they were deployed close enough together that the measurement windows overlap. That is an honest limitation of the number.

## Running it

**SLOs.** p95 latency per engine, tracked separately, because one aggregate hides a sick engine behind three healthy ones. Query error rate split by class — user error and resource exhaustion mean completely different things and should never share a graph. Queue depth per engine, the leading indicator that predicts the latency SLO breaking about ten minutes before it does.

**On-call.** Shared platform rotation. Latency burn-rate alerts page; individual slow queries do not — they go to a weekly review where the top offenders by total time consumed get looked at properly. That review has produced more durable latency improvement than any individual incident.

**Three failure modes we actually see:**

*One tenant's query saturates ClickHouse memory.* A single expensive query — usually a wide date range with no app filter, from a caller who did not know better — exhausts memory and takes concurrent queries with it. Symptom: a cluster-wide error spike traceable to one query ID. Runbook: kill the query, identify the caller, then set a per-user memory limit rather than raising the cluster limit. Raising the cluster limit is the tempting move at 3am and it converts a five-minute incident into a recurring one.

*Trino coordinator bottlenecks on split planning.* A query over a very wide range of Iceberg partitions spends longer being planned than executed, holding coordinator resources other queries need. Symptom: queue depth rising while worker CPU sits idle — unmistakable once you have seen it, baffling before. Runbook: check coordinator planning time before adding workers. Adding workers does nothing here, which does not stop people trying it.

*Citus hot shard from a single large app.* A tenant grows past the point where its shard fits its node, and every query for that tenant slows while everyone else is fine. Symptom: per-tenant latency divergence, invisible in aggregate metrics — which is why per-tenant p95 for the top tenants is tracked separately. Runbook: confirm the shard is genuinely hot rather than the node being sick, then move that tenant to a dedicated node. Rebalancing the whole cluster for one tenant is disproportionate and disruptive.

## What I'd do differently

**I let the four-engine estate arrive by accretion and wrote the ownership rules afterwards.** Each engine was added for a defensible reason, but for a long stretch no document said which workload belongs where — so workloads landed on whichever engine the engineer building the feature knew best, and some landed wrong. That decision matrix would have cost an afternoon and prevented at least two migrations. The rule I would write on day one: an engine is chosen by the access pattern, not by the team's familiarity.

**I optimized the layout before I fully understood the query mix.** I had a strong intuition about the dominant predicate and I was mostly right — but "mostly" meant a class of queries with a different filter shape got quietly slower, and I found out from a complaint rather than a graph. Query-log analysis to classify the real mix by volume and total time consumed is a day of work, and it would have told me exactly what I guessed at.

**I did not build per-tenant latency visibility until skew forced me to.** Aggregate p95 across 25,000+ tenants is a comfortable number that hides the specific tenants having a bad time — and those are exactly the tenants large enough to be talking to their account manager about it. Per-tenant percentiles for the heaviest tenants should have been an SLI from the beginning.
