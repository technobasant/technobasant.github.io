---
title: "For text-to-SQL, the definitions mattered more than the model"
seo_title: "Semantic layer vs schema-only text-to-SQL, measured"
description: "70 customer questions with answers computed by SQL. Given the business's definitions as well as the schema, Llama 3.3 70B went from 55 to 70 right."
date: 2026-10-19 13:00:00 +0545
last_modified_at: 2026-10-19
type: essay
pillar: ai-systems
tags:
  - ai-agents
  - data-modeling
toc: true
featured: false
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - text-to-SQL
  - semantic layer
  - LLM evaluation
mentions:
  - Llama 3.3 70B
  - gpt-oss-120b
  - Qwen3
  - Databricks AI/BI Genie
  - ai-platform-architecture
cover:
  base: "/assets/images/editorial-semantic-layer-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Correct answers out of 70, with the schema only and with a semantic layer: Qwen3 8B 46 to 64, Llama 3.3 70B 55 to 70, gpt-oss-120b 65 to 70; Databricks Genie 69 with the same definitions"
  caption: "With the schema alone, most wrong answers were queries that ran and answered a different question."
faq:
  - q: "Does a semantic layer improve text-to-SQL accuracy?"
    a: "In this test it did, more than changing the model. On 70 customer questions with answers computed by SQL, adding a semantic layer of definitions to the schema moved Llama 3.3 70B from 55 to 70 correct, Qwen3 8B from 46 to 64 and gpt-oss-120b from 65 to 70. Unanswerable questions declined went up too."
  - q: "What goes in a semantic layer for an LLM?"
    a: "What the business means and the schema does not say: periods ('last week' starts on Monday), vocabulary ('people who used the product' is distinct users; 'mobile' is iOS and Android), metric SQL (an average over days counts days with no activity), rules (one row; UNANSWERABLE when the tables cannot answer), and a few worked examples. Here it was about 700 extra tokens per question."
  - q: "How does Databricks Genie compare with a custom text-to-SQL prompt?"
    a: "Given the same definitions as instructions and the same examples, Genie answered 69 of 70 questions correctly, against 70 of 70 for gpt-oss-120b and Llama 3.3 70B with the definitions in the prompt. Its median answer took 14.5 seconds against 2 to 3, and its one wrong answer counted every account's Android users because of missing parentheses."
key_takeaways:
  - "With the schema alone, three models answered 46, 55 and 65 of 70 customer questions correctly; with a semantic layer, 64, 70 and 70."
  - "Most schema-only mistakes were queries that ran and answered a different question: summing events for 'how many people', the last seven days for 'last week'."
  - "Unanswerable questions declined rose with the definitions: gpt-oss-120b declined all 20."
  - "Genie, given the same definitions, answered 69 of 70, slower, at 14.5 seconds median."
  - "The definitions cost about 700 tokens a question, about a hundredth of a cent at list price."
---

Text-to-SQL is usually evaluated as a model comparison: which model writes the best SQL over a schema. For an assistant that answers a business's own questions, I found the model mattered less than whether it was told what the business means.

I measured it for a B2B SaaS company's [usage assistant](/work/ai-platform-architecture/), a scenario common across the industry: customers asking about their own product usage, answered by SQL over a usage mart. Three models, each with the schema alone and with a semantic layer, and Databricks AI/BI Genie with the same definitions as its instructions.

**Operating rule.** Before comparing models for text-to-SQL, write down the business's definitions (periods, vocabulary, metric SQL, what to decline) and give them to every model. Fix wrong answers by fixing a definition and adding the question to the evaluation set, not by swapping models.

## The questions

A reproducible generated copy of the mart: 200 accounts, 1,935 users and 142,896 rows of daily activity from July to September 2026. 24 question templates, each asked for different accounts, 70 in all: "How many people used the mobile apps in September?", "How many events did we have last week?", "Which week of the last quarter had the most events?", "What was our average number of daily active users in September?". Each has a reference answer computed by SQL. Ten more questions cannot be answered from the mart at all (what they paid, which user will cancel, session length), and the right reply is "UNANSWERABLE".

Each model writes one PostgreSQL query; it runs as the customer's own role; the answer counts if the reference value is in the first row of the result.

## The results

| Correct, of 70 | Schema only | With the semantic layer | Unanswerable declined, of 20 |
|---|---:|---:|---|
| Qwen3 8B, local | 46 | 64 | 12 → 18 |
| Llama 3.3 70B, hosted | 55 | **70** | 17 → 19 |
| gpt-oss-120b, hosted | 65 | **70** | 18 → **20** |
| Databricks Genie, the semantic layer as instructions | | 69 | 19 |
{: aria-label="Correct answers with the schema only and with the semantic layer, by model" }

The semantic layer added 15 correct answers to Llama 3.3 70B and 18 to an 8-billion-parameter local model. The gap between the smallest and the largest model with the definitions (64 against 70) was smaller than the gap the definitions made to either.

