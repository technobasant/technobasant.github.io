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
  eyebrow: "Senior Data & AI Platform Engineer"
  meta: "Kathmandu, Nepal · Working US and EU hours"
  h1: "Reliable data. Accountable AI."
  lede: "I design and operate the systems behind both: Kafka into Spark on Kubernetes, an Iceberg lakehouse, freshness SLOs, and a multi-agent analytics layer across %apps% integrated apps. Open-source first. Measured in uptime, latency, and cost."
  actions:
    - label: "Explore selected work"
      url: /work/
      variant: primary
    - label: "How I work"
      url: /about/
      variant: ghost
    - label: "Résumé (PDF)"
      url: /assets/basant-bhattarai-resume.pdf
      variant: link
      icon: arrow-down
  portrait:
    base: /assets/images/portrait
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
  more: "All case studies"
  more_url: /work/

writing:
  label: "Recent writing"
  blurb: "I write up the things that cost me a day to figure out."
  more: "All writing"
  more_url: /writing/

currently:
  label: "Currently"
  body: "Senior Data Engineer at UXCam. I own the data platform end to end — ingestion, the Iceberg lakehouse, the serving layer, and the agent platform on top — along with the pager that comes with it. I mentor the engineers who work in it and hold the line on reliability, governance and cost."
  cta: "Work with me"
  cta_url: /hire/
---
