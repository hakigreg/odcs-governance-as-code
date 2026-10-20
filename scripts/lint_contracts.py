"""Lint every versioned ODCS contract with Data Contract CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

CONTRACTS_ROOT = Path("contracts")


def contract_files() -> list[Path]:
    return sorted(CONTRACTS_ROOT.glob("**/*.odcs.yaml"))


def main() -> int:
    files = contract_files()
    if not files:
        print("No ODCS contracts found.")
        return 1

    failures = 0
    for contract_file in files:
        print(f"Linting {contract_file}")
        result = subprocess.run(
            [
                "datacontract",
                "lint",
                "--all-errors",
                "--no-inline-references",
                str(contract_file),
            ],
            check=False,
        )
        failures += result.returncode != 0

    if failures:
        print(f"{failures} contract(s) failed linting.")
        return 1

    print(f"All {len(files)} contract(s) conform to ODCS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
