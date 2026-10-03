---
title: "The best OCR model I tested does not ship. The scorer decided why."
seo_title: "Choosing an OCR engine for clinic records: eight engines, one scorer"
description: "Eight OCR engines on real clinic records, one fixed scorer. The strongest reader stays switched off: slower on the target box, and it cannot say when it is unsure."
date: 2026-10-03 10:10:00 +0545
last_modified_at: 2026-10-03
type: essay
tags:
  - applied-ml
  - data-quality
toc: true
featured: true
sitemap:
  changefreq: monthly
  priority: 0.8
about:
  - OCR engine evaluation
  - vision-language OCR models
  - handwriting recognition on clinical documents
mentions:
  - RapidOCR
  - PaddleOCR-VL
  - Surya
  - docTR
  - Tesseract
  - LightOnOCR
  - llama.cpp
  - ONNX Runtime
cover:
  base: "/assets/images/editorial-ocr-engines-v1"
  widths: "840,1600"
  raster_widths: "840,1600"
  fallback_width: "1600"
  width: 1600
  height: 900
  alt: "Schematic of eight OCR engines feeding one fixed scorer, with the shipped engine, the switched-off vision-language sidecar, and the engines rejected on accuracy, memory and licence"
  caption: "Same pages, same scorer, only the engine changes. The strongest reader lost on the property a reviewer needs most: knowing when it is unsure."
faq:
  - q: "Is a vision-language model better than classic OCR for handwritten clinical documents?"
    a: "Not by enough to matter on this corpus. The best vision-language configuration read three of six handwritten fields exactly on the test card, with single-character confusions on the rest. It was near-perfect on printed text, which was not the bottleneck. On handwriting, every engine tested hit the same recognition ceiling."
  - q: "Why benchmark OCR engines through the extraction pipeline instead of by character accuracy?"
    a: "Because characters are not fields. On this corpus a page often gained characters and lost fields: docTR read more characters than RapidOCR on handwritten pages and produced fewer correct fields with 70% more inventions. The only comparable number is field-level precision and recall from the same scorer on the same pages."
  - q: "Can a small OCR vision-language model run in 2 GB of RAM?"
    a: "Yes, with care. LightOnOCR-1B at Q4 ran under a hard 2 GB Docker limit with the right llama.cpp flags. PaddleOCR-VL 1.6 fitted only after its 841 MiB F16 vision projector was quantised locally to Q4_K_M, which brought peak RSS to 1,288 MB with no measurable accuracy change."
  - q: "Why does OCR need per-line confidence if the model is accurate?"
    a: "Because review is how a doubtful value reaches a clinician flagged. An engine that returns no recognition score removes that signal entirely; every value arrives with the same authority. On a precision-first clinical extractor, losing the abstain signal costs more than a modest accuracy gain buys."
key_takeaways:
  - "Hold the scorer and the pages fixed and swap only the engine; any other comparison measures the benchmark, not the engine."
  - "The classic defaults won: every documented detection tweak roughly tripled false positives on phone photographs, and a bigger detector found the desk."
  - "The text-assembly layer is part of the engine. Grouping Tesseract's words into lines made extraction seven times worse on identical characters."
  - "The strongest vision-language reader was near-perfect on print and still wrong on handwritten digits, and it returns no per-line confidence, so it ships switched off."
  - "Defaults, warm caches and cross-page corroboration all flattered the numbers; each had to be removed before a result meant anything."
---

Handwriting is where extraction fails on clinic records, so a better OCR model was the obvious fix. The 2026 field is crowded with candidates, several posting headline scores in the mid-nineties on document-parsing benchmarks, and the engine I ship is a classic detect-then-recognise pipeline on ONNX Runtime that nobody would put at the top of a leaderboard.

I measured eight engines against it. The one that read best overall is not the one that ships, and the reasons it lost are worth more than the scores.

**Operating rule.** Choose an OCR engine by its per-class accuracy, its failure mode and its latency on the box you will actually deploy, measured through your own scorer on your own pages. Hold the scorer fixed and swap only the engine. A benchmark that changes two things at once has measured the benchmark.

