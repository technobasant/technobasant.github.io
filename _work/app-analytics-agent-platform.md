---
title: "The App Analytics Agent Platform"
hook: "A multi-agent analytics layer across 25K+ apps that writes its answers into governed tables"
description: "A multi-agent analytics layer over 25,000+ integrated apps: typed MCP tools, LangGraph orchestration, and answers that land in governed, audited tables."
kind: production
order: 2
featured: true
role: "Senior Data Engineer"
org: "UXCam"
period: "2024 – present"
team: "Owned end to end by me; architecture and design run with the Product Owner, Chief Design Officer and the analyst group"
scale: "25,000+ integrated mobile apps; 1M+ session videos a month through the retrieval path"
stack: [Google-ADK, LangGraph, LangChain, CrewAI, MCP, Milvus, Trino, ClickHouse, Apache Iceberg, MLflow, LangSmith, Langfuse, Opik]
metrics: [analytics_delivery, analyst_effort, apps]
tags: [ai-agents, rag, data-quality]
image: /assets/og/og-default.png
image_alt: "A planner agent calling typed MCP tools over the serving layer, with validated output written into governed tables"
---

## Context

UXCam collects behavioral data from **25,000+ integrated mobile apps**. Collection was never the bottleneck. Turning that data into an answer required a human who knew both the product and the schema, and there are far fewer of those than there are questions.

The shape of the problem was a queue. Why did a checkout funnel drop six points in Brazil last week. What does account health look like across forty apps before a renewal call. Does this crash spike track an SDK version. Each is a few hours of analyst work, most of it identical to the last time someone asked. The queue grew faster than the analyst group could, and the questions that did not make the cut were not asked at all.

The obvious 2024 answer was to put a language model in front of the warehouse. I did not want to do that, and the reason is the whole design. An analyst's answer is a *record*: you can go back to it, see the query, disagree with the filter, re-run it. A chat response is not a record. If the platform's output is a transcript, then six months later nobody can say why the number was what it was, and the number quietly stops being trusted. So the requirement I set was that every agent answer lands in a typed, versioned table alongside the inputs that produced it.

## Constraints

**No raw model output on a production path.** Anything a customer or an internal decision touches has to be reproducible from stored inputs. That rules out the whole category of designs where the model composes the final number.

**No new warehouse.** The agents read through the serving layer that already existed — Trino, ClickHouse, the Iceberg gold tables. A separate store for the AI features would have created a second version of every metric, which is exactly the failure I was trying to avoid.

**Cost per answer is a real line.** Tokens are metered, and an agent that scans a wide table and stuffs rows into a prompt is expensive in two directions at once. The budget forced a design where the model reasons over aggregates and never over raw event rows.

**Latency.** Analysts wait, and product surfaces have a patience budget measured in seconds. A design that took ninety seconds to reason its way to an answer would have been correct and unused.

**Tenant isolation and GDPR.** Session data and replay artifacts carry personal-data risk. Retrieval has to be app-scoped by construction, not by a filter the model is asked to remember. There is no version of "the prompt tells it not to cross tenants" that survives review.

**No ML platform team, and non-determinism only in the path.** Whatever I build, I operate, on top of the data platform underneath it. And the same question with the same inputs must produce the same stored answer — the model may take different routes, the row it writes may not vary.

## Architecture

```text
   request (analyst UI, product surface, scheduled report)
                          |
                          v
                  LangGraph orchestrator
        plan -> retrieve -> compute -> validate -> persist
                          |
        +-----------------+------------------+
        v                 v                  v
  role-shaped        MCP tool layer      retrieval
  sub-agents      (typed, permission-     (Milvus)
  (CrewAI /        checked, versioned)        |
   Google-ADK)          |                     |
        |               v                     |
        |     Trino / ClickHouse /            |
        |     Iceberg gold tables             |
        |               |                     |
        +-------+-------+---------------------+
                v
          validator: output schema check,
          freshness gate on every source table,
          deterministic fallback per step
                |
                v
       governed output tables
       run_id | input_hash | tool_trace | schema_version | answer
                |
                v
   tracing: LangSmith / Langfuse / Opik · registry: MLflow
```

