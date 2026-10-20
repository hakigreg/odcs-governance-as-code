# Runtime validation

The runtime demonstration proves that the ODCS contract is executable against
real database metadata and rows, rather than being documentation-only.
PostgreSQL is available only inside the Docker Compose network, so the demo does
not claim or conflict with a PostgreSQL port already running on the host.

## Complete green path

```bash
make demo
```

This command starts PostgreSQL, loads 60 valid events, materializes 25 valid
feature snapshots and 25 valid decisions, and runs all three contracts against
their live tables. Use `make demo-source`, `make demo-features`, or
`make demo-decisions` when demonstrating one boundary in isolation.

## Source contract: green path

```bash
make demo-source
```

This command recreates `raw.telecom_cdr_events`, loads 60 valid synthetic
events, and runs Data Contract CLI against the live source table.

## Source contract: deliberate failure

```bash
make demo-quality-failure
```

The invalid scenario preserves the physical schema but introduces three
business-quality violations:

- a subscriber identifier that is not a SHA-256 hexadecimal string;
- a negative call duration;
- a data event with an inbound direction.

The command is expected to exit with a non-zero status. That failure represents
the enforcement gate working as designed.

## Derived feature contract: green path

```bash
make demo-features
```

This command loads valid source events, builds
`analytics.customer_behavior_features` with SQL, and tests the resulting table
against the derived contract. Each row is a pseudonymous subscriber snapshot
for a complete 30-day window. The transformation produces the dimensions and
measures documented in the contract rather than loading precomputed fixtures.

## Derived feature contract: deliberate failure

```bash
make demo-features-quality-failure
```

The upstream events remain valid. After materialization, the scenario introduces
three independent defects at the feature boundary:

- one snapshot covers 29 days instead of 30;
- one aggregate data-volume measure is negative; and
- one active-day count exceeds the observation window.

The feature contract must reject all three defects with a non-zero exit status.
This isolates accountability: Telecom owns source-event correctness, while Data
Platform owns transformation and feature correctness.

## Decision contract: green path

```bash
make demo-decisions
```

This command executes the complete chain: 60 valid source events become 25
valid feature snapshots and then 25 auditable decision records. A deterministic,
transparent scoring function stands in for model inference because training and
serving a model are outside the MVP. Each record preserves feature and model
lineage, explanation, review state, recommendation, and final outcome.

## Decision contract: deliberate failure

```bash
make demo-decisions-quality-failure
```

The source and feature tables remain valid. Five separate decision records are
modified to demonstrate these control failures:

- a feature snapshot comes from after the decision;
- a score conflicts with its risk band;
- a recommendation conflicts with its risk band;
- a declined outcome has no completed human review; and
- a record claims to have been published before the decision completed.

The decision contract must reject exactly those five semantic defects. Testing
the unchanged feature contract afterward proves that the immediate upstream
interface remains compliant and assigns the failure to Risk Analytics.

## Design boundary

PostgreSQL enforces basic types, required values, and primary keys. The ODCS
contracts enforce producer-consumer expectations that cannot be represented by
DDL alone, including semantic consistency, quality, freshness, and retention.

All records are deterministic synthetic data. No personal, telecom customer, or
real credit-decision data is used.