## What the schema-only mistakes were

Five of the 49 schema-only misses across the three models were queries that failed. The rest ran, returned a number, and answered a different question:

- **"How many people used the mobile apps?"** `SUM(events)` over iOS and Android rows: the number of events, not people.
- **"How many events did we have last week?"** The last seven days, 24 to 30 September, instead of Monday to Sunday, 21 to 27.
- **"How many viewers logged in?"** The number of logins by viewers, not the number of viewers who logged in.
- **"Our average number of daily active users?"** An average over the days anyone was active, skipping the days nobody was.

Each is a reasonable reading of the words. Each disagrees with what the dashboards say, which is how a customer discovers it.

## What went into the semantic layer

About 700 tokens, sent with every question ([`semantic.yml`](https://github.com/technobasant/ai-platform-architecture/blob/main/lab/semantic.yml)):

- **Periods:** today's date; weeks start on Monday; what "last week", "last month", "last quarter" and "the last 7 days" mean, as dates.
- **Vocabulary:** a feature is an event type; "mobile" is iOS and Android; "people who used the product" are distinct users.
- **Metrics with their SQL:** events are a sum; active users are a distinct count, never a sum of daily counts; an average over days includes days with no activity.
- **Rules:** one row; the item first for a "which" question; UNANSWERABLE when the tables cannot answer.
- **Three worked examples.** One of them shows the daily-average metric for August, and the questions ask it for September; the gain was not only that question.

At Databricks' list price, the extra tokens cost gpt-oss-120b about a hundredth of a cent per answer; it answered for $0.00032 on average at the list price in the company's EU region.

## Genie, with the same definitions

Genie got the same definitions as its instructions and the same examples, and answered 69 of 70. Its median answer took 14.5 seconds, against 2 to 3 for the hosted models called directly. Its one wrong answer had a missing pair of parentheses around `OR`, which counted every account's Android users; that is the subject of [the isolation write-up](/writing/prompt-is-not-tenant-isolation/). Genie had no run without the definitions, so it shows that a platform's own assistant reached the same level with them, not that they caused it; that evidence is the three models' before and after.

<div class="callout callout--note" markdown="1">
**Boundary.** One generated mart, 70 answerable questions from 24 templates and 20 unanswerable ones, temperature 0, one run per condition; answers cluster by template, so the independent evidence is closer to 24 cases than 70. Enough to separate 55 from 70 correct; not enough to rank two models that both answered 70. The semantic layer was written with these templates in view (its periods and metric definitions map onto them), so the gain is an upper bound for questions like these; a held-out set written after it was frozen is the next test. The hosted models ran on Databricks Free Edition's model serving and the local one with Ollama on one host, so latencies are indicative. Every response is recorded and re-scored in CI against a freshly built mart.

*Updated 19 October 2026:* six recorded queries asked the database for today's date instead of using the date in the prompt, and were scored against the real clock. They now get the prompt's date, which raised two schema-only scores: Qwen3 8B from 43 to 46 and gpt-oss-120b from 63 to 65.
</div>

## Before choosing a model for text-to-SQL

- Write the evaluation set first, with answers computed by SQL, including questions the data cannot answer.
- Write down the business's periods, vocabulary and metric SQL, and give them to every model you compare.
- Score declines separately from accuracy, so a model that declines everything and one that answers everything both fail.
- When an answer is wrong, add a definition and a question; keep the model.
- Share the definitions with the dashboards, so an answer and a chart can disagree only when one of them is wrong.

## Frequently asked questions

### Does a semantic layer improve text-to-SQL accuracy?

In this test it did, more than changing the model. On 70 customer questions with answers computed by SQL, adding a semantic layer of definitions to the schema moved Llama 3.3 70B from 55 to 70 correct, Qwen3 8B from 46 to 64 and gpt-oss-120b from 65 to 70. Unanswerable questions declined went up too.

### What goes in a semantic layer for an LLM?

What the business means and the schema does not say: periods ("last week" starts on Monday), vocabulary ("people who used the product" is distinct users; "mobile" is iOS and Android), metric SQL (an average over days counts days with no activity), rules (one row; UNANSWERABLE when the tables cannot answer), and a few worked examples. Here it was about 700 extra tokens per question.

### How does Databricks Genie compare with a custom text-to-SQL prompt?

Given the same definitions as instructions and the same examples, Genie answered 69 of 70 questions correctly, against 70 of 70 for gpt-oss-120b and Llama 3.3 70B with the definitions in the prompt. Its median answer took 14.5 seconds against 2 to 3, and its one wrong answer counted every account's Android users because of missing parentheses.

The questions, the definitions, the runners and every recorded response are in [ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture/tree/main/lab), with the design in [the case study](/work/ai-platform-architecture/).
