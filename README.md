# 🔗 **LangGraph Helper Agent** 
*AI-powered coding assistant for LangGraph & LangChain developers*

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](http://localhost:8501)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](http://localhost:8000/docs)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com)

**Dual-mode agent** that answers practical LangGraph/LangChain questions using **offline RAG** (local docs) or **online search** (Tavily). Production-ready with **FastAPI API + Streamlit UI**.

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
#### **Weekly Cron Job** (Sunday 2AM)
    Download fresh llms.txt files

    Rebuild Chroma vectorstore

    Log freshness timestamp

    Zero-downtime (background)

### **Manual trigger**
`curl -X POST http://localhost:8000/admin/refresh`, or:
    Download: curl https://langchain-ai.github.io/langgraph/llms.txt

    Recreate Vector store with `scripts/ingest_docs.py`:

        Chunk: RecursiveCharacterTextSplitter(chunk_size=800, overlap=100)

        Embed: HuggingFaceEmbeddings(all-MiniLM-L6-v2) → Chroma/FAISS

        Query: similarity_score_threshold (k=4, score>0.7)

## API Keys (free)

    Gemini: https://aistudio.google.com/app/apikey → GEMINI_API_KEY

    Tavily: https://app.tavily.com → TAVILY_API_KEY (online mode)


## **Local Setup**

Clone & install

git clone <repo>
pip install -r requirements.txt
.env

echo GEMINI_API_KEY=your_key > .env
echo TAVILY_API_KEY=your_key > /env

UI (recommended)

`streamlit run streamlit_app.py`

API

`uvicorn main:app --reload`

### **Docker**
Build (multi-stage, pre-built wheels)

`docker build -t langgraph-helper .`
Run UI

`docker run -p 8501:8501 -e GEMINI_API_KEY=your_key langgraph-helper`

Run API

`docker run -p 8000:8000 -e AGENT_MODE=online -e GEMINI_API_KEY=your_key langgraph-helper`


### **Health Check**
`curl http://localhost:8000/health`
{"status": "healthy", "mode": "offline"}


## **Tech Stack**
Backend: FastAPI + LangGraph + LangChain V1
Vector DB: Chroma/FAISS
Embeddings: all-MiniLM-L6-v2
LLM: Gemini 2.0 Flash / OpenRouter
Tools: Tavily Search
UI: Streamlit
Container: Docker (multi-stage)