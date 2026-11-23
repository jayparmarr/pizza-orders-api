# Pizza Orders API

A REST API for pizza orders and sales analytics, built with FastAPI, SQLAlchemy and SQLite. It is the Python counterpart of my Node.js Pizza Ordering System: the same domain (orders, peak hours, revenue KPIs) behind a documented, tested API.

## Features

- Create, list, fetch and delete orders (`/orders`)
- Input validation with Pydantic: blank names, zero quantities, negative prices and empty orders are rejected with `422`
- Paging with a capped page size
- Analytics: revenue summary (`/analytics/summary`) and busiest hours (`/analytics/peak-hours`)
- Automated tests (pytest) and a CI pipeline (GitHub Actions)
- Docker image that runs as a non-root user

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API documentation.

Set `DATABASE_URL` to use another database (for example MySQL or PostgreSQL). The default is a local SQLite file.

## Run the tests

```bash
pytest -v
```

## Run with Docker

```bash
docker build -t pizza-orders-api .
docker run -p 8000:8000 pizza-orders-api
```

## Example

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Asha", "items": [{"pizza": "Margherita", "quantity": 2, "unit_price": 10}]}'

curl http://localhost:8000/analytics/summary
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/orders` | Create an order |
| GET | `/orders?skip=0&limit=20` | List orders |
| GET | `/orders/{id}` | Get one order (`404` if missing) |
| DELETE | `/orders/{id}` | Delete an order |
| GET | `/analytics/summary` | Order count, total revenue, average order value |
| GET | `/analytics/peak-hours` | Orders per hour, busiest first |

## Deploy (free tier)

Push this repository to GitHub, then create a Web Service on Render (or Azure App Service for Containers) pointing at the repository. Render detects the Dockerfile automatically. Add the live URL here once it is deployed.

## Project layout

```
app/
  main.py       routes and analytics queries
  models.py     SQLAlchemy models
  schemas.py    request and response validation
  database.py   engine and session
tests/
  test_api.py   13 tests
Dockerfile
.github/workflows/ci.yml
```
