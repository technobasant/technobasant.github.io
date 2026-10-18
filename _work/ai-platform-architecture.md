---
title: "ai-platform-architecture: AI on governed data, every decision tied to a measurement"
seo_title: "AI platform reference architecture: governed agents, evaluation gates, OWASP LLM threat model"
hook: "Thirteen decisions for putting AI features on a company's data, the measurements behind them, and the three targets the labs do not meet yet"
description: "A reference architecture for AI features on governed data: 13 decisions backed by lab results, an evaluation gate, an OWASP LLM threat model and a cost model."
date: 2026-10-18
last_modified_at: 2026-10-18
kind: open-source
pillar: ai-systems
related: [governed-agent, evalproof, data-platform-architecture]
order: 5
role: "Author"
org: "Open source"
period: "2026"
team: "One person"
scale: "13 decision records, 27 measured figures from six public repositories, an evaluation design, an OWASP Top 10 for LLM Applications (2025) threat model, quality targets, runbooks, and a cost model across nine models and three GPU instances"
problem: "AI architecture is usually drawn as boxes around a model: retrieval, an agent, a vector store. What decides whether a feature is safe to put on a company's data is less visible: what the model can reach, what becomes state without a person, how a change is judged, and what an answer costs."
decision: "Write the AI layer as decision records whose evidence is generated from results measured in public labs, state the targets the labs do not meet rather than lowering them, map the OWASP LLM risks to controls and tests, and price every feature before launch."
repo: "https://github.com/technobasant/ai-platform-architecture"
flow: ai-platform-architecture
cover:
  base: "/assets/images/editorial-ai-platform-architecture-v1"
  width: 1600
  height: 900
  alt: "Table of five hosted models with the cost of one help-centre answer and the answers per hour a single-L40S instance must serve to cost less, from 196 against Claude Sonnet 5 to 3,918 against GPT-6 Luna"
  caption: "The cheaper the hosted model, the more a GPU of your own must serve before it pays."
  link: "/writing/ai-answer-cost-and-self-hosting/"
metrics: [aipa_decisions_backed, agent_published_wrong, agent_injection_actions, evalproof_noise_gate, aipa_self_host_break_even]
stack: ["Architecture decision records", MCP, LangGraph, "LLM evaluation", "OWASP LLM Top 10", pgvector, Feast, Python, Mermaid, "GitHub Actions"]
tags: [ai-agents, applied-ml, cost-finops]
image: /assets/og/og-agents.png
image_alt: "AI systems on governed data — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

The AI labs on this site each answer one question: does an agent publish wrong answers on its own, can an evaluation gate tell a regression from noise, does filtered vector search return what it was asked for, does a model learn from the future. An AI architect's job is the layer above them: how those answers combine into features a company can put on its own data, and what they cost.

[ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture) is that layer for the same fictional SaaS business as [data-stack-lab](/work/data-stack-lab/), sitting on the platform in [data-platform-architecture](/work/data-platform-architecture/). It covers five features: an analyst over governed data, a help-centre assistant, triage of short free text, scoring models, and category trends from classifier output.

## Constraints

Everything is assembled from public labs on synthetic and public data, not from any employer's or client's system. The language-model labs ran small local models (Qwen3 1.7B and 8B through Ollama), so the methods transfer to other models while the rates would not. The cost model rests on list prices and assumed token counts; no feature's bill and no inference server's throughput were measured, and the decision that depends on them is marked Proposed.

## Architecture

- **Thirteen decision records**: one typed boundary to data; outputs that become state only after checks and, for side effects, a person; abstention as a measured answer; a paired evaluation gate with latency and cost budgets; judges calibrated and audited; retrieval chosen by filtered recall; labelling distinct strings by cluster and margin; corrected counts from classifiers; point-in-time features; promotion on outcomes; one model gateway with replay and budgets; canary releases; a cost per answer before launch.
- **Evaluation**: answerable, unanswerable, adversarial and boundary cases; deterministic checks before judges; the gate; outcome monitoring after release.
- **Threat model**: the OWASP Top 10 for LLM Applications (2025), each risk mapped to the controls in this design and to what has been tested, with the untested gaps ranked.
- **Quality targets** with the measured value next to each, including the three that are not met.
- **Runbooks**: changing a prompt or model, changing the judge, a reported wrong answer, a provider outage, a spend spike, a review backlog, an injection.
- **A model and cost guide** pricing two features on nine current models, and the request rate at which a GPU instance of your own costs less than the API.

