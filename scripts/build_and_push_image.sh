#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <ecr-image-uri>"
  exit 1
fi

IMAGE_URI="$1"
REGISTRY_HOST="${IMAGE_URI%%/*}"
AWS_REGION="${AWS_REGION:-us-east-1}"
EMBED_MODEL_NAME="${EMBED_MODEL_NAME:-BAAI/bge-base-en-v1.5}"
RERANK_MODEL_NAME="${RERANK_MODEL_NAME:-BAAI/bge-reranker-v2-m3}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY_HOST}"

docker buildx build \
  --platform linux/arm64 \
  --build-arg EMBED_MODEL_NAME="${EMBED_MODEL_NAME}" \
  --build-arg RERANK_MODEL_NAME="${RERANK_MODEL_NAME}" \
  -t "${IMAGE_URI}" \
  --push \
  "${ROOT_DIR}"

echo "Pushed ${IMAGE_URI}"
