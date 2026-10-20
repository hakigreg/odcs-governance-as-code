# ADR 003: Govern model-assisted outcomes as an auditable decision record

- Status: Accepted
- Date: 2026-10-19

## Context

A risk score alone is insufficient evidence for a high-impact process. An
auditor must be able to identify the exact model and feature versions, understand
the principal recommendation reason, distinguish model output from the final
outcome, and verify whether required human oversight occurred.

The MVP does not train or serve a model. It needs a realistic contract boundary
for demonstrating how governed features become an auditable downstream record.

## Decision

Create `credit_risk_decisions` as a separate ODCS v3.2.0 contract owned by Risk
Analytics. It declares `customer_behavior_features` v1.0.0 as its governed
source and records:

- point-in-time feature lineage;
- stable model identity and version;
- bounded risk score, governed risk band, and non-binding recommendation;
- a primary explanation reason code;
- human-review status; and
- the final controlled-process outcome.

The model recommendation and final outcome are deliberately separate fields.
A declined outcome is contractually invalid unless human review is complete.
Decision rows are append-only; reevaluation creates a new identifier.

The organization-specific governance gate requires every high-impact decision
contract to expose the minimum lineage, explanation, oversight, and outcome
fields. ODCS conformance alone does not provide that local control.

## Consequences

Decision evidence becomes queryable and testable rather than being scattered
across application logs. Consumers can reconstruct which governed inputs and
model artifact produced a recommendation while retaining the final human or
policy-controlled outcome as a distinct fact.

The retention period and review workflow are illustrative portfolio policies,
not regulatory advice. A production implementation would map them to applicable
jurisdiction, product, and institutional requirements.
