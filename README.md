# Overland Intelligence System

**High Desert Expeditions — Tucson, AZ**

> Know the terrain before you move.

A multi-agent business intelligence pipeline built with LangGraph, FastAPI, and a single-file HTML dashboard. Upload a CSV, ask a business question, and get a research-backed intelligence report with charts and ranked strategic recommendations — all running locally at zero cost.

---

## Pre-Employment Independent Project Statement

Project state documented as of 2026-04-24 (pre-employment).

This project was independently created before employment at Jack Henry.

It was built on personal time, using personal equipment, personal accounts, and non-employer data. It is not based on employer systems, employer code, employer architecture, employer workflows, employer client data, or employer confidential information.

This project is intended as a personal portfolio project demonstrating my technical skills.

This project uses sample, public, synthetic, or independently sourced data and does not contain employer or client information.

---

## What It Does

The system runs five AI agents in sequence through a stateful LangGraph pipeline:

| Agent | What it does |
|---|---|
| RAG Ingest | Loads supporting documents into Qdrant in-memory vector store |
| Data Analyst | Profiles and analyzes your CSV, extracts key findings |
| Market Research | Runs web searches + RAG retrieval, synthesizes market context |
| Insights Engine | Produces ranked strategic recommendations with confidence scores |
| Report Writer | Generates a full Markdown intelligence report |

Results stream live to the dashboard via SSE. When complete: findings, market intel, recommendations, charts, and a downloadable PDF report — all in one view.

---

## Demo Question

> *Is the Baja and pre-runner segment growing fast enough to justify dedicated product lines, or is it still a niche within the broader overlanding market? Which vehicle platforms and regions should a gear manufacturer prioritize?*

A synthetic 3,500-row sales dataset (`sample_data/hde_overland_sales_2022_2024.csv`) is included so you can run the full pipeline immediately without your own data.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | LangGraph | Stateful graph — explicit node wiring, no magic |
| LLM | Groq llama-3.3-70b | Fast, free tier, excellent reasoning |
| LLM (local) | Ollama llama3.2 / mistral | Zero cost fallback, runs offline |
| Embeddings | Ollama nomic-embed-text | Local, free, no API key |
| Vector store | Qdrant in-memory | No Docker, no persistence needed |
| Search primary | Tavily | Best quality, 1k free/month |
| Search fallback | DuckDuckGo | Unlimited, no key, auto-fallback |
| Backend | FastAPI + SSE | Clean API, real-time streaming |
| Frontend | Single-file HTML/JS | No build step, no framework, opens in any browser |
| Charts | matplotlib | Dark-themed, base64 PNG, embeds in PDF |
| PDF | WeasyPrint | HTML → PDF, charts embedded inline |

**Runtime cost: $0** — Groq free tier + Ollama + DuckDuckGo.

---

## Project Structure

```
overland_intelligence_system/
├── app_api.py              FastAPI backend — upload, analyze/stream, download, providers
├── app.html                Single-file HTML dashboard
├── config/
│   ├── settings.py         Pydantic settings — reads .env, zero provider opinions
│   ├── llm_registry.py     ← ADD NEW LLM PROVIDERS HERE ONLY
│   ├── search_registry.py  ← ADD NEW SEARCH PROVIDERS HERE ONLY
│   ├── embedding_registry.py ← ADD NEW EMBEDDING PROVIDERS HERE ONLY
│   ├── llm_factory.py      Reads registry — no provider logic, never changes
│   ├── search_factory.py   Reads registry — no provider logic, never changes
│   └── embedding_factory.py Reads registry — no provider logic, never changes
├── graph/
│   └── workflow.py         LangGraph state schema + pipeline
├── agents/
│   ├── data_analyst.py
│   ├── question_suggester.py
│   ├── research_agent.py
│   ├── insights_agent.py
│   └── report_agent.py
├── tools/
│   ├── data_tools.py       CSV/Excel load, clean, profile, analyze
│   ├── search_tools.py     Search execution + result normalization
│   ├── chart_tools.py      4 matplotlib charts → base64 PNG
│   └── exceptions.py       Named exceptions with registry-sourced retry messages
├── prompts/                System + user prompts per agent
├── rag/
│   ├── ingest.py           Chunk → embed → Qdrant in-memory
│   └── retriever.py        Similarity search + context builder
├── output/
│   └── pdf_builder.py      Markdown + charts → PDF via WeasyPrint
├── ui/
│   └── styles.py           CSS design system + HTML component helpers
├── tests/                  132 tests across all modules
└── sample_data/
    └── hde_overland_sales_2022_2024.csv
```

