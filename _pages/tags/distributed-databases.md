---
layout: tag
title: Distributed databases
eyebrow: Topic
permalink: /writing/tags/distributed-databases/
tag: distributed-databases
description: "Quorum, sharding, failover and backup across MongoDB, ScyllaDB, Redis, MariaDB/Galera and Solr — measured on a rig rather than quoted from a docs page."
---

Every distributed database advertises high availability, and the claim is usually true in a sense that will not help you at two in the morning. So I built a rig — MongoDB, ScyllaDB, SolrCloud, MariaDB with Galera, Redis in both Cluster and Sentinel modes, and PostgreSQL — and killed the primary in each while measuring what actually happened and how long it took. {{ site.data.metrics.lab_scenarios.value }} {{ site.data.metrics.lab_scenarios.label }}; Redis Sentinel promoted a replica to writable in {{ site.data.metrics.lab_redis_promotion.value }}. Everything in this topic is a number from that rig, published with the test plan attached so you can reproduce it or disagree with it.
