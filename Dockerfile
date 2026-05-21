FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ANALYSIS_DASHBOARD_CONFIG=/app/config.yml

EXPOSE 5001

# Build deps needed to compile ibm_db C extension
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libxml2-dev \
        libxslt-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better Docker layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copy application code. Secrets are intentionally not baked into the image.
COPY app.py .
COPY datamodels.py .
COPY db_connection_params_handler.py .
COPY flight_envelope_limits.yaml .
COPY logic/ logic/
COPY controllers/ controllers/
COPY db_handlers/ db_handlers/
COPY mappers/ mappers/
COPY orm/ orm/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
