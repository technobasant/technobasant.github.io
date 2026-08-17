---
title: Work with me
last_modified_at: 2026-08-17
seo_title: "Data Platform, Database & Agentic AI Consulting — Basant Bhattarai"
eyebrow: Consulting
headline: "Bring me the platform, the database, or the agentic system that has to work in production."
hero_code: "SCOPE / DECIDE"
page_class: page-hire
permalink: /hire/
description: "Senior consulting on data platforms, database lifecycle work, and getting agents into production against a stack you already run. One or two engagements at a time."
---

I take one or two engagements at a time, alongside a full-time role. That constraint is the point: it keeps the work to problems where senior judgement is the bottleneck, not headcount.

<p class="page-actions"><a class="btn btn--primary" href="#hire-form">Send a briefing</a> <a class="btn btn--ghost" href="mailto:{{ site.author.email }}?subject=Consulting%20enquiry">Email instead</a> <span>{{ site.data.availability.headline }} · {{ site.data.availability.response }}</span></p>

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

The form emails me. GitHub Pages never sees what you type. Name, email, and what is breaking are required; the other two questions make the first reply useful. Repositories and diagrams are welcome, never required.

{% include hire-form.html %}

## What I don't do

Declining the wrong work early is cheaper for both of us than discovering the mismatch in week three.

{% for item in site.data.availability.not_doing %}
- {{ item }}
{%- endfor %}
{: .decline-list }

## What I commit to

{{ site.data.availability.response }} I will tell you when a problem does not need me, or needs someone cheaper, and I will say what I think you should do instead.

Work I do ships with the things that make it survivable without me: runbooks, named dataset owners, freshness objectives, and a cost model your finance team can read.
