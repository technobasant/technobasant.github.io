---
title: "Two Postgres servers that ran out of room: an application database and a vector store, moved to Citus"
seo_title: "Consulting Case Study — Scaling PostgreSQL and pgvector Out with Citus"
hook: "One database outgrew its server's disk, memory and CPU; another could no longer insert, read or index its vector embeddings. Both moved to Citus, with the data model doing most of the work."
description: "Consulting case study: two single-server PostgreSQL databases, one relational and one of pgvector embeddings, moved to Citus with coordinator HA and an OLAP engine evaluation."
date: 2026-10-20
last_modified_at: 2026-10-20
kind: consulting
pillar: database-lifecycle
order: 1
role: "Consultant — database architecture and migration"
org: "Two consulting clients (confidential)"
team: "Remote, with each client's engineering team"
scale: "Single-server PostgreSQL databases at the limit of their hardware, one relational and one of vector embeddings"
problem: "A single PostgreSQL server per client had run out of headroom: one could not keep up with its tables and queries, the other with inserting, reading and indexing vector embeddings."
decision: "Move both to Citus, keeping PostgreSQL and its extensions: distribute by the key the queries filter on, co-locate what joins, make the coordinator highly available, and choose columnar or heap storage per table by its workload."
stack: [PostgreSQL, Citus, pgvector, HNSW, repmgr, HAProxy, ClickHouse, "Apache Pinot", StarRocks, Trino]
tags: [distributed-databases, postgres, rag]
image: /assets/og/og-postgres.png
image_alt: "Consulting case study: PostgreSQL and pgvector moved to Citus — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Two clients came with the same problem in different clothes.

**An application database.** One PostgreSQL server held the product's data, and it was running out of everything at once: disk, memory and CPU. Queries and tables took longer every month, and the trend made the business's own growth the risk. A bigger server would have bought time, not a way out.

**A vector store.** The other kept vector embeddings in PostgreSQL with pgvector, next to the data they described. Embeddings grew quickly, and one server stopped coping: it could not keep up with the inserts or the reads, and building the vector index took longer and longer, failed more often than not, and performed poorly when it did finish.

## My role

On both engagements I designed the move and carried it out with the client's team: the distribution model, the cluster and the migration. On the first I also made the coordinator highly available and evaluated analytical engines for the reporting that was outgrowing the database. The clients, their data and their code stay private; this page describes the problems and the decisions.

## Why Citus for both

Both workloads were PostgreSQL, used its extensions and its tools, and had a key most queries filtered on. Citus keeps all of that and spreads tables across worker nodes, so the database grows by adding workers rather than by buying a larger server, and the application keeps speaking PostgreSQL. A different engine would have meant rewriting the application's queries and, for the vector store, moving embeddings away from the rows they describe.

## The design

| Decision | Alternative | Why |
|---|---|---|
| Distribute by the key most queries filter on | Distribute by the primary key of each table | A query for one tenant runs on one shard instead of all of them |
| Co-locate tables that join, on the same key | Distribute each table independently | Joins stay on one worker; repartitioning joins across the network is the slow path |
| Small shared tables as reference tables | Distribute them too | Copied to every worker, they join locally |
| A standby for the coordinator, managed by repmgr, with HAProxy in front | A single coordinator | The coordinator routes every query; without a standby it is the cluster's single point of failure |
| Columnar or heap storage per table, by workload | One storage format for everything | Columnar for read-heavy scans of mostly appended data; heap for write-heavy tables with updates |
| For vectors, shard the embeddings and build the index per shard | Keep one ever-larger index on one server | Each shard builds and searches a smaller index, and the workers share inserts, reads and builds |
| Evaluate ClickHouse, Apache Pinot, StarRocks and Trino for analytics | Keep analytics on the application database | Reporting at scale is a scan workload; the application database's job is the application |

## Measured behind the decisions

The client systems' figures stay with the clients. The behaviours the decisions rely on are measured in labs anyone can re-run:

- In [distributed-db-lab](/work/distributed-db-lab/), a co-located join ran {{ site.data.metrics.ddb_colocation_join.value }} faster than one that had to repartition, a worker joined and 7 shard groups moved under load with {{ site.data.metrics.ddb_rebalance_errors.value }}, and the spread between the largest and smallest worker narrowed, {{ site.data.metrics.ddb_skew_spread.value }}.
- In [retrieval-bench](/work/retrieval-bench/), pgvector matched exact search as closely as Qdrant and OpenSearch, and the trap that matters for any vector store showed up clearly: a post-filtered HNSW search at 10% selectivity returned {{ site.data.metrics.retrieval_filter_rows.value }} rows until pgvector's iterative scan restored recall to {{ site.data.metrics.retrieval_iterative_scan.value }}.

## Lessons that carry over

**The data model is the scaling plan.** A Citus cluster with the wrong distribution key is a slower PostgreSQL. Choosing the key, the co-location groups and the reference tables is most of the work, and it is done before any node is added.

**Plan the coordinator's failure on day one.** A distributed cluster with a single coordinator has moved the single point of failure, not removed it.

**Vectors are data, with the same growth curve.** Embeddings grow with the content they describe, and their index is the expensive part; giving them the same scale-out path as the rest of the data kept them next to it.

The wider choice, when to stay on one managed PostgreSQL, when to shard, and when a different store fits, is in [the decision guide](/writing/choosing-where-the-data-lives/).
