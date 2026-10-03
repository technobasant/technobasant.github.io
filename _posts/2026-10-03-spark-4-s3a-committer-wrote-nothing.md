---
title: "The Spark 4 upgrade that succeeded and wrote nothing"
seo_title: "Spark 4 on hadoop-aws 3.5: the S3A committer that wrote nothing"
description: "Spark 4.2 on hadoop-aws 3.5 read 9,029 records and wrote zero objects, and no task failed. Why the S3A committer was bypassed, and the tests that now catch it."
date: 2026-10-03 07:00:00 +0545
last_modified_at: 2026-10-03
type: essay
series: production-notes
series_order: 1
tags:
  - spark
  - data-quality
toc: true
featured: true
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - S3A committers
  - Apache Spark 4 upgrade
  - silent data loss
mentions:
  - Apache Hadoop
  - AWS SDK for Java v2
  - Amazon S3
  - Kubernetes
cover:
  base: "/assets/images/editorial-spark-committer-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic: task output under Spark's default commit protocol bypasses the S3A committer and leaves pending uploads, while PathOutputCommitProtocol routes it through the magic committer to a landed object"
  caption: "A green batch is a claim. An object in the bucket and a pending-upload count back at zero are the evidence."
faq:
  - q: "Why does Spark 4 with hadoop-aws 3.5 report successful batches but write no files to S3?"
    a: "If an S3A committer is configured but spark.sql.sources.commitProtocolClass is left at Spark's default, HadoopMapReduceCommitProtocol only honours a FileOutputCommitter's work path. S3A committers are not FileOutputCommitters, so task output bypasses them. On hadoop-aws 3.3.4 S3A completed those writes itself; on 3.5.0 in cluster mode they stayed as multipart uploads nothing ever completed."
  - q: "Do I need PathOutputCommitProtocol to use the S3A magic committer from Spark?"
    a: "Yes. Set spark.sql.sources.commitProtocolClass to org.apache.spark.internal.io.cloud.PathOutputCommitProtocol, which ships in the separate spark-hadoop-cloud artifact. It routes task output through the committer. It also refuses dynamic partition overwrite, so jobs that need that must stay on FileOutputCommitter."
  - q: "Should fs.s3a.committer.abort.pending.uploads be true or false?"
    a: "False if more than one job writes under the same destination at once, because the default aborts every pending upload under the destination when a job commits. The cost is that nothing reclaims a failed job's uploads, so add a bucket lifecycle rule for incomplete multipart uploads and, if you need it sooner, an age-gated, prefix-scoped reaper."
  - q: "Why are Spark executors OOMKilled after moving to AWS SDK v2, with no heap dump?"
    a: "SDK v2's Netty client buffers off-heap, while SDK v1 buffered on the heap. A pod sized with the default 10% memoryOverhead can run out of off-heap room. The kernel kills the container with exit 137, which is not a JVM OutOfMemoryError, so HeapDumpOnOutOfMemoryError never fires. Give memoryOverhead an explicit budget."
key_takeaways:
  - "Under Spark's default commit protocol an S3A committer is bypassed; on hadoop-aws 3.5 in cluster mode those writes stayed pending and never became objects."
  - "Nothing failed: batches succeeded, stage counters reported rows, and the only commit log line was one healthy production printed on every batch."
  - "Landed objects and a multipart-upload count that returns to zero are the signals that matter; exit codes and row counters are not."
  - "Concurrent writers need abort.pending.uploads=false, so something with an age gate and a prefix scope has to reclaim failed jobs' uploads."
  - "Test the preconditions that make a configuration mean something. The original test asserted the very setting that caused the incident."
---

A Spark 4.2 streaming job on staging read 9,029 records from Kinesis, reported every micro-batch as successful, and wrote nothing. No task failed. No batch failed. The stage counters said 25 rows had been written. The only log line about the commit was one the healthy Spark 3.4 production jobs had been printing on every batch for years.

What it left behind was 65 incomplete multipart uploads at the final table paths. They were invisible to `aws s3 ls`, still there a day later, and billed as storage the whole time. Nothing in the job's own telemetry told that apart from a quiet hour.

**Operating rule.** After any Spark or Hadoop upgrade that touches the S3 write path, a green batch is not evidence of output. The evidence is objects that landed and a multipart-upload count that returns to zero. Everything that reports success from inside the job — exit codes, batch status, row counters — can be true while nothing becomes visible.

This is how the Spark 3.4.1 → 4.2.0 upgrade on the streaming analytics platform I work on lost data quietly in more than one place, and what now stops each of them. Hadoop 3.3.4 became 3.5.0 and AWS SDK v1 became v2 in the same move.

