# Security notes

* **Authentication.** All `/api/v1/migration/*` endpoints require the `X-API-Key` header, compared in constant time. `/health` is intentionally open for orchestrator probes.
* **Fail-closed in production.** With `APP_ENV=production` the service refuses to start unless `SERVICE_API_KEY` and `MYSQL_PASSWORD` are set. With no key configured in other environments authentication is disabled, for local development only.
* **Secrets** come from environment variables / `.env` (git-ignored). `.env.example` contains placeholders only. Docker Compose refuses to start without database passwords.
* **No internal details in errors.** Database failures return a generic `503`; details go to the logs only.
* **Input limits.** At most 1000 records per API request; amounts must fit the column.
* **Container.** Runs as a non-root user; image contains only runtime dependencies.
* **Data handling.** `data/rejected_records.json` contains raw source records (possibly customer identifiers) and is git-ignored; treat it as sensitive.
* **Dependencies.** Versions are pinned and Dependabot is enabled for pip, Docker and GitHub Actions.

## Not covered (known limits)

* No rate limiting, TLS termination or per-client keys (single shared key) — put the service behind a gateway/ingress for real deployments.
* No database schema migrations tool (tables are created with `create_all`); introduce Alembic before changing the schema in a live system.
