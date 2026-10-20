# Synthetic data

The project does not store fixture datasets in this directory. Valid and
deliberately invalid records are generated deterministically at runtime by
`src/odcs_governance/scenarios.py` and loaded directly into PostgreSQL by the
scenario scripts.

Use the Make targets from the repository root to exercise the datasets:

```bash
make demo
make demo-quality-failure
make demo-features-quality-failure
make demo-decisions-quality-failure
```

The green-path command creates valid source events, behavioral features, and
credit-risk decisions. The failure commands introduce documented violations at
one contract boundary so the corresponding governance gate can reject them.

All generated records are synthetic and ephemeral. They are stored only in the
local Docker Compose PostgreSQL volume and contain no real customer, telecom,
or credit-decision data.
