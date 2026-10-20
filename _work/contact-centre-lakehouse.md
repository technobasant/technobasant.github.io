---
title: "An analytics lakehouse for a contact-centre platform, delivered end to end"
seo_title: "Consulting Case Study — Contact-Centre Analytics Lakehouse on S3, Trino and Airflow"
hook: "A client wanted a working analytics platform, not a design: storage, query engine, orchestration, catalog and API, configured and handed over with security, access control, HA and DR."
description: "Consulting case study: a contact-centre analytics lakehouse on S3, Trino and Airflow, with the catalog moved to AWS Glue, delivered configured with security, access control, HA and DR."
date: 2026-10-20
last_modified_at: 2026-10-20
kind: consulting
pillar: data-platforms
order: 1
role: "Consultant — data platform architecture and delivery"
org: "Consulting client"
team: "Remote, with the client's engineering lead"
scale: "Contact-centre interaction data, reported in the fixed intervals contact centres run on"
problem: "The client needed analytics on its contact-centre data and wanted the whole platform delivered working and configured, not as a design to implement later."
decision: "Keep the data in S3 and query it in place with Trino; compute interval statistics with Airflow; move the table catalog from a Hive Metastore to AWS Glue; serve results through an analytics API; and deliver every component configured, secured and recoverable."
stack: ["Amazon S3", Trino, "Apache Airflow", "AWS Glue Data Catalog", "Hive Metastore", Python, "REST API"]
tags: [iceberg-lakehouse, orchestration]
image: /assets/og/og-lakehouse.png
image_alt: "Consulting case study: a contact-centre analytics lakehouse — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Contact centres are managed in intervals: fixed windows of the day in which the business counts calls offered, answered and abandoned, and how long people waited and talked. A client building software for contact centres needed those statistics, and the history behind them, served through an API. It wanted the platform end to end, configured and working when the engagement ended, not a design to implement later.

## My role

I designed the platform and delivered it configured: storage, the query engine, orchestration, the table catalog and the API that served results, with the security, access control, high availability and disaster recovery around them.

## Architecture

- **Storage in S3.** Interaction data lands in object storage, in open file formats, where it can be kept for years at storage prices and read by more than one engine.
- **Trino as the query engine.** Trino reads the files where they are, so reporting did not need a copy in a warehouse; the table layout decides how much of them a query has to read.
- **Airflow for interval statistics.** Scheduled runs compute each interval's statistics once the interval has closed, so a report reads finished numbers rather than recomputing them on every request.
- **The catalog moved to AWS Glue.** Tables were registered in a Hive Metastore, which is one more service to run, back up and keep available. Moving the catalog to Glue made it a managed service with the rest of the AWS estate.
- **An analytics API.** Results are read through an API rather than by querying the engine directly, which keeps access control and query shapes in one place.

## What "delivered" meant

The difference between a design and a platform is the configuration nobody draws in a diagram. Every component was delivered configured and tuned, with:

- **Security and access control**: who and what may read each table, through which path, enforced at the catalog and the API rather than by convention.
- **High availability** for the services the product depends on, so one failed component does not stop reporting.
- **Disaster recovery**: a defined way back for the data and the catalog when something is lost or written wrongly, not just backups that have never been restored.
- **Optimisation** of the query engine and the table layout for the interval reports the product actually runs.

## Decisions

| Decision | Alternative | Why |
|---|---|---|
| Query the files in place with Trino | Load everything into a warehouse | The data was already in S3; a warehouse would have been another copy and another system to run and pay for |
| Precompute interval statistics with Airflow | Compute them in every query | Contact-centre reports read the same closed intervals many times; computing them once is cheaper and gives every reader the same number |
| AWS Glue as the catalog | Keep running the Hive Metastore | One less stateful service to operate, back up and keep available |
| Serve results through an API | Give consumers direct engine access | Access control and query shapes stay in one place, and the engine can change behind it |
| Hand over a configured platform | Hand over a design document | The client's team could run it from day one; nothing depended on interpreting a diagram |

## How it relates to the rest of my work

The same building blocks, Trino over files in object storage with a catalog in front, are measured on Iceberg tables in [lakehouse-lab](/work/lakehouse-rag-lab/), where a one-month predicate over 1.5 million Iceberg rows took {{ site.data.metrics.lakehouse_partition_prune.value }}, and the choice between query engines and stores is the subject of [the decision guide](/writing/choosing-where-the-data-lives/).

## Lessons that carry over

**A platform is its configuration.** The components were standard; what made it a platform the client could run was the access control, availability and recovery configured around them, which is the part a design document leaves out.

**Interval boundaries belong in the data's contract.** Interval edges and time zones are where contact-centre numbers quietly disagree between systems, so they are worth writing down as part of what the data promises, not discovering in a reconciliation.
