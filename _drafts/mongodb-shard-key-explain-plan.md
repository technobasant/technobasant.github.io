---
title: "Reading a MongoDB shard key off the explain plan"
description: "Whether a query hits one shard or every shard is visible in thirty seconds, and that difference is the whole return on choosing a shard key well."
type: tutorial
tags: [distributed-databases]
series: failover-lab
series_order: 7
toc: true
level: intermediate
---

A hashed shard key on `userId` split 100,000 documents across two shards at 49,607 and 50,393 — an even split, which is the entire point of hashing a monotonic or clustered field rather than ranging on it. Range-partitioning an increasing key sends every new write to the same chunk on the same shard, and no amount of adding shards fixes that.

The part people skip is what the split buys you at query time, and it is visible immediately. A query carrying the shard key was routed to 1 shard. The same collection filtered on `region`, which is not the shard key, scatter-gathered to 2 — and would have gone to all sixty on a sixty-shard cluster, with the router waiting for the slowest one.

The draft will walk the explain output for both queries, show where the targeted shard list appears, and make the case that shard-key coverage belongs in code review for query-heavy collections. It is one of the few distributed-systems properties you can check in thirty seconds without a load test.
