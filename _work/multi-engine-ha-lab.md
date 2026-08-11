---
title: "Multi-engine HA lab: eight failover scenarios"
hook: "Six database engines, eight failover scenarios, one laptop — with the numbers"
description: "A home lab, not a production system: six database engines, eight failover scenarios I wrote and ran on one laptop, and the numbers each one produced."
kind: lab
order: 6
featured: false
role: "Personal lab"
org: "Personal"
period: "2026"
team: "One person"
scale: "Docker on 8 CPU / 12.5 GB; nine compose stacks, brought up one at a time to fit RAM"
stack: [MongoDB, ScyllaDB, SolrCloud, MariaDB, Galera, Redis, PostgreSQL, Docker, Prometheus, Grafana]
metrics: [lab_scenarios, lab_pg_replay_lag, lab_redis_promotion]
tags: [distributed-databases, postgres, observability-slo]
image: /assets/og/og-default.png
image_alt: "Eight database high-availability scenarios run on Docker, each with a pass result"
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

**8 of 8 scenarios in my own test plan passed.** I wrote the plan, so the pass rate measures execution, not difficulty — owning that is more useful than implying an external benchmark.

| Engine | HA / cluster | Sharding | Backup/Restore | Monitoring | Result |
| --- | --- | --- | --- | --- | --- |
| MongoDB 8.0 | 3-node replica set, auto-failover | hashed-key sharded cluster (2 shards) | mongodump/restore | serverStatus, repl lag, oplog | PASS |
| ScyllaDB 2026.1 | 3-node, RF=3, QUORUM survives node loss | token ring (256 vnodes/node) | nodetool snapshot + refresh | nodetool info/tablestats, :9180 | PASS |
| SolrCloud 9 | ZK + 2 nodes, 2×2 shards/replicas | numShards=2 | collection BACKUP/RESTORE | metrics API, solr-exporter | PASS |
| MariaDB 11.8 + Galera 4 | 3-node multi-master, quorum, IST rejoin | n/a (full replicas) | mariabackup SST (state transfer) | wsrep_* status vars | PASS |
| Redis 8 Cluster | 3 primaries + 3 replicas, auto-failover | 16384 hash slots, hash tags | AOF per node | CLUSTER INFO/SHARDS | PASS |
| Redis 8 Sentinel | 1 primary + 2 replicas + 3 sentinels | n/a | AOF/RDB | SENTINEL master/replicas | PASS |
| PostgreSQL 18 | primary + hot-standby, pg_promote failover | n/a | pg_basebackup + WAL/PITR | pg_stat_replication, lag | PASS |
| Observability | exporters → Prometheus → Grafana | n/a | n/a | golden-signals dashboard | PASS |

PostgreSQL 18 streaming replication measured **383 µs replay lag** and 104 µs write lag from `pg_stat_replication`, and `pg_promote()` took the standby out of recovery on timeline 1 → 2. Redis Sentinel promoted a replica **about 5 seconds** after I killed the primary; Redis Cluster self-healed with no data loss, config epoch 2 → 7.

## Running it

Nothing runs continuously — a stack goes up, gets exercised, comes down. The three traps that cost the most time: ScyllaDB's third node refused to start until `fs.aio-max-nr` was raised on the Docker VM; Solr backups returned "access denied" until the location was in `solr.allowPaths` **and** owned by the `solr` user; and PostgreSQL 18 rejects a volume at `/var/lib/postgresql/data`, wanting the mount at `/var/lib/postgresql` with data in an `18/docker` subdirectory.

## What I'd do differently

**No sustained load.** Every failover happened on an idle cluster, which is the easy case. A background writer during the kill would make the numbers mean considerably more.

**Partitions were simulated, not real.** One host means I tested process death, not a split network. A second machine plus `tc`/`netem` would test the case that actually causes split-brain.

**It should have been one script.** Several runs were hand-driven, so reproducing a result means re-reading my own notes.

Each scenario is being written up properly, with commands and output, in [the tutorial series](/writing/).
