---
layout: tag
title: RAG
eyebrow: Topic
permalink: /writing/tags/rag/
tag: rag
description: "Retrieval over corpora that keep growing: chunking, metadata filters, index choice, and the TTL policy that stops a vector store becoming a landfill."
---

The retrieval work I do most is over session video — {{ site.data.metrics.videos.value }} {{ site.data.metrics.videos.label }} through a Milvus-backed ingest path. At that rate a vector index is not something you build once; it is a pipeline with all the ordinary pipeline problems, plus a few of its own. Chunking has to respect the structure of the source rather than a token count, metadata filters usually do more useful work than the embedding does, and without a retention and compaction policy the index quietly becomes a landfill you pay to store and search. These posts are about that operational half, not the demo.
