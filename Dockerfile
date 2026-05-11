FROM python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ANALYSIS_DASHBOARD_CONFIG=/app/config.yml

EXPOSE 5001

# Install dependencies first for better Docker layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --default-timeout=100 --no-cache-dir -r requirements.txt \
    && pip install uvicorn

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
