# 🦾 Agentic Finance Beast

> **Enterprise-Grade Multi-Agent AI Backend for Financial Research, Portfolio Optimization, and Sentiment Analysis.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_AI-FF6F61?style=flat)](https://www.langchain.com/langgraph)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Executive Summary

**Agentic Finance Beast** is an autonomous multi-agent financial research microservice designed to transform raw market feeds into actionable investment intelligence.

Built on **FastAPI** and **LangGraph**, the engine orchestrates autonomous AI agents that:
- Analyze real-time market data via yfinance
- Execute vector-driven sentiment retrieval via **Supabase (`pgvector`)**
- Compute portfolio risk metrics

It serves as the core AI engine for the [Agentic Finance Frontend](https://github.com/Sumayea104/agentic-finance) application.

---

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend / Client                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Agentic Finance Beast Microservice                  │
│                                                                        │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   Price Agent    │    │   Sentiment      │    │   Portfolio      │  │
│  │   (yfinance)     │    │   Agent          │    │   Agent          │  │
│  │                  │    │   (pgvector RAG) │    │   (P&L Calc)     │  │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘  │
│           │                       │                       │            │
│           └───────────────────────┼───────────────────────┘            │
│                                   ▼                                    │
│                     LangGraph Supervisor (Router)                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ JSON Output
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Supabase (pgvector) + Financial APIs                │
└────────────────────────────────────────────────────────────────────────┘

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3.11+ |
| **Framework** | FastAPI |
| **Agents** | LangGraph |
| **LLM** | Mistral AI, Gemini |
| **RAG** | Supabase pgvector |
| **Data** | yfinance |
| **Deployment** | Render |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/ask` | Ask a financial question |
| `GET` | `/docs` | Swagger UI |

---

## 🚀 Live Demo

**Backend API:** [agentic-finance-beast.onrender.com](https://agentic-finance-beast.onrender.com)
**API Docs:** [agentic-finance-beast.onrender.com/docs](https://agentic-finance-beast.onrender.com/docs)

---

## 🔧 Local Setup

```bash
git clone https://github.com/Sumayea104/agentic-finance-beast.git
cd agentic-finance-beast
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload

---
📜 License
MIT © Sumayea Rahman
