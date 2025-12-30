import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from app.tools import get_online_tools
from app.utils import build_vectorstore
from config import settings

logging.basicConfig(level=logging.INFO)


logger = logging.getLogger(__name__)

load_dotenv()

DATA_PATHS = [
    "data/langgraph-llms.txt",
    "data/langgraph-llms-full.txt",
    "data/langchain-llms.txt",
    "data/langchain-llms-full.txt",
]


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    mode: Literal["offline", "online"]
    docs: List[Dict[str, Any]]


class HelperAgent:
    """Wrapper around LLM + LangGraph workflow."""

    def __init__(self):
        logger.info("Initializing agent")
        self.mode: Literal["offline", "online"] = os.getenv("AGENT_MODE", "offline")
        self.llm = self._build_llm()
        if self.mode == "offline":
            vs_path = Path("vectorstore/chroma")
            if not vs_path.exists() or not any(vs_path.iterdir()):
                raise RuntimeError(
                    "Offline mode requires a built vectorstore. "
                    "Run `python scripts/ingest_docs.py` first."
                )

        self._setup_retriever()
        self.tools = []
        self.graph = self._build_graph()

    def _build_llm(self) -> Any:
        """Create an LLM client based on env vars."""
        provider = settings.LLM_PROVIDER
        model = settings.MODEL_NAME

        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model,
                api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.2,
            )
        elif provider == "openrouter":
            return ChatOpenAI(
                model=model,
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
                temperature=0.2,
            )
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER={provider}")

    def _setup_retriever(self):
        """Build Chroma vectorstore from docs."""
        logger.info("Setting up retriever")
        vectorstore = build_vectorstore()
        self._offline_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        logger.info("Successfully built VS as retriever")

    def _router(self, state: AgentState):
        return {"branch": state["mode"]}

    def _offline_rag_node(self, state: AgentState):
        question = state["messages"][-1].content
        logger.info(f"Invoked offline RAG node with question: {question}")
        docs = self._offline_retriever.invoke(question)

        context = "\n\n".join(d.page_content for d in docs[:6])
        logger.info(
            f"Retrieved context: {context[:30] if len(context)>30 else context}...\n Full length: {len(context)}"
        )
        prompt = ChatPromptTemplate.from_template(
            "You are a LangGraph/LangChain helper.\n"
            "Use ONLY the provided documentation.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
        chain = prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})

        return {
            "messages": [AIMessage(content=answer)],
            "docs": [d.metadata for d in docs],
        }

    def _online_node(self, state: AgentState):
        logger.info(f"Invoked online node: {state['messages'][-1].content}")
        try:
            self.tools = get_online_tools()
            logger.info(f"Loaded {len(self.tools)} online tools")
        except (ImportError, Exception) as e:
            logger.warning(f"No tools available: {e}")
            self.tools = []

        if not self.tools:
            logger.info(f"No tools found, loading simple LLM")
            question = state["messages"][-1].content
            prompt = ChatPromptTemplate.from_template(
                "You are a LangGraph/LangChain expert. Answer: {question}"
            )
            chain = prompt | self.llm | StrOutputParser()
            answer = chain.invoke({"question": question})
            logger.info(f"Simple LLM answer: {answer}")
            return {"messages": [AIMessage(content=answer)], "docs": []}

        system_prompt = """You are a LangGraph/LangChain expert. 
        Use search tools for latest information. Provide code examples."""
        logger.info("Creating agent with tools")

        agent = create_agent(self.llm, self.tools, system_prompt=system_prompt)

        result = agent.invoke({"messages": state["messages"]})
        logger.info(f"Agent with tools answer: {result['messages']}")

        return {
            "messages": result["messages"],
            "docs": [{"tool": "search", "query": state["messages"][-1].content}],
        }

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("offline_rag", self._offline_rag_node)
        workflow.add_node("online_search", self._online_node)
        workflow.add_node("router", self._router)

        workflow.add_edge(START, "router")
        workflow.add_conditional_edges(
            "router",
            lambda s: s["branch"],
            {
                "offline": "offline_rag",
                "online": "online_search",
            },
        )
        workflow.add_edge("offline_rag", END)
        workflow.add_edge("online_search", END)

        return workflow.compile()

    async def achat(self, messages: List[Dict[str, str]], thread_id: str = "default"):
        """Async chat entry – used by FastAPI."""
        lc_messages: List[BaseMessage] = []
        for m in messages:
            if m["role"] == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            else:
                lc_messages.append(AIMessage(content=m["content"]))

        state = {
            "messages": lc_messages,
            "mode": self.mode,
            "docs": [],
        }

        config = {"configurable": {"thread_id": thread_id}}
        result = await self.graph.ainvoke(state, config=config)
        answer_msg: BaseMessage = result["messages"][-1]
        logger.info(f"Succesfully got answer: {answer_msg}")
        return {
            "answer": answer_msg.content,
            "mode": self.mode,
            "sources": result.get("docs", []),
        }

    def chat(self, messages: List[Dict[str, str]], thread_id: str = "default") -> dict:
        """Sync wrapper for Streamlit."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.achat(messages, thread_id))
        loop.close()
        return result
