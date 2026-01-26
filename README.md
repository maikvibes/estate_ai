# Estate AI Background Services

Async FastAPI + Kafka + Google GenAI worker that reviews real-estate listings, orchestrates AI agents, and persists results to MongoDB.

## Features
- REST API to enqueue generic agent tasks via Kafka.
- Listing reviewer worker consuming `listings.new`, applying strict business rules with Google GenAI ADK, posting webhook results.
- Kafka wrapper for async producer/consumer with resilient loops.
- MongoDB persistence with indexes for agent runs.
- Vector store abstraction with local Chroma default (no auth) and in-memory fallback.
- Start scripts for Windows (`start_service.bat`) and bash (`start_service.sh`).

## Tech Stack
- Python 3.11+
- FastAPI, Uvicorn
- aiokafka
- MongoDB via Motor
- Google GenAI ADK
- Chroma (local vector DB)
- httpx

## Configuration
Environment-driven via `app/core/config.py`. Key vars:
- `KAFKA_BOOTSTRAP_SERVERS` (default `localhost:9092`)
- `KAFKA_REQUESTS_TOPIC` (default `agent.requests`)
- `KAFKA_LISTINGS_TOPIC` (default `listings.new`)
- `MONGODB_URI` (default `mongodb://localhost:27017`)
- `MONGODB_DB` (default `estate_ai`)
- `GOOGLE_GENAI_API_KEY`, `GOOGLE_GENAI_MODEL`
- `LISTING_REVIEW_WEBHOOK_URL` (default `https://api.estatecompany.com/listings/review`)
- `LISTING_REVIEW_SECRET`
- `CHROMA_PERSIST_DIR` (default `.chroma`)

Create a `.env` file or set env vars before running.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running
Bash:
```bash
./start_service.sh api      # API only
./start_service.sh worker   # Worker only
./start_service.sh both     # Worker bg + API fg
```
Windows:
```bat
start_service.bat api
start_service.bat worker
start_service.bat both
```

## Services
- API: FastAPI at `/api`, main entry `app/main.py`, enqueue route in `app/api/routes.py`.
- Worker: `app/worker.py` starts Kafka consumer for generic agent tasks and listing reviewer when wired.
- Listing reviewer: Agent + consumer in `app/agents/listing_reviewer.py` and `app/services/listing_consumer.py`; sends webhook with structured JSON (status/risk_score/feedback).

## Testing
```bash
pytest
```

## Notes
- Ensure Kafka and MongoDB are running and reachable.
- Chroma writes to `.chroma/`; clean it if you want a fresh index.
- Set `LISTING_REVIEW_SECRET` for webhook auth.
