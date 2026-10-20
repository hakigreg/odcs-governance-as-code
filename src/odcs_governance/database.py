"""PostgreSQL runtime setup for the portfolio demonstration."""

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import datetime, timedelta

import psycopg

from odcs_governance.scenarios import Record

SOURCE_DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
DROP TABLE IF EXISTS raw.telecom_cdr_events;
CREATE TABLE raw.telecom_cdr_events (
    event_id uuid PRIMARY KEY,
    subscriber_id_hash char(64) NOT NULL,
    event_timestamp timestamptz NOT NULL,
    event_type varchar(10) NOT NULL,
    direction varchar(20) NOT NULL,
    duration_seconds integer NOT NULL,
    data_volume_mb numeric(12,3) NOT NULL,
    cell_region_code varchar(20) NOT NULL,
    ingestion_timestamp timestamptz NOT NULL
);
"""

SOURCE_INSERT_SQL = """
INSERT INTO raw.telecom_cdr_events (
    event_id,
    subscriber_id_hash,
    event_timestamp,
    event_type,
    direction,
    duration_seconds,
    data_volume_mb,
    cell_region_code,
    ingestion_timestamp
) VALUES (
    %(event_id)s,
    %(subscriber_id_hash)s,
    %(event_timestamp)s,
    %(event_type)s,
    %(direction)s,
    %(duration_seconds)s,
    %(data_volume_mb)s,
    %(cell_region_code)s,
    %(ingestion_timestamp)s
)
"""

FEATURE_DDL = """
CREATE SCHEMA IF NOT EXISTS analytics;
DROP TABLE IF EXISTS analytics.customer_behavior_features;
CREATE TABLE analytics.customer_behavior_features (
    subscriber_id_hash char(64) NOT NULL,
    feature_window_start timestamptz NOT NULL,
    feature_window_end timestamptz NOT NULL,
    feature_version varchar(20) NOT NULL,
    observation_days integer NOT NULL,
    active_days integer NOT NULL,
    total_events bigint NOT NULL,
    outgoing_call_count bigint NOT NULL,
    total_call_duration_seconds bigint NOT NULL,
    total_data_volume_mb numeric(18,3) NOT NULL,
    mobility_region_count integer NOT NULL,
    computed_at timestamptz NOT NULL,
    PRIMARY KEY (subscriber_id_hash, feature_window_end, feature_version)
);
"""

FEATURE_INSERT_SQL = """
INSERT INTO analytics.customer_behavior_features (
    subscriber_id_hash,
    feature_window_start,
    feature_window_end,
    feature_version,
    observation_days,
    active_days,
    total_events,
    outgoing_call_count,
    total_call_duration_seconds,
    total_data_volume_mb,
    mobility_region_count,
    computed_at
)
SELECT
    subscriber_id_hash,
    %(window_start)s,
    %(window_end)s,
    '1.0.0',
    30,
    COUNT(DISTINCT DATE(event_timestamp))::integer,
    COUNT(*)::bigint,
    COUNT(*) FILTER (
        WHERE event_type = 'call' AND direction = 'outbound'
    )::bigint,
    COALESCE(SUM(duration_seconds) FILTER (
        WHERE event_type = 'call'
    ), 0)::bigint,
    COALESCE(SUM(data_volume_mb) FILTER (
        WHERE event_type = 'data'
    ), 0)::numeric(18,3),
    COUNT(DISTINCT cell_region_code)::integer,
    %(computed_at)s
FROM raw.telecom_cdr_events
WHERE event_timestamp >= %(window_start)s
  AND event_timestamp < %(window_end)s
