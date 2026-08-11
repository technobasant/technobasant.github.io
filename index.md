---
layout: home
permalink: /
title: Basant Bhattarai
# Every string the home page says lives here. `_layouts/home.html` decides where
# things render and never what they say.
#
hero:
  eyebrow: "Senior Data & AI Engineer · Platform & Database Reliability"
  meta: "Kathmandu, Nepal · Working US and EU hours"
  h1:
    first: "I break databases"
    second: "on purpose."
  lede: "Then I publish what came back. Nine years on data platforms and the systems that decide whether their output can be trusted — and a standing habit of testing the recovery claims rather than repeating them."
  actions:
    - label: "Explore selected work"
      url: /work/
      variant: primary
      icon: arrow-right
    - label: "How I work"
      url: /about/
      variant: ghost
    - label: "Résumé (PDF)"
      url: /assets/basant-bhattarai-resume.pdf
      variant: link
      icon: arrow-down
  # The studio portrait, 4:5. Kept to an editorial column width rather than a
  # half-viewport block: the surveys warn against the large hero-photo shape,
  # which also squeezed the headline onto four lines, not against having a face
  # on your own site. A portrait earns its place here because the page carries a
  # consulting CTA.
  portrait:
    base: /assets/images/hero-portrait-v2
    widths: "420,840,1120"
    raster_widths: "420,840,1120"
    fallback_width: "840"
    width: 1120
    height: 1399
    sizes: "(max-width: 56.25rem) 168px, 19rem"
    alt: "Basant Bhattarai"

# Not a stats strip. Two independent surveys — 44 senior-engineer sites and 26
# data/infra sites — found zero with a big-number card grid, zero with a
# years-of-experience claim, and zero with a skills grid. Where engineers of this
# kind do publish numbers, the numbers live in a sentence, attached to hardware
# the author owns and results a reader can reproduce.
# The matrix below the fold is the evidence now, so this line only has to hand
# the reader over to it.
evidence:
  body: "Everything below this line is something I ran on hardware I own, with the commands and the numbers published. Nothing on this page is a figure from an employer's dashboard."

ledger:
  label: "What broke"
  headline: "Three things the documentation did not tell me."
  blurb: "Eight failover scenarios across six engines all passed, which is the least interesting sentence I could write about them. These are the three that cost me an evening each, and none of them produced an error message worth reading."

focus_label: "Where I’m useful"
focus_headline: "I work where correctness, scale, and judgment meet."
focus:
  - index: "01"
    title: "Data platforms"
    url: /about/
    blurb: "Data contracts, freshness objectives, replay, lineage, and ownership boundaries that remain useful when the implementation changes."
  - index: "02"
    title: "Governed AI products"
    url: /writing/building-data-platforms-and-ai-products/
    blurb: "Typed outputs, provenance, evaluation, and policy checks for AI-assisted workflows that affect real product state."
  - index: "03"
    title: "Databases under pressure"
    url: /work/multi-engine-ha-lab/
    blurb: "PostgreSQL, ClickHouse, Trino, ScyllaDB, Redis. Replication, sharding, PITR, and failover I have actually timed."

work:
  label: "Selected work"
  headline: "Systems with constraints, trade-offs, and receipts."
  blurb: "Not a tool list: the decision, what it cost, and the number it moved."
  more: "All case studies"
  more_url: /work/

writing:
  label: "Recent writing"
  headline: "Notes from the sharp edges."
  blurb: "The things that cost me a day to figure out, written so they do not cost you one."
  more: "All writing"
  more_url: /writing/

currently:
  label: "Currently"
  body: "Senior Data Engineer based in Kathmandu. My current work sits between data-platform reliability, database serving, and governed AI delivery. Employer architecture and operational figures are intentionally not published here; the writing focuses on portable methods and reproducible personal labs."
  cta: "Work with me"
  cta_url: /hire/
---
