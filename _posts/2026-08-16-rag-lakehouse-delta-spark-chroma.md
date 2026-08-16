---
title: "A RAG pipeline on a Delta lakehouse, and the bug that survived being fixed"
description: "Scrape to bronze, silver, gold on Spark 4 and Delta, embed into Chroma, and serve answers that cite their sources or decline to answer."
date: 2026-08-16 08:00:00 +0545
last_modified_at: 2026-08-16
type: tutorial
tags: [rag, iceberg-lakehouse]
toc: true
cover:
  base: "/assets/images/editorial-rag-lakehouse-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Diagram: bronze, silver and gold Delta tables feeding embeddings, with one question answered and cited at distance 0.234 and another refused at 0.923"
  caption: "Two questions, two outcomes. The refusal cost no inference at all, which is the cheapest safety property in the system."
featured: true
level: intermediate
time_estimate: "~1 h, most of it pulling images and the first Ivy resolution"
what_youll_build: "A scrape-to-RAG lakehouse on Spark 4 and Delta: raw JSONL to bronze, silver and gold on MinIO, embeddings in Chroma, and a FastAPI endpoint that cites its sources or says it does not know."
prerequisites:
  - "Docker with about 8 GB available to containers, and roughly 6 GB of disk"
  - "No GPU and no API key: embeddings run on CPU and the model is a local 1B"
  - "Comfort reading a docker-compose file and a PySpark job"
tested_on: "macOS Darwin 25 · arm64 host · Docker Desktop 8 CPU / 11.67 GB · Spark 4.0.4 · Delta 4.0.0 · MinIO RELEASE.2025-09-07 · Chroma 1.5.9 · Ollama 0.12.11 with llama3.2:1b · all images native arm64"
key_takeaways:
  - "`bitnami/spark` no longer exists on Docker Hub, and `bitnamilegacy/spark` publishes only sha256 tags — a 2025 compose file will not start in 2026."
  - "delta-spark and Spark are pinned minor to minor: 4.0.0 works against Spark 4.0.4, while 4.1.0 and 4.3.1 resolve cleanly then fail at class load."
  - "The `spark` user in `apache/spark` has no home directory, so spark-submit dies writing to `/nonexistent/.ivy2` before resolving a single package."
  - "A refusal that costs no inference is the cheapest safety property here — the retriever rejected an out-of-corpus question at distance 0.923 without calling the model."
  - "Fixing an encoding bug at the source changed a natural key and orphaned rows in three downstream stores, because every one of them was upsert-only."
---

## What this is

A small end-to-end system: scrape a bounded set of pages, land them in object storage, refine them through bronze, silver and gold Delta tables on Spark, embed the result, and serve answers that cite the passages they came from — or decline.

I built the first version in July 2025. Coming back to it in 2026, the most useful thing about it was not that it worked; it was **why it had stopped**.

## Step 0 — Why a 2025 compose file does not start in 2026

Three reasons, and the first is not a version problem.

```text
bitnami/spark:3.5                  GONE
marquezproject/marquez:latest      pulls
chromadb/chroma:latest             pulls
```

**`bitnami/spark` is gone.** Broadcom moved the Bitnami catalog behind a paid tier during 2025. A `bitnamilegacy` namespace survives, but it publishes **only sha256 digests** — there is no `3.5`, nothing you can write in a compose file and read six months later.

**Nine images were pinned to `:latest`.** Which means the stack that ran in July 2025 is not recoverable, and no assertion about it is checkable. That is the actual cost of `:latest`, and it is not a style preference.

**Three JAR files, roughly 270 MB, had to be downloaded by hand** — `aws-java-sdk-bundle`, `hadoop-aws`, `hadoop-common` — and they were in neither the repository nor my own working copy. The public repo failed on first run for everyone who cloned it, including me. They were also the AWS SDK v1 S3A stack, which Spark 4 has moved past regardless.

<div class="callout callout--gotcha" markdown="1">
**A vendor's free tier is a dependency.** The image was pinned, the tag was specific, and it still evaporated. When a base image comes from a commercial vendor's community edition, the supported exit is worth knowing before you need it — here it was the official `apache/spark`, which also publishes arm64.
</div>

## Step 1 — Spark and Delta, with nothing downloaded by hand

```yaml
  spark-master:
    image: apache/spark:4.0.4-scala2.13-java17-python3-r-ubuntu
    command: /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master
    volumes:
      - ./spark:/opt/spark-lab:ro
      - ./jobs:/opt/jobs:ro
      - ivy_cache:/tmp/ivy
```
{: data-file="docker-compose.yaml"}

The `jars/` directory is gone entirely. Spark resolves S3A and Delta from Maven at submit time:

