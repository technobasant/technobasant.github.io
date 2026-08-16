---
layout: home
permalink: /
title: Basant Bhattarai
seo_title: "Basant Bhattarai — Senior Data & AI Engineer · Platforms, Databases & Agentic Systems"
description: "Senior Data & AI Engineer. Nine years building data platforms, running the databases underneath them, and putting agents into production against both."
hero:
  intro: "Hello, I’m Basant Bhattarai."
  # Just the role. The full "· Platforms, Databases & Agentic Systems" string
  # wrapped to two lines above the H1 and restated what the H1 and lede already
  # say. It still carries in the <title>, JSON-LD and llms.txt, where it is read
  # out of context and needs the qualifier.
  eyebrow: "Senior Data & AI Engineer"
  h1: "I design data platforms, and the agentic systems that run on them."
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
# at /hire/, which until now had no route in from the homepage at all — it is
# absent from the header nav by design, so the footer was the only way in.
practice:
  label: "What I'm hired for"
  headline: "Three problems worth calling me about."
  more: "How an engagement works"
  more_url: /hire/

work:
  label: "Selected work"
  # "…with measured outcomes" described the page rather than the work. The cards
  # below already carry the numbers; the headline should carry the claim.
  headline: "Five systems, and the decisions that kept them running."
  more: "View all work"
  more_url: /work/

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
  spotlight:
    - trino-iceberg-polaris-lakehouse-spine
    - rag-lakehouse-delta-spark-chroma
    - patroni-postgresql-18-rocky8-etcd-failover

contact:
  label: "Profile"
  headline: "Based in Kathmandu. Working across European afternoons and US mornings."
---
