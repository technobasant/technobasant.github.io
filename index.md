---
layout: home
permalink: /
title: Basant Bhattarai
# Every string the home page says lives here. `_layouts/home.html` decides where
# things render and never what they say.
#
hero:
  eyebrow: "Senior Data & AI Engineer · Platform & Database Reliability"
  meta: "Working US and EU hours"
  h1:
    first: "Data platforms,"
    second: "and the systems that keep them honest."
  lede: "I am a senior data and AI engineer with nine years across backend services, production data platforms, database reliability, and AI features that other workflows depend on. I work on the parts that decide whether a system stays correct when it is under load, being changed, or recovering from something."
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
  body: "Six years of that has been one platform end to end — ingestion, transformation, storage, serving, and the contracts and recovery paths between them. The rest is databases under pressure, and AI features held to the same standard as any other write path."

ledger:
  label: "Independent lab work"
  headline: "I test recovery claims instead of repeating them."
  blurb: "I keep a rig for taking database clusters apart: six engines, eight injected faults, every command and measurement published. Three findings from it that no documentation warned me about."

focus_label: "What I do"
focus_headline: "Four areas I have carried in production, not evaluated."
focus:
  - index: "01"
    title: "Data platforms and pipelines"
    url: /work/data-platform-practice/
    blurb: "Batch and streaming ingestion, transformation and the serving layer above it. Spark, Kafka, Airflow, dbt and Iceberg — with data contracts at the boundaries, freshness measured as an objective rather than a job exit code, and replay designed in rather than improvised."
  - index: "02"
    title: "Databases under pressure"
    url: /work/multi-engine-ha-lab/
    blurb: "PostgreSQL, ClickHouse, Trino, MongoDB, Redis, ScyllaDB and MariaDB. Replication and promotion, sharding and partition design, point-in-time recovery, query plans, and the upgrade surprises that only appear on the version you are actually running."
  - index: "03"
    title: "AI features you can audit"
    url: /work/governed-ai-delivery/
    blurb: "LangGraph, CrewAI, MCP and retrieval over real corpora. Typed outputs validated at the boundary, provenance on every generated record, evaluation before rollout, and a fallback that is a real path rather than an apology."
  - index: "04"
    title: "Running it once it is live"
    url: /resume/#skills
    blurb: "Kubernetes, Terraform and CI on AWS and GCP, with Prometheus, Grafana and OpenTelemetry underneath. Capacity, cost, backup and restore, incident runbooks, and ownership that transfers to someone else."

work:
  label: "Selected work"
  headline: "Systems with constraints, trade-offs, and receipts."
  blurb: "Systems I own end to end, and the practice I bring to the ones I do not."
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
  body: "Senior Data Engineer at UXCam, working across data-platform reliability, database serving and AI delivery. Outside that I build ClickHomes, run a database reliability lab, and write up the things that cost me a day. I take a small number of consulting engagements alongside it."
  cta: "Work with me"
  cta_url: /hire/
---