## Two writers that want opposite committers

The pipeline has two kinds of writer, and they want opposite things from an output committer.

Streaming jobs read Kinesis, route records to tables, and write ORC on a five-minute trigger. Several of them, plus a debug job, write into the same Hive table path at the same time. Concurrent writers to one destination is a first-class pattern here, not an accident.

Binning, the compaction job, rewrites whole partitions with `partitionOverwriteMode=dynamic`. It runs one writer per table, and it needs dynamic partition overwrite, which no S3A committer supports.

So the design rule is: streaming gets an S3A committer, binning gets `FileOutputCommitter`, and the two never share a commit protocol. The upgrade broke the first half of that rule twice. The first time was loud.

## The loud failure came first

Midway through the upgrade both job types were unified onto `FileOutputCommitter`. It stages task output under `<output>/_temporary`, a name hardcoded in Hadoop and therefore inside the table path, and `cleanupJob` deletes that tree recursively on every job commit. With two writers on one table, one job's commit deletes the other's in-flight output. Production said so within minutes:

```text
FileNotFoundException: .../_temporary/0/_temporary/attempt_.../part-....orc
  at S3AFileSystem.initiateRename ... FileOutputCommitter.mergePaths ... commitTask
```

A different partition failed on each retry; after four strikes the query terminated. That is the good kind of failure. It stops the job and names the file.

The worse version appeared when I reproduced it on purpose against real S3. A slow writer committing 600 rows across 120 partitions raced a fast writer committing eight times into the same dummy table path. With the S3A committer, 600 of 600 slow rows and 8 of 8 fast rows landed. With `FileOutputCommitter` (algorithm version 2), 566 of 600 landed. Thirty-four rows were gone and nothing failed anywhere: the losing task logs `No Output found` and commits successfully.

Two details made that test worth trusting. The first version wrote 50 rows per job; commits finished in under a second, the writers never overlapped, and `FileOutputCommitter` passed cleanly. The commit window has to be wide enough to overlap, the way a five-minute job commits alongside a one-minute one in production. And the test watches S3 for `<table>/_temporary` while the write runs, so it proves which committer actually ran instead of assuming it.

The fix looked obvious: restore what streaming had used on Spark 3.4 for years, the S3A partitioned committer selected through the s3a committer factory. That restoration is where the silent failure came from.

## The committer that was never called

The restored configuration set the factory and left `spark.sql.sources.commitProtocolClass` at Spark's default. This is the branch in that default protocol that decides where a task writes its file:

```scala
// org.apache.spark.internal.io.HadoopMapReduceCommitProtocol.newTaskTempFile (abridged)
val stagingDir: Path = committer match {
  case _ if dynamicPartitionOverwrite => this.stagingDir
  case f: FileOutputCommitter =>
    new Path(Option(f.getWorkPath).map(_.toString).getOrElse(path))
  case _ => new Path(path)   // every S3A committer lands here
}
```

Every S3A committer extends `PathOutputCommitter`, not `FileOutputCommitter`, so it takes the last branch. The task writes straight to the final table path, the committer's task commit finds nothing staged, and it logs:

```text
Task committer attempt_...: No pending uploads to commit
```

On hadoop-aws 3.3.4, S3A completed those direct writes itself. The committer was a no-op and the output landed anyway, which is why this exact configuration ran in production for years while printing that line on every batch. On hadoop-aws 3.5.0, in cluster mode, the same writes stayed as pending multipart uploads that nothing ever completed. Spark's commit code is byte-identical between v3.4.1 and v4.2.0; the behaviour changed underneath it.

| Signal | What it said | What was true |
| --- | --- | --- |
| Batch and task status | Succeeded | Zero objects written |
| Stage output-row counter | 25 rows | The rows never existed in S3 |
| Commit log line | `No pending uploads to commit` | Printed by healthy jobs too, including on empty batches |
| `aws s3 ls` on the table | Nothing new | Pending uploads are not listed |
| `list-multipart-uploads` | 65 in progress | The only truthful signal |

The local suite had passed 600 of 600 with the same configuration. It runs `local[4]`, so driver and executor share one JVM, and in that shape S3A completed the writes even with the committer bypassed. A green laptop run sat next to a cluster deployment that wrote nothing.

One more hadoop-aws change makes the trap easier to walk into. While writing a later test I found that `fs.s3a.committer.name` resolves to `magic` by default on hadoop-aws 3.5.0, where it was `file` on 3.3.4. Point the s3a factory at `S3ACommitterFactory`, forget the protocol, and you silently get a magic committer that is never called.

