---
title: "Validate said SUCCESS. The upgrade would have died halfway."
seo_title: "Hive Metastore 4 upgrade: clone rehearsal, schematool, blue/green"
description: "A Hive Metastore 4 upgrade rehearsed on a clone: zero constraints, a validator that passed anyway, and why the plan became blue/green."
date: 2026-10-03 08:00:00 +0545
last_modified_at: 2026-10-03
type: essay
series: production-notes
series_order: 2
tags:
  - iceberg-lakehouse
  - spark
  - observability-slo
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - Hive Metastore upgrade
  - schema migration rehearsal
  - blue/green database cutover
mentions:
  - Apache Hive
  - Apache Spark
  - Trino
  - PostgreSQL
  - kube-state-metrics
cover:
  base: "/assets/images/editorial-hms-upgrade-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: schematool -validate reports five SUCCESS lines while a restored clone shows zero constraints and an upgrade that fails after its first script commits"
  caption: "The validator checked that the tables existed. The upgrade needed the constraints inside them."
faq:
  - q: "Does Spark 4 work with Hive Metastore 4?"
    a: "Not with its default client. Spark 4.2 ships a Hive 2.3.10 metastore client that calls the bare get_table Thrift method, which HMS removed in 4.0.1, so it fails with Invalid method name: 'get_table'. Set spark.sql.hive.metastore.version to 4.1.0 with matching client jars, and bump any HiveMetaStoreClient your application builds itself."
  - q: "Why does schematool -validate pass on a metastore that cannot be upgraded?"
    a: "Its checks cover the schema version, sequence numbers, table presence, DFS locations and NULL columns. None of them compares constraints or indexes with a freshly initialised schema, and the upgrade scripts alter constraints by name. Compare pg_constraint and pg_indexes against a reference database instead."
  - q: "How long does a Hive Metastore 3.1 to 4.2 schema migration take?"
    a: "On a restored clone of a staging metastore with tens of thousands of partitions on a small Postgres instance, the seven upgrade scripts took 115 seconds of wall clock, and the full write-stop window was about four minutes. One script took 59.3 seconds of that. Measure your own clone; the dominant step appears to scale with partition count."
  - q: "Should a Hive Metastore upgrade be in-place or blue/green?"
    a: "Blue/green, if you can afford a second database for a day. In-place migrates the only copy one way, so rollback is a snapshot restore. Blue/green migrates a restored copy, validates it before any consumer moves, and rolls back by changing a URI."
key_takeaways:
  - "schematool -validate printed five SUCCESS lines for a metastore with zero constraints and zero indexes; a fresh schema at the same version has 133 and 48."
  - "On that database the upgrade failed in its second script, after the first had already committed, leaving a half-migrated metastore whose only exit is the snapshot."
  - "Spark's metastore version setting caps the client it loads, not the server it talks to: a 4.1.0 client against a 4.2.1 server is valid, and 4.2.1 is where the partition-name SQL injection is fixed."
  - "Measured on the clone, the write-stop window was about four minutes, with one of seven scripts taking 59.3 seconds — numbers that only exist because the rehearsal ran on real data."
  - "Blue/green turned the rollback from a snapshot restore into a URI change, and stopping streaming instead of letting registrations fail removed a mandatory backfill."
---

The runbook was four lines long. Snapshot the database, run `schematool -validate`, run `schematool -upgradeSchema`, start the new server. Validate came back with five `[SUCCESS]` lines, which is the condition the runbook said to wait for. A rehearsal on a throwaway schema had already run all six upgrade scripts clean.

On a restored clone of the real metastore, the upgrade failed in its second script — after the first one had committed. That leaves a database at schema 3.2.0, which neither the old server nor the new one was built to run against, and a single way out: the snapshot. The validator had looked at exactly that database and passed it.

**Operating rule.** A check that confirms things *exist* is not a check that they are *intact*. Rehearse a one-way migration on a restored clone of the database you are about to change, and treat every green signal along the way as a claim that still has to name what it inspected.

## Why the versions had to move together

The upgrade was forced by an API removal, and the removal decided the target version before anything else did.

