---
title: About
eyebrow: Profile
headline: "I build systems that stay trustworthy after the demo."
hero_code: "OPERATE / OWN"
page_class: page-about
permalink: /about/
description: "Nine years across backend engineering, data platforms, database reliability, and governed AI systems — plus the principles I use to operate them."
---

I am a Senior Data & AI Engineer based in Kathmandu, Nepal. Over {{ site.data.metrics.experience.value }}, my work has moved from Python backend services and PostgreSQL schemas to the harder seams between data, databases, APIs, and AI-assisted products. I care about the part after a successful demo: what the system promises, how we know it is keeping that promise, and how another engineer repairs it safely.


## Operating principles

<ol class="principle-list is-wide">
  <li><h3>Ownership before consumption</h3><p>Every published dataset needs a freshness expectation and a named owner before it gets a consumer. An unowned table rarely fails loudly; it keeps serving yesterday's numbers until somebody makes a decision with them.</p></li>
  <li><h3>Choose technology with an exit</h3><p>I look at operating cost, data portability, and recovery work before I look at a feature matrix. A tool earns its place when the team understands both how to run it and how to leave it.</p></li>
  <li><h3>Agents produce records, not theatre</h3><p>A chat transcript cannot be joined, audited, backfilled, or compared with last week's decision. If a model produces something worth acting on, it crosses a schema and validation boundary like any other producer.</p></li>
  <li><h3>Narrow contracts beat wide promises</h3><p>Much of data-quality work is downstream cleanup caused by an upstream table promising more than it can hold. I would rather publish three columns with guarantees I can defend than a wide table everyone quietly stops trusting.</p></li>
</ol>

## What I am doing now

At UXCam I work on production data and AI systems, with the weight on reliability, governance, database serving and evaluation.

Outside that I keep a multi-engine failover lab with restartable scenarios, published commands and measured outcomes, and I build an independent product where I own every layer from the schema to the deployment.

*Updated {{ site.data.availability.updated | date: "%B %Y" }}.*

## Background

I studied computer science at JNTUA College of Engineering in Anantapur, India, from 2015 to 2019. My first roles centered on backend services; the data half of the job gradually became the job. I speak English at C1 and Nepali natively.

I work from Kathmandu and shift my day later to overlap with European afternoons and US mornings, a rhythm I have used with distributed teams for years.

For occasional focused advisory or implementation work, [consulting scope and availability are here](/hire/).

## Elsewhere

[GitHub](https://github.com/technobasant) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [Email](mailto:{{ site.author.email }}) · [Résumé](/resume/)
