---
layout: tag
title: Data quality & contracts
eyebrow: Topic
permalink: /writing/tags/data-quality/
tag: data-quality
description: "Validation, reconciliation, quarantine and tolerant readers — practical boundaries for imperfect producers and changing schemas."
---

“Fix it upstream” stops being useful advice when producers update at different speeds or belong to another team. Then the boundary has to do real work: null, type, range, and referential checks; quarantine that keeps bad records inspectable; reconciliation against expected volume; and readers that can survive a field arriving late or changing shape. These notes are about making failure visible without turning every imperfect record into data loss.
