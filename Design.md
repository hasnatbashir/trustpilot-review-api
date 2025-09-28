# 📐 Design Document – Trustpilot Data Governance & Compliance Take-Home

## 1. Problem Overview
The goal of this project is to ingest a Trustpilot reviews dataset and expose an API for ad-hoc legal/compliance requests. Typical queries:  
- Reviews for a given business  
- Reviews by a given user  
- User account information  

The API must return results in CSV format.  

---

## 2. Design Principles
- **Governance First**: PII must be masked by default; access to unmasked data must be deliberate.  
- **Least Privilege**: Base endpoints expose only minimal, normalized data.  
- **Flexibility**: “Expanded” endpoints provide richer joins for compliance/legal use cases.  
- **Extensibility**: Schema and code structured for easy scaling to more datasets and requests.  
- **Transparency**: Centralized schema definitions and documented design decisions.  

---

## 3. Data Model

### Source Dataset
| Column            | Notes                          | PII |
|-------------------|--------------------------------|-----|
| Review Id         | Unique review key              | No  |
| Reviewer Name     | Free text                      | Yes |
| Review Title      | Short text                     | No  |
| Review Rating     | 1–5                            | No  |
| Review Content    | Free text                      | No  |
| Review IP Address | Sensitive                      | Yes |
| Business Id       | Unique business key            | No  |
| Business Name     | Free text                      | No  |
| Reviewer Id       | Unique reviewer key            | No  |
| Email Address     | Sensitive                      | Yes |
| Reviewer Country  | Country code/text              | No  |
| Review Date       | ISO timestamp                  | No  |

### Normalized Schema
- **raw_reviews**: direct CSV ingest for lineage & traceability.  
- **users**: reviewer details (PII lives here).  
- **businesses**: business details.  
- **reviews**: fact table referencing `users` + `businesses`.  

This normalization avoids data duplication and centralizes PII governance.  

---

## 4. API Design

### Base Endpoints (Normalized, Minimal)
- `/reviews/business/{business_id}` → reviews only (FKs for users).  
- `/reviews/user/{user_id}` → reviews only (FKs for businesses).  
- `/users/{user_id}` → user info (masked).  

### Expanded Endpoints (Convenience, Richer Joins)
- `/reviews/business/{business_id}/expanded` → reviews + user + business details.  
- `/reviews/user/{user_id}/expanded` → reviews + user + business details.  

### Governance Feature
- **`mask_pii` flag**: defaults to `true`.  
  - When `true` → emails and IPs masked.  
  - When `false` → unmasked values returned (in production, only with RBAC).  

---

## 5. Governance & Compliance Features
- **PII Masking**: emails partially obfuscated, IPs anonymized.  
- **Masking Flag**: safe by default, flexible for compliance.  
- **Schema Centralization**: CSV headers defined in `schemas.py` for consistency.  
- **Lineage Metadata**: ingest logs record file name, hash, timestamp, row count.  
- **Auditability**: structure allows logging of API calls for compliance reporting.  

---

## 6. Testing
- **Unit tests** cover:  
  - Ingestion (row counts match source).  
  - Base endpoints return correct structure.  
  - Expanded endpoints return joined data.  
  - Masking flag works as expected.  
- Framework: `pytest`.  

---

## 7. Productionization
If deployed to production, I would:  
- Replace SQLite → PostgreSQL or BigQuery.  
- Containerize with Docker, deploy on AWS ECS/Fargate or Kubernetes.  
- Schedule ingestion with Airflow/Prefect.  
- Add data quality tests with **Great Expectations**.  
- Add lineage & cataloging with **DataHub** or **dbt docs**.  
- Implement **RBAC** around `mask_pii=false` requests.  
- Add monitoring (Prometheus, Grafana, logging).  

---

## 8. Future Extensions
- Support additional request types (e.g., reviews by date range).  
- Add pagination for large extracts.  
- Expose metadata endpoints (`/lineage`, `/schemas`).  
- Enhance compliance features (Right to be Forgotten, GDPR delete requests).  

---

✍️ *Author: Hasnat  
