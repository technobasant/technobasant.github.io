---
title: "The read replica was meant to take the reports. 3 of 412 finished."
seo_title: "Postgres read replica cancelling long queries: max_standby_streaming_delay and hot_standby_feedback, measured"
description: "Reports moved to a Postgres read replica to protect the product. With default settings, 3 of 412 long runs finished, and even 0.1-second queries were cancelled."
date: 2026-10-19 11:30:00 +0545
last_modified_at: 2026-10-19
type: essay
pillar: data-platforms
tags:
  - postgres
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - PostgreSQL
  - hot standby
  - read replicas
  - recovery conflicts
mentions:
  - pgbench
  - Amazon RDS
  - data-platform-architecture
cover:
  base: "/assets/images/editorial-replica-reports-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Where a SaaS company's reports ran and what happened: on the primary the product's p95 latency went from 93 to 794 ms; on the read replica 3 of 412 long report runs finished; once the replica was 30 seconds behind even 0.1-second queries were cancelled; with hot_standby_feedback on, 20 of 20 finished"
  caption: "Two analysts, four reports, five minutes per scenario, on a lab copy of the database."
faq:
  - q: "Why does a Postgres read replica cancel long queries?"
    a: "The primary cleans up old row versions, and the replica has to replay that cleanup. A query on the replica that still needs those versions blocks the replay. After max_standby_streaming_delay, 30 seconds by default, the replica cancels the query with 'canceling statement due to conflict with recovery' (SQLSTATE 40001). In a test with the product updating rows at 100 requests a second, 3 of 412 runs of long reports finished on the replica in five minutes."
  - q: "Is max_standby_streaming_delay a per-query timeout?"
    a: "No. The PostgreSQL documentation says it is the maximum total time allowed to apply WAL once it has been received, so after one query has delayed replay, the next conflicting queries get much less grace. In the test, once the replica was 30 seconds behind, it cancelled conflicting queries at once: the median cancelled run lasted 0.1 seconds, and a 0.1-second report was cancelled 65 times."
  - q: "Does hot_standby_feedback fix replica query cancellations?"
    a: "It stops the cancellations caused by cleanup: with it on, 20 of 20 long report runs finished. The price is on the primary, which keeps the row versions the replica's queries need, so cleanup of the busiest tables waits for the longest report. The PostgreSQL documentation warns it can cause bloat on the primary; with one-to-two-minute reports the effect was not visible in five minutes, and it grows with the length of the reports."
key_takeaways:
  - "With BI reports on the primary, the product's p95 request latency went from 93 ms to 794 ms, and requests over 100 ms from 4.8% to 23.0%."
  - "On a read replica with default settings, 3 of 412 runs of three long reports finished in five minutes; the rest were cancelled by recovery conflicts."
  - "max_standby_streaming_delay is a budget for the replica's replay, not a timeout per query: once spent, even 0.1-second queries were cancelled."
  - "hot_standby_feedback made every report finish by moving the cost to the primary, whose cleanup waits for the longest report."
  - "A read replica is a copy of the product's database, not a reporting database; the fix for reports is a platform built for them."
---

"Put the reports on a read replica" is the standard first answer when analytics starts to hurt a product's database. The replica has the same data, it is one setting on RDS, and the product's primary is left alone. For short queries it works. For the reports a growing business actually runs, it trades one failure for another.

I measured both on a lab copy of a SaaS company's database, as the current state for an [architecture engagement](/work/data-platform-architecture/): what reports on the primary do to the product, and what happens to the same reports on a streaming replica.

**Operating rule.** Treat a read replica as a copy of the product's database, not as a reporting database. If long reports must run there for a while, choose the failure on purpose: cancelled reports by default, a replica that falls further behind with a longer delay, or held-back cleanup on the primary with `hot_standby_feedback`. Then build the reports somewhere designed for them.

## The setup

A Postgres 17 primary and a streaming replica, each limited to 2 vCPU and 4 GB, holding the company's tables at today's scale: 6,000 accounts, 60,000 users and 90 days of product events, 31.5 million rows. The product's request, a customer's usage page, an update to the user's last-seen time and an event insert, runs at 100 a second from pgbench, about half what the lab primary can serve. Two analysts run the BI tool's four reports in turn: revenue by plan (0.1 s on an idle primary), daily active users by plan over 90 days (49 s), the weekly event mix (90 s) and the top accounts of the last 30 days (15 s).

