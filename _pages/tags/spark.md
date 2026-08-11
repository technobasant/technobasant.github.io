---
layout: tag
title: Apache Spark
eyebrow: Topic
permalink: /writing/tags/spark/
tag: spark
description: "Running Spark at ten terabytes a day: shuffle tuning, executor sizing, Kubernetes scheduling, and what it costs when you get partitioning wrong."
---

I have run Spark since 2020, and almost always self-managed on Kubernetes rather than on somebody else's runtime — which means executor sizing, shuffle behavior and scheduling are my problem rather than a support ticket. At {{ site.data.metrics.daily_volume.value }} a day the failure modes stop being interesting and start being expensive: a skewed join key that spills to disk, a partition count that was correct when the table was a tenth of its current size, an autoscaler adding executors to a stage bound by one straggling task. These posts are about that layer — what I measure before touching a config, which knobs turned out not to matter, and the difference between a job that is slow and a job that is slow because it is spilling.
