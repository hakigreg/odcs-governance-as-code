# MVP scope

## Goal

Demonstrate that ODCS v3.2.0 contracts can act as executable interfaces between
data producers, platform teams, governance roles, and AI or analytics consumers.

## Deliverables

- [x] Three connected ODCS v3.2.0 contracts.
- [x] Synthetic valid and invalid datasets.
- [x] PostgreSQL-based local runtime.
- [x] Contract linting against the ODCS specification.
- [x] Organization-specific governance policy checks.
- [x] Breaking-change detection between contract versions.
- [x] Runtime schema, quality, and service-level checks.
- [x] Automated tests and GitHub Actions.
- [x] Architecture, lifecycle, and demonstration documentation.

## Demonstration scenarios

### Green path

Valid contracts and compliant data pass every gate.

### Quality failure

Invalid or stale data fails with an actionable explanation.

### Breaking contract change

An incompatible producer change is rejected before merge.

## Definition of done

- `make demo` runs the green path from a clean checkout.
- `make demo-quality-failure` fails for the expected quality violation.
- `make demo-breaking-change` fails for the expected incompatible change.
- CI runs the same checks used by local development.
- The README explains the business problem, architecture, controls, and trade-offs.
- No real personal, telecom, or credit data is stored in the repository.

## Out of scope

- Production credit decisions or regulatory certification.
- A custom web application or general-purpose contract registry.
- Kubernetes, streaming infrastructure, or multi-cloud deployment.
- Training or serving a machine-learning model.
- A generative-AI assistant.
