.PHONY: install test lint format run up down migrate-sample migrate-api

install:
	pip install -r requirements-dev.txt

test:
	pytest --cov

lint:
	ruff check .
	black --check .

format:
	ruff check --fix .
	black .

run:
	uvicorn app.main:app --reload

up:
	docker compose up --build -d

down:
	docker compose down

migrate-sample:
	python -m app.cli --file data/sample_billing_data.json

migrate-api:
	python -m app.cli --from-api
