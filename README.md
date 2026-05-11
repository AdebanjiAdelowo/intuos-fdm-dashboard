# INTUOS FDM — Flight Data Monitoring Dashboard

A full-stack aviation safety analytics platform. FastAPI + IBM DB2 backend, React + Vite frontend with an INTUOS-style dark green theme.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · Python 3.9 · IBM DB2 (ibm_db) |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS |
| Charts | Recharts (bar, donut) |
| Maps | Leaflet (react-leaflet v4) |
| Auth | JWT (HS256) |
| Container | Docker Compose (backend + nginx frontend) |

## Pages

| Route | Page |
|---|---|
| `/` | Home — KPIs and quick-access links |
| `/fleet` | Fleet Overview — alert distribution donut, top aircraft bar chart |
| `/aircraft` | Aircraft Analysis — per-aircraft flights, alert breakdown, top alerting flights |
| `/flights` | Flight Analysis — all flights with route/duration, per-flight alert detail |
| `/pilots` | Pilot Analysis — searchable pilot list, alert breakdown, top flights |
| `/instructors` | Instructor Analysis — same as pilot view, filtered by role |

## Quick start (Docker Compose)

```bash
cp config.example.yml config.yml   # fill in your DB2 credentials
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:5001 |
| API docs | http://localhost:5001/docs |

## Development

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yml config.yml
uvicorn app:app --host 0.0.0.0 --port 5001 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The Vite dev server proxies `/api/*` to `http://localhost:5001`.

## Dev login bypass

Set `DEV_BYPASS_LOGIN=true` in `docker-compose.yml` (already enabled by default) to skip IBM DB2 auth on every request. The `/login` endpoint still issues a JWT; all other endpoints skip the per-user DB lookup and use the `database_user` section from `config.yml` directly.

## Configuration

### config.yml

```yaml
database:          # auth / login database
  username: '...'
  password: '...'
  ip_address: '...'
  port: '50000'
  db_name: '...'

database_user:     # data database (used in DEV_BYPASS_LOGIN mode)
  username: '...'
  password: '...'
  ip_address: '...'
  port: '50000'
  db_name: '...'
```

### Environment variables (production)

```bash
DATABASE_USERNAME="..."
DATABASE_PASSWORD="..."
DATABASE_HOST="..."
DATABASE_PORT="50000"
DATABASE_NAME="..."
JWT_SECRET="replace-with-a-long-random-secret"
JWT_EXPIRATION_HOURS="8"
CORS_ALLOW_ORIGINS="https://your-frontend.example"
DEV_BYPASS_LOGIN="false"
```

`config.yml`, `.env`, and runtime secrets are intentionally excluded from git.

## Alert colour scheme

| Alert type | Colour |
|---|---|
| Vertical Speed | Blue `#3b82f6` |
| Pitch | Yellow `#eab308` |
| Roll | Purple `#8b5cf6` |
| Ground Speed | Orange `#f97316` |
| G-Force | Red `#ef4444` |
| Hard Landing | Cyan `#06b6d4` |
| High Roll | Violet `#a855f7` |

Colours are centralised in `frontend/src/constants/alarmColors.ts` and applied consistently across all donut charts, bar charts, and progress-bar breakdowns.

## Development checks

```bash
pip install -r requirements-dev.txt
python -m compileall -q .
pytest
ruff check .
```
