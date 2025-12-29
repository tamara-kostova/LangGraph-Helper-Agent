import asyncio
import os

import streamlit as st
from dotenv import load_dotenv

from app.agent import HelperAgent
from config import settings

load_dotenv()

st.set_page_config(
    page_title="🔗 LangGraph Helper Agent", page_icon="🔗", layout="wide"
)

st.sidebar.title("🔧 LangGraph Helper")
mode = st.sidebar.selectbox("Mode", ["offline", "online"], index=0)

if "current_mode" not in st.session_state:
    st.session_state.current_mode = mode

if st.sidebar.button("🔄 Switch Mode", use_container_width=True):
    st.session_state.current_mode = mode
    st.cache_resource.clear()
    st.rerun()

st.sidebar.info(f"**Mode**: {st.session_state.current_mode}")


@st.cache_resource(ttl=300)
def get_agent(_mode: str) -> HelperAgent:
    os.environ["AGENT_MODE"] = _mode
    agent = HelperAgent()
    st.info(f"✅ Agent loaded in {_mode} mode")
    return agent


agent = get_agent(st.session_state.current_mode)

st.title("🔗 LangGraph Helper Agent")
st.markdown("**Live mode switching + full conversation history**")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander(f"📚 {len(message['sources'])} Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**{i}.** `{source.get('source', 'Web')}`")
                    content = source.get("content", "")
                    st.markdown(
                        content[:300] + "..." if len(content) > 300 else content
                    )

if prompt := st.chat_input("💭 Ask about LangGraph/LangChain..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"🤔 {st.session_state.current_mode.title()} mode..."):
            try:
                result = agent.chat(
                    [{"role": "user", "content": prompt}], thread_id="streamlit"
                )
            except AttributeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    agent.achat([{"role": "user", "content": prompt}], "streamlit")
                )
                loop.close()

            st.markdown(result["answer"])

            sources = result.get("sources", [])
            if sources:
                with st.expander(f"📚 {len(sources)} sources"):
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"**{i}.** `{source.get('source', 'Web')}`")
                        content = source.get("content", "")
                        st.markdown(
                            content[:400] + "..." if len(content) > 400 else content
                        )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": sources,
                    "mode": st.session_state.current_mode,
                }
            )

    st.rerun()

if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
**✨ Features:**
- ✅ Live mode switching
- ✅ Conversation history  
- ✅ Source citations
- ✅ Fast startup (50 docs)

**🔑 API Keys:**
- [Google AI Studio](https://aistudio.google.com)
- [Tavily](https://app.tavily.com)
"""
)
