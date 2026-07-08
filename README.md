# AI Video Intelligence Platform

<!-- refresh -->

<p align="center">

**An end-to-end AI platform for extracting, understanding, searching, and interacting with video content.**

Convert hours of video into minutes of knowledge using Speech Recognition, Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), Semantic Search, and Knowledge Extraction.

</p>

---

## Table of Contents

- Overview
- Problem Statement
- Solution
- Key Features
- Demo
- System Architecture
- Technology Stack
- Project Structure
- AI Pipeline
- Installation
- Usage
- API Documentation
- Roadmap
- Benchmarks
- Future Improvements
- Contributing
- License

---

# Overview

AI Video Intelligence Platform is an end-to-end AI system that transforms long-form videos into structured, searchable knowledge.

Instead of watching a 2-hour lecture or meeting, users can:

- Read concise summaries
- Search for concepts instantly
- Chat with the video
- Generate quizzes
- Create flashcards
- Extract action items
- Translate subtitles
- Discover key moments

The platform combines Speech Recognition, Natural Language Processing, Retrieval-Augmented Generation (RAG), Vector Search, and Large Language Models into a single intelligent pipeline.

---

# Problem Statement

Modern video content is growing rapidly:

- University lectures
- Technical talks
- Podcasts
- Business meetings
- Webinars
- YouTube tutorials

Watching everything is time-consuming.

Users need a smarter way to extract knowledge from videos.

Current tools usually provide only subtitles or simple summaries.

This platform aims to transform videos into searchable knowledge bases.

---

# Solution

The platform automatically performs:

Video

↓

Speech Recognition

↓

Transcript Cleaning

↓

Knowledge Extraction

↓

Embeddings

↓

Vector Database

↓

LLM

↓

Search • Chat • Summary • Quiz • Flashcards

---

# Features

## Video Processing

- Upload local videos
- YouTube support (planned)
- Audio extraction
- Faster-Whisper transcription
- Transcript normalization

---

## AI Summary

- Executive Summary
- Detailed Summary
- Bullet Summary
- TL;DR

---

## Chapter Detection

Automatically detects:

- Introduction
- Topics
- Demonstrations
- Conclusions

Generates timestamps.

---

## Key Moments

Automatically identifies:

- Important explanations
- Examples
- Definitions
- Demonstrations

---

## Chat with Video

Ask questions naturally.

Example:

> Where does the speaker explain Retrieval-Augmented Generation?

↓

Answer

↓

Timestamp

↓

Supporting transcript

---

## Semantic Search

Search over thousands of processed videos.

Example:

Transformer Architecture

↓

Returns relevant video segments.

---

## Flashcards

Automatically generate learning flashcards.

Example:

Q:
What is Vector Database?

A:
A database optimized for similarity search using embeddings.

---

## Quiz Generation

Generate:

- Multiple Choice
- True / False
- Short Answer

---

## Mind Map

Generate a structured knowledge graph for learning.

---

## Translation

Translate:

- Transcript
- Summary
- Subtitle

---

## Subtitle Generator

Generate:

- SRT
- VTT

---

## Speaker Diarization

Identify:

Speaker A

Speaker B

Speaker C

---

## Meeting Intelligence

Extract:

- Action Items
- Deadlines
- Decisions
- Responsibilities

---

# System Architecture

(Architecture Diagram)

---

# AI Pipeline

```
Video

↓

Extract Audio

↓

Voice Activity Detection

↓

Speech Recognition

↓

Transcript Cleaning

↓

Speaker Diarization

↓

Topic Segmentation

↓

Knowledge Extraction

↓

Chunking

↓

Embedding

↓

Vector Database

↓

Retrieval

↓

Reranking

↓

LLM

↓

Final Response
```

---

# Tech Stack

| Layer | Technology |
|---------|------------|
| Backend | FastAPI |
| Frontend | Next.js |
| AI Framework | PyTorch |
| LLM | Qwen 3 |
| Speech Recognition | Faster-Whisper |
| Embedding | BGE-M3 |
| Reranker | BGE-Reranker |
| Vector Database | Qdrant |
| Database | PostgreSQL |
| Cache | Redis |
| Queue | Celery |
| Storage | MinIO |
| Monitoring | Prometheus |
| Dashboard | Grafana |
| Deployment | Docker |
| CI/CD | GitHub Actions |

---

# Project Structure

```
backend/
frontend/
ai/
storage/
deployment/
docs/
configs/
monitoring/
```

---

# Data Flow

User Upload

↓

Processing Queue

↓

AI Pipeline

↓

Database

↓

Embedding

↓

Vector Search

↓

LLM

↓

Frontend

---

# Benchmarks

Evaluate:

- ROUGE
- BERTScore
- Answer Relevancy
- Faithfulness
- Latency
- Throughput

---

# API Documentation

Coming Soon

---

# Experiments

Compare:

- Whisper Small
- Whisper Large
- Qwen
- Gemma
- BGE
- E5

---

# Development Roadmap

## Version 1

- Video Upload
- Speech-to-Text
- Summary
- Chapter Detection

---

## Version 2

- Chat with Video
- Semantic Search
- Subtitle
- Timestamp Search

---

## Version 3

- Flashcards
- Quiz
- Mind Map
- Translation

---

## Version 4

- Meeting Intelligence
- Speaker Diarization
- Dashboard
- User Management

---

## Version 5

- Microservices
- Kafka
- Kubernetes
- Monitoring
- CI/CD
- Evaluation Framework

---

# Screenshots

Coming Soon

---

# Demo

Coming Soon

---

# Contributing

Contributions are welcome.

Please open an Issue before submitting a Pull Request.

---

# License

MIT License

---

# Author

Nguyen Hoang Khang

Data / AI Engineer

Ho Chi Minh City University of Industry and Trade

---

If you find this project useful, please consider giving it a Star.