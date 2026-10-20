"""Build a valid or deliberately invalid customer behavior feature snapshot."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from odcs_governance.database import materialize_behavior_features, reset_and_load
from odcs_governance.scenarios import valid_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=("valid", "invalid"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference_time = datetime.now(UTC).replace(microsecond=0)
    records = valid_records(now=reference_time)
    source_count = reset_and_load(records)
    feature_count = materialize_behavior_features(
        feature_window_end=reference_time + timedelta(seconds=1),
        computed_at=reference_time + timedelta(seconds=2),
        invalid=args.scenario == "invalid",
    )
    print(
        f"Loaded {source_count} valid source events and materialized "
        f"{feature_count} rows for the {args.scenario!r} feature scenario."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
