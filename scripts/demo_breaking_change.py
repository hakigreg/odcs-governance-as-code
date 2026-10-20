"""Demonstrate the compatibility gate rejecting a removed feature."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from odcs_governance.compatibility import evaluate_compatibility

BASE_CONTRACT = Path("contracts/customer_behavior_features/v1.0.0.odcs.yaml")
REMOVED_PROPERTY = "total_data_volume_mb"


def main() -> int:
    base_contract = yaml.safe_load(BASE_CONTRACT.read_text())
    candidate_contract = deepcopy(base_contract)
    candidate_contract["version"] = "1.1.0"
    candidate_contract["schema"][0]["properties"] = [
        prop
        for prop in candidate_contract["schema"][0]["properties"]
        if prop["name"] != REMOVED_PROPERTY
    ]

    print(
        f"Simulating {base_contract['name']} {base_contract['version']} -> "
        f"{candidate_contract['version']} with {REMOVED_PROPERTY!r} removed."
    )
    violations = evaluate_compatibility(base_contract, candidate_contract)
    for violation in violations:
        print(f"  [{violation.code}] {violation.path}: {violation.message}")

    if violations:
        print(f"Compatibility gate rejected {len(violations)} breaking change(s).")
        return 1

    print("Unexpected pass: the demonstration did not detect a breaking change.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
