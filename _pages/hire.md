---
title: Work with me
last_modified_at: 2026-10-30
seo_title: "Data Architecture, Platform & AI Consulting — Basant Bhattarai"
eyebrow: "Consulting, contract or full-time"
headline: "Data and AI architecture for SaaS teams that have outgrown one Postgres: reviewed, chosen and built."
hero_code: "SCOPE / DECIDE"
page_class: page-hire
permalink: /hire/
description: "Data and AI architecture: reviews, platform selection, moves off Postgres, governance, SOC 2, AI on governed data. Long-term consulting, contract or full-time."
---

I'm looking for long-term work: a consulting or contract engagement, or a full-time role. I work with one team at a time and stay long enough to see its decisions through: reviewed, chosen, built, and handed over to the people who will run them.

<p class="page-actions"><a class="btn btn--primary" href="#hire-form">Send a briefing</a> <a class="btn btn--ghost" href="mailto:contact@basantbhattarai.com.np?subject=Consulting%20enquiry">Email instead</a> <span>{{ site.data.availability.headline }} · {{ site.data.availability.response }}</span></p>

## Engagements

Each one ends in written deliverables you keep, and in a full-time role it is the work I would lead. The samples are public, so you can read the kind of document you would get before you write to me.

<div class="engagement-grid is-wide">
{% for e in site.data.availability.engagements %}
<article class="engagement-card">
  <span aria-hidden="true">0{{ forloop.index }}</span>
  <h3>{{ e.title }}</h3>
  {%- if e.for %}<p class="engagement-card__for">{{ e.for }}</p>{% endif %}
  <p>{{ e.blurb }}</p>
  {%- if e.samples %}
  <ul class="engagement-card__samples" aria-label="Public samples">
    {%- for s in e.samples %}
    <li><a href="{{ s.url | relative_url }}">{{ s.label }}</a></li>
    {%- endfor %}
  </ul>
  {%- endif %}
</article>
{% endfor %}
</div>

## Availability

**{{ site.data.availability.headline }}.** {{ site.data.availability.coverage }}.

I work a shifted day by design. {{ site.data.availability.detail }} Real overlap with your team, not asynchronous-only.

*Availability updated {{ site.data.availability.updated | date: "%B %-d, %Y" }}. If this page says one thing and my reply says another, believe the reply — but I keep this line current.*

## How a consulting or contract engagement runs

1. **Briefing.** The form below, or a 30-minute call: what breaks or what has to be decided, and what cannot change.
2. **Written proposal.** The scope, the deliverables, and how we will both know it worked.
3. **Weekly readouts** to the person who will make the decision, so nothing arrives as a surprise at the end.
4. **Handover.** Documents, decision records, runbooks and named owners, so the work survives without me.

## How to start

Hiring for a full-time role? Email the role and the team, or use the form. The form emails me. GitHub Pages never sees what you type. Name, email, and what is breaking are required; the other two questions make the first reply useful. Repositories and diagrams are welcome, never required.

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
