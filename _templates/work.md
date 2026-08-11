---
title: "{{TITLE}}"
# One sentence. The problem, not the solution. Shown on the case card.
hook: ""
# 140-158 characters. Meta description AND card blurb.
description: ""
# production | lab
kind: production
role: ""
org: ""
period: ""
team: ""
scale: ""
stack:
  - ""
# Keys into _data/metrics.yml. NEVER hardcode a number here or in the body.
metrics:
  - ""
# 1-3 slugs that MUST already exist in _data/tags.yml
tags:
  - ""
featured: false
order: 100
# image: /assets/images/{{SLUG}}.png
# image_alt: ""
# repo: "https://github.com/technobasant/…"
# live_url: ""
---

## Context

What the system was, who depended on it, and what the constraint was. First
person, plain, specific.

## Decisions

| Decision | Alternative | Why |
|---|---|---|
|  |  |  |

## Results

Every figure resolves through `_data/metrics.yml`:
`{% raw %}{{ site.data.metrics.some_key.value }}{% endraw %}`.

## What I would do differently

The trade-off that is still outstanding.