**Orchestration.** LangGraph holds the state machine: plan, retrieve, compute, validate, persist — each a node with an explicit failure edge. I chose a graph over an agent loop because I need to point at where a request was when it went wrong, and "somewhere in the loop" is not an answer.

**Tools, not SQL.** Agents call typed tools over MCP: `funnel_for_app`, `retention_cohort`, `crash_rate_by_version`. Each has a schema, a permission check on the calling context, and a fixed query behind it that a human reviewed. The model chooses the tool and its arguments and explains the result; it does not invent the computation. For the genuinely open-ended parts — deciding which of forty apps in an account is worth writing about — CrewAI and Google-ADK role-shaped agents sit inside the graph, not around it.

**Validate, then persist.** Nothing is written until the structured output validates against its schema *and* every source table passes its freshness gate. The row that lands carries the answer plus `run_id`, a hash of the resolved inputs, the tool trace and the schema version, so the same question with unchanged inputs returns the same row rather than a new inference. That makes the output joinable, auditable and cacheable at once.

**Observability.** LangSmith, Langfuse and Opik carry prompt traces and regression detection against a frozen question set; MLflow handles the model and experiment side. Traces are the only way to answer "why did this run choose that tool," which is the first question in every investigation.

### Video retrieval on Milvus

Session replay is the corpus where a language model earns its keep, because the signal is in what a user did on a screen and no aggregate table captures it. The retrieval path processes **1M+ session videos a month**: sessions are segmented, embedded and written to Milvus with app-scoped partitions and metadata filters for screen, SDK version and time bucket. App scoping is enforced at the partition level rather than as a query filter, so a retrieval cannot cross a tenant boundary even if the calling code is wrong.

Two things here matter more than the embedding model. TTL, because a vector store over a corpus growing by a million items a month becomes a landfill unless something expires — older sessions age out and are re-embedded on demand. And metadata filters, because retrieval quality at this size is dominated by how well you narrow the candidate set before similarity search, not by how good the search is.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost us |
|---|---|---|---|
| Agents call typed MCP tools; they never write SQL | Text-to-SQL against the serving layer | A bounded, reviewed tool surface is testable, permission-checkable and cost-predictable. Text-to-SQL is none of those at 25,000 tenants, and its failure mode is a plausible wrong number rather than an error. | Every genuinely new question needs a new tool. The catalog is a product now, with a backlog and a deprecation policy. We trade coverage for trust, and sometimes coverage is what someone needed. |
| Persist every answer as a typed row with `run_id`, input hash and tool trace | Return the answer to the UI and move on | Answers become auditable, joinable and idempotent. Re-asking an unchanged question is a lookup, not an inference — which is also where a good share of the cost saving lives. | Schema churn driven by prompt design. Changing what an agent produces is now a migration, with all the ceremony that implies. |
| LangGraph for orchestration, CrewAI and Google-ADK for role-shaped sub-agents | One framework everywhere | Explicit state machine where determinism matters, higher-level abstractions where the work is exploratory. Forcing either style to do the other's job produced worse code both times I tried. | Two mental models in one codebase. Onboarding is slower and framework upgrades hit us twice a year instead of once. |
| A deterministic fallback for every step | Fail the request | A late analytics answer is a useless one. A degraded answer, flagged as computed without model assistance, is still an answer. | Fallback paths run rarely and therefore rot. They have to be exercised on a schedule — ongoing work nobody enjoys. |
| Milvus partitions per app, plus a TTL on the hot index | One flat index over everything | Tenant isolation by construction, and a bounded index. Retrieval quality on a corpus growing by a million videos a month depends on narrowing before searching. | Recall on older sessions drops once they age out, so we needed a re-embed-on-demand path. It is slow, and users notice when they hit it. |
| Freshness gate on every source table before an answer is written | Trust the pipeline | The worst output this system can produce is a confident number from stale data, and it looks exactly like a good one. | Requests fail during incidents that could have been served from slightly old data. Deliberate, and it generates complaints. |

