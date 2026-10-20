---
layout: home
permalink: /
title: Basant Bhattarai
last_modified_at: 2026-10-20
seo_title: "Basant Bhattarai — Data & AI Architect · Senior Data Engineer"
description: "Data and AI architecture, hands-on: architecture reviews, platform selection, migrations off Postgres, governance and SOC 2 readiness, and AI on governed data."
sitemap:
  changefreq: weekly
  priority: 1.0
hero:
  intro: "Hello, I’m Basant Bhattarai."
  # The practice and the title held, together and in that order. The title
  # alone undersold the architecture work; the practice alone would claim a
  # title not held. JSON-LD states only the title held (author.job_title).
  eyebrow: "Data & AI Architect · Senior Data Engineer"
  # Design first, because that is what is hired; "then build them" because the
  # designs are hands-on, which the proof strip below backs. e2e-hero re-run.
  h1: "I design data platforms and the AI on them, then build them."
  # The previous lede read "Kafka, Spark and Iceberg on one side; LangGraph,
  # Google ADK and MCP on the other" — an inventory, and one that framed the two
  # stacks as separate in the same breath as claiming they were integrated. The
  # frameworks now appear where they are load-bearing (résumé, skills, the AI
  # case study) rather than in every lede on the site.
  # Length is a contract here, not a preference: scripts/e2e-hero.mjs asserts the
  # CTAs stay inside the first viewport, and at 320px every ~5 words is another
  # line. 25 words fits; 28 pushed the buttons 12px past the fold.
  # Who it is for, then the five engagements in the order /hire/ lists them.
  lede: "For SaaS teams that have outgrown one Postgres: architecture reviews, platform selection, migrations, governance and SOC 2 readiness, from nine years hands-on."
  actions:
    - label: "Selected work"
      url: /work/
      variant: primary
      icon: arrow-right
    - label: "Work with me"
      url: /hire/
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

# The band that answers "what do I hire you for". Rows come from
# _data/practice.yml; this is only the heading and the exit link. `more` points
# at /hire/. Hire is also in the header nav.
practice:
  label: "What I'm hired for"
  headline: "Four problems worth calling me about."
  more: "Engagements, scope and samples"
  more_url: /hire/

# The ledger of measured results under the capability rows. Rows come from
# _data/findings.yml; each links to the write-up that holds its method.
findings:
  label: "Findings"
  headline: "Measured, with the method in each write-up."
  more: "All writing"
  more_url: /writing/

contact:
  label: "Contact"
  headline: "Facing a platform decision? Send the brief."
---