GROUP BY subscriber_id_hash
"""

INVALID_FEATURE_SQL = (
    """
    WITH target AS (
        SELECT subscriber_id_hash
        FROM analytics.customer_behavior_features
        ORDER BY subscriber_id_hash
        LIMIT 1 OFFSET 0
    )
    UPDATE analytics.customer_behavior_features AS features
    SET feature_window_start = feature_window_end - INTERVAL '29 days'
    FROM target
    WHERE features.subscriber_id_hash = target.subscriber_id_hash
    """,
    """
    WITH target AS (
        SELECT subscriber_id_hash
        FROM analytics.customer_behavior_features
        ORDER BY subscriber_id_hash
        LIMIT 1 OFFSET 1
    )
    UPDATE analytics.customer_behavior_features AS features
    SET total_data_volume_mb = -1
    FROM target
    WHERE features.subscriber_id_hash = target.subscriber_id_hash
    """,
    """
    WITH target AS (
        SELECT subscriber_id_hash
        FROM analytics.customer_behavior_features
        ORDER BY subscriber_id_hash
        LIMIT 1 OFFSET 2
    )
    UPDATE analytics.customer_behavior_features AS features
    SET active_days = observation_days + 1
    FROM target
    WHERE features.subscriber_id_hash = target.subscriber_id_hash
    """,
)

DECISION_DDL = """
CREATE SCHEMA IF NOT EXISTS risk;
DROP TABLE IF EXISTS risk.credit_risk_decisions;
CREATE TABLE risk.credit_risk_decisions (
    decision_id uuid PRIMARY KEY,
    application_id_hash char(64) NOT NULL,
    subscriber_id_hash char(64) NOT NULL,
    decision_timestamp timestamptz NOT NULL,
    feature_window_end timestamptz NOT NULL,
    feature_version varchar(20) NOT NULL,
    model_id varchar(100) NOT NULL,
    model_version varchar(30) NOT NULL,
    risk_score numeric(6,5) NOT NULL,
    risk_band varchar(10) NOT NULL,
    model_recommendation varchar(30) NOT NULL,
    primary_reason_code varchar(40) NOT NULL,
    human_review_status varchar(20) NOT NULL,
    decision_outcome varchar(20) NOT NULL,
    recorded_at timestamptz NOT NULL
);
"""

DECISION_INSERT_SQL = """
WITH scored AS (
    SELECT
        features.*,
        (
            MOD(ABS(HASHTEXT(TRIM(subscriber_id_hash)))::bigint, 100)::numeric / 100
        )::numeric(6,5) AS calculated_risk_score
    FROM analytics.customer_behavior_features AS features
), classified AS (
    SELECT
        scored.*,
        CASE
            WHEN calculated_risk_score < 0.35 THEN 'low'
            WHEN calculated_risk_score < 0.70 THEN 'medium'
            ELSE 'high'
        END AS calculated_risk_band
    FROM scored
)
INSERT INTO risk.credit_risk_decisions (
    decision_id,
    application_id_hash,
    subscriber_id_hash,
    decision_timestamp,
    feature_window_end,
    feature_version,
    model_id,
    model_version,
    risk_score,
    risk_band,
    model_recommendation,
    primary_reason_code,
    human_review_status,
    decision_outcome,
    recorded_at
)
SELECT
    MD5(
        TRIM(subscriber_id_hash) || feature_window_end::text || feature_version
    )::uuid,
    ENCODE(
        SHA256(CONVERT_TO('application-' || TRIM(subscriber_id_hash), 'UTF8')),
        'hex'
    ),
    subscriber_id_hash,
    computed_at + INTERVAL '1 second',
    feature_window_end,
    feature_version,
    'portfolio-credit-risk-proxy',
    '1.0.0',
    calculated_risk_score,
    calculated_risk_band,
    CASE calculated_risk_band
        WHEN 'low' THEN 'approve_candidate'
        WHEN 'medium' THEN 'manual_review'
        ELSE 'decline_candidate'
    END,
    CASE calculated_risk_band
        WHEN 'low' THEN 'favorable_activity'
        WHEN 'medium' THEN 'limited_history'
        ELSE 'elevated_risk_signal'
    END,
    CASE calculated_risk_band
        WHEN 'low' THEN 'not_required'
        WHEN 'medium' THEN 'pending'
        ELSE 'completed'
    END,
    CASE calculated_risk_band
        WHEN 'low' THEN 'approved'
        WHEN 'medium' THEN 'referred'
        ELSE 'declined'
    END,
    computed_at + INTERVAL '2 seconds'
