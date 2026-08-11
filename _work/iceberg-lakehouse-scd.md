---
title: "Slowly-changing dimensions at petabyte scale on Iceberg"
hook: "Petabyte-scale slowly-changing dimensions without a warehouse bill"
description: "Slowly-changing dimensions over a multi-petabyte Iceberg lakehouse on S3: MERGE-based SCD2, hidden partitioning, compaction, and a 35% smaller bill."
kind: production
order: 3
featured: true
role: "Data Engineer"
org: "UXCam"
period: "2021 – 2023"
team: "Designed and led by me, inside the data team, with the analytics consumers as reviewers"
scale: "Multi-petabyte table footprint; 10 TB+ landing per day; years of history that had to stay queryable"
stack: [Apache Iceberg, Apache Spark, PySpark, Amazon S3, AWS Glue Data Catalog, Trino, dbt, Databricks, Unity Catalog]
metrics: [storage_cost, daily_volume]
tags: [iceberg-lakehouse, spark, cost-finops]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

Underneath UXCam's data platform is a storage layer holding years of mobile-analytics history at multi-petabyte scale. Before the Iceberg migration it was what most lakes are: Parquet files on S3 under Hive-style partition directories, registered in a catalog, read by Spark and Trino.

That works until it doesn't, and it stops working in three specific ways.

**There are no atomic commits.** A job that rewrites a partition is visible to readers halfway through. You end up scheduling around it — nobody queries between 02:00 and 04:00 — which is a social solution to a technical problem, and social solutions do not survive a new team member.

**Schema changes are rewrites.** Changing a type, renaming a field, or reorganizing a partition scheme means rewriting history, and at petabyte scale that is a project rather than a task. So people stop doing it. The schema calcifies around whatever was convenient in 2019 and new requirements get bolted on as side tables.

**Nothing tracks what changed.** Mobile analytics has genuine dimension churn: an app changes its name, its plan, its retention setting; a device model gets reclassified. If you only store the current value, every historical report silently rewrites itself when a dimension changes. A funnel from eight months ago should be computed with the app's configuration as it was eight months ago.

The obvious answer to all three is a warehouse. The problem with that answer is arithmetic: at this footprint the bill for keeping full history in Snowflake or Redshift was not something the business was going to sign. So the requirement became: get warehouse semantics on top of S3 object storage, and get them cheaply.

## Constraints

**There was no budget to put the full history in a warehouse.** This is the constraint that determined the entire design. Everything else follows from it.

**Ingest could not stop.** The same no-freeze-window constraint from [the platform migration](/work/uxcam-data-platform/) applies here: data lands continuously, so every migration step had to be a dual-read or dual-write, never a cutover.

**Backfills could not block readers.** Rewriting historical partitions is a normal operation on a table like this. It happens after a bug fix, a schema correction, or a late-arriving data repair. If a backfill makes the table unreadable, backfills stop happening and bugs stay unfixed.

**Multiple engines had to read the same tables.** Spark writes them, Trino serves ad-hoc and federated queries, Databricks reads them for governed collaborative work. Any format fully readable by only one of those was disqualified regardless of its other merits.

**The history had already changed shape several times.** Not a greenfield model. Years of accumulated schema decisions, including some that were wrong, had to stay queryable through the migration. "Fix the model and reload" was not available.

**Per-subject deletion had to stay possible.** GDPR-aware retention means deleting a subject's data and proving it, which constrains physical layout: you cannot pick a clustering scheme that turns a deletion into a full-table rewrite.

**The SCD semantics had to stay understandable to analysts.** Someone writing SQL in dbt has to get the right answer without reading the merge logic. A technically superior model that produces wrong results when queried naively is a worse model.

## Architecture

