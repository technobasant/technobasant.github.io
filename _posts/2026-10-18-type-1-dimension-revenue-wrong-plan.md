---
title: "A Type 1 dimension put 15% of a year's revenue on the wrong plan"
seo_title: "SCD Type 2 in dbt: what Type 1 gets wrong, measured on a year of revenue"
description: "Type 1 moved $152,227 of a year's revenue to the wrong plan. A Type 2 dimension from dbt snapshots got all 5,048 invoices right, and only a unit test saw the bug."
date: 2026-10-18 09:00:00 +0545
last_modified_at: 2026-10-19
type: essay
pillar: data-platforms
series: data-stack-lab
series_order: 1
tags:
  - data-modeling
  - data-quality
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - slowly changing dimensions
  - dimensional modelling
  - dbt snapshots
  - data testing
mentions:
  - dbt
  - DuckDB
  - data-stack-lab
cover:
  base: "/assets/images/editorial-data-stack-lab-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Revenue by plan for 5,048 invoices: billed versus attributed by each account's current plan, with $10,700 landing on the free plan, beside three results — Type 2 got every invoice right, Type 1 moved 15.1%, monthly snapshots saw 533 of 570 changes"
  caption: "The same invoices summed two ways. Totals match; the plans do not."
faq:
  - q: "What is the difference between a Type 1 and a Type 2 slowly changing dimension?"
    a: "A Type 1 dimension overwrites an attribute in place, so every fact, past and present, sees today's value. A Type 2 dimension adds a new row per change with a validity window, and each fact joins to the version that was in effect when it happened. On a year of generated SaaS invoices, Type 1 put 15.1% of revenue on a plan the invoice did not bill; Type 2 got all 5,048 invoices right."
  - q: "Do dbt snapshots capture every change to a table?"
    a: "No. A snapshot records the state of the source each time it runs, so a change that is made and replaced between two runs is never seen. With monthly extracts, 37 of 570 account changes in a year were missed, 26 of them short trial upgrades. For facts dated at the extract that cost nothing; for daily usage it put 0.08% of events on the wrong plan."
  - q: "How do you test a Type 2 join in dbt?"
    a: "With a unit test on hand-written rows that states which version a fact must join to. Data tests on real data are not enough: joining invoices to the current version instead of the version in effect produced valid keys, every invoice and revenue that reconciled to the cent, and passed every data test. Only the unit test failed."
  - q: "Does dbt v2 run dbt unit tests the same way as dbt Core?"
    a: "Not yet for timestamps. dbt v2 2.0.8 does not compare timestamp columns in a unit test's expected rows, so a test expecting 2025-03-01 passed when the model produced 2025-06-10. It is reported as dbt-labs/dbt#15894. Strings, integers and booleans are compared."
key_takeaways:
  - "Joining facts to today's attributes rewrote a year of revenue: $152,227 (15.1%) landed on a plan the invoice did not bill."
  - "Totals still reconcile under Type 1, so no check on totals, keys or row counts can see the error; a unit test that names the expected version can."
  - "A snapshot sees only what each extract shows: monthly extracts missed 37 of 570 changes, mostly trials that started and ended in one month."
  - "Stretch the first version back to creation, close open versions at 9999-12-31, and test that windows neither overlap nor leave gaps."
  - "Run unit tests on the engine you deploy with: dbt v2 2.0.8 never compares expected timestamps (dbt-labs/dbt#15894)."
---

A finance analyst asks a simple question: how much revenue did each plan earn last year? The warehouse has invoices and an accounts table, and each account has a plan. Join one to the other, group by plan, and the report is done in ten minutes. It also puts about one dollar in seven on the wrong plan. The accounts table says which plan each customer is on *today*, and a year is long enough for customers to upgrade, downgrade and leave.

I built the model both ways on a year of generated data and scored each against what really happened. Attributing invoices by the current plan, which is what a Type 1 dimension does, put **$152,227 of $1,010,202 (15.1%)** on a plan the invoice did not bill. It credited the free plan with $10,700. A Type 2 dimension, built from dbt snapshots, put all 5,048 invoices on the right plan.

**Operating rule.** If a fact must be read against an attribute that changes, keep the attribute's history and join each fact to the version in effect when it happened. Test that join with rows written by hand, because data tests on real data cannot see it go wrong.

