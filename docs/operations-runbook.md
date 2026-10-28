# Operations Runbook

This is a learning runbook for diagnosing the local Docker Compose deployment. It is not a substitute for an on-call policy or production observability stack.

## First checks

```bash
docker compose ps
docker compose logs --tail=200 app
docker compose logs --tail=200 mysql
curl -i http://localhost:8000/health
```

Use the `X-Request-ID` response header to correlate a request with log lines. Avoid logging API keys or raw rejected billing records.

## Common symptoms

| Symptom | Checks | Likely next action |
|---|---|---|
| App container exits on startup | `docker compose logs app`; confirm `.env` exists and required MySQL passwords are set | Correct environment values, then `docker compose up -d --build`. |
| MySQL health check stays unhealthy | MySQL logs; root password; volume initialization state | Correct credentials. If the volume was initialized with different credentials, changing `.env` alone may not reset it. Back up data before considering `docker compose down -v`. |
| `/health` returns HTTP 503 | Check MySQL health and app logs; verify host is `mysql` inside Compose and credentials/database name match | Restore DB connectivity before retrying migration requests. |
| Migration endpoint returns HTTP 401 | Verify `SERVICE_API_KEY` in app environment and `X-API-Key` header | Use the configured key; never disable authentication in a shared or exposed environment. |
| Source API returns 401/403 | Check `API_BASE_URL` and outbound `API_KEY` | Fix the source credentials. Permanent 4xx errors are not retried. |
| Source API times out or returns 429/5xx | Review source availability and configured timeout/retry count | Bounded retries use exponential backoff. Do not increase retries indefinitely; investigate source health and rate limits. |
| Migration returns generic HTTP 503 | Correlate request ID with application logs; inspect database availability | Treat the request as failed until the outcome is checked. This implementation uses an atomic batch transaction; verify transaction status before retrying if the client lost the response. |
| Reconciliation reports a mismatch | Inspect response counts and transaction IDs; query target rows using `sql/queries.sql` | Do not mark the migration complete until the mismatch is understood. |

## Safe recovery principles

1. Capture the request ID, timestamp, status code, and sanitized error details.
2. Check `/health` and container logs before retrying writes.
3. Use the transaction status endpoint to check known IDs after an ambiguous client timeout.
4. Because the migration uses `external_transaction_id` for idempotency, retrying the same valid input should skip rows already present. Confirm counts and reconciliation after the retry.
5. Preserve rejected-record reports securely; they may contain customer identifiers.
6. Do not delete the MySQL volume to troubleshoot unless the data is disposable and deletion is explicitly intended.

## Reliability gaps to address before production

- Add metrics for request rate, error rate, latency, retry counts, rejected records, migration failures, and reconciliation mismatches.
- Add alert thresholds and an on-call escalation policy.
- Add structured log shipping, retention, access controls, and secret redaction.
- Use TLS, a gateway, rate limits, and per-client identity.
- Use Alembic migrations, backups, restore drills, and a documented recovery-point/recovery-time objective.
- Add retry jitter and explicit handling for source pagination and rate-limit headers.
