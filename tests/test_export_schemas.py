from __future__ import annotations

from types import SimpleNamespace

import pytest

from matintegrity.contracts import Contract
from matintegrity.registry import default_registry
from scripts.audit_schema_coverage import audit_schema_coverage
from scripts.export_schemas import complete_export_contracts, contract_schema_filename, write_schema_index


def test_unique_contract_names_keep_legacy_filename():
    contract = SimpleNamespace(__name__="UniqueContract", __module__="matintegrity.example")
    assert contract_schema_filename(contract, {"UniqueContract": 1}) == "UniqueContract.json"


def test_colliding_contract_names_use_their_own_module_names():
    first = SimpleNamespace(__name__="Criterion", __module__="matintegrity.models.chemical_cleaning_campaign")
    second = SimpleNamespace(__name__="Criterion", __module__="matintegrity.models.repair_welding_campaign")
    counts = {"Criterion": 2}
    assert contract_schema_filename(first, counts) == "chemical_cleaning_campaign__Criterion.json"
    assert contract_schema_filename(second, counts) == "repair_welding_campaign__Criterion.json"


def test_all_registered_inputs_are_included_without_manual_enumeration():
    registry = default_registry()
    contracts = complete_export_contracts((), registry)
    assert set(contracts) == {registry.input_type(model) for model in registry.list_models()}
    assert len(contracts) == len(set(contracts))


def test_explicit_nested_contracts_and_alias_input_types_are_preserved():
    class Nested(Contract):
        value: float

    class Input(Contract):
        child: Nested

    registry = SimpleNamespace(list_models=lambda: ("first", "alias"), input_type=lambda _: Input)
    assert complete_export_contracts((Nested, Input, Nested), registry) == (Nested, Input)


def test_schema_index_binds_model_to_actual_file_digest(tmp_path):
    import hashlib
    import json

    class Input(Contract):
        value: float

    target = tmp_path / "Input.json"
    target.write_text(json.dumps(Input.model_json_schema()), encoding="utf-8")
    registry = SimpleNamespace(list_models=lambda: ("example",), input_type=lambda _: Input)
    index = write_schema_index(tmp_path, (Input,), {"Input": 1}, registry)
    assert index["models"]["example"]["filename"] == "Input.json"
    assert index["models"]["example"]["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    assert json.loads((tmp_path / "schema_index.json").read_text(encoding="utf-8")) == index
    assert audit_schema_coverage(tmp_path, registry)["covered_models"] == 1
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        audit_schema_coverage(tmp_path, registry)


def test_coverage_audit_rejects_wrong_schema_even_with_updated_digest(tmp_path):
    class Input(Contract):
        value: float

    target = tmp_path / "Input.json"
    target.write_text("{}", encoding="utf-8")
    registry = SimpleNamespace(list_models=lambda: ("example",), input_type=lambda _: Input)
    write_schema_index(tmp_path, (Input,), {"Input": 1}, registry)
    with pytest.raises(ValueError, match="differs from executable"):
        audit_schema_coverage(tmp_path, registry)


def test_coverage_audit_rejects_stale_model_set(tmp_path):
    import json

    class Input(Contract):
        value: float

    (tmp_path / "Input.json").write_text(json.dumps(Input.model_json_schema()), encoding="utf-8")
    registry = SimpleNamespace(list_models=lambda: ("example",), input_type=lambda _: Input)
    write_schema_index(tmp_path, (Input,), {"Input": 1}, registry)
    changed = SimpleNamespace(list_models=lambda: ("example", "new"), input_type=lambda _: Input)
    with pytest.raises(ValueError, match="registered model set"):
        audit_schema_coverage(tmp_path, changed)
