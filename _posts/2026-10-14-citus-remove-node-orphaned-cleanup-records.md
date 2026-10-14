---
title: "Citus removed the node. Its cleanup records stayed behind."
seo_title: "Citus orphaned shard error after citus_remove_node: stale pg_dist_cleanup rows"
description: "Draining a Citus worker and removing it straight away left cleanup records for a node that no longer existed. A later rebalance retried one move 33 times."
date: 2026-10-14 09:35:00 +0545
last_modified_at: 2026-10-14
type: essay
pillar: database-lifecycle
series: reference-systems
series_order: 8
tags:
  - distributed-databases
  - postgres
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - Citus shard rebalancing
  - Citus node removal
  - pg_dist_cleanup
  - deferred shard cleanup
mentions:
  - Citus
  - PostgreSQL 17
  - citusdata/citus#7333
cover:
  base: "/assets/images/editorial-distributed-db-lab-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: draining and removing a Citus worker leaves eight pg_dist_cleanup rows for a node group that no longer exists; minutes later a rebalance moves seven shard groups and retries the eighth 33 times until the stale rows are deleted"
  caption: "Removing a node is not finished when citus_remove_node returns. It is finished when nothing in the catalog still points at it."
faq:
  - q: "What does \"shard move failed as the orphaned shard … leftover from the previous move could not be cleaned up\" mean in Citus?"
    a: "A row in pg_dist_cleanup still names that shard. Citus refuses to move a shard group while any of its shards has a cleanup record, so the move cannot collide with a leftover copy. If the record points at a node group that has since been removed, the cleaner skips it forever and the move fails every time."
  - q: "Why doesn't citus_cleanup_orphaned_resources() remove the stale records?"
    a: "It runs the same cleaner loop, which skips any record whose node group has no primary node. Once the node is removed, its records are neither cleaned, deleted nor reported, and the call returns without a warning."
  - q: "How do I fix a shard move blocked by cleanup records for a removed node?"
    a: "Delete the records whose node_group_id matches no node: DELETE FROM pg_dist_cleanup WHERE node_group_id NOT IN (SELECT groupid FROM pg_dist_node). The move then succeeds. The old shard tables stay on the removed server, which is out of the cluster; drop them there if it might rejoin."
  - q: "How do I remove a Citus node without leaving cleanup records behind?"
    a: "After citus_drain_node returns, run CALL citus_cleanup_orphaned_resources() and check that pg_dist_cleanup has no rows for the node's group before calling citus_remove_node. In the reproduction, waiting longer than citus.defer_shard_delete_interval, 15 seconds by default, also avoided it."
key_takeaways:
  - "citus_remove_node deletes a node's placements and transaction records but not its pg_dist_cleanup rows, so a drain's last deferred drop can outlive the node."
  - "The cleaner silently skips records whose node group has no primary, so every later move of that shard group fails: 33 retries over 33 minutes in the lab."
  - "Only the shard group named in the stale records is blocked. Other moves succeed, which makes it look like one bad shard rather than a catalog problem."
  - "Clean up and check pg_dist_cleanup for the group before removing a node, and alert on any cleanup record whose group no longer exists."
  - "The bug was reported in 2023. A minimal reproduction on the current release and the code path added more to that issue than a duplicate would have."
---

The rebalance was the part of the lab I expected to be hard, and it went well. With eight client threads reading and writing through a Citus coordinator, a new worker joined and seven shard groups moved in 37.1 seconds. Nearly a million operations ran over the ten-minute load with zero errors, and every acknowledged write was there afterwards.

Then the job stopped making progress. The eighth move failed, waited, and failed again, 33 times over 33 minutes, with an error about something I had not done in that run:

```text
ERROR:  shard move failed as the orphaned shard public.tenants_102385 leftover from the previous move could not be cleaned up
```

Nothing was wrong with the shard, the target worker or the load. The cause was a node I had removed earlier in the session, and a catalog table that still remembered it.

