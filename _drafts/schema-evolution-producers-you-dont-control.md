---
title: "Schema evolution when you don't control the producers"
description: "A schema registry assumes you can reject a bad producer. You cannot when the producer is twenty-five thousand apps on SDK versions you have no way to recall."
type: essay
tags: [data-quality, kafka-streaming, iceberg-lakehouse]
toc: true
level: advanced
---

"Just use a schema registry" is good advice for a system where the producers are services you deploy. It quietly assumes the ability to reject: a producer sends something incompatible, the registry says no, someone fixes the producer. That loop does not exist when the producer is a mobile SDK embedded in twenty-five thousand apps, shipped through two app stores, on versions going back years, with no recall mechanism.

The draft will make the case for tolerant readers as the default posture — parse what you understand, preserve what you do not, never fail the batch on an unknown field — paired with explicit data contracts that state which fields are load-bearing and which are advisory.

Then the storage side: Apache Iceberg's schema evolution by field id rather than by position, so a rename is not a rewrite and an added column is not a migration; and a quality gate that fails loudly on the fields that matter while quarantining the rest, so a producer regression shows up as a named alert on a named dataset instead of a silent null rate that someone notices in a dashboard a month later.
