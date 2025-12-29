import logging
import os
from pathlib import Path
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)


logger = logging.getLogger(__name__)


def load_docs(paths: list[str]):
    logger.info(f"Loading docs from paths: {paths}")
    docs = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n## ", "\n### ", "\n- ", "\n1. "],
    )
    for path in paths:
        if os.path.exists(path):
            loader = TextLoader(path, encoding="utf-8")
            raw_docs = loader.load()
            for doc in raw_docs:
                doc.metadata["source"] = Path(path).name
            chunks = splitter.split_documents(raw_docs)
            docs.extend(chunks)
        else:
            logger.warning(f"Missing file: {path}")

    logger.info(f"Succesfully loaded docs")
    return docs


def build_vectorstore(docs: Optional[List] = None) -> Chroma:
    """Build Chroma vectorstore."""
    persist_directory = "vectorstore/chroma"
    os.makedirs(persist_directory, exist_ok=True)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    logger.info("Building vector store")

    if docs:
        logger.info(f"Building Chroma with {len(docs)} docs")
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name="langgraph_docs",
        )
        logger.info(f"Successfully built vector store with {len(docs)} docs")
    else:
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name="langgraph_docs",
        )
        count = vectorstore._collection.count()
        logger.info(f"Loaded existing vector store with {count} docs")

    return vectorstore
