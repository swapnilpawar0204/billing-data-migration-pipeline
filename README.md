# Cloud Billing Data Migration Pipeline

A cloud-ready billing data migration pipeline built with Python, FastAPI,
MySQL, Docker and GitHub Actions.

The project demonstrates a production-oriented data migration workflow:

External REST API
→ Ingestion
→ Validation
→ Transformation
→ Idempotent Migration
→ MySQL
→ Reconciliation

## Project Status

🚧 Local application + Docker + CI completed.

Current capabilities:

- REST API ingestion
- Request validation
- Data transformation
- Idempotent database migration
- Atomic database transactions
- Reconciliation
- Migration status lookup
- Error handling
- Automated tests
- Docker Compose
- GitHub Actions CI

Planned:

- Azure deployment
- Terraform infrastructure
- Observability and metrics
- Security hardening
- Production deployment workflow

---

## Problem

Billing systems can contain duplicate, invalid, incomplete or inconsistent
transaction records.

Directly migrating this data can result in:

- duplicate transactions
- invalid records
- partial migrations
- inconsistent source and target data
- difficult failure recovery

This project provides a controlled migration pipeline that validates,
transforms, migrates and reconciles billing transactions.

---

## Architecture

```text
                    External Billing API
                            |
                            v
                    +---------------+
                    |   FastAPI     |
                    |   Ingestion   |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    |  Validation   |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Transformation|
                    +-------+-------+
                            |
                            v
                    +---------------+
                    |   Migration   |
                    |  Idempotency  |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    |     MySQL     |
                    +-------+-------+
                            |
                            v
                    +---------------+
                    | Reconciliation|
                    +---------------+

             GitHub Actions
                   |
                   v
             Quality Checks
                   |
                   v
              Docker Build
