#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <ecr-image-uri>"
  exit 1
fi

IMAGE_URI="$1"
REGISTRY_HOST="${IMAGE_URI%%/*}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY_HOST}"

docker buildx build \
  --platform linux/arm64 \
  -t "${IMAGE_URI}" \
  --push \
  "${ROOT_DIR}"

echo "Pushed ${IMAGE_URI}"
