---
title: "data-stack-lab: dbt, Airflow, data-quality, Spark and Databricks projects, checked against known answers"
seo_title: "Hands-on dbt, Airflow, data quality, PySpark and Databricks projects, each measured"
hook: "One project per tool on one synthetic SaaS dataset, each with a result the data can prove"
description: "Hands-on data engineering projects on one synthetic SaaS dataset: dbt, Airflow 3, data quality, PySpark and Databricks, each with measured results."
date: 2026-10-18
last_modified_at: 2026-10-19
kind: lab
pillar: data-platforms
related: [dataset-registry, data-platform-practice, streaming-platform]
order: 7
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "1,000 accounts, 5,048 invoices and 913,388 events over a year; a dbt project with 11 models, 46 data tests and 3 unit tests; an Airflow 3 DAG backfilled four ways; a month of deliveries with nine injected defects; a PySpark 4.2 rollup over 365 daily partitions; ten days of files loaded six ways on Databricks; DuckDB"
problem: "Most dbt and Airflow portfolios show code that runs. Whether it is right is a different question, and the usual checks (keys, totals, green task runs) cannot answer it: a join to the wrong version of a dimension, or a load that skips a day, is complete, correctly keyed and green."
decision: "Generate the data so the correct answer is known, build each project the way production would see the data, check every result against that answer, and break things on purpose to see which tests and runs notice."
repo: "https://github.com/technobasant/data-stack-lab"
flow: data-stack-lab
cover:
  base: "/assets/images/editorial-data-stack-lab-v1"
  width: 1600
  height: 900
  alt: "Revenue by plan for 5,048 invoices, billed versus attributed by each account's current plan, beside three results: Type 2 got every invoice right, Type 1 moved 15.1%, monthly snapshots saw 533 of 570 changes"
  caption: "Summed by the plan each invoice billed, and by the plan the account is on today. Totals match; the plans do not."
  link: "/writing/type-1-dimension-revenue-wrong-plan/"
metrics: [dsl_type1_misattributed, dsl_backwards_loss, dsl_quality_block, dsl_spark_static_overwrite, dsl_databricks_corrected_missed]
stack: ["dbt Core 1.12", "dbt v2", "Apache Airflow 3.3", "PySpark 4.2", Databricks, "Delta Lake", "Unity Catalog", "Auto Loader", DuckDB, Parquet, "dbt snapshots", "dbt unit tests", "model contracts", Python, NumPy, PyArrow, "GitHub Actions"]
tags: [data-modeling, orchestration, data-quality, spark, databricks]
image: /assets/og/og-lakehouse.png
image_alt: "Data modelling and dbt — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Data modelling and Airflow are each in about two of every five data-engineering job descriptions I have collected, and they are the skills a portfolio shows worst. A dbt project that runs proves the SQL compiles; a DAG that runs green proves the tasks finished. Neither proves the numbers are right, and the usual checks (unique keys, not-null columns, successful runs) are checks on shape, not on meaning.

