FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY agent.py .
COPY app.py .

# Cloud Run injects PORT env var; default 8080
ENV PORT=8080

EXPOSE 8080

# Gunicorn: 1 worker is enough for free-tier, saves memory
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "60", "app:app"]
