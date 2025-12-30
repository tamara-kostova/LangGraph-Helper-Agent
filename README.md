# 🔗 **LangGraph Helper Agent** 
*AI-powered coding assistant for LangGraph & LangChain developers*

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

**Dual-mode agent** that answers practical LangGraph/LangChain questions using **offline RAG** (local docs) or **online search** (Tavily)
with **FastAPI API + Streamlit UI**.

## **Quick Start**

### Prerequisites
Create a `.env` file with your API keys:
```bash
GEMINI_API_KEY=your_gemini_key        # Required for both modes
TAVILY_API_KEY=your_tavily_key        # Required for online mode only
```

### **Online Mode**
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### **Offline Mode**
```bash
pip install -r requirements.txt
python scripts/ingest_docs.py          # Build vectorstore (one-time setup)
streamlit run streamlit_app.py
```
## **Architecture Overview**

![alt text](<LangGraph Helper Agent Workflow.png>)
### **Graph Design**
START → Router → Conditional Edge → {offline: RAG, online: Tools} → END
- **State**: `AgentState(messages, mode, docs)` with `add_messages` reducer
- **Router**: Simple `state["mode"]` branch
- **Offline RAG**: Chroma + `sentence-transformers/all-MiniLM-L6-v2`
- **Online Tools**: Tavily Search (ReAct agent via `langchain.agents.create_agent`)

## **Operating Modes**

### **Offline Mode**
User Query → Chroma Similarity Search → LLM + Context → Answer + Sources
- **Retriever**: Chroma vectorstore
- **Data**: txt files in `data` folder
- **Embedding**: `all-MiniLM-L6-v2` (384-dim)
- **Chunking**: 800 chars with 100 chars overlap

#### Offline Data Preparation
Offline mode relies on a locally built vectorstore created from official
LangGraph and LangChain documentation.
The data/ directory contains the offline documentation source.

To keep application startup fast and deterministic, document ingestion
is performed as a **separate, explicit step**.

##### Ingestion Script

Before starting the application in offline mode, run:

```bash
python scripts/ingest_docs.py
```

⚠️ **Important**
Offline mode requires a pre-built Chroma vectorstore.

The application does **not** ingest documents at startup to avoid long initialization times.
If the vectorstore is missing, the agent will raise an error.

You must run the ingestion script at least once before starting the app in offline mode.

### **Online Mode**
User Query → LangChain Agent → Tavily Search → Reasoning Loop → Answer
- **Tools**: TavilySearchResults (5 max results, `include_answer=True`)
- **Agent**: `create_agent(llm, tools, system_prompt)`
- **Free tier**: 1000 searches/month

### **Mode Switching**
Streamlit: Sidebar dropdown + "Switch Mode" → Cache clear → New agent

FastAPI: AGENT_MODE=offline|online env var

Docker: -e AGENT_MODE=online

CLI: export AGENT_MODE=online

## **Data Freshness Strategy**
### **Automated Data Refresh** (Built-in)
#### **Scheduled Background Job (APScheduler)** (Sunday 2AM)
The application includes a built-in background scheduler (APScheduler)
that periodically refreshes offline documentation.

The refresh process:
1. Downloads the latest LangGraph and LangChain documentation
2. Rebuilds the persisted Chroma vectorstore on disk
3. Stores a freshness timestamp

Note:
- The vectorstore is rebuilt **out-of-band**
- A running agent continues using the existing retriever
- The refreshed data is picked up on the **next agent initialization**
  (app restart or mode switch)

This design avoids blocking requests or reloading embeddings at runtime.

### Manual Data Refresh

POST /admin/refresh triggers an immediate documentation download
and vectorstore rebuild.

Note: the refreshed data will be used by newly initialized agents.

## **API Keys** (Free Tier)

### Required for Both Modes
- **Gemini API**: [Google AI Studio](https://aistudio.google.com/app/apikey)
  - Set as `GEMINI_API_KEY` in `.env`
  - Free tier: 1500 requests/day (Gemini 2.5 Flash Lite)

### Required for Online Mode Only
- **Tavily Search**: [Tavily Dashboard](https://app.tavily.com)
  - Set as `TAVILY_API_KEY` in `.env`
  - Free tier: 1000 searches/month


## **Local Setup**

### Clone Repository
```bash
git clone https://github.com/tamara-kostova/LangGraph-Helper-Agent.git
cd LangGraph-Helper-Agent
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Setup Environment Variables
```bash
echo "GEMINI_API_KEY=your_key" > .env
echo "TAVILY_API_KEY=your_key" >> .env
```

### Build Vectorstore (Required for Offline Mode)
```bash
python scripts/ingest_docs.py
```

### Run Application

**Streamlit UI (Recommended)**
```bash
streamlit run streamlit_app.py
```

**FastAPI Server**
```bash
uvicorn main:app --reload
```

### **Docker**

#### Build Image
**Note**: Initial build takes **5-10 minutes** as it:
1. Installs all Python dependencies
2. Downloads LangGraph/LangChain documentation (7MB)
3. Builds the Chroma vectorstore with embeddings

```bash
docker build -t langgraph-helper .
```

The image is **ready-to-run** with the vectorstore pre-built for offline mode.

#### Run Containers

**Using Environment File (Recommended)**

Create a `.env` file with your configuration (see Setup Environment Variables above), then:

**Streamlit UI**
```bash
docker run --env-file .env -p 8501:8501 langgraph-helper streamlit run streamlit_app.py
```

**FastAPI Server**
```bash
docker run --env-file .env -p 8000:8000 langgraph-helper
```

**Using Individual Environment Variables**

**Streamlit UI (Offline Mode)**
```bash
docker run -p 8501:8501 \
  -e GEMINI_API_KEY=your_key \
  langgraph-helper streamlit run streamlit_app.py
```

**FastAPI Server (Offline Mode)**
```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  langgraph-helper
```

**FastAPI Server (Online Mode)**
```bash
docker run -p 8000:8000 \
  -e AGENT_MODE=online \
  -e GEMINI_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  langgraph-helper
```

**Streamlit UI (Online Mode)**
```bash
docker run -p 8501:8501 \
  -e AGENT_MODE=online \
  -e GEMINI_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  langgraph-helper streamlit run streamlit_app.py
```


### **Health Check**
`curl http://localhost:8000/health`

{"status": "healthy", "mode": "offline"}


## **Tech Stack**
- **Backend**: FastAPI + LangGraph + LangChain V1
- **Vector DB**: Chroma (persistent, disk-based)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, local)
- **LLM**: Google Gemini 2.5 Flash Lite (configurable: Gemini/OpenRouter)
- **Search Tools**: Tavily Search API (online mode)
- **UI**: Streamlit with live mode switching
- **Container**: Docker multi-stage build (optimized for size)
- **Scheduler**: APScheduler (automated data refresh)