```bash
exec /opt/spark/bin/spark-submit \
  --master "${SPARK_MASTER:-spark://spark-master:7077}" \
  --conf spark.jars.ivy="${IVY_DIR:-/tmp/ivy}" \
  --packages "io.delta:delta-spark_2.13:${DELTA_VERSION},org.apache.hadoop:hadoop-aws:${HADOOP_AWS_VERSION}" \
  --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
  --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
  --conf spark.hadoop.fs.s3a.endpoint="${S3_ENDPOINT}" \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  "$@"
```
{: data-file="spark/submit.sh"}

Two things in there are load-bearing and neither is obvious.

<div class="callout callout--gotcha" markdown="1">
**`spark.jars.ivy` is not optional on `apache/spark`.** The `spark` user has no home directory, so spark-submit dies before resolving anything:

```text
java.io.FileNotFoundException: /nonexistent/.ivy2.5.2/cache/resolved-org.apache.spark-…xml
```

Bitnami's image set a home; the official one does not. This is the single most likely thing to bite anyone migrating off Bitnami.
</div>

**Delta and Spark are pinned to each other, minor by minor.** Same Spark, three Delta versions:

| `delta-spark_2.13` | Spark 4.0.4 | result |
| --- | --- | --- |
| 4.3.1 (latest) | ✗ | `NoSuchMethodError: ParserInterface.$init$` |
| 4.1.0 | ✗ | same |
| **4.0.0** | ✓ | 50,000 rows written |

All three resolve from Maven without a murmur. Maven has no idea which Spark you are running, so a wrong pairing is a class-load failure on the first DataFrame call, several seconds after everything looked fine. **"Use the latest" is the wrong instinct here. Matching is.**

<div class="callout callout--gotcha" markdown="1">
**One from the container runtime rather than Spark.** Mounting `./jobs` at `/opt/spark-lab/jobs` while `/opt/spark-lab` was itself a `:ro` mount left both Spark containers stuck in `Created` with **no logs at all** — the failure happens before any process starts, so there is nothing to read and `docker compose logs` returns empty. Use separate mount points.
</div>

**Verify.** `spark: 4.0.4`, `rows_written: 50000`, and a `_delta_log/` prefix in the bucket.
{: .verify}

## Step 2 — Scraping is not a Spark job

```python
def allowed(url: str) -> bool:
    """Ask robots.txt per host, not once at the start."""
    parts = urllib.parse.urlsplit(url)
    rp = robotparser.RobotFileParser()
    rp.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return False   # unreadable robots.txt is a no, not a yes
    return rp.can_fetch(UA, url)
```
{: data-file="ingest/scrape.py"}

Scraping is IO-bound and rate-limited by politeness. Putting it on the cluster buys nothing and makes the robots check harder to follow. It runs in a small Python container and lands append-only JSONL.

Chunking is by `<h2>`/`<h3>` section rather than by page or by character count. A whole reference page is far too much context for one embedding; a fixed character window cuts sentences in half. A section is roughly one idea, which is the unit a question is usually about.

**Verify.** `landed s3://lakehouse/raw/scrape/…jsonl sections=187 skipped=0 bytes=882663`.
{: .verify}

## Step 3 — Bronze, silver, gold, and what each layer owes you

```python
# bronze: pure function of the raw prefix, overwritten each run
raw = spark.read.json(f"{BUCKET}/raw/scrape/")
bronze = raw.withColumn("ingested_at", F.current_timestamp()) \
            .withColumn("text_len", F.length("text"))
bronze.write.format("delta").mode("overwrite").save(f"{BUCKET}/bronze/sections")
```
{: data-file="jobs/etl.py"}

| layer | rows | what it owes you |
| --- | --- | --- |
| bronze | 187 | every raw record, typed and stamped, nothing dropped |
| silver | 170 | cleaned and deduplicated on `(url, section)` |
| gold | 170 | a deterministic `chunk_id`, the text, and enough provenance to cite |

<div class="callout callout--gotcha" markdown="1">
**Read the directory, not a glob.** `raw/scrape/*.jsonl` returns the right rows *and* throws `FileNotFoundException: No such file or directory` into the log on the way past — S3A resolves the glob by listing, and the miss surfaces as an exception the job then recovers from. A stack trace in a successful run trains you to ignore stack traces.
</div>

## Step 4 — Embeddings, and why the id is a hash

`chunk_id` is `sha256(url :: section)` truncated to 16 characters. That makes it stable across runs, so re-running the pipeline **updates** a vector instead of inserting a second copy beside it.

```text
read      170 chunks from delta in 0.21s
embed     170 chunks in 2.62s (64.8/s, dim=384, model load 7.42s)
upsert    170 vectors in 0.25s
```

Reading Delta here uses the Rust `deltalake` reader, not PySpark. Embedding 170 rows does not need a cluster, and a 400 MB JVM image to read a small table is the kind of default that makes a stack feel heavier than its problem.

## Step 5 — An answer that can be checked, or no answer