FROM classified
"""

INVALID_DECISION_SQL = (
    """
    WITH target AS (
        SELECT decision_id
        FROM risk.credit_risk_decisions
        ORDER BY decision_id
        LIMIT 1 OFFSET 0
    )
    UPDATE risk.credit_risk_decisions AS decisions
    SET feature_window_end = decision_timestamp + INTERVAL '1 hour'
    FROM target
    WHERE decisions.decision_id = target.decision_id
    """,
    """
    WITH target AS (
        SELECT decision_id
        FROM risk.credit_risk_decisions
        ORDER BY decision_id
        LIMIT 1 OFFSET 1
    )
    UPDATE risk.credit_risk_decisions AS decisions
    SET risk_score = CASE risk_band WHEN 'low' THEN 0.90 ELSE 0.10 END
    FROM target
    WHERE decisions.decision_id = target.decision_id
    """,
    """
    WITH target AS (
        SELECT decision_id
        FROM risk.credit_risk_decisions
        ORDER BY decision_id
        LIMIT 1 OFFSET 2
    )
    UPDATE risk.credit_risk_decisions AS decisions
    SET model_recommendation = CASE
        WHEN model_recommendation = 'manual_review' THEN 'approve_candidate'
        ELSE 'manual_review'
    END
    FROM target
    WHERE decisions.decision_id = target.decision_id
    """,
    """
    WITH target AS (
        SELECT decision_id
        FROM risk.credit_risk_decisions
        ORDER BY decision_id
        LIMIT 1 OFFSET 3
    )
    UPDATE risk.credit_risk_decisions AS decisions
    SET decision_outcome = 'declined', human_review_status = 'pending'
    FROM target
    WHERE decisions.decision_id = target.decision_id
    """,
    """
    WITH target AS (
        SELECT decision_id
        FROM risk.credit_risk_decisions
        ORDER BY decision_id
        LIMIT 1 OFFSET 4
    )
    UPDATE risk.credit_risk_decisions AS decisions
    SET recorded_at = decision_timestamp - INTERVAL '1 second'
    FROM target
    WHERE decisions.decision_id = target.decision_id
    """,
)


def reset_and_load(records: Iterable[Record], database_url: str | None = None) -> int:
    """Recreate the demo table and load the supplied records."""
    materialized_records = list(records)
    connection_string = database_url or os.environ["DATABASE_URL"]

    with psycopg.connect(connection_string) as connection, connection.cursor() as cursor:
        cursor.execute(SOURCE_DDL)
        cursor.executemany(SOURCE_INSERT_SQL, materialized_records)

    return len(materialized_records)


def materialize_behavior_features(
    *,
    feature_window_end: datetime,
    computed_at: datetime,
    invalid: bool = False,
    database_url: str | None = None,
) -> int:
    """Build the governed feature table from the loaded telecom source."""
    connection_string = database_url or os.environ["DATABASE_URL"]
    parameters = {
        "window_start": feature_window_end - timedelta(days=30),
        "window_end": feature_window_end,
        "computed_at": computed_at,
    }

    with psycopg.connect(connection_string) as connection, connection.cursor() as cursor:
        cursor.execute(FEATURE_DDL)
        cursor.execute(FEATURE_INSERT_SQL, parameters)
        feature_count = cursor.rowcount

        if invalid:
            for statement in INVALID_FEATURE_SQL:
                cursor.execute(statement)

    return feature_count


def materialize_credit_decisions(
    *,
    invalid: bool = False,
    database_url: str | None = None,
) -> int:
    """Build auditable decision records from the governed feature table."""
    connection_string = database_url or os.environ["DATABASE_URL"]

    with psycopg.connect(connection_string) as connection, connection.cursor() as cursor:
        cursor.execute(DECISION_DDL)
        cursor.execute(DECISION_INSERT_SQL)
        decision_count = cursor.rowcount

        if invalid:
            for statement in INVALID_DECISION_SQL:
                cursor.execute(statement)

    return decision_count
