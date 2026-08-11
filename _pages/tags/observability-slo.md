---
layout: tag
title: Observability & SLOs
eyebrow: Topic
permalink: /writing/tags/observability-slo/
tag: observability-slo
description: "What to measure when 'uptime' means nothing for a data platform: freshness SLIs, burn-rate alerts, lineage, and alerts that should actually page someone."
---

Availability is close to meaningless as a first metric for a data platform: every service can be green while the tables serve yesterday's numbers to somebody making a decision. So I run freshness and latency objectives per dataset, each with a named owner, burn-rate alerts in Prometheus and Grafana, and enough lineage that a page tells you what broke rather than what noticed. Serving has held {{ site.data.metrics.uptime.value }} {{ site.data.metrics.uptime.label }}, but the number I would actually defend in a design review is the freshness one. These posts cover what to measure, what deserves to wake a human, and which alerts I have deleted.
