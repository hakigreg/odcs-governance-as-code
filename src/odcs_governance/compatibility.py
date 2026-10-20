"""Conservative compatibility rules for versioned ODCS interfaces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

Contract = Mapping[str, Any]

CLASSIFICATION_RANK = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "restricted": 3,
}


@dataclass(frozen=True, slots=True)
class CompatibilityViolation:
    code: str
    path: str
    message: str


def _named_items(items: Any) -> dict[str, Contract]:
    if not isinstance(items, list):
        return {}
    return {
        item["name"]: item
        for item in items
        if isinstance(item, Mapping) and isinstance(item.get("name"), str)
    }


def _enum_values(prop: Contract) -> set[Any]:
    values: set[Any] = set()
    for item in prop.get("enum", []):
        values.add(item.get("value") if isinstance(item, Mapping) else item)
    return values


def _semantic_version(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def _compare_properties(
    base_properties: Any,
    candidate_properties: Any,
    base_path: str,
) -> list[CompatibilityViolation]:
    violations: list[CompatibilityViolation] = []
    base = _named_items(base_properties)
    candidate = _named_items(candidate_properties)

    for name in sorted(base.keys() - candidate.keys()):
        violations.append(
            CompatibilityViolation(
                code="property.removed",
                path=f"{base_path}.{name}",
                message="An existing property cannot be removed from a compatible version.",
            )
        )

    for name in sorted(candidate.keys() - base.keys()):
        if candidate[name].get("required") is True:
            violations.append(
                CompatibilityViolation(
                    code="property.required.added",
                    path=f"{base_path}.{name}",
                    message="A newly added property must be optional in a compatible version.",
                )
            )

    for name in sorted(base.keys() & candidate.keys()):
        original = base[name]
        updated = candidate[name]
        path = f"{base_path}.{name}"

        for type_field in ("logicalType", "physicalType"):
            if original.get(type_field) != updated.get(type_field):
                violations.append(
                    CompatibilityViolation(
                        code="property.type.changed",
                        path=f"{path}.{type_field}",
                        message=(
                            f"{type_field} changed from {original.get(type_field)!r} "
                            f"to {updated.get(type_field)!r}."
                        ),
                    )
                )

        if original.get("required") is not True and updated.get("required") is True:
            violations.append(
                CompatibilityViolation(
                    code="property.required.tightened",
                    path=f"{path}.required",
                    message="An existing optional property cannot become required.",
                )
            )

        for key_field in ("primaryKey", "primaryKeyPosition"):
            if original.get(key_field) != updated.get(key_field):
                violations.append(
                    CompatibilityViolation(
                        code="property.key.changed",
                        path=f"{path}.{key_field}",
                        message=f"{key_field} cannot change in a compatible version.",
                    )
                )

        original_classification = original.get("classification")
        updated_classification = updated.get("classification")
        original_rank = CLASSIFICATION_RANK.get(original_classification)
        updated_rank = CLASSIFICATION_RANK.get(updated_classification)
        if (
            original_rank is not None
            and updated_rank is not None
            and updated_rank > original_rank
        ):
            violations.append(
                CompatibilityViolation(
                    code="property.classification.tightened",
                    path=f"{path}.classification",
                    message=(
                        f"Classification tightened from {original_classification!r} "
                        f"to {updated_classification!r}."
                    ),
                )
            )

        original_enum = _enum_values(original)
        updated_enum = _enum_values(updated)
        for value in sorted(original_enum - updated_enum, key=str):
            violations.append(
                CompatibilityViolation(
                    code="property.enum.removed",
                    path=f"{path}.enum",
                    message=f"Existing enum value {value!r} was removed.",
                )
            )
        for value in sorted(updated_enum - original_enum, key=str):
            violations.append(
                CompatibilityViolation(
                    code="property.enum.added",
                    path=f"{path}.enum",
                    message=(
                        f"New enum value {value!r} may break exhaustive downstream consumers."
                    ),
                )
            )

        violations.extend(
            _compare_properties(
                original.get("properties"),
                updated.get("properties"),
                f"{path}.properties",
            )
        )

    return violations


def evaluate_compatibility(
    base_contract: Contract,
    candidate_contract: Contract,
) -> list[CompatibilityViolation]:
    """Return every incompatible change from base to candidate."""
    violations: list[CompatibilityViolation] = []

    if base_contract.get("id") != candidate_contract.get("id"):
        violations.append(
            CompatibilityViolation(
                code="contract.id.changed",
                path="id",
                message="A version transition must preserve the contract id.",
            )
        )

    base_version = _semantic_version(base_contract.get("version"))
    candidate_version = _semantic_version(candidate_contract.get("version"))
    if base_version is None or candidate_version is None or candidate_version <= base_version:
        violations.append(
            CompatibilityViolation(
                code="contract.version.not-increased",
                path="version",
                message="Candidate version must be a greater MAJOR.MINOR.PATCH version.",
            )
        )

    base_schemas = _named_items(base_contract.get("schema"))
    candidate_schemas = _named_items(candidate_contract.get("schema"))

    for name in sorted(base_schemas.keys() - candidate_schemas.keys()):
        violations.append(
            CompatibilityViolation(
                code="schema.removed",
                path=f"schema.{name}",
                message="An existing schema object cannot be removed from a compatible version.",
            )
        )

    for name in sorted(base_schemas.keys() & candidate_schemas.keys()):
        original = base_schemas[name]
        updated = candidate_schemas[name]
        for physical_field in ("physicalName", "physicalType"):
            if original.get(physical_field) != updated.get(physical_field):
                violations.append(
                    CompatibilityViolation(
                        code="schema.physical.changed",
                        path=f"schema.{name}.{physical_field}",
                        message=f"{physical_field} cannot change in a compatible version.",
                    )
                )
        violations.extend(
            _compare_properties(
                original.get("properties"),
                updated.get("properties"),
                f"schema.{name}.properties",
            )
        )

    return violations
