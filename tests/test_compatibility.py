from copy import deepcopy
from pathlib import Path

import yaml

from odcs_governance.compatibility import evaluate_compatibility

BASE = yaml.safe_load(
    Path("contracts/customer_behavior_features/v1.0.0.odcs.yaml").read_text()
)


def candidate_contract() -> dict:
    candidate = deepcopy(BASE)
    candidate["version"] = "1.1.0"
    return candidate


def property_by_name(contract: dict, name: str) -> dict:
    return next(prop for prop in contract["schema"][0]["properties"] if prop["name"] == name)


def violation_codes(candidate: dict) -> set[str]:
    return {violation.code for violation in evaluate_compatibility(BASE, candidate)}


def test_unchanged_interface_with_increased_version_is_compatible() -> None:
    assert evaluate_compatibility(BASE, candidate_contract()) == []


def test_removed_property_is_breaking() -> None:
    candidate = candidate_contract()
    candidate["schema"][0]["properties"] = [
        prop
        for prop in candidate["schema"][0]["properties"]
        if prop["name"] != "total_data_volume_mb"
    ]

    assert "property.removed" in violation_codes(candidate)


def test_changed_physical_type_is_breaking() -> None:
    candidate = candidate_contract()
    property_by_name(candidate, "total_events")["physicalType"] = "integer"

    assert "property.type.changed" in violation_codes(candidate)


def test_new_required_property_is_breaking_but_optional_is_compatible() -> None:
    optional_candidate = candidate_contract()
    optional_candidate["schema"][0]["properties"].append(
        {
            "name": "optional_note",
            "logicalType": "string",
            "physicalType": "varchar(100)",
            "required": False,
        }
    )
    required_candidate = deepcopy(optional_candidate)
    property_by_name(required_candidate, "optional_note")["required"] = True

    assert evaluate_compatibility(BASE, optional_candidate) == []
    assert "property.required.added" in violation_codes(required_candidate)


def test_enum_changes_are_breaking_in_full_compatibility_mode() -> None:
    base_with_enum = deepcopy(BASE)
    property_by_name(base_with_enum, "feature_version")["enum"] = [
        {"value": "1.0.0"},
        {"value": "1.1.0"},
    ]
    candidate = deepcopy(base_with_enum)
    candidate["version"] = "1.1.0"
    property_by_name(candidate, "feature_version")["enum"] = [
        {"value": "1.1.0"},
        {"value": "2.0.0"},
    ]

    codes = {
        violation.code for violation in evaluate_compatibility(base_with_enum, candidate)
    }
    assert "property.enum.removed" in codes
    assert "property.enum.added" in codes


def test_tighter_classification_is_breaking() -> None:
    candidate = candidate_contract()
    property_by_name(candidate, "total_events")["classification"] = "confidential"

    assert "property.classification.tightened" in violation_codes(candidate)
