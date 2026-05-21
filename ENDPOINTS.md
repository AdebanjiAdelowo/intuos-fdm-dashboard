# API Endpoints

Base URL: `http://localhost:5001`

---

## Auth

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/luciano` | Health-check / sanity ping |
| `POST` | `/login` | Authenticate with email + password; returns JWT |

---

## Flights

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/flights` | All flights |
| `GET` | `/flight/{id}/time_duration` | Duration of a specific flight |
| `GET` | `/telemetry/flight/{id}` | Raw telemetry samples for a flight |
| `GET` | `/registration/{registration_id}/flights` | All flights for an aircraft registration |
| `GET` | `/pilot/{pilot_id}/flights` | All flights for a pilot |
| `GET` | `/registration/{registration_id}/flights/{start_date}/{end_date}` | Flights for a registration within a date range |
| `GET` | `/pilot/{pilot_id}/flights/{start_date}/{end_date}` | Flights for a pilot within a date range |
| `POST` | `/registration/flights/{start_date}/{end_date}` | Flights for multiple registrations (IDs in body) within a date range |
| `POST` | `/pilot/flights/{start_date}/{end_date}` | Flights for multiple pilots (IDs in body) within a date range |

---

## Flew Hours

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/flewhours/pilot/{pilot_id}/flights/{start_date}/{end_date}` | Total flew hours/minutes for a pilot in a date range |
| `GET` | `/flewhours/registration/{registration_id}/flights/{start_date}/{end_date}` | Total flew hours/minutes for a registration in a date range |

---

## Registrations (Aircraft)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/all_registrations` | All aircraft registrations |
| `GET` | `/all_registrations_count` | Total count of registrations |
| `GET` | `/registrations_with_flights` | Registrations that have at least one flight |
| `GET` | `/registrations_with_flights_count` | Count of registrations with flights |

---

## Pilots

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/all_pilots` | All pilots |
| `GET` | `/all_pilots_count` | Total count of pilots |
| `GET` | `/pilots_with_flights` | Pilots that have at least one flight |
| `GET` | `/pilots_with_flights_count` | Count of pilots with flights |
| `GET` | `/all_pilots_pg/{start_date}/{end_date}` | Paginated pilots with flight and alarm stats in a date range |
| `GET` | `/all_pilots_search/{start_date}/{end_date}` | Searchable pilots with flight and alarm stats in a date range |

---

## Alarms

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/registrations/alarms/{start_date}/{end_date}` | Alarm counts per registration in a date range |
| `GET` | `/top_registrations/alarms/{top}/{start_date}/{end_date}` | Top N registrations by alarm count in a date range |
| `GET` | `/registration/{registration_id}/alarms` | All alarms for a registration (all time) |
| `GET` | `/pilot/{pilot_id}/alarms` | All alarms for a pilot (all time) |
| `GET` | `/registration/{registration_id}/alarms/{start_date}/{end_date}` | Alarms for a registration in a date range |
| `GET` | `/pilot/{pilot_id}/alarms/{start_date}/{end_date}` | Alarms for a pilot in a date range |
| `GET` | `/registration/{registration_id}/{top}/alarms/{start_date}/{end_date}` | Top N alarms for a registration in a date range |
| `GET` | `/pilot/{pilot_id}/{top}/alarms/{start_date}/{end_date}` | Top N alarms for a pilot in a date range |
| `GET` | `/alarms/flight/{id}` | All alarms for a specific flight |
| `GET` | `/alarms/flight/{id}/{top}` | Top N alarms for a specific flight |

---

## Flights with Alarms

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/registration/{registration_id}/flightswithalarms/{start_date}/{end_date}` | Flights that triggered alarms for a registration in a date range |
| `GET` | `/pilot/{pilot_id}/flightswithalarms/{start_date}/{end_date}` | Flights that triggered alarms for a pilot in a date range |
| `GET` | `/registration/{registration_id}/top_flightswithalarms/{top}/{start_date}/{end_date}` | Top N alarm-triggering flights for a registration in a date range |
| `GET` | `/pilot/{pilot_id}/top_flightswithalarms/{top}/{start_date}/{end_date}` | Top N alarm-triggering flights for a pilot in a date range |

---

## Telemetry

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/registration/{registration_id}/telemetry/{start_date}/{end_date}` | Telemetry samples for a registration in a date range |
| `GET` | `/pilot/{pilot_id}/telemetry/{start_date}/{end_date}` | Telemetry samples for a pilot in a date range |
| `POST` | `/registration/telemetry/{start_date}/{end_date}` | Telemetry for multiple registrations (IDs in body) in a date range |
| `POST` | `/pilot/telemetry/{start_date}/{end_date}` | Telemetry for multiple pilots (IDs in body) in a date range |
| `GET` | `/registrations/alarms/telemetry/{start_date}/{end_date}` | Alarm-flagged telemetry samples across all registrations in a date range |
| `POST` | `/registration/alarms/telemetry/{start_date}/{end_date}` | Alarm-flagged telemetry for specific registrations (IDs in body) in a date range |

---

## Notes

- All `{start_date}` / `{end_date}` parameters use `YYYY-MM-DD` format.
- All endpoints except `/login` and `/luciano` require a Bearer JWT in the `Authorization` header.
- `DEV_BYPASS_LOGIN=true` (default in development) skips per-request token validation.
- Interactive docs available at `http://localhost:5001/docs`.
