# Trustpilot DGC Take-Home – Senior Data Engineer (IC5)

A compact, production-minded PoC that:

1. **Ingests** a reviews CSV into a relational DB (SQLite by default; Postgres if `DATABASE_URL` is set).  
2. **Normalises** data into `users`, `businesses`, `reviews` tables and tracks lineage in `ingest_metadata`.  
3. **Serves** ad-hoc extract APIs with CSV output, with governance controls (masking, expanded joins, etc.).

---

## 📦 Quickstart

```bash
# 1) (Optional) Set up a virtual environment
python -m venv .venv && source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Ingest data
python -m app.ingest --csv data/reviews.csv

# 4) Run the API
uvicorn app.main:app --reload
```

Open interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔄 Switching Between SQLite and Postgres

By default, the app uses SQLite (`sqlite:///./reviews.db`). You can override with:

```bash
export DATABASE_URL=postgres://trustuser:trustpass@localhost:5432/reviews
uvicorn app.main:app --reload
```

The application reads `DATABASE_URL` and configures SQLAlchemy accordingly.

Docker Compose sets this for you automatically for local Postgres + API.

---

## API (CSV Downloads)

All endpoints stream `text/csv`.

### Core review extracts (normalized, least-privilege columns)
- `GET /reviews/business/{business_id}`
  - Query params: `start_date`, `end_date`, `min_rating`, `max_rating`, `limit`, `offset`
- `GET /reviews/user/{user_id}`
  - Same filters as above

### Expanded (joined) review views
- `GET /reviews/business/{business_id}/expanded`
  - Query params: `mask_pii` (default `true`), `limit`, `offset`
- `GET /reviews/user/{user_id}/expanded`
  - Query params: `mask_pii` (default `true`), `limit`, `offset`

### Entity lookup
- `GET /users/{user_id}` (PII masked by default)
- `GET /health` (simple status)

### PII masking
- By default, `email`, `user_name`, and `ip_address` are masked in expanded endpoints and the user endpoint (see [`mask_row`](app/pii.py)).  
- Disable with `mask_pii=false` (intended only for privileged use in production with RBAC).  

### Examples

```bash
# Business reviews (normalized, filtered by rating)
curl -L "http://127.0.0.1:8000/reviews/business/abc123?min_rating=4" -o business_reviews.csv

# User reviews in a time window (normalized)
curl -L "http://127.0.0.1:8000/reviews/user/user_42?start_date=2023-01-01&end_date=2023-12-31" -o user_reviews.csv

# Expanded business reviews (joined + masked PII)
curl -L "http://127.0.0.1:8000/reviews/business/abc123/expanded" -o business_reviews_expanded.csv

# Expanded user reviews without masking (privileged use only)
curl -L "http://127.0.0.1:8000/reviews/user/user_42/expanded?mask_pii=false" -o user_reviews_expanded_raw.csv

# User info (masked)
curl -L "http://127.0.0.1:8000/users/user_42" -o user_info.csv
```

---

## Data Model

Tables (see [`app/models.py`](app/models.py)):

- **users** (`user_id` PK, `user_name`, `email`, `country`)  
- **businesses** (`business_id` PK, `business_name`)  
- **reviews** (`review_id` PK, `user_id` FK, `business_id` FK, `rating`, `title`, `text`, `created_at`, `ip_address`)  
  - `created_at` defaults to DB timestamp if missing.  
- **ingest_metadata** (see [`IngestMetadata`](app/metadata.py)) tracks lineage for each load.  

If your CSV contains only a flat reviews table, ingestion **derives** `users` and `businesses` from it (see [`run`](app/ingest.py)).

---

## Governance Hooks (PII/Lineage/Quality)

- **PII masking**: `user_email`, `user_name`, and `ip_address` are masked by default. Toggle with `mask_pii`.  
- **Lineage**: each ingest writes a row to [`ingest_metadata`](app/metadata.py) with `source_path`, row counts, and file hash.  
- **Quality checks**: [`basic_validations`](app/validate.py) enforce non-null keys, rating range, timestamp coercion. Extend with Great Expectations/dbt in production.

---

## Tests

```bash
pytest -q
```

---

## 📦 Docker & Docker-Compose

```bash
# Build local SQLite container
docker build -t trust-api .

# Run with Postgres via compose
docker-compose up --build
# Ingest within API container
docker-compose run --rm api python -m app.ingest --csv data/reviews.csv
```

- API exposed at `:8000`, Postgres at `:5432`  
- API configured to use Postgres via `DATABASE_URL` in compose file  

---

## 🧪 Testing & CI/CD

Run tests locally:

```bash
pytest -q
```

**GitHub Actions** pipeline:

- **PRs** → run tests on SQLite + Postgres  
- **Push to main** → run tests + **build & push** Docker image to GHCR  
- Image tagged `latest` (and optionally commit SHA tag)

---

## 🛠 Repo Structure

```
app/
  api.py             # FastAPI routes / request handling
  main.py            # FastAPI app instantiation
  models.py          # ORM definitions
  database.py        # Engine & session setup
  ingest.py          # Data ingestion logic
  constants.py       # Column/table name constants + rename mappings
  pii.py             # Masking logic (email, name, ip)
  utils.py           # Shared helpers (e.g. sa_to_dict)
  schemas.py         # Header definitions (for CSV output)
  validate.py        # Data quality checks & validation rules
  metadata.py        # Ingest lineage tracking
  crud.py            # Database CRUD operations
  config.py          # Configuration & environment settings
tests/
Dockerfile
docker-compose.yml
README.md
Design.md
```

---

## 💡 Debrief & Notes

- **Least privilege design**: exposure is minimal by default; expanded endpoints unlock richer data but with masking.  
- **Upsert strategy**: dimensions via batch upsert to avoid duplicates; reviews treated as immutable events.  
- **Production path**: in a full deployment, you'd integrate schema/catalog tooling (DataHub/OpenMetadata), dbt as transformation layer, and more rigorous data quality enforcement.  
- **Masking and RBAC**: `mask_pii=false` is available in PoC; in production access to unmasked outputs would be guarded.  
- **Scalability considerations**: for large extracts, use pagination, efficient streaming, and scaling API workers.
