# fin-doc-llm-orchestrator

## What This Project Is

This project is a pipeline (a sequence of automated steps) that takes unstructured financial documents (raw text with no fixed format) like bank statements, dispute letters, invoices, and news snippets, and turns them into structured, searchable data. It uses a chain of LLM (large language model) calls where each call has a specific job: classify the document, extract key information, store it, and summarize risk.

---

## Problem It Solves

Fraud and risk teams in banks and fintech companies receive thousands of documents daily. These documents are unstructured, meaning the information is buried in plain text and cannot be queried like a database. Manually reviewing them is slow and error-prone. There is no easy way to ask "which documents mention this account number?" or "what are the high-risk transactions this week?" without reading everything by hand.

This project automates that entire workflow.

---

## Why This Is the Best Approach

The combination of LLM routing, structured output extraction, and retrieval-augmented generation (RAG, which means answering questions by first fetching relevant stored documents rather than relying on model memory alone) is currently the leading approach for document intelligence tasks.

LLMs are no longer single-pass text generators but act as orchestrators, invoking external tools, applying multi-step reasoning, and iteratively validating their own outputs. Retrieval-augmented models improve accuracy and contextual understanding without retraining on sensitive customer data, while agentic workflows allow LLMs to perform tasks like cross-referencing fields, summarizing complex contracts, or suggesting exceptions.

Traditional models often struggle to incorporate and interpret heterogeneous financial data in real time, but RAG can dynamically retrieve relevant external documents and integrate them with proprietary financial records to improve decision-making accuracy. As financial applications increasingly demand real-time, explainable, and context-aware insights, RAG presents a scalable and interpretable approach to addressing these challenges.

Organizations rely on diverse information sources like invoices, customer surveys, legal documents, and banking records to support business activities. As this data, both structured and unstructured, grows in volume, efficient information extraction methods become essential for informed decision-making.

Techniques such as document chunking, document comparators, and multi-agent orchestration have been developed to handle extremely long texts, and LLM pipelines for finance typically convert documents into embeddings stored in a searchable database, with a retrieval step finding relevant chunks for a given question and a generative model producing the answer or summary.

---

## Features

- Document router that classifies incoming text into one of four types: bank statement, invoice, dispute letter, news snippet
- Specialized extraction chain per document type that pulls out entities such as amounts, dates, account numbers, party names, and risk keywords
- All extracted output is validated against a fixed schema (Pydantic model) so downstream code always receives clean, typed data
- Vector store ingestion: extracted text is embedded and stored so you can run semantic search across all processed documents
- RAG-style Q&A interface to query across documents using natural language
- Risk summary chain that reads extracted data and writes a short risk report
- Cost and latency logging per pipeline step so you can see exactly what each call costs and how long it takes
- Synthetic document generator to create test documents without needing real sensitive data

---

## Tools Used

| Tool | How It Is Used |
|---|---|
| LangChain | Builds the router, chains, and orchestration logic that connects every step |
| OpenAI API | Provides the LLM calls; a fast cheap model (gpt-3.5-turbo) for classification, a stronger model (gpt-4o) for extraction and summarization |
| Pydantic | Defines strict data schemas so extracted output is always typed and validated |
| ChromaDB | Local vector database that stores document embeddings for semantic search and RAG Q&A |
| OpenAI Embeddings | Converts document text into vector representations for storage in ChromaDB |
| Python-dotenv | Loads API keys from a .env file so secrets are never hardcoded |
| tiktoken | Counts tokens per request to calculate cost per step |
| time (stdlib) | Measures latency of each pipeline step |
