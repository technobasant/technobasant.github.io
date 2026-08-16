---
layout: tag
title: Observability & SLOs
last_modified_at: 2026-08-16
eyebrow: Topic
permalink: /writing/tags/observability-slo/
tag: observability-slo
description: "What to measure when 'uptime' means nothing for a data platform: freshness SLIs, burn-rate alerts, lineage, and alerts that should actually page someone."
---

Availability is a weak first signal for a data product: every service can be green while a table serves yesterday's answer. I prefer consumer-facing signals such as freshness, completeness, decision latency, and safe replay, each with a named owner. These notes cover what deserves to wake a person, how to connect an alert to a repair action, and why deleting a noisy alert can be a reliability improvement.
