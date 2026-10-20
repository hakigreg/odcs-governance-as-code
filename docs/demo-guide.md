# Portfolio demonstration guide

This guide presents the project in roughly ten minutes from a clean checkout.
All commands run from the repository root and use only Docker, Compose, and Make.

## 1. Build the containerized tooling environment

```bash
make bootstrap
```

Explain that Python, ODCS tooling, and PostgreSQL versions are isolated from the
reviewer's machine.

## 2. Show the three contract boundaries

Open the contracts in order:

1. `telecom_cdr_events` — source semantics and privacy constraints.
2. `customer_behavior_features` — transformation lineage and semantic measures.
3. `credit_risk_decisions` — model lineage, explanation, and human oversight.

Use `docs/architecture.md` to show that each boundary has a different accountable
domain and runtime schema.

## 3. Run the fast delivery gates

```bash
make check
```

Expected evidence:

- three contracts conform to ODCS v3.2.0;
- three contracts satisfy the organizational policy;
- compatibility discovery succeeds; and
- 23 unit tests pass.

## 4. Execute the full green path

```bash
make demo
```

The command generates 60 source events, materializes 25 feature snapshots and 25
decision records, then runs all three live contracts. Expected totals are 40,
48, and 69 passed checks.

## 5. Prove that failures are intentional

The verified targets return success only when the underlying contract command
fails for the expected reason and with the expected failed-row count:

```bash
make verify-source-quality-failure
make verify-feature-quality-failure
make verify-decision-quality-failure
make verify-breaking-change
```

Expected evidence:

| Scenario | Valid upstream boundary | Expected rejection |
| --- | --- | --- |
| Invalid source events | None | 3 source checks |
| Invalid feature transformation | Source events | 3 feature checks |
| Invalid decision controls | Behavioral features | 5 decision checks |
| Removed feature property | Current contract | `property.removed` |

For a single CI-equivalent command that includes green and negative paths:

```bash
make ci-runtime
```

## 6. Close the demonstration

Restore the complete valid chain and stop services without deleting the named
volume:

```bash
make seed-decisions-valid
make down
```

Conclude with the project claim: ODCS provides an interoperable contract model;
organizational policy, compatibility analysis, runtime evidence, and CI turn it
into a practical governance-as-code workflow.
