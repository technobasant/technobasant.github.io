---
title: "ClickHomes: an independent real-estate product"
hook: "A product I own end to end, documented without exposing deployment or partner internals"
description: "An independent real-estate product that shows how I approach data contracts, schema evolution, operational safety, and accountable AI."
kind: production
order: 1
featured: true
role: "Founder and sole engineer — built outside my day job"
org: "Independent personal project"
period: "2024 – present"
team: "One person"
scale: "Public details are limited to repository-verifiable engineering work"
stack: [Python, PostgreSQL, Pydantic, Docker, "Modern web stack"]
metrics: [clickhomes_migrations]
tags: [postgres, data-quality, ai-agents]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
live_url: "https://clickhomes.ai"
---

## Context

ClickHomes is the product I build outside work. It gives me something valuable that an employer project cannot: permission to discuss the decisions publicly because the code, the trade-offs, and the consequences are mine.

## Constraints

I still draw a boundary around the details. This page does not publish partner feeds, deployment topology, credentials, security controls, customer data, or operational thresholds. The public evidence is the schema history: **90+ versioned SQL migrations**. That number is not a claim about traffic or commercial traction. It shows that the data model has changed through reviewable, repeatable steps instead of manual edits on a live database.

## Architecture

Three principles guide the build:

1. **Every external payload crosses a typed boundary.** A source can change without notice. The product should reject or quarantine a shape it does not understand instead of guessing.
2. **A retry must converge on the same state.** Imports and background jobs are designed to be rerun. Recovery should not require remembering which half of a batch succeeded.
3. **AI output is product data when a workflow can act on it.** Useful output receives a schema version, provenance, validation state, and history. A disposable transcript is not an operational record.

Those rules matter more to me than the tool list. Implementations can change; the failure boundaries should remain legible.

## Decisions and trade-offs

| Decision | Why it stays | Cost I accept |
| --- | --- | --- |
| Version every schema change | A fresh environment and an existing environment must reach the same shape | Small changes require discipline and review |
| Preserve invalid input with a reason | A rejected record is debuggable; a dropped record is a mystery | Quarantine needs ownership and cleanup |
| Make background work idempotent | Replays and retries become routine instead of dangerous | Stable keys and conflict rules take design time |
| Persist AI-assisted decisions as typed records | Results can be reviewed, compared, and corrected | Schema and policy versions must remain compatible |
| Prefer a boring recovery path | One person must be able to understand it months later | Some automation remains deliberately conservative |
{: aria-label="Public engineering decisions in the ClickHomes personal project" }

## Results

The strongest evidence here is not a diagram. It is the accumulated maintenance work: migrations that can be replayed, inputs that fail visibly, jobs that can be retried, and records that retain the context needed to review them later.

That is also why this page is intentionally less detailed than an internal design document. A portfolio should demonstrate judgment without turning private architecture into marketing copy.

## Running it

The operating routine is deliberately unremarkable: migrations are versioned, background work receives stable keys, invalid inputs retain a reason, and changes include a rollback or repair note. The value is not novelty. It is being able to return months later and understand what happened without relying on memory.

When an AI-assisted action matters to the product, the durable record stores its validation and provenance state. The interface may change; the review boundary should not.

## What I'd do differently

I would write the recovery path earlier. My first instinct on a new project is still to prove the happy path and add replay afterwards. That order feels fast for a week and expensive for the next year.

I would also introduce stable read models sooner. Physical schemas need to evolve; product consumers should not have to follow every internal change. A narrow compatibility layer costs less than coordinating the same migration across every reader.

The lesson is ordinary and worth repeating: the quality of a data product shows up in its second attempt—the retry, the backfill, the correction, and the explanation—not only in the first successful demo.
