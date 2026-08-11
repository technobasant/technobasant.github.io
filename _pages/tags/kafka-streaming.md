---
layout: tag
title: Kafka & streaming
eyebrow: Topic
permalink: /writing/tags/kafka-streaming/
tag: kafka-streaming
description: "Ingestion that survives replay, late events, duplicate deliveries and producers you do not control. Kafka, Kinesis, Structured Streaming, CDC."
---

The ingestion path I operate takes {{ site.data.metrics.daily_events.value }} {{ site.data.metrics.daily_events.label }} from mobile SDKs I do not control and cannot force anyone to upgrade. That single fact sets the design for everything downstream: the producer will send duplicates, events that arrive hours late, and payload shapes from a release two years old, and none of that is a bug you get to fix at the source. I have built this path twice — Kinesis into Spark Structured Streaming, then Kafka into Spark on Kubernetes — plus change data capture out of operational databases. These posts cover idempotent loads, replay and backfill that do not double-count, watermarking choices, and why the right answer to a late event is usually a policy decision rather than a code change.
