# 🔗 **LangGraph Helper Agent** 
*AI-powered coding assistant for LangGraph & LangChain developers*

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](http://localhost:8501)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](http://localhost:8000/docs)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com)

**Dual-mode agent** that answers practical LangGraph/LangChain questions using **offline RAG** (local docs) or **online search** (Tavily)
with **FastAPI API + Streamlit UI**.

## **Quick Start**
**Online**:

set up the .env file with `GEMINI_API_KEY` and `TAVILY_API_KEY`
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**Offline**:
```bash
pip install -r requirements.txt
python scripts/ingest_docs.py
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

## API Keys (free)

    Gemini: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) → GEMINI_API_KEY

    Tavily: [app.tavily.com](https://app.tavily.com) → TAVILY_API_KEY (online mode)


## **Local Setup**

Clone & install

`git clone <https://github.com/tamara-kostova/LangGraph-Helper-Agent.git>`
`pip install -r requirements.txt`
.env

`echo GEMINI_API_KEY=your_key > .env`

`echo TAVILY_API_KEY=your_key > /env`

UI (recommended)

`streamlit run streamlit_app.py`

API

`uvicorn main:app --reload`

### **Docker**
Build (multi-stage, pre-built wheels)

`docker build -t langgraph-helper .`
Run UI

`docker run -p 8501:8501 -e GEMINI_API_KEY=your_key langgraph-helper streamlit run streamlit_app.py`

Run API

`docker run -p 8000:8000 -e AGENT_MODE=online -e GEMINI_API_KEY=your_key langgraph-helper uvicorn main:app`


### **Health Check**
`curl http://localhost:8000/health`
{"status": "healthy", "mode": "offline"}


## **Tech Stack**
- Backend: FastAPI + LangGraph + LangChain V1
- Vector DB: Chroma
- Embeddings: all-MiniLM-L6-v2
- LLM: Gemini 2.0 Flash / OpenRouter
- Tools: Tavily Search
- UI: Streamlit
- Container: Docker (multi-stage)