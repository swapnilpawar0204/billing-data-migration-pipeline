# Billing Data Migration Pipeline

A containerized billing-data migration pipeline built with **Python, FastAPI, MySQL, SQLAlchemy, Docker, and GitHub Actions**.

The project demonstrates reliable data ingestion, validation, transformation, database migration, idempotency, reconciliation, automated testing, containerization, and CI automation.

---

## Project Status

| Component                        | Status             |
| -------------------------------- | ------------------ |
| Core migration pipeline          | ✅ Complete         |
| REST API                         | ✅ Complete         |
| Data validation & transformation | ✅ Complete         |
| MySQL database integration       | ✅ Complete         |
| Idempotent migration             | ✅ Complete         |
| Migration reconciliation         | ✅ Complete         |
| Automated tests                  | ✅ Complete         |
| Docker & Docker Compose          | ✅ Complete         |
| GitHub Actions CI                | ✅ Complete         |
| Azure deployment                 | ⏳ Not implemented  |
| Terraform infrastructure         | ⏳ Preparation only |
| Production cloud deployment      | ⏳ Planned          |

> **Note:** Azure deployment, production cloud infrastructure, and production CD are intentionally not presented as completed features.

---

## Overview

The pipeline processes billing transactions received through a REST API and safely migrates them into a MySQL database.

### Data Flow

```text
                 External REST API
                        │
                        ▼
                Data Ingestion
                        │
                        ▼
                 Input Validation
                        │
                        ▼
             Data Transformation
                        │
                        ▼
              Duplicate Detection
                        │
                        ▼
              Database Migration
                        │
                        ▼
                 Reconciliation
                        │
                        ▼
                     MySQL
```

The system is designed to prevent duplicate migrations, validate incoming data, handle database failures safely, and verify that migrated records match the expected result.

---

## Key Features

### API & Data Processing

* REST API built with FastAPI
* HTTPX-based external API ingestion
* Pydantic request validation
* Data normalization and transformation
* Structured API error handling
* Batch processing support

### Database & Migration

* MySQL 8 database
* SQLAlchemy ORM
* Transaction-based database operations
* Rollback on migration failure
* Duplicate detection
* Idempotent migration using `external_transaction_id`
* Migration status lookup
* Migration reconciliation

### Reliability

* Input validation before database operations
* Idempotent processing
* Duplicate protection
* Database transaction handling
* Rollback handling
* Health checks
* Automated test coverage
* Failure-path testing

### DevOps & Cloud-Oriented Engineering

* Docker containerization
* Docker Compose multi-container environment
* Non-root application container
* Environment-based configuration
* GitHub Actions CI
* Ruff code-quality checks
* Black formatting checks
* Python compilation checks
* Docker image build verification
* Terraform infrastructure preparation

### Security Practices

* Environment variables for configuration
* `.env.example` provided for local setup
* No credentials committed to the repository
* Non-root Docker container
* Separation of configuration from application code

---

## Technology Stack

| Category                   | Technology             |
| -------------------------- | ---------------------- |
| Language                   | Python 3.13            |
| API Framework              | FastAPI                |
| Data Validation            | Pydantic               |
| Database                   | MySQL 8                |
| ORM                        | SQLAlchemy             |
| HTTP Client                | HTTPX                  |
| Testing                    | pytest                 |
| Code Quality               | Ruff, Black            |
| Containerization           | Docker, Docker Compose |
| CI                         | GitHub Actions         |
| Version Control            | Git, GitHub            |
| Infrastructure Preparation | Terraform              |

---

## Project Structure

```text
billing-data-migration-pipeline/
│
├── app/
│   ├── api/
│   │   └── routes/
│   │
│   ├── config/
│   │
│   ├── database/
│   │
│   ├── ingestion/
│   │
│   ├── validation/
│   │
│   ├── transformation/
│   │
│   ├── migration/
│   │
│   ├── reconciliation/
│   │
│   ├── monitoring/
│   │
│   └── utils/
│
├── tests/
│
├── scripts/
│
├── sql/
│
├── docker/
│
├── terraform/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Database

### Main Table

```text
billing_transactions
```

### Important Fields

| Field                     | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| `external_transaction_id` | External transaction identifier and idempotency key |
| `customer_id`             | Customer identifier                                 |
| `invoice_id`              | Invoice identifier                                  |
| `amount`                  | Billing amount                                      |
| `currency`                | Transaction currency                                |
| `status`                  | Transaction status                                  |
| `transaction_date`        | Transaction date                                    |
| `source_system`           | Originating system                                  |
| `created_at`              | Record creation timestamp                           |
| `updated_at`              | Last update timestamp                               |

### Idempotency

The `external_transaction_id` is used as the idempotency key.

This prevents the same external transaction from being migrated multiple times.

Example:

```text
External Transaction
        │
        ▼
Check external_transaction_id
        │
        ├── Already exists ──► Return existing migration
        │
        └── Does not exist ──► Perform migration
```

---

## Reliability Design

The migration workflow follows several reliability principles:

```text
Request
   │
   ▼
Validate Input
   │
   ▼
Transform Data
   │
   ▼
Check Duplicate
   │
   ▼
Start Database Transaction
   │
   ▼
Insert Migration Record
   │
   ├── Success ──► Commit
   │
   └── Failure ──► Rollback
                         │
                         ▼
                   Return Error
   │
   ▼
