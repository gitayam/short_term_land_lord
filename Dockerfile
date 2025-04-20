FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure template directories exist
RUN mkdir -p /app/app/templates/auth /app/app/templates/custom

# Make entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

ENV FLASK_APP=app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=1

EXPOSE 5000

# Use the entrypoint script instead of direct command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
