---
layout: tag
title: Cost & FinOps
eyebrow: Topic
permalink: /writing/tags/cost-finops/
tag: cost-finops
description: "Where the money actually goes in a data platform, and the levers that move it: storage layout, compaction, instance shape, and retention nobody wanted."
---

The interesting part of platform cost is not the invoice total; it is the workload behavior that produced it. File sizes, rewrite frequency, storage layout, idle capacity, and retention policy usually matter more than a discount negotiation. These notes show how I trace a bill back to engineering choices, change one lever at a time, and keep the performance and recovery consequences visible beside the savings.
