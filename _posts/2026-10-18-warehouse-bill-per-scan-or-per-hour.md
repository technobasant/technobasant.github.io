---
title: "Per scan or per hour: the number that decides an analytics bill"
seo_title: "Snowflake vs Databricks vs BigQuery vs Athena cost: the per-scan break-even"
description: "Per-scan billing beats per-hour warehouses until an hour of compute scans about 1.4 to 3.4 TB. The break-even from list prices, and how to find your own number."
date: 2026-10-18 18:00:00 +0545
last_modified_at: 2026-10-19
type: essay
pillar: data-platforms
tags:
  - cost-finops
  - iceberg-lakehouse
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - data platform cost
  - warehouse pricing
  - platform selection
mentions:
  - Snowflake
  - Databricks
  - BigQuery
  - Amazon Athena
  - Trino
  - data-platform-architecture
cover:
  base: "/assets/images/editorial-data-platform-architecture-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Table of four engines billed by the hour, with the terabytes one hour of compute must scan before BigQuery on-demand or Athena costs more: Trino on EC2 0.37 and 0.42, Snowflake Standard 1.41 and 1.6, Snowflake Enterprise 2.11 and 2.4, Databricks SQL Serverless 2.96 and 3.36"
  caption: "The break-even depends only on list prices. Where your workload sits relative to it is the part to measure."
faq:
  - q: "Is BigQuery or Athena cheaper than Snowflake or Databricks?"
    a: "It depends on how much data one hour of compute scans in your workload. From October 2026 list prices, a Medium Snowflake Enterprise warehouse costs $12 an hour, the same as scanning 2.11 TB on BigQuery on-demand or 2.4 TB on Athena. If an hour of your warehouse scans less than that, paying per scan is cheaper; if it scans more, paying for the hour is."
  - q: "How do I find how much my warehouse scans per hour?"
    a: "Divide a month of bytes scanned by a month of compute hours, both from query history. On Snowflake, BYTES_SCANNED is in SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY and credits in WAREHOUSE_METERING_HISTORY. On BigQuery, total_bytes_billed and total_slot_ms are in INFORMATION_SCHEMA.JOBS. On Databricks, system.billing.usage and the query history system table give the two halves."
  - q: "Why does per-scan pricing get expensive?"
    a: "Because the worst query sets the bill. At a large workload tier with about 18 TB of event history, one query that ignores partitioning and reads all of it costs about $101 on BigQuery on-demand every time it runs. A time-billed warehouse caps that query's cost at the hours it takes, and charges for idle time instead."
  - q: "Is a self-run Trino lakehouse the cheapest option?"
    a: "On the bill, often: four r7i.2xlarge workers cost $2.12 an hour at list price. The bill leaves out the catalog service, table maintenance, upgrades and the engineers who do them, which for a small team usually costs more than the difference."
key_takeaways:
  - "Paying per scan beats paying per hour until one hour of compute scans 1.41 to 3.36 TB, depending on the warehouse; for self-run Trino the line is 0.37 to 0.42 TB."
  - "That break-even depends only on list prices; whether your workload is above or below it is the measurement that decides the platform's bill."
  - "Ranking platforms by total monthly cost mostly ranks the assumption about scanned TB per hour, so state that assumption or do not rank."
  - "Per-scan pricing is set by the worst query: one full scan of 18 TB of history costs about $101 on BigQuery on-demand, every time."
  - "The cheapest line on a bill, a self-run engine, is priced without the people who run it."
---

Choosing between Snowflake, Databricks, BigQuery and an open lakehouse usually starts with features and ends with an argument about cost. The argument rarely settles anything, because the platforms charge for different things. Snowflake and Databricks charge for warehouse time. BigQuery on-demand and Athena charge for bytes scanned. A self-run Trino cluster charges you for instances.

Put on one axis, the comparison comes down to a single number: how many terabytes one hour of compute scans in your workload. Below a break-even, paying per scan is cheaper. Above it, paying for the hour is. The break-even depends only on list prices, so it can be computed for everyone. Where your workload sits is the part only your query history can tell you.

