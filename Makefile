.PHONY: help setup config infra-up infra-down seed run pause resume status load verify test demo

PYTHON ?= python

help:
	@echo "Available commands:"
	@echo "  make setup        - Install dependencies into current environment"
	@echo "  make config       - Display current configuration (CLI)"
	@echo "  make infra-up     - Start MinIO, ClickHouse, and Mock API via Docker Compose"
	@echo "  make infra-down   - Tear down Docker containers and volumes"
	@echo "  make seed         - Seed mock HubSpot API with synthetic data"
	@echo "  make run          - Execute pipeline ingestion across CRM resources"
	@echo "  make pause        - Gracefully pause running extraction"
	@echo "  make resume       - Resume paused or interrupted extraction"
	@echo "  make status       - Display current runner checkpoints and status"
	@echo "  make load         - Ingest landed Parquet files into ClickHouse"
	@echo "  make verify       - Verify exact checksums and deduplication"
	@echo "  make test         - Run automated test suite"
	@echo "  make demo         - Run interactive narrated demonstration"

setup:
	$(PYTHON) -m pip install -r requirements.txt

config:
	$(PYTHON) -m hubspot_pipeline.cli config

infra-up:
	docker compose up -d

infra-down:
	docker compose down -v

seed:
	$(PYTHON) -m hubspot_pipeline.cli seed

run:
	$(PYTHON) -m hubspot_pipeline.cli run

pause:
	$(PYTHON) -m hubspot_pipeline.cli pause

resume:
	$(PYTHON) -m hubspot_pipeline.cli resume

status:
	$(PYTHON) -m hubspot_pipeline.cli status

load:
	$(PYTHON) -m hubspot_pipeline.cli load

verify:
	$(PYTHON) -m hubspot_pipeline.cli verify

test:
	$(PYTHON) -m pytest tests/

demo:
	$(PYTHON) -m hubspot_pipeline.cli demo
