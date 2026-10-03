---
layout: home
permalink: /
title: Basant Bhattarai
last_modified_at: 2026-10-03
seo_title: "Basant Bhattarai — Senior Data & AI Engineer"
description: "Senior Data & AI Engineer. Nine years across data platforms and their databases, AI systems in production, and the system architecture that connects them."
sitemap:
  changefreq: weekly
  priority: 1.0
hero:
  intro: "Hello, I’m Basant Bhattarai."
  # Just the role. The full "· Data Platforms, AI Systems & Architecture" string
  # wrapped to two lines above the H1 and restated what the H1 and lede already
  # say. It still carries in the <title>, JSON-LD and llms.txt, where it is read
  # out of context and needs the qualifier.
  eyebrow: "Senior Data & AI Engineer"
  # "…and the agentic systems that run on them" named two of the three things
  # the practice is hired for. Architecture is the third, and the one a
  # reviewer cannot infer from a stack list. +5 characters; e2e-hero re-run.
  h1: "I design data platforms, AI systems, and the architecture between them."
  # The previous lede read "Kafka, Spark and Iceberg on one side; LangGraph,
  # Google ADK and MCP on the other" — an inventory, and one that framed the two
  # stacks as separate in the same breath as claiming they were integrated. The
  # frameworks now appear where they are load-bearing (résumé, skills, the AI
  # case study) rather than in every lede on the site.
  # Length is a contract here, not a preference: scripts/e2e-hero.mjs asserts the
  # CTAs stay inside the first viewport, and at 320px every ~5 words is another
  # line. 25 words fits; 28 pushed the buttons 12px past the fold.
  lede: "Nine years on systems that have to keep working: terabyte-scale ingestion, the databases underneath, and agents that write into governed stores, not a chat window."
  actions:
    - label: "Selected work"
      url: /work/
      variant: primary
      icon: arrow-right
    - label: "View résumé"
      url: /resume/
      variant: ghost
  portrait:
    base: /assets/images/hero-portrait-v2
    widths: "420,840"
    raster_widths: "420,840"
    fallback_width: "840"
    width: 1120
    height: 1399
    sizes: "(max-width: 48rem) 88px, 19rem"
    alt: "Basant Bhattarai"

proof:
  keys:
    - experience
    - professional_platform_scale
    - professional_event_volume

# The band that answers "what do I hire you for". Rows come from
# _data/practice.yml; this is only the heading and the exit link. `more` points
# at /hire/. Hire is also in the header nav.
practice:
  label: "What I'm hired for"
  headline: "Three problems worth calling me about."
  more: "How an engagement works"
  more_url: /hire/

work:
  label: "Selected work"
  # "…with measured outcomes" described the page rather than the work. The cards
  # below already carry the numbers; the headline should carry the claim.
  headline: "Six systems across data, AI and architecture, and the decisions that kept them running."
  more: "View all work"
  more_url: /work/
  # Curated by slug, one per register: employer practice (data, then AI),
  # consulting, open source, independent product, measured lab. Everything
  # else — including ClickHomes, which the README keeps to /work/ — is one click
  # away. A slug that does not resolve is skipped, so check the build.
  selected:
    - data-platform-practice
    - governed-ai-delivery
    - consulting-short-text-and-alerting
    - spark-sql-kinesis
    - clinic-records-ocr
    - multi-engine-ha-lab

writing:
  label: "Start here"
  headline: "What I learned, written clearly."
  more: "Browse writing"
  more_url: /writing/
  # Curated, not `site.posts limit: 3`.
  #
  # Posts sort by `date`, and several articles are dated to the client project
  # they were rebuilt from rather than to publication. That is deliberate and it
  # is correct for the structured data — but it put the whole lakehouse series
  # at positions 13 to 17 of 16, so the four strongest technical pieces on the
  # site never reached the front page and the feed read as PostgreSQL-only.
  #
  # An explicit list fixes the shop window without touching a single date. Slugs,
  # so a rename fails loudly at build rather than silently dropping a row.
  #
  # One slot per register the site is hired for: applied-ML evaluation (a
  # measurement that withdrew its own plan), agent governance, and the
  # lakehouse. "Ten CI gates" stays one click away as part two of the series.
  spotlight:
    - ocr-measurement-withdrew-the-plan
    - coding-agents-repo-governance
    - trino-iceberg-polaris-lakehouse-spine

contact:
  label: "Contact"
  headline: "Working across European afternoons and US mornings."
---
