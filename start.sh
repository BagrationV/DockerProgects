#!/bin/bash

# No need to start Ollama service as it runs in its own container

# Wait for PostgreSQL to be ready
until pg_isready -h postgres -U vit --dbname=vit; do
  echo "Waiting for PostgreSQL to start..."
  sleep 5
done

# Wait for Ollama to be ready
until curl -s http://ollama:11434/api/version > /dev/null; do
  echo "Waiting for Ollama to start..."
  sleep 5
done

# Wait for Ollama to be ready
until curl -s http://ollama:11434/api/version > /dev/null; do
  echo "Waiting for Ollama to start..."
  sleep 5
done

# Run the application
exec uvicorn app:app --host 0.0.0.0 --port 8000