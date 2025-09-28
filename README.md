# Trustpilot DGC Take‑Home – Senior Data Engineer (IC5)

A compact, production‑minded PoC that:
1) **Ingests** a Reviews CSV into a relational DB (SQLite by default).
2) **Models & cleans** data into `users`, `businesses`, `reviews` tables.
3) **Serves** ad‑hoc requests via an **API** that returns **CSV** downloads:
   - Reviews **for a business**
   - Reviews **by a user**
   - **User account** info
   - (Expanded) Joined review + user + business views

## Quickstart

```bash
# 1) Create & activate a virtualenv (optional)
python -m venv .venv && source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Ingest your CSV (put it under ./data/ as reviews.csv or pass --csv path)
python -m app.ingest --csv data/reviews.csv

# 4) Run the API
uvicorn app.main:app --reload
```

Open the docs at http://127.0.0.1:8000/docs

## API (CSV Downloads)

All endpoints stream `text/csv`.

Core review extracts (narrow columns from [`HEADERS["reviews"]`](app/schemas.py)):
- `GET /reviews/business/{business_id}`
  - Query params: `start_date`, `end_date`, `min_rating`, `max_rating`, `limit`, `offset`
- `GET /reviews/user/{user_id}`
  - Same filters as above

Expanded (joined) review views (columns from [`HEADERS["reviews_expanded"]`](app/schemas.py)):
- `GET /reviews/business/{business_id}/expanded`
  - Query params: `mask_pii` (default `true`), `limit`, `offset`
- `GET /reviews/user/{user_id}/expanded`
  - Query params: `mask_pii` (default `true`), `limit`, `offset`

Entity lookup:
- `GET /users/{user_id}` (PII masked by default)
- `GET /health` (simple status)

PII masking:
- Email masking applied in expanded endpoints & user endpoint via `mask_pii` (see [`to_expanded_review_dict`](app/crud.py) and [`mask_row`](app/pii.py)).
- Set `mask_pii=false` to return raw email in expanded endpoints.

### Examples

```bash
# Filtered business reviews (narrow)
curl -L "http://127.0.0.1:8000/reviews/business/abc123?min_rating=4" -o business_reviews.csv

# User reviews time window (narrow)
curl -L "http://127.0.0.1:8000/reviews/user/user_42?start_date=2023-01-01&end_date=2023-12-31" -o user_reviews.csv

# Expanded business reviews (joined + masked PII)
curl -L "http://127.0.0.1:8000/reviews/business/abc123/expanded" -o business_reviews_expanded.csv

# Expanded user reviews without masking
curl -L "http://127.0.0.1:8000/reviews/user/user_42/expanded?mask_pii=false" -o user_reviews_expanded_raw.csv

# User info (masked)
curl -L "http://127.0.0.1:8000/users/user_42" -o user_info.csv
```

## Data Model

Tables (see [`app/models.py`](app/models.py)):

- **users** (`user_id` PK, `user_name`, `email`, `country`)
- **businesses** (`business_id` PK, `business_name`)
- **reviews** (`review_id` PK, `user_id` FK, `business_id` FK, `rating`, `title`, `text`, `created_at`, `ip_address`)
  - `created_at` defaults to DB timestamp if missing.
- **ingest_metadata** (see [`IngestMetadata`](app/metadata.py)) tracks lineage for each load.

If your CSV only contains a single flat reviews table, ingestion **derives** `users` and `businesses` from it (see [`run`](app/ingest.py)).

## Governance Hooks (PII/Lineage/Quality)

- **PII tagging**: Columns tagged in `app/pii.py` are masked by default in user + expanded review endpoints (email → `***@example.com`). Disable with `mask_pii=false`.
- **Lineage**: Each ingest writes a row to [`ingest_metadata`](app/metadata.py) with source path + row counts.
- **Quality**: Basic validations in [`basic_validations`](app/validate.py) (non‑null keys, rating range). Extend as needed.

## Tests

```bash
pytest -q
```

## Productionisation Notes (for debrief)

- Swap SQLite for Postgres (`DATABASE_URL` in [`app/config.py`](app/config.py)).
- Containerize + deploy (ECS/Fargate/K8s).
- Schedule ingestion (CRON/Airflow/Prefect).
- Add observability, authn/z, rate limits.
- Integrate catalog/lineage (DataHub/Collibra).
- Add Great Expectations/dbt tests in CI/CD.

---

**Time‑saving defaults**: sensible schema, streaming CSV responses, clear tests, single ingest command.
