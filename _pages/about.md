---
title: About
eyebrow: Profile
headline: "I build systems that stay trustworthy after the demo."
hero_code: "OPERATE / OWN"
page_class: page-about
permalink: /about/
description: "Nine years across backend engineering, production data platforms, database reliability, and governed AI systems — plus the principles I use to operate them."
---

I am a Senior Data & AI Engineer in Kathmandu. Over nine years I have moved from Python backend services and PostgreSQL schemas to owning production data infrastructure end to end: ingestion, transformation, lakehouse storage, database serving, reliability, governance, and the AI products built on top. At UXCam that means Kafka into Spark on self-managed Kubernetes, Iceberg underneath, Trino and ClickHouse in front, and a multi-agent analytics platform above it. The part of the work I value most is the part many teams postpone: defining what a dataset promises, making that promise observable, and being accountable when it stops being true.

## How I work

<ol class="principle-list is-wide">
  <li><h3>Ownership before consumption</h3><p>Every dataset gets a freshness objective and a named owner before it gets a consumer. An unowned table does not fail loudly; it keeps serving yesterday's numbers until somebody makes a decision on them. If nobody will own a dataset, I would rather not publish it.</p></li>
  <li><h3>Open-source, with an exit</h3><p>I will take operational work over a bill I cannot walk away from. Managed services earn their place where the data model stays mine and the exit stays cheap, which is why Databricks sits beside self-managed Spark rather than replacing it.</p></li>
  <li><h3>Agents produce records, not theatre</h3><p>A chat transcript cannot be joined, audited, backfilled, or diffed against last week. If a model produces something worth acting on, it passes through a schema and validator like any other producer—and gets rejected the same way when it fails.</p></li>
  <li><h3>Narrow contracts beat wide promises</h3><p>Most data-quality work is downstream cleanup caused by an upstream table promising more than it can hold. I would rather ship three columns with a guarantee I can defend than a wide table everyone quietly stops trusting.</p></li>
  <li><h3>The method belongs beside the number</h3><p>Every figure on this site carries how it was measured. If I cannot name the counter, query, or billing line behind a claim, I do not make the claim.</p></li>
</ol>

## What I'm doing now

I own the data platform and the App Analytics Agent Platform at UXCam, which currently means more time on retrieval quality, agent evaluation, database serving, and governance than on raw batch throughput.

I am writing up a failover lab: six database engines, eight scenarios, measured on a rig I can restart rather than quoted from a documentation page.

Outside work I am the founder and sole engineer behind ClickHomes, a real-estate data and AI platform with PostgreSQL for operational truth, ClickHouse for analytical speed, a mandatory RESO transformation boundary, and more than 90 versioned SQL migrations.

*Updated {{ site.data.availability.updated | date: "%B %Y" }}.*

## Background

I am from Kathmandu and still live here. I studied computer science at JNTUA College of Engineering in Anantapur, India, from 2015 to 2019, and spent my first two working years on backend services before the data half of the job took over completely. I speak English at C1 and Nepali natively. Nepal sits at UTC+5:45, a 45-minute offset that no scheduling tool has ever handled gracefully, so my working day is deliberately shifted late — it covers US business hours and European afternoons, and it means almost every colleague I have had was several thousand kilometers and several hours away.

I take one or two consulting engagements at a time; what that involves, and what I decline, is on [Work with me](/hire/).

## Elsewhere

[GitHub](https://github.com/technobasant) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [Email](mailto:{{ site.author.email }}) · [Résumé](/resume/)
