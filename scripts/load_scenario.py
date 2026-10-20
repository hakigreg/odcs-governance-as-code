"""Load a valid or deliberately invalid runtime demonstration scenario."""

from __future__ import annotations

import argparse

from odcs_governance.database import reset_and_load
from odcs_governance.scenarios import invalid_records, valid_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=("valid", "invalid"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = valid_records() if args.scenario == "valid" else invalid_records()
    loaded = reset_and_load(records)
    print(f"Loaded {loaded} rows for the {args.scenario!r} scenario.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