```text
              streaming + batch writers (Spark)
                          |
                          v
   +---------------------------------------------------+
   |  bronze  — append-only, tolerant, quarantine table |
   |            raw shape preserved, nothing rejected   |
   +---------------------------------------------------+
                          |
                          v
   +---------------------------------------------------+
   |  silver  — typed, deduped facts (append-only)      |
   |            + dimensions maintained as SCD Type 2   |
   |              via MERGE INTO on a narrow table      |
   +---------------------------------------------------+
                          |
                          v
   +---------------------------------------------------+
   |  gold    — dbt-modeled marts, one grain per table  |
   +---------------------------------------------------+

   all three are Apache Iceberg tables on Amazon S3
   catalog: AWS Glue Data Catalog

   maintenance jobs (scheduled, with their own SLOs):
     - bin-pack compaction        (small-file control)
     - rewrite manifests          (planning cost control)
     - expire snapshots           (metadata + orphan bytes)
     - remove orphan files        (failed-write cleanup)

   readers: Spark · Trino · Databricks + Unity Catalog
```

**Bronze** is append-only and deliberately permissive. Records that fail the data-quality contract land in a quarantine table with their failure reason rather than being dropped, because the producers are SDKs in apps we cannot recall and the payload we reject today is one we can never ask for again.

**Silver** splits into two things people often model the same way. Facts — sessions, events, screens — are append-only, immutable and enormous. Dimensions — apps, plans, device classifications, SDK versions — are small, mutable, and where all the temporal logic lives. Facts get no update path. Dimensions get SCD Type 2.

**The SCD Type 2 mechanism** is an Iceberg `MERGE INTO` against a narrow dimension table carrying `valid_from`, `valid_to` and `is_current`. Each run compares the incoming snapshot against current rows, closes the ones whose tracked attributes changed, and inserts the new versions. Facts join on the key plus an event-timestamp-between-validity-window predicate, which is what makes an eight-month-old funnel compute with eight-month-old configuration. For analysts who do not want to think about that, gold exposes a current-only view of each dimension; the historical join is available, not mandatory.

**Hidden partitioning** is the Iceberg feature that mattered most day to day. Partitioning is a property of the table, expressed as a transform — day-truncation on the event timestamp, bucketing on the high-cardinality key. Query authors write a predicate on the timestamp and Iceberg maps it to partitions. Nobody has to remember to also filter on a derived `dt` column, which is the most common source of accidental full-table scans in a Hive-layout lake.

**Maintenance is scheduled infrastructure, not a chore.** Compaction, manifest rewriting, snapshot expiry and orphan-file removal each run on their own cadence with their own alerting. Treating these as optional is how a lakehouse becomes slower and more expensive than the lake it replaced.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost us |
|---|---|---|---|
| Apache Iceberg as the table format | Delta Lake | Engine neutrality was the deciding factor. Spark writes, Trino serves, Databricks reads — all three had to be first-class. Hidden partitioning also removed an entire class of user error we were living with daily. | At the time we adopted it, Iceberg shipped fewer batteries. We wrote and scheduled our own compaction, expiry and orphan-cleanup jobs. On Databricks specifically, Delta's tooling was better and we knowingly gave that up. |
| SCD Type 2 by `MERGE INTO` on a narrow dimension | Rebuild the dimension table from scratch each day | A full rebuild is O(history) and got measurably slower every month it ran. A merge is O(change), and change is small. | Merges write delete files. Read amplification grows steadily between compaction runs, which promoted compaction from a background nicety to a scheduled job with its own SLO and its own pager. |
| Facts stay append-only; only dimensions are mutable | Type 2 semantics everywhere, including facts | Rewriting fact partitions at this volume is not economically possible, and a mutable fact table invites people to try. | Any late correction to a fact has to be expressed as a compensating row, and every downstream consumer has to know that and sum accordingly. That is a real cognitive tax on every new analyst, and it has bitten people. |
| Hidden partitioning (day truncation + bucketing) | Explicit partition columns in the schema | Query authors stopped needing to know the physical layout, and we could change the layout later without breaking existing SQL. | Partition evolution is not retroactive. Older snapshots keep the old layout, so a query spanning the change point plans against two schemes and costs more. You are trading a permanent small cost for a one-time large one. |
| Expire snapshots on a fixed window | Unlimited time travel | Metadata files, manifests and orphaned data were a genuine share of the storage bill — not a rounding error at this footprint. | We lost time travel beyond the window. At least one investigation needed data from before the horizon and had to be served from a separate archive, slowly and manually. |
| Bronze accepts everything and quarantines failures | Reject non-conforming records at write time | Producers are SDKs in apps we cannot recall. Rejected data is gone permanently; quarantined data is repairable. | Bronze is large, messy and costs storage. Every silver job carries coercion logic, and the quarantine table needs its own retention policy that nobody wants to own. |

