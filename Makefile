.DEFAULT_GOAL := help

.PHONY: help bootstrap up down shell test lint format contract-lint governance-check compatibility-check contract-test feature-contract-test decision-contract-test check seed-valid seed-invalid seed-features-valid seed-features-invalid seed-decisions-valid seed-decisions-invalid demo demo-source demo-quality-failure demo-features demo-features-quality-failure demo-decisions demo-decisions-quality-failure demo-breaking-change verify-source-quality-failure verify-feature-quality-failure verify-decision-quality-failure verify-breaking-change ci-runtime status

help: ## Show the available commands
	@awk 'BEGIN {FS = ":.*## "; printf "Available commands:\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Build the reproducible Python tooling image
	docker compose build tooling

up: ## Start PostgreSQL and wait until it is healthy
	docker compose up -d postgres

down: ## Stop the local services without deleting their data
	docker compose down

shell: ## Open a shell in the tooling container
	docker compose run --rm tooling bash

test: ## Run the automated test suite
	docker compose run --rm --no-deps tooling pytest

lint: ## Run static checks
	docker compose run --rm --no-deps tooling ruff check src tests scripts

contract-lint: ## Validate every contract against ODCS
	docker compose run --rm --no-deps tooling python scripts/lint_contracts.py

governance-check: ## Enforce the minimum organizational governance policy
	docker compose run --rm --no-deps tooling python scripts/check_governance.py

compatibility-check: ## Reject breaking changes between consecutive contract versions
	docker compose run --rm --no-deps tooling python scripts/check_compatibility.py

contract-test: up ## Test the telecom contract against live PostgreSQL data
	docker compose run --rm tooling datacontract test --no-inline-references --server local contracts/telecom_cdr_events/v1.0.0.odcs.yaml

feature-contract-test: up ## Test the feature contract against live PostgreSQL data
	docker compose run --rm tooling datacontract test --no-inline-references --server local contracts/customer_behavior_features/v1.0.0.odcs.yaml

decision-contract-test: up ## Test the decision contract against live PostgreSQL data
	docker compose run --rm tooling datacontract test --no-inline-references --server local contracts/credit_risk_decisions/v1.0.0.odcs.yaml

seed-valid: up ## Recreate the demo table with contract-compliant synthetic data
	docker compose run --rm tooling python scripts/load_scenario.py valid

seed-invalid: up ## Recreate the demo table with deliberate quality violations
	docker compose run --rm tooling python scripts/load_scenario.py invalid

seed-features-valid: up ## Build valid features from valid telecom events
	docker compose run --rm tooling python scripts/materialize_features.py valid

seed-features-invalid: up ## Build features with deliberate transformation defects
	docker compose run --rm tooling python scripts/materialize_features.py invalid

seed-decisions-valid: up ## Build valid decisions from valid governed features
	docker compose run --rm tooling python scripts/materialize_decisions.py valid

seed-decisions-invalid: up ## Build decisions with deliberate control defects
	docker compose run --rm tooling python scripts/materialize_decisions.py invalid

demo-source: seed-valid contract-test ## Validate the source contract end to end

demo: ## Run the complete green path across all three contract boundaries
	$(MAKE) seed-decisions-valid
	$(MAKE) contract-test
	$(MAKE) feature-contract-test
	$(MAKE) decision-contract-test

demo-quality-failure: seed-invalid contract-test ## Demonstrate the contract rejecting invalid data

demo-features: seed-features-valid feature-contract-test ## Validate derived features end to end

demo-features-quality-failure: seed-features-invalid feature-contract-test ## Reject invalid derived features

demo-decisions: seed-decisions-valid decision-contract-test ## Validate decision records end to end

demo-decisions-quality-failure: seed-decisions-invalid decision-contract-test ## Reject invalid decisions

demo-breaking-change: ## Demonstrate rejection of a removed contract property
	docker compose run --rm --no-deps tooling python scripts/demo_breaking_change.py

verify-source-quality-failure: seed-invalid ## Assert the source gate fails for three expected checks
	docker compose run --rm tooling python scripts/assert_failure.py \
		--contains "Data contract is invalid" --occurs "│ failed │" 3 -- \
		datacontract test --no-inline-references --server local contracts/telecom_cdr_events/v1.0.0.odcs.yaml

verify-feature-quality-failure: seed-features-invalid ## Assert the feature gate fails for three expected checks
	docker compose run --rm tooling python scripts/assert_failure.py \
		--contains "Data contract is invalid" --occurs "│ failed │" 3 -- \
		datacontract test --no-inline-references --server local contracts/customer_behavior_features/v1.0.0.odcs.yaml

verify-decision-quality-failure: seed-decisions-invalid ## Assert the decision gate fails for five expected checks
	docker compose run --rm tooling python scripts/assert_failure.py \
		--contains "Data contract is invalid" --occurs "│ failed │" 5 -- \
		datacontract test --no-inline-references --server local contracts/credit_risk_decisions/v1.0.0.odcs.yaml

verify-breaking-change: ## Assert the compatibility demo fails for the expected reason
	docker compose run --rm --no-deps tooling python scripts/assert_failure.py \
		--contains "[property.removed]" --contains "rejected 1 breaking change(s)" -- \
		python scripts/demo_breaking_change.py

ci-runtime: ## Run all green paths and verify every expected-failure scenario
	$(MAKE) demo
	$(MAKE) verify-source-quality-failure
	$(MAKE) verify-feature-quality-failure
	$(MAKE) verify-decision-quality-failure
	$(MAKE) verify-breaking-change

check: lint contract-lint governance-check compatibility-check test ## Run all static, contract, and unit checks

format: ## Format Python sources
	docker compose run --rm --no-deps tooling ruff format src tests scripts

status: ## Show the service status
	docker compose ps
