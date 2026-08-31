from langchain_core.tools import tool
import requests
import logging
from config import TRAVILY_API_KEY

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@tool
def web_search(query: str) -> str:
    """
    Search the live web for current, up-to-date information NOT found in the
    Smartovate knowledge base — e.g., recent news, events after the knowledge
    base's last update, or general facts unrelated to Smartovate that the user
    explicitly asks about. Do NOT use this for questions already answerable
    from the Smartovate knowledge base.
    """
    logger.info("Using web search for query: %s", query)
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TRAVILY_API_KEY, "query": query, "max_results": 3},
            timeout=10
        )
        resp.raise_for_status()
    except requests.RequestException:
        logger.exception("Web search request failed for query: %s", query)
        return "Web search failed. Please try again later."

    results = resp.json().get("results", [])
    logger.info("Web search returned %d results for query: %s", len(results), query)

    return "\n".join(f"{r['title']}: {r['content']}" for r in results)