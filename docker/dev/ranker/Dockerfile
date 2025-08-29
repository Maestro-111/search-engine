FROM python:3.12-slim

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    libpq-dev \
    curl \
    ca-certificates \
    gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Set working directory and copy files
COPY pyproject.toml poetry.lock* /app/
WORKDIR /app

# Install Python dependencies
RUN poetry install --no-root --only main,ranker

# Copy the app code
COPY ranker /app/ranker

# Default environment variables
ENV MONGODB_URI=mongodb://mongodb:27017 \
    MONGODB_DATABASE=wikipedia_db \
    MONGODB_COLLECTION=articles

CMD ["python", "/app/ranker/pipeline.py"]
