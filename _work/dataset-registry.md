---
title: "dataset-registry: data contracts that wait for the consumers they break"
seo_title: "dataset-registry — Data Ownership, Contracts and Lineage in Go and PostgreSQL"
hook: "A breaking schema change should be a question to the teams it breaks, asked by a registry that knows who they are"
description: "Open-source data-ownership registry in Go and PostgreSQL: owned datasets, JSON Schema contracts checked both ways, OpenLineage lineage, freshness SLOs."
date: 2026-10-14
last_modified_at: 2026-10-14
kind: open-source
order: 6
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "Go API, PostgreSQL 18, Next.js UI and Prometheus as containers on one host; 51 labelled contract changes; lineage graphs up to 10,000 datasets"
problem: "Data contracts usually fail one of two ways: a checker that blocks every breaking change, so teams route around it with _v2 tables, or no checker, so consumers learn about the change from an incident. Neither knows who depends on what."
decision: "Make ownership the first rule, check every contract change in both directions with a checker allowed to over-report but never to under-report, and turn a breaking change into an acknowledgement from each registered consumer."
repo: "https://github.com/technobasant/dataset-registry"
metrics: [registry_false_negatives, registry_false_alarms, registry_ingest]
stack: [Go, "PostgreSQL 18", sqlc, OpenLineage, "JSON Schema", Next.js, "React Flow", Prometheus, Playwright, "Docker Compose"]
tags: [data-quality, postgres]
image: /assets/og/og-default-v3.png
image_alt: "Basant Bhattarai — Reliable data. Accountable AI."
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

A familiar kind of data incident starts like this. Someone changes a table or a topic, the change looks harmless, and a team two hops downstream finds out from a broken dashboard. Data contracts are meant to stop that, and in practice they tend to fail in one of two ways. A checker that rejects every breaking change teaches teams to route around it: a new topic, a `_v2` table, a column nobody removes. Or there is no checker, and the contract describes what someone intended last quarter.

Both failures have the same root. Nothing in the system knows who depends on what, so there is nobody to ask when a change is genuinely breaking and still the right change.

