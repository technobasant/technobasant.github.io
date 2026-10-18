---
layout: tag
title: Data modelling & dbt
last_modified_at: 2026-10-18
eyebrow: Topic
permalink: /writing/tags/data-modeling/
tag: data-modeling
description: "Star schemas, slowly changing dimensions and dbt: as-of joins, snapshots, contracts and tests, measured against data whose truth is known."
---

A model is a set of promises about what a number means: which version of a customer a payment belongs to, what grain a fact table has, which joins can drop or double a row. Most of those promises fail without an error. The totals reconcile and the keys resolve while revenue sits on the wrong plan. These notes build the models in dbt on data whose ground truth is known, so each design choice can be scored, and the tests are broken on purpose to see which ones notice.
