---
layout: tag
title: ClickHouse
eyebrow: Topic
permalink: /writing/tags/clickhouse/
tag: clickhouse
description: "Column-store analytics: MergeTree design, partition and ordering keys, materialized views, and keeping system log tables from quietly eating the disk."
---

I have worked with ClickHouse since 2021, including in production systems and independent product experiments. It rewards careful ordering keys, partitions, and read-shaped models, then punishes weak choices quietly through merge pressure, part counts, and disk growth rather than a clean error. These notes focus on reproducible mechanics: MergeTree design, materialized views as incremental aggregation, query evidence, and the maintenance that keeps system logs from becoming the largest workload.
