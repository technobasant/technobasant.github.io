---
title: "ClickHomes: an independent real-estate product"
hook: "A real-estate product I own end to end: PostgreSQL for truth, ClickHouse for speed, RESO as the only way in"
description: "An independent real-estate product that shows how I approach data contracts, schema evolution, operational safety, and accountable AI."
date: 2024-01-01
last_modified_at: 2026-08-15
kind: production
order: 3
featured: true
role: "Founder and sole engineer — built outside my day job"
org: "Independent personal project"
period: "2024 – present"
team: "One person"
scale: "Public details are limited to architecture and operational decisions I can responsibly describe"
problem: "External listing shapes, operational workflows, analytics, and AI-assisted actions had to evolve without corrupting source meaning or making retries unsafe."
decision: "Keep typed RESO transformation as the only listing path, separate operational and analytical stores, and make every durable workflow replayable and reviewable."
flow: clickhomes
stack: [Python, FastAPI, PostgreSQL, ClickHouse, RESO, Next.js, Docker]
metrics: [clickhomes_migrations]
tags: [postgres, data-quality, ai-agents]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
live_url: "https://clickhomes.ai"
---

## Context

ClickHomes is the product I build outside work. It gives me something valuable that an employer project cannot: permission to discuss the decisions publicly because the code, the trade-offs, and the consequences are mine.

The product spans public discovery, decision tools, operational workflows, analytics, and AI-assisted work. The engineering challenge is to let each surface evolve without weakening source provenance or creating a second version of truth.

## Constraints

This is a one-person product, so the recovery path has to remain understandable months after I last touched it. External listing shapes can change without notice, migrations must work for both fresh and long-lived environments, and background retries cannot duplicate user-visible state.

The public case study also has a deliberate boundary: it explains the contracts and failure handling without exposing private connector details, provider credentials, user data, or commercial claims.

## Architecture

External market data follows one path: connector, RESO transformation, gold loader, and RESO-aligned analytical models. The connector retains source and rights metadata. The transformer owns field meaning. The loader accepts typed records, not arbitrary dictionaries.

PostgreSQL stores operational truth: users, sessions, leads, CRM state, and workflow history. ClickHouse stores listings, market data, analytics, and scoring. FastAPI routes stay thin; services own decisions; repositories own queries. This split prevents product workflows from becoming accidental analytics jobs and keeps listing reads away from operational transactions.

AI-assisted work enters through one agent service and becomes durable only through typed workflow records with provenance, validation state, and history. A transcript alone is not product state.

## Decisions and rejected alternatives

| Decision | Alternative rejected | Why it stays | Cost accepted |
| --- | --- | --- | --- |
| Transform every listing source through RESO | Let each connector write its own shape | Source differences stop at one typed boundary | New source fields need deliberate mapping |
| Separate PostgreSQL and ClickHouse by workload | Put every model in one familiar database | Operational truth and analytical reads scale independently | Cross-store workflows need explicit orchestration |
| Keep API → service → repository boundaries | Put data access in endpoints for speed | Decisions remain testable and database code stays local | More files for small features |
| Version every schema change | Patch long-lived environments manually | Fresh and existing environments converge | Even small changes require review |
| Make jobs idempotent with stable keys | Track partial retries by hand | Replays converge instead of duplicate | Conflict rules take design time |
| Persist AI-assisted actions as typed records | Treat chat output as sufficient | Results can be reviewed, compared, and corrected | Policy and schema versions must remain compatible |
{: .case-decisions aria-label="Public engineering decisions and rejected alternatives in the ClickHomes project" }

## Evidence

The private repository carries **{{ site.data.metrics.clickhomes_migrations.value }} versioned SQL migrations**. The count is self-reported implementation evidence, with its counting method disclosed; it is not presented as independently verifiable while the repository remains private.

The stronger engineering signal is the set of enforced boundaries: external data cannot bypass RESO transformation, operational and analytical state have separate stores, background work is designed for retry, and AI-assisted actions keep the context needed for review.

This page deliberately stops short of private connector details, credentials, user data, or commercial claims. Public architecture should demonstrate judgment without turning sensitive implementation into marketing copy.

## Operating and recovery

The operating routine is deliberately unremarkable: migrations are versioned, background work receives stable keys, invalid inputs retain a reason, and changes include a rollback or repair note. The value is not novelty. It is being able to return months later and understand what happened without relying on memory.

When an AI-assisted action matters to the product, the durable record stores its validation and provenance state. The interface may change; the review boundary should not.

## Reflection

I would write the recovery path earlier. My first instinct on a new project is still to prove the happy path and add replay afterwards. That order feels fast for a week and expensive for the next year.

I would also introduce stable read models sooner. Physical schemas need to evolve; product consumers should not have to follow every internal change. A narrow compatibility layer costs less than coordinating the same migration across every reader.

The lesson is ordinary and worth repeating: the quality of a data product shows up in its second attempt—the retry, the backfill, the correction, and the explanation—not only in the first successful demo.