## The fix: four settings that only work together

The fix gives the committer the data. Each of these keys is load-bearing, and any one of them alone is either a silent no-write or a concurrency hazard:

```properties
spark.sql.sources.commitProtocolClass=org.apache.spark.internal.io.cloud.PathOutputCommitProtocol
spark.hadoop.mapreduce.outputcommitter.factory.scheme.s3a=org.apache.hadoop.fs.s3a.commit.S3ACommitterFactory
spark.hadoop.fs.s3a.committer.name=magic
spark.hadoop.fs.s3a.committer.magic.enabled=true
spark.hadoop.fs.s3a.committer.abort.pending.uploads=false
spark.hadoop.mapreduce.fileoutputcommitter.marksuccessfuljobs=false
```
{: data-file="streaming commit settings" }

| Setting | What breaks without it |
| --- | --- |
| `commitProtocolClass = PathOutputCommitProtocol` | Task output bypasses the committer; on hadoop-aws 3.5 the uploads are abandoned |
| s3a factory `= S3ACommitterFactory` | No S3A committer is constructed at all |
| `committer.name = magic` | The staging committers hand `.pendingset` files from executors to the driver through a shared filesystem, which a cluster-mode split can break |
| `abort.pending.uploads = false` | The first job to commit aborts every other job's in-flight uploads under the same destination |

Magic keeps both the pending data and its metadata in S3, under `<dest>/__magic_job-<jobId>/`. I checked the property the architecture depends on against the hadoop-aws 3.5.0 source rather than assuming it. The magic path prefix is job-scoped (`__magic_job-`), and `cleanupStagingDirs` deletes only that job's magic path, not the whole `__magic` tree. A committing job cannot reach a sibling's uploads the way `_temporary` cleanup did.

