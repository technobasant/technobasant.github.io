---
layout: tag
title: AI agents in production
eyebrow: Topic
permalink: /writing/tags/ai-agents/
tag: ai-agents
description: "Agents whose outputs land in typed, audited tables rather than chat transcripts. LangGraph, CrewAI, Google-ADK, MCP, structured contracts and fallbacks."
---

I built and own an agent platform that answers analytics questions across {{ site.data.metrics.apps.value }} {{ site.data.metrics.apps.label }}, orchestrated with Google-ADK, LangGraph and CrewAI over MCP tools. It follows the same rule as every other producer on the platform: output lands in a typed, validated table or it does not ship, because a chat transcript cannot be joined, audited, diffed against last week or backfilled. Delivery time on recurring analytics dropped {{ site.data.metrics.analytics_delivery.value }}, and almost none of that came from prompt wording — it came from tool design, structured output contracts, evaluation, and having a defined thing to do when the model is confidently wrong.