The code is [data-stack-lab](https://github.com/technobasant/data-stack-lab), the first project of a repository that builds one SaaS business scenario on the tools data teams use, and scores each project against the data's ground truth. Nothing in it is real. Every figure below is in its [MEASUREMENTS.md](https://github.com/technobasant/data-stack-lab/blob/main/MEASUREMENTS.md), and CI regenerates the data, rebuilds the warehouse and fails if a single number moves.

## The same invoices, two answers

The business has four plans: free, team at $49 a month, business at $199 and enterprise at $999. A thousand accounts sign up, then about 0.8 times a year upgrade, downgrade or churn; one upgrade in five is a trial that drops back within a few weeks unless something else changes first. Paid accounts are billed on the first of each month. The billing export carries the account and the amount, not the plan, which is common: billing knows money, and the warehouse is expected to know the rest.

The generator also writes what a warehouse never gets: the plan each invoice really billed. That makes the two attributions measurable.

| Plan | Billed (truth) | Type 2 | Type 1 (today's plan) | Type 1 error |
|---|---:|---:|---:|---:|
| free | $0 | $0 | $10,700 | n/a |
| team | $140,581 | $140,581 | $157,008 | +11.7% |
| business | $325,166 | $325,166 | $340,030 | +4.6% |
| enterprise | $544,455 | $544,455 | $502,464 | −7.7% |
{: aria-label="Revenue by plan for 5,048 invoices: the plan billed, Type 2 attribution and Type 1 attribution" }

Type 1 got 873 of the 5,048 invoices wrong. The errors are not noise around the truth; they follow the direction customers moved. The largest single flow is $60,939 billed on enterprise and reported under business, by accounts that have since downgraded. Accounts that later fell back to free take $10,700 of paid history with them, which produces a report in which the free plan earns money.

A plan-level report is where this matters. Pricing reviews, sales compensation and churn analysis all ask what a plan earned, and Type 1 answers a different question: what did the customers who are on this plan now pay, on whatever plan they were on at the time.

## Totals reconcile, so nothing checks it

Under Type 1 the total is still $1,010,202. Every invoice is still there, once. Every key resolves. That is why this mistake survives review: the usual checks on a fact table are about completeness and keys, and a join to the wrong version is complete and correctly keyed.

I tested that directly. The repository's mutation script breaks the models in four ways and builds each break twice, once with the unit tests and once with only the data tests running on the real data. One break replaces the as-of join in the invoice fact with a join to the current version. Against the 46 data tests it passed all of them: `not_null` and relationship tests on the key, and a reconciliation that the fact holds exactly the billing export's invoices and money. It failed only one test, a unit test that gives the model three versions of one account and two invoices and states which version each invoice must get:

```yaml
unit_tests:
  - name: an_invoice_takes_the_version_in_effect_when_billed
    model: fct_invoices
    given:
      - input: ref('stg_billing__invoices')
        format: csv
        rows: |
          invoice_id,account_id,invoiced_at,amount_usd
          INV-1,7,2026-02-01 00:00:00,49
          INV-2,7,2026-03-01 00:00:00,199
      - input: ref('dim_account')
        format: csv
        rows: |
          account_key,account_id,valid_from,valid_to
          v1,7,2025-03-01 09:00:00,2026-02-14 08:00:00
          v2,7,2026-02-14 08:00:00,2026-05-02 10:00:00
          v3,7,2026-05-02 10:00:00,9999-12-31 00:00:00
    expect:
      format: csv
      rows: |
        invoice_id,account_key,invoice_date_key
        INV-1,v1,20260201
        INV-2,v2,20260301
```

The other three breaks were caught by both layers: on the real data, data tests found NULL keys, a NULL validity end and duplicated event ids, and the unit tests found the logic wrong. Only the plausible-but-wrong join needed the unit test alone. That is the kind of mistake a unit test is for: logic that produces valid-looking output.

## A snapshot only knows what an extract showed

The accounts table in the application holds the current state and nothing else. The warehouse receives it as a full extract on the first of each month. History exists only because a dbt snapshot runs after each load and records what changed:

```yaml
snapshots:
  - name: snap_accounts
    relation: source('app', 'accounts')
    config:
      unique_key: account_id
      strategy: timestamp
      updated_at: updated_at
```

The timestamp strategy starts a new version whenever the application's `updated_at` moves and dates it from that value, so a version's validity is when the change happened, not when the snapshot ran. It cannot see what no extract showed. Of the 570 changes made during the year, 533 survived to a month-end extract. The other 37 were replaced before the next one, and 26 of those were trial upgrades that started and ended inside a month.

Whether that matters depends on when the facts happen. Invoices are billed at 00:00 on the first, the instant the extract is taken, so the snapshot's state at billing time is always right, and 0 of 5,048 invoices were affected. Product usage happens all month. Against the true plan at each event's timestamp, the Type 2 dimension put 734 of 906,015 events (0.08%) on the wrong plan, all inside states no extract saw. Type 1 put 13.65% there.

There is a quieter cost too. The timestamp strategy recorded 33 versions identical to the one before: an account tried a higher plan and dropped back between two extracts, which left the plan unchanged and `updated_at` moved. The check strategy compares column values instead and would skip those, but by default it dates each version to the snapshot run, which is the worse trade for an as-of join. If missed states matter, the answer is not a cleverer snapshot but a better source: extract more often, or read the change log (change data capture).

## Three details that make an as-of join safe

A Type 2 join is a range predicate, `fact_time >= valid_from and fact_time < valid_to`, and three small decisions decide whether every fact finds exactly one version:

```sql
{% raw %}select
    i.invoice_id,
    a.account_key,
    i.account_id,
    {{ date_key('i.invoiced_at') }} as invoice_date_key,
    i.invoiced_at,
    i.amount_usd
from {{ ref('stg_billing__invoices') }} as i
left join {{ ref('dim_account') }} as a
    on
        i.account_id = a.account_id
        and i.invoiced_at >= a.valid_from
        and i.invoiced_at < a.valid_to{% endraw %}
```

**The first version reaches back to creation.** An account that changed plan before its first extract is first seen with `updated_at` after its signup, so events in that gap find no version. The dimension stretches each account's first version back to signup. What the account looked like in the gap is unknown; its first known state is the best available answer, and `version_number = 1` labels it. Without the stretch, the usage fact had NULL account keys on real data.

**Open versions end at 9999-12-31, not NULL.** A NULL end makes every as-of join special-case the current row, on every warehouse. A far-future date keeps it a plain range.

**Facts use a LEFT JOIN, with a `not_null` test on the key.** An inner join would drop an unmatched fact silently; a left join turns it into a failing test. Two generic tests guard the dimension itself: no two versions of an account overlap, and each version ends exactly where the next begins.

## The unit test that passed on dbt v2

The project runs on dbt Core 1.12 and on dbt v2, the Rust engine (the Apache-2.0 `dbt-oss` distribution, 2.0.8). Both build the same 11 models and pass the same tests, and the measurements are identical byte for byte. CI runs both.

The mutation script found the one difference. On v2, the unit test that pins the first version to signup kept passing when the stretch was deleted: the model returned 2025-06-10 where the test expected 2025-03-01. Changing an expected timestamp in another unit test to 1999 also passed, while a wrong string, integer or boolean failed as it should. The SQL v2 compiles for the test returns both values, so the gap is in how v2 compares the fetched rows. It is [dbt-labs/dbt#15894](https://github.com/dbt-labs/dbt/issues/15894), reported in August and open; I reproduced it on 2.0.8 with DuckDB. The data tests caught both breaks anyway, which is the case for keeping both layers. The repository records which tests catch which break on each engine, so CI will notice when the fix lands.

<div class="callout callout--note" markdown="1">
**Boundary.** Generated data from one fixed-seed generator, one year, one price per plan, no seats, discounts or refunds. The 15.1% is what this business's rates of change produce, not a constant: more plan changes, more error. Invoices fall on the extract instant by design, which is why snapshot gaps cost invoices nothing here; a billing cycle out of step with the extracts would inherit the same gaps as usage. Everything ran on DuckDB. The project is written with dbt's cross-database macros so other engines can run it. *Update, 19 October 2026:* it has since built on Databricks with one change (contract types `varchar` became `string`) and gave these figures exactly; Snowflake and BigQuery are not claimed.
</div>

## What goes in a Type 2 dimension

- Snapshot the source as it arrives, not a cleaned model: the snapshot is the only record of history.
- Date versions by the application's change time when the source has one, and know which changes an extract cadence cannot see.
- Stretch the first version back to creation, end open versions at a far-future date, and label the stretched rows.
- Join facts with a left join on the validity range, and fail the build on an unmatched key.
- Test that versions neither overlap nor leave gaps, reconcile facts to their source, and write a unit test that names the version each fact must get.
- Break the model on purpose and confirm a test fails, on the dbt engine you deploy with.

## Frequently asked questions

### What is the difference between a Type 1 and a Type 2 slowly changing dimension?

A Type 1 dimension overwrites an attribute in place, so every fact, past and present, sees today's value. A Type 2 dimension adds a new row per change with a validity window, and each fact joins to the version that was in effect when it happened. On a year of generated SaaS invoices, Type 1 put 15.1% of revenue on a plan the invoice did not bill; Type 2 got all 5,048 invoices right.

### Do dbt snapshots capture every change to a table?

No. A snapshot records the state of the source each time it runs, so a change that is made and replaced between two runs is never seen. With monthly extracts, 37 of 570 account changes in a year were missed, 26 of them short trial upgrades. For facts dated at the extract that cost nothing; for daily usage it put 0.08% of events on the wrong plan.

### How do you test a Type 2 join in dbt?

With a unit test on hand-written rows that states which version a fact must join to. Data tests on real data are not enough: joining invoices to the current version instead of the version in effect produced valid keys, every invoice and revenue that reconciled to the cent, and passed every data test. Only the unit test failed.

### Does dbt v2 run dbt unit tests the same way as dbt Core?

Not yet for timestamps. dbt v2 2.0.8 does not compare timestamp columns in a unit test's expected rows, so a test expecting 2025-03-01 passed when the model produced 2025-06-10. It is reported as dbt-labs/dbt#15894. Strings, integers and booleans are compared.

The code, the measurements and the mutation results are in [data-stack-lab](https://github.com/technobasant/data-stack-lab), with the design in [the case study](/work/data-stack-lab/). Contracts between teams, rather than inside one model, are the subject of [the data contracts post](/writing/json-schema-compatibility-data-contracts/). More on [data modelling and dbt](/writing/tags/data-modeling/) and [data quality](/writing/tags/data-quality/).
