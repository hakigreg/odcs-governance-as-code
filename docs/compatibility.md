# Contract compatibility gate

ODCS conformance proves that one document follows the standard. It does not
prove that a new version preserves the interface relied on by producers and
consumers. This repository therefore evaluates consecutive versions of every
contract as a separate delivery gate.

## Conservative full-compatibility rules

The gate rejects:

- a changed contract identity or a version that does not increase;
- removed schema objects or properties;
- changed logical or physical types;
- changed physical table names or primary keys;
- optional properties becoming required;
- new required properties;
- added or removed enum values; and
- a property moving to a more restrictive classification.

Enum additions are intentionally treated as breaking because exhaustive
downstream consumers may not understand the new value. Physical type changes
are also always reviewed rather than attempting automatic widening inference.
This conservative policy favors explicit migration over ambiguous automation.

## Run the gate

Check every consecutive version found under `contracts/`:

```bash
make compatibility-check
```

Compare any two explicit files:

```bash
python scripts/check_compatibility.py BASE.odcs.yaml CANDIDATE.odcs.yaml
```

With only v1.0.0 contracts, repository discovery reports zero transitions and
passes. The gate becomes active automatically when another version is added to
a contract directory.

## Demonstrate rejection

```bash
make demo-breaking-change
```

The demonstration creates an in-memory v1.1.0 candidate for
`customer_behavior_features`, removes `total_data_volume_mb`, and exits with a
non-zero status after reporting `property.removed`. It never modifies the
versioned contract on disk.
