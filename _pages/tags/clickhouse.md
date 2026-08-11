---
layout: tag
title: ClickHouse
eyebrow: Topic
permalink: /writing/tags/clickhouse/
tag: clickhouse
description: "Column-store analytics: MergeTree design, partition and ordering keys, materialized views, and keeping system log tables from quietly eating the disk."
---

I have run ClickHouse since 2021 on both sides of the fence — as an analytics serving engine inside a platform answering {{ site.data.metrics.query_volume.value }} {{ site.data.metrics.query_volume.label }}, and as the OLAP half of a deliberately split two-database design on a personal project. It rewards you enormously for choosing the right ordering key and partitioning scheme, and punishes you quietly when you do not: the symptom is merge pressure, part counts and disk, not an error message. These posts cover MergeTree design, materialized views used as incremental aggregation rather than as convenience, and the operational hygiene that keeps a cluster from filling its own disk with its own logs.
