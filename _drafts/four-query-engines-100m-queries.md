---
title: "Four query engines, one estate, one decision table"
description: "Federated ad-hoc, wide-column scan, sharded row-store and time-series rollup — picking by access pattern, and the schema changes that halved p95 latency."
type: essay
tags: [clickhouse, postgres, distributed-databases]
toc: true
level: advanced
---

Most engine comparisons are written by someone who runs one of them. The useful version is written by someone who has tuned all of them in the same estate, against the same data, for the same users — because then the comparison is about access patterns rather than benchmarks chosen to flatter a favorite.

The draft is a decision table across four shapes: federated ad-hoc querying over the lakehouse, wide-column scans, a sharded row-store for high-cardinality operational reads, and time-series rollups. For each: what it is genuinely good at, the query shape that falls off a cliff, the operational cost nobody mentions, and the honest answer to "could we just use one of these".

The concrete part is the tuning. Most of the p95 improvement came from schema and layout decisions — ordering keys, partition granularity, pre-aggregation, repartitioning to match the read pattern — not from engine settings or bigger instances. The engine choice sets the ceiling; the data model decides where you actually land.
