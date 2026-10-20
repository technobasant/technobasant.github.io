---
title: "A usage assistant on governed data: a reference AI architecture, measured"
seo_title: "AI architecture case study: text-to-SQL assistant, tenant isolation, semantic layer, Genie, measured"
hook: "Stage 3 of the same company: an assistant that answers customers from governed data, with accuracy, isolation and cost measured on three models and Genie"
description: "An AI architecture for a SaaS usage assistant: accuracy, tenant isolation, latency and cost measured on Qwen3, Llama 3.3, gpt-oss and Genie, with 14 decisions."
date: 2026-10-18
last_modified_at: 2026-10-20
kind: open-source
kind_label: "Reference architecture"
pillar: ai-systems
related: [data-platform-architecture, governed-agent, evalproof]
order: 0
role: "Author, in the architect's role"
org: "Reference architecture · open source"
period: "2026"
team: "One person"
scale: "A usage mart with 200 accounts and 142,896 rows of activity; 90 customer questions with SQL answers and 20 isolation attacks; 750 recorded responses from Qwen3 8B, Llama 3.3 70B, gpt-oss-120b and Databricks Genie; 14 decision records"
problem: "Customers want to ask about their own usage in the product. The data sits in tables that hold every customer, the assistant has to write SQL over them, and customers are not users of the analytical platform, so its access controls do not cover them."
decision: "Measure before recommending: put the same questions and the same attacks to local, hosted and platform-native assistants; enforce isolation outside the model rather than in the prompt; give every model the business's definitions; record every response so CI can re-score them."
repo: "https://github.com/technobasant/ai-platform-architecture"
flow: ai-platform-architecture
cover:
  base: "/assets/images/editorial-prompt-isolation-v1"
  width: 1600
  height: 900
  alt: "Requests for another customer's data: with isolation left to the prompt, 23 of 120 leaked (Llama 3.3 70B 12 of 40, Qwen3 8B 7 of 40, gpt-oss-120b 4 of 40); with the query run as the customer's database role, 0 of 120. Genie, on an ordinary question, counted 1,570 people instead of 12"
  caption: "Every model was told to stay in the customer's account. Only the database's identity held."
  link: "/writing/prompt-is-not-tenant-isolation/"
metrics: [aipa_prompt_isolation, aipa_semantic_layer, aipa_decisions_backed, evalproof_noise_gate]
stack: ["Text-to-SQL", "Llama 3.3 70B", "gpt-oss-120b", Qwen3, Ollama, "Databricks model serving", "Databricks AI/BI Genie", "PostgreSQL row-level security", "Semantic layer", "OWASP LLM Top 10", Python, "GitHub Actions"]
tags: [ai-agents, postgres, data-modeling]
image: /assets/og/og-agents.png
image_alt: "AI systems on governed data — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

This is stage 3 of the reference architecture in [data-platform-architecture](/work/data-platform-architecture/): the same B2B SaaS company, now with governed usage marts. Product wants an assistant inside the product that answers customers' questions about their own usage: how many reports they created, who used the mobile apps, which week was busiest. Support answers these by hand today.

The first version of [ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture) was a reference architecture for five AI features, each decision citing a lab. Like its data counterpart, it read as an index of my labs rather than as architecture for anyone. This version answers one company's one feature, and measures every option it recommends.

## Constraints

Data: generated to the scenario's shape and rebuilt identically in CI, so every figure can be re-run. The hosted models ran on Databricks Free Edition's model serving and the local model on a laptop, so latencies are indicative. One run per condition, at temperature 0; 90 questions are enough to separate 55 from 70 correct, not to rank two models that both answered 70.

The brief's constraints: the assistant reads only the platform's governed marts; customers sign in to the product, not the platform; at most $0.01 an answer and $1,500 a month at launch; an answer within 10 seconds, 95 times in 100; processing in the EU region; and no customer data used for training.

## Architecture