## In the code

The cost model is deliberately small. Its one non-obvious output is the self-hosting break-even: an instance's hourly price divided by the API's price per request. That is the request rate a dedicated GPU must sustain before it is cheaper, before anyone asks whether it can.

```python
break_even = {
    gpu: {
        "usd_per_hour": g["usd_per_hour"],
        "requests_per_hour": {m: round(g["usd_per_hour"] / answer_cost(models[m], feature)) for m in models},
    }
    for gpu, g in prices["gpus"].items()
}
```
{: data-file="cost/model.py" }

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Models reach data only through typed tools | a database connection for the agent | the model's judgment would be the access control | a tool and a schema per capability |
| Nothing with a side effect runs without a person | autonomous actions | a wrong action costs more than a wrong answer | a review queue to staff |
| Gate on paired significance, budgets separate | pass-rate delta against a tolerance | a gate that fails on noise is switched off | small sets cannot see small regressions, and the gate says so |
| Keep unmet targets as targets | lower them to what the labs reached | a target describes what the business needs | the README shows three misses |
| Price per answer before launch | watch the invoice | cost varies a hundredfold by model alone | assumed token counts until the gateway measures them |

## Results

**Twelve of thirteen decisions are backed by measured results.** Among them: {{ site.data.metrics.agent_injection_actions.value }} planted instructions led to an action; a 4.8-point drop that the paired gate correctly called noise at {{ site.data.metrics.evalproof_noise_gate.value }}; and filtered vector search that returned 3.9 of 10 rows until the engine's iterative scan was used. All 27 figures are in the repository's [EVIDENCE.md](https://github.com/technobasant/ai-platform-architecture/blob/main/EVIDENCE.md).

**Three targets are not met.** {{ site.data.metrics.agent_published_wrong.value }} answers that passed every check and published without review were wrong, against a target under 1%; 4 of 8 unanswerable questions were declined, against 7 of 8; accuracy was 48 of 54, just under 90%. The architecture keeps them as targets; they are what the next iteration of the checks is measured against.

**What an answer costs.** The same help-centre answer costs from $0.0005 to $0.0475 across the nine models priced. A single-L40S instance costs less than the API above {{ site.data.metrics.aipa_self_host_break_even.value }} answers an hour against Claude Sonnet 5 and GPT-6 Luna respectively. The reasoning is in [the write-up](/writing/ai-answer-cost-and-self-hosting/).

## What went wrong

**The first README miscounted its own misses.** It listed two unmet targets; 48 of 54 is 88.9%, under the 90% accuracy target, so there were three. The table and the text now say three.

**A cover headline claimed more than the arithmetic.** "A GPU pays off only against the bigger models" assumed that one instance cannot serve 3,918 answers an hour, which nobody measured. It now says what the numbers show: the cheaper the hosted model, the more a GPU of your own must serve.

**A cost comparison mixed volume tiers.** A draft contrasted $33 a month with $33,000; the second figure was a tier ten times larger. The same feature at the same volume ranges from $33 to $3,300.

## What I'd do differently

**Close the three gaps in the labs.** The grounding check and abstention are where the governed agent is weakest; the next change to it should be judged against these targets.

**Write the adversarial suites the threat model ranks first:** tenant isolation, injection through retrieved documents, and spend caps under load.

**Measure what the cost model assumes.** Token counts per call from a running gateway, and the serving rate of an open model on one GPU instance, would turn the break-even from arithmetic into a decision.

The decisions, documents, cost model and checks are in [ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture).
