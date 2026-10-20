"""Check explicit or discovered ODCS version transitions for breaking changes."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

import yaml

from odcs_governance.compatibility import evaluate_compatibility

CONTRACTS_ROOT = Path("contracts")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contracts", nargs="*", type=Path, metavar="CONTRACT")
    args = parser.parse_args()
    if len(args.contracts) not in (0, 2):
        parser.error("provide either no paths or exactly BASE and CANDIDATE")
    return args


def _version_key(path: Path) -> tuple[int, int, int]:
    version = path.name.removeprefix("v").removesuffix(".odcs.yaml")
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Contract filename must use vMAJOR.MINOR.PATCH: {path}")
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def discovered_transitions() -> list[tuple[Path, Path]]:
    transitions: list[tuple[Path, Path]] = []
    for contract_directory in sorted(path for path in CONTRACTS_ROOT.iterdir() if path.is_dir()):
        versions = sorted(contract_directory.glob("v*.odcs.yaml"), key=_version_key)
        transitions.extend(zip(versions, versions[1:], strict=False))
    return transitions


def check_transitions(transitions: Iterable[tuple[Path, Path]]) -> int:
    checked = 0
    failures = 0
    for base_path, candidate_path in transitions:
        checked += 1
        base_contract = yaml.safe_load(base_path.read_text())
        candidate_contract = yaml.safe_load(candidate_path.read_text())
        violations = evaluate_compatibility(base_contract, candidate_contract)

        if not violations:
            print(f"PASS {base_path} -> {candidate_path}")
            continue

        failures += 1
        print(f"FAIL {base_path} -> {candidate_path}")
        for violation in violations:
            print(f"  [{violation.code}] {violation.path}: {violation.message}")

    if failures:
        print(f"Compatibility gate rejected {failures} version transition(s).")
        return 1

    print(f"Compatibility gate passed {checked} version transition(s).")
    return 0


def main() -> int:
    args = parse_args()
    transitions = [tuple(args.contracts)] if args.contracts else discovered_transitions()
    return check_transitions(transitions)


if __name__ == "__main__":
    raise SystemExit(main())
