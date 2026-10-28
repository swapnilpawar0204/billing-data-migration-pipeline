# SRE Interview Guide: Billing Data Migration Pipeline

Use this guide to explain what is implemented in this repository accurately. Do not describe planned work as completed production experience.

## 60-second project explanation

“I built a Python billing data migration service using FastAPI, SQLAlchemy, and MySQL, with Docker Compose for local deployment and GitHub Actions for CI. It accepts billing transactions from a JSON file or an external API, validates and normalizes them, writes valid records in an atomic database transaction, skips previously processed external transaction IDs, and reconciles the expected IDs against the target database. I also added bounded retries for transient source API failures, a database health endpoint, request IDs for log correlation, API-key authentication, and automated tests. The project is a local portfolio implementation; cloud deployment, metrics, and alerting are still future work.”

## Pipeline walkthrough

1. **Ingestion:** CLI reads JSON or the API client fetches raw records. Transient source errors are retried with bounded exponential backoff.
2. **Validation:** required fields, identifiers, and amount constraints are checked. Rejected records keep reasons so bad data is visible.
3. **Transformation:** strings and optional values are normalized; monetary amounts use `Decimal` and are rounded to cents.
4. **Migration:** SQLAlchemy inserts valid records in a database transaction. `external_transaction_id` is the idempotency key and is protected by a unique constraint.
5. **Reconciliation:** the service checks whether expected IDs exist in the target database and reports missing/duplicate conditions.
6. **Observability and delivery:** request IDs are attached to responses and log lines; CI runs lint, formatting, compile checks, tests/coverage, and a Docker build.

## Common SRE questions and sample answers

### 1. What does idempotency mean here?

An operation is idempotent when repeating the same request does not create duplicate transactions. The service uses `external_transaction_id` as a business key, checks existing IDs, and has a database uniqueness constraint as a final safeguard. In production I would also consider concurrent requests, conflict handling, and a durable migration/job record so a client can safely recover from ambiguous timeouts.

### 2. Why use a database transaction?

A batch should not be left half-written if an insert fails. The service groups inserts into a transaction and rolls the batch back on a SQLAlchemy database error. That simplifies recovery, though very large batches may need smaller transactional chunks and explicit job state depending on business requirements.

### 3. What is the difference between liveness and readiness?

Liveness asks whether the process is running and should not be restarted. Readiness asks whether it can safely serve traffic, often including critical dependencies. This project exposes `/health` that checks database connectivity, so it behaves more like a dependency-aware readiness check than a pure liveness check. A production deployment would usually expose separate liveness and readiness probes.

### 4. How does retry work, and what can go wrong?

The source API client retries timeouts, connection errors, HTTP 429, and HTTP 5xx responses a bounded number of times with exponential backoff. It does not retry permanent 4xx errors. Retries can amplify load during an outage, so production needs limits, jitter, rate-limit awareness, metrics, and a clear idempotency policy. Retrying writes is riskier than retrying a GET because the first write may have succeeded even if the response was lost.

### 5. How would you investigate a 503 from the migration API?

I would capture the timestamp and `X-Request-ID`, check the app logs, check `/health`, inspect MySQL container health and connectivity, and determine whether the error is a database outage or migration failure. I would check the transaction status for affected IDs before retrying. I would avoid exposing database exception details to API clients, but retain safe diagnostic logs internally.

### 6. How would you investigate a slow service?

First determine scope and start time. Compare request latency and error rate, check container CPU/memory, database connection and query latency, source API latency, and retry frequency. Use request IDs to trace representative requests. Mitigate first if customer impact is ongoing, then find the root cause and add a regression test or alert.

### 7. What would you monitor?

- API request rate, p50/p95/p99 latency, and 4xx/5xx rates.
- Database connection failures, query latency, pool saturation, and transaction rollbacks.
- Source API latency, timeouts, 429/5xx responses, and retry count.
- Records received/accepted/rejected/inserted/skipped and reconciliation mismatches.
- Container restarts, CPU/memory usage, disk use, and deployment health.

These metrics and dashboards are **not currently implemented** in the repository.

### 8. What is in your CI pipeline?

GitHub Actions checks out the repository, sets up Python 3.12, installs development dependencies, runs Ruff, Black check, compileall, pytest with coverage enforcement, and builds the Docker image. This helps detect code-quality, syntax, test, and image-build regressions before merge. It does not deploy the application.

### 9. What are the main security limitations?

The API uses one shared API key, and health is unauthenticated. A real deployment should terminate TLS at a gateway, use per-client identity or stronger auth, apply rate limiting, store secrets in a secret manager, redact sensitive data from logs, and define retention/access rules for rejected records.

### 10. Is this production-ready?

No. It demonstrates reliability patterns, but it does not include a cloud deployment, infrastructure as code, metrics/alerting, separate liveness/readiness endpoints, rate limiting, TLS configuration, or managed database migrations. Those would be the next steps before a real production rollout.

## Be ready to demo

1. Start Compose and show `docker compose ps`.
2. Call `/health` and explain why a database outage should produce 503.
3. Submit one valid transaction and inspect inserted/reconciled counts.
4. Submit the same external ID again and explain why it is skipped.
5. Submit an invalid amount and show the rejection reason.
6. Show the CI workflow and explain each stage.
7. Explain one failure scenario and how you would investigate it with request IDs and logs.

Use only local/test data. Never show real API keys, customer data, or credentials in a screen share.
