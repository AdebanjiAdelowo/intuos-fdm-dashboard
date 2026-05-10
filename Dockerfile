FROM python:3.9

WORKDIR /app

EXPOSE 5001

# Install dependencies first (better caching)
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt
# Copy application code
COPY app.py .
COPY datamodels.py .
COPY db_connection_params_handler.py .
COPY config.yml .
COPY flight_envelope_limits.yaml .

COPY logic/ logic/
COPY controllers/ controllers/
COPY db_handlers/ db_handlers/
COPY mappers/ mappers/
COPY orm/ orm/

CMD ["python", "app.py"]