**Operating rule.** Removing a Citus node is not finished when `citus_remove_node` returns. It is finished when nothing in the catalog still points at the node. Between the drain and the removal, run the cleanup and check `pg_dist_cleanup` for the node's group. Afterwards, alert on any cleanup record whose group no longer exists.

This came out of [distributed-db-lab](https://github.com/technobasant/distributed-db-lab), which I built to measure a Citus migration, rebalancing and tenant skew, and to compare TimescaleDB and ClickHouse on the same data. The lab figures are in its [MEASUREMENTS.md](https://github.com/technobasant/distributed-db-lab/blob/main/MEASUREMENTS.md); the reproduction figures are from a minimal rebuild I posted to the Citus issue tracker.

## How I got there

An earlier attempt at the rebalance-under-load run was spoiled by my own harness: it reused insert ids, so the run logged unique-key violations that had nothing to do with Citus. To start again from two workers, I drained the third worker with `citus_drain_node`, removed it with `citus_remove_node` as soon as the drain returned, brought a third worker back into the cluster, and started the load and the rebalance again.

Drain, then remove, is the sequence Citus documents for taking a node out. Both calls returned success, and neither said anything about a cleanup queue.

The background job's own record told the rest. It started at 05:15 UTC, finished eight tasks (reference-table replication and seven shard-group moves), and recorded the ninth as an error at 05:48 with 33 retries. Every retry was the same `citus_move_shard_placement` call for shard 102385, the `tenants` shard of one co-located group.

## What pg_dist_cleanup was holding

Citus does not drop a shard's old copy at the moment a move completes, because queries that started before the move may still be reading it. Instead the move writes a deferred-drop record into `pg_dist_cleanup`, and the maintenance daemon drops the copy on its next pass, every `citus.defer_shard_delete_interval` (15 seconds by default). A record names the object, the node group it lives on, and a policy; deferred drops are policy type 2.

Before every move, Citus also checks that none of the shards it is about to move still has such a record, since a leftover copy with the same name would collide with the new one. That check raised the error above. This is what the table held when the job gave up:

```text
 record_id |           object_name            | node_group_id
-----------+----------------------------------+---------------
       279 | public.tenants_102385            |             7
       280 | public."AuditLog_102417"         |             7
       281 | public.events_102449             |             7
       282 | public.orders_102481             |             7
       283 | public.projects_102513           |             7
       284 | public.users_102545              |             7
       285 | public.webhook_deliveries_102577 |             7
       286 | public.webhooks_102609           |             7
```

Eight rows, one for each table in the co-located shard group, all on group 7: the group of the worker I had removed. No node in `pg_dist_node` belonged to group 7 any more.

## Why nothing ever cleaned them up

I read the Citus source on `main` at d41eec3459, which behaves the same as the v14.2.0 tag here. Three pieces of code meet.

- **The drain's last move is the one that leaks.** Every shard move starts by cleaning up orphaned resources in a separate transaction, which drops the previous move's leftovers while their node still exists. The final move of a drain has no successor, so its records wait for the maintenance daemon. Remove the node before the daemon's next pass, and they are stranded.
- **Node removal doesn't touch the cleanup queue.** `RemoveNodeFromCluster` deletes the node's replicated-table placements, its `pg_dist_transaction` rows through `DeleteWorkerTransactions`, and the node row. It never deletes the group's `pg_dist_cleanup` rows.
- **The cleaner skips groups with no primary.** `DropOrphanedResourcesForCleanup` contains `if (!PrimaryNodeForGroup(record->nodeGroupId, NULL)) continue;`. A record for a removed group is not cleaned, not deleted and not counted as a failure, so there is no warning either. `citus_cleanup_orphaned_resources()` runs the same loop and returns quietly.

The check that raises the error, `ErrorIfCleanupRecordForShardExists`, finds a record by object name alone, whatever its group. So a record for a copy on a server that has left the cluster blocks that shard group's move to every server, permanently.

Two properties made it slow to diagnose. It blocks only the shard group named in the stale records, and other shards move normally, so it looks like one bad shard rather than a catalog problem. And in a background rebalance the task stays runnable and retries with backoff, holding up the tasks queued behind it, so the job looks busy rather than broken.

## Reducing it to a dozen statements

A failure seen once in a noisy lab is an anecdote. I wanted a reproduction small enough to paste into an issue, so I rebuilt it on fresh clusters: a coordinator and four workers, one container per node, Citus 14.2.0 on PostgreSQL 17.11, every setting at its default except `citus.shard_count = 8`.

```sql
SELECT citus_set_coordinator_host('coordinator', 5432);
SELECT citus_add_node('worker1', 5432);
SELECT citus_add_node('worker2', 5432);
SELECT citus_add_node('worker3', 5432);
CREATE TABLE items (id bigint PRIMARY KEY, payload text);
CREATE TABLE item_events (id bigint PRIMARY KEY, item_id bigint, note text);
SELECT create_distributed_table('items', 'id');
SELECT create_distributed_table('item_events', 'id', colocate_with => 'items');
INSERT INTO items SELECT g, md5(g::text) FROM generate_series(1, 5000) g;
INSERT INTO item_events SELECT g, g, 'n' FROM generate_series(1, 5000) g;

SELECT citus_drain_node('worker3', 5432);
SELECT citus_remove_node('worker3', 5432);   -- right after the drain returns

CALL citus_cleanup_orphaned_resources();      -- returns; cleans nothing, warns nothing
SELECT citus_add_node('worker4', 5432);

SELECT citus_move_shard_placement(102010, 'worker2', 5432, 'worker4', 5432);
-- ERROR:  shard move failed as the orphaned shard public.items_102010
--         leftover from the previous move could not be cleaned up
```

A move of a different shard, straight afterwards, succeeded. I ran the bug sequence and two controls:

| Scenario | Runs | Result |
|---|---|---|
| Drain, then remove immediately | 3 fresh clusters | reproduced 3 of 3 |
| Drain, `CALL citus_cleanup_orphaned_resources()`, then remove | 1 | no stale records; the move and a rebalance succeed |
| Drain, wait 20 s (past the 15 s interval), then remove | 1 | `pg_dist_cleanup` empty before removal; a rebalance succeeds |
{: aria-label="Reproduction of stale cleanup records after node removal, with two controls" }

The controls are one run each. They show that the sequence works, not that it always works under load.

In a background job the shape matched the lab. Draining the worker that now held the affected shard scheduled four moves; 30 seconds later two were done, the move of the affected shard was runnable with two retries and the same error, and the task after it was blocked.

## It was already reported

Before filing anything I searched the tracker and found [citusdata/citus#7333](https://github.com/citusdata/citus/issues/7333), open since November 2023. Its reporter had lost a worker to a hardware failure, removed it, and then could not move one shard: the same error, and a `pg_dist_cleanup` row for the lost node's group. A maintainer replied the same day that it would be good for `citus_remove_node` to clean those records up, and suggested deleting the rows by hand in the meantime. The issue was still open.

A duplicate would have added nothing. What the thread lacked was that the bug does not need a hardware failure: the ordinary drain-then-remove sequence triggers it on the current release, deterministically, inside the cleanup interval. So I [commented](https://github.com/citusdata/citus/issues/7333#issuecomment-6140552778) with the reproduction, the 3-of-3 result and both controls, and the three code locations above. I offered a patch that deletes the removed group's records in `RemoveNodeFromCluster`, next to the existing `DeleteWorkerTransactions` call. Deferred-drop records could always go; records belonging to an operation that might still be running would only go when that operation's lock can be taken, the guard the cleaner already uses. Whether that is the shape the maintainers want is their call, so it waits for their reply.

## The guard I use now

Until `citus_remove_node` handles this itself, removal gets a check around it:

```sql
-- after citus_drain_node returns, before citus_remove_node
CALL citus_cleanup_orphaned_resources();

SELECT count(*) AS pending
  FROM pg_dist_cleanup
 WHERE node_group_id = (SELECT groupid FROM pg_dist_node
                         WHERE nodename = 'worker3' AND nodeport = 5432);
-- remove the node only when pending = 0
```

The second check belongs in monitoring, because it catches the state however it arose, including the dead-node case from the original report, where there is no chance to drain first:

```sql
SELECT record_id, object_name, node_group_id
  FROM pg_dist_cleanup
 WHERE node_group_id NOT IN (SELECT groupid FROM pg_dist_node);
```

Any row it returns is a shard group that cannot move. The repair is to delete those rows, which is what let the lab's stuck move finish in 5.3 seconds:

```sql
DELETE FROM pg_dist_cleanup
 WHERE node_group_id NOT IN (SELECT groupid FROM pg_dist_node);
```

The old shard tables stay on the removed server. Out of the cluster, they cost the cluster nothing, but if that server might rejoin, drop them there first.

The broader habit is the one I took away. A distributed database keeps queues of deferred work in its own catalog: cleanup records, two-phase-commit records, background jobs. An operation can return success and leave work in one of them that nothing will ever finish. After a topology change, I now read those queues as well as the return value. The same lab hit the pattern twice more, in a PostgreSQL minor release that quietly switched off tenant isolation and a single table without a primary key that stopped the rebalancer for the whole cluster; both are in [the case study](/work/distributed-db-lab/).

<div class="callout callout--note" markdown="1">
**Boundary.** The 33 retries, the eight stale rows and the 5.3-second repair come from one lab run on Citus 14.2.0 built from source on PostgreSQL 17.11, with every node in its own container on one host (Apple M5, a Docker VM with 8 CPUs and 11.67 GiB), so node-to-node latency is local. The 3-of-3 result and both controls come from the separate minimal reproduction on the same build; each control is a single run. The code path was read on Citus `main` at d41eec3459 and the v14.2.0 tag. I did not test the dead-node path from the original report, `citus_disable_node`, or releases before 14.2. No fix has been merged; everything here describes 14.2.0.
</div>

## Frequently asked questions

### What does "shard move failed as the orphaned shard … leftover from the previous move could not be cleaned up" mean in Citus?

A row in `pg_dist_cleanup` still names that shard. Citus refuses to move a shard group while any of its shards has a cleanup record, so the move cannot collide with a leftover copy. If the record points at a node group that has since been removed, the cleaner skips it forever and the move fails every time.

### Why doesn't citus_cleanup_orphaned_resources() remove the stale records?

It runs the same cleaner loop, which skips any record whose node group has no primary node. Once the node is removed, its records are neither cleaned, deleted nor reported, and the call returns without a warning.

### How do I fix a shard move blocked by cleanup records for a removed node?

Delete the records whose `node_group_id` matches no node: `DELETE FROM pg_dist_cleanup WHERE node_group_id NOT IN (SELECT groupid FROM pg_dist_node)`. The move then succeeds. The old shard tables stay on the removed server, which is out of the cluster; drop them there if it might rejoin.

### How do I remove a Citus node without leaving cleanup records behind?

After `citus_drain_node` returns, run `CALL citus_cleanup_orphaned_resources()` and check that `pg_dist_cleanup` has no rows for the node's group before calling `citus_remove_node`. In the reproduction, waiting longer than `citus.defer_shard_delete_interval`, 15 seconds by default, also avoided it.

The rest of the lab, from the migration that failed six ways to TimescaleDB and ClickHouse on the same data, is in [the case study](/work/distributed-db-lab/) and the [repository](https://github.com/technobasant/distributed-db-lab). More on [distributed databases](/writing/tags/distributed-databases/) and [PostgreSQL](/writing/tags/postgres/).