Each scenario ran for five minutes, after a forced checkpoint and with the replica caught up. The harness and every result are in [data-platform-architecture](https://github.com/technobasant/data-platform-architecture/tree/main/baseline).

## Reports on the primary

| The product's requests | p50 | p95 | p99 | Over 100 ms |
|---|---:|---:|---:|---:|
| No reports running | 4.9 ms | 93 ms | 483 ms | 4.8% |
| Two analysts' reports on the primary | 14.3 ms | **794 ms** | 1,847 ms | **23.0%** |
{: aria-label="The product's request latency without and with reports on the primary" }

The reports read the whole events table. That pushes the product's recent pages out of memory and takes its CPUs, and the product's 95th-percentile request got eight times slower. This is the month-end slowdown that sends reports to the replica in the first place.

## Reports on the replica

| Reports on the replica | Runs | Finished | Cancelled |
|---|---:|---:|---:|
| Three long reports, default settings | 412 | **3** | 409 |
| The 0.1-second revenue report, default settings | 138 | 73 | 65 |
| Three long reports, `hot_standby_feedback = on` | 20 | 20 | 0 |
| The revenue report, `hot_standby_feedback = on` | 7 | 7 | 0 |
{: aria-label="Reports finished and cancelled on the read replica under each setting" }

Every update on the primary leaves an old row version behind, and the primary's cleanup removes old versions once no transaction on the primary needs them. The replica replays that cleanup. If a report on the replica is still reading a version the cleanup removes, the replay has to wait for the report or cancel it. After `max_standby_streaming_delay`, 30 seconds by default, it cancels: `canceling statement due to conflict with recovery`, SQLSTATE 40001. The product updates its `users` table on every request, so cleanup records arrive constantly.

## The delay is a budget, not a timeout

The number of runs in that table looks odd: 550 report runs in five minutes, from two analysts. Most were cancelled almost immediately. The median cancelled run lasted 0.1 seconds, and even the 0.1-second revenue report was cancelled 65 times.

That is what the setting means. The PostgreSQL documentation is explicit that `max_standby_streaming_delay` "is not the same as the maximum length of time a query can run before cancellation; rather it is the maximum total time allowed to apply WAL data once it has been received from the primary server. Thus, if one query has resulted in significant delay, subsequent conflicting queries will have much less grace time until the standby server has caught up again."

One long report held replay back until the replica was 30 seconds behind. From then on, every query that conflicted with the next cleanup record was cancelled at once, until replay caught up, and the next long report started the cycle again. The replica spent the five minutes between 16 seconds behind at the median and 31 at the worst. The analysts in the harness went straight on to the next report each time, as people re-running a dashboard do, and three long reports finished.

## The three ways out, and what each costs

- **Leave the defaults.** Reports are cancelled, and the product is safe. Fine for short queries; for long reports it means dashboards that fail at random.
- **Raise `max_standby_streaming_delay`.** Reports get longer before they are cancelled, and the replica falls further behind while they run. Everything reading the replica, reports included, sees older data, and a replica that also serves the product's reads now serves stale ones. I did not measure this setting; its cost is the lag, which is unbounded at `-1`.
- **Turn on `hot_standby_feedback`.** The replica tells the primary which row versions its queries still need, and the primary keeps them. Every report finished. The cost moves to the primary: cleanup of the product's busiest tables waits for the longest report, and the documentation warns it "can cause database bloat on the primary for some workloads". With reports of one to two minutes the effect was not visible in five minutes; with hour-long reports it is an hour of the product's cleanup held back, every time one runs.

None of them makes a replica a reporting database. They choose which part of the system absorbs the conflict between a busy product and long reads of the same data.

## What the client did

For the engagement's client, the recommendation was the first option, deliberately, for at most three months: every report on the replica, defaults left alone, because a cancelled report is a better failure than a slower product or a bloated product database. Then a separate analytical platform fed by change data capture, where reports read their own copy and the product's database only serves a replication slot. The [case study](/work/data-platform-architecture/) has the rest: the options, the staged target and the decision records.

<div class="callout callout--note" markdown="1">
**Boundary.** Postgres 17.11 in Docker on a laptop, not RDS, with 2 vCPU and 4 GB per server. The primary and the replica share one host's disk, so in the replica scenarios the product's latency also rose; on separate machines it would not, and those figures are not used. Absolute latencies include the virtual disk's flush times. The counts of finished and cancelled reports, and the comparison on the primary, are the results. One run per scenario, five minutes each.
</div>

## Before you point reports at a replica

- Time your longest reports. Anything near or above `max_standby_streaming_delay` will be cancelled under write load.
- Count cancellations: `pg_stat_database_conflicts` on the replica, and SQLSTATE 40001 in the BI tool's logs.
- Watch the replica's replay lag while reports run, not only its average.
- If you turn on `hot_standby_feedback`, watch dead rows and table size on the primary's most-updated tables, and know your longest report.
- Do not give the product's own reads and long reports the same replica.
- Plan the move: reports that grow with the business need a store built for them.

## Frequently asked questions

### Why does a Postgres read replica cancel long queries?

The primary cleans up old row versions, and the replica has to replay that cleanup. A query on the replica that still needs those versions blocks the replay. After `max_standby_streaming_delay`, 30 seconds by default, the replica cancels the query with "canceling statement due to conflict with recovery" (SQLSTATE 40001). In a test with the product updating rows at 100 requests a second, 3 of 412 runs of long reports finished on the replica in five minutes.

### Is max_standby_streaming_delay a per-query timeout?

No. The PostgreSQL documentation says it is the maximum total time allowed to apply WAL once it has been received, so after one query has delayed replay, the next conflicting queries get much less grace. In the test, once the replica was 30 seconds behind, it cancelled conflicting queries at once: the median cancelled run lasted 0.1 seconds, and a 0.1-second report was cancelled 65 times.

### Does hot_standby_feedback fix replica query cancellations?

It stops the cancellations caused by cleanup: with it on, 20 of 20 long report runs finished. The price is on the primary, which keeps the row versions the replica's queries need, so cleanup of the busiest tables waits for the longest report. The PostgreSQL documentation warns it can cause bloat on the primary; with one-to-two-minute reports the effect was not visible in five minutes, and it grows with the length of the reports.

The harness, the queries and the results are in [data-platform-architecture](https://github.com/technobasant/data-platform-architecture/tree/main/baseline), with the engagement they belong to in [the case study](/work/data-platform-architecture/). More on [PostgreSQL](/writing/tags/postgres/).
