---
layout: tag
title: Cost & FinOps
eyebrow: Topic
permalink: /writing/tags/cost-finops/
tag: cost-finops
description: "Where the money actually goes in a data platform, and the levers that move it: storage layout, compaction, instance shape, and retention nobody wanted."
---

The two largest bills I have moved were compute, cut {{ site.data.metrics.infra_cost.value }} in a Kubernetes migration, and object storage, cut {{ site.data.metrics.storage_cost.value }} by changing the table format and the compaction cadence underneath it. Neither came from a discount negotiation or an instance-type spreadsheet. They came from storage layout, file sizes, how often data gets rewritten, and retention rules that nobody wanted to own because owning them means telling someone their data is going away. These posts are about finding where the money is actually going in a data platform, and the small set of levers that move it.
