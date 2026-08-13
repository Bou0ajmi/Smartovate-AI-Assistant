from langchain_community.vectorstores import FAISS
from typing import List, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from langchain_core.documents import Document

class VectorStore:
    def __init__(self, embedding_model,chunk_size: int = 1200, chunk_overlap: int = 200):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = None

    def chunk_documents(self, documents):
        splitter= RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n· ", "\n", ". ", " ", ""]
            )
        chunks=splitter.split_documents(documents)
        print(f"Total chunks created: {len(chunks)}")
        return chunks
    

    def create_vector_store(self, documents: List[Document])->None:
        print(f"[INFO] Creating vector store for {len(documents)} documents...")
        chunks=self.chunk_documents(documents)
        self.vector_store = FAISS.from_documents(chunks, self.embedding_model)
        print(f"[INFO] Vector store created with {self.vector_store.index.ntotal} vectors.")

    def save_vector_store(self, file_path: str):
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        self.vector_store.save_local(file_path)
        print(f"[INFO] Vector store saved to {file_path}")

    def load_vector_store(self, file_path: str):
        try:
            self.vector_store = FAISS.load_local(file_path,
                                                self.embedding_model,
                                                allow_dangerous_deserialization=True
                                                )
            print(f"[INFO] Vector store loaded from {file_path} with {self.vector_store.index.ntotal} vectors.")
        except Exception as e:
            print("problem loading the vector store\n")
            print(e)
    
    def add_documents(self, new_documents: List[Document]):
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        new_chunks = self.chunk_documents(new_documents)
        print(f"[INFO] Adding {len(new_chunks)} new chunks to the vector store...")
        self.vector_store.add_documents(new_chunks)
        print(f"[INFO] Vector store now contains {self.vector_store.index.ntotal} vectors.")
    
    def retrieve_documents(self, query: str, top_k: int = 5) -> str:
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        print(f"[INFO] Retrieving top {top_k} similar documents for the query: '{query}'")
        results = self.vector_store.similarity_search(query, k=top_k)
        return results
    
    