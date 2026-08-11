---
layout: tag
title: Data quality & contracts
eyebrow: Topic
permalink: /writing/tags/data-quality/
tag: data-quality
description: "Validation, reconciliation, quarantine and tolerant readers — for when the producer is twenty-five thousand apps on SDK versions you cannot recall."
---

My producers are {{ site.data.metrics.apps.value }} {{ site.data.metrics.apps.label }} running SDK versions nobody can recall, which rules out the standard advice of fixing the problem upstream. What is left is work at the boundary: null, type, range and referential checks on the streaming path, quarantine rather than rejection so bad records stay inspectable, reconciliation jobs that compare what arrived against what should have, and readers tolerant enough to survive a field appearing or changing type mid-release. {{ site.data.metrics.data_quality.value }} {{ site.data.metrics.data_quality.label }} — the interesting engineering lives entirely in what happens to the remainder.
