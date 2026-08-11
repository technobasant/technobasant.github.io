---
title: "Agents that write into governed tables"
description: "The gap between an agent demo and an agent platform is that outputs land in typed, audited records with fallbacks, not in a transcript nobody can query."
type: essay
tags: [ai-agents, data-quality]
toc: true
level: intermediate
---

An agent demo ends with text on a screen. A platform ends with a row in a table that has a schema, an owner, a retention policy, and a query that has to keep working next quarter. Everything hard about the second one is in that sentence, and almost none of it is prompting.

The draft will lay out the boundary I keep rebuilding: structured JSON contracts on every tool call and every model output, Pydantic models as the enforcement point so a malformed response fails at the edge instead of three joins downstream, an MCP tool registry so capabilities are declared rather than improvised, and tracing on every span so a wrong answer can be reconstructed rather than argued about.

Then the parts that only matter in production: what the fallback does when the model returns something unparseable twice in a row, how a low-confidence output gets written as a low-confidence output rather than dropped, and why the audit record needs the model version and the prompt hash in it. An agent that cannot explain where a number came from is not an analyst, it is a rumor with an API.
