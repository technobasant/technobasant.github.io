---
layout: tag
title: Kubernetes
last_modified_at: 2026-08-11
eyebrow: Topic
permalink: /writing/tags/kubernetes/
tag: kubernetes
description: "Stateful data workloads on Kubernetes: scheduling, operators, resource shaping, disruption, and the operational price of explicit control."
---

I have operated data workloads on Kubernetes since 2022. Kubernetes does not make stateful systems simple; it makes scheduling, disruption, resource pressure, and ownership explicit. These notes examine that trade through mechanics you can reproduce: requests and limits, operators, eviction, autoscaling signals, rollout safety, and the difference between a busy cluster and an efficient one.
