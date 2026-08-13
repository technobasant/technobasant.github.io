---
title: "{{TITLE}}"
# 120–165 characters. This is the meta description and card blurb.
description: ""
date: {{DATE}}
type: essay
# One to three existing slugs from _data/tags.yml.
tags:
  - career
toc: true
featured: false
# Three to five complete sentences. These render as the article's argument map.
key_takeaways:
  - ""
  - ""
  - ""
# ── optional ──────────────────────────────────────────────────────────────
# last_modified_at: {{DATE}}
cover:
  base: "/assets/images/editorial-{{SLUG}}-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Describe the scene; no UI chrome, no logos."
  caption: "One sentence that states the operating claim the image is standing in for."
# image: /assets/images/{{SLUG}}.png
# image_alt: ""
# canonical_url: ""
# cross_posted_to: ""
# work: ""            # slug of a related _work/ case study
# seo_title: ""       # only when the browser title should differ
---

Open with the tension in two short paragraphs: the decision, mistaken
assumption, or production consequence. Do not announce the article and do not
start with biography.

## State the argument

Make one claim that can be disproved. Define the boundary and the terms that
matter before listing technologies.

## Show the evidence

Use a measurement, failure trace, decision table, or concrete system boundary.
Every portfolio metric comes from `_data/metrics.yml`, for example
`{% raw %}{{ site.data.metrics.some_key.value }}{% endraw %}`.

| Decision | Evidence | Consequence |
| --- | --- | --- |
| Example | What was observed | What changed |

<div class="callout callout--note" markdown="1">
**Boundary.** State what was measured and what remains an inference.
</div>

## Make the decision useful

Close with the operating rule, trade-off, or question a reader can apply. Do not
repeat the introduction and do not end with a generic contact pitch.
