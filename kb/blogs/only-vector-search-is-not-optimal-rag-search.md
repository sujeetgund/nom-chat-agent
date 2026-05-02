---
title: "Why Vector Search Alone Is Not Optimal for RAG"
excerpt: "Vector search captures meaning, but hybrid retrieval with BM25 adds precision. This guide shows why combining both improves RAG relevance and reduces noisy context."
date: "2026-02-01"
author: "sujeetgund"
tags: ["RAG", "Vector Search", "BM25", "Hybrid Search", "LangChain"]
status: "published"
ogImage: "https://github.com/user-attachments/assets/5c773113-8859-432d-a6d8-185f3eb47ea3"
coverImage: "https://github.com/user-attachments/assets/5c773113-8859-432d-a6d8-185f3eb47ea3"
---

Vector search is powerful, and for many use cases it is a great starting point. But in production RAG systems, semantic similarity alone often misses exact intent. If the goal is precise and relevant retrieval, hybrid search usually performs better.

Most tutorials stop after these steps:

1. Load documents.
2. Chunk them.
3. Generate embeddings.
4. Store in a vector database.
5. Retrieve semantically similar chunks.

That pipeline works, but it is not always optimal. Better retrieval quality depends on document parsing, chunking strategy, retrieval logic, and reranking.

This post demonstrates hybrid retrieval (vector + keyword search) and shows why it is often more practical than vector-only retrieval.

## Why Add Keyword Search to Vector Search?

### Semantic Similarity Is Not the Same as User Intent

Embeddings are good at relationships like "coffee" and "espresso." But they do not always capture exact constraints in a query.

In real systems, vector search can retrieve documents that sound similar, even when they are not the most precise match for what the user asked.

### The Specificity Problem

Imagine a financial archive assistant.

Query: "What was the tax split we paid in 2021?"

A vector-only retriever may return records from 2020, 2021, and 2022 because all discuss tax split language. That increases recall, but also adds irrelevant context.

### Hidden Costs of Fuzzy Retrieval

- Increased latency: more irrelevant chunks are fetched and processed.
- Context bloat: unnecessary text fills the model context window.
- Higher cost and risk: more tokens, plus a higher chance of hallucination.

![](https://github.com/user-attachments/assets/5c773113-8859-432d-a6d8-185f3eb47ea3)

## The Hybrid Retrieval Approach

Vector retrieval provides semantic breadth.
BM25 provides exact keyword precision.

Using both gives a better balance of recall and specificity.

## Hands-On: Hybrid Search in LangChain

Install dependencies:

```bash
pip install -q langchain langchain-community langchain-classic faiss-cpu rank_bm25 langchain-huggingface
```

Set your Hugging Face token:

```python
import os

os.environ["HF_TOKEN"] = "YOUR_HF_TOKEN"
```

Create sample documents:

```python
from langchain_core.documents import Document

docs = [
    Document(
        page_content="Form 10-K Annual Report: Our cybersecurity infrastructure protects against unauthorized access. We utilize AES-256 encryption for all data at rest.",
        metadata={"source": "annual_report_2023", "tag": "security", "id": 1}
    ),
    Document(
        page_content="Quarterly Earnings Summary: Revenue grew by 15% YoY. The primary driver was the adoption of our AI-driven 'Smart-Invest' advisor platform.",
        metadata={"source": "q3_earnings", "tag": "finance", "id": 2}
    ),
    Document(
        page_content="Policy Update: Users must enable Two-Factor Authentication (2FA) to access the 'Smart-Invest' dashboard. This prevents identity theft and phishing.",
        metadata={"source": "policy_manual", "tag": "security", "id": 3}
    ),
    Document(
        page_content="Market Analysis: High interest rates usually lead to decreased consumer spending, affecting retail-heavy investment portfolios negatively.",
        metadata={"source": "market_brief", "tag": "macroeconomics", "id": 4}
    ),
    Document(
        page_content="Customer Support: If you cannot see your 'Smart-Invest' balance, refresh the app or check if the server status is 'Operational' on our website.",
        metadata={"source": "support_faq", "tag": "support", "id": 5}
    )
]
```

Build the FAISS vector store:

```python
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

embedding_fn = HuggingFaceEmbeddings(model="BAAI/bge-large-en-v1.5")
vectorstore = FAISS.from_documents(docs, embedding_fn)
```

Create vector and BM25 retrievers:

```python
from langchain_community.retrievers import BM25Retriever

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
bm25_retriever = BM25Retriever.from_documents(docs)
bm25_retriever.k = 5
```

Run a test query:

```python
query = "How is the company protecting my Smart-Invest account information?"
```

BM25 and vector retrieval produce different rank orders. BM25 tends to prioritize exact matches like "Smart-Invest" and "information," while vector retrieval emphasizes semantically close content such as 2FA and identity theft.

## Ensemble Retriever for Hybrid Ranking

LangChain's `EnsembleRetriever` merges outputs from multiple retrievers and reranks them using Reciprocal Rank Fusion (RRF).

Use it like this:

```python
from langchain_classic.retrievers import EnsembleRetriever

ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.6, 0.4],
)
```

RRF uses rank positions instead of raw scores. This matters because BM25 and vector similarity scores are on different scales and cannot be compared directly.

For document $d$, the fused score is commonly represented as:

$$
	ext{RRF}(d) = \sum_{r \in R} \frac{1}{k + \text{rank}_r(d)}
$$

where $R$ is the set of retrievers and $k$ is a smoothing constant.

## What the Results Show

In this example:

- BM25 ranks the support FAQ highly because of direct keyword overlap.
- Vector search ranks the 2FA policy highly due to semantic relevance to account protection.
- The ensemble keeps the strongest semantic result at the top while still benefiting from keyword precision.

That is exactly the behavior we want in many real-world RAG systems.

## Final Takeaway

Vector search is a strong default, but not a complete retrieval strategy for every business problem.

When user intent depends on exact terms, dates, IDs, policies, or product names, hybrid retrieval provides better precision with minimal additional complexity. In practice, that often means faster answers, lower token usage, and more trustworthy outputs.
