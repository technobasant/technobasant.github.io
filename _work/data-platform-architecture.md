---
title: "data-platform-architecture: an architecture engagement for a SaaS company leaving Postgres"
seo_title: "Data architecture case study: Postgres to Databricks or Snowflake, measured current state, 15 decisions"
hook: "A fictional client, its real problems measured on a copy of its database, and a staged architecture with every decision tied to evidence"
description: "A data architecture engagement for a fictional SaaS company: current state measured, five options, a staged target, data contracts and 15 decisions."
date: 2026-10-18
last_modified_at: 2026-10-19
kind: open-source
pillar: data-platforms
related: [data-stack-lab, ai-platform-architecture, dataset-registry]
order: 8
role: "Author, in the architect's role"
org: "Open source"
period: "2026"
team: "One person"
scale: "A client with 6,000 accounts and 350,000 events a day; a lab copy of its Postgres with 31.5 million events; 10 documents, 15 decision records, 3 data contracts, a cost model at three points of the client's growth"
problem: "A B2B SaaS company runs every report on its product's Postgres. The product slows down at month end, reports on the replica fail, revenue by plan disagrees with billing, history stops at 90 days, and two enterprise prospects want SOC 2 and provable erasure."
decision: "Measure the current state on a copy of the client's database before recommending anything; move analytics to a managed platform in stages; and choose between Databricks and Snowflake by a proof of concept on criteria and weights fixed in advance."
repo: "https://github.com/technobasant/data-platform-architecture"
flow: data-platform-architecture
cover:
  base: "/assets/images/editorial-replica-reports-v1"
  width: 1600
  height: 900
  alt: "Where the client's reports ran and what happened: on the primary the product's p95 latency went from 93 to 794 ms; on the read replica 3 of 412 long report runs finished; once the replica was 30 seconds behind even 0.1-second queries were cancelled; with hot_standby_feedback on, 20 of 20 finished"
  caption: "Measured on a lab copy of the client's database before anything was recommended."
  link: "/writing/read-replica-cancelled-the-reports/"
metrics: [dpa_bi_on_primary, dpa_replica_reports, dpa_erasure_time_travel, dsl_dbt_databricks, dpa_decisions_backed]
stack: ["Architecture decision records", "Open Data Contract Standard", "C4 model", Mermaid, "PostgreSQL 17", pgbench, Docker, Databricks, Snowflake, dbt, Python, "GitHub Actions"]
tags: [postgres, data-modeling, cost-finops]
image: /assets/og/og-lakehouse.png
image_alt: "Data platform architecture — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Architecture work is judged on deliverables: a current state someone measured, a target someone can reach, decisions with the options that lost, a data model, governance an auditor can check, and a migration that does not stop the business. Most public "reference architectures" are a diagram and a list of tools. I had published one of those, and it read as an index of my labs rather than as architecture for anyone in particular.

