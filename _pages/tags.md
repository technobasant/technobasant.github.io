---
title: Topics
eyebrow: Writing
permalink: /writing/tags/
description: "Thirteen topics I write about — Spark, Kafka, Iceberg, Postgres, ClickHouse, Kubernetes, agents, RAG, SLOs, data contracts, cost and career notes."
---

Thirteen topics, and nothing outside them. A tag exists here only if I have operated the thing in production or measured it on a rig I built, which keeps the list short and the archive worth reading.
{% for t in site.data.tags %}{% assign n = site.posts | where_exp: "p", "p.tags contains t.slug" | size %}
**[{{ t.name }}](/writing/tags/{{ t.slug }}/)**{% if n > 0 %} <span class="chip chip--count">{{ n }} post{% unless n == 1 %}s{% endunless %}</span>{% endif %} — {{ t.blurb }}
{% endfor %}
Everything is also available as [RSS](/writing/feed.xml) or [JSON Feed](/writing/feed.json).
