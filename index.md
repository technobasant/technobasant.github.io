---
layout: home
permalink: /
title: Basant Bhattarai
# Every string the home page says lives here. `_layouts/home.html` decides where
# things render and never what they say.
#
# `%apps%` in the lede is substituted from _data/metrics.yml at build time, so the
# only number on this page still has a single source of truth.

hero:
  eyebrow: "Senior Data & AI Engineer · Platform & Database Reliability"
  meta: "Kathmandu, Nepal · Working US and EU hours"
  h1:
    first: "Reliable data."
    second: "Accountable AI."
  lede: "Nine years from backend services to production data infrastructure. Today I design and operate Kafka into Spark on Kubernetes, an Iceberg lakehouse, database serving, freshness SLOs, and a governed multi-agent analytics layer across %apps% integrated apps."
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

# Five metrics, by key, from _data/metrics.yml. Four unqualified percentages read
# like a résumé; five qualified ones read like someone who owns a dashboard — so the
# method microcopy under each number is the point, not decoration.
stats_label: "Selected outcomes"
stats:
  - daily_volume
  - apps
  - uptime
  - infra_cost
  - analytics_delivery

focus_label: "Where I’m useful"
focus_headline: "I work where correctness, scale, and judgment meet."
focus:
  - index: "01"
    title: "Data platforms"
    url: /work/uxcam-data-platform/
    blurb: "Kafka → Spark → Iceberg → dbt/Airflow on Kubernetes. Data contracts, freshness SLIs, lineage, and a cost budget somebody actually reads."
  - index: "02"
    title: "Agentic AI in production"
    url: /work/app-analytics-agent-platform/
    blurb: "LangGraph, CrewAI, Google-ADK, MCP. Agents whose outputs land in typed, audited tables — not chat transcripts."
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
  body: "Senior Data Engineer at UXCam. I own the data platform end to end — ingestion, the Iceberg lakehouse, the serving layer, and the agent platform on top — along with the pager that comes with it. I mentor the engineers who work in it and hold the line on reliability, governance and cost."
  cta: "Work with me"
  cta_url: /hire/
---
