FROM python:3.12-slim


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user for development
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y curl \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# Install Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# Set working directory and copy files
COPY pyproject.toml poetry.lock* /app/

# Install Python dependencies
RUN poetry install --no-root --only main,webserver

# Copy the app code
COPY webserver /app/webserver
COPY .env /app/
COPY Makefile /app/
COPY entrypoint.sh /app/entrypoint.sh

RUN chown -R $USERNAME:$USERNAME /app
RUN chmod +x /app/entrypoint.sh

USER $USERNAME

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["webserver_worker"]
