# Daily Word Service

## Problem Statement

This project delivers a Python-based RESTful service that fetches the daily word from Wordsmith's RSS feed, uses OpenAI to generate a compact article, and caches that generated result so it can be served efficiently throughout the day. The service is intentionally small in product scope but structured like a production-ready backend so it can demonstrate clear modularity, testability, daily refresh behavior, and upgrade paths.

## Why This Project Fits The Challenge

- Python REST API built with FastAPI
- GenAI feature built around article generation
- Package-based runtime under `src/daily_word_service`
- Modular service boundaries for API, configuration, feed ingestion, generation, caching, and scheduling
- Containerized execution and deterministic tests

## Architecture Summary

The runtime package lives under `src/daily_word_service` and is split into focused modules:

- `main.py`: FastAPI app bootstrap and lifespan management
- `api.py`: REST routes and HTTP error mapping
- `settings.py`: typed environment-backed settings
- `rss.py`: Wordsmith feed client
- `genai.py`: OpenAI integration using the modern SDK
- `cache.py`: cache abstraction with an in-memory implementation
- `service.py`: orchestration layer for fetch, generation, cache, and health
- `scheduler.py`: optional refresh scheduling

This separation keeps framework concerns away from the core orchestration logic and makes each dependency easy to replace or mock.

## API Endpoints

- `GET /word-of-the-day`: returns the cached or freshly generated article
- `POST /word-of-the-day/refresh`: forces a refresh and updates the cache
- `GET /health`: reports readiness, cache state, scheduler state, and the last refresh error

Example response:

```json
{
  "header": "A daily word worth knowing today",
  "body": "A concise definition with usage and an interesting detail."
}
```

## Local Run

1. Configure environment variables in `.env`.
2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Start the API:

```bash
PYTHONPATH=src uvicorn daily_word_service.main:app --host 0.0.0.0 --port 8000
```

## Docker Run

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000/word-of-the-day`.

## Running Tests

```bash
python3 -m pytest
```

Or with Docker:

```bash
docker compose run --rm tests
```

## Configuration

- `OPENAI_API_KEY`: API key for OpenAI
- `OPENAI_MODEL`: model used for article generation, default `gpt-4o-mini`
- `WORDSMITH_RSS_FEED`: RSS feed source
- `CACHE_TTL`: cache time-to-live in seconds
- `ENABLE_SCHEDULER`: enables the daily refresh scheduler

## Scalability And Quality Choices

- The API layer is thin, and orchestration is isolated in a service class for maintainability.
- The cache is hidden behind an interface so Redis or another distributed cache can replace it later without changing the API routes.
- Startup is resilient: the service can boot even if RSS or OpenAI is temporarily unavailable.
- Health reporting exposes degraded states instead of failing silently.
- External dependencies are mocked in tests so the suite is stable and fast.

## Future Improvements

- Replace the in-memory cache with Redis for multi-instance deployments.
- Persist refresh history for traceability and analytics.
- Add request correlation IDs and richer structured logging.
- Add retry and circuit-breaker policies around upstream dependencies.
- Introduce CI workflows and dependency pinning for tighter release control.
