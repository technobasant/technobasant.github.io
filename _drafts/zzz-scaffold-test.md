---
title: "Scaffolder smoke test"
# 140-158 characters. This is the meta description AND the card blurb.
description: ""
date: 2026-08-11 08:58:13 +0545
# essay | tutorial | note
type: essay
# 1-3 slugs, each of which MUST already exist in _data/tags.yml
tags:
  - career
# ── optional ──────────────────────────────────────────────────────────────
# last_modified_at: 2026-08-11 08:58:13 +0545
# series: ""
# series_order: 1
# featured: false
toc: false
# image: /assets/images/zzz-scaffold-test.png
# image_alt: ""
# canonical_url: ""
# cross_posted_to: ""
# work: ""            # slug of a _work/ case study this post belongs to
# seo_title: ""       # only when the <title> should differ from `title`
# ── tutorial only ─────────────────────────────────────────────────────────
# repo: "https://github.com/technobasant/…"
# level: intermediate            # beginner | intermediate | advanced
# time_estimate: "25 minutes"
# what_youll_build: ""
# prerequisites:
#   - ""
# tested_on: ""
---

Open with the problem, in one short paragraph. What broke, what it cost, why the
obvious fix was wrong. No preamble, no "in this post we will".

<!--more-->

## The first section starts at h2

Never author an `#` heading — the layout renders the H1 from `page.title`.

Every number in the body must come from `_data/metrics.yml`:
`{% raw %}{{ site.data.metrics.some_key.value }}{% endraw %}`. Do not hardcode one.

```python
# a fenced block becomes a direct child of .prose
print("hello")
```
{: data-file="path/to/file.py"}

<div class="callout callout--gotcha" markdown="1">
**The thing that will bite you.** Use `callout--note`, `--tip`, `--warn`,
`--danger` or `--gotcha`.
</div>

## What I would do differently

Close with the trade-off you accepted and what you would change.
