---
title: "retrieval-bench: three vector engines, one set of vectors"
seo_title: "retrieval-bench — pgvector vs Qdrant vs OpenSearch, measured on the same embeddings"
hook: "Is Postgres enough, and is hybrid search worth it? One embedding pass, three engines under the same limits, and numbers that flatter none of them"
description: "pgvector, Qdrant and OpenSearch measured on the same 381,559 vectors: retrieval quality, latency, filters, build cost, concurrency and writes under load."
date: 2026-10-14
last_modified_at: 2026-10-14
kind: lab
order: 7
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "381,559 vectors × 384 dimensions; PostgreSQL 18 with pgvector, Qdrant and OpenSearch, each in its own container with 4 CPUs and 5 GiB"
problem: "Every RAG system meets the same early question — do we need a vector database, or is Postgres enough, and do we need hybrid search at all? Vendor benchmarks answer it for their own engine. I wanted the answer on public data, with pinned versions, measuring the trade-offs that actually decide a production choice."
decision: "Embed once and load identical vectors into every engine, compute exact ground truth, compare engines at equal recall rather than equal settings, and publish the runs that flatter nobody — including my own measurement mistakes."
repo: "https://github.com/technobasant/retrieval-bench"
metrics: [retrieval_filter_rows, retrieval_filter_middle, retrieval_iterative_scan, retrieval_engine_quality]
stack: [pgvector, "PostgreSQL 18", Qdrant, OpenSearch, Faiss, Python, numpy, "sentence-transformers", Docker]
tags: [rag, postgres]
image: /assets/og/og-databases.png
image_alt: "retrieval-bench — pgvector, Qdrant and OpenSearch measured on the same vectors"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

The question behind this repository is one every RAG system meets early, and one I kept answering from other people's benchmarks: is Postgres with pgvector enough, or does retrieval need a dedicated vector database — and does hybrid search earn its complexity? Vendor benchmarks measure their own engine on their own terms. Public comparisons usually change two things at once, the engine and the embeddings, so a gap in quality could be either.

