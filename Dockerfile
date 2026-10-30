# Dockerfile - Standalone Production Container for SafeChat NLP Web Application
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Install system dependencies (build-essential, curl, git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition first for Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy model & NLTK linguistic corpora inside Docker image
RUN python -m spacy download en_core_web_sm && \
    python -m nltk.downloader punkt punkt_tab stopwords averaged_perceptron_tagger averaged_perceptron_tagger_eng

# Copy application files
COPY . .

# Pre-train and bake model artifacts if not already present
RUN python train_and_syllabus.py

# Expose server port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/ping || exit 1

# Production server start using gunicorn with gevent worker
CMD exec gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:${PORT} app:app
