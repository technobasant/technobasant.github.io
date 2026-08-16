---
layout: tag
title: Apache Spark
last_modified_at: 2026-08-11
eyebrow: Topic
permalink: /writing/tags/spark/
tag: spark
description: "Practical Spark work: shuffle diagnosis, executor sizing, partitioning, skew, and the evidence to collect before touching a configuration."
---

I have worked with Spark since 2020. The useful diagnosis usually starts with the stage graph, skew, spill, partition size, and one stubborn task—not with a copied configuration checklist. These notes focus on what I measure before changing a knob, how I separate a scheduling problem from a data-layout problem, and how to make a performance claim reproducible on data that can be shared safely.
