---
title: Work with me
eyebrow: Consulting
headline: "Bring me the system that is expensive, slow, or hard to trust."
hero_code: "SCOPE / DECIDE"
page_class: page-hire
permalink: /hire/
description: "Senior consulting on data platforms, database reliability, and governed AI systems — focused engagements with an explicit decision, measurable outcome, and clean handoff."
---

I take one or two engagements at a time, alongside a full-time role. That constraint is the point: it keeps the work to problems where senior judgement is the bottleneck, not headcount.

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

## What I don't do

Declining the wrong work early is cheaper for both of us than discovering the mismatch in week three.

{% for item in site.data.availability.not_doing %}
- {{ item }}
{%- endfor %}
{: .decline-list }

## Availability

**{{ site.data.availability.headline }}** — {{ site.data.availability.hours }}, {{ site.data.availability.coverage }}.

I work a shifted day by design: {{ site.data.availability.detail }} Real overlap with your team, not asynchronous-only.

*Availability updated {{ site.data.availability.updated | date: "%B %-d, %Y" }}. If this page says one thing and my reply says another, believe the reply — but I keep this line current.*

## How to start

Email <a href="mailto:{{ site.author.email }}?subject=Consulting%20enquiry">{{ site.author.email }}</a>. There is no contact form here on purpose: a form on a static site means a third-party endpoint, a spam problem, and one more thing to keep patched.

Answer these five in the first message and my first reply can be useful instead of a list of questions:

1. **What breaks today, and how do you find out?** A customer email, an alert that fires, or a number somebody eventually notices is wrong — the three imply very different fixes.
2. **What are the volumes?** Events or rows per day, total bytes stored, and the growth rate on both. An architecture that is right at 50 GB a day is wrong at 5 TB.
3. **What is already running, and what cannot be replaced?** Engines, orchestrator, cloud, warehouse — plus the contractual or political constraints on each.
4. **Who owns this after I leave, and how many of them are there?** I build for the team that inherits it. One part-time analyst and a four-person platform team get different designs.
5. **What decision are you trying to make, and by when?** "Should we move off the warehouse" and "our pipeline is down" both need help, but not the same engagement.
{: .briefing-list }

Repositories, diagrams and dashboards are welcome but never required in a first email. A paragraph of honest description beats a polished deck.

## What I commit to

{{ site.data.availability.response }} I will tell you when a problem does not need me, or needs someone cheaper, and I will say what I think you should do instead.

Work I do ships with the things that make it survivable without me: runbooks, named dataset owners, freshness objectives, and a cost model your finance team can read.
