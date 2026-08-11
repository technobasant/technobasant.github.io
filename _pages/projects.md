---
permalink: /projects/
title: Selected work
eyebrow: Case studies
excerpt: Systems where architecture, data, AI, and product had to meet production constraints.
---

Staff portfolios earn trust with **problem → approach → outcome**, not logo walls. Three pieces of work that show how I operate.

<div class="case" markdown="1">

## UXCam — company data platform

<span class="case-meta"><span>Platform</span><span>2020 – Present</span><span>Spark · Kafka · Iceberg · K8s</span></span>

**Problem.** Mobile analytics at multi-TB / day needs a platform that is fast enough for product, correct enough for finance-grade metrics, and cheap enough to survive growth — without collapsing into a pile of one-off jobs.

**Approach.** Rebuilt ETL in Spark/PySpark, automated with Airflow, then moved the estate onto Kubernetes. Designed an Iceberg lakehouse with SCD patterns, quality gates on streaming paths, and governed Databricks / Unity Catalog where collaboration mattered. Defined freshness SLOs and OpenTelemetry-backed observability.

**Outcome.** **50%** faster processing on **5TB+/day**, **35%** storage cost reduction, **40%** infra cost down after K8s migration, **99.9%** uptime, **100M+** queries/day after engine and schema work.

</div>

<div class="case" markdown="1">

## UXCam — App Analytics Agent Platform

<span class="case-meta"><span>Agentic AI</span><span>2024 – Present</span><span>LangGraph · CrewAI · ADK · Milvus</span></span>

**Problem.** Analysts could not keep pace with insight demand across **25K+** apps. Raw LLM chat was not an answer — outputs had to land in structures the rest of the platform trusts.

**Approach.** Built a multi-agent analytics platform (Google-ADK, LangChain, CrewAI, MCP, LangGraph) with tool-using workflows, RAG on Milvus for video-scale corpora, and MLflow for MLOps. Emphasized structured contracts, fallbacks, and observability over demo UX.

**Outcome.** **60%** faster analytics delivery, **75%** less analyst manual effort, **1M+ videos/month** through RAG paths, measurable personalization lift.

</div>

<div class="case" markdown="1">

## ClickHomes — AI-native real-estate platform

<span class="case-meta"><span>Product</span><span>2024 – Present</span><span>FastAPI · Next.js · PG · ClickHouse</span></span>

**Problem.** Real-estate outcomes (buy, sell, lease, agent CRM) need one continuous system — public discovery, decision tools, operational CRM, and AI assistance — without lying about data quality or forcing capture before value.

**Approach.** Founded and lead-engineered the platform: **PostgreSQL** for OLTP, **ClickHouse** for listings/analytics, mandatory RESO transformation pipeline (Connector → Transformer → Gold), AgentService for LLM work, static-export-capable Next.js frontend, auth/RBAC, and production ops on Docker/VPS.

**Outcome.** A live product at [clickhomes.ai](https://clickhomes.ai) with dual-database invariants, typed load boundaries, and AI features that persist into operational records rather than disposable chat.

</div>

---

More code and experiments: [github.com/technobasant](https://github.com/technobasant).