**Operating rule.** Before comparing platforms on cost, measure your workload's terabytes scanned per engine-hour, and compare it with the break-even. Do not rank platforms on total cost unless that ratio is stated next to the ranking.

This comes from the cost model in [data-platform-architecture v0.1.0](https://github.com/technobasant/data-platform-architecture/tree/v0.1.0), a reference architecture for a SaaS data platform whose other decisions are each backed by measurements in public labs. The cost model is not one of those measurements. It is arithmetic on on-demand list prices, retrieved from each vendor's own pricing page on 18 October 2026, for AWS us-east-1 (BigQuery: US multi-region). Every price, its source and the quoted line are in [`cost/prices.yml`](https://github.com/technobasant/data-platform-architecture/blob/v0.1.0/cost/prices.yml).

*Updated 19 October 2026:* the repository has since become an engagement for one client, whose data must stay in one EU region and whose requirements need Snowflake Enterprise. Re-priced for AWS EU (Ireland) at those editions, a medium engine-hour costs $15.60 to $21.84 and the line against Athena moves to 3.1–4.4 TB; the arithmetic below, on the first version's US prices, is unchanged as arithmetic.

## The break-even

The model prices one hour of a medium-sized engine on each time-billed option and divides it by the price of scanning a terabyte:

| Paid by the hour | Per hour | Same as scanning on BigQuery on-demand | Same as scanning on Athena |
|---|---:|---:|---:|
| Trino on EC2, four r7i.2xlarge workers | $2.12 | 0.37 TB | 0.42 TB |
| Snowflake Standard, Medium warehouse | $8.00 | 1.41 TB | 1.6 TB |
| Snowflake Enterprise, Medium warehouse | $12.00 | 2.11 TB | 2.4 TB |
| Databricks SQL Serverless, Medium | $16.80 | 2.96 TB | 3.36 TB |
{: aria-label="Terabytes one engine-hour must scan before per-scan billing costs more" }

The inputs are short. A Medium Snowflake warehouse uses 4 credits an hour, at $2 (Standard) or $3 (Enterprise) a credit. A Medium Databricks SQL Serverless warehouse uses 24 DBUs an hour at $0.70, instances included. BigQuery on-demand charges $6.25 per TiB, which is $5.68 per TB, after a free first TiB each month. Athena charges $5 per TB. Four r7i.2xlarge instances cost $0.5292 an hour each.

What "Medium" means is not the same on every platform, and nothing here measured one against another. The break-even is per hour of whatever you would actually run; if your Databricks workload needs a Small warehouse where Snowflake needs a Medium, use those prices instead.

## Why ranking totals misleads

My first version of the model printed a monthly total per platform for three workload sizes and sorted them. At every size, BigQuery and Athena came out cheapest, by a lot: about $175–220 a month against $2,200–4,700 for the warehouses at the middle tier.

That ranking was mostly my own assumption printed back to me. To price the warehouses I had to assume compute hours per day, and to price the scan-billed engines I had to assume terabytes scanned per day. Together those imply a ratio. At the middle tier it was 0.09 TB per engine-hour, a workload of many small queries on a warehouse kept warm through the day. Below every break-even in the table, per-scan wins. Raise the ratio past the break-evens (about 0.4 TB per hour against self-run Trino, 1.4 to 3.4 TB against the managed warehouses), a workload of heavy scans, and the ranking reverses.

So the model now leads with the break-even and prints the assumed ratio next to every total. A cost comparison that does not state how much an hour of compute scans has not compared anything.

## The worst query sets a per-scan bill

Per-scan pricing has a failure mode that per-hour pricing does not. At the large tier in the model, the event history is about 18 TB. A query that ignores the partitioning and reads all of it costs about $101 on BigQuery on-demand, and the same again each time a dashboard refreshes it. On a time-billed warehouse, that query costs the minutes it runs.

The trade goes the other way for idle time. A Snowflake warehouse bills per second with a 60-second minimum every time it resumes, so a dashboard that wakes it every few minutes pays for many minimum periods. Per-scan pricing charges nothing for idle.

That makes the platform choice partly a choice of discipline. Per-scan pricing needs partitioning, clustering and query review, or costs follow the worst query. Per-hour pricing needs auto-suspend and right-sized warehouses, or costs follow the idle hours.

## What the bill leaves out

Trino on EC2 has the lowest hourly price in the table, $2.12 for four workers. The model adds an always-on coordinator and storage, and at the middle tier the total is about $930 a month. It leaves out everything a managed service does for you: running the catalog, compacting and expiring tables, upgrading the engine, and the on-call. For a team of three, those hours cost more than the difference in the bill. The open tables underneath are still worth having (the architecture keeps them as the system of record so that engines can change), but the engine on top is a staffing decision as much as a pricing one.

## Find your own number

1. **Bytes scanned for a month.** On Snowflake, sum `BYTES_SCANNED` from `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`. On BigQuery, sum `total_bytes_billed` from `INFORMATION_SCHEMA.JOBS` in the region. On Databricks, the query history system table records what each query read.
2. **Compute hours for the same month.** On Snowflake, credits from `WAREHOUSE_METERING_HISTORY` divided by the warehouse's credits per hour. On BigQuery, `total_slot_ms` gives slot time, which is what the editions bill. On Databricks, DBUs from `system.billing.usage`.
3. **Divide** to get terabytes scanned per engine-hour, and compare it with the table.
4. **Put your own volumes** into the model's [`workloads.yml`](https://github.com/technobasant/data-platform-architecture/blob/v0.1.0/cost/workloads.yml) (the tiers this post uses are in version 0.1.0) and run it.
5. **Run a week of real queries** on the shortlist before committing. A break-even narrows the choice; only running the workload settles it.

<div class="callout callout--note" markdown="1">
**Boundary.** These are on-demand list prices on one day, in one region, with no commitments or discounts, which every serious contract has. BigQuery editions (slot-hours), Snowflake Gen2 warehouses and Redshift Serverless are not in the model. No platform was run against this workload: the break-even is arithmetic, and the compute equivalence between "Medium" sizes is assumed, not measured. Re-check the prices in the repository before using any figure.
</div>

## What to bring to a platform decision

- Your terabytes scanned per engine-hour, from a month of query history.
- The break-even for each option you are considering, at the size you would actually run.
- The worst query in your workload, and what it would cost on a per-scan engine.
- The idle pattern: how often dashboards wake a warehouse, and the minimum billed each time.
- Who will operate a self-run engine, and what their time costs.
- A week of real queries run on the shortlist.

## Frequently asked questions

### Is BigQuery or Athena cheaper than Snowflake or Databricks?

It depends on how much data one hour of compute scans in your workload. From October 2026 list prices, a Medium Snowflake Enterprise warehouse costs $12 an hour, the same as scanning 2.11 TB on BigQuery on-demand or 2.4 TB on Athena. If an hour of your warehouse scans less than that, paying per scan is cheaper; if it scans more, paying for the hour is.

### How do I find how much my warehouse scans per hour?

Divide a month of bytes scanned by a month of compute hours, both from query history. On Snowflake, `BYTES_SCANNED` is in `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` and credits in `WAREHOUSE_METERING_HISTORY`. On BigQuery, `total_bytes_billed` and `total_slot_ms` are in `INFORMATION_SCHEMA.JOBS`. On Databricks, `system.billing.usage` and the query history system table give the two halves.

### Why does per-scan pricing get expensive?

Because the worst query sets the bill. At a large workload tier with about 18 TB of event history, one query that ignores partitioning and reads all of it costs about $101 on BigQuery on-demand every time it runs. A time-billed warehouse caps that query's cost at the hours it takes, and charges for idle time instead.

### Is a self-run Trino lakehouse the cheapest option?

On the bill, often: four r7i.2xlarge workers cost $2.12 an hour at list price. The bill leaves out the catalog service, table maintenance, upgrades and the engineers who do them, which for a small team usually costs more than the difference.

The model as this post used it is in [data-platform-architecture v0.1.0](https://github.com/technobasant/data-platform-architecture/tree/v0.1.0), and the current, re-priced one in [the main branch](https://github.com/technobasant/data-platform-architecture), with the design in [the case study](/work/data-platform-architecture/). More on [cost](/writing/tags/cost-finops/) and [the lakehouse](/writing/tags/iceberg-lakehouse/).
