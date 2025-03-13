# AI Chat Assistant

A web-based chat application that uses local LLMs (Large Language Models) via Ollama to provide conversational AI capabilities with memory persistence.

## Overview

This application provides a simple web interface for users to interact with AI language models. It features:

- Real-time chat interface
- Persistent conversation memory across sessions
- Support for multiple language models with fallback options
- Docker containerization for easy deployment
- PostgreSQL database for conversation storage

## Architecture

The application consists of:

1. **Frontend**: HTML/CSS/JavaScript web interface
2. **Backend API**: FastAPI Python application
3. **Database**: PostgreSQL for conversation history storage
4. **LLM Service**: Ollama for running local language models

## Dependencies

### Backend Dependencies
- Python 3.9+
- FastAPI
- Uvicorn (ASGI server)
- Psycopg2 (PostgreSQL adapter)
- Requests (HTTP client)
- Aiofiles
- Python-multipart

### Frontend Dependencies
- Pure HTML/CSS/JavaScript (no external libraries required)

### Infrastructure Dependencies
- Docker and Docker Compose
- PostgreSQL
- Ollama (running in a separate container)

## Docker Setup

The application is containerized using Docker for easy deployment. The setup includes:

1. **FastAPI Application Container**: Runs the Python backend
2. **PostgreSQL Container**: Stores conversation history
3. **Ollama Container**: Runs the LLM service

### Dockerfile Explanation

```dockerfile
FROM python:3.9-slim

# Install curl and PostgreSQL client
RUN apt-get update && \
    apt-get install -y curl postgresql-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]