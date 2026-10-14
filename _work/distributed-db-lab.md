---
title: "Sharding Postgres with Citus, measured against TimescaleDB and ClickHouse"
seo_title: "Distributed DB lab: Citus sharding, TimescaleDB and ClickHouse, measured"
hook: "A schema that refused to distribute six ways, a tenant whose shard was 7.4× the median, and a rebalance under live writes"
description: "A Citus migration that failed six ways before it worked, a rebalance under load with zero errors, and TimescaleDB and ClickHouse measured on the same data."
date: 2026-10-14
last_modified_at: 2026-10-14
kind: lab
pillar: database-lifecycle
related: [multi-engine-ha-lab, patroni-ha-backup-lab, clickhomes]
order: 3
featured: false
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "Citus 14.2 coordinator + 3 workers, TimescaleDB 2.30, ClickHouse 25.8 at 2 shards × 2 replicas; one container per node; 6M to 20.7M rows per part"
problem: "Sharding Postgres is usually explained as a topology diagram. What decides whether it works is which key every table carries, which constraints change before the first table can move, what a rebalance does to live writes, and what to do with the tenant that dwarfs the rest."
decision: "Rebuild the patterns on synthetic data: generate the migration from the catalog, distribute and co-locate everything by tenant, measure the rebalance under load, then put one dataset into four engines and compare rather than crown one."
repo: "https://github.com/technobasant/distributed-db-lab"
flow: distributed-db-lab
cover:
  base: "/assets/images/editorial-distributed-db-lab-v1"
  width: 1600
  height: 900
  alt: "Schematic: draining and removing a Citus worker leaves eight pg_dist_cleanup rows for a node group that no longer exists; minutes later a rebalance moves seven shard groups and retries the eighth 33 times until the stale rows are deleted"
  caption: "Removing a drained worker straight away left eight cleanup records behind, and the next rebalance could not move the eighth shard group until they were deleted."
  link: "/writing/citus-remove-node-orphaned-cleanup-records/"
metrics: [ddb_rebalance_errors, ddb_colocation_join, ddb_skew_spread, ddb_tsdb_compression, ddb_ch_replica_outage]
stack: [Citus, "PostgreSQL 17", TimescaleDB, ClickHouse, "ClickHouse Keeper", "Docker Compose", Python]
tags: [distributed-databases, postgres, clickhouse]
image: /assets/og/og-databases.png
image_alt: "Databases at scale — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Horizontal scale for Postgres is usually sold as a diagram: add nodes, the data spreads, queries get faster. What decides whether it works is less photogenic. Every table has to carry the distribution key. Primary keys, unique constraints and foreign keys have to be reshaped before the first table can be distributed. A rebalance has to run while writes keep arriving. And there is always one customer whose data is several times anyone else's.

