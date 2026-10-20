from copy import deepcopy
from pathlib import Path

import yaml

from odcs_governance.policy import PolicyConfig, evaluate_contract

POLICY = PolicyConfig.from_file(Path("policies/minimum-governance.yaml"))
CONTRACT = yaml.safe_load(
    Path("contracts/telecom_cdr_events/v1.0.0.odcs.yaml").read_text()
)


def violation_codes(contract: dict) -> set[str]:
    return {violation.code for violation in evaluate_contract(contract, POLICY)}


def test_current_contract_satisfies_minimum_governance() -> None:
    assert evaluate_contract(CONTRACT, POLICY) == []


def test_owner_and_steward_are_required() -> None:
    contract = deepcopy(CONTRACT)
    contract["team"]["members"] = [
        member for member in contract["team"]["members"] if member["role"] == "Technical Owner"
    ]

    assert "team.role.required" in violation_codes(contract)


def test_critical_data_elements_require_quality_rules() -> None:
    contract = deepcopy(CONTRACT)
    event_id = contract["schema"][0]["properties"][0]
    event_id.pop("quality")

    assert "cde.quality.required" in violation_codes(contract)


def test_every_property_requires_classification() -> None:
    contract = deepcopy(CONTRACT)
    contract["schema"][0]["properties"][3].pop("classification")

    assert "property.classification.required" in violation_codes(contract)


def test_sensitive_properties_require_tags() -> None:
    contract = deepcopy(CONTRACT)
    subscriber_id = contract["schema"][0]["properties"][1]
    subscriber_id.pop("tags")

    assert "sensitive.tags.required" in violation_codes(contract)


def test_high_impact_contracts_require_ai_context() -> None:
    contract = deepcopy(CONTRACT)
    contract.pop("context")

    codes = violation_codes(contract)
    assert "high-impact.context.required" in codes
    assert "high-impact.constraints.required" in codes


def test_credentials_are_forbidden_in_server_definitions() -> None:
    contract = deepcopy(CONTRACT)
    contract["servers"][0]["password"] = "do-not-commit-secrets"

    assert "server.credential.forbidden" in violation_codes(contract)


def test_derived_contracts_require_source_lineage() -> None:
    contract = deepcopy(CONTRACT)
    governance_tier = next(
        item
        for item in contract["customProperties"]
        if item["property"] == "governanceTier"
    )
    governance_tier["value"] = "high-impact-derived"

    violations = evaluate_contract(contract, POLICY)
    lineage_paths = {
        violation.path
        for violation in violations
        if violation.code == "derived.lineage.required"
    }

    assert lineage_paths == {
        "customProperties.sourceContractId",
        "customProperties.sourceContractVersion",
    }


def test_decision_contracts_require_auditability_fields() -> None:
    contract = deepcopy(CONTRACT)
    governance_tier = next(
        item
        for item in contract["customProperties"]
        if item["property"] == "governanceTier"
    )
    governance_tier["value"] = "high-impact-decision"

    violations = evaluate_contract(contract, POLICY)
    decision_paths = {
        violation.path
        for violation in violations
        if violation.code == "decision.property.required"
    }

    assert decision_paths == {
        f"schema.*.properties.{property_name}"
        for property_name in POLICY.required_decision_properties
    }
