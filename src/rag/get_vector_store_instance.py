from src.models.embedding_model import get_embedding_model
from src.rag.vector_store import VectorStore
from functools import lru_cache

@lru_cache
def get_vector_store():
    store = VectorStore(embedding_model=get_embedding_model())
    store.load_vector_store("MyVectorStore") # create a new vector store if it doesn't exist
    return store
