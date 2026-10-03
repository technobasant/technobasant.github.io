---
title: "Ten seconds per idle shard: why I maintain a Kinesis connector for Spark 4"
seo_title: "Spark 4 Kinesis connector: AWS SDK v2 and no idle-shard floor"
description: "The awslabs Kinesis connector for Spark 4 waits on every idle shard. Why I ported the synchronous connector to Spark 4.2 and AWS SDK v2, and maintain it in public."
date: 2026-10-03 10:00:00 +0545
last_modified_at: 2026-10-03
type: essay
tags: [kafka-streaming, spark]
toc: true
featured: true
work: spark-sql-kinesis
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - Spark Structured Streaming
  - Amazon Kinesis Data Streams
  - open-source connector maintenance
  - benchmark methodology
mentions:
  - Apache Spark 4.2
  - AWS SDK for Java v2
  - awslabs spark-sql-kinesis-connector
  - Kinesis Producer Library
  - Maven Central
cover:
  base: "/assets/images/editorial-spark-kinesis-connector-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic comparing two Kinesis read models: a background queue that waits through empty polls on every idle shard, and an in-task fetch that stops when the shard is caught up and resumes an unchanged checkpoint"
  caption: "On a stream with many quiet shards, the read model decides batch latency. Tuning the other one only moves the floor."
faq:
  - q: "Why is the awslabs Kinesis connector for Spark slow when shards are idle?"
    a: "It fetches on a background thread into a queue and decides a shard is exhausted only after a number of consecutive empty polls. With the defaults of two polls at five seconds each, every shard in every micro-batch waits about ten seconds even when it holds zero records. The lowest value the connector accepts is two polls of three seconds."
  - q: "Which Kinesis connector works with Spark 4 and AWS SDK v2?"
    a: "Besides the awslabs connector, io.github.technobasant:spark-sql-kinesis_2.13:1.3.0_spark-4.2.0 on Maven Central is a Spark 4.2, Scala 2.13, Java 17 build of the synchronous connector originally written by Qubole, ported to AWS SDK v2 with KCL removed. Each jar targets one Spark minor version, which is why the Spark version is part of the artifact version."
  - q: "Can a running Spark 3.4 streaming query move to the Spark 4 build without a new checkpoint?"
    a: "Yes, for this connector. The port kept the offset JSON byte-identical and the shard-commit layout unchanged, so the query resumes its existing checkpoint. Stop the old job before the new one starts, because two queries writing one checkpoint directory corrupt it."
  - q: "How do you benchmark a new Kinesis consumer without contaminating production?"
    a: "Do not run it beside the incumbent on the same stream. Per-shard read limits are shared by every shared-throughput consumer. Stop the incumbent, let the candidate run as the only reader, compare against the incumbent's own uncontended history, and watch throttling and iterator age as contamination detectors."
key_takeaways:
  - "The awslabs connector infers end-of-data from empty queue polls, so batch read time is roughly ceil(shards / task slots) × the idle floor, even at zero records."
  - "Tuning it is possible but not free: one task slot per shard, a heap-resident queue per task, and a legal floor of six seconds that still dwarfs one API round trip."
  - "A shadow job on the same stream shares per-shard read limits with production, slowed the live job by roughly 70%, and voided every number it produced."
  - "Porting the synchronous connector to Spark 4.2 and AWS SDK v2 replaced KCL with a small KPL decoder and kept the offset format byte-identical."
  - "Because the checkpoint format did not change, production upgraded in place with no drain, no write pause, and no data gap."
---

