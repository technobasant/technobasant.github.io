---
title: "data-platform-architecture: a reference design where every decision cites a measurement"
seo_title: "Data platform reference architecture: 13 decisions, measured evidence, cost model"
hook: "Thirteen platform decisions, each tied to a result measured in a public lab, and a cost model that says what it does not know"
description: "A reference architecture for a SaaS data platform: 13 decision records backed by measured lab results, quality targets, runbooks and a platform cost model."
date: 2026-10-18
last_modified_at: 2026-10-18
kind: open-source
pillar: data-platforms
related: [data-stack-lab, streaming-platform, dataset-registry]
order: 8
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "13 decision records, 32 measured figures from nine public repositories, quality targets, governance, operations runbooks, and a cost model across six engine options and three workload tiers"
problem: "Architecture documents are usually diagrams and opinions. The decisions in them are rarely tied to evidence, and the evidence, when it exists, lives in a different place from the decision and drifts away from it."
decision: "Write the platform as decision records whose evidence is generated from one file of measured results, so a figure cannot change in one place and not the other; state which decisions are measured and which are modelled; and price the platform choice from list prices with every source quoted."
repo: "https://github.com/technobasant/data-platform-architecture"
flow: data-platform-architecture
cover:
  base: "/assets/images/editorial-data-platform-architecture-v1"
  width: 1600
  height: 900
  alt: "Table of four engines billed by the hour, with the terabytes one hour of compute must scan before BigQuery on-demand or Athena costs more, from 0.37 TB for self-run Trino to 3.36 TB for Databricks SQL Serverless"
  caption: "The break-even depends only on list prices; where a workload sits relative to it is the part to measure."
  link: "/writing/warehouse-bill-per-scan-or-per-hour/"
metrics: [dpa_decisions_backed, dpa_break_even, stream_failure_exactness, dsl_backwards_loss, lakehouse_rollback]
stack: ["Architecture decision records", Mermaid, Python, "Apache Iceberg", Kafka, dbt, Airflow, ClickHouse, Citus, "GitHub Actions"]
tags: [cost-finops, iceberg-lakehouse, data-quality]
image: /assets/og/og-lakehouse.png
image_alt: "Data platform architecture — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

The public labs on this site each answer a narrow question: does exactly-once survive a broker kill, does a rollback restore a table, which incremental load survives a backfill. An architect's job is the layer above them: which of those answers a platform should be built on, and how they fit together for one business.

