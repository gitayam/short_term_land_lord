#!/bin/bash
# Setup PostgreSQL schema within Docker network

echo "Creating PostgreSQL schema..."

# Run Python script in the same network as PostgreSQL
docker run --rm \
    --network landlord_network \
    -v "$(pwd)":/app \
    -w /app \
    -e DATABASE_URL="postgresql://landlord:password@landlord_postgres:5432/landlord_prod" \
    python:3.11-slim \
    sh -c "pip install -q -r requirements.txt psycopg2-binary && python3 create_postgres_schema.py"

echo "Schema creation complete!"