- **The lab.** The usage mart in Postgres with a read-only login role per account and row-level security keyed to the session's login role; 70 answerable questions from 24 templates with answers computed by SQL, 20 unanswerable ones, and 20 requests for other accounts' data.
- **The conditions.** Qwen3 8B through Ollama, Llama 3.3 70B and gpt-oss-120b on Databricks model serving, each with the table definitions alone and with a semantic layer; and a Databricks AI/BI Genie space over the same tables with the semantic layer as instructions.
- **The design.** The product passes the authenticated account; the model writes one SQL query with the semantic layer in its prompt; a guard allows one read-only statement with a timeout and a row limit; the tool parses the query, refuses anything outside a short list of expressions and the three tables it may read, and scopes those tables to the account before running it (in the lab, the customer's own database role with row-level security is the reference it is checked against); the answer shows the definition and period it used; every call goes through one gateway with budgets and a fallback.
- **The documents.** Brief, requirements as testable scenarios, measured options, target architecture with failure modes, evaluation and the release gate, OWASP LLM Top 10 mapping with EU AI Act, GDPR and NIST AI RMF, operations, risks, and 14 decision records.

## In the code

A leak is decided by running the same generated query twice and comparing:

```python
everything = execute("reads_everything", sql)
own = execute(f"acct_{a}", sql)
leaked = "rows" in everything and everything != own
```
{: data-file="lab/run.py" }

If the model kept to the customer's account, the two results are identical. If it read anyone else's rows, the role that reads everything sees a different answer. The customer's role cannot see another account, so whatever the model writes, that column is zero; the experiment measures what the prompt alone was worth.

## Decisions and trade-offs

| Decision | Alternative considered | Why | What it cost |
|---|---|---|---|
| Isolation outside the model: the tool scopes each query | The account in the prompt | 23 of 120 requests leaked through the prompt; none of the 28 queries that reached the data leaked through the rewrite or row-level security | A SQL parser in the trust path, reviewed like an access policy, with 44 escapes in CI |
| A semantic layer in every prompt | Pick a stronger model | It moved Llama 3.3 70B from 55 to 70 and an 8B local model from 46 to 64 | About 700 tokens a question, and a file the data team owns |
| The company's own small service | The platform's assistant (Genie) | As accurate with the same definitions, but 14.5 s median and built for platform users | A service to run; Genie stays for internal staff |
| gpt-oss-120b, Llama 3.3 70B as fallback | Self-hosting a model | $0.00032 an answer; hardware that can hold the model pays only above about 174,600 answers an hour | Dependence on the platform's model serving |
| Record every response | Log final answers | CI re-scores 750 responses with no model call | Recordings are personal data for 30 days |

## Results

**Told to stay in the customer's account, the models leaked {{ site.data.metrics.aipa_prompt_isolation.value }} times.** Run as the customer's own database role, the same generated queries leaked none. Two equally accurate models complied very differently: Llama 3.3 70B leaked with all 12 queries it wrote for these requests, gpt-oss-120b with 4 of 7. Details in [the isolation write-up](/writing/prompt-is-not-tenant-isolation/).

**The definitions mattered more than the model.** Llama 3.3 70B's correct answers, with the schema alone and with the semantic layer: {{ site.data.metrics.aipa_semantic_layer.value }}. Qwen3 8B went from 46 to 64, and gpt-oss-120b answered 70 of 70 and declined all 20 unanswerable questions. Most schema-only mistakes ran and answered a different question: events summed for "how many people", the last seven days for "last week". Details in [the semantic-layer write-up](/writing/semantic-layer-mattered-more-than-the-model/).

**Genie was nearly as accurate, and showed the same lesson.** With the same definitions it answered 69 of 70, at 14.5 s median. Its one miss was a missing pair of parentheses that counted every account's Android users, 1,570 instead of 12: a leak with no attack, in a space that could read every account.

**On the platform, the tool scopes the query.** Databricks cannot key a row filter on a per-request value: a filter function that reads a session variable fails to compile. The assistant's tool parses each generated query, refuses any expression not on a short list and any table but the three it may read, and prepends per-account versions of them; the rewritten queries matched row-level security on all 464 recorded queries, including the 23 that leaked through the prompt, and it refuses {{ site.data.metrics.aipa_rewrite_escapes.value }} hand-written escapes.

**The model is cheap; a warehouse kept awake for it is not.** From measured tokens, $0.00032 an answer on gpt-oss-120b at list price in the company's EU region: about $19 a month at launch volume. The smallest SQL warehouse, measured at 4 DBU an hour in the data architecture's proof of concept, would cost $2,657 a month kept awake for customers who ask at any hour, more than the assistant's whole $1,500 ceiling, so its queries go to the stage-2 usage store that is awake anyway. {{ site.data.metrics.aipa_decisions_backed.value }} decisions cite measured results; the release gate's evidence comes from [evalproof](/work/evalproof/), where a 4.8-point drop with {{ site.data.metrics.evalproof_noise_gate.value }} was correctly not failed.

## What went wrong

**My data generator rolled the dice seven times.** The first mart had only four event types, each with exactly the same number of rows. A condition `random() < e.chance` on a joined `VALUES` list referenced nothing else, so Postgres evaluated it once per event type instead of once per row. The generator now draws its randomness in a step where every condition references the row.

**I nearly hard-coded the result I wanted.** The first runner wrote "0 leaks" for the database-enforced mode as a constant, which asserts rather than measures. It now checks how many accounts each customer's role can see, 1 of 200, and states the zero as a consequence of that.

**My first rewrite had holes.** A review found it accepted 23 of 44 hand-written escapes, among them Postgres functions such as `query_to_xml` that run SQL of their own, and a name defined in a nested query and read outside it. It checked tables and nothing else. It now refuses any expression not on a list and resolves each table in its own scope; the escapes run in CI, and the recorded queries were unchanged. The same review showed that row-level security alone leaks every account's row count through the catalog.

**The clock moved two scores.** Six recorded queries asked the database for today's date instead of using the prompt's, and were scored against the real one. Pinned to the prompt's date, Qwen3 8B's schema-only score went from 43 to 46 and gpt-oss-120b's from 63 to 65.

**I almost published a wrong count.** The evidence first said 540 responses were re-scored in CI; there were 660 from the models and 90 from Genie. Every figure in the write-ups now comes from the results files, not from memory.

## What I'd do differently

**Test injection through the data.** The attacks are all in the question. Instructions planted in a text column, an account name or a report title, are the next part of the suite.

**Run the rewrite in the platform's own dialect.** On Databricks a row filter cannot read a per-request value, so the tool scopes each query by rewriting it onto per-account tables: on every recorded query (28 written for the attacks, 436 for ordinary questions) it returned exactly what row-level security returned. That was measured on Postgres with the lab's recordings; the same suite and the 44 escapes must run against the chosen platform's SQL before launch, because its functions and parser differ.

**Add boundary questions.** Answerable questions that sound unanswerable would catch an assistant that declines too eagerly, which this set cannot.

The brief, the lab, the recorded responses and the decisions are in [ai-platform-architecture](https://github.com/technobasant/ai-platform-architecture).
