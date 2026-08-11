---
title: "Redis Cluster vs Sentinel, both timed on the same rig"
description: "Two failure models shipped in one product, measured back to back: slot ownership and epoch bumps against quorum-based promotion, and how to pick between them."
type: essay
tags: [distributed-databases]
series: failover-lab
series_order: 5
toc: true
level: intermediate
---

Redis ships two high-availability stories and they solve different problems. Cluster shards data across 16,384 hash slots and gives each shard its own failover. Sentinel does not shard at all — it monitors one primary and promotes a replica when a quorum of sentinels agrees the primary is down.

Evidence from the rig, both run on the same Docker host. Cluster: six nodes formed three primaries and three replicas with all 16,384 slots covered; killing a master that owned slots 5461–10922 promoted its replica, bumped the config epoch from 2 to 7, returned `cluster_state:ok` with `cluster_slots_ok:16384`, and lost nothing. Sentinel: three sentinels with quorum 2 and `down-after-milliseconds 5000` promoted a replica about five seconds after the primary was stopped, kept a canary key, and demoted the old primary to a replica of the new one when it came back.

The decision is not really about Redis. It is about what your client library does with a `MOVED` redirect, whether your access pattern survives keys living on different shards, and whether hash tags are enough to keep the multi-key operations you already wrote working. Pick Sentinel when you need availability and your data fits one node; pick Cluster when you also need horizontal scale and can accept the constraints it puts on your key design.
