---
title: About
last_modified_at: 2026-10-20
seo_title: "About Basant Bhattarai — Data & AI Architect · Senior Data Engineer"
eyebrow: Profile
headline: "I design data platforms, the governance around them and the AI on them, then build them."
hero_code: "OPERATE / OWN"
page_class: page-about
permalink: /about/
description: "About Basant Bhattarai: data and AI architect, Senior Data Engineer at UXCam. Platform architecture, databases, governance and SOC 2 readiness, and AI on governed data."
lede: "Nine years that started with backend services and PostgreSQL schemas, and ended up owning the platforms, the databases underneath them, and the agents that write into both."
---

I work as a data and AI architect, and I still build what I design. My title is Senior Data Engineer at UXCam, where I own the reliability and governance of the data platform, operate the databases under it, design the production agent workflows, and am responsible for meeting the SOC 2 criteria for the platform and its infrastructure. I also take consulting engagements: [an analytics lakehouse](/work/contact-centre-lakehouse/) delivered configured and running, [two Postgres databases moved to Citus](/work/postgres-scale-out-citus/), [a managed-or-self-run decision and an RDS fleet](/work/postgres-on-rds/), and [a classifier redesigned](/work/consulting-short-text-and-alerting/) for a client's Databricks lakehouse. The architecture work I can show in full is [a reference architecture](/work/data-platform-architecture/) for a B2B SaaS company leaving Postgres, a scenario common across the industry: the current state measured, 18 decisions, a data model, SOC 2 readiness and a proof of concept on Databricks.

The job arrived in a particular order. First Python services and PostgreSQL schemas; then the databases those services leaned on, which is where I learned that most outages are a storage decision made two years earlier; then the platform around them — Kafka ingestion, Spark processing, Airflow orchestration, lakehouse modeling, analytical serving.

Agents came last and belong to the same stack. The interesting part was never the orchestration framework. It was the boundary: what a model is allowed to write, what validates it, what happens on the second attempt, and how you compare today's answer to last week's. I work close to system internals — throughput and failure limits, recovery paths, observability, and cost before scale turns an architectural shortcut into an operational one.

Architecture is what ties the two together, and it is most of what I am asked to review: where state lives, which operations are idempotent, what a second delivery does, and how a system degrades when a dependency is slow. I write those down as decisions next to the alternative I rejected, so the next person can disagree with a reason rather than a hunch. The same habit shows up outside the day job — in [a connector I maintain in the open](/work/spark-sql-kinesis/), in consulting work, and in [the reference architecture's 18 decision records](https://github.com/technobasant/data-platform-architecture/tree/main/decisions).


## Operating principles

<ol class="principle-list is-wide">
  <li><h3>Ownership before consumption</h3><p>Every published dataset needs a freshness expectation and a named owner before it gets a consumer. An unowned table rarely fails loudly; it keeps serving yesterday's numbers until somebody makes a decision with them.</p></li>
  <li><h3>Choose technology with an exit</h3><p>I look at operating cost, data portability, and recovery work before I look at a feature matrix. A tool earns its place when the team understands both how to run it and how to leave it.</p></li>
  <li><h3>Agents produce records, not theatre</h3><p>A chat transcript cannot be joined, audited, backfilled, or compared with last week's decision. If a model produces something worth acting on, it crosses a schema and validation boundary like any other producer.</p></li>
  <li><h3>Narrow contracts beat wide promises</h3><p>Much of data-quality work is downstream cleanup caused by an upstream table promising more than it can hold. I would rather publish three columns with guarantees I can defend than a wide table everyone quietly stops trusting.</p></li>
</ol>

## What I am doing now

At UXCam I work across the data platform and the stores underneath it: processing, serving, database reliability, governance and the SOC 2 controls for the platform and its infrastructure, and architecture review. I also own the production agent workflows — LangGraph and Google ADK for orchestration, MCP for the tool surface — with the same requirement as any other producer: what they emit lands in the governed stores, typed and reviewable, or it does not land.

Outside that I maintain [spark-sql-kinesis](https://github.com/technobasant/spark-sql-kinesis), a Kinesis source for Spark 4, and publish reference systems with their method and measurements in the repository: LLM evaluation, a governed agent, filtered vector retrieval, real-time ML, exactly-once streaming, data contracts, progressive delivery and sharded databases. They are [on the work page](/work/), alongside a multi-engine failover lab with restartable scenarios, published commands and measured outcomes, and two reference architectures: [a SaaS company leaving Postgres](/work/data-platform-architecture/) and [the usage assistant on its governed data](/work/ai-platform-architecture/).

*Updated {{ site.data.availability.updated | date: "%B %Y" }}.*

## Background

I studied computer science at JNTUA College of Engineering in Anantapur, India, from 2015 to 2019. My first roles centered on backend services; the data half of the job gradually became the job. I speak English at C1 and Nepali natively.

I shift my day later to overlap with European afternoons and US mornings, a rhythm I have used with distributed teams for years.

For occasional focused advisory or implementation work, [consulting scope and availability are here](/hire/).

## Write to me

Name, email, and a paragraph. Consulting briefings belong on [the hire page](/hire/#hire-form).

{% include hire-form.html variant="contact" id="about-contact" %}

## Elsewhere

[GitHub](https://github.com/technobasant) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [Email](mailto:contact@basantbhattarai.com.np) · [Résumé](/resume/)