### Adding a New Provider

To add a new LLM, search, or embedding provider — **edit one file only**:

| What you're adding | Edit this file |
|---|---|
| New LLM | `config/llm_registry.py` |
| New search provider | `config/search_registry.py` |
| New embedding provider | `config/embedding_registry.py` |

Then add the required keys to `.env`. The dashboard dropdown, error messages,
and fallback logic update automatically — no other files change.

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/candiwestin/overland_intelligence_system
cd overland_intelligence_system
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — at minimum set your Groq key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

Get a free Groq key at [console.groq.com](https://console.groq.com).

### 3. Pull Ollama models (optional — for local LLM)

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

Model downloads and embedding caches are local runtime assets and should not be committed.

### 4. Run

```bash
uvicorn app_api:app --reload --port 8000
```

Then open `app.html` in your browser:

```
# Windows (WSL):
explorer.exe .

# macOS:
open app.html

# Linux:
xdg-open app.html
```

---

## Running a Demo

1. Drag `sample_data/hde_overland_sales_2022_2024.csv` onto the upload zone
2. Click one of the suggested questions — or type your own
3. Select LLM and Search providers in the sidebar
4. Click **Run Analysis**
5. Watch the agent feed tick through the pipeline live
6. Review findings, market intel, and recommendations in the tabs
7. Click **Download Intelligence Report** for the PDF

---

## Running Tests

```bash
python -m pytest tests/ -v
```

131 tests across all modules. No API keys required — all external calls are mocked.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq` or `ollama` |
| `GROQ_API_KEY` | — | Required for Groq |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL_PRIMARY` | `llama3.2` | Primary Ollama model |
| `OLLAMA_MODEL_SECONDARY` | `mistral` | Secondary Ollama model |
| `EMBEDDING_PROVIDER` | `ollama` | Embeddings backend |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model name |
| `SEARCH_PROVIDER` | `tavily` | `tavily` or `duckduckgo` |
| `TAVILY_API_KEY` | — | Required for Tavily search |
| `RAG_CHUNK_SIZE` | `500` | Token chunk size for RAG |
| `RAG_TOP_K` | `5` | Number of RAG results to retrieve |

---

## Architecture

```
Browser (app.html)
    │
    │  POST /upload          CSV → file_id + suggested questions
    │  POST /analyze/stream  SSE stream — node events + final result
    │  GET  /download/{id}   PDF file download
    │  GET  /providers       Registry-driven provider list → populates dashboard dropdowns
    │
FastAPI (app_api.py)
    │
    └── LangGraph Pipeline (graph/workflow.py)
            │
            ├── ingest_rag       rag/ingest.py → Qdrant in-memory
            ├── data_analyst     agents/data_analyst.py → pandas analysis + LLM
            ├── research         agents/research_agent.py → search + RAG + LLM
            ├── insights         agents/insights_agent.py → ranked recommendations
            └── [report_agent]   agents/report_agent.py → Markdown report
                    │
                    └── output/pdf_builder.py → WeasyPrint PDF
```

All LLM and search providers are swappable at runtime via the sidebar dropdowns — no restart required.

---

## A Note on the Data Layer

The dashboard includes a CSV file upload for demonstration purposes. This was a deliberate choice to
keep the portfolio demo self-contained and easy to run. Just drag a file in, ask a question, see the
full pipeline run.

In a production deployment, the data layer would be replaced by automated connectors feeding the
system on an ongoing basis.

Realistic production sources would include:

- **A relational database** — Postgres, Snowflake, BigQuery — queried on a schedule or on demand
- **A cloud storage bucket** — S3, GCS, Azure Blob — with new files landing continuously and triggering ingestion
- **An API feed** — internal or third-party — pulling structured data into the pipeline automatically

The agent pipeline, RAG layer, and report generation are all source-agnostic. Replacing the upload
with any of these connectors requires changes only to the data ingestion layer — everything downstream
runs identically. The CSV upload exists to demonstrate the system; the architecture was designed with
production data sources in mind.

---

## License

MIT