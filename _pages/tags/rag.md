---
layout: tag
title: RAG
eyebrow: Topic
permalink: /writing/tags/rag/
tag: rag
description: "Retrieval over corpora that keep growing: chunking, metadata filters, index choice, and the TTL policy that stops a vector store becoming a landfill."
---

A retrieval index is not something you build once; it is a data pipeline with additional ways to be confidently wrong. Chunking should respect source structure, metadata filters often carry more precision than embeddings, and retention needs an owner before the index grows without bound. These notes focus on evaluation, provenance, deletion, re-indexing, and the operational half of retrieval that short demos usually skip.