The `abort.pending.uploads` line is Hadoop's own advice. The comment on the key says to change it "if more than one committer is writing to the same destination tree simultaneously; otherwise the first job to complete will cancel all outstanding uploads from the others." The [S3A committers documentation](https://hadoop.apache.org/docs/stable/hadoop-aws/tools/hadoop-aws/committers.html) and Spark's [cloud integration guide](https://spark.apache.org/docs/latest/cloud-integration.html) cover the protocol binding. If you write Parquet rather than ORC, the guide also asks for its binding Parquet committer.

Two constraints come with the protocol. `PathOutputCommitProtocol` ships in `spark-hadoop-cloud`, a separate artifact from `spark-sql`, so a Spark bump or a slimmer base image can drop it while the configuration stays intact. And it refuses dynamic partition overwrite, which is exactly why binning must never inherit it. Code review found a legacy single-partition binning entry point that did inherit the streaming committer. It was not deployed, but it was documented as the way to re-bin by hand.

## What abort.pending.uploads=false leaves behind

Turning off the abort has a price: nothing reclaims a failed job's uploads. S3A won't, because the abort is disabled. The committer's cleanup is job-scoped and runs only on a clean path. Pod death doesn't help, because the garbage is in S3, not on disk. And streaming is designed to fail and retry on spot capacity, with a retry budget of thousands of restarts, so failed jobs are routine.

The 65 orphans from the broken staging window were the proof: about an hour of bad writes, still pending a day later. They also cost a diagnostic. A climbing pending-upload count is the best detector of the silent no-write failure. If the baseline is permanently non-zero and drifting, that signal is dead, and S3A's per-commit warning (`N active upload(s) in progress … failed jobs are not being cleaned up`) becomes noise. That noise invites someone to fix it by setting the abort back to `true`, which silences the warning and reintroduces cross-job destruction.

So a small reaper runs as a daemon thread on the driver. Its safety comes from construction, not timing:

- **Age gate: seven days.** Batches finish in seconds and commits in minutes, so nothing that old belongs to a live job. Exactly seven days is not reapable; the boundary is exclusive.
- **Prefix scope.** Only under the job's own data path. The bucket is shared, and the built-in `fs.s3a.multipart.purge` is bucket-wide.
- **Driver only, every six hours.** No stampede of executors on the S3 API at startup.
- **Never fails a batch.** Every throwable is caught and logged. A reaper that can break ingestion is worse than the garbage.
- **Idempotent and bounded.** Overlapping prefixes are harmless, and at most 500 aborts run per sweep so a backlog drains over several passes.

The unit suite passed 53 tests, with 6 cancelled because they are gated on real S3 and Kinesis. The gated real-S3 spec passed 3 of 3. A seven-day sweep against a seconds-old upload aborted none. The abort path aborted 2 of 2 throwaway uploads. Sweeping one prefix aborted 1 and left a sibling prefix untouched. Across every run the 65 genuine orphans stayed at 65, because they were one day old, not seven.

The first version of that spec used a zero-day gate and failed. S3 reports an upload's `Initiated` time from the server clock at one-second granularity, and the sweep compares it with the local clock, so ordinary skew makes a fresh upload look zero or negative in age. The spec now uses a negative gate and says why. The run that failed also leaked two uploads of its own, which I aborted by hand. In-process cleanup dies with the process. The reaper complements a bucket `AbortIncompleteMultipartUpload` lifecycle rule; it doesn't replace one.

The same review found the reaper's predecessor. Every micro-batch, the driver ran a blanket recursive delete of `fs.s3a.buffer.dir` on a shared mount that executors were writing upload blocks into. It was safe only because `foreachBatch` is synchronous; a straggling or retried task would have lost its block mid-upload. I briefly moved the buffer to pod-local disk, then moved it back, because an existing age-gated cleanup job running in a separate pod already owned that mount and the move put the buffer out of its reach. The per-batch delete stayed deleted. Garbage collection belongs to something that can prove the garbage is dead.

<div class="callout callout--gotcha" markdown="1">
**The reaper had a bug of its own.** It built a short-lived S3 client every six hours and closed it. In AWS SDK v2, closing a client also closes the credentials provider you passed in. That took down the process-wide credential chain at the next refresh, so streaming crashed a predictable 6 h 49 m to 6 h 59 m after driver start: the six-hour interval plus whatever was left of the credential cache's hour. The fix was a delegate around the shared chain whose `close()` does nothing, so no short-lived client can shut down a provider it does not own.
</div>

## The memory that moved off-heap

The next failure after the committer was memory. Executors were OOMKilled, and each kill took the whole query down with `A shuffle map stage with indeterminate output was failed and retried`. Measured just before the change, one executor sat at 7,658 Mi against a 7,700 Mi limit while idle at 1m CPU, 42 Mi from the kill.

The total was fine. The split was the problem:

| | Before | After |
| --- | --- | --- |
| Heap (`memory`) | 7,000 Mi | 5,500 Mi |
| `memoryOverhead` | unset → 10% default = 700 Mi | 2,048 Mi |
| Pod limit | 7,700 Mi | 7,548 Mi |
| `ReservedCodeCacheSize` | 512 Mi | 256 Mi |
| Left for metaspace, Netty direct buffers, GC and ORC/ZSTD native buffers | ~188 Mi | ~1,792 Mi |

Ninety-one percent of the pod went to the heap, and the code cache reservation ate most of what remained. That had held on Spark 3.4 because AWS SDK v1 buffers on the heap. SDK v2's Netty client buffers off-heap, and the S3 analytics accelerator and the magic committer's pending-upload state live there too. The off-heap budget hadn't changed, but much more now lived in it.

The kill was exit 137 from the cgroup, not a JVM `OutOfMemoryError`. That is why `-XX:+HeapDumpOnOutOfMemoryError` never produced a dump for any of them. With the new split, a genuine heap shortfall fails as a JVM OOM with a heap dump, which you can diagnose; a silent 137 you can't.

```yaml
executor:
  memory: 5500m            # was 7000m
  memoryOverhead: "2048"   # was unset, so Spark applied 0.1 x 7000 = 700Mi
  javaOptions: >-
    -XX:+UseZGC -XX:+ExitOnOutOfMemoryError -XX:+HeapDumpOnOutOfMemoryError
    -XX:ReservedCodeCacheSize=256M
```
{: data-file="SparkApplication executor spec (abridged)" }

The same manifest carried `spark.executor.memory: 6g` in `sparkConf`, and it was inert. The Spark operator renders `spec.executor.memory` into that key and wins. The proof was the pod limit itself: 7,700 Mi is 7,000 plus 10%, where 6g would have produced 6,758 Mi. A third number on the page that never takes effect is how the next person sizes the pod wrong, so it was removed.

This change stops the OOMKills, which were what kept triggering the failure. It does not make executor loss survivable. A spot reclaim still aborts a query whose plan is indeterminate, with no OOM involved, and that needs a fix in the job itself.

The silent pattern showed up once more, in binning. A colleague traced tasks that hung for 2.5 hours or more, while healthy tasks in the same stage finished in 0.2 to 3.5 minutes. The cause was a deadlock in the S3 Analytics Accelerator, which hadoop-aws 3.5 selects as the default input stream. Pinning `fs.s3a.input.stream.type=classic` fixed it. The shape was the same as before: the executor kept heartbeating, no task failed, and the stage simply never ended.

## Test the preconditions, not the values

The test suite had an assertion named "streaming leaves commitProtocolClass at Spark's default." It encoded the configuration that caused the incident, and it passed. A config-equality test can't catch this class of bug, because the configuration was correct by its own lights. What was wrong was a precondition the configuration silently depended on.

The suite now guards the silent failure modes directly:

- `PathOutputCommitProtocol` must be loadable with the constructor Spark calls reflectively, because it lives in a separate artifact that an image change can drop.
- Streaming must never resolve to Spark's default protocol — the precise regression.
- All four load-bearing keys must be present, each asserted with its consequence in the failure message. A future simplification has to delete a named claim, not quietly drop a line.
- Streaming and binning must never share a commit protocol, and every binning entry point, including the legacy one, must resolve to `FileOutputCommitter`.
- Streaming must carry no staging-committer-only settings. They are inert under magic and imply a handoff that isn't happening, and that false mental model made this incident harder to diagnose.
- At startup, each job re-reads the effective values after `getOrCreate` and refuses to start if anything overrode them.
{: .checklist }

The startup check had a trap of its own. Hadoop's `Configuration.get()` expands `${...}` references, so an expression-valued setting such as a buffer directory can never equal its effective reading. A naive verify would have rejected the configuration it pins, and every streaming job would have refused to start. It compares expression-valued keys unexpanded and separately checks that the expansion happened.

In the cluster, I watch three things: objects landed per batch, the multipart-upload count under the job's prefix trending back to zero, and S3A's `active upload(s) in progress` warning. None of them is a batch status.

<div class="callout callout--note" markdown="1">
**Boundary.** The 9,029-read, 0-written, 65-pending figures and the 25-row counter come from the staging deployment before the fix. The 600/600 versus 566/600 race is from a gated test against a real S3 dummy table path, run from a laptop in `local[4]`. The 7,658 Mi reading and the before/after memory split come from the production executor spec and the pod's measured usage just before the change; the "left over" row is arithmetic on those settings. The reaper's results come from its unit and real-S3 specs; no upload had been reaped at the real seven-day threshold when it shipped, and pagination past the 500-abort cap is unexercised. I have not traced exactly which hadoop-aws 3.5 change turns a bypassed direct write into a pending upload across the cluster process boundary while a single JVM still completes it. The fix removes the bypass, so it doesn't depend on that answer. The analytics-accelerator deadlock was a colleague's diagnosis, not mine.
</div>

## Frequently asked questions

### Why does Spark 4 with hadoop-aws 3.5 report successful batches but write no files to S3?

If an S3A committer is configured but `spark.sql.sources.commitProtocolClass` is left at Spark's default, `HadoopMapReduceCommitProtocol` only honours a `FileOutputCommitter`'s work path. S3A committers are not `FileOutputCommitter`s, so task output bypasses them. On hadoop-aws 3.3.4 S3A completed those writes itself; on 3.5.0 in cluster mode they stayed as multipart uploads nothing ever completed.

### Do I need PathOutputCommitProtocol to use the S3A magic committer from Spark?

Yes. Set `spark.sql.sources.commitProtocolClass` to `org.apache.spark.internal.io.cloud.PathOutputCommitProtocol`, which ships in the separate `spark-hadoop-cloud` artifact. It routes task output through the committer. It also refuses dynamic partition overwrite, so jobs that need that must stay on `FileOutputCommitter`.

### Should fs.s3a.committer.abort.pending.uploads be true or false?

False if more than one job writes under the same destination at once, because the default aborts every pending upload under the destination when a job commits. The cost is that nothing reclaims a failed job's uploads. Add a bucket lifecycle rule for incomplete multipart uploads and, if you need it sooner, an age-gated, prefix-scoped reaper.

### Why are Spark executors OOMKilled after moving to AWS SDK v2, with no heap dump?

SDK v2's Netty client buffers off-heap, while SDK v1 buffered on the heap. A pod sized with the default 10% `memoryOverhead` can run out of off-heap room. The kernel kills the container with exit 137, which is not a JVM `OutOfMemoryError`, so `HeapDumpOnOutOfMemoryError` never fires. Give `memoryOverhead` an explicit budget.

The same upgrade also changed how fast the streaming connector reads, which became its own measurement exercise: [the idle floor and a benchmark I had to retract](/writing/spark-4-kinesis-connector-idle-floor/). More on [Apache Spark](/writing/tags/spark/) and [data quality](/writing/tags/data-quality/), and how this fits [the data platform practice](/work/data-platform-practice/).
