from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document
from typing import List
import os


def load_pdfs(folder_path: str) -> List[Document]:
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    loader = DirectoryLoader(
        path=folder_path,
        glob="**/*.pdf", 
        loader_cls=PyPDFLoader,
    )

    return loader.load()