---
title: "data-stack-lab: a dbt star schema scored against the truth"
seo_title: "dbt dimensional modelling: Type 2 dimension, snapshots and tests, measured"
hook: "One synthetic business, built tool by tool; the first module asks what a slowly changing dimension is worth in dollars"
description: "A Kimball star schema in dbt with a Type 2 dimension built from monthly snapshots, contracts and unit tests, run on dbt Core and v2 and scored against ground truth."
date: 2026-10-18
last_modified_at: 2026-10-18
kind: lab
pillar: data-platforms
related: [dataset-registry, data-platform-practice, streaming-platform]
order: 7
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "1,000 accounts, 11,963 users, 5,048 invoices and 913,388 events over a year; 13 snapshot loads; 11 models, 46 data tests, 3 unit tests, on DuckDB"
problem: "Most dbt portfolios show a model that runs. Whether it is right is a different question, and the usual checks on a fact table, keys and totals, cannot answer it: a join to the wrong version of a dimension is complete, correctly keyed and wrong."
decision: "Generate the data so its truth is known, build the model the way a warehouse would see the data (one monthly extract at a time), score every design choice against the truth, and break the model on purpose to see which tests notice."
repo: "https://github.com/technobasant/data-stack-lab"
flow: data-stack-lab
cover:
  base: "/assets/images/editorial-data-stack-lab-v1"
  width: 1600
  height: 900
  alt: "Revenue by plan for 5,048 invoices, billed versus attributed by each account's current plan, beside three results: Type 2 got every invoice right, Type 1 moved 15.1%, monthly snapshots saw 533 of 570 changes"
  caption: "Summed by the plan each invoice billed, and by the plan the account is on today. Totals match; the plans do not."
  link: "/writing/type-1-dimension-revenue-wrong-plan/"
metrics: [dsl_type1_misattributed, dsl_type2_correct, dsl_snapshot_coverage, dsl_mutants]
stack: ["dbt Core 1.12", "dbt v2", DuckDB, "dbt snapshots", "dbt unit tests", "model contracts", Python, NumPy, PyArrow, "GitHub Actions"]
tags: [data-modeling, data-quality]
image: /assets/og/og-lakehouse.png
image_alt: "Data modelling and dbt — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Data modelling is in about two of every five data-engineering job descriptions I have collected, and it is the skill a portfolio shows worst. A dbt project that runs proves the SQL compiles. It does not prove the model answers the question it is named for, and the usual tests (unique keys, not-null columns, accepted values) are checks on shape, not on meaning.

[data-stack-lab](https://github.com/technobasant/data-stack-lab) is a repository I am building one module at a time: a single fictional SaaS business, modelled and run on the tools data teams use, starting with dbt and moving on to orchestration, data quality and the warehouse and lakehouse platforms. Every module runs on the same seeded dataset, and the generator keeps what really happened, so each module can be scored instead of merely run. This first module is the dimensional model. It asks a narrow question with a dollar answer: what does keeping a dimension's history buy, and what does it miss?

## Constraints

Everything is synthetic, and the business is deliberately small: four plans at one price each, no seats, proration, discounts or refunds. The rates at which accounts upgrade, downgrade, trial a plan and churn are assumptions, so the percentages describe this business rather than any real one.

The warehouse is DuckDB, so the module runs anywhere with no server, and CI rebuilds it on every commit. That rules out claims about Snowflake, Databricks or BigQuery behaviour. The SQL is written to be portable (dbt's cross-database macros, no `QUALIFY`), and those platforms get their own modules running this same project. Timings came from one host, an Apple M5 with 24 GB, and are observations only; every other figure is a count over seeded data that CI reproduces byte for byte on Linux.

## Architecture

- **Generator.** One seeded Python module writes the sources as an application would deliver them: a full extract of the accounts table on the first of each month (current state only), users, a price list, a billing export carrying amounts but not plans, and 913,388 product events, 0.8% of them delivered twice. It also writes two truth files the warehouse never sees: every account change with its timestamp, and the plan each invoice billed.
- **Load and snapshot.** A script replaces `raw.accounts` with each month's extract in turn and runs `dbt snapshot` after each, 13 times, so the history in the warehouse is exactly what the extracts showed.
- **Model.** Staging views normalise types and e-mail addresses and drop redelivered events. The marts are a Kimball star: `dim_account` (Type 2), `dim_plan`, `dim_date` and `dim_user` (Type 1, with personal data left in staging), and two facts, `fct_invoices` and `fct_daily_usage`, each joined to the account version in effect when it happened. A `revenue_by_plan` model carries both attributions side by side.
- **Tests.** Enforced contracts on the dimension and both facts; 46 data tests including three generic ones written for this (validity windows that neither overlap nor leave gaps, and a composite grain) and two reconciliations; 3 unit tests on hand-written rows.
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

**Two engines, one result.** dbt v2 (the Apache-2.0 `dbt-oss` 2.0.8 distribution) built the same 11 models, passed the same tests and produced byte-identical measurements after one change to the YAML. End to end, 13 snapshot runs and a build took 83 s on dbt Core and 24 s on v2 on the same host.

## What went wrong

**dbt v2 passed two unit tests it should have failed.** The mutation script showed that on v2, deleting the first-version stretch or the far-future end left the dimension's unit test green. A wrong expected timestamp, even 1999, passes on v2, while a wrong string, integer or boolean fails. The SQL v2 compiles for the test returns both values, so the gap is in how it compares the rows it fetches. It is [dbt-labs/dbt#15894](https://github.com/dbt-labs/dbt/issues/15894), open since August, and I reproduced it on 2.0.8 with DuckDB. The data tests caught both breaks, which is the argument for having both layers; the repository now records the per-engine result, so CI fails when the behaviour changes.

**v2 rejected a source property dbt Core accepts.** `loaded_at_field` at the table level of a source is an error on v2, which wants it under `config:`. One line, but a project that runs on Core is not automatically a v2 project.

**My first mutation run reported every break as surviving.** The harness read the failing node's name from the wrong segment of dbt's unique id, which puts a unit test's name last. All four breaks had in fact been caught. A harness that reports on tests needs its own known failure to check against before its output means anything.

## What I'd do differently

**Score the cadence, not just the model.** The snapshot's blind spot is set by how often the source is extracted. The next step is to rebuild the dimension from daily extracts and from a change-data-capture log of the same history and put the three side by side, which is a sharper argument for CDC than any diagram.

**Add the platforms early.** The model is portable by construction but proven only on DuckDB. Running the same project on Snowflake and Databricks is the next module, and type mapping in the contracts is where I expect the first surprises.

**Lint the SQL.** Formatting is consistent by hand. A SQL linter in CI would keep it that way once the project has more than one author.

The code, the truth files' generator, and every measurement and mutant record are in [data-stack-lab](https://github.com/technobasant/data-stack-lab).
