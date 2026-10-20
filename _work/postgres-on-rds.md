---
title: "Managed or self-run PostgreSQL: a capacity plan and an RDS fleet"
seo_title: "Consulting Case Study — PostgreSQL Capacity Planning and an Amazon RDS / Aurora Fleet"
hook: "A capacity plan that had to choose between a managed service and running PostgreSQL yourself, and a fleet of RDS and Aurora databases tuned and failover-tested: the same rule decided both."
description: "Consulting case study: a PostgreSQL 16 capacity plan with the managed-or-self-run decision, and an optimisation programme for a fleet of RDS and Aurora databases with failover tests."
date: 2026-10-20
last_modified_at: 2026-10-20
kind: consulting
pillar: database-lifecycle
order: 2
role: "Consultant — PostgreSQL capacity, operations and platform choice"
org: "Two consulting clients (confidential)"
team: "Remote, with each client's engineering team"
scale: "Application databases for web products and services, one PostgreSQL 16 system and a fleet of RDS and Aurora instances"
problem: "One client had to plan PostgreSQL 16's capacity and decide whether to run it as a managed service or on its own servers; another ran a fleet of RDS and Aurora databases that needed tuning and proof that failover worked."
decision: "Default to managed PostgreSQL for ordinary applications, since it costs about the same as running it yourself and brings HA, configuration and monitoring; run it yourself only for extensions the service lacks or superuser access; and test failover rather than assume it."
stack: [PostgreSQL, "Amazon RDS", "Amazon Aurora", PgBouncer, AWS]
tags: [postgres, observability-slo]
image: /assets/og/og-postgres.png
image_alt: "Consulting case study: PostgreSQL capacity planning and an RDS fleet — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Two engagements asked the question most PostgreSQL decisions start with, from opposite ends.

**A capacity plan.** A client running PostgreSQL 16 needed a plan for its growth and, with it, a decision: run the database as a managed service, or on servers of its own. The work also traced a performance problem to its root in the background writer, the PostgreSQL process that flushes changed pages to disk.

**A fleet.** Another ran its applications on a fleet of Amazon RDS and Aurora databases. The work was an optimisation programme across the fleet, connection pooling benchmarked with PgBouncer, and failover tests, so that the availability the services relied on was demonstrated rather than assumed.

## My role

I planned capacity, found the root cause and set out the managed-or-self-run decision on the first engagement; on the second I ran the optimisation programme, the PgBouncer benchmarks and the failover tests with the client's team. The clients, their data and their code stay private; this page describes the problems and the decisions.

## The rule both came down to

For an ordinary web application or a single service, the comparison is closer than it looks on a price list. Running PostgreSQL on EC2 yourself and running it on RDS came out at about the same cost. What differs is everything around the database:

| | Managed (RDS, Aurora) | Self-run (EC2 or own servers) |
|---|---|---|
| High availability | Multi-AZ failover, operated by the provider | yours to build, test and keep working |
| Backups and point-in-time recovery | built in | yours to run and to restore |
| Configuration and upgrades | parameter groups, managed minor and major upgrades | yours |
| Monitoring | built in, with performance insight | yours to assemble |
| Extensions | the provider's list | any |
| Superuser access | no | yes |

So the rule: **managed by default; self-run only when an extension the service does not offer, or full superuser access, is a requirement.** When it is, high availability, backup and recovery become your work, and they are real work.

## Measured behind the decisions

The client systems' figures stay with the clients. What self-running high availability involves is measured in labs:

- In [postgres-ha-lab](/work/patroni-ha-backup-lab/), a Patroni cluster with etcd and pgBackRest over mutual TLS promoted a new leader {{ site.data.metrics.lab_patroni_promotion.value }} after the old one was killed, rebuilt a replica from backup in {{ site.data.metrics.lab_replica_rebuild.value }}, and recovered {{ site.data.metrics.lab_pitr_recovery.value }} rows by point-in-time restore: the machinery a managed service already includes.
- In [the multi-engine HA lab](/work/multi-engine-ha-lab/), {{ site.data.metrics.lab_scenarios.value }} failover scenarios passed across six engines, because each one was rehearsed, which is the point of failover tests on a managed fleet too.

## Lessons that carry over

**A failover nobody has triggered is a hope.** Managed services make failover easy to configure; only a test shows what the application does during it, which connections drop and how long the pool takes to recover.

**Root causes hide in settings.** A database that slows down is often doing exactly what its configuration asks; the background writer is one of the places to look before buying a larger instance.

**Price the work, not the instance.** The instance prices were close; the difference was who builds, tests and runs high availability, backups and upgrades.

When an application outgrows one PostgreSQL server altogether, the next step is in [the Citus case study](/work/postgres-scale-out-citus/), and the wider choice of store is in [the decision guide](/writing/choosing-where-the-data-lives/).
