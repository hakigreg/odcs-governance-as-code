"""Evaluate versioned ODCS contracts against the minimum-governance policy."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from odcs_governance.policy import PolicyConfig, evaluate_contract

DEFAULT_POLICY = Path("policies/minimum-governance.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contracts", nargs="*", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = PolicyConfig.from_file(args.policy)
    contract_files = args.contracts or sorted(Path("contracts").glob("**/*.odcs.yaml"))

    if not contract_files:
        print("No ODCS contracts found.")
        return 1

    total_violations = 0
    for contract_file in contract_files:
        contract = yaml.safe_load(contract_file.read_text())
        violations = evaluate_contract(contract, config)
        if not violations:
            print(f"PASS {contract_file}")
            continue

        print(f"FAIL {contract_file}")
        for violation in violations:
            print(f"  [{violation.code}] {violation.path}: {violation.message}")
        total_violations += len(violations)

    if total_violations:
        print(f"Governance gate failed with {total_violations} violation(s).")
        return 1

    print(
        f"All {len(contract_files)} contract(s) satisfy "
        f"{config.policy_id} v{config.version}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