This is the clinic-records product I am building for small outpatient clinics in Nepal; the [companion essay](/writing/ocr-measurement-withdrew-the-plan/) covers its scorer and the capture-defect plan that measurement withdrew. This one is the engine decision.

## The rules of the bake-off

Every comparison followed three rules, and each exists because breaking it produced a wrong answer at least once.

**One scorer.** Each engine's output went through the same extraction pipeline and the same field-level scorer that produce the shipping numbers. Each bench reuses the previous bench's scorer rather than writing its own, because a second scorer makes two engines incomparable — the failure these benches exist to prevent.

**The real hardware.** The deployment target is a small clinic box: two vCPUs, and a memory budget of 2 to 4 GB that the OCR worker shares with the API and the database. Laptop GPU numbers do not transfer. The memory benches ran under a hard Docker limit (`--memory=2g --memory-swap=2g`) so that "fits" meant a cgroup said so.

**Patient data stays on the machine.** The corpus is real clinical captures, so hosted OCR APIs were out of scope by design, not by benchmark. Every engine here runs locally.

The page sets were small, and they are named everywhere they are used: **11 mixed pages** with full field labels for the classic engines, **26 pages where handwriting is the payload** for the handwriting re-test, and for the vision-language models **one real 17-page checkup packet**, which is one patient's documents. That last n is the weakest thing in this essay, and the conclusions below are scoped to it.

## Classic engines: the defaults won

The shipped engine is RapidOCR with PP-OCRv6 models on ONNX Runtime, at a model tier capped per document kind. The first question was whether it was even configured well.

| Configuration (11 mixed pages) | F1 | Precision | Recall | False positives | s/page |
|---|---:|---:|---:|---:|---:|
| **PP-OCRv6 medium, library defaults (shipped)** | **0.423** | 0.703 | 0.302 | 11 | 4.78 |
| v6 detection + v5 English recogniser | 0.352 | 0.564 | 0.256 | 17 | 1.76 |
| v5 server detector + v6 recogniser | 0.229 | 0.237 | 0.221 | 61 | 6.21 |
| Best documented detection tweak (960 px, sensitive) | 0.331 | 0.434 | — | 30 | — |
| Higher input resolution (1280 px) | 0.287 | 0.311 | — | 51 | — |
{: aria-label="RapidOCR model and detection-parameter sweep on 11 labelled pages" }

Nothing needed changing, and every alternative failed the same way.

"English only" was not a free choice: PP-OCRv6 ships one unified multilingual recogniser, and the English-specific weights stop at an older, smaller v5 model. Restricting to English cost 17% of F1. The larger server detector was much worse, not better — 61 false positives against 11 — because on a photograph most of the extra text it finds is the desk, the facing page and the document underneath.

The detection parameters told the same story. I started from the values the documentation and the DB post-processing literature recommend: lower thresholds to recover faint strokes, higher input resolution for small text. Every one of six settings scored worse than the library default, and false positives roughly tripled while true positives barely moved. The advice is sound for **scans of documents**. These are **photographs of paper on a desk**, where "competing documents in frame" is one of the commonest attributes in the corpus. More sensitive detection recovers the neighbouring document, and every recovered line becomes a candidate field.

Then two other engines, through the same pipeline:

| Engine | Pages | F1 | Precision | Recall | s/page |
|---|---|---:|---:|---:|---:|
| **RapidOCR, PP-OCRv6 (shipped)** | 11 mixed | **0.426** | 0.722 | 0.302 | 4.4 |
| docTR `fast_base` + `parseq`, rotation on | 11 mixed | 0.217 | 0.382 | 0.151 | 9.4 |
| Tesseract 5.5, word-per-line adapter | 11 mixed | 0.165 | 0.727 | 0.093 | 1.0 |
| **RapidOCR, PP-OCRv6 (shipped)** | 26 handwritten | **0.150** | 0.279 | 0.102 | 3.4 |
| docTR `fast_base` + `parseq`, rotation on | 26 handwritten | 0.058 | 0.087 | 0.043 | 5.2 |
{: aria-label="RapidOCR against docTR and Tesseract, scored through the same pipeline" }

