# Cloud Billing Data Migration Pipeline

> Entry-level portfolio project — a realistic, runnable ETL/migration pipeline demonstrating
> Python backend, SQL, REST APIs, Docker, CI/CD, and Azure deployment practices.
> Everything here reflects a fresher-level build, not claimed production experience.

**Status:** 🚧 Phase 9 of 14 — REST ingestion, validation, transformation, migration, reconciliation, FastAPI integration, reliability testing, and Docker Compose implemented; later phases remain pending.

---

## Table of Contents
*(sections below are placeholders — filled in as each phase completes)*

1. Project Overview — *pending*
2. Business Problem — *pending*
3. Architecture — see `docs/architecture.md` (Phase 14)
4. Features — *pending*
5. Technology Stack — see below (stable as of Phase 1)
6. Project Structure — see below
7. Local Setup — *pending (Phase 2)*
8. Environment Variables — see `.env.example`
9. Database Setup — see below (Phase 3)
10. Running the Application — *pending (Phase 7)*
11. Running Migration — *pending (Phase 6)*
12. Running Tests — *pending (Phase 8)*
13. Docker Setup — *pending (Phase 9)*
14. CI/CD — *pending (Phase 10)*
15. Azure Deployment — *pending (Phase 11)*
16. Terraform — *pending (Phase 12)*
17. Monitoring — *pending (Phase 13)*
18. Security — see `docs/security.md` (Phase 14)
19. Troubleshooting — *pending*
20. Future Improvements — *pending*

---

## Technology Stack (confirmed for this project)

- **Backend:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy, PyMySQL/mysql-connector-python, httpx
- **Database:** MySQL 8
- **Testing:** pytest
- **Code quality:** Ruff, Black
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Cloud:** Microsoft Azure (Container Apps + Azure Database for MySQL + Azure Monitor, low-cost alternatives documented before any real deployment)
- **Infrastructure as Code:** Terraform

## Project Structure

```
billing-data-migration-pipeline/
├── app/
│   ├── main.py                   # FastAPI entrypoint
│   ├── api/routes.py             # /health, /api/migration/*, /api/transactions/*
│   ├── config/settings.py        # env-driven configuration
│   ├── database/                 # connection.py, models.py
│   ├── ingestion/api_client.py   # external REST API client
│   ├── validation/validators.py  # Pydantic validation rules
│   ├── transformation/transformer.py
│   ├── migration/migration_service.py
│   ├── reconciliation/reconciliation_service.py
│   ├── monitoring/health.py
│   └── utils/logger.py
├── tests/                        # pytest suite (mirrors app/ layers)
├── data/                         # sample_billing_data.json, rejected_records.json
├── scripts/                      # init_db.py, seed_database.py, run_migration.py (--dry-run)
├── sql/                          # schema.sql, queries.sql
├── docker/Dockerfile
├── terraform/                    # main.tf, variables.tf, outputs.tf, README.md
├── .github/workflows/ci-cd.yml
├── docs/                         # architecture.md, security.md
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE
```

**Why this structure:**
- `app/` is layered by pipeline stage (ingestion → validation → transformation → migration → reconciliation), not by technical type — each folder maps directly to one step in section 2's architecture diagram, so the code and the docs stay traceable to each other.
- `config/` and `database/` are isolated from business logic so credentials and connection handling never leak into validation/transformation code, and so the app is easy to point at a different DB or environment later.
- `scripts/` holds one-off/CLI operations (seeding, running a migration) separately from the long-running `app/` service — these are invoked directly, not imported by the API.
- `terraform/` and `docker/` are kept out of `app/` entirely — infrastructure and application code are versioned and reviewed separately, which also means the Python app has zero dependency on how or where it's deployed.
- `docs/` holds narrative documentation (architecture, security) that doesn't belong inline in code or in the top-level README's quick-reference sections.

## Environment Variables

See `.env.example` for the full list (API credentials, MySQL connection, app/log config). Copy it to `.env` for local development — `.env` is git-ignored and must never be committed.

## Phase 3: Database Layer

Phase 3 adds the SQLAlchemy 2.x database layer for MySQL through PyMySQL. It defines the
`BillingTransaction` model and a reusable FastAPI database-session dependency. Initialize
the schema explicitly with `python scripts/init_db.py`; importing the application does not
initialize the database automatically.

## Phase 7: FastAPI API

The FastAPI integration exposes the existing services without duplicating their business
logic:

- `GET /health` returns the existing health response.
- `POST /api/v1/migration/validate` validates and transforms a batch without database writes.
- `POST /api/v1/migration/run` validates, transforms, migrates, and reconciles a batch.
- `GET /api/v1/migration/status/{external_transaction_id}` checks whether a transaction exists.

Migration requests use the `transactions` batch property. Invalid records are reported as
rejected and are never migrated. Repeated external transaction IDs remain idempotent and
are reported as skipped duplicates. Interactive OpenAPI documentation is available at
`/docs` when the application is running.

## Phase 6: Migration and Reconciliation

Phase 6 composes the pipeline as **validation → transformation → migration → reconciliation**.
Only valid, transformed records are migrated through SQLAlchemy. Migration is idempotent:
an existing or repeated `external_transaction_id` is skipped rather than inserted again.
The migration uses an atomic transaction and rolls back the batch if a database operation
fails. Reconciliation checks expected external IDs against the database and reports missing
records, count mismatches, and duplicate rows without claiming success when records are missing.

## Testing and Reliability

Phase 8 adds layered reliability coverage:

- Unit tests cover ingestion error handling, validation, transformation, migration, and reconciliation.
- API tests cover request validation, partial batches, empty and larger batches, idempotency, status lookups,
  and safe database error responses.
- Full-pipeline tests exercise validation → transformation → migration → reconciliation.
- Failure-path tests cover HTTP errors, timeouts, connection failures, invalid JSON, rollback, malformed records,
  invalid amounts, missing fields, and reconciliation mismatches.
- Migration and API tests use isolated in-memory SQLite databases and mocked HTTP transports; they do not require
  MySQL, external APIs, credentials, or production services.
- Quality checks include pytest, Ruff, Black, and Python bytecode compilation.

## Phase 9: Docker Compose

### Prerequisites

Install Docker Desktop with Docker Compose support. Copy `.env.example` to `.env` and
replace the placeholder passwords with local development values. Never commit `.env`.

Build and start the application and MySQL database:

```text
docker compose build
docker compose up
```

Run in the background:

```text
docker compose up -d
```

The FastAPI application is available at `http://localhost:8000`; Swagger/OpenAPI is at
`http://localhost:8000/docs`. View application logs with `docker compose logs -f app`,
and stop the stack with `docker compose down`.

Inside Compose, the application connects to MySQL using `MYSQL_HOST=mysql`. For local
Windows execution outside Docker, use `MYSQL_HOST=localhost` in `.env`. Compose waits
for the MySQL health check before starting the application, then runs the existing
`scripts/init_db.py` explicitly to create the SQLAlchemy tables.

MySQL data persists in the named `mysql_data` volume. To intentionally remove the
persistent database and start clean, run:

```text
docker compose down -v
```

This removes the named volume and all local database data.
