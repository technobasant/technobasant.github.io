---
title: "What an AI answer costs, and when a GPU of your own pays for itself"
seo_title: "LLM cost per answer and self-hosting break-even, from October 2026 list prices"
description: "One help-centre answer costs $0.0005 to $0.05, by model. A GPU of your own beats Claude Sonnet 5 at about 196 answers an hour, but GPT-6 Luna at 3,918."
date: 2026-10-18 18:30:00 +0545
last_modified_at: 2026-10-20
type: essay
pillar: ai-systems
tags:
  - ai-agents
  - cost-finops
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - LLM cost
  - self-hosting language models
  - AI architecture
mentions:
  - Claude
  - GPT
  - Gemini
  - AWS EC2
  - ai-platform-architecture
cover:
  base: "/assets/images/editorial-ai-platform-architecture-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Table of five hosted models with the cost of one help-centre answer and the answers per hour a single-L40S instance must serve to cost less: Claude Sonnet 5 and GPT-6.1 Sol 196, Claude Haiku 4.5 392, Gemini 3.8 Flash 522, GPT-6 Luna 3,918"
  caption: "Price arithmetic only. Whether one GPU can serve that rate, with a model that passes the gate, is the part to measure."
faq:
  - q: "How much does one LLM answer cost?"
    a: "For a help-centre answer of about 3,500 input and 250 output tokens, October 2026 list prices give $0.0005 on GPT-6 Luna, $0.0048 on Claude Haiku 4.5, $0.0095 on Claude Sonnet 5 and $0.0475 on GPT-6 Astra: a hundredfold range for the same answer. An agent that plans, queries and composes pays for three calls per answer."
  - q: "When does self-hosting an LLM become cheaper than an API?"
    a: "When a dedicated instance serves more requests per hour than its hourly price divided by the API's price per request. A g6e.xlarge with one L40S costs $1.861 an hour, so it costs less than Claude Sonnet 5 above about 196 help-centre answers an hour, and less than GPT-6 Luna above about 3,918. Whether one instance can serve that rate with a model that passes your evaluation gate has to be measured."
  - q: "What reduces LLM costs the most?"
    a: "Model choice first: about 100 times between the cheapest and most expensive model priced here. Then design: labelling short text once per cluster instead of once per row cut day-one calls from 20,000 to 125, about 13 times cheaper on every model. Then calls per answer and context size, and finally prompt caching and batch pricing."
key_takeaways:
  - "The same answer costs a hundred times more on the most expensive model priced than on the cheapest, so model choice is a cost decision first."
  - "Pick the cheapest model that passes the feature's evaluation gate, and price the next one up to see what the quality gain costs."
  - "A single-L40S instance costs less than the API above 196 answers an hour against Claude Sonnet 5, but only above 3,918 against GPT-6 Luna."
  - "Design can beat model choice: labelling by cluster instead of by row cut day-one calls from 20,000 to 125."
  - "Prices move: two Gemini models double in price within three months, so a cost model needs a date on every number."
---

An AI feature's cost is four numbers multiplied: tokens per call, calls per answer, answers per month and price per token. Each varies by an order of magnitude between designs: the same analyst feature, at the same volume, costs $33 a month on one model and $3,300 on another. Teams usually find out which one they built from the invoice.

The [ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture) reference design makes the cost of each feature a number before launch: a cost model that prices each feature on nine current models, with every list price read from the vendor's own page on 18 October 2026 and quoted in [`cost/prices.yml`](https://github.com/technobasant/ai-platform-architecture/blob/v0.1.0/cost/prices.yml). The rest of that architecture is backed by measurements in public labs. The cost model is not. It is arithmetic on list prices and on token counts I assumed, and it says so.

<div class="callout callout--note" markdown="1">
*Update, 20 October 2026:* the tokens have since been measured. Over the architecture's 90 evaluation questions, the usage assistant averaged 1,094 input and 198 output tokens an answer, reasoning included: [$0.00032 an answer](https://github.com/technobasant/ai-platform-architecture/blob/main/decisions/0014-cost-per-answer.md) on gpt-oss-120b at Databricks' pay-per-token price in AWS EU (Ireland). The break-even table below is still price arithmetic only. An L4 (24 GB) or L40S (48 GB) is far too small to hold a 120-billion-parameter model at all, so for that model the comparison is with hardware that can, such as eight H100s, where self-hosting pays only above about 174,600 answers an hour.
</div>

**Operating rule.** Choose the cheapest model that passes the feature's evaluation gate, price the feature on it and on the next model up, and consider a GPU of your own only above the break-even request rate, after measuring that one instance can serve it.

## The same answer, a hundred times apart

Two features from the architecture. A help-centre answer is one call: about 3,500 input tokens (a short system prompt, five retrieved passages, the question) and 250 output tokens. An analyst answer, from an agent that plans, queries through tools and composes, is three calls of about 4,000 input and 300 output tokens each.