[HIVE-26537](https://github.com/apache/hive/pull/3599) removed the deprecated Thrift methods from the metastore interface, including the bare `get_table`. The first release without them is 4.0.1. Spark 4.2 still bundles a Hive 2.3.10 metastore client, and that client calls the bare method. The result against any server from 4.0.1 onward is the error [PyIceberg users reported against 4.0.1](https://github.com/apache/iceberg-python/issues/1222):

```text
TApplicationException: Invalid method name: 'get_table'
```

| HMS server | bare `get_table` | minimum JDK |
| --- | --- | --- |
| 3.1.3 (the starting point) | present | 8 |
| 4.0.0 | present | 8 |
| 4.0.1 | removed | 8 |
| 4.1.0 | removed | 17 |
| 4.2.0 / 4.2.1 | removed | 21 |

The setting that fixes it is easy to misread. [`spark.sql.hive.metastore.version`](https://spark.apache.org/docs/latest/sql-data-sources-hive-tables.html) constrains the **client** Spark loads, not the server it talks to. Spark 4.2 documents client ranges up to 4.1.0. The server can be newer, provided its IDL still declares every method the client calls — and the 4.2.1 IDL does: `get_table_req`, `add_partitions_req`, `drop_partition_req`, `get_partitions`, `get_database`.

That pairing mattered because of what 4.2.1 fixes. [CVE-2026-49845](https://www.mail-archive.com/announce@apache.org/msg11789.html) (HIVE-29622) is a SQL injection in the metastore's partition-name direct-SQL paths, affecting 4.0.0 through 4.2.0. There is no 4.1.1. A 4.1.0 *server* would have meant upgrading onto a known critical issue, in partition-name lookups that a metastore serving a streaming writer exercises all day. So: server 4.2.1, client 4.1.0.

```properties
spark.sql.hive.metastore.version=4.1.0
spark.sql.hive.metastore.jars=path
spark.sql.hive.metastore.jars.path=file:///opt/hive-client/*
```
{: data-file="spark-defaults.conf" }

Two consequences follow. First, there is no configuration in which the old and new Spark settings both work against one server, so the metastore and the Spark client change land together, per environment. Second, those three properties govern only Spark's own catalog client. A `HiveMetaStoreClient` your application constructs directly comes from the application classpath and ignores them; it needs its own bump, with the 2.3.10 jar evicted, or partition registration fails with the same `Invalid method name`.

## What the clone found

The first rehearsal was synthetic. I created a 3.1.0 schema with the production image itself, seeded a table shaped like the real ones, and migrated it with the new image. Six scripts, `Completed` each, data intact, server serving. That rehearsal proved the image and the scripts. It proved nothing about the database.

The second rehearsal ran on a snapshot of the live staging metastore, restored into a new instance. The source was checked before and after and never touched. Before migrating anything I compared it with a freshly initialised schema at the same version:

```text
                    live metastore    fresh initSchema 3.1.0
constraints                      0                       133
explicit indexes                 0                        48
```

No primary keys, no foreign keys, no unique constraints, no indexes — across tens of thousands of partitions. I do not know how the database got that way, and for the upgrade it does not matter. The upgrade scripts alter and drop constraints *by name*, so they assume the reference schema is there:

```text
Upgrade script upgrade-3.1.0-to-3.2.0.postgres.sql          Completed
Upgrade script upgrade-3.2.0-to-4.0.0-alpha-1.postgres.sql
  Error: constraint "UNIQUE_WM_RESOURCEPLAN" of relation "WM_RESOURCEPLAN" does not exist
  Aborting command set because "force" is false
  Upgrade FAILED! Metastore state would be inconsistent !!
```

Note where it stops. The first script has committed, so the database now says 3.2.0 — a version neither the old server nor the new one was built to run against. In production that is a metastore outage with a snapshot restore as its only exit.

Then the part that justifies the rest of this post. On that same database:

```text
$ schematool -dbType postgres -validate
Validating schema version ......................... [SUCCESS]
Validating sequence number for SEQUENCE_TABLE ..... [SUCCESS]
Validating metastore schema tables ................ [SUCCESS]
Validating DFS locations .......................... [SUCCESS]
Validating columns for incorrect NULL values ...... [SUCCESS]
Done with metastore validation: [SUCCESS]
```

The validator's own output lists what it checks: version, sequences, that the tables exist, locations, NULLs. Nothing in that list is "constraints and indexes match the reference". It answered its questions correctly. They were not the questions the upgrade was going to ask.

Restoring the constraints surfaced the drift those constraints would have prevented. Both items were found only by trying:

- **2,415 orphan rows in `PARTITION_PARAMS`** pointing at partitions that no longer existed — leaked precisely because there was no foreign key to cascade the deletes.
- **One table name registered twice** in the same database, both empty, a leftover from a retired proof of concept. The `UNIQUETABLE` constraint cannot be created until one goes.

A sweep of ten other child tables found zero orphans and no duplicate IDs, so the damage was contained. After cleanup the clone matched the reference exactly, 133 of 133, and the migration ran clean. The queries are short enough to run before any metastore upgrade:

```sql
-- Run on the live metastore AND on a fresh `schematool -initSchema` at the same version.
SELECT count(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace;
SELECT count(*) FROM pg_indexes    WHERE schemaname   = 'public';

-- Rows that a foreign key would have removed.
SELECT count(*)
FROM "PARTITION_PARAMS" pp
LEFT JOIN "PARTITIONS" p ON p."PART_ID" = pp."PART_ID"
WHERE p."PART_ID" IS NULL;

-- Names that would block UNIQUETABLE.
SELECT "DB_ID", "TBL_NAME", count(*)
FROM "TBLS"
GROUP BY 1, 2
HAVING count(*) > 1;
```
{: data-file="metastore-readiness.sql" }

Zero indexes is also a problem with no upgrade attached. Every partition lookup becomes a sequential scan. I think that contributes to the metastore socket timeouts seen on queries without a partition filter, but I have not isolated it, so it stays an inference.

## The window, measured rather than guessed

The question I had been asked was how long writes would have to stop. The clone answered it with numbers, which an estimate had not.

| Step | Measured | Writes stopped? |
| --- | --- | --- |
| Database snapshot | 160 s | no |
| De-duplicate the doubled table | 3 s | no — do it days ahead |
| Delete 2,415 orphan rows | 3 s | no — do it days ahead |
| Restore 133 constraints and 48 indexes | ~60–95 s | yes |
| `schematool -upgradeSchema` 3.1.0 → 4.2.0 | 115 s | yes |
| `-info` and `-validate` | 46 s | yes |
| New server start to `Started the new metaserver` | 28 s | — |

About four minutes of write stop, plus pod drain. The migration was seven scripts, not the six the 4.1 plan expected, because 4.2 adds one — and one script dominates:

```text
upgrade-3.1.0-to-3.2.0                    2.9 s
upgrade-3.2.0-to-4.0.0-alpha-1            6.4 s
upgrade-4.0.0-alpha-1-to-4.0.0-alpha-2   59.3 s
upgrade-4.0.0-alpha-2-to-4.0.0-beta-1     6.4 s
upgrade-4.0.0-beta-1-to-4.0.0             8.4 s
upgrade-4.0.0-to-4.1.0                    6.7 s
upgrade-4.1.0-to-4.2.0                    7.5 s
                                sum      97.6 s   (wall clock 115 s)
```

These numbers do not transfer. The other environments' metastore databases run on different instance sizes and do not even share a Postgres major version with staging. The dominant script appears to scale with partition count. Each environment gets its own constraint check and its own clone before anyone commits to a window.

<div class="callout callout--note" markdown="1">
**Boundary.** Every figure here was measured on a restored clone of the staging metastore, or in local containers built from the deploy image. Nothing ran against production, and production's constraint state was unknown when this plan was written. Two claims are inferences, not measurements: that the 59.3-second script scales with partition count, and that the missing indexes contribute to metastore timeouts.
</div>

## Why the plan became blue/green

The clone changed the risk model. An in-place migration of a database that might be drifted means betting the only copy on a one-way operation. So the plan stopped migrating the live database at all.

| | In-place | Blue/green |
| --- | --- | --- |
| Live database | migrated one way | untouched |
| Rollback | restore snapshot and revert image | change a URI back |
| Validation | after the fact, on the live copy | before any consumer moves |
| Trino during the work | down | keeps reading the old metastore |
| Partitions registered during the freeze | lost to a swallowed exception — backfill required | none attempted — streaming is stopped |

That last row was the biggest win, and it came from reading the writer rather than the metastore. In the in-place plan, streaming kept running while the metastore was down. Its partition registrations failed into a caught-and-logged exception, and because each batch only registers partitions it has not seen before, they were never retried. A partition first seen during the window would have stayed missing from Hive indefinitely. Stopping streaming instead lets the stream retain the records and the job resume from its checkpoint: no gap, no backfill, provided the stream's retention outlasts the freeze.

The sequence follows from that. Snapshot, restore into a new instance, clean up and migrate *that*, validate it, then bring up a second metastore Deployment pointed at it. Move Trino first, because Trino only reads and switching back is trivial. Move Spark second. Unsuspend the batch rewrite job last.

Rollback is free until Spark writes to the new metastore. After that, every partition registered on green is missing from blue, so rolling back means a backfill. A job that deletes and rewrites files is worse still: roll back after it runs and the old metastore points at files that no longer exist. The longer Spark writes to green, the more the rollback costs. Decide fast.

<div class="callout callout--gotcha" markdown="1">
**The selector trap.** If the new Deployment reuses the old pods' `app.kubernetes.io/name` label, the *existing* Service selects the new pods too. Thrift calls then round-robin between a 3.1.0 schema and a 4.2.0 one — intermittent, and very confusing. Give the green stack a distinct label value and its own Service.
</div>

Apache's official `standalone-metastore` image carries three more defaults worth knowing. Its [entrypoint](https://github.com/apache/hive/blob/rel/release-4.2.1/packaging/src/docker/entrypoint.sh) runs `schematool -initOrUpgradeSchema` on every start unless `IS_RESUME=true` — three replicas, three concurrent migrations. `DB_DRIVER` defaults to Derby. And it adds `-Xmx1G` to the heap options, which, with JVM overhead on top, overruns a container limited to 1 GiB.

```yaml
env:
  - { name: DB_DRIVER, value: postgres }  # the image defaults to derby
  - { name: IS_RESUME, value: "true" }    # otherwise every replica migrates on start
resources:
  limits: { memory: 2Gi }                 # the entrypoint already sets -Xmx1G
```
{: data-file="hive-metastore-green-deploy.yaml" }

One config value breaks silently. On Hadoop 3.4, S3A uses AWS SDK v2, and [V1 credential-provider class names must be replaced](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/aws_sdk_upgrade.html). With the old `com.amazonaws.auth.WebIdentityTokenCredentialsProvider` left in place, the metastore starts cleanly and then every partition registration fails, because it checks each partition's location in S3. The replacement is `software.amazon.awssdk.auth.credentials.WebIdentityTokenFileCredentialsProvider`.

## Green signals that were lies

The validator was not an isolated case. In the same week, on the same platform, I collected a small set of signals that reported health without having looked.

| Signal | What it reported | What was true |
| --- | --- | --- |
| `schematool -validate` | five `[SUCCESS]` | zero constraints; the upgrade dies after its first commit |
| Batch rewrite job | exit code 0 | the script has no `set -e`; a failed step still exits 0 |
| An in-image `grep -c` | 0 matches — class "missing" | `unzip` is not installed in the image; it counted the output of a failed command |
| kube-state-metrics pod | Running, 0 restarts | its 17.3 MiB response exceeded the scraper's 16 MiB cap, so every `kube_*` series vanished |
| Trino CPU alert | `NoData` | Trino was fine; the alert divides by a kube-state-metrics series, and the denominator had gone |
| Spark job monitor | "No problematic jobs detected", exit 0 | `kubectl` was failing; every list came back empty |
| Executor-failure alert | "6 failed of 166", then 168, then 171 | a lifetime counter against a fixed threshold, with UNKNOWN pods counted as failed |
| Zero-executor check | never fired | the code tested `== 5` |

The scrape-size case has a detail worth keeping. The scrape config already had a keep-list naming the ten metric families the dashboards and alerts use. But metric relabelling runs *after* the response is downloaded and parsed. It governs what is stored, not what is transferred, and the size cap applies to the raw body. Roughly 74% of each scrape was downloaded and immediately thrown away. The fix moved the filter server-side with kube-state-metrics' metric allowlist, which should shrink the payload to roughly the quarter that was being kept. Raising the cap to 32 MiB is headroom, not the fix.

Every row has the same shape. The signal answered a narrower question than the one its reader was asking, and nothing on the screen said so. The fixes are all the same move as the metastore check: make the signal name what it inspected, and make "I could not look" a different state from "I looked and it was fine". The job monitor now reports DEGRADED and exits non-zero when it cannot read the cluster. The failure alert uses a ratio and counts UNKNOWN separately. The metastore runbook compares constraints against a reference instead of trusting `-validate`.

## A readiness checklist for a one-way metastore migration

- Compare `pg_constraint` and `pg_indexes` counts against a fresh `initSchema` at the current version, per environment.
- Run the orphan and duplicate checks; clean up days ahead, outside the window.
- Restore a snapshot into a new instance and run the full migration there, timing every script.
- Treat `-validate` as necessary, never as sufficient.
- Pin the client version Spark loads, and separately bump any metastore client your application builds itself.
- Replace V1 S3A credential-provider class names before the first start, not after the first failed registration.
- Set `IS_RESUME=true` and `DB_DRIVER` on the official image; run the migration once, as a Job.
- Give the green stack a distinct selector label and its own Service.
- Stop streaming instead of letting registrations fail; confirm the stream's retention covers the freeze.
- Move readers first, writers second, rewrite jobs last. Decide on rollback before writers move.
{: .checklist }

## Frequently asked questions

### Does Spark 4 work with Hive Metastore 4?

Not with its default client. Spark 4.2 ships a Hive 2.3.10 metastore client that calls the bare `get_table` Thrift method, which HMS removed in 4.0.1, so it fails with `Invalid method name: 'get_table'`. Set `spark.sql.hive.metastore.version` to 4.1.0 with matching client jars, and bump any `HiveMetaStoreClient` your application builds itself.

### Why does schematool -validate pass on a metastore that cannot be upgraded?

Its checks cover the schema version, sequence numbers, table presence, DFS locations and NULL columns. None of them compares constraints or indexes with a freshly initialised schema, and the upgrade scripts alter constraints by name. Compare `pg_constraint` and `pg_indexes` against a reference database instead.

### How long does a Hive Metastore 3.1 to 4.2 schema migration take?

On a restored clone of a staging metastore with tens of thousands of partitions on a small Postgres instance, the seven upgrade scripts took 115 seconds of wall clock, and the full write-stop window was about four minutes. One script took 59.3 seconds of that. Measure your own clone; the dominant step appears to scale with partition count.

### Should a Hive Metastore upgrade be in-place or blue/green?

Blue/green, if you can afford a second database for a day. In-place migrates the only copy one way, so rollback is a snapshot restore. Blue/green migrates a restored copy, validates it before any consumer moves, and rolls back by changing a URI.

The metastore is the quietest dependency in most lakehouses until it is the loudest. More on the layer it serves in [the lakehouse spine]({{ '/writing/trino-iceberg-polaris-lakehouse-spine/' | relative_url }}) and under [Iceberg & the lakehouse]({{ '/writing/tags/iceberg-lakehouse/' | relative_url }}). The same Spark 4 upgrade produced [a streaming job that succeeded and wrote nothing]({{ '/writing/spark-4-s3a-committer-wrote-nothing/' | relative_url }}) and [a connector benchmark I had to retract]({{ '/writing/spark-4-kinesis-connector-idle-floor/' | relative_url }}).
