from src.rag.get_vector_store_instance import get_vector_store
from langchain_core.tools import tool

@tool
def rag_tool(query: str) -> str:
    """Search the company's knowledge base for company-specific information
    (products, policies, pricing, procedures, etc).

    Args:
        query: A specific question or search phrase.

    Returns:
        Relevant document excerpts with sources, or a message if none found.
    """
    vector_store = get_vector_store()
    docs = vector_store.retrieve_documents(query=query)

    if not docs:
        return "No relevant documents found in the knowledge base."

    formatted = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        formatted.append(f"[Doc {i}] (source: {source})\n{doc.page_content}")

    return "\n\n".join(formatted)