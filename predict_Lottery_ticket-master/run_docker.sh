#!/usr/bin/env bash
set -euo pipefail
IMAGE_NAME="dlt-predictor:latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build
docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

# Ensure host dirs exist for persistence
mkdir -p "$SCRIPT_DIR/model" "$SCRIPT_DIR/data"

# Run; forward args to the app (e.g., --predict-only)
docker run --rm -it \
  -v "$SCRIPT_DIR/model:/app/model" \
  -v "$SCRIPT_DIR/data:/app/data" \
  "$IMAGE_NAME" "$@"