The design discussion where I was most outnumbered was the tool catalog. The reasonable position on the other side, argued from product and design, was that a bounded catalog caps what users can ask — and the whole appeal of a language model is answering the question you did not anticipate. That is true. I still think the trade is right, because the first time this system produces a confident wrong number in front of a customer, everything else it has ever said becomes suspect. But it is a real cost, and the tool backlog is where it shows up.

## Results

Median turnaround on recurring analytics requests dropped **60%** against the pre-agent request queue, measured over two quarters. The word *recurring* is doing real work there. Genuinely novel questions still go to a human, and should. What moved was the large body of requests structurally identical to something asked the week before.

Manual analyst effort on recurring reporting fell **75%**, measured as analyst hours on that reporting before and after the platform, across 2024–2025. This is the number I would defend hardest, because it has the clearest counterfactual: the reports still exist, the same people are accountable for them, and the hours are logged.

The platform covers the full estate of **25,000+ integrated apps** — apps with an active SDK integration, not paying customers. Two numbers are deliberately absent. Earlier versions of my CV claimed an engagement-insight lift and a personalization lift from this work; I cut both, because too many things changed in the same window for me to attribute a percentage to this system honestly.

## Running it

**SLOs.** p95 answer latency on the interactive path. Tool error rate split by tool, because a single bad tool is invisible in the aggregate. Eval pass rate on the frozen question set, checked on every promote. Cost per answer, weekly — the SLI that catches a prompt change which quietly doubled the context.

**On-call.** Same rotation as the data platform. Two classes page: the validator rejecting a sustained share of outputs, and the eval suite failing after a promote. Everything else goes to a dashboard.

**Three failure modes we actually see:**

*Model provider degradation.* Latency climbs or requests time out, usually without an error saying so. The runbook is not "wait": a per-step timeout trips into the deterministic fallback, and the on-call action is to confirm the fallback is engaging and answers are flagged as degraded. The failure that matters is the fallback *not* engaging, because then requests hang.

*A stale table behind a healthy-looking tool.* An upstream job fails, the gold table stops updating, and the tool keeps returning valid rows that happen to be a day old. Runbook: when the freshness gate starts rejecting, do not disable the gate — fix the upstream job. Disabling it to unblock users converts a visible outage into an invisible correctness problem, which is a much worse trade than it feels like at 2am.

*Retrieval collapse after a compaction or TTL pass.* A partition ends up empty and the agent answers from almost nothing, which reads as confident because low-context answers usually do. Runbook: check partition row counts against the expected profile before blaming the model, then trigger the re-embed path for that app and window. Detection here is the weakest part of the platform and I know it.

## What I'd do differently

**I designed the persistence schema after the agents; it should have been first.** I built the reasoning layer, got it working, then asked what shape its output should take. That is backwards. The output contract is the interface to the rest of the platform and should have constrained prompt design rather than being retrofitted around it. It cost two schema migrations and left the first version of the table carrying fields that exist only because an early prompt happened to produce them.

**I did not set a cost-per-answer budget for the first few months.** I tracked total spend, which is the wrong granularity: it hides which path is expensive and rewards nobody for making one cheaper. By the time I instrumented per-answer cost, two tool paths had grown context in ways that would never have shipped if the number had been on a dashboard from week one.

**I ran too many frameworks at once.** Google-ADK, LangChain, CrewAI, LangGraph and MCP each earn their place somewhere and I can defend all of them individually. Collectively they are more surface area than one person should maintain. Starting again I would be strict about the orchestration layer and the tool protocol and treat everything else as replaceable, rather than letting each proof-of-concept leave its framework behind in production.
