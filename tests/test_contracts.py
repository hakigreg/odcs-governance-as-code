from pathlib import Path

import yaml
from open_data_contract_standard.model import OpenDataContractStandard

CONTRACTS = sorted(Path("contracts").glob("**/*.odcs.yaml"))


def test_repository_contains_versioned_contracts() -> None:
    assert CONTRACTS, "At least one versioned ODCS contract is required"


def test_contracts_parse_with_official_model() -> None:
    for contract_file in CONTRACTS:
        OpenDataContractStandard.from_file(contract_file)


def test_contracts_target_odcs_3_2_0() -> None:
    for contract_file in CONTRACTS:
        contract = yaml.safe_load(contract_file.read_text())
        assert contract["apiVersion"] == "v3.2.0"
        assert contract["kind"] == "DataContract"


def test_contract_filename_matches_declared_version() -> None:
    for contract_file in CONTRACTS:
        contract = yaml.safe_load(contract_file.read_text())
        assert contract_file.name == f"v{contract['version']}.odcs.yaml"


def test_declared_source_contracts_exist_at_the_required_version() -> None:
    contracts = [yaml.safe_load(contract_file.read_text()) for contract_file in CONTRACTS]
    available_contracts = {
        (contract["id"], str(contract["version"])) for contract in contracts
    }

    for contract in contracts:
        custom_properties = {
            item["property"]: str(item["value"])
            for item in contract.get("customProperties", [])
        }
        source_id = custom_properties.get("sourceContractId")
        if source_id is None:
            continue

        assert (
            source_id,
            custom_properties["sourceContractVersion"],
        ) in available_contracts
