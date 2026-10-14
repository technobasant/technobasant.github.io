---
title: "governed-agent: an analytics agent that can propose but never execute"
seo_title: "governed-agent — a LangGraph and MCP Agent With a Review Queue, Measured"
hook: "An agent that writes SQL and proposes refunds will sometimes be confidently wrong, and a system prompt is not a control"
description: "Open-source reference system: a LangGraph and MCP analytics agent whose answers pass schema, policy, grounding and review gates, measured on 54 questions."
date: 2026-10-14
last_modified_at: 2026-10-14
kind: open-source
pillar: ai-systems
related: [evalproof, platform-deployments, governed-ai-delivery]
order: 3
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "A 54-question golden set over a seeded warehouse of 9,000 orders; one local model, recorded and replayed in CI"
problem: "An analytics agent that can query data and propose refunds will be fluently wrong some of the time, and telling the model to behave does not stop a wrong answer or an injected instruction from becoming state."
decision: "Treat every model output as a candidate. It becomes state only after a typed schema, a policy, a deterministic grounding check and, for anything that would change something, a named reviewer; approved actions run once through an outbox."
repo: "https://github.com/technobasant/governed-agent"
flow: governed-agent
cover:
  base: "/assets/images/editorial-governed-agent-v1"
  width: 1600
  height: 900
  alt: "Schematic: 54 questions pass through schema, policy and grounding gates into three routes — 37 published with 3 wrong, 8 held for review with 3 wrong, 9 honest fallbacks with none wrong"
  caption: "The model got 48 of 54 right, but the figure a deployment answers for is the 3 wrong answers among the 37 that published without a person."
  link: "/writing/agent-measured-by-what-it-publishes/"
metrics: [agent_answer_match, agent_published_wrong, agent_unanswerable_admitted, agent_injection_actions]
stack: [Python, LangGraph, MCP, sqlglot, DuckDB, FastAPI, PostgreSQL, "Next.js", Ollama, OpenTelemetry, evalproof]
tags: [ai-agents, data-quality]
image: /assets/og/og-agents.png
image_alt: "AI agents in production — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

[Governed AI delivery](/work/governed-ai-delivery/) describes the operating model I use for AI features: generation is a candidate, and policy decides what becomes product state. That page has to stay at the level of principles, because the system it comes from is not mine to publish. This repository is the same idea built from scratch and in the open, small enough to read in an afternoon and complete enough to measure.

The agent answers questions about the warehouse of a fictional homewares retailer: orders, customers, products, refunds, inventory. It can also propose three actions: a refund, a supplier quality case, or a change to a metric's definition. It cannot perform any of them. The question the repository answers is not "can a model write SQL?" but "what reaches state without a person, and how often is it wrong?"

## Constraints

- **The model is the least trusted component.** Every guarantee below has to hold when it misbehaves, including when it reads instructions planted in the data.
- **A local model, so anyone can reproduce the run.** `qwen3:8b` under Ollama, temperature 0, seed 0, thinking off, on an Apple M5 with 24 GB. A hosted model is optional, not required.
- **Synthetic data, seeded.** 9,000 orders, 1,500 customers, 910 refunds, generated from a fixed seed so the golden set's answer keys can be computed by SQL, not written by a model.
- **CI cannot call a model.** It has to be deterministic and free, and it still has to fail when the model would see something new.

## Architecture

A LangGraph graph with code-owned edges: plan, act and tools in a loop, then draft, validate, policy, ground and route. The only way to the data is an MCP server with four tools. `query_warehouse` sits behind a parser-based SQL guard and a read-only DuckDB connection. `propose_action` checks a proposal against the data and records it, and nothing more.

Findings, proposals, reviews and an append-only audit log live in PostgreSQL behind a FastAPI service. A Next.js review UI shows each run's timeline, every SQL statement, and each number linked to the cell it came from. An approved action executes at most once, through a transactional outbox with an idempotency key. OpenTelemetry traces span the API, the agent and the MCP server.

## In the code

Every gate in the graph feeds this one function, and it is the only code that lets a finding publish without a person. Publication is the fall-through case, reached only when nothing blocked, every number was grounded and no rule asked for review, which is exactly how the three wrong answers that passed every check published themselves.

