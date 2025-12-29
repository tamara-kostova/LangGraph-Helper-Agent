from app.utils import build_vectorstore, load_docs

DOC_PATHS = [
    "data/langgraph-llms.txt",
    "data/langgraph-llms-full.txt",
    "data/langchain-llms.txt",
    "data/langchain-llms-full.txt",
]

if __name__ == "__main__":
    docs = load_docs(DOC_PATHS)
    build_vectorstore(docs)
    print("Ingestion complete.")
