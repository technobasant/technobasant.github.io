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
    first: "Reliable data."
    second: "Accountable AI."
  lede: "Nine years from backend services to production data and AI systems. I focus on the contracts, recovery paths, and operating decisions that keep those systems trustworthy under change."
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
  portrait:
    base: /assets/images/hero-portrait-v2
    widths: "420,840,1120"
    raster_widths: "420,840,1120"
    fallback_width: "840"
    width: 1120
    height: 1399
    sizes: "(max-width: 56.25rem) min(88vw, 34rem), 31rem"
    alt: "Basant Bhattarai, data and AI platform engineer, Kathmandu"
    caption: "Basant Bhattarai · Kathmandu, Nepal"

# Only personal, reproducible evidence is published here. Employer scale,
# topology, customer, cost, and reliability figures stay private.
stats_label: "Public evidence"
stats:
  - experience
  - lab_scenarios
  - clickhomes_migrations

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
