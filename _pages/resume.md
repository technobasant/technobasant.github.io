---
title: Résumé
eyebrow: Career
headline: "Nine years from backend systems to data and AI platforms."
hero_code: "CAREER / LOG"
page_class: page-resume
permalink: /resume/
description: "Nine years in software engineering, spanning platform ownership, database reliability, governed AI delivery, mentoring, and independent systems work."
redirect_from:
  - /experience/
  - /skills/
---

<p><a class="btn btn--primary" href="{{ '/assets/basant-bhattarai-resume.pdf' | relative_url }}">Download the PDF</a></p>


## Career shape

A résumé usually flattens a career into a list. The more useful story is how the responsibility changed.

- **2017–2019 · SV Technology, India.** Built backend services and the PostgreSQL schemas behind them. This is where I learned that many “API bugs” begin as unclear data-model decisions.
- **2019–2020 · SVCET, India.** Led a small team delivering an NLP dialogue system. It was my first time being accountable for a plan assembled by more than one person.
- **2020–2024 · UXCam, Data Engineer.** Worked across ingestion, transformation, data modeling, orchestration, and analytical serving. The job expanded from making data arrive to keeping it correct, recoverable, and affordable.
- **2024–present · UXCam, Senior Data Engineer.** Own broader platform and AI-product outcomes: reliability, governance, design review, operational readiness, and the boundaries where automated output becomes trusted data.
{: .career-timeline }

## Experience at a glance

| Role | Period | Public scope |
|---|---|---|
| Senior Data Engineer, UXCam | 2024 – present | Data-platform and AI-product reliability, governance, architecture review, and technical leadership |
| Data Engineer, UXCam | 2020 – 2024 | Batch and streaming pipelines, data modeling, orchestration, storage, serving, and operations |
| Project Leader, SVCET | 2019 – 2020 | Planning and delivery of an NLP dialogue-system project with a small team |
| Software Developer, SV Technology | 2017 – 2019 | Python backend services, PostgreSQL schema work, reporting, and CI |

## Senior Data Engineer · UXCam

**February 2024 – present** · Kathmandu, working with a global team

- Own reliability and governance outcomes across production data and AI-assisted workflows, including clear service expectations, incident-ready runbooks, and reviewable data contracts.
- Design boundaries that turn model output into typed, validated, traceable records before another product workflow can depend on it.
- Lead design reviews and operational improvements across data processing, storage, serving, observability, and recovery without treating any one tool as the architecture.
- Mentor engineers through pairing and code review, with an emphasis on making ownership transferable rather than concentrating system knowledge in one person.

## Data Engineer · UXCam

**February 2020 – February 2024** · Kathmandu

- Built and operated batch and streaming data pipelines, then took on the data models, orchestration, storage, and analytical serving paths around them.
- Improved recovery and change safety by treating schema evolution, replay, late data, and backfills as designed interfaces instead of emergency procedures.
- Tuned distributed processing and query workloads by starting with the read path, measurement, and data layout before changing infrastructure settings.
- Worked with teams across time zones to turn product questions into maintainable datasets and operational workflows.

## Earlier roles

**Project Leader, SVCET**, India, 2019–2020 — led a small team building an intelligent dialogue system; coordinated requirements, planning, reviews, and delivery across academic and industry stakeholders.

**Software Developer, SV Technology**, India, 2017–2019 — built Python backend services, designed and maintained PostgreSQL schemas and reporting procedures, contributed to CI, and began the pipeline work that pulled me toward data engineering.

## Skills
{: #skills }

{{ site.data.skills.note }}

### {{ site.data.skills.tier1.heading }}

{{ site.data.skills.tier1.blurb }}

| Technology | Since | Public description | Evidence |
|---|---|---|---|
{% for item in site.data.skills.tier1.items -%}
| {{ item.name }} | {{ item.since }} | {{ item.scale }} | [{{ item.evidence_label | default: "Public note" }}]({{ item.evidence }}) |
{% endfor %}

### {{ site.data.skills.tier2.heading }}

{{ site.data.skills.tier2.blurb }}
{% for group in site.data.skills.tier2.groups %}
**{{ group.name }}**{% for i in group.items %} <span class="chip">{{ i }}</span>{% endfor %}
{% endfor %}
**Clouds**{% for cloud in site.data.skills.clouds %} <span class="chip">{{ cloud.name }}: {{ cloud.items | join: ", " }}</span>{% endfor %}

### {{ site.data.skills.tier3.heading }}

{{ site.data.skills.tier3.blurb }}

<small>{{ site.data.skills.tier3.items | join: ", " }}.</small>
{: .tech-list }

## Education and languages

**Bachelor of Technology, Computer Science and Engineering** — JNTUA College of Engineering, Anantapur, India, 2015–2019.

English: C1 · Nepali: native

## Contact

Kathmandu, Nepal · [{{ site.author.email }}](mailto:{{ site.author.email }}) · [LinkedIn](https://www.linkedin.com/in/technobasant) · [GitHub](https://github.com/technobasant)
