---
title: "Short-text classification, alerting and agent knowledge for a lakehouse team"
seo_title: "Consulting Case Study — Short-Text Classification and Alerting"
hook: "A comment classifier that failed in production, rebuilt around the unit of work — plus the alerting, agent knowledge and trend measurement around it."
description: "Consulting case study: multilingual short-text classification, metric alerting and agent knowledge on a lakehouse, designed around distinct strings, not rows."
date: 2026-08-25
last_modified_at: 2026-10-03
kind: consulting
order: 1
role: "Consultant — data and AI"
org: "Consulting client (confidential)"
period: "2026"
team: "Remote, alongside the client's data and product leads"
scale: "Daily batches of short multilingual user comments on a lakehouse"
problem: "A comment-classification notebook failed in production, and the per-row model calls proposed to replace it would have been the most expensive way to buy the cheapest inference available."
decision: "Make the distinct normalized string the unit of work, cache its label per taxonomy version, discover new categories on clusters of strings, and ship the model inside the image."
stack: [Databricks, "Delta Lake", Python, "multilingual-e5", UMAP, HDBSCAN, Docker, "Slack API"]
tags: [applied-ml, data-quality, ai-agents]
image: /assets/og/og-agents.png
image_alt: "Consulting case study: short-text classification and alerting on a lakehouse — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

A consumer-facing service collects short free-text comments from its users: `scam`, `spam`, the name of a brand someone was impersonating, occasionally a sentence describing a threat. Comments arrive in many languages from several regions, they are often one to three words long, and they land every day in a Databricks lakehouse. The team wanted them turned into governed categories that product, risk and operations could act on — and wanted new patterns surfaced before anyone had a name for them.

The existing notebook failed in production, and the reason was mundane. Databricks job clusters are ephemeral: every run started with an empty model cache and re-downloaded the weights from the Hugging Face Hub. That was slow when it worked and failed outright whenever the Hub throttled. The conclusion on the table was to drop local models and call a hosted model for every row.

## My role

I reviewed the first version, wrote the redesign and its build specification, built a reference implementation with tests, and packaged the model so the job never touches the network. The team then asked for three adjacent pieces: an alerting engine for warehouse metrics, a structure for the knowledge their agents read, and a research note on measuring how categories trend. The client, its data and its code stay private; this page describes the problems and the decisions.

## Four workstreams

**1. Classification, around the right unit of work.** The failing notebook did not show that local models were impractical. It showed that the model was not under version control. The expensive mistake was never hosted versus local; it was classifying the same string thousands of times. Short comments are canned, so a small head of distinct strings carries most of the volume. The redesign normalizes every comment to a key (Unicode NFKC, case folding, punctuation), caches the label per key and taxonomy version, and sends only cache misses — distinct strings, never rows — to a labeller. New categories are discovered on clusters of distinct strings, one model call names a cluster, and a human approves it. A new string is assigned only when its best match clears a similarity floor *and* beats the runner-up by a margin; otherwise it goes to review or to an outlier pool that is itself re-clustered. Forcing every string into its nearest cluster would absorb a new pattern into an old category where nobody would see it.

**2. Alerting on warehouse metrics.** Alerts needed Acknowledge, Resolve and Close buttons in Slack. A scheduled job cannot receive a click, so the design is two deployables sharing one codebase: a stateless detector on a schedule, and a small receiver holding an outbound Socket Mode connection, because the platform's apps sit behind an authentication proxy and nothing could arrive inbound. State is written before Slack is called, so a Slack outage delays a message and never loses an alert. Windows are aligned to the wall clock, so a late run evaluates the same window as an on-time one. A backfill command replays a threshold over the previous 30 days before an alert is enabled: an alert that would have fired 400 times does not get switched on. This one is a reviewed design; it was not built during the engagement.