```python
kept = [(d, m, s) for d, m, s in zip(docs, metas, dists) if s <= MAX_DISTANCE]
if not kept:
    return {"answer": "I don't know.", "grounded": False,
            "nearest_distance": round(min(dists), 4), "sources": []}
```
{: data-file="rag/api.py"}

Three questions against a corpus of Python standard-library documentation:

| question | grounded | evidence |
| --- | --- | --- |
| read and write JSON in Python | yes | cites the `json` sections |
| difference between a list and a tuple | yes | `Tuples` d=0.234, `Lists` d=0.356 |
| **capital city of Nepal** | **no** | nearest passage d=0.923, above the 0.75 threshold |

The third is the one worth building for. The response carried a `retrieve` timing and **no `generate` timing at all** — the model was never called. Nothing in the corpus was close enough, so there was nothing to be fluent about.

That ordering matters. A retriever that hands four irrelevant passages to a model and asks it to be careful is asking the wrong component to hold the line. **A refusal that costs no inference is the cheapest safety property in the system**, and it is a threshold rather than a prompt.

**Verify.** An out-of-corpus question returns `grounded: false`, a `nearest_distance` above your threshold, and no generate timing.
{: .verify}

## Step 6 — The bug that survived being fixed

This is the part I would keep if I could keep only one.

Every section title came back with a stray `Â` welded to the pilcrow — `requests` had guessed the charset from headers that did not commit to one. The fix is one line: hand BeautifulSoup `r.content` instead of `r.text` and let it sniff the meta charset.

That fixed the scrape. It fixed nothing downstream.

`chunk_id` is a hash of `(url, section)`. Changing the title changed the identity of every chunk — and every store in the chain is upsert-only:

| store | rows after the "fix" | why |
| --- | --- | --- |
| bronze — Delta, overwrite | 187, correct | rewritten from raw every run |
| silver — Delta, MERGE | **323** | MERGE inserts and updates. It never deletes a row the source stopped producing. |
| gold — Delta, overwrite | 323 | derived from a silver that was already wrong |
| Chroma — upsert | **323** | same shape, same outcome |

Then the retriever answered a question with both copies:

```text
src: 'Tuples'   dist 0.2338
src: 'TuplesÂ'  dist 0.2350
```

Two near-identical passages competing for the same context window, from a bug that had already been fixed at the source. From the outside this reads as a model problem — the answer is repetitive, the citations are redundant. It is a pipeline problem, three layers upstream.

The lesson is not "handle encodings". It is that **a natural key derived from scraped content is not stable**, and an upsert-only layer has no way to forget. A merge that is meant to converge on its source needs a delete clause for rows the source no longer produces, or the layer needs a periodic full rebuild. I added the rebuild:

```python
if os.environ.get("REBUILD", "").lower() in ("1", "true", "yes"):
    client.delete_collection("sections")
```
{: data-file="rag/embed.py"}

## Measured

| stage | figure |
| --- | --- |
| scrape | 187 sections, 10 pages, 883 KB |
| bronze → silver | 187 → 170 (17 duplicates removed) |
| embed | 170 chunks in 2.6 s — 64.8/s, 384 dimensions |
| upsert | 0.16 s |
| retrieve | 45–58 ms |
| generate | 20–34 s, llama3.2:1b on CPU |

The generate figure is honest and unflattering: a 1B model on CPU. That is deliberate — the subject here is the pipeline around the model, and a larger model would make every run slower while changing none of the properties being tested.

## Failure modes

| Symptom | Cause | Repair |
| --- | --- | --- |
| `bitnami/spark:3.5` not found | image moved to a paid catalog | use `apache/spark` |
| `/nonexistent/.ivy2` FileNotFoundException | `spark` user has no home | set `spark.jars.ivy` |
| `NoSuchMethodError: ParserInterface.$init$` | Delta/Spark minor mismatch | match Delta to Spark, not to latest |
| Containers stuck in `Created`, no logs | volume mounted inside a `:ro` mount | separate mount points |
| `FileNotFoundException` in a successful job | S3A glob listing | read the directory |
| Duplicate near-identical citations | upsert-only stores, changed key | full rebuild, or a delete clause |

## Clean up and operating consequence

```bash
docker compose --profile tools down -v
```

Two rules came out of this.

**Pin everything, and know your exit from every vendor image.** The stack did not break because of a bad upgrade. It broke because a company changed its distribution model and `:latest` meant there was nothing to fall back to.

**Ask which of your stores can forget.** Every layer here could accept new data and none could drop stale data, which is fine until a key changes — and keys derived from source content change more often than anyone plans for. The question to ask of a pipeline is not "does a re-run add the right rows", it is "does a re-run *remove* the wrong ones". Bronze could. Nothing else could.

Lineage is the obvious next piece: the original had Marquez wired in, and an OpenLineage graph would have shown the orphaned rows propagating across three stores in one picture rather than three separate counts.