docTR has a genuinely good architecture list and better layout handling, and it reached half the F1. The first run was unfair to it — it assumed straight pages and read a sideways lab report as a column of `I`s — so the table shows it with its own rotation handling on, its strongest recogniser, and both detectors; the result barely moved. It was then re-tested on the narrower question it was suggested for, handwritten English only, with the Devanagari and image-size objections deliberately set aside. The gap widened: 39% of RapidOCR's F1 and 31% of its precision, and slower. It read *more* characters than RapidOCR on those pages and produced fewer than half the correct fields, with 70% more inventions. Extra characters that do not resolve into fields are a cost on a precision-first pipeline, not a gain.

Tesseract kept its place as the fallback for when the primary engine cannot start: its precision is comparable, its recall collapses, and some extraction beats none.

## The assembly layer is part of the engine

The Tesseract run also refuted a hypothesis I was fairly sure of.

Its adapter emits one evidence row per *word*, and every parser downstream reads lines — a medicine needs drug, dose, route and frequency together. Grouping the words into the lines Tesseract itself reports looked like an obvious fix. It made extraction **seven times worse**, from 0.165 to 0.023 F1, on identical characters.

The reason is the layer between the recogniser and the parsers. It re-clusters boxes into visual rows geometrically, splits columns by page-relative gaps, joins labels to values and reunites bare labels — all calibrated against the box sizes, confidences and line granularity of the engine it was built on. Feed it another engine's geometry and the calibration is wrong in ways the character count cannot show: the grouped and ungrouped Tesseract runs produced the same 643 characters and differed sevenfold in fields.

That layer is also where the largest single gain in the project came from, and it had nothing to do with recognition. Early on, the review form was filling a name field with the label "Age:" and body height with a one-centimetre value. The instinct was "OCR is inaccurate". A printed body-composition slip disproved it: recognition was perfect, and extraction returned one field of nine, because the pipeline threw away geometry and ran regular expressions over a flat string. Pairing each label with the value to its right or below, and learning a lab table's columns from its header row, took that slip from one field to nine and lab pages from zero extracted values to twenty-three — with the same engine.

So the honest cost of an engine swap is not the swap. It is re-tuning the assembly layer against the new engine's geometry, and none of the benchmark scores above include that work. A competing engine's score is a floor, not a ceiling — and docTR would have had to double after that work merely to draw level.

## Vision-language models: right answers, wrong failure modes

If the classic recognisers share a handwriting ceiling, the candidates that might break it are the small OCR-specialised vision-language models. Five were run locally through llama.cpp; three more were skipped because their documented footprints are well above the memory budget.

| Model (quantised) | Test | Handwriting | Print | Speed | Verdict |
|---|---|---|---|---|---|
| LightOnOCR-1B, Q4 | one handwritten card, 2 GB cgroup | best result, in bands mode only | — | 104 s full page; 18 s as 3 bands | invented place names on full page |
| LightOnOCR-2, Q4 | same card, 8 GB | two fields wrong | — | 63 s | weaker than v1 |
| Nanonets-OCR-s, Q4 | same card, 8 GB | clean JSON; two fields weak | — | 55 s | 2.6 GB of weights |
| Surya 2 (0.65B, F16) | card + 17-page packet | decimal wrong in every mode | identifiers 44% at its default 96 dpi, 100% at 200 dpi | 32.7 s card on CPU | ≥ 4 GB; weights licence gated |
| **PaddleOCR-VL 1.6** (official pipeline) | card + 17-page packet | **3 of 6 fields exact** | **near-perfect on repeated printed text** | 6.9–7.2 s/page on a laptop GPU; ~7.2 s on the 2-vCPU box | strongest reader; ships off |
{: aria-label="Small vision-language OCR models evaluated locally" }

Four results changed the design, and none of them is a score.

