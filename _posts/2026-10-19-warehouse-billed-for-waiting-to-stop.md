---
title: "The day's work took 38 seconds. The warehouse was billed for 11 minutes."
seo_title: "Databricks SQL serverless cost: auto-stop, idle time and DBUs, measured from the billing tables"
description: "A client's daily build and reports took 38 seconds on Databricks' smallest SQL warehouse. The billing table charged 11 minutes: 95% of it was waiting to stop."
date: 2026-10-19 20:45:00 +0545
last_modified_at: 2026-10-19
type: essay
pillar: data-platforms
tags:
  - databricks
  - cost-finops
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - Databricks SQL
  - serverless SQL warehouses
  - cloud cost
  - auto-stop
mentions:
  - Databricks
  - system.billing.usage
  - data-platform-architecture
cover:
  base: "/assets/images/editorial-warehouse-idle-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "One day's work on a 2X-Small Databricks SQL warehouse: the daily build took 24 seconds and two analysts' reports 8 seconds, then the warehouse sat idle for 10 minutes until auto-stop; the billing table charged 0.743 DBU for 11 minutes 9 seconds awake, 95% of it waiting"
  caption: "The work set none of the bill's minutes; the auto-stop setting set most of them."
faq:
  - q: "How does a Databricks serverless SQL warehouse bill?"
    a: "For the time it is running, at the size's DBU rate, whether or not a query is executing. On the smallest size, 2X-Small, the billing table charged exactly 4 DBU an hour of uptime in every hour checked against the warehouse's own start and stop events, four of them."
  - q: "What does auto-stop cost?"
    a: "Every time the warehouse wakes, it stays up for the auto-stop period after the last query. With the 10-minute setting in the test, a day's build and reports that took 38 seconds were billed for 11 minutes 9 seconds: 0.743 DBU, of which 95% was the wait to stop."
  - q: "How should a Databricks SQL warehouse's cost be estimated?"
    a: "By the hours it will be awake, not by the queries. Count how often it wakes and how long each wake lasts with the auto-stop tail, multiply by the size's DBU rate and the region's price per DBU, and check the estimate monthly against system.billing.usage and system.compute.warehouse_events."
key_takeaways:
  - "The client's daily build and one round of reports took 38 seconds on a 2X-Small warehouse; the billing table charged 11 minutes 9 seconds of uptime."
  - "Billed DBUs matched uptime at exactly 4 DBU an hour for a 2X-Small, in every hour checked against the warehouse's start and stop events."
  - "95% of the day's bill was the 10-minute auto-stop wait after the last query."
  - "At list price in the client's EU region the same work costs $21 a month woken once a day, and $961 kept awake through working hours."
  - "Anything that must answer at any hour, like a customer-facing assistant, should not keep the warehouse awake: that alone is $2,657 a month."
---

A warehouse that bills by the second sounds as if it bills for work. It bills for being awake. For a small, bursty workload the difference is most of the bill, and it is set by one setting most teams never change.

I measured it for the cost criterion of a platform proof of concept for a fictional SaaS client, in [data-platform-architecture](/work/data-platform-architecture/): what the platform's own billing table charges for one day of the client's work.

**Operating rule.** Estimate a SQL warehouse by the hours it will be awake, not by its queries. Set auto-stop on purpose, wake it as few times a day as the work allows, keep anything that must answer at any hour off it, and check the estimate every month against the billing table and the warehouse's start and stop events.

## The test

The client's data at today's scale: 6,000 accounts, 60,000 users and 90 days of product events, 31.5 million rows, in Databricks SQL 2026.39 on the smallest serverless SQL warehouse, 2X-Small, with the default 10-minute auto-stop. The day's work, as the client's design has it:

- **The daily build.** Load yesterday's 350,000 events with `INSERT … REPLACE WHERE`, replace the last three days of the usage mart, and run the mart contract's quality check.
- **The reports.** Two analysts run the BI tool's four reports once each.

The warehouse started from stopped at the top of an hour and nothing else touched it until the hour was over, so that hour's billing rows belong to this work alone. The figures come from three system tables: `system.query.history` for the statements, `system.compute.warehouse_events` for start and stop, and `system.billing.usage` for what was charged. Free Edition runs no bill, but its billing table records usage the same way, and the list price turns it into money.

## What was billed

| | Time (UTC) | |
|---|---|---|
| Warehouse starting | 11:00:32.6 | |
| First statement | 11:00:32.7 | the build: 23.7 s of statements |
| Last statement ends | 11:01:10.4 | the reports: two analysts, 7.5 s |
| Stopping | 11:11:13.3 | ten minutes after the last statement |
| Stopped | 11:11:43.4 | |
| **Billed** | | **0.743 DBU**, for 11 min 9 s running |
{: aria-label="One day's work on the warehouse, and what the billing table charged" }

