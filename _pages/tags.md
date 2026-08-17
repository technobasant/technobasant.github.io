---
title: Topics
last_modified_at: 2026-08-11
seo_title: "Writing topics — Basant Bhattarai"
eyebrow: Writing
headline: "Browse by system, failure mode, or layer."
hero_code: "TOPIC / INDEX"
page_class: page-topics
permalink: /writing/tags/
description: "Published field notes organized by system, failure mode, and platform layer — from distributed databases and PostgreSQL to streaming, Iceberg, agents, and SLOs."
---

<div class="topic-index is-wide">
{% assign visible_index = 0 %}
{% for t in site.data.tags %}{% assign n = site.posts | where_exp: "p", "p.tags contains t.slug" | size %}{% if n > 0 %}
{% assign visible_index = visible_index | plus: 1 %}
<a class="topic-index__item" href="/writing/tags/{{ t.slug }}/">
  <span class="topic-index__number" aria-hidden="true">{% if visible_index < 10 %}0{% endif %}{{ visible_index }}</span>
  <span class="topic-index__copy"><strong>{{ t.name }}</strong><span>{{ t.blurb }}</span></span>
  <span class="topic-index__count">{{ n }} post{% unless n == 1 %}s{% endunless %}</span>
</a>
{% endif %}{% endfor %}
</div>

Everything is also available as [RSS](/writing/feed.xml) or [JSON Feed](/writing/feed.json).