[data-platform-architecture](https://github.com/technobasant/data-platform-architecture) is that layer, written for the same fictional SaaS business the [data-stack-lab](/work/data-stack-lab/) projects generate data for. It has four consumers with different needs: finance and analysts, customers looking at their own usage inside the product, the product's own features, and models.

## Constraints

Everything in it is assembled from public labs on synthetic data. It is not a description of any employer's or client's platform, and the workload tiers it prices are assumptions about a plausible business, not measurements of one.

The labs run multi-node clusters on one host, so their results show behaviour (what fails, what is lost, what recovers), not capacity. The managed platforms (Snowflake, Databricks, BigQuery) have not been run against this workload; they are compared from list prices and documentation only, and the decision that depends on them is marked Proposed.

## Architecture

- **Thirteen decision records**: three ways in (events through Kafka, database changes through CDC, vendor files), Iceberg tables behind a catalog that vends scoped credentials, exactly-once with per-layer reconciliation, contracts that wait for consumers, Type 2 history, loads by data interval, freshness measured from the reader's side, serving by access pattern, rehearsed recovery, three layers of tests, point-in-time features, canary releases, and the managed-platform choice.
- **Views**: data paths, zones and who may read each, deployment, and a failure-modes table where every row cites a measured recovery.
- **Quality targets**: freshness, completeness, correctness, recoverability, change safety and release safety, each with how it is measured and what has been measured so far, and a list of what has not.
- **Governance and operations**: ownership, classification, personal data and erasure, access, lineage; runbooks for backfills, late input, schema changes, failover, restore and tenant skew.
- **A platform selection guide and cost model** for Snowflake, Databricks SQL Serverless, BigQuery on-demand, Athena and Trino on EC2, priced from list prices quoted with their sources.

## In the code

The evidence in each decision record is not written by hand. A build script reads the measured figures from one YAML file and writes them into every record that cites them, and into the decision table in the README. CI runs it in check mode, so a figure that changes in the file but not in a record fails the build, and so does an Accepted decision that cites nothing.

```python
for a in adrs:
    for section in SECTIONS:
        if section not in a["text"]:
            problems.append(f"{a['path'].name}: missing '{section}'")
    for i in a["evidence"]:
        if i not in evidence:
            problems.append(f"{a['path'].name}: unknown evidence id '{i}'")
    if a["status"] == "Accepted" and not a["evidence"]:
        problems.append(f"{a['path'].name}: an Accepted decision must cite evidence")
```
{: data-file="scripts/build.py" }

A second check follows every source link to the lab repository's file, weekly as well as on every push, so a renamed results file shows up before a reader finds it.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| One file of evidence, generated into the records | Figures typed into each document | A number can only change in one place | A build step, and records that are partly generated |
| Mark measured and modelled decisions differently | Present the whole design with one voice | A reader should know which parts were run | One decision stays Proposed until a managed platform is run |
| Lead the cost model with a break-even | Rank platforms by monthly total | The total mostly ranks the assumed TB scanned per hour | No single "cheapest platform" answer |
| Open tables as the system of record | One managed platform for everything | Engines can change per workload without moving data | Table maintenance and a catalog to run |
| Workload tiers stated as assumptions | Claim a real company's numbers | Synthetic labs cannot honestly measure capacity | Tier figures are illustrations, not forecasts |

## Results

**Twelve of thirteen decisions are backed by measured results.** Among them: every record exact in {{ site.data.metrics.stream_failure_exactness.value }} failure runs; {{ site.data.metrics.lakehouse_rollback.value }} rows restored by a table rollback; and high-water-mark loads that lost {{ site.data.metrics.dsl_backwards_loss.value }} of a month when backfilled newest day first, which is why loads go by data interval. All 32 figures, with methods and sources, are in the repository's [EVIDENCE.md](https://github.com/technobasant/data-platform-architecture/blob/main/EVIDENCE.md).

**The platform cost turns on one ratio.** From list prices, paying per scan (BigQuery on-demand, Athena) costs less than a Medium Snowflake or Databricks warehouse until one hour of compute scans {{ site.data.metrics.dpa_break_even.value }}; against self-run Trino the line is about 0.4 TB. Which side a workload falls on is the measurement that decides its bill, and the guide shows how to take it from query history. The reasoning is in [the write-up](/writing/warehouse-bill-per-scan-or-per-hour/).

## What went wrong

**The first cost model ranked platforms by total.** At every workload tier, the per-scan engines came out cheapest by a factor of ten or more. The ranking was my own assumption about terabytes scanned per engine-hour, printed back. The model now leads with the break-even and prints the assumed ratio next to every total.

**Fact-checking caught overstatements before publishing.** Drafts said a restore recovered rows "deleted after the target time" (it restored a dropped table), that managed Postgres services cannot run Citus (Azure has offered managed Citus; Amazon RDS and Aurora do not offer it), and that a full scan at the large tier reads 23 TB (that is all stored data; the event history is about 18 TB, so the scan costs about $101, not $131). Each was checked against its source and corrected.

**The first diagram tried to show everything.** Every cross-cutting service on one chart made a tangle of crossing lines. The README now draws the data path only, and names the registry, probes and canaries in a sentence below it.

## What I'd do differently

**Measure the managed platforms.** Run the same dbt project and the same week of queries on Snowflake, Databricks and BigQuery, and replace the assumed compute equivalence with a measured one. Until then the cost guide is arithmetic.

**Build the CDC path.** Change data capture is in the design and not in any lab yet; replication slots across a Postgres failover are the first thing it has to prove.

**Exercise erasure.** The governance document designs deletion of one person's data across zones, snapshots and serving copies; a test that proves nothing remains would turn that design into evidence.

The decisions, documents, cost model and checks are in [data-platform-architecture](https://github.com/technobasant/data-platform-architecture).
