---
title: "Why naive SCD2 on Iceberg costs more than you think"
description: "Slowly changing dimensions can become a rewrite amplifier. The durable cost levers are partitioning, compaction cadence, and snapshot expiry."
type: essay
tags: [iceberg-lakehouse, cost-finops]
toc: true
level: advanced
---

The textbook SCD Type 2 pattern — close the old row, insert the new one — can become a rewrite amplifier on file-backed tables: a small logical change rewrites whole files, every rewrite produces a new snapshot, and every snapshot keeps predecessor files alive until an explicit policy expires them.

The instinct when the storage bill grows is to reach for compression. The draft argues that compression is the smallest lever available and that the real ones are structural: a partition layout that keeps updates local instead of spraying them across the table, a compaction cadence tuned to the update rate rather than run nightly out of habit, and a snapshot expiry and orphan-file policy that someone actually owns.

It will also cover when to stop doing SCD2 at all — merge-on-read against copy-on-write, and the cases where an append-only event table with a view over it is both cheaper and more honest about what the data means.
