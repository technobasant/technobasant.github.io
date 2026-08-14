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

work:
  label: "Selected work"
  # "…with measured outcomes" described the page rather than the work. The cards
  # below already carry the numbers; the headline should carry the claim.
  headline: "Five systems, and the decisions that kept them running."
  more: "View all work"
  more_url: /work/

writing:
  label: "Latest note"
  headline: "What I learned, written clearly."
  more: "Browse writing"
  more_url: /writing/

contact:
  label: "Profile"
  headline: "Based in Kathmandu. Working across European afternoons and US mornings."
---