The contested decision here was Iceberg versus Delta. The argument for Delta was not weak: we were already paying for Databricks, Delta was native there, and standardizing on the vendor's format meant less code to write and better tooling on day one. What tipped it was Trino. A meaningful share of our query volume comes through Trino, and being second-class in the engine that serves the most queries is not a trade I was willing to make to save a few maintenance jobs. Had Trino been a smaller part of the mix, I would have gone the other way.

## Results

The migration to Iceberg cut the **S3 bytes-stored billing line by 35%**, measured before and after across 2022–2023 on a multi-petabyte footprint. Three things produced that, roughly in order: compaction eliminating a long tail of small files accumulated over years of streaming writes; snapshot expiry and orphan-file removal reclaiming space the old layout had no mechanism to reclaim at all; and better file sizing on new writes.

Worth stating plainly, because it is what a number like this hides: that is the storage line specifically. Compute went up slightly, since compaction and manifest rewriting are jobs that did not previously exist. The net was strongly positive, but "35% lower storage cost" is not "35% lower total cost."

The layer absorbs the platform's full **10 TB+ per day** of landing volume, per Spark job metrics, and its history stayed queryable across the schema changes that happened during and after the migration. Storage cost made the project fundable. Schema evolution without rewrites made it worth doing.

## Running it

**SLOs.** Freshness on the gold marts is the user-facing one. Behind it sit three that only the data team looks at, and they are the ones that predict trouble: compaction backlog as the count of files below target size, manifest count per table as a proxy for planning cost, and snapshot age distribution. When those three are healthy, freshness takes care of itself. When they are not, freshness fails a week later.

**On-call.** Shared with the wider platform rotation. Maintenance-job failures do not page on the first occurrence — a failed compaction run is recoverable and the next run absorbs it. Two consecutive failures page, because that is where the backlog starts compounding.

**Three failure modes we actually see:**

*Compaction falls behind and small files explode.* A burst of streaming writes, or a compaction job that failed quietly for two days, and suddenly planning takes longer than execution. The symptom is query latency rising with no change in data volume. Runbook: check file-count-below-threshold first, run targeted bin-pack compaction on the affected partitions rather than the whole table, and only then investigate why the scheduled job stopped. Compacting the whole table to fix one partition is a mistake I have watched people make under pressure.

*Concurrent writers conflict on the same partition.* Iceberg commits are optimistic: two jobs writing one partition means one commits and one retries, and an aggressive retry window turns that into a storm that starves both. Runbook: identify the writers, confirm whether the overlap is by design, and if it is, serialize them at the scheduler rather than tuning retry parameters. Retry tuning treats the symptom and the symptom comes back.

*A long-running query outlives a snapshot.* A Trino query planned against snapshot N, expiry ran, and the files it meant to scan are gone. It fails mid-scan with an error that does not obviously say "your snapshot expired." Runbook: check the expiry job's run time against the query start time before debugging the query at all — the error message sends people in the wrong direction. The structural fix is a retention window comfortably longer than the slowest legitimate query, and we widened ours after this happened.

## What I'd do differently

**I set the compaction and expiry policy after the first backfill, not before it.** The initial migration wrote a very large number of files at a size that made sense for the write job and none at all for the read path, so we spent real compute rewriting data we had just written. That policy belongs in the table definition from the first commit — it is not an operational detail, it is part of the schema in every way that matters.

**I wrote the SCD Type 2 merge as per-table SQL; it should have been one library.** Each dimension got its own hand-written merge statement, and they drifted. Two of them handled the "attribute changed back to a previous value" case differently, which produced a confusing bug that took far too long to find because the merges looked similar enough that nobody diffed them. One parameterized implementation with one test suite would have cost a day and saved a week.

**I did not monitor metadata growth as a first-class signal.** I watched data volume closely and manifest count not at all. Manifest count drives query planning time on a table this size, and by the time it shows up as slow queries it has been growing for weeks. It is an SLI now; it should have been one from the first week.
