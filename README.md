# \# Billing Data Migration Pipeline

# 

# > A containerized ETL and data migration pipeline built with Python, FastAPI, MySQL, SQLAlchemy, Docker, and GitHub Actions.

# 

# \## Project Status

# 

# \* Core pipeline: Complete

# \* Tests: 61 passed

# \* Docker + Docker Compose: Complete

# \* GitHub Actions CI: Complete

# \* Azure deployment: Not implemented

# \* Terraform: Preparation only

# \* Production cloud deployment: Planned

# 

# \## Overview

# 

# This project demonstrates a reliable billing-data migration workflow:

# 

# ```text

# External REST API

# &#x20;      ↓

# Data Ingestion

# &#x20;      ↓

# Validation

# &#x20;      ↓

# Transformation

# &#x20;      ↓

# Database Migration

# &#x20;      ↓

# Reconciliation

# &#x20;      ↓

# MySQL

# ```

# 

# The pipeline validates billing records, transforms data into a consistent format, migrates records safely, prevents duplicate migrations, and verifies the migration result.

# 

# \## Key Features

# 

# \* REST API ingestion using HTTPX

# \* FastAPI backend

# \* Pydantic validation

# \* Data transformation and normalization

# \* MySQL database with SQLAlchemy

# \* Idempotent migration using `external\_transaction\_id`

# \* Duplicate detection

# \* Transaction rollback on database failures

# \* Migration reconciliation

# \* Structured error handling

# \* Automated tests with pytest

# \* Code quality checks with Ruff and Black

# \* Docker and Docker Compose

# \* GitHub Actions CI

# \* Non-root Docker container

# \* Environment-based configuration

# \* No credentials committed to Git

# 

# \## Technology Stack

# 

# | Category         | Technology             |

# | ---------------- | ---------------------- |

# | Language         | Python 3.12+           |

# | API              | FastAPI                |

# | Validation       | Pydantic               |

# | Database         | MySQL 8                |

# | ORM              | SQLAlchemy             |

# | HTTP Client      | HTTPX                  |

# | Testing          | pytest                 |

# | Code Quality     | Ruff, Black            |

# | Containerization | Docker, Docker Compose |

# | CI               | GitHub Actions         |

# | Version Control  | Git, GitHub            |

# | IaC Preparation  | Terraform              |

# 

# \## Project Structure

# 

# ```text

# billing-data-migration-pipeline/

# │

# ├── app/

# │   ├── api/

# │   ├── config/

# │   ├── database/

# │   ├── ingestion/

# │   ├── validation/

# │   ├── transformation/

# │   ├── migration/

# │   ├── reconciliation/

# │   ├── monitoring/

# │   └── utils/

# │

# ├── tests/

# ├── scripts/

# ├── sql/

# ├── docker/

# ├── terraform/

# ├── .github/

# │   └── workflows/

# │       └── ci.yml

# ├── docker-compose.yml

# ├── requirements.txt

# ├── .env.example

# └── README.md

# ```

# 

# \## Database

# 

# \### Main Table

# 

# `billing\_transactions`

# 

# \### Important Fields

# 

# \* `external\_transaction\_id`

# \* `customer\_id`

# \* `invoice\_id`

# \* `amount`

# \* `currency`

# \* `status`

# \* `transaction\_date`

# \* `source\_system`

# \* `created\_at`

# \* `updated\_at`

# 

# `external\_transaction\_id` is used as the idempotency key to prevent duplicate migrations.

# 

# \## Reliability

# 

# The pipeline is designed around common data-migration reliability requirements:

# 

# \* Input validation before database migration

# \* Duplicate detection

# \* Idempotent migration

# \* Database transaction handling

# \* Rollback on migration failure

# \* Migration reconciliation

# \* Automated test coverage

# \* Containerized execution

# 

# \## Testing

# 

# Run the test suite with:

# 

# ```bash

# pytest -v

# ```

# 

# Run code-quality checks:

# 

# ```bash

# ruff check .

# black --check .

# ```

# 

# \## Docker

# 

# Build and start the application:

# 

# ```bash

# docker compose up --build

# ```

# 

# Stop the containers:

# 

# ```bash

# docker compose down

# ```

# 

# View application logs:

# 

# ```bash

# docker compose logs app

# ```

# 

# \## GitHub Actions

# 

# The CI workflow validates the project by running automated checks such as:

# 

# \* Dependency installation

# \* Ruff

# \* Black

# \* Python compilation checks

# \* pytest

# \* Docker image build

# 

# The current workflow is \*\*CI\*\*, not a production deployment pipeline.

# 

# \## Cloud / Infrastructure Roadmap

# 

# The repository is structured so that cloud infrastructure can be added later.

# 

# Planned improvements include:

# 

# 1\. Azure application deployment

# 2\. Terraform infrastructure

# 3\. Cloud database configuration

# 4\. Application monitoring and metrics

# 5\. Production deployment workflow

# 6\. Additional security hardening

# 

# These capabilities are not presented as completed features until they are implemented and tested.

# 

# \## Future Improvements

# 

# \* Add database migrations with Alembic

# \* Add API authentication and authorization

# \* Add request/batch size limits

# \* Improve health and readiness checks

# \* Add application metrics

# \* Add structured production logging

# \* Add cloud deployment

# \* Add Terraform infrastructure

# \* Add production CD workflow

# 

# \## Project Goal

# 

# The project demonstrates practical backend and cloud-oriented engineering concepts including:

# 

# \* REST API development

# \* Data validation

# \* ETL-style processing

# \* Database migration

# \* Idempotency

# \* Transaction management

# \* Reliability testing

# \* Docker

# \* CI automation

# \* Infrastructure-as-Code preparation