[retrieval-bench](https://github.com/technobasant/retrieval-bench) holds everything else fixed. One embedding pass, one set of float32 vectors, loaded unchanged into PostgreSQL 18 with pgvector 0.8.7, Qdrant 1.19.2 and OpenSearch 3.9.0. Every number it publishes is in [MEASUREMENTS.md](https://github.com/technobasant/retrieval-bench/blob/main/MEASUREMENTS.md), drawn from JSON results the repository commits.

## Constraints

Public data with licences I could check at the source, not at a mirror: SciFact, ArguAna and Touché 2020 on args.me, all under CC BY 4.0 (SciFact's abstracts under ODC-By), credited in the repository's NOTICE. NFCorpus and NQ were left out because their original licences could not be confirmed, and MS MARCO because it is non-commercial.

The engines run on one host, each in its own container capped at 4 CPUs and 5 GiB, and only the engine under test runs while anything is timed. There is no network between client and database, so latency is client-observed with each engine's round-trip floor published beside it (0.15 to 0.28 ms). Everything fits in memory; quantisation, on-disk indexes and multi-node deployments are outside this run.

## Architecture

A small Python harness, `rbench`, downloads the BEIR datasets, embeds each corpus once with `bge-small-en-v1.5` at a pinned revision, and computes exact nearest neighbours in numpy — with any filter applied — as ground truth. Each engine is one adapter class behind a common protocol: build from scratch, search with an `ef_search` or `probes` setting and an optional filter, insert, report sizes. The same runner drives quality runs against human relevance judgements, recall–latency sweeps, filtered search, concurrency from 1 to 16 client processes, and inserts while querying. `make smoke` pushes synthetic data through every adapter in CI.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Embed once, load the same arrays everywhere | Let each engine's integration embed | A quality gap between engines is then an index gap, not a model gap | Nothing engine-specific, such as built-in quantisation, is exercised |
| Compare at equal recall (each engine's smallest `ef_search` reaching 0.95) | Compare at equal settings | The same `ef_search` bought recall from 0.82 to 0.90 across engines | Operating points must be re-derived whenever a version changes |
| Exact ground truth over the rows that pass a filter | Relevance judgements only | Isolates what the index loses from what the model gets wrong | Filtered runs measure recall, not answer relevance |
| A synthetic hash filter at 50%, 10% and 1% | A real metadata field | A field correlated with content would measure the data, not the engine | Real tenant and date filters behave differently and are not measured |
| Hold out 986 near-duplicates of the query set | Use the corpus as published | 98.5% of queries had a near-copy in the index, inflating recall | The ANN corpus differs from the quality corpus by those rows |
| Refuse to time anything off mains power | Trust the operator | A battery run was several times slower and had to be discarded | Timed runs need the machine plugged in, checked before and after |

## Results

On the same vectors, the three engines differed from exact search by {{ site.data.metrics.retrieval_engine_quality.value }} nDCG@10 on all three datasets, and at recall@10 ≈ 0.97 their median latencies differed by 0.13 ms. Choosing between them on quality or single-query speed would be choosing on noise. What separated them was everything around the query:

| Question | Measured |
|---|---|
| What does a selective filter do? | Post-filtered pgvector HNSW returned {{ site.data.metrics.retrieval_filter_rows.value }} rows at 10% selectivity, as fast as a full answer. OpenSearch's efficient filter returned ten rows with recall {{ site.data.metrics.retrieval_filter_middle.value }}. pgvector's `relaxed_order` iterative scan restored recall to {{ site.data.metrics.retrieval_iterative_scan.value }} |
| How far does it scale on 4 CPUs? | Peak at 8 clients: Qdrant 5,643 QPS, OpenSearch 4,920, pgvector HNSW 4,483; IVFFlat tops out at 732 |
| What happens while rows are written? | pgvector inserts 639 rows/s with query latency unchanged; Qdrant ingests 25× faster, and its median rose from 0.66 to 2.30 ms until its optimiser finished 86 s later |
| Is hybrid search worth it? | As a hedge: +1.3 nDCG@10 on SciFact, +7.3 on Touché, −2.2 on ArguAna. A larger embedding model gained more than fusion where both were measured |
| Can Postgres do the keyword half? | Not with built-in full-text: the best variant trailed BM25 by 8 to 23 points, and hybrid built on it scored below vector search alone on all three datasets |
| What does it cost to hold? | pgvector stores every vector twice, table and index; OpenSearch's container used 3.7 GiB including a fixed 2 GiB heap |
{: aria-label="retrieval-bench results, from MEASUREMENTS.md" }

The filtered results are the ones that changed what I would ship, and they are written up in [Filtered vector search returned four rows instead of ten](/writing/filtered-vector-search-four-rows-not-ten/).

## What went wrong

The repository keeps a failure log, because each failure changed the design.

**The first sweep was too good.** pgvector reached recall@10 of 0.965 at `ef_search = 10` on 382,000 vectors. ArguAna and args.me both scraped the same debate site, so 98.5% of the queries already had a near-identical document in the index. Holding those 986 rows out dropped a query's median similarity to its nearest document from 0.988 to 0.861, in line with Touché's own topics.

**A warm-up was not a warm-up.** One setting's throughput rose from 459 to 703 QPS over three passes after a 50-query warm-up. Every point now gets a full warm-up pass and five timed passes interleaved across the sweep.

**The machine was on battery.** A rerun came back several times slower — p50 5.65 ms against 1.26 — because macOS had switched on Low Power Mode. The harness now refuses to start a timed run off mains power and records the power state in every result.

**Postgres full-text found nothing.** `websearch_to_tsquery` ANDs every term, so 274 of 300 SciFact claims matched no document, and the `ts_rank_cd` ranker most examples use halved the score even with ORed terms.

## What I'd do differently

**Use a filter that correlates with content.** The hash filter is the cleanest test of an index and the least like production. A tenant or date field, where the passing rows cluster, is the next run, because it can make a graph walk better or worse and I do not know which.

**Test significance.** Quality differences are reported without significance tests, and Touché's 49 topics make its column noisy. Differences of a few thousandths of nDCG@10 should carry an interval, not a ranking.

**Measure what larger corpora need.** Quantisation, on-disk indexes, updates and deletes under load, and multi-node deployments all change the picture past the size where everything fits in memory, and none of them are in this run.
