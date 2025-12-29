import logging
from typing import List

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

from config import settings

logging.basicConfig(level=logging.INFO)


logger = logging.getLogger(__name__)


@tool
def search_langchain_docs(query: str) -> str:
    """Search for latest LangChain/LangGraph information online."""
    logger.info(f"Calling search docs tool with query: {query}")
    return TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        api_key=settings.TAVILY_API_KEY,
    ).invoke(query)


def get_online_tools() -> List:
    """Return online search tools."""
    return [search_langchain_docs]