[data-stack-lab](https://github.com/technobasant/data-stack-lab) is a set of hands-on data engineering projects, one per tool, all on the same synthetic SaaS data. Each runs with one command and has its results checked in CI. Because the data is generated, the correct answer is known, so each project can prove its result instead of just running. This case covers the first five. The dbt project asks what keeping a dimension's history is worth in dollars. The Airflow project asks which way of loading "only what is new" survives re-runs, backfills and an upgrade to Airflow 3. The data-quality project asks which checks catch which defects, and what blocking or quarantining lets through. The Spark project asks what a partitioned PySpark job's defaults do on a re-run and to the files it writes. The Databricks project asks which way of loading files survives the incidents real deliveries have, and how Delta re-runs a day.

## Constraints

Everything is synthetic, and the business is deliberately small: four plans at one price each, no seats, proration, discounts or refunds. The rates at which accounts upgrade, downgrade, trial a plan and churn are assumptions, so the percentages describe this business rather than any real one.

The warehouse is DuckDB, so the dbt, Airflow, data quality and Spark projects run anywhere with no server, and CI rebuilds it on every commit. Spark runs in local mode on four cores, so there is no network shuffle and no object store, where small files cost more. The Databricks project ran once on Free Edition and cannot run in CI; CI checks its prediction from the documented semantics, and that the recorded run matched it. The same dbt project, written to be portable (dbt's cross-database macros, no `QUALIFY`), also built on Databricks with one change; nothing here is claimed about Snowflake or BigQuery. Timings came from one host, an Apple M5 with 24 GB, and are observations only; every other figure is a count over seeded data that CI reproduces byte for byte on Linux.

## Architecture

- **Generator.** One seeded Python module writes the sources as an application would deliver them: a full extract of the accounts table on the first of each month (current state only), users, a price list, a billing export carrying amounts but not plans, and 913,388 product events, 0.8% of them delivered twice. It also writes two truth files the warehouse never sees: every account change with its timestamp, and the plan each invoice billed.
- **Load and snapshot.** A script replaces `raw.accounts` with each month's extract in turn and runs `dbt snapshot` after each, 13 times, so the history in the warehouse is exactly what the extracts showed.
- **Model.** Staging views normalise types and e-mail addresses and drop redelivered events. The marts are a Kimball star: `dim_account` (Type 2), `dim_plan`, `dim_date` and `dim_user` (Type 1, with personal data left in staging), and two facts, `fct_invoices` and `fct_daily_usage`, each joined to the account version in effect when it happened. A `revenue_by_plan` model carries both attributions side by side.
- **Tests.** Enforced contracts on the dimension and both facts; 46 data tests including three generic ones written for this (validity windows that neither overlap nor leave gaps, and a composite grain) and two reconciliations; 3 unit tests on hand-written rows.
- **Airflow.** One DAG, two tasks: `land` replaces a day's partition of event files in the warehouse, and `transform` runs three dbt incremental models that differ only in the filter that picks the batch (newer than the newest event time, newer than the newest arrival, or inside the run's data interval). A harness backfills September four ways through `dag.test()`; the in-order backfill was also run once on `airflow standalone` with `airflow backfill create`.
- **Data quality.** September is delivered daily with one injected defect every three days and checked in dbt: an enforced contract, row tests, batch tests against the last seven accepted days, and control totals against the producer's manifest. Every delivered row is labelled good or bad, and two policies (block the day, or quarantine failing rows) are scored on what they let through and what they hold back.
- **Spark.** A PySpark 4.2 rollup written as Parquet partitioned by day, used for three experiments: re-running one day under each partition overwrite mode, writing the rollup four ways and counting files, and counting the files that hold one day's rows.
- **Databricks.** Ten days of event files delivered into a Unity Catalog volume with four incidents (a duplicate file under another name, a truncated upload corrected under the same name, a late file, a repeated run) and loaded six ways from a serverless SQL warehouse and a Lakeflow pipeline; then one day of the Spark rollup re-run on a Delta table five ways.
- **Scoring.** A measurement script compares the warehouse with the truth files. A mutation script breaks the models four ways and records which tests fail, per dbt engine. CI runs everything on dbt Core 1.12 and on dbt v2, and fails if a single published number or mutant result changes.

## In the code

Two lines in the dimension decide whether every fact finds exactly one version. The first version is stretched back to signup, because an account that changed before its first extract is first seen later than it existed. The open version ends at a far-future date instead of NULL, so the as-of join in each fact stays a plain range predicate on any warehouse.

```sql
{% raw %}select
    v.dbt_scd_id as account_key,
    v.account_id,
    cast(v.version_number as integer) as version_number,
    v.account_name,
    v.industry,
    v.country,
    v.plan_id,
    p.plan_name,
    v.status,
    v.signup_at,
    case when v.version_number = 1 then v.signup_at else v.dbt_valid_from end as valid_from,
    coalesce(v.dbt_valid_to, cast('9999-12-31 00:00:00' as timestamp)) as valid_to,
    v.dbt_valid_to is null as is_current
from versions as v
inner join {{ ref('dim_plan') }} as p on v.plan_id = p.plan_id{% endraw %}
```
{: data-file="dbt/models/marts/dim_account.sql" }

Both lines are pinned by a unit test, and the mutation script deletes each in turn to check that something fails.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Snapshot the raw source | Snapshot a cleaned staging model | The snapshot is the only record of history; it should keep exactly what arrived | Cleaning runs after the snapshot, on every build |
| Timestamp strategy on the application's `updated_at` | Check strategy on chosen columns | Versions are dated when the change happened, not when the snapshot ran | 33 versions identical to the one before, from changes undone between two extracts |
| Stretch the first version back to signup | Leave a gap before the first extract | Without it, usage in the gap found no version at all | The gap's state is assumed; `version_number = 1` labels it |
| Facts left-join the dimension, with `not_null` on the key | Inner join | An unmatched fact fails the build instead of disappearing | One more test per fact |
| No dbt packages | dbt_utils for the generic tests | Runs offline and on dbt v2 unchanged | Three generic tests written by hand, under 50 lines |
| Score against a truth file | Trust the tests | Tests check shape; only the truth says whether the number is right | The truth exists only because the data is synthetic |

## Results

**Type 1 rewrote a year of revenue.** Attributing each invoice to its account's current plan put {{ site.data.metrics.dsl_type1_misattributed.value }} of revenue on a plan the invoice did not bill: $152,227 of $1,010,202, across 873 invoices. Enterprise came out 7.7% low and team 11.7% high, and the free plan was credited with $10,700; the largest single flow was $60,939 of enterprise billing reported under business by accounts that later downgraded. The Type 2 dimension put {{ site.data.metrics.dsl_type2_correct.value }} invoices on the right plan.

**Snapshots see what extracts show.** Monthly snapshots captured {{ site.data.metrics.dsl_snapshot_coverage.value }} changes made during the year; 26 of the 37 missed were trial upgrades that began and ended inside a month. Invoices, billed at the extract instant, lost nothing. Usage, which happens all month, put 734 of 906,015 events (0.08%) on the wrong plan with Type 2, against 13.65% with Type 1.

**Tests that fail when they should.** {{ site.data.metrics.dsl_mutants.value }} deliberate breaks failed the build. The one that matters most, joining invoices to the current version, passed all 46 data tests (keys valid, every invoice present, revenue reconciled to the cent) and was caught only by a unit test that names the version each invoice must get. The full table and the per-engine record are in the [write-up](/writing/type-1-dimension-revenue-wrong-plan/) and the repository's [MEASUREMENTS.md](https://github.com/technobasant/data-stack-lab/blob/main/MEASUREMENTS.md).

**High-water marks skip what runs out of order.** Backfilled in order, the event-time model lost 2,034 of 2,291 late events and the other two lost nothing. When the file for 10 September landed two days late and the day was re-run, the arrival-time model loaded nothing for it. Backfilled newest day first, both watermark models lost {{ site.data.metrics.dsl_backwards_loss.value }} of the month with every run green. The data-interval model lost nothing in any of those orders. Details in [the Airflow write-up](/writing/airflow-3-daily-no-data-interval/).

**Airflow 3's @daily has no interval.** On the default schedule, a `CronTriggerTimetable` in Airflow 3, each run's data interval starts and ends at the same instant. The data-interval model loaded {{ site.data.metrics.dsl_default_daily_loaded.value }} events in 30 successful runs. `saas_daily` names `CronDataIntervalTimetable` explicitly, and a test pins both schedules. The real-scheduler backfill produced tables identical to the harness's.

**Wrong data and missing data need different checks.** Blocking on any failure let {{ site.data.metrics.dsl_quality_block.value }} bad rows through and held 19,545 good ones; quarantining failing rows let 87 through and held 12,865. Three of the nine defects (a truncated upload, a silent platform, a late third) left no bad rows at all and were caught only by control totals, volume and per-platform share; the volume band caught the late third in one run and missed it by 12 rows in the other. Details in [the data-quality write-up](/writing/wrong-data-missing-data-different-checks/).

**Spark's defaults delete and fragment.** Re-running one day with `mode("overwrite")` under the default static partition overwrite mode left {{ site.data.metrics.dsl_spark_static_overwrite.value }} daily partitions; dynamic kept all 365. A partitioned write made 5,970 files for a month with adaptive execution off and 1,460 for a year with it on; repartitioning by the partition column made one file a day. Details in [the Spark write-up](/writing/spark-rerun-one-day-deleted-the-rest/).

**A correction under the same name is never read.** `COPY INTO` and Auto Loader track files by path, so when a truncated upload was re-sent complete under the same name, both skipped it and {{ site.data.metrics.dsl_databricks_corrected_missed.value }} of 29,095 events never arrived. Only Auto Loader with `allowOverwrites` followed by a `MERGE` on the event key was exact. On Delta, `INSERT OVERWRITE` of one day left 1 of 365 days even with a `PARTITION` clause, and `RESTORE` brought them back. The dbt project itself built on Databricks with {{ site.data.metrics.dsl_dbt_databricks.value }} models, data tests and unit tests passing after one change to its contract types, and gave the published revenue figures exactly. Details in [the Databricks write-up](/writing/copy-into-never-read-the-corrected-file/).

**Two engines, one result.** dbt v2 (the Apache-2.0 `dbt-oss` 2.0.8 distribution) built the same 11 models, passed the same tests and produced byte-identical measurements after one change to the YAML. End to end, 13 snapshot runs and a build took 83 s on dbt Core and 24 s on v2 on the same host.

## What went wrong

**dbt v2 passed two unit tests it should have failed.** The mutation script showed that on v2, deleting the first-version stretch or the far-future end left the dimension's unit test green. A wrong expected timestamp, even 1999, passes on v2, while a wrong string, integer or boolean fails. The SQL v2 compiles for the test returns both values, so the gap is in how it compares the rows it fetches. It is [dbt-labs/dbt#15894](https://github.com/dbt-labs/dbt/issues/15894), open since August, and I reproduced it on 2.0.8 with DuckDB. The data tests caught both breaks, which is the argument for having both layers; the repository now records the per-engine result, so CI fails when the behaviour changes.

**v2 rejected a source property dbt Core accepts.** `loaded_at_field` at the table level of a source is an error on v2, which wants it under `config:`. One line, but a project that runs on Core is not automatically a v2 project.

**Two streaming tables blocked each other.** Free Edition allows one active pipeline per type, and each `CREATE STREAMING TABLE` is a pipeline of its own, so refreshing the two Auto Loader tables in turn was refused for minutes at a time. Both now live in one Lakeflow pipeline, updated once per run, which is also how they would run in production.

**The first Spark file experiment would have taken most of an hour.** With adaptive execution off, a year of rollup is written as about 73,000 files. The AQE-off variant now runs on one month, and a separate variant runs the year with AQE on, which turned out to be the more useful result: four files a day without any tuning.

**The first data-quality run failed every day.** A `unique` test on raw deliveries fired on every clean day, because delivery is at least once and 0.8% of events arrive twice. The batch model now deduplicates first and the uniqueness test checks what is left; a spike in redeliveries is a warning, not a failure.

**My first backfill covered the wrong days.** The date passed to `dag.test()` is treated as the moment the run fires, so on a data-interval schedule it covers the day before; the scheduler's own backfill labels the same run by the start of its window. Passing each day as the date covered 31 August to 29 September and reported 30 September's 3,076 events as lost by the two strategies that were complete. Checking the harness against a scheduler run is what made the difference visible.

**My first mutation run reported every break as surviving.** The harness read the failing node's name from the wrong segment of dbt's unique id, which puts a unit test's name last. All four breaks had in fact been caught. A harness that reports on tests needs its own known failure to check against before its output means anything.

## What I'd do differently

**Score the cadence, not just the model.** The snapshot's blind spot is set by how often the source is extracted. The next step is to rebuild the dimension from daily extracts and from a change-data-capture log of the same history and put the three side by side, which is a sharper argument for CDC than any diagram.

**Add Snowflake.** The dbt project now builds on Databricks with one change and gives the published figures exactly: the model contracts declared `varchar`, which Databricks refuses without a length; `string` works on every engine. Snowflake is next.

**Run the other orders on the scheduler too.** Only the in-order backfill ran on a real scheduler. The backwards and late-file cases ran through `dag.test()`; `airflow backfill create --run-backwards` and a cleared-and-re-run day on the scheduler would close that gap.

**Lint the SQL.** Formatting is consistent by hand. A SQL linter in CI would keep it that way once the project has more than one author.

The code, the data generator, and every measurement, backfill and mutant record are in [data-stack-lab](https://github.com/technobasant/data-stack-lab).