[data-platform-architecture](https://github.com/technobasant/data-platform-architecture) is now an engagement for one fictional client: a B2B SaaS company with 6,000 accounts, 350,000 product events a day growing threefold a year, and a data team of two. Everything the business knows about itself is read from the product's Postgres on RDS and its one read replica. The CTO and CFO want a target architecture, a choice between Databricks and Snowflake (both have pitched), a migration that does not touch the product, and a twelve-month roadmap.

## Constraints

The client is fictional and its data synthetic: the same business [data-stack-lab](/work/data-stack-lab/) generates. Its current state is measured on a lab copy of its database in Docker on a laptop, so comparisons between scenarios are the result and absolute latencies are not. The managed platforms are compared from documentation and list prices; the decision between them is written as a proof of concept still to run, with its criteria fixed now.

The brief sets the constraints every decision answers to: two data people growing to four, no one on call for a data platform, under $15,000 a month to run, the product's database not to be changed, a SOC 2 Type II window in month three, and erasure within 30 days everywhere a person's data is held.

## Architecture

- **Brief and current state.** Stakeholders, constraints, scale today and in the growth plan. A Postgres 17 primary and streaming replica at the client's scale (31.5 million events), the product's own requests at a fixed rate, and two analysts running the BI tool's queries, in four controlled scenarios.
- **Requirements.** Fifteen quality targets written as testable scenarios, each with today's value where it could be measured, and a ranking for when they conflict.
- **Options.** Scaling Postgres, AWS-native, Databricks, Snowflake and a self-run lakehouse, scored against the requirements, with the vendor bill and the bill plus the people to run each.
- **Target, in stages.** Stage 0 moves every report off the primary now; stage 1 is a managed platform fed by change data capture, with a Type 2 star schema and governance; stage 2 serves customers' usage from a stream-fed store; stage 3 is the assistant. C4 context and container views, zones, deployment, and how each part fails.
- **Data model and contracts.** A conceptual model, the marts with their grain, a bus matrix, keys and history; three contracts in the Open Data Contract Standard.
- **Security, migration, operations, roadmap.** Classification, roles and row filters, erasure, a SOC 2 and GDPR controls table; an inventory of every reader with a disposition, migration waves with a parallel run and rollback; runbooks; the first 90 days and the year; a risk register.
- **Fifteen decision records**, each with drivers, an options table, consequences, how reversible it is, when to revisit it, and evidence generated from measured results.

## In the code

A contract check only means something if it is seen to fail. CI lints every contract, then runs the producer-side check against a copy of the product contract with one column renamed, and requires it to report the change as breaking:

```yaml
- name: A renamed column is reported as breaking; an unchanged contract is not
  run: |
    original=models/contracts/product-database.odcs.yaml
    renamed=tests/fixtures/product-database-renamed-column.odcs.yaml
    if uvx --from "$DATACONTRACT" datacontract breaking "$original" "$renamed"; then
      echo "::error::removing users.email was not reported as breaking"
      exit 1
    fi
    uvx --from "$DATACONTRACT" datacontract breaking "$original" "$original"
```
{: data-file=".github/workflows/ci.yml" }

A unit test keeps the fixture honest: it may differ from the real contract by the rename and the version line, and nothing else.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Measure the current state before recommending | Take the client's description of it | The replica's failure was worse than, and different from, how it was described | A lab harness and a day of measurement |
| Reports on the replica now, with default settings | Turn on `hot_standby_feedback` | A cancelled report is a better failure than bloat in the product's busiest tables | Long reports keep failing until stage 1 |
| A managed platform, chosen by a proof of concept | Recommend one from experience | At this scale the bill does not separate them; ingestion, governance and erasure do, and those can be measured | Two weeks before the choice |
| Criteria and weights fixed before the proof of concept | Score after seeing results | A result cannot be argued backwards | Some criteria will turn out to matter less than weighted |
| The AWS-native option kept as the control | Compare only the two vendors that pitched | The cheapest credible option keeps the comparison honest | More to price |
| Usage page stays on the primary until stage 2 | Move it in stage 1 | No customer-facing path depends on the migration | The primary keeps one analytical load for months |

## Results

**Reports on the primary slowed the product.** The product's 95th-percentile request latency, without and with two analysts' reports running on the primary: {{ site.data.metrics.dpa_bi_on_primary.value }}. Requests over 100 ms went from 4.8% to 23.0%.

**Reports on the replica were cancelled.** On the read replica with default settings, {{ site.data.metrics.dpa_replica_reports.value }} runs of the three long reports finished in five minutes. Once the replica had fallen 30 seconds behind, it cancelled conflicting queries at once, including a 0.1-second report 65 times. With `hot_standby_feedback` on, all 20 finished, at the cost of holding back cleanup on the primary for as long as the longest report runs. The full account is in [the write-up](/writing/read-replica-cancelled-the-reports/).

**The rest of the case rests on measurements made elsewhere.** {{ site.data.metrics.dpa_decisions_backed.value }} decisions cite measured results, among them the {{ site.data.metrics.dsl_type1_misattributed.value }} of revenue a Type 1 dimension misplaces, the 1,638 events `COPY INTO` never loaded from a corrected file, and a Delta table restored after an overwrite left 1 day of 365. The four waiting on measurement say so in their status.

**The Databricks half of the proof of concept is in.** The client's dbt project built on Databricks with {{ site.data.metrics.dsl_dbt_databricks.value }} models, data tests and unit tests passing after one change (contract types `varchar` to `string`), and gave the published revenue figures exactly. One policy on a governed classification tag masked every personal column, including one on a table created after the policy. And an erased user's rows were still returned by time travel, {{ site.data.metrics.dpa_erasure_time_travel.value }}, after `DELETE`, after a purge and after `VACUUM`, until the table's retention had passed: the subject of [the erasure write-up](/writing/delta-delete-is-not-erasure/).

**The bill does not decide the platform.** At the client's scale every managed option costs a few hundred to about three thousand dollars a month at list price; a self-run lakehouse is cheap on the bill and the most expensive once the engineer it needs is counted. Per scan or per hour turns on {{ site.data.metrics.dpa_break_even.value }} scanned per engine-hour ([the cost write-up](/writing/warehouse-bill-per-scan-or-per-hour/)).

## What went wrong

**The first version had no client.** It was thirteen decisions about a generic platform, each citing a lab. Reviewed against what architecture roles and practitioners actually publish, it read as a list of things I had built. The rework starts from one client's brief and keeps only the evidence that client's decisions need; the first version stays in the repository's v0.1.0 tag.

**My first lab copy of the database was unrealistic.** I generated events in random time order, so the last week's rows were spread across all 5 GB and never in memory, and the product looked slow with nothing else running. A real table is appended in time order. Regenerated that way, the product's median request took 5 ms.

**I counted queueing twice.** pgbench's per-request time at a fixed rate already includes the wait to start; I had added the schedule lag on top. The first numbers were double the real ones.

**The first runs were noisy for reasons that had nothing to do with reports.** A replica restart, a checkpoint inside a scenario and Docker's virtual disk all moved the slowest requests. Every scenario now starts after a forced checkpoint, with the replica caught up and no checkpoint due; the remaining host effects are written down, and the replica scenarios' product latency, inflated by a shared disk that RDS does not have, is not used as evidence.

## What I'd do differently

**Run the Snowflake half of the proof of concept.** The Databricks half is done; the same dbt project, masking policy, erasure timeline and bill from the billing tables on Snowflake would let decision 0005 be accepted on measurements rather than on one platform's.

**Build the reconciliation suite against the lab database.** The migration plan's parallel run is designed; running it against the lab copy would show the explained-difference report finance has to trust.

**Measure the feedback setting's cost properly.** Five minutes with one-to-two-minute reports did not show the bloat `hot_standby_feedback` causes; an hour with hour-long reports would.

The brief, the measurements, the decisions and the checks are in [data-platform-architecture](https://github.com/technobasant/data-platform-architecture).
