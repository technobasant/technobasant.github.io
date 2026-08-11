---
title: "Freshness SLOs, because job success rate is not an SLI"
description: "Uptime means nothing for a data platform. The SLI is event-time-to-queryable p95 per dataset, and the alert that pages someone is a burn rate, not a failure."
type: essay
tags: [observability-slo]
toc: true
level: intermediate
---

A green DAG tells you a process finished. It does not tell you whether yesterday's events are queryable, which is the only thing a consumer of the platform actually cares about. Job success rate goes to 100% during an outage where a producer stopped sending, because the job succeeded at processing nothing.

The SLI I argue for is event-time-to-queryable, measured per dataset at p95: the wall-clock gap between the timestamp inside the record and the moment a query can return it. It is defined from the consumer's side, it survives retries and backfills, and it degrades gracefully rather than flipping between 0 and 1.

The draft will cover instrumenting it with Prometheus and OpenTelemetry from the ingest and materialization paths, setting a target per dataset tier rather than one number for the platform, and writing multi-window burn-rate alerts so that a slow drift pages nobody at 3 a.m. while a fast burn does. Plus the uncomfortable part: publishing the SLO makes it possible to be visibly wrong, which is exactly why it works.
