---
layout: tag
title: Iceberg & the lakehouse
eyebrow: Topic
permalink: /writing/tags/iceberg-lakehouse/
tag: iceberg-lakehouse
description: "Table formats in practice: schema evolution, slowly changing dimensions, snapshot expiry, compaction cadence, and repairable history."
---

I have worked with Apache Iceberg since 2022. The table format matters because it shapes how safely a team can evolve schemas, correct history, compact small files, and expire snapshots. These notes focus on the portable decisions: slowly changing dimension patterns, maintenance cadence, metadata growth, and the recovery path you need before a routine correction turns into an expensive rewrite.