```python
# Even a "can't answer" goes to a person if it claims something was done or comes with a
# proposal: the text would be false, or the proposal needs a decision either way.
_SEEN_BY_A_PERSON = frozenset({"claims_side_effect", "proposes_action"})
# …
def route(finding: Finding | None, checks: Checks, violations: list[Violation]) -> Disposition:
    """Publish only what passed everything; hold what a person can still rescue."""
    if finding is None:
        # No finding at all: the model wrote something unparseable (rejected), or the run
        # ran out of time before it wrote anything (an honest "can't answer").
        return Disposition.REJECTED if checks.schema_errors else Disposition.UNANSWERABLE
    if any(v.severity == "block" for v in violations):
        return Disposition.REJECTED
    if finding.status == "unanswerable" and not any(
        v.code in _SEEN_BY_A_PERSON for v in violations
    ):
        return Disposition.UNANSWERABLE
    if checks.ungrounded or violations:
        return Disposition.HELD_FOR_REVIEW
    return Disposition.PUBLISHED
```
{: data-file="agent/ga_agent/policy.py" }

The policy rules that produce those violations sit above it in [agent/ga_agent/policy.py](https://github.com/technobasant/governed-agent/blob/main/agent/ga_agent/policy.py).

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| An explicit graph with code-owned edges | A loop around the model | Stopping, repair and routing are decisions the code makes and records | More code than a loop, and every new step is a graph change |
| MCP as the only path to data | The agent importing a database client | The agent's capabilities are the server's tool list; read-only is a parser plus a read-only connection, not a prompt | A guard written for one dialect; a second engine needs its own allow-list review |
| A deterministic grounding check | A second model judging support | A judge is a classifier that needs calibrating; a cell match gives the same verdict every run and links each number to its source | It proves provenance, not relevance: a real number under the wrong label passes |
| Review before execute, enforced by the data model | Telling the model to ignore injected text | Resistance is probabilistic; the absence of an execution path is not | Every proposal costs a person's decision, including the correct ones |
| CI replays a recorded real model | A live model in CI, or only a fake | Deterministic and free, and it exercises the real tools and checks | Any prompt change fails CI until the cassette is re-recorded against the live model |
{: .case-decisions aria-label="governed-agent decisions and trade-offs" }

## Results

One live run of 54 questions, with the full method in [MEASUREMENTS.md](https://github.com/technobasant/governed-agent/blob/main/MEASUREMENTS.md). The model answered **{{ site.data.metrics.agent_answer_match.value }}** correctly, including every count, total and lookup. That is the least useful number in the run.

The one a deployment answers for is what got through unreviewed: 37 findings were published automatically and **{{ site.data.metrics.agent_published_wrong.value }}** were wrong. Eight were held for review, three of them wrong and five right. Nine got the honest "I can't answer this from the data available", and all nine were right to.

The weakest property was admitting ignorance: **{{ site.data.metrics.agent_unanswerable_admitted.value }}** unanswerable questions were admitted as unanswerable. The strongest was injection: **{{ site.data.metrics.agent_injection_actions.value }}** planted instructions led to a proposal, and no action executed, because no execution path exists without approval. Median latency was 23.7 s per question, p95 46.1 s, with 1.1 tool calls on average.

Two live runs at temperature 0 gave byte-identical model replies, and CI replays them. A one-line change to the system prompt makes every case a cassette miss, and the evalproof gate fails the build. The analysis of where the six wrong answers went is in [the agent got 48 of 54 right; three of the wrong ones published themselves](/writing/agent-measured-by-what-it-publishes/).

## What the measurements refused to show

**The grounding check did not catch the published errors, and it was never going to.** Two of the three were a question the data cannot answer, met with a real figure from a real query. Delivery time came back as supplier lead time; conversion rate came back as the share of web orders delivered. Every number traced to a cell. The check did catch the two invented $0.00 answers.

**A fix to the check published more wrong answers.** Between the first and final runs the model's side was byte-identical, 167 of 167 exchanges, so every difference was the checks. Accepting a declared number found in a result, even when its calculation field held prose, released three right answers from review and two wrong ones into publication. The first pass's lower error count had been luck: those two were held for a formatting quirk, not because anything detected them.

**Not measured:** other models, thinking on, the API and UI under load, or a human reviewer's accuracy at the queue.

## What I'd do differently

**Hold answers whose question terms match no column.** Both published proxies answered a question about data that does not exist. A deterministic rule comparing the question's key terms with the schema is the cheapest next control, and the next thing to measure.

**Build authentication before the queue.** The reviewer's identity is a request header. The decisions are recorded with a name and a reason, but nothing proves who sent them. Reviewer auth and separation of duties are first on the roadmap.

**Make tampering detectable, not just inconvenient.** Triggers reject updates and deletes on the audit log, but a database superuser can drop a trigger. A hash-chained log, and real migrations in place of a schema created at startup, would turn a reference implementation into something I would run.
