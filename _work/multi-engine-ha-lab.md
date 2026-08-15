---
title: "Multi-engine HA lab: eight failover scenarios"
hook: "Six database engines, eight failover scenarios, one laptop — with the numbers"
description: "A home lab, not a production system: six database engines, eight failover scenarios I wrote and ran on one laptop, and the numbers each one produced."
date: 2026-08-04
last_modified_at: 2026-08-15
kind: lab
order: 4
featured: true
role: "Personal lab"
org: "Personal"
period: "2026"
team: "One person"
scale: "Docker on 8 CPU / 12.5 GB; nine compose stacks, brought up one at a time to fit RAM"
problem: "Documentation describes expected failover; I wanted current, measured evidence of what six engines actually preserved, promoted, and exposed after a primary or node disappeared."
decision: "Run one reproducible cluster at a time, seed known state, inject a specific fault, and record promotion, recovery, and data-survival evidence."
flow: lab
stack: [MongoDB, ScyllaDB, SolrCloud, MariaDB, Galera, Redis, PostgreSQL, Docker, Prometheus, Grafana]
metrics: [lab_scenarios, lab_pg_replay_lag, lab_redis_promotion]
tags: [distributed-databases, postgres, observability-slo]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

This is a lab, not a production system, and I would rather say that in the first sentence than bury it. It is a rig I built to re-earn hands-on failover knowledge across engines I do not run daily — by killing processes and reading what came back, rather than quoting a docs page.

## Constraints

One host, 8 CPU and ~12.5 GB of RAM, which is why each cluster came up, got exercised and got torn down one at a time. No cross-engine load test. No real network partitions — a single Docker host cannot give you one. 2026 engine versions throughout, which meant meeting each version's current surprises rather than the ones in older tutorials.

## Architecture

Nine Docker Compose stacks: `mongo-ha`, `mongo-shard`, `scylla-ha`, `solr-ha`, `galera-ha`, `redis-cluster`, `redis-sentinel`, `pg-replication`, `observability`. Each stands up a real multi-node cluster, gets seeded, gets broken deliberately, and gets checked for what survived.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost us |
|---|---|---|---|
| Docker Compose on one host | A VM per node in the cloud | Quorum, election and promotion behavior is observable at this scale, at zero cost | Node-level network partitions and disk failure are not testable at all |
| One cluster at a time | Everything up simultaneously | 12.5 GB of RAM | No contention testing; every result is an isolated run |
| `docker kill` rather than graceful stop | Graceful shutdown | Ungraceful loss is the case that actually breaks quorum, and the difference is the whole lesson | Slower resets; some engines needed manual recovery |
| Current 2026 versions | Older LTS releases | I wanted today's failure modes | Version-specific traps cost real time (see below) |

## Results

**8 of 8 scenarios in my own test plan passed.** I wrote the plan, so the pass rate measures execution, not difficulty — owning that is more useful than implying an external benchmark. Which is also why the table below reports what each engine *measured* rather than a PASS column: a constant column carries about one bit, and the numbers are the part you can argue with.

{% include ledger.html %}

The last row is the limit of the rig, not a result. One Docker host cannot produce a split network, so every failover here is process death — and partition is the case that actually causes split-brain.

## What went wrong

The passes are the boring part. These three cost the most time, and each one is a version-specific trap that no documentation page warned me about.

{% include findings.html %}

## Running it

Nothing runs continuously — a stack goes up, gets exercised, comes down. The three traps that cost the most time: ScyllaDB's third node refused to start until `fs.aio-max-nr` was raised on the Docker VM; Solr backups returned "access denied" until the location was in `solr.allowPaths` **and** owned by the `solr` user; and PostgreSQL 18 rejects a volume at `/var/lib/postgresql/data`, wanting the mount at `/var/lib/postgresql` with data in an `18/docker` subdirectory.

## What I'd do differently

**No sustained load.** Every failover happened on an idle cluster, which is the easy case. A background writer during the kill would make the numbers mean considerably more.

**Partitions were simulated, not real.** One host means I tested process death, not a split network. A second machine plus `tc`/`netem` would test the case that actually causes split-brain.

**It should have been one script.** Several runs were hand-driven, so reproducing a result means re-reading my own notes.

Each scenario is being written up properly, with commands and output, in [the tutorial series](/writing/).
