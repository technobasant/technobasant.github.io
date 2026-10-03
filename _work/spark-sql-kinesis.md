---
title: "spark-sql-kinesis: a Kinesis source for Spark 4 without the idle-shard floor"
seo_title: "spark-sql-kinesis — an Open-Source Kinesis Source for Spark 4"
hook: "Spark 4 dropped the AWS SDK the streaming connector depended on, and the maintained alternative paid seconds on every idle shard"
description: "Open-source maintenance case: porting a Kinesis connector to Spark 4.2 and AWS SDK v2, replacing KCL, and upgrading production in place with no drain."
date: 2026-08-10
last_modified_at: 2026-10-03
kind: open-source
order: 1
role: "Maintainer"
org: "Open source"
period: "2023 – present"
team: "Solo maintainer"
scale: "Streaming jobs that read Kinesis on Spark 4"
problem: "Spark 4 removed AWS SDK v1, the connector was pinned to SDK v1 and KCL 1.x past end of life, and the awslabs replacement waited out an idle floor on every shard in every micro-batch."
decision: "Keep the synchronous read model, port it to Spark 4.2 and AWS SDK v2, replace KCL with a small KPL decoder, and keep the checkpoint format byte-identical so production upgrades in place."
repo: "https://github.com/technobasant/spark-sql-kinesis"
metrics: [kinesis_idle_floor]
stack: [Scala, "Apache Spark 4.2", "AWS SDK v2", "Amazon Kinesis", "Kinesis Producer Library", Protobuf, Maven, "Maven Central"]
tags: [kafka-streaming, spark]
image: /assets/og/og-streaming.png
image_alt: "Kafka and streaming — a Kinesis source for Spark 4, maintained in the open"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

The connector reads and writes Amazon Kinesis from Spark Structured Streaming. Qubole wrote it; Ron Cemer ported it to Spark 3.2; then [upstream](https://github.com/roncemer/spark-sql-kinesis) was declared unmaintained and its use "strongly discouraged". The streaming analytics platform I work on runs on it, so since 2023 I have carried it myself — Spark 3.2, 3.3 and 3.4 builds, Scala 2.13, in [a public repository](https://github.com/technobasant/spark-sql-kinesis).

Spark 4 turned maintenance into a decision. The connector was pinned to AWS SDK v1, end of life on 2025-12-31, and KCL 1.x, end of life on 2026-01-30. The obvious replacement, the [awslabs connector](https://github.com/awslabs/spark-sql-kinesis-connector), reads through a background queue and infers end-of-data from consecutive empty polls, so every shard waits out a floor in every micro-batch, even with zero records. On a stream with many shards and modest traffic, that floor dominates batch latency.

## My role

I own the connector end to end: the Spark 4.2 and AWS SDK v2 port, the KCL removal, the test suites, the release pipeline to Maven Central under `io.github.technobasant`, and the in-place production upgrade. Before porting, I measured the awslabs connector on staging and ran a production comparison — which taught me as much about benchmark contamination as about connectors. That story is written up in [Ten seconds per idle shard](/writing/spark-4-kinesis-connector-idle-floor/).

## Decisions

| Decision | Alternative | Why |
|---|---|---|
| Keep the synchronous DataSource V1 read model | Adopt the awslabs DSv2 connector and tune it | Tuning cuts the floor to a legal minimum of six seconds per shard, at the cost of a task slot and a heap-resident queue per shard. The synchronous model stops when the shard reports it is caught up: one round trip. |
| Replace KCL with a small KPL decoder | Port to KCL 2.x | KCL was only needed to decode the KPL aggregation format, and the KPL already ships those protobuf classes. Dropping it removed DynamoDB, CloudWatch and Netty transitives without reworking resharding. |
| Keep the offset JSON and shard-commit layout byte-identical | A cleaner new checkpoint format | Running queries resume their existing checkpoints across a Spark major version: no write pause, no drain, no offset migration, no data gap. |
| Put the Spark version in the artifact version | One artifact across Spark minors | The connector links against Spark streaming internals that move between minors, so a jar is only valid for the minor it was built against. Making that visible prevents a silent mismatch. |
| Shade AWS SDK v2, Netty, protobuf and HttpClient | Rely on the cluster's classpath | `hadoop-aws` brings its own SDK and HTTP clients; shading means the connector cannot collide with them. Apache HttpClient is pinned rather than left to `ServiceLoader` ordering. |
| Publish to Maven Central via the Central Portal | Hand-built jars in each deployment | The old release path targeted Sonatype's retired OSSRH and no longer worked. A resolved dependency replaces a binary checked into `lib/`. |

## Results

`1.3.0_spark-4.2.0` is on Maven Central for Spark 4.2, Scala 2.13 and Java 17, with no `com.amazonaws` artifact left in the dependency tree. Production moved to it in place against existing checkpoints. The claim that nothing was lost rests on the unchanged offset format and resumed sequence numbers, not on a separate record-level reconciliation.

The choice of read model was validated against internal production traffic; those figures stay internal. The public evidence is on staging, a sixteen-shard test stream: the awslabs connector at its defaults took 174 s per micro-batch, almost all of it the idle floor paid in serial waves, and 47 s after giving it one task slot per shard and the lowest legal floor. Its remaining cost against the synchronous model is structural, not a tuning gap.

The port also surfaced three defects that no test had reached. A credentials builder stored session credentials and never read them. Shard listing sent `streamName` together with `nextToken`, which the API rejects on paginated calls. And the first test of the new decoder showed the protobuf version was too old for the KPL's generated code — a `NoClassDefFoundError` that only appears at runtime, when a record is decoded.

## What I would do differently

**Benchmark with one consumer from the start.** My first production comparison ran beside the live job on the same stream, shared its per-shard read limits, and slowed it by roughly 70%. Every number from that run was void, and I had to retract a projection built on it.

**Publish a clean before-and-after for the port itself.** The case for the synchronous model rests on the mechanism, staging measurements and internal production data. A public, single-consumer comparison on a reproducible stream would let anyone check it.

**Close the resharding gaps.** New and child shards created mid-query start from the configured position rather than the parent's committed one, and with `failondataloss=false` a deleted shard is dropped with a warning. Both are documented and safe in steady state, and both are the next things worth fixing. A DataSource V2 rewrite stays on the roadmap only if it keeps the synchronous fetch.
