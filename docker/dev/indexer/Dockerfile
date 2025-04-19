FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Set working directory and copy files
COPY pyproject.toml poetry.lock* /app/
WORKDIR /app

# Install Python dependencies
RUN poetry install --no-root --only main,indexer

# Copy the app code
COPY indexer /app/indexer

# Default environment variables
ENV MONGODB_URI=mongodb://mongodb:27017 \
    MONGODB_DATABASE=wikipedia_db \
    MONGODB_COLLECTION=articles

ENTRYPOINT ["/bin/bash"]

