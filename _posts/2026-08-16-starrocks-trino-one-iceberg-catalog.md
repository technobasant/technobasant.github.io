---
title: "Two engines, one Iceberg catalog: StarRocks beside Trino, neither holding a key"
description: "Attach StarRocks to the same Polaris REST catalog Trino writes through, measure both on identical data, and check for standing S3 keys."
date: 2026-08-16 09:00:00 +0545
last_modified_at: 2026-08-16
type: tutorial
tags: [iceberg-lakehouse, clickhouse]
series: lakehouse-trino-iceberg
series_order: 4
toc: true
cover:
  base: "/assets/images/editorial-lakehouse-engines-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Diagram: Trino and StarRocks both reading the same Iceberg tables through one Polaris REST catalog, with neither engine holding AWS credentials"
  caption: "The argument for a REST catalog is not the lookup. It is that a second engine inherits both the tables and the authorisation boundary."
featured: false
level: intermediate
time_estimate: "~20 min, mostly waiting for the StarRocks backend to register"
what_youll_build: "StarRocks 4.1.4 attached to the same Polaris catalog Trino writes through, reading the same tables with no copy and no S3 credentials of its own."
prerequisites:
  - "The stack from parts one to three, with silver.orders_enriched populated"
  - "About 3 GB of free container memory — stop Airflow if you are tight"
tested_on: "macOS Darwin 25 · arm64 host · Docker Desktop 8 CPU / 11.67 GB · StarRocks 4.1.4 (allin1) · Trino 483 · Apache Polaris 1.7.0 · MinIO RELEASE.2025-09-07"
key_takeaways:
  - "StarRocks read Trino's Iceberg tables through the same REST catalog with no export, copy, or re-registration."
  - "StarRocks supports Polaris credential vending too — a catalog with no `aws.s3.access_key` at all read the table successfully."
  - "On one partition-pruned aggregate, StarRocks returned in 34 ms against Trino's 99 ms. That is a narrow test, and the post says why."
  - "The FE reports ready before any backend registers; `SHOW BACKENDS` is the real readiness signal, not a successful `SELECT 1`."
  - "A second engine surfaced the schema-naming debris from part two — the catalog is shared, so mistakes are shared too."
---

## The claim a REST catalog is actually making

Parts one to three built a lakehouse on Trino and never left it. That is a fine way to test Iceberg, and a poor way to test the *catalog*, because the argument for Polaris over Hive Metastore is not that it looks tables up faster.

The argument is that the catalog is the system of record, so a second engine should see the tables the first one wrote — without an export, a copy, a `CREATE EXTERNAL TABLE` per table, or a second set of credentials.

That last clause is the part worth checking. [Part one]({{ '/writing/' | relative_url }}) went to some trouble to make Trino hold no standing S3 key. If adding StarRocks means pasting the MinIO keys into a second config file, the boundary is gone and the whole exercise was decoration.

So: attach StarRocks 4.1.4 to the same catalog, read the same tables, and see. The original 2024 build ran StarRocks 3.2 beside Trino 437 against Hive Metastore — same question, and the answer has changed.

## Step 1 — StarRocks on the same network

```yaml
  starrocks:
    image: starrocks/allin1-ubuntu:4.1.4
    profiles: ["engines"]
    depends_on:
      polaris:
        condition: service_healthy
    ports:
      - "9030:9030"   # MySQL protocol
      - "8030:8030"   # FE HTTP
    healthcheck:
      test: ["CMD-SHELL", "mysql -h127.0.0.1 -P9030 -uroot -e 'SELECT 1' || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 40
      start_period: 90s
```
{: data-file="docker-compose.yaml"}

`allin1` bundles the frontend and backend in one container. Production splits them; a lab that splits them spends 2 GB teaching nothing this post is about.

<div class="callout callout--gotcha" markdown="1">
**`SELECT 1` succeeding does not mean StarRocks is ready.** The FE accepts connections well before any BE registers, so the healthcheck above goes green and the first real query fails:

```text
ERROR 1064 (HY000): Backend node not found. Check if any backend node is down.
```

The honest readiness signal is `SHOW BACKENDS` reporting `Alive: true`. If you are scripting a wait loop, poll that rather than a trivial query — otherwise you will write a retry that papers over a startup ordering bug you have not actually fixed.
</div>

**Verify.** `SELECT current_version()` returns `4.1.4-…` rather than the backend error.
{: .verify}

## Step 2 — One catalog definition, no table definitions

```sql
CREATE EXTERNAL CATALOG lakehouse PROPERTIES (
  'type' = 'iceberg',
  'iceberg.catalog.type' = 'rest',
  'iceberg.catalog.uri' = 'http://polaris:8181/api/catalog',
  'iceberg.catalog.warehouse' = 'lakehouse',
  'iceberg.catalog.security' = 'oauth2',
  'iceberg.catalog.oauth2.credential' = 'root:s3cr3t-dev-only',
  'iceberg.catalog.oauth2.scope' = 'PRINCIPAL_ROLE:ALL',
  'iceberg.catalog.vended-credentials-enabled' = 'true',
  'aws.s3.endpoint' = 'http://minio:9000',
  'aws.s3.enable_path_style_access' = 'true'
);
```
{: data-file="starrocks"}

That is the entire integration. No table DDL, no schema mirroring, no sync job.

Read it back:

```sql
SHOW DATABASES FROM lakehouse;
```

```text
bronze
gold
information_schema
silver
silver_gold
silver_silver
```

Every namespace Trino created, immediately. Including `silver_gold` and `silver_silver` — the debris from the schema-naming bug in [part two]({{ '/writing/' | relative_url }}), which I had fixed in dbt but never cleaned out of the catalog.

That is a small thing that says something real: **the catalog is shared, so mistakes are shared too.** A second engine is also a second pair of eyes on your namespace hygiene.

```sql
SELECT count(*) FROM lakehouse.silver.orders_enriched;
```

```text
1645100
```

Trino reports the same number for the same table.

**Verify.** Row counts match between engines, and `SHOW DATABASES FROM lakehouse` lists the namespaces you created in Trino.
{: .verify}

## Step 3 — Does the second engine reintroduce standing keys?

The catalog above declares `vended-credentials-enabled` and — deliberately — **no `aws.s3.access_key` or `aws.s3.secret_key` at all**. If StarRocks did not support vending, this would fail at first read.

It does not fail. 1,645,100 rows, with StarRocks obtaining short-lived credentials from Polaris exactly as Trino does: authenticate as an OAuth2 principal, receive a session token scoped to the table's prefix, use it, discard it.

This is the result that justifies the architecture. The authorisation boundary built in part one is **engine independent**. Adding a query engine does not add a place where a long-lived S3 key has to live, which is the failure mode that quietly undoes most "we use a catalog" stories.

<div class="callout callout--gotcha" markdown="1">
**Check this on your own store rather than assuming it.** Vending depends on the object store exposing STS and on the engine implementing the delegation header. Part one showed both failing against MinIO in different ways. The five-minute test is the one above: define a catalog with no keys in it and see whether a read succeeds.
</div>

## Step 4 — Measure both, fairly

Same query, same table, same catalog:

```sql
SELECT count(*), sum(totalprice)
FROM lakehouse.silver.orders_enriched
WHERE orderdate >= '1995-03-01' AND orderdate < '1995-04-01';
```

Getting a comparable number took two attempts. Wall-clock through each engine's CLI is useless: the Trino CLI starts a JVM, the MySQL client does not. Subtracting a `SELECT 1` baseline from each was worse — it gave Trino a **negative** query time, because JVM startup varies by more than the query costs.

Both engines report their own timings, so use those. Trino from `system.runtime.queries`; StarRocks from its FE audit log:

```bash
grep 'orders_enriched' /data/deploy/starrocks/fe/log/fe.audit.log \
  | grep -o 'Time=[0-9]*' | tail -7
```

| engine | server-side median |
| --- | --- |
| Trino 483 | 99 ms |
| StarRocks 4.1.4 | **34 ms** |

<div class="callout callout--gotcha" markdown="1">
**This is a narrow test and the number should be read narrowly.** One aggregate, one partition, 100,000 rows, on a laptop. That is close to the shape StarRocks' vectorised MPP engine is built for, and it says nothing about the cases Trino is usually chosen for: federating across catalogs, joining a lakehouse table to a Postgres table, or long multi-table joins where the cost model matters more than the scan.

The useful conclusion is not "StarRocks is 2.9× faster". It is that **you can now measure that question on your own data without migrating anything**, because both engines read the same tables. Before a REST catalog, answering it meant a copy.
</div>

## Step 5 — Clean up the shared debris

Since the catalog is shared, so is the tidying:

```sql
DROP TABLE IF EXISTS lakehouse.silver_silver.orders_enriched;
DROP TABLE IF EXISTS lakehouse.silver_gold.daily_revenue;
DROP SCHEMA IF EXISTS lakehouse.silver_silver;
DROP SCHEMA IF EXISTS lakehouse.silver_gold;
```

```text
bronze
gold
information_schema
silver
system
```

Note this needs `DROP_WITH_PURGE_ENABLED` from part two, or the drops fail with a Trino error that never mentions purge.

## Failure modes

| Symptom | Cause | Repair |
| --- | --- | --- |
| `Backend node not found` | FE up, BE not yet registered | Poll `SHOW BACKENDS` for `Alive: true` |
| Catalog created, `SHOW DATABASES` empty | OAuth2 scope or grant chain missing | Check `PRINCIPAL_ROLE:ALL` and the part-one grant chain |
| Reads fail with no S3 keys set | Engine or store lacks vending support | Test with a keyless catalog before committing to the design |
| Unexpected namespaces appear | Shared catalog, shared history | They are real; clean them from either engine |
| Engine timings wildly inconsistent | Measuring client startup | Use `system.runtime.queries` and `fe.audit.log` |

## Clean up and operating consequence

```bash
docker compose --profile engines down
```

The rule: **a catalog earns its place when the second engine costs one DDL statement and no new credentials.**

That is a testable bar, and it is worth applying before committing to a catalog rather than after. Attach a second engine to a throwaway namespace, define it with no storage keys, and read a table the first engine wrote. If that works, the catalog is doing the job the architecture diagram claims. If it needs a copy, a manual table registration, or its own set of long-lived keys, you have a metadata service — which may still be worth running, but not for the reasons usually given.

The rest of this series is on GitHub as a single `docker compose` file: [MinIO, Polaris, Trino, dbt, Airflow and StarRocks]({{ '/work/' | relative_url }}), with every figure in these four posts reproducible from it.
