FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libmagic1 build-essential python3-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=main.py
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PORT=8080
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app
EXPOSE 8080
CMD gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0