Spark 4 dropped the bundled AWS SDK v1, so a streaming job that reads Kinesis needs a connector built against SDK v2. The obvious choice was the [awslabs connector](https://github.com/awslabs/spark-sql-kinesis-connector). On staging, with two records in the micro-batch, it took 174 seconds against a one-minute trigger. The connector it was replacing read the same idle shards for about one API round trip each.

I could tune that down, and did. Then I benchmarked the tuned version against production, published a projection from the run, and had to withdraw it. What I ended up shipping was neither: a port of the old synchronous connector to Spark 4.2 and AWS SDK v2, which I now maintain in public as [`technobasant/spark-sql-kinesis`](https://github.com/technobasant/spark-sql-kinesis).

**Operating rule.** On a stream with many shards and modest traffic, the read model decides batch latency, not the tuning. Pick the read model first. And before you trust any number for a new consumer, name the resource it shares with the incumbent — on Kinesis, per-shard read limits — and watch the incumbent for the whole run. If the incumbent moves, the number is void.

## What the connector is, and why it still exists

The connector was written by Qubole for Structured Streaming and later ported to Spark 3.2 by Ron Cemer, after which [upstream](https://github.com/roncemer/spark-sql-kinesis) was declared unmaintained and its use "strongly discouraged". I had already been carrying it through Spark 3.2, 3.3 and 3.4 with Scala 2.13 since 2023, because the streaming analytics platform I work on runs on it. Spark 4 forced the real decision: AWS SDK v1 reached end of life on 2025-12-31 and KCL 1.x on 2026-01-30, and the connector was pinned to both.

The `1.3.0_spark-4.2.0` release is on Maven Central:

```scala
libraryDependencies += "io.github.technobasant" % "spark-sql-kinesis_2.13" % "1.3.0_spark-4.2.0"
```
{: data-file="build.sbt" }

It targets Spark 4.2, Scala 2.13 and Java 17. The Spark version is part of the artifact version on purpose. The connector links against Spark's streaming internals, which move between minor releases (Spark 4.2 relocated `SerializedOffset`, `OffsetSeq` and friends), so a jar only works on the Spark minor it was built for. AWS SDK v2, Netty, protobuf and Apache HttpClient are shaded under the connector's own package, so it cannot collide with whatever `hadoop-aws` puts on the classpath.

Reading looks the way it always has:

```scala
val events = spark.readStream
  .format("kinesis")
  .option("streamName", stream)
  .option("endpointUrl", "https://kinesis.us-east-1.amazonaws.com")
  .option("startingPosition", "LATEST")   // read only when the checkpoint is empty
  .load()
```

On EKS with IRSA you pass no keys; the default provider chain resolves the web identity. The awslabs connector registers `aws-kinesis`, so both can be installed side by side during a comparison — which, as it turned out, is exactly where the trouble starts.

## Where ten seconds per shard comes from

The two connectors read Kinesis in fundamentally different ways.

This connector is a DataSource V1 source. Each task calls `getRecords` inline and stops the moment Kinesis reports it is caught up:

```scala
// spark-sql-kinesis KinesisSourceRDD: synchronous, in-task
if (records.millisBehindLatest.longValue() == 0) { /* stop fetching this shard */ }
```

The awslabs connector is DataSource V2. A background publisher fetches into a `BlockingQueue` and the partition reader drains it. Nothing on the reader side says a shard is caught up, so it infers end-of-data from silence:

```scala
// awslabs KinesisV2PartitionReader.pollNextUserRecord: asynchronous, inferred
dataQueue.poll(dataQueueWaitTimeout.getSeconds, SECONDS)
// ... end-of-data only after maxDataQueueEmptyCount consecutive empty polls
```

The defaults are two empty polls of five seconds. **Every shard pays ten seconds in every micro-batch, including shards that hold no records at all.** An idle shard on the synchronous connector costs one round trip.

The connector maps one Spark task to each shard, and a task blocked in `poll` holds a task slot while using almost no CPU. So the read stage runs in waves:

```text
read time ≈ ceil(shards / task slots) × floor
```

The staging stream has sixteen shards and the executor had one core, so one task slot. The model predicts 16 × 10 s = 160 s. The measured read stage was 167 s, with individual tasks at 10.1–11.9 s and offset planning at 0.4 s. The floor explains 160 of the 167 seconds.

[Enhanced fan-out](https://docs.aws.amazon.com/streams/latest/dev/enhanced-consumers.html) does not help. Both publishers feed the same queue and the reader has no branch on consumer type. The queue exists because fan-out pushes records and needs a buffer; polling inherits the cost without needing it.

## What it costs to tune the floor away

The model points at two levers, and both cost something. This is the part of "slower and heavier" that is easy to miss: the awslabs connector can be made faster, but only by spending resources the synchronous connector never needed.

**Task slots.** To finish in one wave you need a slot per shard. In the Spark operator, `cores` is the slot count and also — only when `coreRequest` is unset — the pod's CPU request. Pinning `coreRequest` decouples them:

```yaml
executor:
  # Task SLOTS, not CPU. Each shard task parks on BlockingQueue.poll (~0 CPU).
  cores: 16
  coreRequest: "1"   # pod CPU request unchanged
  coreLimit: 2000m
```
{: data-file="streaming-job.yaml" }

CPU request, driver and pod count stayed the same. The cost moves to heap: every task can buffer up to the queue capacity of 1,000 records, so slots-per-shard means queues-per-shard.

**The floor.** It is set by two undocumented `kinesis.internal.` options. My first attempt, one poll of one second, was rejected:

```text
IllegalArgumentException: kinesis.internal.maxDataQueueEmptyCount
  * kinesis.internal.dataQueueWaitTimeoutSec must be greater than 5
```

That is a data-safety guard — it stops a slow fetch being mistaken for an empty shard — and I would not patch it out. But it is validated when the streaming query starts, after the checkpoint has been restored, so each attempt ran the driver for about three minutes before dying. Under `restartPolicy: Always` that crash-looped staging for roughly forty minutes. Two polls of three seconds is the lowest legal floor.

| Staging configuration | Per-task read | Batch (`addBatch`) |
| --- | --- | --- |
| 1 slot, 10 s floor (defaults) | 10.1–11.9 s, serialised | 174 s |
| 16 slots, 6 s floor (lowest legal) | 8.4 s, all in parallel | **47 s** |

That is 3.7× on the batch, and the remaining forty-odd seconds are sequential table writes, not the connector. But the best the awslabs design can do on an idle shard is six seconds, against one round trip, and it costs a slot and a queue per shard to get there.

<div class="callout callout--gotcha" markdown="1">
**Silent options.** Both connectors ignore option names they do not recognise. A half-finished migration from one to the other starts cleanly, reads with defaults you did not choose, and looks configured. Lock the option contract your job emits in a test, and make that test *fail*, not cancel, when the connector jar is missing from the classpath.
</div>

## The benchmark that measured itself

Staging proved the mechanism. It could not show whether Spark 4 on the awslabs connector would keep up with production traffic. So I ran a shadow Spark 4 job beside the live Spark 3.4 job in one production region: same stream, same trigger, separate output prefix.

The live job, which nobody had touched, **slowed by roughly 70%** as soon as the shadow started, and its consumer's iterator age rose by about 40%. Incoming volume was flat, so traffic was ruled out. Throttling appeared only while the shadow ran. The cause is a documented limit I had not taken seriously enough: Kinesis gives each shard [five `GetRecords` calls per second and 2 MB/s of reads](https://docs.aws.amazon.com/streams/latest/dev/service-sizes-and-limits.html), *shared across every shared-throughput consumer*. A second consumer doubles read demand on every shard, and both back off.

So every number the shadow produced was taken under contention it created. Its best batch was 2.5× the live job's uncontended median, and that is not a measurement of Spark 4. It is a measurement of two consumers fighting over one budget.

One observation did not fit even after allowing for that. Some of the shadow's read stages were floor-bound exactly as the model predicts. But the dominant read stage in each batch ran two to three orders of magnitude slower per task than the synchronous connector on the same stream. In production the idle floor was not the main cost; backlog per task and throttled retry backoff are the likely candidates, and I did not establish which.

That is where the retraction comes in. I had projected that this region on Spark 4 would hold roughly its current batch time, on the assumption that the six-second floor was the only added cost. The data did not support the assumption. I withdrew the projection in writing, in the findings document the team was working from. A wrong number left in a findings document gets quoted in someone else's plan a month later.

## What a valid comparison looks like

The fix is not a cleverer analysis of contaminated data. It is a different experiment.

| Contaminant | How it shows up | Control |
| --- | --- | --- |
| Shared per-shard read limits | Incumbent's batch time and iterator age rise when the candidate starts | Run the candidate as the only consumer; stop the incumbent for the window |
| GitOps self-heal | The stopped job reappears within one sync interval | Stop it with a git change or a suspended app, not `kubectl delete` |
| Baseline drift | Comparing against a handful of batches from a different hour | Use the incumbent's own uncontended history |
| Mixed stage types | Read stages averaged with shuffle stages on the write path | Filter to stages with exactly one task per shard, never `>=` |
| Wrong batch boundaries | Log-derived durations end too early | Take `addBatch` from streaming-query progress, not a log line |

The last two rows came from my own scripts, and both looked plausible on first read. That is the argument for writing the filter and the boundary definition next to every number they produced. The measurement itself is cheap once the experiment is clean: per-stage timings from Spark's [monitoring REST API](https://spark.apache.org/docs/latest/monitoring.html#rest-api), and two CloudWatch series as contamination detectors that must stay flat while the candidate runs.

```bash
curl -s "localhost:4040/api/v1/applications/${APP_ID}/stages?limit=400" > stages.json

for m in ReadProvisionedThroughputExceeded GetRecords.IteratorAgeMilliseconds; do
  aws cloudwatch get-metric-statistics --namespace AWS/Kinesis --metric-name "$m" \
    --statistics Maximum --period 60 --dimensions Name=StreamName,Value="${STREAM}" \
    --start-time "${START}" --end-time "${END}"
done
```

## Porting instead of tuning

By then the conclusion was clear, and it was validated against internal production traffic: the synchronous read model is the right one for this workload, and the awslabs connector needed more slots, more heap and still paid a floor the old one did not.

The awkward part is that three days earlier I had written "do not port the old connector". I assumed removing KCL meant reworking resharding. That was mostly wrong. The connector used KCL for one thing that mattered: decoding the KPL record-aggregation format. The KPL already ships the protobuf classes for that format, so a small `AggregatorUtil` replaced KCL entirely, along with its DynamoDB, CloudWatch and Netty transitives. Sub-records keep their *parent* record's sequence number, matching KCL 1.x's `UserRecord`, because that is what the connector checkpoints on.

The rest of the port was mechanical but not trivial:

- **SDK v2 credentials.** STS moved to `StsAssumeRoleCredentialsProvider`; the instance-profile retry wrapper had to delegate rather than extend, because v2's provider is final; the region is now parsed from the endpoint URL, because v2 removed the reverse lookup.
- **HTTP client pinned.** The KPL contributes a second synchronous HTTP implementation through the Glue schema registry, which leaves `ServiceLoader` ordering to choose between two. The connector pins Apache HttpClient instead.
- **Two latent defects.** A credentials builder stored session credentials and never read them, so `basicSessionCredentials(...)` had never had any effect. And shard listing sent `streamName` together with `nextToken`, which the API rejects on paginated calls.
- **One runtime-only failure.** The first test of the new decoder showed the protobuf version was too old for the KPL's generated code — a `NoClassDefFoundError` that compiles cleanly and appears only when a record is decoded. Nothing had tested that path before.

The release path needed fixing too. The old configuration targeted Sonatype's retired OSSRH, so it was already dead; publishing moved to the Central Portal under `io.github.technobasant`.

## Upgrading in place

The operational payoff is why porting beat any amount of tuning. **The offset JSON is byte-identical and the shard-commit layout is unchanged**, so a running query resumes its existing checkpoint across a Spark major version. The upgrade needed no write pause, no drain, no offset migration and no gap. The awslabs connector's offsets and committer layout are unreadable by this one, so staying on it would have meant a fresh checkpoint and a drain.

Two rules came with it:

- **Stop the old job before the new one starts.** Two queries writing one checkpoint directory corrupt it. With GitOps self-heal on, stopping a job is a git change.
- **`startingPosition` is read only when the checkpoint is empty.** That makes clearing a checkpoint the one action that actually loses data. Staging was the live example: its checkpoint was weeks older than the stream's 24-hour retention, so it had to be cleared and restarted from `LATEST`. Production checkpoints were current and resumed.

<div class="callout callout--note" markdown="1">
**Boundary.** *Measured on staging*, a sixteen-shard test stream with a one-minute trigger and low volume: the per-task reads, the 167 s stage and 174 s batch, the crash loop, and the 47 s tuned batch. *Measured in production*, in one region during the shadow run, and reported here only as ratios: the roughly 70% slowdown of the live job, the 40% rise in iterator age, the shadow's best batch at 2.5× the uncontended median, and the per-task read gap. The comparison that settled the read-model decision was validated against internal production traffic; those figures stay internal. *Inference*: that the port keeps the synchronous read profile, because it runs the same code path. The claim that the in-place upgrade lost nothing rests on the unchanged offset format and resumed sequence numbers, not on a separate record-level reconciliation. The cause of the slow dominant stage in the shadow remains unexplained.
</div>

## Frequently asked questions

### Why is the awslabs Kinesis connector for Spark slow when shards are idle?

It fetches on a background thread into a queue and decides a shard is exhausted only after a number of consecutive empty polls. With the defaults of two polls at five seconds each, every shard in every micro-batch waits about ten seconds even when it holds zero records. The lowest value the connector accepts is two polls of three seconds.

### Which Kinesis connector works with Spark 4 and AWS SDK v2?

Besides the awslabs connector, `io.github.technobasant:spark-sql-kinesis_2.13:1.3.0_spark-4.2.0` on Maven Central is a Spark 4.2, Scala 2.13, Java 17 build of the synchronous connector originally written by Qubole, ported to AWS SDK v2 with KCL removed. Each jar targets one Spark minor version, which is why the Spark version is part of the artifact version.

### Can a running Spark 3.4 streaming query move to the Spark 4 build without a new checkpoint?

Yes, for this connector. The port kept the offset JSON byte-identical and the shard-commit layout unchanged, so the query resumes its existing checkpoint. Stop the old job before the new one starts, because two queries writing one checkpoint directory corrupt it.

### How do you benchmark a new Kinesis consumer without contaminating production?

Do not run it beside the incumbent on the same stream. Per-shard read limits are shared by every shared-throughput consumer. Stop the incumbent, let the candidate run as the only reader, compare against the incumbent's own uncontended history, and watch throttling and iterator age as contamination detectors.

The maintenance story, decisions and known gaps are in [the connector's case study](/work/spark-sql-kinesis/), and the source, changelog and release notes are [on GitHub](https://github.com/technobasant/spark-sql-kinesis). More on ingestion under [Kafka & streaming](/writing/tags/kafka-streaming/), and the operating model behind this work is in [the data platform practice](/work/data-platform-practice/).
