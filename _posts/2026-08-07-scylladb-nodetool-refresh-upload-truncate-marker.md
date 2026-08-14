---
title: "nodetool refresh only reads upload/ — and TRUNCATE hides your SSTables"
seo_title: "ScyllaDB nodetool refresh only reads upload/"
description: "Three ScyllaDB behaviors that make a perfectly valid snapshot restore return zero rows, with the repro, the fix, and the AIO limit that stops node three."
date: 2026-08-07 09:00:00 +0545
last_modified_at: 2026-08-11 10:20:00 +0545
type: tutorial
tags: [distributed-databases]
series: failover-lab
series_order: 2
featured: true
toc: true
cover:
  base: "/assets/images/editorial-scylla-refresh-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Scylla node with SSTable discs; only the upload tray glows, a TRUNCATE marker hides older files"
  caption: "nodetool refresh only reads upload/, and a TRUNCATE marker keeps pre-truncate SSTables invisible even when the files are back."
level: advanced
time_estimate: "~40 min hands-on"
what_youll_build: "A three-node ScyllaDB cluster at RF=3 that survives a node loss at QUORUM, and a snapshot restore that actually returns your rows instead of zero."
prerequisites:
  - "Docker 24+ with 8 CPU and 12.5 GB of RAM available to the daemon"
  - "Docker Compose v2 — the `docker compose` subcommand, not `docker-compose`"
  - "Ability to run a privileged container, to raise a sysctl inside the Docker VM"
  - "Basic CQL: CREATE KEYSPACE, CREATE TABLE, SELECT"
tested_on: "ScyllaDB 2026.1 · Docker Compose v2 · 8 CPU / 12.5 GB"
key_takeaways:
  - "nodetool refresh only scans the live table directory's upload/ subdirectory; valid SSTables placed beside the live files are ignored without an error."
  - "A TRUNCATE marker keeps pre-truncate SSTables invisible, so recovery requires dropping and recreating the table before loading the snapshot."
  - "The recreated table has a new UUID and directory; verify that identity in system_schema.tables before copying files or running refresh."
---

## What went wrong

I had a good snapshot. I had the SSTable files on disk. I ran `nodetool refresh` on all three nodes, got no errors, and `SELECT count(*)` returned zero.

It took three separate discoveries to get the rows back, and none of them produced an error message at any point. That is what makes this expensive: every step in the obvious restore procedure succeeds, and the data still is not there.

The three behaviors, stated up front so you can stop reading if one of them is your problem:

1. **`nodetool refresh` only loads SSTables from the table's `upload/` subdirectory.** Files dropped into the table directory itself are ignored — silently, with a zero exit code.
2. **`TRUNCATE` writes a truncation marker**, and that marker hides every SSTable written before it. You can put the old files back and they stay invisible. Recovering from a `TRUNCATE` needs `DROP TABLE` and a recreate, not another restore attempt.
3. **Recreating a table gives it a new UUID**, and the on-disk directory is named after that UUID. The path you carefully copied files into a minute ago now belongs to a dead table.

There is a fourth thing, which happens before any of this and is the reason the cluster would not start in the first place. It gets Step 1.

The compose file is reproduced inline below. There is no public repository to clone.

## Step 1 — Raise fs.aio-max-nr before the third node

The first two Scylla nodes came up fine. The third exited during startup with:

```text
system does not satisfy minimum AIO requirements
```

ScyllaDB's Seastar runtime reserves asynchronous I/O contexts per reactor when it starts. `fs.aio-max-nr` is a kernel-wide ceiling on those contexts, and the Linux VM behind Docker Desktop ships with a low default. Two nodes fit under it. Three did not.

The limit belongs to the VM, not to a container, so raise it from a privileged throwaway container. It applies to every container on that daemon, including ones you start later.

```bash
docker run --rm --privileged alpine sysctl -w fs.aio-max-nr=1048576
```

**Verify.**
{: .verify}

```console
$ docker run --rm --privileged alpine sysctl -w fs.aio-max-nr=1048576
fs.aio-max-nr = 1048576
```

<div class="callout callout--gotcha" markdown="1">
**Gotcha.** This sysctl lives inside the Docker VM, and the VM is rebuilt when Docker Desktop restarts. The fix does not persist. If a node that started yesterday refuses to start today with the same AIO message, re-run the privileged container before you look at anything else.
</div>

## Step 2 — Bring the ring up one node at a time

Three nodes, each pinned to a single shard and 1200 MB, which is what makes three of them fit on one laptop. `scylla1` is the seed; the other two join it.

