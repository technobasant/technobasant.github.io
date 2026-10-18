---
layout: tag
title: Airflow & orchestration
last_modified_at: 2026-10-18
eyebrow: Topic
permalink: /writing/tags/orchestration/
tag: orchestration
description: "Scheduling that survives re-runs and backfills: data intervals, idempotent loads and the Airflow defaults that change between versions."
---

A scheduler's job looks simple until a day has to be re-run, a backfill goes in the wrong order, or an upgrade changes what a schedule means. Most of the failures here end with every task green: the load ran, it just asked for the wrong rows. These notes run real DAGs over data whose correct answer is known and count what each design loses.
