-- Reporting and reconciliation queries for the billing_transactions table (MySQL 8).

-- 1. Row counts per status
SELECT status, COUNT(*) AS transactions, SUM(amount) AS total_amount
FROM billing_transactions
GROUP BY status
ORDER BY transactions DESC;

-- 2. Revenue per customer and currency (never add amounts across currencies)
SELECT customer_id, currency, COUNT(*) AS transactions, SUM(amount) AS total_amount
FROM billing_transactions
GROUP BY customer_id, currency
ORDER BY total_amount DESC;

-- 3. Duplicate check: should always return zero rows (unique constraint)
SELECT external_transaction_id, COUNT(*) AS copies
FROM billing_transactions
GROUP BY external_transaction_id
HAVING COUNT(*) > 1;

-- 4. Reconcile against a source system's expected totals
SELECT source_system, COUNT(*) AS migrated_rows, SUM(amount) AS migrated_total
FROM billing_transactions
GROUP BY source_system;

-- 5. Daily migration volume (UTC)
SELECT DATE(created_at) AS migrated_on, COUNT(*) AS rows_migrated
FROM billing_transactions
GROUP BY DATE(created_at)
ORDER BY migrated_on DESC;
