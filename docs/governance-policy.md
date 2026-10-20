# Minimum viable governance policy

ODCS validates whether a contract conforms to the open standard. This project
adds a separate organizational policy gate to answer a different question:
is the contract sufficiently governed to be accepted as a trusted interface?

The policy is intentionally small, transparent, and executable. Its parameters
live in `policies/minimum-governance.yaml`; its implementation lives in
`src/odcs_governance/policy.py`.

## Enforced controls

| Policy code | Requirement |
| --- | --- |
| `description.required` | Purpose, usage, and limitations are explicit. |
| `team.role.required` | An Owner and Data Steward are assigned. |
| `support.issues.required` | Consumers have an incident channel. |
| `sla.required` | Freshness, frequency, and retention are declared. |
| `property.classification.required` | Every property has a classification. |
| `sensitive.tags.required` | Confidential or restricted properties include handling tags. |
| `cde.quality.required` | Every Critical Data Element has an executable quality rule. |
| `quality.id.required` | Quality rules have stable identifiers for evidence and targeting. |
| `server.credential.forbidden` | Credentials are never committed inside a contract. |
| `derived.lineage.required` | Derived contracts identify their source contract and version. |
| `decision.property.required` | High-impact decisions expose minimum model lineage, explanation, oversight, and outcome fields. |
| `high-impact.context.required` | High-impact contracts provide machine-readable instructions. |
| `high-impact.constraints.required` | High-impact contracts declare prohibited uses. |

## Run the gate

```bash
make governance-check
```

The command checks every versioned contract. A violation produces a stable code,
the contract path, an actionable message, and a non-zero exit status suitable
for CI.

## Design choice

The organizational rules are not embedded in the ODCS schema. Keeping the
layers separate preserves interoperability with the open standard while making
local expectations explicit and independently evolvable.
