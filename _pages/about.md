---
title: About
seo_title: "About Basant Bhattarai — Big Data & Agentic AI Engineer"
eyebrow: Profile
headline: "I architect big data platforms and agentic AI systems for production."
hero_code: "OPERATE / OWN"
page_class: page-about
permalink: /about/
description: "About Basant Bhattarai: a Senior Data & AI Engineer specializing in Spark pipelines, lakehouse platforms, distributed systems, and production AI agents."
lede: "From Kafka ingestion and Spark processing to Iceberg storage, analytical serving, and governed AI agents, I design the full lifecycle for scale, resilience, and cost."
---

I am a Senior Data & AI Engineer based in Kathmandu, Nepal. Over {{ site.data.metrics.experience.value }}, my work has moved from Python backend services to high-volume Kafka ingestion, Spark/PySpark processing, Airflow orchestration, lakehouse modeling, distributed analytical serving, and production agentic AI. I work close to system internals: finding throughput and reliability limits, designing for recovery, integrating security and observability, and controlling cost before scale turns an architectural weakness into an operational problem.


## Operating principles

<ol class="principle-list is-wide">
  <li><h3>Ownership before consumption</h3><p>Every published dataset needs a freshness expectation and a named owner before it gets a consumer. An unowned table rarely fails loudly; it keeps serving yesterday's numbers until somebody makes a decision with them.</p></li>
  <li><h3>Choose technology with an exit</h3><p>I look at operating cost, data portability, and recovery work before I look at a feature matrix. A tool earns its place when the team understands both how to run it and how to leave it.</p></li>
  <li><h3>Agents produce records, not theatre</h3><p>A chat transcript cannot be joined, audited, backfilled, or compared with last week's decision. If a model produces something worth acting on, it crosses a schema and validation boundary like any other producer.</p></li>
  <li><h3>Narrow contracts beat wide promises</h3><p>Much of data-quality work is downstream cleanup caused by an upstream table promising more than it can hold. I would rather publish three columns with guarantees I can defend than a wide table everyone quietly stops trusting.</p></li>
</ol>

## What I am doing now

At UXCam I work across production big-data pipelines and AI systems, with the weight on Spark processing, platform reliability, governance, analytical serving, agent evaluation, and operational readiness.

Outside that I keep a multi-engine failover lab with restartable scenarios, published commands and measured outcomes, and I build an independent product where I own every layer from the schema to the deployment.

*Updated {{ site.data.availability.updated | date: "%B %Y" }}.*

## Background

I studied computer science at JNTUA College of Engineering in Anantapur, India, from 2015 to 2019. My first roles centered on backend services; the data half of the job gradually became the job. I speak English at C1 and Nepali natively.

I work from Kathmandu and shift my day later to overlap with European afternoons and US mornings, a rhythm I have used with distributed teams for years.

For occasional focused advisory or implementation work, [consulting scope and availability are here](/hire/).

## Elsewhere

[GitHub](https://github.com/technobasant) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [Email](mailto:{{ site.author.email }}) · [Résumé](/resume/)
