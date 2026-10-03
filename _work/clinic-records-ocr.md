---
title: "Camera-first clinic records, with OCR that knows when to refuse"
seo_title: "Clinic Records OCR Case Study — Measured, FHIR-Shaped Drafts"
hook: "Clinicians photograph paper records; the system drafts structured fields for review and refuses what it cannot read."
description: "A camera-first records product for small clinics: OCR drafts FHIR-shaped fields, a fixed scorer picks the engine, and anything unreadable goes to a person."
date: 2026-08-20
last_modified_at: 2026-10-03
kind: production
order: 2
featured: true
role: "Founder and sole engineer — built outside my day job"
org: "Independent product"
period: "2026 – present"
team: "Solo"
scale: "Small outpatient clinics in Nepal; evaluated on a private corpus of real captures"
problem: "Outpatient records live on paper. Retyping them is slow, and OCR that guesses confidently is worse than none, because a plausible wrong value can reach a patient's chart."
decision: "Treat every extracted value as a draft: measure accuracy per document class with a scorer written first, refuse what the recogniser could not read, and commit nothing without a clinician."
metrics: [clinic_ocr_lab_value_accuracy, clinic_ocr_engines_evaluated]
stack: [Python, FastAPI, PostgreSQL, RapidOCR, ONNX Runtime, React, "FHIR R4", Docker]
tags: [applied-ml, data-quality, postgres]
image: /assets/og/og-agents.png
image_alt: "Camera-first clinic records with reviewable OCR — Basant Bhattarai"
sitemap:
  changefreq: monthly
  priority: 0.8
---

## Context

Small outpatient clinics in Nepal keep their records on paper: OPD tickets, lab reports, prescriptions, discharge notes, cards filled in by hand. A doctor who wants a patient's history photographs the pages or does without. The product turns those photographs into a searchable longitudinal record — but only through a review step, because a clinical record is the one place where an OCR system that guesses fluently is more dangerous than one that does nothing.

The constraint that shaped everything else was the deployment: a small box in the clinic, two vCPUs and a few gigabytes of memory shared with the API and the database, and patient images that never leave the machine. That rules out hosted OCR and most of the large models that lead document benchmarks.

## My role

I own every layer: the capture flow in the browser, the API and data model, the OCR worker, the extraction and evaluation code, the labelled corpus and its scorer, and the deployment. The engine benches are mine too, each kept as a standalone tool so its numbers can be re-run rather than remembered.

## Architecture

A clinician captures a multi-page document on a phone. Each page is stored once as an immutable, checksummed original plus a metadata-stripped copy for display and OCR. Every page becomes a row in a PostgreSQL job table, and workers claim jobs with a compare-and-set lease decided by affected row count, so horizontally scaled workers never process a page twice and a worker that dies mid-page has its claim expire and recovered. OCR itself runs in a child process, so a malformed page cannot take the worker down.

```text
phone capture ─→ immutable original + derivative (SHA-256)
             ─→ OCR job row (lease, attempts, claim expiry)
             ─→ RapidOCR / ONNX Runtime, tier capped per document kind
             ─→ geometry-aware extraction (label↔value pairing, lab-table columns)
             ─→ plausibility rails + readability filter + closed vocabularies
             ─→ draft, FHIR-shaped, with provenance per value
             ─→ clinician review ─→ atomic commit to the patient timeline
```
{: data-file="pipeline.txt" }

Extraction reads position, not a flat string: a lab table's columns are learned from its header row, and a printed form's label is paired with the value beside or below it. Names are matched against closed, bundled vocabularies of medicines, conditions, tests and allergens, accepted only with a margin over the runner-up, because mislabelling one analyte as another is worse than dropping the row. Every number passes a plausibility rail, and rows the recogniser could not read are refused before they can become typed fields — shown read-only beside the draft, never discarded. Confirmed facts are exposed in FHIR R4 shapes: Observation, DiagnosticReport, Encounter, DocumentReference.

## Decisions

| Decision | Alternative | Why |
| --- | --- | --- |
| Score fields with a fixed, precision-weighted scorer written before tuning | Character accuracy, or one aggregate F1 | Characters are not fields, and a missed row costs typing while an invented one can reach a chart. Correct refusals and unscorable pages get their own states. |
| Ship RapidOCR (PP-OCRv6, ONNX Runtime) at library-default settings | docTR, Tesseract, larger detectors, documented tuning | Measured through the same scorer, every alternative scored lower on these phone photographs; Tesseract stays as the fallback. |
| Keep a vision-language OCR sidecar, switched off | Make it the engine | Strongest reader on print, no better on handwriting, several times slower on the target box, and it returns no per-line confidence — the signal review depends on. |
| Withdraw image-quality work after a per-defect cost table | Deskew, illumination and binarisation as planned | Holding document type constant, the defects cost approximately nothing. |
| Postgres job table with compare-and-set leases | Request-scoped background tasks; `SKIP LOCKED` | Survives restarts; correct on both PostgreSQL and SQLite without dialect-specific locking. |
| Targets per document class, plus one absolute | A single 99% across all documents | Printed lab reports and handwritten cards have different ceilings; never being silently wrong on a value is the one target that does not move. |

## Results

On printed lab reports, the pipeline reads result rows with high precision and gets the value itself right in the large majority of matched rows; record type is detected correctly on every labelled page. Handwritten and narrative sections are far below that, and the evaluation explains why: on handwritten diagnoses most missed rows never appear in the OCR text at all, so the ceiling is recognition, and every engine tested — classic or vision-language — hit the same one. The measured figures, with their page counts and methods, are in [the engine evaluation](/writing/choosing-an-ocr-engine-for-clinic-records/) and in [the essay on the plan that measurement withdrew](/writing/ocr-measurement-withdrew-the-plan/).

The more durable results are negative ones, written down so nobody re-covers the ground: documented detection tuning made phone photographs worse, a bigger detector read the desk, grouping words into lines made one engine seven times worse, capture defects cost nothing once document type was held constant, and adding workers was safe but not faster while each ONNX Runtime session took every core it could see.

## What I would do differently

Label more pages earlier. The comparisons that decided the engine ran on 11 and 26 labelled pages, and the vision-language bench on a single patient's packet; every conclusion is scoped to those numbers. The next investment is a larger, held-out, human-verified split — the only set the project allows to be quoted as accuracy — and a scored multi-kind corpus with hallucination counts before any vision-language model is switched on, even as a second opinion.