Reconcile Result
```

### Reliability mechanisms

* Input validation
* Duplicate detection
* Idempotent processing
* Database transactions
* Rollback on failure
* Reconciliation
* Health checks
* Automated failure testing
* Containerized execution

---

## Testing

The project uses **pytest** for automated testing.

Current test status:

```text
61 tests passed
```

Run the test suite:

```bash
pytest -v
```

### Code Quality

Run Ruff:

```bash
ruff check .
```

Run Black verification:

```bash
black --check .
```

Run Python compilation checks:

```bash
python -m compileall app tests
```

---

## Running Locally

### Prerequisites

Install:

* Python 3.13+
* Docker Desktop
* Git

Optional for local development:

* MySQL 8
* VS Code / IntelliJ / PyCharm

---

### 1. Clone the Repository

```bash
git clone https://github.com/swapnilpawar0204/billing-data-migration-pipeline.git
```

Move into the project:

```bash
cd billing-data-migration-pipeline
```

---

### 2. Create Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update the values in `.env` according to your local environment.

> Do not commit `.env` or real credentials to Git.

---

## Running with Docker Compose

Build and start the application:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up --build -d
```

Check running containers:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs app
```

Follow application logs:

```bash
docker compose logs -f app
```

Stop the application:

```bash
docker compose down
```

Stop containers and remove volumes:

```bash
docker compose down -v
```

---

## API

The application provides REST endpoints for billing-data ingestion and migration operations.

Typical workflow:

```text
POST billing data
        │
        ▼
Validate request
        │
        ▼
Transform data
        │
        ▼
Migrate to MySQL
        │
        ▼
Check migration status
        │
        ▼
Reconcile result
```

### API Documentation

When the FastAPI application is running, interactive API documentation is available through:

```text
http://localhost:8000/docs
```

OpenAPI documentation:

```text
http://localhost:8000/openapi.json
```

---

## Health Check

The application exposes a health endpoint for basic service availability checks.

Example:

```text
GET /health
```

This can be used by Docker and operational tooling to verify application availability.

---

## GitHub Actions CI

The repository includes a GitHub Actions workflow:

```text
.github/
└── workflows/
    └── ci.yml
```

The CI workflow performs automated checks including:

```text
Git Push / Pull Request
        │
        ▼
Install Dependencies
        │
        ▼
Ruff
        │
        ▼
Black
        │
        ▼
Python Compilation
        │
        ▼
pytest
        │
        ▼
Docker Image Build
```

The current workflow is **CI only**.

It does not automatically deploy the application to Azure or another production cloud environment.

---

## Docker

The application is containerized using Docker.

The Docker setup includes:

* Application container
* MySQL container
* Docker Compose orchestration
* Environment-based configuration
* Health checks
* Non-root application execution
* Persistent database volume

Example:

```bash
docker compose up --build
```

---

## Infrastructure / Terraform

The repository contains a `terraform/` directory for future infrastructure work.

Current status:

```text
Terraform
   │
   ├── Repository structure: Present
   ├── Infrastructure preparation: Present
   └── Production infrastructure deployment: Not implemented
```

Terraform is therefore treated as **infrastructure preparation**, not as completed cloud infrastructure.

---

## Cloud Roadmap

The project is structured so that it can be extended into a cloud-based deployment.

Planned cloud work:

### Phase 1 — Azure Deployment

Deploy the application to Azure using appropriate managed services.

### Phase 2 — Infrastructure as Code

Expand Terraform configuration to manage the required cloud resources.

### Phase 3 — Cloud Database

Move the database from local Docker/MySQL to an appropriate managed cloud database.

### Phase 4 — Monitoring

Add application and infrastructure monitoring, metrics, logs, and alerts.

### Phase 5 — Production CD

Extend GitHub Actions from CI to a controlled production deployment workflow.

### Phase 6 — Security Hardening

Introduce additional production security controls such as:

* API authentication
* Authorization
* Secret management
* Network restrictions
* Additional container hardening

---

## Future Improvements

Planned improvements include:

* Alembic database migrations
* API authentication and authorization
* Application metrics
* Structured production logging
* Azure deployment
* Terraform-managed infrastructure
* Managed cloud database
* Production CD workflow
* Additional security hardening
* Monitoring and alerting

---

## Engineering Concepts Demonstrated

This project demonstrates practical backend, data-engineering, and cloud/SRE concepts:

### Backend

* REST API development
* FastAPI
* Pydantic
* SQLAlchemy
* MySQL
* HTTPX

### Data Engineering

* Data ingestion
* Data validation
* Data transformation
* Data normalization
* Database migration
* Reconciliation

### Reliability Engineering

* Idempotency
* Duplicate prevention
* Transaction management
* Rollback handling
* Health checks
* Failure-path testing
* Automated testing

### DevOps

* Docker
* Docker Compose
* Git
* GitHub Actions
* CI automation
* Code-quality automation

### Infrastructure

* Terraform preparation
* Cloud deployment planning
* Environment-based configuration

---

## What This Project Does Not Claim

To keep the project technically accurate, the following are **not presented as completed features**:

* Production Azure deployment
* Production cloud infrastructure
* Production managed database
* Production monitoring/alerting
* Production continuous deployment
* Full production authentication/authorization

These are planned extensions of the project.

---

## Project Goal

The goal of this project is to demonstrate how a billing-data migration service can be designed with reliability and operational considerations from the beginning.

The project combines:

```text
FastAPI
   +
Data Validation
   +
ETL-style Processing
   +
MySQL
   +
Idempotent Migration
   +
Transaction Management
   +
Reconciliation
   +
Automated Testing
   +
Docker
   +
GitHub Actions
   +
Infrastructure Preparation
```

This provides a practical foundation for further development toward a cloud-deployed data migration service.

---

## Author

**Swapnil Pawar**

BCA Graduate | Cloud & DevOps / SRE

GitHub: `https://github.com/swapnilpawar0204`

LinkedIn: `https://linkedin.com/in/swapnil-pawar-a2907a326/`
