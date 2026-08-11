---
layout: tag
title: Kubernetes
eyebrow: Topic
permalink: /writing/tags/kubernetes/
tag: kubernetes
description: "Stateful data workloads on Kubernetes: autoscaling Spark, operators, resource shaping, and the cost model that actually made the migration worth doing."
---

I led the migration of a full data infrastructure onto self-managed Kubernetes and have run stateful data workloads on it since 2022 — Spark executors that scale with the queue, operators for stateful engines, and the resource requests and limits that decide whether a cluster is efficient or merely busy. It cut data-infrastructure spend by {{ site.data.metrics.infra_cost.value }}, but the honest version is that Kubernetes made nothing simpler: it made the complexity explicit, schedulable, and mine. These posts are about that trade, and about the failure modes that only appear once a stateful workload can be evicted.
