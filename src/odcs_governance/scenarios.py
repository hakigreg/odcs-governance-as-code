"""Deterministic synthetic datasets for runtime contract demonstrations."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid5

Record = dict[str, Any]


def _subscriber_hash(index: int) -> str:
    return hashlib.sha256(f"synthetic-subscriber-{index}".encode()).hexdigest()


def valid_records(*, now: datetime | None = None, count: int = 60) -> list[Record]:
    """Return a recent, contract-compliant synthetic telecom event batch."""
    reference_time = (now or datetime.now(UTC)).replace(microsecond=0)
    records: list[Record] = []

    for index in range(count):
        event_type = ("call", "sms", "data")[index % 3]
        direction = "not_applicable" if event_type == "data" else ("inbound", "outbound")[index % 2]
        event_timestamp = reference_time - timedelta(minutes=index * 15)

        records.append(
            {
                "event_id": uuid5(NAMESPACE_URL, f"odcs-demo-event-{index}"),
                "subscriber_id_hash": _subscriber_hash(index % 25),
                "event_timestamp": event_timestamp,
                "event_type": event_type,
                "direction": direction,
                "duration_seconds": 45 + index if event_type == "call" else 0,
                "data_volume_mb": round(2.5 + index / 10, 3) if event_type == "data" else 0,
                "cell_region_code": f"AR-{(index % 5) + 1:02d}",
                "ingestion_timestamp": event_timestamp + timedelta(minutes=10),
            }
        )

    return records


def invalid_records(*, now: datetime | None = None) -> list[Record]:
    """Return a batch containing three deliberate contract violations."""
    records = valid_records(now=now)
    records[0]["subscriber_id_hash"] = "not-a-sha256-hash"
    records[1]["duration_seconds"] = -10
    records[2]["direction"] = "inbound"
    return records
