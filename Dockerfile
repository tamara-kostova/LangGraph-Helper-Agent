FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --only-binary=all && \
    pip cache purge

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .
RUN mkdir -p data vectorstore/chroma

RUN if [ ! -f data/langgraph-llms.txt ]; then \
    curl -o data/langgraph-llms.txt https://langchain-ai.github.io/langgraph/llms.txt && \
    curl -o data/langgraph-llms-full.txt https://langchain-ai.github.io/langgraph/llms-full.txt && \
    curl -o data/langchain-llms.txt https://docs.langchain.com/llms.txt && \
    curl -o data/langchain-llms-full.txt https://docs.langchain.com/llms-full.txt; \
    fi

ENV PYTHONUNBUFFERED=1 \
    AGENT_MODE=offline
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