```yaml
name: scylla-ha

services:
  scylla1:
    image: scylladb/scylla:2026.1
    command: ["--seeds=scylla1", "--smp=1", "--memory=1200M", "--overprovisioned=1", "--api-address=0.0.0.0"]
    ports: ["9042:9042"]
    volumes: ["s1:/var/lib/scylla"]

  scylla2:
    image: scylladb/scylla:2026.1
    command: ["--seeds=scylla1", "--smp=1", "--memory=1200M", "--overprovisioned=1", "--api-address=0.0.0.0"]
    volumes: ["s2:/var/lib/scylla"]
    depends_on: [scylla1]

  scylla3:
    image: scylladb/scylla:2026.1
    command: ["--seeds=scylla1", "--smp=1", "--memory=1200M", "--overprovisioned=1", "--api-address=0.0.0.0"]
    volumes: ["s3:/var/lib/scylla"]
    depends_on: [scylla1]

volumes:
  s1:
  s2:
  s3:
```
{: data-file="scylla-ha/docker-compose.yml"}

`depends_on` only controls start order, not readiness, so bring the nodes up by hand. Start the seed, wait for it to report Up/Normal, then add one joiner at a time.

```bash
docker compose -f scylla-ha/docker-compose.yml up -d scylla1
```

```bash
docker exec scylla-ha-scylla1-1 nodetool status
```

Once `scylla1` shows `UN`, add the second, wait again, then the third:

```bash
docker compose -f scylla-ha/docker-compose.yml up -d scylla2
```

```bash
docker compose -f scylla-ha/docker-compose.yml up -d scylla3
```

**Verify.** `nodetool status` lists three nodes at `UN` — Up and Normal — each holding 256 tokens:
{: .verify}

```console
UN 172.21.0.2 ... rack1
UN 172.21.0.3 ... rack1
UN 172.21.0.4 ... rack1
```

A node stuck at `UJ` is still joining and streaming; give it time rather than restarting it. A node at `DN` never made it — check that its AIO problem is fixed and that the seed was `UN` before it started.

## Step 3 — Create the keyspace and a query-driven table

RF=3 on a three-node cluster means every node holds every row, which is what makes the QUORUM behavior in the next step easy to reason about.

```sql
CREATE KEYSPACE poc WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'datacenter1': 3
};

CREATE TABLE poc.sensor_by_day (
  sensor_id text,
  day       date,
  ts        timestamp,
  value     double,
  PRIMARY KEY ((sensor_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);
```

The partition key is `(sensor_id, day)`, not `sensor_id` alone. Bucketing a time series by day bounds the partition: a sensor that reports for two years does not accumulate one enormous partition that has to be read, repaired and compacted as a unit. This is the single most common modeling mistake in Cassandra-family stores, and it does not show up until the partition is already too big to fix comfortably.

Three rows are enough for the whole exercise:

```bash
docker exec scylla-ha-scylla1-1 cqlsh -e "
INSERT INTO poc.sensor_by_day (sensor_id, day, ts, value) VALUES ('s1','2026-06-07','2026-06-07 09:00:00',42.0);
INSERT INTO poc.sensor_by_day (sensor_id, day, ts, value) VALUES ('s1','2026-06-07','2026-06-07 09:01:00',43.5);
INSERT INTO poc.sensor_by_day (sensor_id, day, ts, value) VALUES ('s1','2026-06-07','2026-06-07 09:02:00',41.2);"
```

**Verify.**
{: .verify}

```console
cqlsh> SELECT count(*) FROM poc.sensor_by_day;

 count
-------
     3

(1 rows)
```

## Step 4 — Confirm RF=3, then lose a node

Before testing the failure, confirm the replication actually landed where you think it did. `nodetool getendpoints` answers "which nodes hold this partition" for a specific partition key.

```bash
docker exec scylla-ha-scylla1-1 nodetool getendpoints poc sensor_by_day "s1:2026-06-07"
```

**Verify.** Three addresses, one per node, because RF=3 on a three-node ring means every node is a replica:
{: .verify}

```console
172.21.0.2
172.21.0.3
172.21.0.4
```

Now stop one node and read at QUORUM. QUORUM of RF=3 is 2, so two survivors are exactly enough.

```bash
docker stop scylla-ha-scylla2-1
```

**Verify.**
{: .verify}

```console
cqlsh> CONSISTENCY QUORUM;
Consistency level set to QUORUM.
cqlsh> SELECT count(*) FROM poc.sensor_by_day;

 count
-------
     3

(1 rows)
```

That is the whole availability claim, checked. Stop a second node and the same query starts failing with an unavailable exception, which is also correct — at that point the cluster cannot prove it is returning current data, so it refuses rather than guessing.

Bring the node back before continuing:

```bash
docker start scylla-ha-scylla2-1
```

## Step 5 — Take a snapshot on every node

`nodetool snapshot` flushes memtables and then hardlinks the current SSTables into a `snapshots/<tag>` directory under the table. It costs almost nothing at the moment you take it, because hardlinks; it starts costing disk later as compaction replaces the live files and the snapshot keeps the old ones alive.