Citus has been part of my work since 2021; [citusdata/citus#4776](https://github.com/citusdata/citus/issues/4776) is a report of mine from then, about adding an unnamed constraint to a distributed table, which Citus's maintainers fixed by adding that support in January 2023. This lab rebuilds, from scratch and on synthetic data, the patterns I worked through on consulting engagements: a schema migrated table by table onto Citus, and an audit of a TimescaleDB hypertable whose index outweighed its data. Then it loads one dataset into four engines to see where each earns its place. No client code, schema or figures are in it. Every number is in the repository's [MEASUREMENTS.md](https://github.com/technobasant/distributed-db-lab/blob/main/MEASUREMENTS.md), next to the file it came from.

## Constraints

Every node is its own container, and all of them run on one host — an Apple M5 with a Docker VM of 8 CPUs and 11.67 GiB — so node-to-node latency is local and there are no network partitions to test. The host was not quiet either: load average sat between 10 and 44 during the runs, partly from a network filter on the host. Medians are the figures to trust; p99s carry that noise.

The data is seeded: 2,000 tenants with Zipf-shaped sizes, one tenant pinned to 15% of events, and 0.5% of events with no tenant at all. The published Citus images are amd64-only, and timing an emulated database would have been meaningless, so Citus 14.2.0 is built from its source tag; CI runs the official image at small scale. Each part runs alone and is torn down before the next.

## Architecture

Four parts, one compose stack each, with a benchmark container inside each network. Running the client from the host instead added about 3 ms to a `SELECT 1`.

- **Citus 14.2 on PostgreSQL 17.11.** A coordinator and two workers with 32 shards, then a third worker added under load. Eight tables distributed by `tenant_id` and co-located with `tenants`; two small lookup tables as reference tables.
- **TimescaleDB 2.30.** 20.7 million ticks in one-day chunks, loaded twice with opposite primary-key orders, then columnstore, hierarchical candles and retention.
- **ClickHouse 25.8.** Two shards × two replicas of ReplicatedMergeTree behind a Distributed table sharded by `intHash64(tenant_id)`, with one Keeper.
- **A comparison.** The same 10 million rows in PostgreSQL with a B-tree, Citus columnar, TimescaleDB columnstore and ClickHouse, warm and VM-cold.

The Citus migration is generated by a planner that reads the live catalog, picks the root table and writes the SQL for every change. On this schema it found 15 issues, from primary keys without the tenant column to a mixed-case table name.

## In the code

This function writes the whole migration, and its order is the answer to the naive attempt's six failures: the key and constraint fixes run first in one transaction, and every foreign key comes off before any table moves, because Citus will not distribute a table that local tables still reference. The foreign keys return only once all eight tenant tables sit in one co-location group led by `tenants`, which is what keeps one tenant's joins on one shard.

```python
def emit_sql(cat: Catalog, p: Plan) -> str:
    """Fixes, then reference tables, then the co-located distribution, then FKs."""
    drops, adds = _fk_readd(cat, p)
    out = ["-- generated by tools/plan_distribution.py — review before running", "BEGIN;"]
    out.append("\n-- every foreign key comes off first; they return once all tables are placed")
    out += drops
    for code in ["NULL_KEY", "MISSING_KEY", "PK_WITHOUT_KEY"]:
        for i in (i for i in p.issues if i.code == code):
            out.append(f"\n-- {i.code} {i.table}: {i.detail}")
            # …
    out.append("COMMIT;\n")
    out.append("-- reference tables (replicated to every node)")
    out += [f"SELECT create_reference_table('{q(r)}');" for r in p.reference]
    out.append("\n-- distributed tables, one co-location group led by the root")
    out.append(f"SELECT create_distributed_table('{q(p.root)}', '{p.key}');")
    for name, col in p.distributed.items():
        if name != p.root:
            out.append(
                f"SELECT create_distributed_table('{q(name)}', '{col}', "
                f"colocate_with => '{q(p.root)}');"
            )
    out.append("\n-- foreign keys, re-added; between distributed tables they carry the key")
    out += adds
    # …
```
{: data-file="tools/plan_distribution.py" }

Two tests pin that order, and the planner, catalog queries included, is in [tools/plan_distribution.py](https://github.com/technobasant/distributed-db-lab/blob/main/tools/plan_distribution.py).

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Distribute every tenant table by `tenant_id`, co-located with `tenants` | Each table by its own id | One tenant's joins and foreign keys stay on one shard | Every primary key and foreign key had to gain the tenant column first |
| Generate the migration from the catalog | Hand-write it table by table | The naive attempt failed six different ways, one at a time; a planner finds them all at once | Its first run still failed on a foreign key it had not cleared, now fixed and pinned by a test |
| Rows with no tenant go to a reserved tenant | A separate local table | One query path for everything | Their references to other tenants' rows had to be cleared, because a composite foreign key cannot hold them |
| Isolate the largest tenant before rebalancing | Trust the rebalancer | No move can split a shard | The split needed a setting changed on every node first (below) |
| One dataset, four engines, no winner declared | Tune each engine and rank them | The useful question is which workload each one fits | Not a vendor benchmark: each engine would do better with an expert's settings |

## Results

**Routing is the performance model.** A one-tenant query routed to a single shard ran at a p50 of 3.77 ms; the same question across every tenant fanned out to 32 shards and took 677 ms. The same join was {{ site.data.metrics.ddb_colocation_join.value }} faster co-located than repartitioned: 1,252 ms against 5,206 ms, both returning 617,895 rows.

**A node can join under write load.** With eight client threads running, adding a third worker moved seven shard groups in 37.1 s with {{ site.data.metrics.ddb_rebalance_errors.value }} across 977,368 operations, and all 195,543 acknowledged writes were there afterwards. Write p99 rose from 38.0 ms to 54.7 ms while shards moved.

**Skew needs splitting, not moving.** The largest tenant's shard was 7.4× the median. After the default rebalance the workers were 2.36× apart and the rebalancer declined every further move, because `by_disk_size` adds a fixed 100 MiB to each shard group's cost and shards of tens of megabytes all look alike. Isolating that tenant to its own shard and rebalancing with the base cost at 0 took the spread to 1.10×.

**TimescaleDB: key order is a trade-off.** An entity-led primary key made entity queries 2.3–3.2× faster, but its index grew to 1.43× the heap against 0.91× for a time-led key, because time-ordered ingest only appends to a time-led B-tree. Columnstore made the data {{ site.data.metrics.ddb_tsdb_compression.value }}, and daily candles came from a continuous aggregate in 0.157 ms instead of 15.3 ms.

**ClickHouse: the sort key is the index.** With a tenant-first `ORDER BY`, one tenant's query read 49,152 rows; ordered by time, it read the whole shard, 4,168,647. With one replica down for 60 s, {{ site.data.metrics.ddb_ch_replica_outage.value }} inserts and 30 of 30 reads succeeded, and the replica caught up 0.8 s after it was serving again.

**On one dataset,** PostgreSQL with a B-tree answered the one-tenant question as fast as anything (2.1 ms) and took 8–9× the disk of the three columnar engines, which landed within 14% of each other. ClickHouse was fastest on all three scans and the least affected by a cold start; TimescaleDB tied PostgreSQL on the point query and came within 5 ms of ClickHouse on the month-long scan.

## What went wrong

These cost more time than everything that worked, and none came with an obvious error.

**A removed node blocked a rebalance half an hour later.** To reset a run, I drained the third worker and removed it straight away. The drain's last move had queued a deferred drop in `pg_dist_cleanup`, and the removal left those eight records pointing at a node group that no longer existed. Later, the rebalance moved seven shard groups and retried the eighth 33 times over 33 minutes. Deleting the stale rows let it finish in 5.3 s. It is the open [citusdata/citus#7333](https://github.com/citusdata/citus/issues/7333), reported in 2023; I confirmed it on 14.2 with a minimal reproduction. The mechanism is in [the write-up](/writing/citus-remove-node-orphaned-cleanup-records/).

**A PostgreSQL minor release switched off tenant isolation.** The August 2026 minor releases, 17.11 among them, only allow the logical-decoding output plugins listed in the new `output_plugin_libraries`, and Citus's shard split decodes through `citus`. `isolate_tenant_to_new_shard` failed with `library "citus" may not be used as an output plugin`, while shard moves, which use `pgoutput`, kept working. The fix is a bare list on every node; quoting the whole value stores it as one name and silently does nothing.

**One table without a primary key stopped the rebalancer for the whole cluster.** A `CREATE TABLE … AS` copy left distributed for a join test had no replica identity, and `citus_rebalance_start` refused to move anything until it was gone.

**ClickHouse 25.7 changed what `LIMIT` means.** `INSERT INTO <Distributed> SELECT … FROM <Distributed> LIMIT n` now runs on each shard and applies the limit per shard. My "2,000,000 rows" wrote 3,950,848.

## What I'd do differently

**Guard node removal from the start.** Run `CALL citus_cleanup_orphaned_resources()` and check that `pg_dist_cleanup` is empty for the node's group before `citus_remove_node`. The later reproduction showed that sequence avoids the stale records; the lab itself did not use it.

**Put a real network between nodes.** One host means no partitions and loopback latency. QEMU VMs on a shared fabric, as in the [Patroni lab](/work/patroni-ha-backup-lab/), would let the rebalance and the replica outage be measured with a network in the way.

**Add a connection pooler and a Keeper quorum.** Nothing here put PgBouncer in front of the coordinator, which is where an application of this shape meets connection limits first. And one Keeper coordinates replication without being a quorum, so the ClickHouse outage tests a replica, not the coordination layer.

The code, the planner and every result file are in [distributed-db-lab](https://github.com/technobasant/distributed-db-lab).
