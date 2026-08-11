---
layout: tag
title: PostgreSQL
eyebrow: Topic
permalink: /writing/tags/postgres/
tag: postgres
description: "Replication, point-in-time recovery, promotion, connection limits, and the version-upgrade surprises that only ever show up under production traffic."
---

PostgreSQL is the database I have used longest — since 2017 — and still my default for anything transactional, including the OLTP half of ClickHomes. Most of what I know about it comes from the operational side rather than the query side: how far behind a standby actually falls under write pressure, point-in-time recovery you have rehearsed instead of documented, promotion while traffic is still arriving, connection limits meeting an application that opens a pool per worker, and major-version upgrades. On my failover rig, PostgreSQL 18 streaming replication held a replay lag of {{ site.data.metrics.lab_pg_replay_lag.value }} — measured on the rig, not quoted from a release note.
