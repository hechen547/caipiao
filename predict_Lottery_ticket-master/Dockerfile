# syntax=docker/dockerfile:1
FROM python:3.8-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2

WORKDIR /app

# System deps (for lxml wheels typically not needed, but build tools are helpful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first to leverage layer cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Default entrypoint runs the one-click DLT predictor
ENTRYPOINT ["python", "dlt_predict_app.py"]
# You can pass args like: --predict-only or --force-train
CMD []