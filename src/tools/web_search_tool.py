from langchain_core.tools import tool
import requests
from config import TRAVILY_API_KEY

@tool
def web_search(query: str) -> str:
    """
    Search the live web for current, up-to-date information NOT found in the
    Smartovate knowledge base — e.g., recent news, events after the knowledge
    base's last update, or general facts unrelated to Smartovate that the user
    explicitly asks about. Do NOT use this for questions already answerable
    from the Smartovate knowledge base.
    """
    print(f"[INFO] using web search for query: {query})")
    resp = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": TRAVILY_API_KEY, "query": query, "max_results": 3}
    )
    results = resp.json().get("results", [])
    
    return "\n".join(f"{r['title']}: {r['content']}" for r in results)