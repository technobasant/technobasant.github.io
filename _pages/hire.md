---
title: Work with me
seo_title: "Big Data Platform & Agentic AI Consulting — Basant Bhattarai"
eyebrow: Consulting
headline: "Bring me the big data pipeline or AI agent system that must scale reliably."
hero_code: "SCOPE / DECIDE"
page_class: page-hire
permalink: /hire/
description: "Senior consulting on Spark pipelines, lakehouse platforms, distributed data systems, and governed agentic AI—focused on scale, reliability, observability, and cost."
---

I take one or two engagements at a time, alongside a full-time role. That constraint is the point: it keeps the work to problems where senior judgement is the bottleneck, not headcount.

<p class="page-actions"><a class="btn btn--primary" href="mailto:{{ site.author.email }}?subject=Consulting%20enquiry">Email Basant</a> <span>{{ site.data.availability.headline }} · {{ site.data.availability.response }}</span></p>

## Four shapes an engagement takes

<div class="engagement-grid is-wide">
{% for e in site.data.availability.engagements %}
<article class="engagement-card">
  <span aria-hidden="true">0{{ forloop.index }}</span>
  <h3>{{ e.title }}</h3>
  <p>{{ e.blurb }}</p>
</article>
{% endfor %}
</div>

## Availability

**{{ site.data.availability.headline }}** — {{ site.data.availability.hours }}, {{ site.data.availability.coverage }}.

I work a shifted day by design. {{ site.data.availability.detail }} Real overlap with your team, not asynchronous-only.

*Availability updated {{ site.data.availability.updated | date: "%B %-d, %Y" }}. If this page says one thing and my reply says another, believe the reply — but I keep this line current.*

## How to start

One paragraph is enough. If you can, include these three things so my first reply can be useful:

1. **What breaks today, and how do you find out?** A customer email, an alert that fires, or a number somebody eventually notices is wrong — the three imply very different fixes.
2. **What is already running, and what cannot be replaced?** Engines, orchestrator, cloud, warehouse — plus the contractual or organizational constraints on each.
3. **What decision are you trying to make, and by when?** "Should we move off the warehouse" and "our pipeline is down" both need help, but not the same engagement.
{: .briefing-list }

Repositories, diagrams and dashboards are welcome but never required in a first email. A paragraph of honest description beats a polished deck.

## What I don't do

Declining the wrong work early is cheaper for both of us than discovering the mismatch in week three.

{% for item in site.data.availability.not_doing %}
- {{ item }}
{%- endfor %}
{: .decline-list }

## What I commit to

{{ site.data.availability.response }} I will tell you when a problem does not need me, or needs someone cheaper, and I will say what I think you should do instead.

Work I do ships with the things that make it survivable without me: runbooks, named dataset owners, freshness objectives, and a cost model your finance team can read.