**Unit of image matters more than the model.** LightOnOCR on a full page took 104 seconds and wrote invented country names into a clinical document's printed address — the hallucination failure the review rails exist to contain. Six single-line crops fixed nothing: document-trained models degenerate without layout context, and the numeric crops came back as empty lines. Three *semantic bands* of the page were 5.8 times faster than the full page, invented nothing, and were the only configuration at any memory budget that read the handwritten decimal exactly. And overlapping bands that disagree are a usable abstain signal: one band misread a reading another band got right. A second, unrelated model later failed the same way on the same region.

**A model is its pipeline.** PaddleOCR-VL scored "weak field extraction" in the first bench, which prompted a bare GGUF once through llama.cpp. Run through its official pipeline — layout detection, orientation and unwarping first, then regions to the model — it became the strongest engine measured. Same weights; different system.

**Quantisation is a measurement, not an assumption.** Upstream publishes no quantised vision projector, and the 841 MiB F16 projector was what caused an out-of-memory under the 2 GB limit. Quantising the official file locally to Q4_K_M took total weights to 751 MiB and peak RSS to 1,288 MB, and identifier accuracy was identical across all three weight configurations; burned-in measurements came back exactly on both quantised ones, and the handwriting errors did not change by a character. A third-party Q4 of the model behaved byte-identically to the official weights on the handwriting — evidence that the errors are the model's, not the quantisation's, and the right way to accept someone else's re-quant into a clinical system is to diff it against upstream output first. In the other direction, a quantised KV cache saved 125 MB and *changed the transcription*, so it is a flag, not a default.

**The leaderboard number is real, and it is about print.** PaddleOCR-VL's model card reports 96.33% on OmniDocBench, a document-parsing benchmark scored largely on printed material. That is consistent with everything I measured: a repeated printed letterhead phrase at seven of seven, an alphanumeric certificate code at six of six, ultrasound measurements burned into an image read exactly where Surya returned nothing. And on the handwritten card, three of six fields exact, with errors that are single-character confusions — a handwritten 5 read as an S, a slash read as a 1 — stable under full-precision weights, greedy decoding and banding. The benchmark does not cover the hardest thing this product does, and print was never the bottleneck.

## Why the strongest reader ships switched off

PaddleOCR-VL is in the codebase as a sidecar behind two off-by-default switches. The [companion essay](/writing/ocr-measurement-withdrew-the-plan/) has its latency on the deployment box; the decision rests on three properties, in order of weight.

| Property | RapidOCR (shipped) | PaddleOCR-VL sidecar |
|---|---|---|
| Per-line confidence | yes | **none** — layout-then-transcribe has no recognition score |
| Geometry for label–value pairing | line boxes | layout blocks only |
| Handwritten field that motivated the test | wrong | still wrong |
| Printed text | good | near-perfect |
| Text burned into images | partial | exact |
| Latency on the 2-vCPU target | baseline | about 5× |
| Weights licence | Apache-2.0 | Apache-2.0 |
{: aria-label="Shipped engine against the vision-language sidecar" }

The first row is the disqualifying one. A low-confidence line is how a doubtful value reaches a clinician flagged for review. An engine that returns a constant there does not improve the signal; it removes it, and every value arrives with the same authority. The second row matters almost as much: form reading pairs a printed label with the value beside it by position, and approximating line positions from block subdivisions is the wrong foundation for reading a template's height field.

So the sidecar has two modes and neither is on. Escalation keeps RapidOCR authoritative and adds a second opinion, marking every disagreement low-confidence so it arrives for review. Engine replacement makes the sidecar the only engine, and then a sidecar failure raises rather than silently falling back — because an engine substitution a clinician cannot see in provenance is worse than a capture that failed and retried. A circuit breaker stops a down sidecar from costing every page its full timeout.

Surya, the other strong candidate, lost on different grounds: it is the best result for structure and for hallucination — none in any run — but it peaked above 2 GB even with a single parallel slot, still misses the handwritten decimal, emits no text at all for regions it classifies as pictures, and its weights carry a revenue-and-funding-gated licence with a no-competing-product clause. Its code is Apache-2.0; its weights are not, and that distinction is easy to miss on a repository page.

