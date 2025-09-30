# 📐 Design Document – Trustpilot Data Governance & Compliance Take-Home

## 1) Goals

- Provide **governed, auditable extracts** of review data for legal/compliance & analyst consumers.  
- Balance **least-privilege** outputs with an **expanded** convenience view when justified.  
- Keep the solution small, testable, and production-minded.

---

## 2) Principles

- **Least privilege by default**: normalized endpoints don’t expose PII.  
- **PII safety**: masking is **on by default**; unmask only when explicitly requested (`mask_pii=false`) and, in production, gated by RBAC.  
- **Lineage**: every ingest is recorded (`source_path`, row counts, file hash, timestamps).  
- **Extensibility**: schema names and headers are centralized; swapping DBs is a config change.  
- **Separation of concerns**: ingestion vs. serving vs. masking vs. schema constants are clearly separated.

---

## 3) Data Model

### Source CSV (example columns)
- Review Id, Reviewer Name, Review Title, Review Rating, Review Content, Review IP Address, Business Id, Business Name, Reviewer Id, Email Address, Reviewer Country, Review Date

### Normalized Schema (SQLAlchemy models)
- **users** (`user_id` PK, `user_name`, `email`, `country`)  
- **businesses** (`business_id` PK, `business_name`)  
- **reviews** (`review_id` PK, `user_id` FK, `business_id` FK, `rating`, `title`, `text`, `created_at`, `ip_address`)  
- **ingest_metadata** (per-load lineage: `source_path`, `total_rows`, `loaded_rows`, `file_hash`, timestamps)

> **Why normalized?**  
> - Centralizes PII to a single place (user), simplifies masking.  
> - Avoids duplication, simplifies ownership and quality rules.  
> - Scales better for governance and future datasets.

**Schema governance** is encoded in `app/constants.py`:
- **Source→normalized rename map**  
- **Field constants** (e.g., `F_USER_ID`)  
- **Table name constants** (e.g., `TBL_USERS`)  

---

## 4) Ingestion Design

### Behavior
- **Batch upserts for dimensions (`users`, `businesses`)**:  
  - Read existing keys.  
  - De-duplicate incoming rows.  
  - Insert only new keys (idempotent).  
- **Append-only for facts (`reviews`)**:  
  - Insert only unseen `review_id`.  
  - Treat reviews as immutable events.

### Why batch upsert?
- In SQLite, row-by-row `merge` can attempt duplicate inserts for repeating keys in the same transaction.  
- Batch upsert avoids UNIQUE violations and is more efficient.  
- In production (Postgres), we’d use `INSERT … ON CONFLICT DO UPDATE`.

### Lineage
- Each run writes a row in `ingest_metadata`:  
  - `source_path`, `total_rows`, `loaded_rows`  
  - `file_hash` (sha256)  
  - created/updated timestamps

---

## 5) Serving (API)

- **Framework**: FastAPI  
- **Format**: streaming `text/csv` for all endpoints  
- **Normalized extracts**:  
  - `/reviews/business/{business_id}` and `/reviews/user/{user_id}` return **minimal** columns  
- **Expanded extracts**:  
  - `/reviews/*/expanded` join `reviews` + `users` + `businesses`  
  - `mask_pii=true` by default (mask `user_email`, `user_name`, `ip_address`)  
  - `mask_pii=false` for privileged use (RBAC in production)

**Headers**: centralized in `app/schemas.py` → prevents drift between code and documentation.

**Conversion**: ORM→dict via helper (`sa_to_dict`) and header-driven projection to keep outputs consistent and ordered.

---

## 6) PII & Quality Controls

- **PII fields**: `user_email`, `user_name`, `ip_address`  
  - Masked in expanded outputs + user endpoint by default  
  - Unmasked only with explicit flag (RBAC in prod)  
- **Validations** (lightweight):  
  - Non-null keys for PKs  
  - Rating constrained 1–5  
  - Timestamps coerced to UTC or `NULL`  
- Extensible to **Great Expectations** or **dbt tests**.

---

## 7) DevEx & Ops

- **Switch DBs via `DATABASE_URL`** (SQLite default; Postgres for compose/CI).  
- **Dockerfile** for containerizing API; **docker-compose** for local Postgres + API.  
- **CI/CD (GitHub Actions)**:  
  - On **PR** → run tests on SQLite + Postgres.  
  - On **push to `main`** → tests + **build & push** image to GHCR (`:latest` and optionally `:<short-sha>`).  
- **Logging**: keep it simple (stdout + FastAPI logs). In production → centralize logs and add metrics.

---

## 8) Future Enhancements

- **Data Catalog & Lineage**: integrate **DataHub/OpenMetadata** (ingest DB metadata, tag PII, show column-level lineage).  
- **Transformations**: move modeling and tests to **dbt** (docs, exposures, and PII tagging via `meta`).  
- **Data Quality**: **Great Expectations** suite run in CI and in Airflow/Prefect on ingestion.  
- **Access Control**: RBAC/OIDC for API; only allow unmasked extracts for authorized roles, with request-level audit logging.  
- **Deletion workflows**: support GDPR “Right to be Forgotten” (cascading deletes or tombstoning with audit).  
- **Scale**: cursor pagination for very large extracts; optional parquet export; async workers.

---

## 9) Trade-offs & Rationale

- **Batch upsert vs. ORM merge**: chose batch upsert for dimensions to avoid SQLite duplicate insert issues within a single transaction; reviews are append-only. In Postgres we’d prefer `ON CONFLICT` upserts for all.  
- **CSV streaming vs. JSON**: CSV is more natural for ad-hoc compliance/analyst downloads.  
- **Masking flag**: kept in API to demonstrate governance; would be **RBAC-protected** in production.  
- **Catalog/quality tooling**: out-of-scope to integrate fully; simulated via constants + validations to keep PoC lean but forward-compatible.

---

✍️ Author: Hasnat
