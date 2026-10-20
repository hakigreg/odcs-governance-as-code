# Continuous integration

The GitHub Actions workflow runs the same Docker-based gates exposed by the
Makefile. Contributors therefore use the same commands locally and in CI,
reducing environment-specific behavior.

## Workflow design

`Contract CI` runs on pushes, pull requests, and manual dispatches with
read-only repository permissions. Concurrent runs for the same ref are
cancelled when a newer run starts.

It contains two jobs:

1. **Static and contract gates** builds the tooling image and runs `make check`:
   Python lint, ODCS conformance, organizational governance, version
   compatibility, and unit tests.
2. **Runtime contract scenarios** starts PostgreSQL and runs `make ci-runtime`:
   every green runtime demonstration plus verified source, feature, decision,
   and compatibility failure scenarios.

The runtime job waits for the static job, avoiding unnecessary database work
when a fast gate already failed.

## Expected failures

A quality-failure demonstration returning non-zero is not enough to prove the
right control fired; infrastructure errors also return non-zero. The helper
`scripts/assert_failure.py` requires both:

- a non-zero command exit code; and
- scenario-specific markers and exact failed-row counts in the captured output.

This turns negative demonstrations into positive CI assertions. For example,
the invalid decision scenario is accepted by CI only when Data Contract CLI
reports an invalid contract and exactly five failing checks.

## Security choices

- Workflow permissions are limited to `contents: read`.
- Checkout does not persist GitHub credentials.
- No repository secrets are required.
- PostgreSQL is isolated inside the Compose network.
- Containers and the ephemeral database volume are removed after every runtime
  job, even when an earlier step fails.
