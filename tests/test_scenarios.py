import re
from datetime import UTC, datetime

from odcs_governance.scenarios import invalid_records, valid_records

REFERENCE_TIME = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def test_valid_scenario_is_deterministic_and_contract_compliant() -> None:
    records = valid_records(now=REFERENCE_TIME)

    assert len(records) == 60
    assert len({record["event_id"] for record in records}) == 60
    assert len({record["subscriber_id_hash"] for record in records}) == 25
    assert all(SHA256_PATTERN.fullmatch(record["subscriber_id_hash"]) for record in records)
    assert all(record["duration_seconds"] >= 0 for record in records)
    assert all(record["data_volume_mb"] >= 0 for record in records)
    assert all(
        (record["event_type"] == "data") == (record["direction"] == "not_applicable")
        for record in records
    )


def test_invalid_scenario_contains_the_expected_violations() -> None:
    records = invalid_records(now=REFERENCE_TIME)

    assert not SHA256_PATTERN.fullmatch(records[0]["subscriber_id_hash"])
    assert records[1]["duration_seconds"] < 0
    assert records[2]["event_type"] == "data"
    assert records[2]["direction"] != "not_applicable"
