---
layout: tag
title: Iceberg & the lakehouse
eyebrow: Topic
permalink: /writing/tags/iceberg-lakehouse/
tag: iceberg-lakehouse
description: "Table formats in production: schema evolution, slowly-changing dimensions at petabyte scale, snapshot expiry, compaction cadence, and the storage bill."
---

I moved storage to Apache Iceberg in 2022 and have run it at multi-petabyte scale since, including slowly-changing dimensions over years of history. The table format is the component that decides whether a schema change is a five-minute pull request or a quarter-long migration, and whether correcting a mistake in last March's data costs you a rewrite of last March. Storage cost fell {{ site.data.metrics.storage_cost.value }} after the move, but that is not why I would do it again — snapshot isolation and safe schema evolution are. These posts cover SCD patterns that hold at scale, compaction and expiry cadence, and the metadata overhead nobody warns you about until your query planner is reading thousands of manifests.
