---
title: "A lakehouse, and the RAG pipeline that runs on it"
hook: "The two halves of the thesis as one system: Trino and Iceberg underneath, retrieval and answers on top, both measured"
description: "A measured lab where a Trino/Iceberg lakehouse and a Delta-backed RAG pipeline share the same storage — credential vending proven scoped, a rollback performed, and grounding enforced at the retriever rather than the prompt."
date: 2024-01-27
last_modified_at: 2026-08-16
kind: lab
order: 6
featured: true
role: "Personal lab"
org: "Personal"
period: "2024 – 2026"
team: "One person"
scale: "One laptop: MinIO, Apache Polaris 1.7.0, Trino 483 (coordinator + worker), StarRocks 4.1.4, Spark 4.0.4 with Delta 4.0.0, Chroma, Ollama, Airflow 3.3.1 — every image native arm64"
problem: "This site claims I design data platforms and the agentic systems that run on them. The platform work and the AI work were evidenced separately, which proves each half and not the sentence. I wanted one rig where the same storage carries both, and where the claims about it are numbers rather than adjectives."
decision: "Rebuild two real client stacks on current versions rather than write about the originals, measure everything server-side, and publish the failures — including the ones where the tool reported success."
flow: rag
stack: [Trino, "Apache Iceberg", "Apache Polaris", StarRocks, "Apache Spark", "Delta Lake", dbt, Airflow, Chroma, Ollama, MinIO]
metrics: [lakehouse_partition_prune, lakehouse_rollback, rag_refusal]
tags: [iceberg-lakehouse, rag, distributed-databases]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
---

## Context

The two case studies above this one evidence the halves. `data-platform-practice` is the platform; `governed-ai-delivery` is the agentic layer. Both are professional work, both are real, and neither shows the thing the headline actually claims — that the second runs on the first.

So this is one rig where it does. A lakehouse underneath: object storage, an Iceberg REST catalog that decides who may touch a table, two query engines reading the same tables. A retrieval pipeline on top: the same storage refined through Delta, embedded, and served as answers that cite their sources.

Both halves were rebuilt from client projects — a January 2024 Trino/Iceberg build and a July 2025 RAG pipeline. Neither could be simply refreshed. The 2024 stack's catalog image is archived and its metastore is superseded; the 2025 stack's Spark image **no longer exists on Docker Hub at all**, and it required three hand-downloaded JARs that were absent from its own repository. That failure is in the write-ups because it is the more useful lesson: the stack did not break from a bad upgrade, it broke because a vendor changed its distribution model and `:latest` left nothing to fall back to.

## What it proves

**Storage that lends credentials instead of sharing them.** Trino holds no S3 key. It authenticates to Apache Polaris as an OAuth2 principal; Polaris checks a grant chain, calls STS, and returns a credential scoped to one table prefix. That is a claim, so it was tested rather than asserted:

```text
credential vended for bronze.orders
  own prefix                 ALLOW  84 objects
  sibling bronze.customers   DENY   AccessDenied
  whole warehouse bucket     DENY   AccessDenied
```

StarRocks was then attached to the same catalog with one DDL statement, no table definitions, and no S3 credentials of its own. The boundary is engine-independent, which is the actual argument for a REST catalog over a metastore — and the reason to test it before choosing one.

**A recovery that was performed, not described.** An unqualified `DELETE` removed 909,968 rows. `rollback_to_snapshot` returned all of them in 589 ms, because a rollback moves a pointer rather than data. Then `expire_snapshots` demonstrated where that safety net ends: the same time-travel read afterwards returns `Iceberg snapshot ID does not exists`. Retention is a recovery policy, not housekeeping.

**Grounding enforced at the retriever.** The RAG endpoint answers with the passages it used, or declines. Asked something outside its corpus, the nearest passage sat at cosine distance 0.923 against a 0.75 threshold — so the response carried a retrieve timing and **no generate timing at all**. The model was never called. A refusal that costs no inference is a threshold, not a prompt, and it is the cheapest safety property in the system.

## What it does not prove

It is a laptop. The query timings are honest ceilings for 8 CPUs and 11.67 GB, not production numbers, and the language model is a 1B running on CPU — chosen so that the pipeline around it is the subject rather than the model.

The engine comparison is narrower than it looks: StarRocks returned in 34 ms against Trino's 99 ms on one partition-pruned aggregate, which is close to the shape StarRocks is built for and says nothing about federation or large joins. The useful conclusion is not which is faster. It is that **the question can now be measured on the same tables without migrating anything**, which before a REST catalog meant a copy.

## The failure worth keeping

Three of the failures across this rig were reported as successes by the tool that caused them, and one propagated across three stores.

A charset guess in the scraper put a stray character on every section title. Fixing it changed the titles, which changed the `sha256(url::section)` chunk id — and every store downstream was upsert-only. Delta's `MERGE` inserts and updates; it never deletes a row the source stopped producing. Chroma's upsert behaves the same. So silver went from 170 rows to 323, gold inherited it, the vector store inherited it, and the retriever answered one question with both copies of the same passage at distances 0.2338 and 0.2350.

From the outside that reads as a model problem: repetitive answer, redundant citations. It is a pipeline problem three layers upstream, from a bug that had already been fixed at the source.

The operating rule it produced is the one I would take to a review: **the question to ask of a pipeline is not whether a re-run adds the right rows, it is whether it removes the wrong ones.** Bronze could. Nothing else could.

## Write-ups

Every figure here comes from a run, and each stage is documented step by step with the failures included:

- [The lakehouse spine]({{ '/writing/trino-iceberg-polaris-lakehouse-spine/' | relative_url }}) — Trino, Iceberg and Polaris, and proving the vended credentials are scoped
- [Bronze, silver, gold]({{ '/writing/dbt-trino-iceberg-medallion-airflow/' | relative_url }}) — dbt-trino and Airflow 3, and the partition spec dbt silently discards
- [Iceberg maintenance]({{ '/writing/iceberg-compaction-snapshots-rollback/' | relative_url }}) — compaction measured, and a rollback performed
- [Two engines, one catalog]({{ '/writing/starrocks-trino-one-iceberg-catalog/' | relative_url }}) — StarRocks beside Trino, neither holding a key
- [A RAG pipeline on a Delta lakehouse]({{ '/writing/rag-lakehouse-delta-spark-chroma/' | relative_url }}) — and the bug that survived being fixed