The work took 38 seconds from the first statement to the last. The warehouse was billed for 11 minutes 9 seconds, from running to stopped, at 4 DBU an hour: 10 minutes 33 seconds of it, 95%, came after the last statement, the warehouse waiting to stop.

The rate is the size's, and it is exact. In three earlier hours the same warehouse was up 54.2, 33.45 and 27.37 minutes, and the billing table charged 3.614, 2.230 and 1.825 DBU: 4 DBU an hour of uptime, to the second, whatever ran in it.

## The bill is set by how often the warehouse wakes

At list price in the client's region, AWS EU (Ireland), a DBU of serverless SQL is $0.91, so an hour of the smallest warehouse is $3.64. The day above cost about $0.68. What the month costs depends on how the warehouse is used, not on the work:

| How the warehouse is used | Hours awake a month | List price a month |
|---|---:|---:|
| Woken once a day: the build, then the reports | 5.6 | $21 |
| The build, and reports in six separate sessions on working days | about 30 | about $109 |
| Awake through EU working hours, 12 hours on 22 days | 264 | $961 |
| Awake all month | 730 | $2,657 |
{: aria-label="Monthly cost of the smallest Databricks SQL warehouse by how often it is awake" }

Each separate session costs at least the auto-stop period: an analyst who opens one dashboard at 10:00 and another at 10:30 pays for two ten-minute tails. A dashboard that refreshes every five minutes keeps the warehouse awake forever. The client's cost model had assumed 1.5 hours a day of a Medium warehouse, about $996 a month in this region; the measurement says the smallest size does today's work in seconds, and the same money buys a 2X-Small awake through every working hour.

The last row is the one that changed the design. The client's stage-3 assistant answers customers, who ask at any hour, so a warehouse serving it never stops: $2,657 a month at the smallest size, more than the assistant's whole $1,500 ceiling, before a single model token, which costs the same assistant about $19 a month. Its queries go to the usage store the product already keeps awake, as the [AI architecture](/work/ai-platform-architecture/) now records.

<div class="callout callout--note" markdown="1">
**Boundary.** One day, one warehouse of the smallest size, on Databricks Free Edition, whose warehouse is in US East: the billing table's DBUs are measured, the dollars are list price for the client's EU region and include no discount. Serverless start-up was about 2 seconds here; a larger size or a cold region may take longer. Auto-stop was the default 10 minutes; a shorter one shortens every tail and wakes the warehouse more often. At 36 months the client's data is about 14 times larger, and keeping the reports to seconds will need a bigger size, whose rate scales the same arithmetic.
</div>

## Checks before trusting a warehouse estimate

- Price the warehouse by hours awake: wakes a day, times work plus the auto-stop period, times the size's DBU rate and the region's price.
- Set auto-stop deliberately, and know that every separate session pays for one full tail.
- Batch scheduled jobs so the warehouse wakes once for them, not once per job.
- Find what keeps it awake: dashboard auto-refresh, monitoring queries, a service polling it.
- Keep anything that must answer at any hour, a product page or an assistant, off the warehouse.
- Each month, compare `system.billing.usage` with uptime from `system.compute.warehouse_events`; they should agree to the size's rate.

## Frequently asked questions

### How does a Databricks serverless SQL warehouse bill?

For the time it is running, at the size's DBU rate, whether or not a query is executing. On the smallest size, 2X-Small, the billing table charged exactly 4 DBU an hour of uptime in every hour checked against the warehouse's own start and stop events, four of them.

### What does auto-stop cost?

Every time the warehouse wakes, it stays up for the auto-stop period after the last query. With the 10-minute setting in the test, a day's build and reports that took 38 seconds were billed for 11 minutes 9 seconds: 0.743 DBU, of which 95% was the wait to stop.

### How should a Databricks SQL warehouse's cost be estimated?

By the hours it will be awake, not by the queries. Count how often it wakes and how long each wake lasts with the auto-stop tail, multiply by the size's DBU rate and the region's price per DBU, and check the estimate monthly against `system.billing.usage` and `system.compute.warehouse_events`.

The runner and its results are in [data-platform-architecture](https://github.com/technobasant/data-platform-architecture/tree/main/poc/databricks), with the rest of the proof of concept in its [proof-of-concept document](https://github.com/technobasant/data-platform-architecture/blob/main/docs/11-proof-of-concept.md). More on [Databricks](/writing/tags/databricks/) and [cost](/writing/tags/cost-finops/).
