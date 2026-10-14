---
title: "streaming-platform: exactly-once clickstream, counted at every layer"
seo_title: "streaming-platform — Kafka, Flink, ClickHouse and Iceberg, Reconciled Through Failure"
hook: "Exactly-once is a claim about counts, so every layer was counted against a ledger, through broker kills, TaskManager kills and stalls"
description: "Open-source streaming platform: Kafka, Flink, ClickHouse and Iceberg reconciled event by event through nine failures, and where the window counts were not."
date: 2026-10-14
last_modified_at: 2026-10-14
kind: open-source
pillar: data-platforms
related: [spark-sql-kinesis, dataset-registry, realtime-ml]
order: 5
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "Three KRaft brokers, a Flink JobManager and two TaskManagers, ClickHouse, Iceberg on S3; up to 6,000 events/s; one container per node"
problem: "Exactly-once is usually asserted from configuration. I wanted it counted: every event at every layer, against a ledger of every fault injected, through the failures that are supposed to break it."
decision: "Make every hop transactional or idempotent, put a reconciler that counts by sequence number at the end of every run, and treat the window aggregates as a separate claim with its own check."
repo: "https://github.com/technobasant/streaming-platform"
flow: streaming-platform
cover:
  base: "/assets/images/editorial-streaming-platform-v1"
  width: 1600
  height: 900
  alt: "Bar chart: across nine failure runs, events.clean, ClickHouse and Iceberg stayed exact, while 10-second window counts held between 59.8% and 100% of on-time events"
  caption: "Every event layer stayed exact through nine failure runs, while the 10-second window counts fell to as little as 59.8% of on-time events."
  link: "/writing/exactly-once-records-not-window-counts/"
metrics: [stream_failure_exactness, stream_window_undercount, stream_freshness_p99, stream_stall_page]
stack: ["Apache Kafka 4.3", "Apache Flink 1.20", ClickHouse, "Apache Iceberg", "Schema Registry · Avro", Prometheus, Grafana, Python, Docker]
tags: [kafka-streaming, clickhouse, iceberg-lakehouse]
image: /assets/og/og-streaming.png
image_alt: "Kafka and streaming — exactly-once events, counted through failure"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

