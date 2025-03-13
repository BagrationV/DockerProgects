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