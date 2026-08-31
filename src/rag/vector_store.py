from langchain_community.vectorstores import FAISS
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())  # library code shouldn't force its own handler

class VectorStore:
    def __init__(self, embedding_model, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = None

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n· ", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        logger.info("Total chunks created: %d", len(chunks))
        return chunks

    def create_vector_store(self, documents: List[Document]) -> None:
        logger.info("Creating vector store for %d documents...", len(documents))
        chunks = self.chunk_documents(documents)
        self.vector_store = FAISS.from_documents(chunks, self.embedding_model)
        logger.info("Vector store created with %d vectors.", self.vector_store.index.ntotal)

    def save_vector_store(self, file_path: str) -> None:
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        self.vector_store.save_local(file_path)
        logger.info("Vector store saved to %s", file_path)

    def load_vector_store(self, file_path: str) -> None:
        try:
            self.vector_store = FAISS.load_local(
                file_path,
                self.embedding_model,
                allow_dangerous_deserialization=True
            )
            logger.info(
                "Vector store loaded from %s with %d vectors.",
                file_path, self.vector_store.index.ntotal
            )
        except Exception:
            logger.exception("Problem loading the vector store from %s", file_path)
            raise

    def add_documents(self, new_documents: List[Document]) -> None:
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        new_chunks = self.chunk_documents(new_documents)
        logger.info("Adding %d new chunks to the vector store...", len(new_chunks))
        self.vector_store.add_documents(new_chunks)
        logger.info("Vector store now contains %d vectors.", self.vector_store.index.ntotal)

    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Document]:
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        logger.info("Retrieving top %d similar documents for the query: '%s'", top_k, query)
        return self.vector_store.similarity_search(query, k=top_k)