A snapshot is per node. There is no cluster-wide snapshot command — you run it everywhere.

```bash
for n in 1 2 3; do
  docker exec scylla-ha-scylla$n-1 nodetool snapshot -t poc_bkp poc
done
```

**Verify.** The snapshot directory exists under the table directory:
{: .verify}

```console
$ docker exec scylla-ha-scylla1-1 sh -c 'ls -d /var/lib/scylla/data/poc/sensor_by_day-*/snapshots/poc_bkp'
/var/lib/scylla/data/poc/sensor_by_day-6f1c8ad0-6373-11f1-9c4d-3a17e2c3b901/snapshots/poc_bkp
```

The UUID in that path is the table's identity, and it will be different on your ring. Remember that it is there. It becomes the third gotcha in Step 7.

## Step 6 — Destroy the data

The loss scenario. `TRUNCATE` rather than a dropped table, because truncate is the mistake people actually make — it is one word away from a `SELECT` in a terminal that is pointed at the wrong environment.

```bash
docker exec scylla-ha-scylla1-1 cqlsh -e "TRUNCATE poc.sensor_by_day;"
```

**Verify.**
{: .verify}

```console
cqlsh> SELECT count(*) FROM poc.sensor_by_day;

 count
-------
     0

(1 rows)
```

## Step 7 — Why the obvious restore does nothing

The obvious restore is: copy the snapshot's SSTables back next to the live ones, then tell the node to pick them up.

```bash
docker exec scylla-ha-scylla1-1 sh -c '
  cp /var/lib/scylla/data/poc/sensor_by_day-*/snapshots/poc_bkp/* \
     /var/lib/scylla/data/poc/sensor_by_day-*/'
docker exec scylla-ha-scylla1-1 nodetool refresh poc sensor_by_day
```

That command exits 0. It prints nothing. And the count is still zero.

<div class="callout callout--gotcha" markdown="1">
**Gotcha 1 — `refresh` only reads `upload/`.** `nodetool refresh` does not scan the table directory. It scans the table's `upload/` subdirectory, loads whatever valid SSTables it finds there, and returns. Files sitting directly in the table directory are not an error and not a warning; they are simply not looked at. Create `upload/` if it does not exist and put the files inside it.
</div>

Move the files into `upload/` and refresh again, and the count is *still* zero. That is the second behavior.

<div class="callout callout--gotcha" markdown="1">
**Gotcha 2 — `TRUNCATE` leaves a marker that hides older SSTables.** Truncate does not just delete files. It records a truncation record for the table, and every SSTable whose data predates that record is treated as truncated away, no matter how it arrived on disk afterwards. Loading a pre-truncate snapshot into a table that has been truncated gets you nothing. The marker belongs to the table, so the way out is `DROP TABLE` and recreate — which discards the marker along with the table.
</div>

So: drop, recreate, copy into `upload/`, refresh. And it is still zero, for a third reason.

<div class="callout callout--gotcha" markdown="1">
**Gotcha 3 — a recreated table gets a new UUID and a new directory.** The on-disk path is `<table_name>-<table_id>`, and `DROP` + `CREATE` mints a fresh id. The old directory survives on disk with your snapshot inside it, which is why nothing looks broken. You are loading files into a directory that no longer belongs to any live table. The live one is the directory whose suffix matches `system_schema.tables.id` for that table.
</div>

Three behaviors, three silent no-ops, one restore that has to be done in a specific order to work.

## Step 8 — The restore that works

The ordering matters: stage the snapshot files **out** of the table directory first, because the drop in the next command takes the directory context with it.

Stage on every node:

```bash
for n in 1 2 3; do
  docker exec scylla-ha-scylla$n-1 sh -c '
    mkdir -p /tmp/stage &&
    cp /var/lib/scylla/data/poc/sensor_by_day-*/snapshots/poc_bkp/* /tmp/stage/'
done
```

Drop and recreate the table, which discards the truncation marker:

```bash
docker exec scylla-ha-scylla1-1 cqlsh -e "DROP TABLE poc.sensor_by_day;"
docker exec scylla-ha-scylla1-1 cqlsh -e "
CREATE TABLE poc.sensor_by_day (
  sensor_id text, day date, ts timestamp, value double,
  PRIMARY KEY ((sensor_id, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC);"
```

Confirm which directory is now the live one. The id here is what the directory suffix has to match:

```bash
docker exec scylla-ha-scylla1-1 cqlsh -e "
SELECT id FROM system_schema.tables
 WHERE keyspace_name='poc' AND table_name='sensor_by_day';"
```

```bash
docker exec scylla-ha-scylla1-1 sh -c 'ls -d /var/lib/scylla/data/poc/sensor_by_day-*'
```

You will see at least two directories: the stale one from before the drop, and the new live one. Copy into the new one's `upload/`, on every node:

```bash
for n in 1 2 3; do
  docker exec scylla-ha-scylla$n-1 sh -c '
    LIVE=$(ls -dt /var/lib/scylla/data/poc/sensor_by_day-* | head -1)
    echo "$LIVE"
    mkdir -p "$LIVE/upload"
    cp /tmp/stage/* "$LIVE/upload/"
    chown -R scylla:scylla "$LIVE/upload"'
done
```

<div class="callout callout--warn" markdown="1">
**Check the directory, do not trust the sort.** `ls -dt | head -1` picks the most recently modified directory, which is the newly created one on a clean run. If you have dropped and recreated the table more than once, or touched the stale directory in between, that heuristic will pick the wrong one. Compare the printed path against the `id` you just read from `system_schema.tables` before you trust it.
</div>

Now refresh, on every node:

```bash
for n in 1 2 3; do
  docker exec scylla-ha-scylla$n-1 nodetool refresh poc sensor_by_day
done
```

**Verify.**
{: .verify}

```console
cqlsh> CONSISTENCY QUORUM;
Consistency level set to QUORUM.
cqlsh> SELECT count(*) FROM poc.sensor_by_day;

 count
-------
     3

(1 rows)
```

Three rows, read at QUORUM, restored from a snapshot taken before a truncate. `nodetool tablestats` will confirm the loaded files are being served — on my run it reported a read count of 40 and an SSTable count of 6 for this table after the exercise.

```bash
docker exec scylla-ha-scylla1-1 nodetool tablestats poc.sensor_by_day
```

Two things worth saying about what this restore is and is not. First, snapshots are per node and this ring is RF=3, so every node had a complete copy and loading all three was straightforward; on a larger ring with RF smaller than the node count, each node's snapshot is a different subset and the staging has to keep them apart. Second, `refresh` is a load, not a repair. Real disaster recovery on this engine also involves `nodetool repair` for anti-entropy and node `rebuild` to restream from replicas, and `gc_grace_seconds` governs when tombstones can actually be collected — get that wrong and you resurrect deleted rows.

For monitoring, ScyllaDB exposes Prometheus metrics on port 9180 — `scylla_storage_proxy_*` for coordinator-side latency and errors, and reactor utilization for the shard-per-core saturation signal that is specific to this engine.

## Step 9 — Clean up

```bash
docker compose -f scylla-ha/docker-compose.yml down -v
```

**Verify.**
{: .verify}

```console
$ docker volume ls --filter name=scylla-ha
DRIVER    VOLUME NAME
```

Three nodes' worth of SSTables and snapshots come to real disk. `down` without `-v` keeps all of it.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Node exits at startup: `system does not satisfy minimum AIO requirements` | `fs.aio-max-nr` in the Docker VM is below what Seastar reserves per reactor | `docker run --rm --privileged alpine sysctl -w fs.aio-max-nr=1048576`, then restart the node |
| That AIO fix worked yesterday and does not today | Docker Desktop restarted and rebuilt its VM, discarding the sysctl | Re-run the privileged sysctl container after every restart |
| `nodetool refresh` exits 0 and nothing is loaded | SSTables are in the table directory, not in `upload/` | Copy them into `<table-dir>/upload/` and refresh again |
| Files are in `upload/`, refresh is clean, rows still missing | A `TRUNCATE` marker is hiding every SSTable older than the truncate | `DROP TABLE` and recreate, then load the snapshot into the new table |
| Restore works on one node, count is short at QUORUM | `refresh` was only run on some nodes | Run `nodetool snapshot` and `nodetool refresh` on every node |
| Refresh finds nothing right after a `DROP` + `CREATE` | The recreate minted a new table UUID, so the directory you loaded is stale | Read `system_schema.tables.id` and load into the directory whose suffix matches it |
| Refresh logs a permission error | Files were copied into `upload/` as root, and the server runs as `scylla` | `chown -R scylla:scylla <table-dir>/upload` before refreshing |
| A joiner sits at `UJ` for a long time | Bootstrap streaming on a one-shard, 1200 MB node is slow, not stuck | Wait, and watch progress with `nodetool netstats` |
| A joiner never appears in `nodetool status` | All three nodes were started at once, before the seed was `UN` | Start `scylla1`, wait for `UN`, then start `scylla2` and `scylla3` one at a time |
| `SELECT` fails with an unavailable exception at QUORUM | Two of three nodes are down, so QUORUM of RF=3 cannot be met | Bring a node back; do not lower the consistency level to hide it |

The next post in this series is [PostgreSQL 18 won't take a volume at /var/lib/postgresql/data](/writing/postgresql-18-docker-volume-path-change/). The rig itself, and the full eight-scenario results matrix, is in [A failover lab you can run on one laptop](/writing/failover-lab-six-engines-eight-scenarios/).
