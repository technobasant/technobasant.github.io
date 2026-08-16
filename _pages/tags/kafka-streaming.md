---
layout: tag
title: Kafka & streaming
last_modified_at: 2026-08-11
eyebrow: Topic
permalink: /writing/tags/kafka-streaming/
tag: kafka-streaming
description: "Ingestion that survives replay, late events, duplicate deliveries and producers you do not control. Kafka, Kinesis, Structured Streaming, CDC."
---

Streaming systems have to assume duplicates, late events, partial producer upgrades, and replays. I have built and operated ingestion and change-data-capture paths across several technologies, but the transferable lessons live above the brand names: idempotent writes, explicit event-time policy, backfills that do not double-count, schema compatibility, and a repair path that works while new traffic is still arriving.
