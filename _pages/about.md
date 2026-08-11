---
title: About
eyebrow: Profile
permalink: /about/
description: "Basant Bhattarai — how I work on data platforms and the AI layer above them, what I am building now, and the timezone I do it from in Kathmandu."
---

I build data platforms, and the AI layer that sits on top of them. At UXCam I own one product's ingestion, storage, serving and governance — Kafka into Spark on self-managed Kubernetes, an Iceberg lakehouse underneath, query engines in front, and a multi-agent analytics platform above all of it. The part of the work I actually like is the part most people skip: deciding what a dataset promises, writing that promise down where a consumer can read it, and being the person paged when it stops being true.

## How I work

**Every dataset gets a freshness objective and a named owner before it gets a consumer.** An unowned table does not fail loudly. It keeps serving yesterday's numbers until somebody makes a decision on them, which makes it an outage with a delay fuse. If nobody will own a dataset, I would rather not publish it.

**Open-source first, and I will take the operational work over a bill I cannot walk away from.** I have migrated off a platform once. The expensive part was never the license — it was re-deriving semantics that lived only inside somebody else's product. Managed services earn their place where the data model stays mine and the exit stays cheap, which is why Databricks sits beside self-managed Spark in my stack rather than replacing it.

**An agent's output is not a product until it lands in a typed table.** A chat transcript cannot be joined, audited, backfilled or diffed against last week. If a model produces something worth acting on, it passes through a schema and a validator like any other producer, and it gets rejected the same way when it fails.

**The cheapest correctness mechanism is a narrower contract.** Most data-quality work I have seen is downstream cleanup that exists because an upstream table promised more than it could hold. I would rather ship three columns with a guarantee I can defend than a wide table everyone quietly stops trusting.

**I publish the method next to the number.** Every figure on this site carries how it was measured, because a percentage without a denominator is a decoration. If I cannot name the counter, the query or the billing line behind a claim, I do not make the claim.

## What I'm doing now

I own the data platform and the App Analytics Agent Platform at UXCam, which currently means more time on retrieval quality and agent evaluation than on batch throughput.

I am writing up a failover lab: six database engines, eight scenarios, measured on a rig I can restart rather than quoted from a documentation page.

Outside work I build ClickHomes, a real-estate platform, largely as an excuse to own a dual OLTP/OLAP schema end to end without a committee.

*Updated {{ site.data.availability.updated | date: "%B %Y" }}.*

## Background

I am from Kathmandu and still live here. I studied computer science at JNTUA College of Engineering in Anantapur, India, from 2015 to 2019, and spent my first two working years on backend services before the data half of the job took over completely. I speak English at C1 and Nepali natively. Nepal sits at UTC+5:45, a 45-minute offset that no scheduling tool has ever handled gracefully, so my working day is deliberately shifted late — it covers US business hours and European afternoons, and it means almost every colleague I have had was several thousand kilometers and several hours away.

I take one or two consulting engagements at a time; what that involves, and what I decline, is on [Work with me](/hire/).

## Elsewhere

[GitHub](https://github.com/technobasant) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [Email](mailto:{{ site.author.email }}) · [Résumé](/resume/)