**3. Knowledge an agent can use.** Their agents read wiki pages, notebooks and old chat answers that disagreed with each other. The structure I proposed: one concept per file with a fixed template, a `verified_on` date and an owner, and an explicit **Disputed** section instead of silently choosing a winner. An index sits on top, plus a semantic layer that maps kinds of question to tables, including the tables an agent must never use. Anything that changes on its own, such as schemas or row counts, is generated rather than written by hand, and invariants an agent must not get wrong are promoted into tools.

**4. Measuring trends honestly.** A related question was how fast each category is growing. That is a quantification problem, not a classification problem: classify-and-count is biased exactly when the mix shifts. The note specifies adjusted estimators, a per-period gold sample for valid intervals, fixed weighting across sources, and treating any model or taxonomy change as a measurement break. I later [measured the core of it in a simulation](/writing/count-prevalence-not-classifications/).

## Decisions

| Decision | Alternative | Why |
|---|---|---|
| Classify distinct normalized strings; cache per taxonomy version | Classify every row | Cost follows novelty, not volume. The cache key is the irreversible decision; the labeller behind it can be swapped. |
| Bake the model into the image and prove it loads offline | Download at run time, or a hosted call per row | The download was the failure. A per-row API turns the cheapest inference into the most expensive. |
| Three bands: assigned, review, outlier pool | Nearest cluster always wins | Forced assignment hides new patterns inside old categories. |
| A generic mechanism label plus a brand and region attribute | One label per impersonated brand | Brand labels multiply across regions and fragment the training data for one mechanism. |
| One multilingual embedding model | A pipeline per language | Per-language pipelines multiply maintenance; one model shows a wave hitting several markets as one cluster. |
| Alert state written before Slack; Socket Mode receiver | Notify first; inbound webhook | Notify-first loses alerts when Slack is down; inbound was impossible behind the proxy. |
| Alert state in a Delta table behind an interface | Managed Postgres from day one | Tens of alerts do not justify an instance, and a scale-to-zero resume can land inside Slack's three-second acknowledgement budget. |

## What the v1 review found

The first version had 22 defects. They fell into five groups, and almost none of them would have failed a demo.

- **Orchestration.** A date parameter was declared and then ignored in favour of `current_date()`, so a backfill processed zero rows and reported success. Steps described as idempotent were insert-only, a counter incremented in place double-counted under retries, and parallel backfills collided on `MERGE` with `ConcurrentAppendException`.
- **Silent cache misses.** A naive `lower()` and regex normalization gave two encodings of the same visible text — NFC and NFD — two different keys.
- **Model handling.** Weights were downloaded on every run; clustering ran on raw high-dimensional vectors; an unbounded `toPandas()` sat in the hot path. The e5 models expect a `query: ` prefix, and leaving it off raises no error, so it has to be enforced in code rather than remembered.
- **Governance.** There was no taxonomy version, clusters were recreated daily with unstable IDs, unresolved rows were silently dropped, and nothing would notice if the hosted model changed underneath the series.
- **Supply chain.** A Hugging Face token passed as a Docker build argument is recorded in `docker history`. It became a build secret, and the image check counts zero matches. A model download without file filters also pulled about 2 GB of duplicate formats for a model of roughly 470 MB.

## Results

The reference implementation ships with 15 tests, each named after the defect it guards, and all passed on the last recorded run. The container check runs with networking disabled and fails the build if the model cannot load. Embedding throughput, measured locally, was about 2,600 short texts per second on four CPU threads. The 20–40× reduction in model tokens was an estimate from stated assumptions, and the proposal said so; its first build step was the profiling query that replaces the assumption with a measurement.

Because the client's data stays private, I rebuilt the classification design from scratch on a synthetic corpus and measured it: [label the string, not the row](/writing/classify-distinct-strings-not-rows/).

## What I would do differently

I would put the distribution profile in the first paragraph of the proposal, not in the first step of the build. Every cost figure depended on how heavy the head of distinct strings was, and the document had to carry that as an assumption. I would also push earlier for a few hundred labelled real comments: the margin and category-count defaults were tuned on synthetic data, and both are flagged for recalibration before anyone trusts them.