| Model | Help-centre answer | 100,000 a month | Analyst answer | 20,000 a month |
|---|---:|---:|---:|---:|
| GPT-6 Luna | $0.0005 | $48 | $0.0017 | $33 |
| Gemini 3.5 Flash-Lite | $0.0017 | $168 | $0.0059 | $117 |
| Gemini 3.8 Flash | $0.0036 | $356 | $0.0124 | $248 |
| Claude Haiku 4.5 | $0.0048 | $475 | $0.0165 | $330 |
| Claude Sonnet 5 | $0.0095 | $950 | $0.0330 | $660 |
| GPT-6.1 Sol | $0.0095 | $950 | $0.0330 | $660 |
| Gemini 3.1 Pro (preview) | $0.0100 | $1,000 | $0.0348 | $696 |
| Claude Opus 5.5 | $0.0190 | $1,900 | $0.0660 | $1,320 |
| GPT-6 Astra | $0.0475 | $4,750 | $0.1650 | $3,300 |
{: aria-label="Cost per answer and per month for two AI features on nine models, from list prices" }

The table says nothing about which of these models is good enough. That is what the feature's evaluation gate is for: run the candidate models through the same paired cases and keep the cheapest one that passes.

## Design moves cost as much as the model

Three levers sit beside model choice:

- **Calls per answer.** The analyst pays three times per answer because it plans, queries and composes. An agent loop that takes one more step adds a third to the bill.
- **Context.** Retrieved passages and tool schemas are most of the input tokens: in the help-centre answer, the five passages are about 2,900 of the 3,500.
- **What gets sent at all.** In the [short-text triage lab](https://github.com/technobasant/short-text-triage), normalising and clustering free text before calling a model meant 125 labelling calls on day one instead of 20,000, one per cluster instead of one per row. On Claude Haiku 4.5 that is $0.35 instead of $4.50, and the ratio holds on every model priced. The call counts are measured; the tokens per call are assumed.

Prompt caching and batch pricing are not in the model, and both are large: cached input is a small fraction of the input price on every provider here, and batch APIs halve prices for work that can wait.

## When a GPU of your own pays for itself

Self-hosting replaces a price per request with a price per hour. The break-even is the hourly price divided by the API's price per request:

| Hosted model replaced | g6.xlarge, 1× L4, $0.80/h | g6e.xlarge, 1× L40S, $1.86/h |
|---|---:|---:|
| Claude Sonnet 5, GPT-6.1 Sol | 85 answers/hour | 196 answers/hour |
| Claude Haiku 4.5 | 169 | 392 |
| Gemini 3.8 Flash | 226 | 522 |
| GPT-6 Luna | 1,694 | 3,918 |
{: aria-label="Help-centre answers per hour a GPU instance must serve to cost less than each hosted model" }

Running all month, the L40S instance costs about $1,359. At 100,000 help-centre answers a month, that is more than Claude Sonnet 5 would charge for the same answers ($950). At a million answers a month it is far less than Sonnet ($9,500), and still more than GPT-6 Luna ($475). The cheaper the hosted model, the more traffic a GPU of your own needs before it pays.

Three things the arithmetic does not know. Whether one instance can serve that rate, with batching and the context sizes above: that is a measurement. Whether an open model you can run on it passes the feature's gate: also a measurement. And who runs it: an inference server is one more service to patch, scale and be on call for.

## Prices move

Two of the prices in the model are already scheduled to change: Gemini 3.8 Flash doubles on 1 January 2027, and Gemini 4 Argon, a model not priced here, doubles on 1 December 2026. A cost model needs a date on every number, and the cost of a feature is something to re-run, not a figure to quote once.

<div class="callout callout--note" markdown="1">
**Boundary.** Standard API list prices and on-demand GPU prices in us-east-1, read on 18 October 2026, with no caching, batch or committed-use discounts. Token counts per call are assumptions; the only measured counts here are the triage lab's calls per day. No inference server was benchmarked, and no hosted model was evaluated on these features for this article. The point is the shape of the decision, not a vendor ranking.
</div>

## Before choosing a model for a feature

- The feature's evaluation gate, with answerable, unanswerable and adversarial cases.
- The cheapest model that passes it, and the price of the next one up.
- Measured tokens per call and calls per answer, from the gateway, as soon as the feature runs.
- A budget per feature, enforced where the calls go out.
- For self-hosting: a measured serving rate on the instance you would buy, against the break-even.
- A date on every price, and a reminder to re-run the numbers.

## Frequently asked questions

### How much does one LLM answer cost?

For a help-centre answer of about 3,500 input and 250 output tokens, October 2026 list prices give $0.0005 on GPT-6 Luna, $0.0048 on Claude Haiku 4.5, $0.0095 on Claude Sonnet 5 and $0.0475 on GPT-6 Astra: a hundredfold range for the same answer. An agent that plans, queries and composes pays for three calls per answer.

### When does self-hosting an LLM become cheaper than an API?

When a dedicated instance serves more requests per hour than its hourly price divided by the API's price per request. A g6e.xlarge with one L40S costs $1.861 an hour, so it costs less than Claude Sonnet 5 above about 196 help-centre answers an hour, and less than GPT-6 Luna above about 3,918. Whether one instance can serve that rate with a model that passes your evaluation gate has to be measured.

### What reduces LLM costs the most?

Model choice first: about 100 times between the cheapest and most expensive model priced here. Then design: labelling short text once per cluster instead of once per row cut day-one calls from 20,000 to 125, about 13 times cheaper on every model. Then calls per answer and context size, and finally prompt caching and batch pricing.

The model and its sources are in [ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture), with the design in [the case study](/work/ai-platform-architecture/). The data-platform counterpart is [the per-scan or per-hour break-even](/writing/warehouse-bill-per-scan-or-per-hour/). More on [AI agents in production](/writing/tags/ai-agents/) and [cost](/writing/tags/cost-finops/).
