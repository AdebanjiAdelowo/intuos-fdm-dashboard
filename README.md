# AnalysisDashboard

FastAPI backend for flight, pilot, registration, telemetry, and alarm analytics backed by IBM DB2.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yml config.yml  # fill with local DB2 credentials
python app.py
```

Open the API docs at <http://localhost:5001/docs>.

A simple smoke-test endpoint is available at <http://localhost:5001/luciano>.

## Run with Docker Compose

```bash
cp config.example.yml config.yml  # fill with local DB2 credentials
docker compose up --build
```

The compose file mounts `./config.yml` read-only into the container. Secrets are not copied into the Docker image.

## Production configuration

Prefer environment variables over a checked-in config file:

```bash
export DATABASE_USERNAME="..."
export DATABASE_PASSWORD="..."
export DATABASE_HOST="..."
export DATABASE_PORT="50000"
export DATABASE_NAME="..."
export JWT_SECRET="replace-with-a-long-random-secret"
export CORS_ALLOW_ORIGINS="https://your-frontend.example"
```

`config.yml`, `.env`, and runtime token state are intentionally ignored by git.

## Development checks

```bash
pip install -r requirements-dev.txt
python -m compileall -q .
pytest
ruff check .
```
