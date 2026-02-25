# Vocal Remover POC

FastAPI service that separates vocals and accompaniment using Spleeter, with async processing via Celery and Redis.

## Features
- JWT login and authenticated endpoints
- Async audio separation via Celery worker
- Task status and history
- Simple rate limit on `/api/v1/separate` (2 requests per 30 seconds)

## Tech Stack
- FastAPI
- Celery + Redis
- SQLite (local `database/app.db`)
- Spleeter for audio separation

## Project Layout
- `app/main.py` FastAPI app
- `app/api/v1/` API routes
- `app/services/audio_processing.py` Spleeter processing
- `app/worker/` Celery worker
- `data/` input/output audio data
- `database/` SQLite DB

## Prereqs
- Docker Desktop

## Quick Start (Docker Compose)
```bash
docker compose up --build
```

The API will be available at `http://127.0.0.1:8000`.

## API Overview
All endpoints are under `/api/v1`.

### Auth
`POST /login`

Request:
```json
{
  "email": "test@example.com",
  "password": "password"
}
```

Response:
```json
{
  "access_token": "JWT",
  "token_type": "bearer"
}
```

Use `Authorization: Bearer <token>` for protected routes.

### Audio Separation
`POST /separate`

Request:
```json
{
  "filename": "example.mp3"
}
```

Notes:
- File must exist in `data/sample/`.
- Only `.mp3` is processed by the splitter.
- Rate limit: 2 requests per 30 seconds.

Response:
```json
{
  "task_id": "uuid"
}
```

### Status
`GET /status/{task_id}`

Response:
```json
{
  "task_id": "uuid",
  "status": "queued|processing|completed|failed"
}
```

### History
`GET /history`

Returns a list of recent tasks for the current user.

## Data Paths
Outputs are written under:
- `data/output/<source_name>/vocals.wav`
- `data/output/<source_name>/accompaniment.wav`

## Environment Variables
- `REDIS_URL` (default `redis://redis:6379/0`)

## Development Notes
- SQLite is used by both API and worker; heavy concurrency may hit locks.
- The limiter uses `fastapi-limiter` 0.2.0 with `pyrate-limiter`.
