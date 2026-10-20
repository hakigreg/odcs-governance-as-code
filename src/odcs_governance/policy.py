"""Organization-specific governance policies for ODCS contracts."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

Contract = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    policy_id: str
    version: str
    required_description_fields: tuple[str, ...]
    required_team_roles: tuple[str, ...]
    required_sla_properties: tuple[str, ...]
    sensitive_classifications: frozenset[str]
    high_impact_governance_tiers: frozenset[str]
    derived_governance_tiers: frozenset[str]
    decision_governance_tiers: frozenset[str]
    required_decision_properties: tuple[str, ...]
    forbidden_server_keys: frozenset[str]

    @classmethod
    def from_file(cls, path: Path) -> PolicyConfig:
        raw = yaml.safe_load(path.read_text())
        return cls(
            policy_id=raw["id"],
            version=raw["version"],
            required_description_fields=tuple(raw["requiredDescriptionFields"]),
            required_team_roles=tuple(raw["requiredTeamRoles"]),
            required_sla_properties=tuple(raw["requiredSlaProperties"]),
            sensitive_classifications=frozenset(raw["sensitiveClassifications"]),
            high_impact_governance_tiers=frozenset(raw["highImpactGovernanceTiers"]),
            derived_governance_tiers=frozenset(raw["derivedGovernanceTiers"]),
            decision_governance_tiers=frozenset(raw["decisionGovernanceTiers"]),
            required_decision_properties=tuple(raw["requiredDecisionProperties"]),
            forbidden_server_keys=frozenset(raw["forbiddenServerKeys"]),
        )


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    code: str
    path: str
    message: str


def _is_non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _custom_property(contract: Contract, name: str) -> Any | None:
    for item in contract.get("customProperties", []):
        if isinstance(item, Mapping) and item.get("property") == name:
            return item.get("value")
    return None


def _iter_properties(properties: Any, base_path: str) -> Iterator[tuple[str, Contract]]:
    if not isinstance(properties, list):
        return

    for index, prop in enumerate(properties):
        if not isinstance(prop, Mapping):
            continue
        name = prop.get("name", index)
        path = f"{base_path}.{name}"
        yield path, prop
        yield from _iter_properties(prop.get("properties"), f"{path}.properties")


def evaluate_contract(contract: Contract, config: PolicyConfig) -> list[PolicyViolation]:
    """Return every minimum-governance violation found in one contract."""
    violations: list[PolicyViolation] = []

    description = contract.get("description")
    for field in config.required_description_fields:
        value = description.get(field) if isinstance(description, Mapping) else None
        if not _is_non_empty_text(value):
            violations.append(
                PolicyViolation(
                    code="description.required",
                    path=f"description.{field}",
                    message=f"A non-empty {field!r} is required.",
                )
            )

    team = contract.get("team")
    members = team.get("members", []) if isinstance(team, Mapping) else []
    actual_roles = {
        member.get("role", "").casefold()
        for member in members
        if isinstance(member, Mapping) and _is_non_empty_text(member.get("role"))
    }
    for role in config.required_team_roles:
        if role.casefold() not in actual_roles:
            violations.append(
                PolicyViolation(
                    code="team.role.required",
                    path="team.members",
                    message=f"The team must include the {role!r} role.",
                )
            )

    support = contract.get("support", [])
    if not any(
        isinstance(channel, Mapping) and channel.get("scope") == "issues" for channel in support
    ):
        violations.append(
            PolicyViolation(
                code="support.issues.required",
                path="support",
                message="At least one support channel with scope 'issues' is required.",
            )
        )

    actual_sla_properties = {
        item.get("property")
        for item in contract.get("slaProperties", [])
        if isinstance(item, Mapping)
    }
    for sla_property in config.required_sla_properties:
        if sla_property not in actual_sla_properties:
            violations.append(
                PolicyViolation(
                    code="sla.required",
                    path="slaProperties",
                    message=f"SLA property {sla_property!r} is required.",
                )
            )

    forbidden_keys = {key.casefold() for key in config.forbidden_server_keys}
    for index, server in enumerate(contract.get("servers", [])):
        if not isinstance(server, Mapping):
            continue
        for key in server:
            if str(key).casefold() in forbidden_keys:
                violations.append(
                    PolicyViolation(
                        code="server.credential.forbidden",
                        path=f"servers[{index}].{key}",
                        message="Credentials must be supplied through the runtime environment.",
                    )
                )

    for schema_index, schema_object in enumerate(contract.get("schema", [])):
        if not isinstance(schema_object, Mapping):
            continue
        schema_name = schema_object.get("name", schema_index)
        base_path = f"schema.{schema_name}.properties"

        for path, prop in _iter_properties(schema_object.get("properties"), base_path):
            classification = prop.get("classification")
            if not _is_non_empty_text(classification):
                violations.append(
                    PolicyViolation(
                        code="property.classification.required",
                        path=f"{path}.classification",
                        message="Every property must declare a data classification.",
                    )
                )
            elif classification in config.sensitive_classifications and not prop.get("tags"):
                violations.append(
                    PolicyViolation(
                        code="sensitive.tags.required",
                        path=f"{path}.tags",
                        message="Sensitive properties must include handling or sensitivity tags.",
                    )
                )

            if prop.get("criticalDataElement") is True and not prop.get("quality"):
                violations.append(
                    PolicyViolation(
                        code="cde.quality.required",
                        path=f"{path}.quality",
                        message="Critical Data Elements must have at least one quality rule.",
                    )
                )

            for quality_index, quality_rule in enumerate(prop.get("quality", [])):
                quality_id_missing = isinstance(quality_rule, Mapping) and not _is_non_empty_text(
                    quality_rule.get("id")
                )
                if quality_id_missing:
                    violations.append(
                        PolicyViolation(
                            code="quality.id.required",
                            path=f"{path}.quality[{quality_index}].id",
                            message="Every quality rule must have a stable id.",
                        )
                    )

        for quality_index, quality_rule in enumerate(schema_object.get("quality", [])):
            if isinstance(quality_rule, Mapping) and not _is_non_empty_text(quality_rule.get("id")):
                violations.append(
                    PolicyViolation(
                        code="quality.id.required",
                        path=f"schema.{schema_name}.quality[{quality_index}].id",
                        message="Every quality rule must have a stable id.",
                    )
                )

    governance_tier = _custom_property(contract, "governanceTier")
    if governance_tier in config.derived_governance_tiers:
        for property_name in ("sourceContractId", "sourceContractVersion"):
            if not _is_non_empty_text(_custom_property(contract, property_name)):
                violations.append(
                    PolicyViolation(
                        code="derived.lineage.required",
                        path=f"customProperties.{property_name}",
                        message=(
                            f"Derived contracts must declare a non-empty {property_name!r}."
                        ),
                    )
                )

    if governance_tier in config.decision_governance_tiers:
        actual_property_names = {
            prop.get("name")
            for schema_index, schema_object in enumerate(contract.get("schema", []))
            if isinstance(schema_object, Mapping)
            for _, prop in _iter_properties(
                schema_object.get("properties"), f"schema[{schema_index}].properties"
            )
        }
        for property_name in config.required_decision_properties:
            if property_name not in actual_property_names:
                violations.append(
                    PolicyViolation(
                        code="decision.property.required",
                        path=f"schema.*.properties.{property_name}",
                        message=(
                            "High-impact decision contracts must expose the "
                            f"{property_name!r} control field."
                        ),
                    )
                )

    if governance_tier in config.high_impact_governance_tiers:
        context = contract.get("context")
        instructions = context.get("instructions") if isinstance(context, Mapping) else None
        constraints = context.get("constraints") if isinstance(context, Mapping) else None
        if not _is_non_empty_text(instructions):
            violations.append(
                PolicyViolation(
                    code="high-impact.context.required",
                    path="context.instructions",
                    message=(
                        "High-impact contracts must provide machine-readable usage instructions."
                    ),
                )
            )
        if not isinstance(constraints, list) or not constraints:
            violations.append(
                PolicyViolation(
                    code="high-impact.constraints.required",
                    path="context.constraints",
                    message="High-impact contracts must declare at least one usage constraint.",
                )
            )

    return violations
