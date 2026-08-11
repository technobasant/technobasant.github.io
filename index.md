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
  # Portrait removed from the homepage: the background is a generated
  # circuit-board render, which is the strongest amateur signal a technical site
  # can carry, and homepage portraits are rare in this genre anyway. The square
  # crop still serves the post author card and the Person structured data.
  portrait_disabled:
    base: /assets/images/hero-portrait-v2
    widths: "420,840,1120"
    raster_widths: "420,840,1120"
    fallback_width: "840"
    width: 1120
    height: 1399
    sizes: "(max-width: 56.25rem) min(88vw, 34rem), 31rem"
    alt: "Basant Bhattarai, data and AI platform engineer, Kathmandu"
    caption: "Basant Bhattarai · Kathmandu, Nepal"

# Not a stats strip. Two independent surveys — 44 senior-engineer sites and 26
# data/infra sites — found zero with a big-number card grid, zero with a
# years-of-experience claim, and zero with a skills grid. Where engineers of this
# kind do publish numbers, the numbers live in a sentence, attached to hardware
# the author owns and results a reader can reproduce.
evidence:
  body: "Most recently I wrote a common test plan and ran it against six database engines — MongoDB, ScyllaDB, SolrCloud, MariaDB with Galera, Redis and PostgreSQL — on a single machine I own. Eight failover scenarios, every command and measurement published, including a PostgreSQL 18 replay lag of 383 µs and a Redis Sentinel promotion at roughly five seconds."
  cta: "Read the lab, the rig, and the numbers"
  url: /work/multi-engine-ha-lab/

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
