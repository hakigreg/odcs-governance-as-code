# ADR 002: Govern derived behavioral features as a separate contract

- Status: Accepted
- Date: 2026-10-19

## Context

The telecom event contract governs a source-aligned interface owned by the
Telecom domain. Credit-risk consumers should not couple themselves to raw event
semantics or reproduce feature logic independently. That would blur ownership,
increase privacy exposure, and make model inputs difficult to reproduce.

## Decision

Create `customer_behavior_features` as a separate ODCS v3.2.0 contract owned by
the Data Platform feature team.

The contract:

- declares `urn:odcs:telecom:telecom-cdr-events` v1.0.0 as its governed source;
- defines a subscriber-level, 30-day snapshot rather than exposing event history;
- identifies dimensions and measures with ODCS 3.2 semantic types;
- records transformation logic beside each derived feature;
- uses `subscriber_id_hash`, `feature_window_end`, and `feature_version` as its
  reproducibility key; and
- carries privacy and high-impact-use constraints into the derived interface.

The contract defines features, not a machine-learning model or credit decision.
Those concerns remain downstream and will receive their own contract boundary.

## Consequences

Consumers can discover feature meaning, lineage, ownership, and quality without
reading pipeline code. Feature logic becomes reviewable as part of the contract.
The Data Platform team becomes accountable for the derived interface and its
daily service level.

The repository must also reject high-impact derived contracts that omit source
contract identity or version. Runtime materialization and data-quality evidence
for this contract will be implemented in a subsequent step.
