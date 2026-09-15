# INTUOS FDM: Flight Data Monitoring Dashboard

A full-stack aviation safety analytics platform. FastAPI + IBM DB2 backend, React + Vite frontend with an INTUOS-style dark green theme and Tremor component library.

## Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · Python 3.11 · IBM DB2 (`ibm_db 3.2.8`) |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · Tremor |
| Charts | Tremor (DonutChart, BarChart) · Recharts (custom-colour charts) |
| Maps | Leaflet (react-leaflet v4) |
| Auth | JWT (HS256) |
| Container | Docker Compose (backend + nginx frontend) · `linux/amd64` |

## Pages

| Route | Page |
|---|---|
| `/` | Home: KPI cards and top-registrations bar chart |
| `/fleet` | Fleet Overview: alert distribution donut, top aircraft bar chart, breakdown table |
| `/aircraft` | Aircraft Analysis: per-aircraft flights, alert breakdown, top alerting flights, flight map |
| `/flights` | Flight Analysis: all flights with route/duration, per-flight alert detail |
| `/pilots` | Pilot Analysis: searchable/paginated pilot list, alarm breakdown, recent flights |
| `/instructors` | Instructor Analysis: same as pilot view, filtered by role |

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

> **Apple Silicon (M-series) note:** The backend image is built for `linux/amd64` (set in both the `Dockerfile` `FROM` line and `docker-compose.yml`). Docker Desktop runs it under Rosetta. This is required because `ibm_db` has no `linux/arm64` wheel.

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

## API endpoints

A full list of all 43 endpoints is documented in [ENDPOINTS.md](ENDPOINTS.md).

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
| Low GS | Rose `#f43f5e` |
| Altitude | Green `#10b981` |
| Acc Z | Slate `#64748b` |

Colours are centralised in `frontend/src/constants/alarmColors.ts` and applied consistently across all donut charts, bar charts, and progress-bar breakdowns.

## Development checks

```bash
pip install -r requirements-dev.txt
python -m compileall -q .
pytest
ruff check .
```

## Security Notes

A prior security review identified and fixed an alarm-logic precedence bug and a default
auth-bypass setting, both now covered by tests. Rotating the DB2 credential used in earlier
development is a remaining external action (not a code or documentation change) and is not
addressed in this repository.