[dataset-registry](https://github.com/technobasant/dataset-registry) is the control plane I built to test a different arrangement. Every dataset has an owning team and a named person, a freshness SLO, a versioned JSON Schema contract, lineage from OpenLineage, and a list of the teams that consume it. A breaking change is neither blocked nor shipped quietly. It waits until every one of those teams has acknowledged it. The demo data belongs to a fictional retailer, the same one used in [governed-agent](https://github.com/technobasant/governed-agent), [streaming-platform](https://github.com/technobasant/streaming-platform) and [realtime-ml](https://github.com/technobasant/realtime-ml).

## Constraints

This is a from-scratch reference system, not a production deployment, and it has no real users. That shaped what I could claim. I could measure the checker against labelled changes, the API under load, and the delay before a freshness breach is noticed. I could not measure how real teams behave when they are asked to acknowledge a change, so the post about the checker does not pretend to.

Everything runs as containers on one host: an Apple M5 with 24 GB, Docker's Linux VM given 8 CPUs, PostgreSQL 18 with its stock configuration, and other projects' containers idle alongside. There is no network latency in any figure. Absolute numbers are this host's, and the point is the shape: what grows with what.

## Architecture

One Go binary holds five parts, all writing to PostgreSQL 18:

- **Lineage ingest.** Accepts OpenLineage `RunEvent`s exactly as the OpenLineage HTTP transport sends them. Each event is validated against the 2-0-2 schema and stored in one transaction.
- **Registry rules.** Ownership, consumers and contracts. A dataset first seen in lineage is recorded as unowned, and nobody can register as its consumer until a team claims it.
- **Compatibility checker.** Compares two contract versions and reports, change by change, whether each one breaks BACKWARD, FORWARD or both, with a reason.
- **Change-request state machine.** `open → approved → published`, or `rejected` or `withdrawn`. There is one open request per dataset, enforced by a partial unique index.
- **Freshness evaluator.** Runs on an interval, records every status transition, and exports staleness to Prometheus, which owns the alerting.

Every transition goes into an append-only audit log whose triggers refuse `UPDATE`, `DELETE` and `TRUNCATE`. The Next.js UI is server-rendered and calls the API with bearer tokens. It shows datasets by SLO status, contract diffs with the checker's report, a React Flow lineage graph and the change-request review.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Compatibility defined on validity sets, FORWARD by default | Avro-style resolution rules | A JSON Schema validator does not skip unknown fields or fill defaults. One rule (absent fields take `additionalProperties`) replaces a table of special cases | Strict labels surprise people: removing an optional field from an open object breaks consumers |
| Checker may over-report, never under-report | A checker that guesses at regex containment and unions | A false negative is an incident; a false alarm is a review | Regex, `anyOf`, `$ref` and `multipleOf` changes are always flagged, so a `$ref`-heavy corpus would see many false alarms |
| Breaking changes wait for every consumer's acknowledgement | Reject every breaking change | Blocking pushes teams to `_v2` tables and contracts that describe nothing | A consumer that never answers blocks the owner; there is no expiry yet |
| OpenLineage events, validated against the published schema | A custom lineage format with adapters | Airflow, dbt, Spark and Flink already emit it, and unowned datasets fall out for free | The registry trusts producers' clocks, and edges are never retired |
| Freshness from the last successful write, checked on an interval | Querying the data itself | No data access needed, and the lag is bounded and measurable | A job that reports success after writing nothing keeps its dataset fresh |
| Go with sqlc, one binary | Python with an ORM | The SQL that matters — row locks, a partial unique index, a recursive lineage walk — is the SQL that runs, typed at compile time | More code to write than an ORM for the plain parts |
| HS256 role tokens and a development issuer | An identity provider | It makes the authorization rules real and testable; OIDC would touch one package | Not production authentication; reads are open |
{: aria-label="dataset-registry design decisions and their costs" }

## Results

**The checker.** On 51 hand-labelled schema changes, the checker passed {{ site.data.metrics.registry_false_negatives.value }} breaking changes as safe, in any of the three modes. A unit test enforces that on every case, so a false negative fails CI. In each direction it flagged {{ site.data.metrics.registry_false_alarms.value }} changes as breaking that are in fact safe, all from keywords it deliberately does not reason about. The labels are not just my opinion. An oracle generated 8,092 probe documents from both versions of every schema, ran them through a real JSON Schema validator, and agreed with all 51. [The post on the checker](/writing/json-schema-compatibility-data-contracts/) covers which "safe" changes break which direction, and why the checker leans the way it does.

**Ingest.** OpenLineage ingest stored {{ site.data.metrics.registry_ingest.value }} events from 32 concurrent clients, with no errors. Throughput grew about 7× from one client to 32 while p50 latency grew about 4×, which puts the limit in the database rather than the handler.

**Lineage.** A five-hop downstream query in a 10,000-dataset graph took {{ site.data.metrics.registry_lineage_5hop.value }} at p50. One hop cost the same at 100 datasets as at 10,000. Latency followed the size of the neighbourhood, not the size of the graph.

**Freshness.** At the default 15 s evaluator interval, a breach was noticed {{ site.data.metrics.registry_breach_delay.value }} after its deadline at the median. That is half an interval, exactly what an interval scheduler predicts, so I measured the lag rather than assuming it.

## What the measurements refused to show

**Whether the checker is accurate on real contracts.** I wrote the labelled set alongside the checker. It tests the rules the checker claims to implement and is not a sample of real-world schema changes. A real corpus would have far more `$ref` and `oneOf`, which this checker always calls breaking.

**Whether people answer.** The acknowledgement workflow is tested end to end by Playwright, from register to consume to breaking change to acknowledge to publish. Nothing measures how long a real consumer team takes to respond, or whether teams start rubber-stamping reviews once they arrive often enough.

**Whether data arrived.** Freshness means a pipeline reported `COMPLETE`. A job that writes nothing and reports success keeps its dataset green.

**Where it slows down.** The weak spots are measured and listed rather than hidden. Listing all 1,000 datasets runs three correlated subqueries per row. A pass in which all 10,000 SLOs change status at once, as after a restart with stale statuses, takes seconds because each transition is its own transaction.

## What I'd do differently

**Check the schema facet against the contract.** OpenLineage events can carry the output schema, and the registry currently ignores it. Comparing it on every run would catch a producer drifting from its contract without anyone proposing a change. That is the most useful thing it does not do.

**Give change requests a clock.** A request with no expiry and no escalation turns one unresponsive team into a veto. Notifying consumers when a request opens, and escalating after a deadline, belong in the first version, not the roadmap.

**Measure the checker on a real corpus before trusting the false-alarm rate.** Two in 51 is a number about my own labelled set. The figure that would change a decision is the rate on a few hundred real contract histories, and I do not have that yet.