[streaming-platform](https://github.com/technobasant/streaming-platform) is a real-time data platform for the storefront clickstream of a fictional homewares retailer. Shoppers browse, add to cart, check out and pay, and the events arrive the way real ones do: some twice, some out of order, some minutes late, a few not even valid. Contracts sit at the front door, Kafka and Flink process everything exactly once, ClickHouse answers queries a few seconds old, Iceberg keeps the record, and a freshness SLO pages when the pipeline stalls.

It is a from-scratch reference system, not a production deployment. What makes it worth reading is the reconciler. A seeded generator writes a ledger of every event and every fault it injected; after each run, the reconciler counts the run at every layer — Kafka, Flink's output, ClickHouse, the Iceberg table, the dead-letter topic, the window aggregates — by sequence number. A layer is *exact* only when nothing is missing, nothing is there twice, and no poison leaked.

## Constraints

All nodes are containers on one Docker VM with 8 vCPU and 11.7 GiB, so replication and network latency are local, and a CPU stall on the host slows every node at once. A broker kill here is process death, not a network partition. Each experiment ran three times; load runs lasted 90 seconds, failure runs 90 to 330. Everything is in [MEASUREMENTS.md](https://github.com/technobasant/streaming-platform/blob/main/MEASUREMENTS.md), with the raw reconciliation reports in `results/`.

## Architecture

A generator sends Avro through an idempotent producer into `clickstream.raw`. A transactional gatekeeper decodes and validates each batch inside one Kafka transaction, writing valid events to `events.valid` and bad bytes, with a reason, to `events.dlq`. Flink 1.20 runs two SQL jobs: `clean` deduplicates on `event_id` and writes `events.clean` through a two-phase-commit Kafka sink and an Iceberg table that commits a snapshot per checkpoint; `windows` computes 10-second tumbling counts and 30-second sessions by event time and routes anything behind the watermark to `events.late`. ClickHouse reads every topic `read_committed` into `ReplacingMergeTree` tables keyed on the event. A probe exporter sends one synthetic event every 5 seconds through the front door and watches for it in ClickHouse; Prometheus turns those probes into multi-window burn-rate alerts.

Kafka is three KRaft nodes, each broker and controller, with every topic replicated three times and `min.insync.replicas=2`. Checkpoints run every 5 seconds to S3 on SeaweedFS.

## In the code

The window counts were the one layer that did not stay exact, and this split is why: the late filter routes on the same condition the window uses to drop, which keeps every event in exactly one place only while disorder stays inside the 5-second watermark. Catching up after a failure reorders partitions beyond that bound, so on-time events land in `events.late`, and after a restore `CURRENT_WATERMARK` is `NULL` until the first new watermark, so a late event read in that gap is dropped by the window and never routed.

```sql
CREATE TABLE events_clean (
  -- …
  -- Out-of-order tolerance: an event up to 5 s behind the newest one seen is on time.
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
-- …
  INSERT INTO agg_windows
  SELECT window_start, window_end, event_type,
         COUNT(*), SUM(COALESCE(amount_cents, 0)), COUNT(DISTINCT session_id)
  FROM TABLE(TUMBLE(TABLE shopper_events, DESCRIPTOR(event_time), INTERVAL '10' SECOND))
  GROUP BY window_start, window_end, event_type;
  -- …
  -- The window operator drops a record when the watermark has reached the last
  -- millisecond of its window (window_end - 1 ms), not merely its own timestamp.
  -- Route on the same condition so that every event lands in exactly one place.
  INSERT INTO events_late
  SELECT event_id, event_type, event_time, CURRENT_WATERMARK(event_time)
  FROM shopper_events
  WHERE CURRENT_WATERMARK(event_time) IS NOT NULL
    AND TIMESTAMPADD(SECOND, 10 - MOD(CAST(EXTRACT(SECOND FROM event_time) AS INT), 10),
          CAST(FLOOR(event_time TO SECOND) AS TIMESTAMP(3))) - INTERVAL '0.001' SECOND
        <= CURRENT_WATERMARK(event_time);
```
{: data-file="flink/sql/20-windows.sql" }

The whole job, including the parallelism and idle-timeout settings that each fixed an earlier miscount, is in [flink/sql/20-windows.sql](https://github.com/technobasant/streaming-platform/blob/main/flink/sql/20-windows.sql).

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| A transactional gatekeeper in front of Flink | Flink's `avro-confluent` format | The format can fail the job or drop a bad record silently; it cannot route one to a dead-letter topic with a reason | One process with one `transactional.id`. When its transaction coordinator died, the pipeline waited about 70 s |
| Transactions to Kafka, then `read_committed` into `ReplacingMergeTree` | A JDBC upsert sink | Every Flink sink stays two-phase-commit, and ClickHouse gets a replayable source | The 5 s checkpoint interval is the latency floor; ClickHouse's at-least-once ingest needs `FINAL` or a merge to be exact |
| Avro, `FULL_TRANSITIVE`, no auto-registration | `BACKWARD`; Protobuf | Producers and consumers deploy in any order, and old data stays readable by new code and the reverse | Every new field needs a default. Three breaking changes were refused with HTTP 409, which is the point |
| Late events to a side output | Allowed lateness with updating windows | Append-only outputs for transactional sinks, and no event silently dropped | A failure's reordering becomes a lasting under-count in the window table |
| Idle timeout of 60 s | The 10 s it started with | A partition that is only stalled must not be declared idle, or everything it delivers next is late | Windows close up to a minute late when traffic stops |
| A freshness SLO measured by probes | `now() - max(event_time)` | A probe measures the whole path and keeps measuring at zero traffic | It does not measure each shopper event; that comes from the reconciler |
| Iceberg REST catalog fixture on SeaweedFS | Hive Metastore, Nessie, Polaris | One small JVM, no database | No compaction or snapshot expiry yet |

## Results

In steady state, nine load runs and 2.7 million unique events with every fault injected came out exact at every layer, window counts included. ClickHouse made events queryable at a p99 of 6.1, 6.6 and 9.1 s at 1,000, 3,000 and 6,000 events/s, with the median just above half the checkpoint interval at every rate. Five dashboard queries on 6 million rows answered at a p50 of 8 to 26 ms while ingesting 2,000 events/s.

Through three controller-broker kills, three TaskManager kills and three 150-second stalls, every event layer stayed exact. The idempotent producer saw no failed sends; writes paused for about 10 seconds until the dead broker left the in-sync replicas. Restarts rewrote 658 to 7,522 records that aborted transactions had already written, and no `read_committed` reader saw them. A frozen pipeline paged in 59 to 62 seconds. The dead-letter topic held exactly the injected poison in every run of every experiment.

The window aggregates did not hold. Every failure moved on-time events into the late side output, up to 40% of one broker-kill run, and two restores lost late events from both the windows and the side output. [The analysis](/writing/exactly-once-records-not-window-counts/) takes that apart.

## What the measurements refused to show

**The aggregates are not exact under failure.** Catching up after a stall reads partitions at different speeds, so `events.clean` carries more disorder than the 5-second watermark bound allows. Restoring the `windows` job also drops late events that arrive before its first new watermark. The raw table and the lake keep every event; the window tables are fast and approximate during incidents.

**It got slower with age.** After about four hours of experiments, two 1,000/s runs had a p99 of 23 to 25 seconds instead of 6, with checkpoints stretching to 32 seconds and SeaweedFS at its 512 MB memory cap. They were still exact. It is not root-caused.

**The gatekeeper fix is unmeasured.** The 70-second stall came from librdkafka's 30-second connection-setup timeout to the dead coordinator. The timeout is now 5 seconds, and that change has not been re-run.

Building it surfaced bugs outside my code too. A broker healthcheck that started a JVM every 5 seconds held each broker at about 150% CPU, which voided every measurement taken before it was fixed. Kafka 4.1.0's group coordinator wedged after the VM clock stepped back ([KAFKA-19888](https://issues.apache.org/jira/browse/KAFKA-19888)). And librdkafka 2.16.0 aborted inside a timed-out admin request during broker kills ([librdkafka#4605](https://github.com/confluentinc/librdkafka/issues/4605)).

## What I'd do differently

**Run the failures before choosing the window semantics.** Append-only windows with a late side output were designed for clients that send late. A failure creates a different kind of lateness — disorder introduced by recovery itself — and that lateness looks identical in the output. Watermark alignment on the deduplicating job's source, and late events emitted from the window operator itself, are now on the roadmap.

**Soak, not sprint.** Ninety-second runs on a fresh stack are a best case. The four-hour slowdown only showed up because I repeated the load runs at the end.

**Give the broker test a real network.** QEMU VMs with `tc` would add the case containers cannot produce: a partition, where the broker is alive but unreachable.
