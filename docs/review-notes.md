# Repository Review Notes

Review date: 2026-10-27

## Scope

Reviewed the uploaded ZIP's source tree, README, Dockerfile, Compose configuration, CI workflow, settings/security code, migration and reconciliation paths, API routes, and test files.

## Verification performed

- Python syntax compilation: `python -m compileall -q app tests scripts` — passed.
- Test function inventory: 83 test functions found by static AST count across `tests/test_*.py` (parameterized tests may produce a larger collected case count).
- Pytest execution attempted, but test collection stopped because `PyMySQL` was not installed in the review environment.
- Installing `requirements-dev.txt` was attempted, but package installation was blocked by unavailable network/DNS in this environment.
- Therefore, pytest, coverage, Ruff, Black, and Docker image build are **not verified** by this review. Run the commands in the README in an environment with the pinned dependencies and Docker installed.

## Documentation changes made

- Rewrote README to include a more accurate project scope, Windows setup, API table, Docker quick start, configuration, safe shutdown, and limitations.
- Removed the unsupported claim of approximately 96% coverage and corrected the static test-function inventory to 83.
- Added an operations runbook for common health, database, authentication, and source API incidents.
- Added an SRE interview guide with a short project pitch, pipeline walkthrough, reliability questions, monitoring suggestions, and demo sequence.

## Important limitations confirmed from repository configuration

- No cloud deployment or infrastructure-as-code is present.
- No metrics, dashboards, or alerting configuration is present.
- `/health` checks database connectivity, so it is dependency-aware rather than a pure process-liveness probe.
- API-key authentication is a shared-key mechanism; if `SERVICE_API_KEY` is empty, auth is disabled outside production. Set `APP_ENV=production` and a strong `SERVICE_API_KEY` for a secured container environment.
- Database tables use `create_all`; a schema migration tool such as Alembic is not configured.
- The source API retry loop uses bounded exponential backoff without jitter.

## Recommended next validation on the developer machine

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest -q --cov
ruff check .
black --check .
python -m compileall -q app tests scripts
docker compose config
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
```

Use non-production sample data and never commit `.env` or generated rejected-record files.
