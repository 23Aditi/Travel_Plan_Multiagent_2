# ✈️ TripMate AI — Autonomous Multi-Agent Travel Planner

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-FF4B4B?style=flat&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Ultra--Fast-F55036?style=flat)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Railway](https://img.shields.io/badge/Deploy%20on-Railway-0B0D0E?style=flat&logo=railway&logoColor=white)](https://railway.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, stateful **Multi-Agent Travel Operating System** built with **LangGraph**, **FastAPI**, and **Groq**. TripMate AI coordinates six specialized AI agents executing concurrently with parallel fan-out/fan-in pipelines, live tool caching, LangSmith observability, and conversational multi-turn refinement.

---

## 🌐 Live Demo & Deployment

| Environment | Status | Link |
|---|---|---|
| **Railway Cloud (Production)** | Ready to Deploy | [Deploy on Railway Guide](#-deploying-to-railway) |
| **Local Cockpit** | Localhost | `http://127.0.0.1:8000` |

---

## 🏛️ System Architecture

TripMate AI replaces linear agent chains with a **concurrent DAG (Directed Acyclic Graph)** in LangGraph:

```mermaid
flowchart TD
    User([User Request / Prompt]) --> UI[Glassmorphic Web Cockpit]
    UI -->|SSE Stream /api/travel/stream| Engine[FastAPI Orchestrator]
    
    Engine --> Intent[1. Intent Parser Agent]
    
    subgraph Parallel Concurrency [Parallel Fan-Out]
        Intent --> Flight[2. Flight Intelligence Agent]
        Intent --> Hotel[3. Hotel Discovery Agent]
        
        Flight <--> Cache1[(TTL Flight Cache)]
        Hotel <--> Cache2[(TTL Hotel Cache)]
        
        Flight --> LiveAv[AviationStack API]
        Hotel --> LiveTav[Tavily Search API]
    end
    
    Flight --> Itinerary[4. Itinerary Architect Agent]
    Hotel --> Itinerary
    
    Itinerary --> Budget[5. Budget Analyst Agent]
    Budget --> Final[6. Final Synthesizer Agent]
    
    Final --> Response([Streamed Markdown Dossier + PDF Export])
    
    Checkpointer[(PostgreSQL / Memory Checkpointer)] <-->|Session State Persistence| Engine
```

---

## 🌟 Key Engineering Highlights

### 1. ⚡ Parallel Agent Concurrency (Fan-Out / Fan-In)
- Independent data-gathering operations (`flight_agent` and `hotel_agent`) execute **simultaneously** after intent extraction.
- Reduces total pipeline wait time by **~50%** compared to traditional sequential workflows.
- Disjoint write sets and annotated state reducers (`Annotated[int, operator.add]`) ensure atomic updates without state collisions.

### 2. 🔄 Multi-Turn Conversational Refinement (Human-in-the-Loop)
- Utilizes LangGraph thread checkpointers (`PostgresSaver` with graceful `MemorySaver` fallback).
- Allows users to iteratively refine trips on the same session ID (e.g. *"Make it 5 days instead of 7 and focus more on street food"*).
- The `intent_agent` detects previous conversation context and updates parameters while preserving unchanged preferences.

### 3. 💾 Intelligent In-Memory TTL Tool Caching
- Caches live route lookups (AviationStack) and hotel discoveries (Tavily) with configurable Time-To-Live (1–2 hours).
- Eliminates redundant external API overhead, protects rate limits, and achieves **sub-second repeat responses**.

### 4. 📊 LangSmith Observability & Telemetry
- Native telemetry integration via LangSmith: track token expenditure, per-agent latency, and error rates across all sessions.
- Real-time pipeline latency (`execution_time_seconds`) and cache stats (`cache_stats.hits`) returned on API responses.

### 5. 🎨 Dynamic Web Cockpit
- **Live Multi-Agent Workflow Tracker**: Real-time status cards with pulsing radar indicators for each agent.
- **Categorized Tabbed Deck**: Executive Summary, Day-by-Day Plan, Budget Breakdown, Flight Details, Accommodations, and Full Dossier.
- **Client-Side PDF Generation & Clipboard Sharing**: Clean export for offline itineraries.

---

## 📂 Project Structure

```text
TripMate-AI/
├── app.py                  # FastAPI application with SSE streaming routes
├── config.py               # Centralized settings & LangSmith configuration
├── schemas.py              # Pydantic data contracts & LangGraph TravelState
├── database.py             # Resilient checkpointer (PostgreSQL + MemorySaver fallback)
├── graph.py                # LangGraph StateGraph assembly & streaming engine
├── backend.py              # Backward-compatibility re-export module
├── railway.json            # Railway deployment configuration
├── Procfile                # Cloud process file
├── Dockerfile              # Production multi-stage Docker container
├── docker-compose.yml      # Multi-container orchestration (App + PostgreSQL)
├── requirements.txt        # Pinned Python dependencies
├── agents/                 # Specialized agent implementations
│   ├── __init__.py
│   ├── intent.py           # Structured parameter extractor & refinement handler
│   ├── flight.py           # Flight intelligence with error boundary
│   ├── hotel.py            # Hotel research with query optimization
│   ├── itinerary.py        # Day-by-day itinerary architect
│   ├── budget.py           # Itemized financial audit & savings recommendations
│   └── final.py            # Executive dossier synthesizer
├── tools/                  # Third-party intelligence integrations
│   ├── cache.py            # In-memory TTL caching engine
│   ├── flight_tool.py      # AviationStack route resolver
│   └── tavily_tool.py      # Tavily search discovery
├── static/                 # Dark glassmorphic CSS & responsive JS
│   ├── style.css
│   └── script.js
└── templates/              # Jinja2 HTML layout
    └── index.html
```

---

## 🚀 Quickstart Guide

### Option A: Local Virtual Environment

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/TripMate-AI.git
   cd TripMate-AI
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the root folder:
   ```env
   GROQ_API_KEY=your_groq_api_key
   AVIATIONSTACK_API_KEY=your_aviationstack_api_key
   TAVILY_API_KEY=your_tavily_api_key
   DATABASE_URL=postgresql://postgres:password@localhost:5432/travel_db
   DEFAULT_ORIGIN_IATA=DAC
   
   # Optional: LangSmith Observability
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_PROJECT=TripMate-AI
   ```

5. **Start the Application**:
   ```bash
   python app.py
   ```
   Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

### Option B: Docker Compose (Zero-Config with PostgreSQL)

Run the entire system with an isolated PostgreSQL database using a single command:

```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## ☁️ Deploying to Railway

TripMate AI is pre-configured for seamless deployment to **[Railway](https://railway.app)**:

1. **Push your code to a GitHub repository.**
2. Go to **Railway.app** > Click **New Project** > **Deploy from GitHub Repo**.
3. Select your `TripMate-AI` repository.
4. (Optional) In Railway, click **Add Service** > **Database** > **PostgreSQL** to provision a managed cloud database.
5. In your web service's **Variables** tab, add your environment variables:
   - `GROQ_API_KEY`
   - `TAVILY_API_KEY`
   - `AVIATIONSTACK_API_KEY`
   - `DATABASE_URL` (Reference `${{Postgres.DATABASE_URL}}` if using Railway PostgreSQL, or leave blank to use the automatic MemorySaver fallback!)
6. Railway will automatically detect `Dockerfile` or `railway.json` and deploy. Once complete, click **Generate Domain** to get your public URL!

---

## 📡 API Endpoints Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves the interactive glassmorphic web cockpit |
| `POST` | `/api/travel/stream` | **SSE Endpoint**: Streams live agent progress updates and final dossier |
| `POST` | `/api/travel` | **REST Endpoint**: Synchronous execution returning complete JSON results |
| `GET` | `/health` | Health check with LangSmith status and cache telemetry |

### Sample JSON Request:
```bash
curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 4-day trip to Tokyo with a $1500 budget"}'
```

---

## 💼 Resume Description Template

```markdown
TripMate AI — Autonomous Multi-Agent Travel Planning System
Tech Stack: Python, LangGraph, FastAPI, Groq LLMs, PostgreSQL, Tavily, Docker, Railway

• Architected a parallel multi-agent travel orchestration engine in LangGraph, coordinating 
  6 specialized agents (Intent, Flight, Hotel, Itinerary, Budget, Final Synthesizer) with 
  fan-out/fan-in concurrency to reduce workflow latency by ~50%.
• Built real-time Server-Sent Events (SSE) streaming with an interactive glassmorphic dashboard, 
  visualizing live agent transitions, telemetry metrics, and multi-tab dossier exports.
• Implemented resilient session checkpointing with PostgreSQL and in-memory fallbacks, enabling 
  stateful multi-turn conversational itinerary refinement.
• Designed an in-memory TTL caching layer for third-party flight and search APIs, protecting rate 
  limits and slashing repeat query latency to sub-second speeds.
• Containerized multi-service deployment with Docker & Docker Compose and deployed to Railway Cloud.
```

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
