FROM python:3.11-slim

WORKDIR /app

ARG EMBED_MODEL_NAME=BAAI/bge-base-en-v1.5
ARG RERANK_MODEL_NAME=BAAI/bge-reranker-v2-m3

ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/opt/huggingface \
    TRANSFORMERS_CACHE=/opt/huggingface \
    MODEL_CACHE_DIR=/opt/huggingface

COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts/prefetch_models.py ./scripts/prefetch_models.py
COPY taxonomy ./taxonomy

RUN mkdir -p "${HF_HOME}" \
    && python scripts/prefetch_models.py \
      --embed-model "${EMBED_MODEL_NAME}" \
      --cache-dir "${HF_HOME}"

RUN python scripts/prefetch_models.py \
      --rerank-model "${RERANK_MODEL_NAME}" \
      --cache-dir "${HF_HOME}"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

CMD ["python", "-m", "app.main"]