<div class="callout callout--gotcha" markdown="1">
**Five ways these numbers lied before they were fixed.** A warm `llama-server` reported 3.9 s/page because it reused cached prompt state; cold, it was 6.9 s, so every throughput figure comes from a fresh server. Peak RSS sampled on Apple's GPU backend read as little as 36 MB for a model occupying over a gigabyte, because offloaded weights are not resident memory; only a Linux cgroup settles fit. Surya's defaults — 96 dpi and eight parallel slots — corrupted an alphanumeric identifier in five of nine readings and were slower *and* fatter than four slots. Scoring a whole packet against one card's truth credited a model with the exact name and height, both read from *printed* pages elsewhere in the packet. And a DPI comparison across two different page sets produced a "24% slower" that was really 2.4×, because output tokens dominate and pages differ in how much text they carry.
</div>

## What the engine choice actually decided

The engine was not the lever. On handwritten pages every engine, classic or vision-language, hit the same ceiling, and an earlier audit had already found that most of what the pipeline misses on handwritten cards never appears in the OCR text at all. What the bake-off bought was narrower and more useful than a better score:

- **A shortlist with reasons.** RapidOCR for detection, geometry, confidence and print; a vision-language model, if one is ever switched on, for semantic bands of handwriting-bearing pages, never whole pages and never single lines.
- **A safety property.** Disagreement between overlapping bands, or between engines, is treated as abstention and routed to a person. No value read only by a vision-language model reaches a chart without clinician confirmation.
- **A re-open condition.** Any challenger must beat the shipped engine's field-level F1 and precision on the same labelled subsets, measured through the same scorer — not a character count, not a benchmark card.

<div class="callout callout--note" markdown="1">
**Boundary.** The classic-engine comparisons ran on 11 and 26 labelled pages from a private corpus of 198 real clinic captures; the vision-language comparisons ran on one handwritten card and one 17-page packet from a single patient, so they settle a shortlist, not a ranking. All scores are development-set diagnostics from my own machines, not held-out accuracy and not clinical validation. Latencies name their hardware: Apple Silicon development laptop, CPU-only Docker with a 2 GB or 8 GB cgroup, or the 2-vCPU deployment class. Hosted OCR services were out of scope because patient images do not leave the machine. No patient text, value, name or image appears here; the character confusions quoted are generic.
</div>

## Frequently asked questions

### Is a vision-language model better than classic OCR for handwritten clinical documents?

Not by enough to matter on this corpus. The best vision-language configuration read three of six handwritten fields exactly on the test card, with single-character confusions on the rest. It was near-perfect on printed text, which was not the bottleneck. On handwriting, every engine tested hit the same recognition ceiling.

### Why benchmark OCR engines through the extraction pipeline instead of by character accuracy?

Because characters are not fields. On this corpus a page often gained characters and lost fields: docTR read more characters than RapidOCR on handwritten pages and produced fewer correct fields with 70% more inventions. The only comparable number is field-level precision and recall from the same scorer on the same pages.

### Can a small OCR vision-language model run in 2 GB of RAM?

Yes, with care. LightOnOCR-1B at Q4 ran under a hard 2 GB Docker limit with the right llama.cpp flags. PaddleOCR-VL 1.6 fitted only after its 841 MiB F16 vision projector was quantised locally to Q4_K_M, which brought peak RSS to 1,288 MB with no measurable accuracy change.

### Why does OCR need per-line confidence if the model is accurate?

Because review is how a doubtful value reaches a clinician flagged. An engine that returns no recognition score removes that signal entirely; every value arrives with the same authority. On a precision-first clinical extractor, losing the abstain signal costs more than a modest accuracy gain buys.

The habit that carries beyond OCR is to evaluate a model as a component with a failure mode, not as a score: what it does when it is unsure, what it costs on the hardware you have, and what the layer after it was tuned to expect. The scorer and the withdrawn capture plan are in [the companion essay](/writing/ocr-measurement-withdrew-the-plan/); the product itself is [the clinic-records case study](/work/clinic-records-ocr/). More on [applied ML and evaluation](/writing/tags/applied-ml/) and [data quality](/writing/tags/data-quality/).
