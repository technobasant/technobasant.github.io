---
title: About
last_modified_at: 2026-11-10
seo_title: "About Basant Bhattarai — Data & AI Architect · Senior Data Engineer"
eyebrow: Profile
headline: "I lead the architecture of data and AI platforms end to end, and I build what I design."
hero_code: "OPERATE / OWN"
page_class: page-about
permalink: /about/
description: "About Basant Bhattarai: Senior Data Engineer at UXCam, practising as a Data & AI Architect. 9+ years in industry; governance, SOC 2, AI built in."
lede: "9+ years in industry, nearly 7 full-time: from backend services and PostgreSQL schemas to the architecture of the whole platform, its governance, and the AI built into it."
---

I work as a data and AI architect: I set the target architecture, choose platforms by measuring them on the workload, design the data model and the controls around it, and lead the build through to the people who will run it. My title is Senior Data Engineer at UXCam, and the job is exactly that, on a platform handling {{ site.data.metrics.professional_event_volume.value }} events a day. Projects I have delivered and written up include [an analytics lakehouse](/work/contact-centre-lakehouse/) handed over configured and running, [two Postgres databases moved to Citus](/work/postgres-scale-out-citus/), [a managed-or-self-run decision and an RDS fleet](/work/postgres-on-rds/), and [a failing classifier rebuilt](/work/consulting-short-text-and-alerting/) on a Databricks lakehouse. The architecture work I can show in full is [a reference architecture](/work/data-platform-architecture/) for a B2B SaaS company leaving Postgres, a scenario common across the industry: the current state measured, 18 decisions, a data model, SOC 2 readiness and a proof of concept on Databricks.

The job arrived in a particular order. First Python services and PostgreSQL schemas; then the databases those services leaned on, which is where I learned that most outages are a storage decision made two years earlier; then the platform around them — Kafka ingestion, Spark processing, Airflow orchestration, lakehouse modelling, analytical serving.

Agents came last and belong to the same stack. The interesting part was never the orchestration framework. It was the boundary: what a model is allowed to write, what validates it, what happens on the second attempt, and how you compare today's answer to last week's. I work close to system internals — throughput and failure limits, recovery paths, observability, and cost before scale turns an architectural shortcut into an operational one.

Architecture ties the data platform and the agents together, and it is most of what I am asked to review: where state lives, which operations are idempotent, what a second delivery does, and how a system degrades when a dependency is slow. I write those down as decisions next to the alternative I rejected, so the next person can disagree with a reason rather than a hunch. The same habit shows up outside the day job — in [a connector I maintain in the open](/work/spark-sql-kinesis/), in the projects above, and in [the reference architecture's 18 decision records](https://github.com/technobasant/data-platform-architecture/tree/main/decisions).


## Operating principles

<ol class="principle-list is-wide">
  <li><h3>Ownership before consumption</h3><p>Every published dataset needs a freshness expectation and a named owner before it gets a consumer. An unowned table rarely fails loudly; it keeps serving yesterday's numbers until somebody makes a decision with them.</p></li>
  <li><h3>Choose technology with an exit</h3><p>I look at operating cost, data portability, and recovery work before I look at a feature matrix. A tool earns its place when the team understands both how to run it and how to leave it.</p></li>
  <li><h3>Agents produce records, not theatre</h3><p>A chat transcript cannot be joined, audited, backfilled, or compared with last week's decision. If a model produces something worth acting on, it crosses a schema and validation boundary like any other producer.</p></li>
  <li><h3>Narrow contracts beat wide promises</h3><p>Much of data-quality work is downstream cleanup caused by an upstream table promising more than it can hold. I would rather publish three columns with guarantees I can defend than a wide table everyone quietly stops trusting.</p></li>
</ol>

## What I am doing now

At UXCam I own the architecture of the data platform and the stores underneath it: processing, serving, database reliability, governance and the SOC 2 controls for the platform and its infrastructure, and the architecture review every new store, pipeline and agent workflow passes before production. I also own the production agent workflows — LangGraph and Google ADK for orchestration, MCP for the tool surface — with the same requirement as any other producer: what they emit lands in the governed stores, typed and reviewable, or it does not land.

Outside that I maintain [spark-sql-kinesis](https://github.com/technobasant/spark-sql-kinesis), a Kinesis source and sink for Spark 4, and publish reference systems with their method and measurements in the repository: LLM evaluation, a governed agent, filtered vector retrieval, real-time ML, exactly-once streaming, data contracts, progressive delivery and sharded databases. They are [on the work page](/work/), alongside a multi-engine failover lab with restartable scenarios, published commands and measured outcomes, and two reference architectures: [a SaaS company leaving Postgres](/work/data-platform-architecture/) and [the usage assistant on its governed data](/work/ai-platform-architecture/).

*Updated {{ site.data.availability.updated | date: "%B %Y" }}.*

## Background

I studied computer science and engineering at SVCET, an autonomous college affiliated to JNTU Anantapur, in India, from 2015 to 2019. In the final two years I worked part-time as a backend developer, in Python with Flask and Django, and led a final-year research project: a deep-learning dialogue system, a TensorFlow sequence-to-sequence model behind a Flask interface. The data half of the job gradually became the job. I speak English at C1 and Nepali natively.

I work from Kathmandu, remotely with teams in the US and Europe; UXCam itself is based in California and Berlin. I shift my day later to overlap with European afternoons and US mornings, a rhythm I have used for years.

I'm open to Senior or Lead Data Engineer, AI Engineer and Data & AI Architect roles, long-term contract or full-time, and to consulting engagements. [Scope and availability are here](/hire/).

## Write to me

Name, email, and a paragraph. Consulting, contract and job enquiries belong on [the hire page](/hire/#hire-form).

{% include hire-form.html variant="contact" id="about-contact" %}

## Elsewhere

[GitHub](https://github.com/technobasant) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [Email](mailto:contact@basantbhattarai.com.np) · [Résumé](/resume/)
