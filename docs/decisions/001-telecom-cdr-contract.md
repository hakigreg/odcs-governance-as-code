# ADR 001: Start with the source-aligned telecom event contract

## Status

Accepted.

## Context

The MVP needs to demonstrate a clear producer-consumer boundary. Starting with
features or credit decisions would hide the obligations of the source producer
and mix raw-event governance with downstream analytical interpretation.

Telecom activity is sensitive even after direct identifiers have been removed.
The contract must therefore express more than a physical schema: it must make
purpose, ownership, quality, retention, access, and usage constraints explicit.

## Decision

The first contract governs a source-aligned `telecom_cdr_events` table with one
row per synthetic network event.

The contract:

- exposes only a one-way pseudonymous subscriber identifier;
- separates event occurrence time from ingestion time;
- classifies critical and sensitive elements;
- defines executable completeness, uniqueness, validity, and consistency checks;
- establishes daily delivery, freshness, and retention expectations;
- prevents re-identification, individual targeting, and sole-source adverse decisions;
- uses the ODCS v3.2.0 `context` block for human and machine consumers.

## Consequences

- Downstream feature contracts can reference a stable, governed source interface.
- Privacy and decision-use limits are visible before a consumer receives access.
- The runtime implementation must create the `raw.telecom_cdr_events` table and
  enforce the same semantics demonstrated by the contract.
- Pseudonymization reduces exposure but does not make the records anonymous.

## Alternatives considered

### Put every dataset in one contract

Rejected because source events, derived features, and decisions have different
owners, purposes, lifecycles, and consumers.

### Begin with the credit score output

Rejected because it would demonstrate the result without showing how producer
obligations and permitted downstream use are established.
