"""Input contract checks for core physics model inputs."""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import get_args

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from matintegrity.registry import default_registry

_CASES = Path(__file__).parent / "data" / "core_physics_missing_input_targets.json"
_BASELINES = Path(__file__).parent / "data" / "core_physics_valid_input_baselines.json"


def _strictly_below(bound: int | float) -> int | float:
    return bound - 1 if isinstance(bound, int) else math.nextafter(float(bound), -math.inf)


def _strictly_above(bound: int | float) -> int | float:
    return bound + 1 if isinstance(bound, int) else math.nextafter(float(bound), math.inf)


@lru_cache(maxsize=1)
def _registry():
    return default_registry()


def _uncovered_model_ids() -> list[str]:
    cases = json.loads(_CASES.read_text(encoding="utf-8"))
    return cases["model_ids"]


def _example_inputs() -> dict[str, dict]:
    return json.loads(_BASELINES.read_text(encoding="utf-8"))["model_inputs"]


def _type_mutations() -> list[tuple[str, str, dict]]:
    registry = _registry()
    baselines = _example_inputs()
    cases = []
    for model_id in _uncovered_model_ids():
        payload = baselines.get(model_id)
        if payload is None:
            continue
        for name, value in payload.items():
            if isinstance(value, bool):
                replacement = "__invalid_boolean_type__"
            elif isinstance(value, str):
                replacement = 123456789
            elif isinstance(value, (int, float)):
                replacement = "__invalid_numeric_type__"
            elif isinstance(value, list):
                replacement = {"__invalid_shape__": True}
            elif isinstance(value, dict):
                replacement = ["__invalid_shape__"]
            else:
                continue
            mutated = dict(payload)
            mutated[name] = replacement
            try:
                registry._models[model_id].input_type.model_validate_json(
                    json.dumps(mutated, allow_nan=False)
                )
            except ValidationError:
                cases.append((model_id, name, mutated))
    return cases


def _numeric_bound_mutations() -> list[tuple[str, str, dict]]:
    registry = _registry()
    baselines = _example_inputs()
    cases = []
    for model_id, payload in baselines.items():
        schema = registry._models[model_id].input_type.model_json_schema()
        for name, value in payload.items():
            field_schema = schema.get("properties", {}).get(name, {})
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            candidates = []
            if "minimum" in field_schema:
                candidates.append(_strictly_below(field_schema["minimum"]))
            if "exclusiveMinimum" in field_schema:
                candidates.append(field_schema["exclusiveMinimum"])
            if "maximum" in field_schema:
                candidates.append(_strictly_above(field_schema["maximum"]))
            if "exclusiveMaximum" in field_schema:
                candidates.append(field_schema["exclusiveMaximum"])
            for invalid_value in candidates:
                mutated = dict(payload)
                mutated[name] = invalid_value
                cases.append((model_id, name, mutated))
    return cases


def _required_null_probes() -> list[tuple[str, str]]:
    registry = _registry()
    return [
        (model_id, name)
        for model_id in _uncovered_model_ids()
        for name, field in registry._models[model_id].input_type.model_fields.items()
        if field.is_required()
    ]


def _required_type_probes() -> list[tuple[str, str, object]]:
    registry = _registry()
    probes = []
    for model_id in _uncovered_model_ids():
        schema = registry._models[model_id].input_type.model_json_schema()
        for name, field in registry._models[model_id].input_type.model_fields.items():
            if not field.is_required():
                continue
            shape = schema.get("properties", {}).get(name, {})
            if "anyOf" in shape:
                shape = next((item for item in shape["anyOf"] if item.get("type") != "null"), shape)
            kind = shape.get("type")
            invalid = {
                "string": 2026,
                "integer": "invalid-integer",
                "number": "invalid-number",
                "boolean": "invalid-boolean",
                "array": {"invalid-array": True},
                "object": ["invalid-object"],
            }.get(kind)
            if invalid is not None:
                probes.append((model_id, name, invalid))
    return probes


def _optional_scalar_type_probes() -> list[tuple[type[BaseModel], str, object]]:
    """Probe wrong JSON shapes on optional non-null fields without full payload fixtures."""
    probes = []
    for contract_type in _contract_types():
        for name, field in contract_type.model_fields.items():
            if field.is_required():
                continue
            annotation = field.annotation
            candidates = [arg for arg in get_args(annotation) if arg is not type(None)]
            scalar = next((arg for arg in candidates if arg in {str, int, float, bool}), None)
            if scalar is None and annotation in {str, int, float, bool}:
                scalar = annotation
            text = str(annotation)
            if scalar is not None:
                invalid = {str: 2026, int: "invalid-integer", float: "invalid-number", bool: "invalid-boolean"}[scalar]
            elif "Literal" in text or "str" in text:
                invalid = 2026
            elif "tuple" in text or "list" in text or "Sequence" in text:
                invalid = {"invalid-array-shape": True}
            elif "dict" in text or "Mapping" in text:
                invalid = ["invalid-object-shape"]
            else:
                continue
            try:
                TypeAdapter(annotation).validate_python(invalid, strict=True)
            except ValidationError:
                probes.append((contract_type, name, invalid))
    return probes


def _contract_types() -> list[type[BaseModel]]:
    registry = _registry()
    found: set[type[BaseModel]] = set()

    def visit(annotation: object) -> None:
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            if annotation in found:
                return
            found.add(annotation)
            for field in annotation.model_fields.values():
                visit(field.annotation)
        for argument in get_args(annotation):
            visit(argument)

    for model_id in _uncovered_model_ids():
        visit(registry._models[model_id].input_type)
    return sorted(found, key=lambda model: (model.__module__, model.__name__))


def _nested_required_fields() -> list[tuple[type[BaseModel], str]]:
    roots = {_registry()._models[mid].input_type for mid in _uncovered_model_ids()}
    return [
        (contract_type, name)
        for contract_type in _contract_types()
        if contract_type not in roots
        for name, field in contract_type.model_fields.items()
        if field.is_required()
    ]


def _nested_wrong_type_probes() -> list[tuple[type[BaseModel], str, object]]:
    roots = {_registry()._models[mid].input_type for mid in _uncovered_model_ids()}
    probes = []
    for contract_type in _contract_types():
        if contract_type in roots:
            continue
        schema = contract_type.model_json_schema()
        for name, field in contract_type.model_fields.items():
            if not field.is_required():
                continue
            shape = schema.get("properties", {}).get(name, {})
            if "anyOf" in shape:
                shape = next((item for item in shape["anyOf"] if item.get("type") != "null"), shape)
            invalid = {
                "string": 2026,
                "integer": "invalid-integer",
                "number": "invalid-number",
                "boolean": "invalid-boolean",
                "array": {"invalid-array": True},
                "object": ["invalid-object"],
            }.get(shape.get("type"))
            if invalid is not None:
                probes.append((contract_type, name, invalid))
    return probes


def _nested_required_evidence_fields() -> list[tuple[type[BaseModel], str]]:
    roots = {_registry()._models[mid].input_type for mid in _uncovered_model_ids()}
    return [
        (contract_type, name)
        for contract_type in _contract_types()
        if contract_type not in roots
        for name, field in contract_type.model_fields.items()
        if "evidence" in name.lower()
        and field.is_required()
        and get_args(field.annotation)
        and "Evidence" in str(field.annotation)
    ]


def _standalone_numeric_bound_probes() -> list[tuple[type[BaseModel], str, object]]:
    registry = _registry()
    unit_inventory = json.loads(
        (Path(__file__).parent / "data" / "core_physics_input_contract_inventory.json").read_text(
            encoding="utf-8"
        )
    )
    probes = []
    for row in unit_inventory:
        contract_type = registry._models[row["model_id"]].input_type
        for name in row["unit_fields"]:
            field = contract_type.model_fields.get(name)
            if field is None or field.annotation is not int:
                continue
            schema = contract_type.model_json_schema()["properties"][name]
            if "minimum" in schema:
                probes.append((contract_type, name, schema["minimum"] - 1))
            elif "exclusiveMinimum" in schema:
                probes.append((contract_type, name, schema["exclusiveMinimum"]))
            if "maximum" in schema:
                probes.append((contract_type, name, schema["maximum"] + 1))
            elif "exclusiveMaximum" in schema:
                probes.append((contract_type, name, schema["exclusiveMaximum"]))
    return probes


def _baseline_physical_input_probes() -> list[tuple[str, str, object]]:
    return [
        ("corrosion.faraday", "molar_mass_kg_mol", -1.0),
        ("corrosion.stern_geary", "anodic_tafel_slope_V_decade", -1.0),
        ("degradation.archard_wear", "hardness_Pa", 0.0),
        ("fracture.stress_intensity", "crack_depth_m", 0.0),
        ("transport.semi_infinite_diffusion", "diffusivity_m2_s", 0.0),
    ]


def _schema_invalid_values(field_schema: dict) -> list[object]:
    """Build invalid JSON-native values for constraints at any schema depth."""
    if "$ref" in field_schema:
        return []  # referenced Contract fields are checked as their own model type
    candidates: list[object] = []
    branches = field_schema.get("anyOf", field_schema.get("oneOf", []))
    if branches:
        for branch in branches:
            if branch.get("type") != "null":
                candidates.extend(_schema_invalid_values(branch))
        return candidates
    if "enum" in field_schema:
        candidates.append("__invalid_enum_member__")
    kind = field_schema.get("type")
    if kind == "string":
        if field_schema.get("minLength", 0) > 0:
            candidates.append("")
        if "maxLength" in field_schema:
            candidates.append("x" * (field_schema["maxLength"] + 1))
        if "pattern" in field_schema:
            candidates.append("__invalid_pattern__")
    elif kind in {"integer", "number"}:
        if "minimum" in field_schema:
            candidates.append(_strictly_below(field_schema["minimum"]))
        if "exclusiveMinimum" in field_schema:
            candidates.append(field_schema["exclusiveMinimum"])
        if "maximum" in field_schema:
            candidates.append(_strictly_above(field_schema["maximum"]))
        if "exclusiveMaximum" in field_schema:
            candidates.append(field_schema["exclusiveMaximum"])
    elif kind == "array":
        minimum = field_schema.get("minItems", 0)
        if minimum > 0:
            candidates.append([])
        if "maxItems" in field_schema:
            candidates.append([None] * (field_schema["maxItems"] + 1))
        item_schemas = field_schema.get("prefixItems") or [field_schema.get("items", {})]
        if isinstance(item_schemas, dict):
            item_schemas = [item_schemas]
        for index, item_schema in enumerate(item_schemas):
            for invalid_item in _schema_invalid_values(item_schema):
                size = max(minimum, index + 1, len(item_schemas) if "prefixItems" in field_schema else 1)
                value = [0] * size
                value[index] = invalid_item
                candidates.append(value)
    elif kind == "object":
        if field_schema.get("minProperties", 0) > 0:
            candidates.append({})
        if "maxProperties" in field_schema:
            count = field_schema["maxProperties"] + 1
            properties = list(field_schema.get("properties", {}))
            if field_schema.get("additionalProperties") is not False:
                properties.extend(f"__probe_{index}" for index in range(count - len(properties)))
            candidates.append({key: None for key in properties[:count]})
        additional = field_schema.get("additionalProperties")
        if isinstance(additional, dict):
            for invalid_value in _schema_invalid_values(additional):
                candidates.append({"__schema_probe__": invalid_value})
    return candidates


def _schema_constraint_probes() -> list[tuple[type[BaseModel], str, object]]:
    """Probe each root and nested Contract field directly, including collection items."""
    probes = []
    for contract_type in _contract_types():
        schema = contract_type.model_json_schema()
        for name, field_schema in schema.get("properties", {}).items():
            for invalid_value in _schema_invalid_values(field_schema):
                probes.append((contract_type, name, invalid_value))
    return probes


def _evidence_removal_probes() -> list[tuple[str, tuple[str, ...], dict]]:
    probes = []

    def walk(value: object, model_id: str, model_payload: dict, path: tuple[str, ...] = ()):
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = path + (key,)
                if "evidence" in key.lower() and isinstance(child, list) and child:
                    probes.append((model_id, child_path, _replace_path(model_payload, child_path, [])))
                elif (
                    "evidence" in key.lower()
                    and isinstance(child, dict)
                    and {"source_id", "origin", "citation"} <= child.keys()
                ):
                    payload = _replace_path(model_payload, child_path, None)
                    try:
                        _registry()._models[model_id].input_type.model_validate_json(
                            json.dumps(payload, allow_nan=False)
                        )
                    except ValidationError as error:
                        if any(
                            "evidence" in ".".join(map(str, item["loc"])).lower()
                            for item in error.errors()
                        ):
                            probes.append((model_id, child_path, payload))
                walk(child, model_id, model_payload, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, model_id, model_payload, path + (str(index),))

    def _replace_path(root: dict, path: tuple[str, ...], replacement: object) -> dict:
        result = json.loads(json.dumps(root))
        target = result
        for component in path[:-1]:
            target = target[int(component)] if component.isdigit() else target[component]
        target[path[-1]] = replacement
        return result

    for current_model, current_payload in _example_inputs().items():
        walk(current_payload, current_model, current_payload)

    # This model has no truthful full baseline: its public source lacks physical
    # specimen IDs and tensor histories. Still probe the required observation
    # Evidence field with an intentionally invalid, non-baseline input skeleton.
    sines_life_id = "fatigue.multiaxial_sines_life_fit"
    if sines_life_id in _uncovered_model_ids() and sines_life_id not in _example_inputs():
        partial = {
            "campaign_id": "input-contract-probe",
            "material_condition_id": "input-contract-probe",
            "fit_source_id": "finite_sines_parameter_loglog_ordinary_least_squares",
            "independent_specimen_identity_reviewed": True,
            "failure_endpoint_and_observation_rights_reviewed": True,
            "loglog_power_law_form_and_fit_domain_reviewed": True,
            "tests": [{
                "test_id": "input-contract-probe",
                "physical_specimen_id": "input-contract-probe",
                "source_group_id": "input-contract-probe",
                "source_record_id": "input-contract-probe",
                "cycles_to_failure": 1.0,
                "observation_evidence": {
                    "source_id": "input-contract-probe",
                    "origin": "synthetic",
                    "citation": "invalid contract-test placeholder; not experimental evidence",
                },
                "screen": {},
            }],
        }
        path = ("tests", "0", "observation_evidence")
        probes.append((sines_life_id, path, _replace_path(partial, path, [])))
    return probes


@pytest.mark.parametrize("model_id", _uncovered_model_ids())
def test_empty_json_is_rejected_when_model_has_required_input(model_id: str) -> None:
    spec = _registry()._models[model_id]
    input_type = spec.input_type
    required = [name for name, field in input_type.model_fields.items() if field.is_required()]
    assert required, f"{model_id} has no required fields; use a meaningful invalid-value case"

    with pytest.raises(ValidationError) as caught:
        input_type.model_validate_json("{}")

    errors = caught.value.errors()
    assert errors
    assert all(error["type"] == "missing" for error in errors), errors


@pytest.mark.parametrize("model_id,field_name,payload", _type_mutations())
def test_wrong_top_level_field_type_is_rejected(model_id: str, field_name: str, payload: dict) -> None:
    input_type = _registry()._models[model_id].input_type
    with pytest.raises(ValidationError, match=field_name):
        input_type.model_validate_json(json.dumps(payload, allow_nan=False))


@pytest.mark.parametrize("model_id,field_name,payload", _numeric_bound_mutations())
def test_declared_numeric_bound_violation_is_rejected(model_id: str, field_name: str, payload: dict) -> None:
    input_type = _registry()._models[model_id].input_type
    with pytest.raises(ValidationError, match=field_name):
        input_type.model_validate_json(json.dumps(payload, allow_nan=False))


@pytest.mark.parametrize("model_id,field_name", _required_null_probes())
def test_required_field_rejects_explicit_null(model_id: str, field_name: str) -> None:
    input_type = _registry()._models[model_id].input_type
    with pytest.raises(ValidationError) as caught:
        input_type.model_validate({field_name: None})
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize("model_id,field_name,invalid_value", _required_type_probes())
def test_required_field_rejects_wrong_json_type(
    model_id: str, field_name: str, invalid_value: object
) -> None:
    input_type = _registry()._models[model_id].input_type
    with pytest.raises(ValidationError) as caught:
        input_type.model_validate({field_name: invalid_value})
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize("contract_type,field_name,invalid_value", _schema_constraint_probes())
def test_declared_schema_constraint_rejects_invalid_field_value(
    contract_type: type[BaseModel], field_name: str, invalid_value: object
) -> None:
    input_type = contract_type
    with pytest.raises(ValidationError) as caught:
        input_type.model_validate_json(json.dumps({field_name: invalid_value}, allow_nan=False))
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize(
    "contract_type,field_name,invalid_value",
    _standalone_numeric_bound_probes(),
    ids=lambda v: v.__name__ if isinstance(v, type) else str(v),
)
def test_nested_standalone_numeric_bound_rejects_invalid_value(
    contract_type: type[BaseModel], field_name: str, invalid_value: object
) -> None:
    with pytest.raises(ValidationError) as caught:
        contract_type.model_validate({field_name: invalid_value})
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize("model_id,field_name,invalid_value", _baseline_physical_input_probes())
def test_physical_input_bound_rejects_nonphysical_scalar(
    model_id: str, field_name: str, invalid_value: object
) -> None:
    payload = dict(_example_inputs()[model_id])
    payload[field_name] = invalid_value
    input_type = _registry()._models[model_id].input_type
    with pytest.raises(ValidationError) as caught:
        input_type.model_validate_json(json.dumps(payload, allow_nan=False))
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize(
    "contract_type",
    [
        t
        for t in _contract_types()
        if t not in {_registry()._models[mid].input_type for mid in _uncovered_model_ids()}
    ],
    ids=lambda t: t.__name__,
)
def test_nested_contract_rejects_empty_input(contract_type: type[BaseModel]) -> None:
    with pytest.raises(ValidationError) as caught:
        contract_type.model_validate_json("{}")
    assert caught.value.errors()
    assert all(error["type"] == "missing" for error in caught.value.errors())


@pytest.mark.parametrize(
    "contract_type,field_name",
    _nested_required_fields(),
    ids=lambda v: v.__name__ if isinstance(v, type) else str(v),
)
def test_nested_required_field_rejects_null(contract_type: type[BaseModel], field_name: str) -> None:
    with pytest.raises(ValidationError) as caught:
        contract_type.model_validate({field_name: None})
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize(
    "contract_type,field_name,invalid_value",
    _nested_wrong_type_probes(),
    ids=lambda v: v.__name__ if isinstance(v, type) else str(v),
)
def test_nested_required_field_rejects_wrong_type(
    contract_type: type[BaseModel], field_name: str, invalid_value: object
) -> None:
    with pytest.raises(ValidationError) as caught:
        contract_type.model_validate({field_name: invalid_value})
    assert any(error["loc"][0] == field_name for error in caught.value.errors())


@pytest.mark.parametrize(
    "contract_type,field_name,invalid_value",
    _optional_scalar_type_probes(),
    ids=lambda value: value.__name__ if isinstance(value, type) else str(value),
)
def test_optional_scalar_field_rejects_wrong_json_type(
    contract_type: type[BaseModel], field_name: str, invalid_value: object
) -> None:
    with pytest.raises(ValidationError) as caught:
        TypeAdapter(contract_type.model_fields[field_name].annotation).validate_python(
            invalid_value, strict=True
        )
    assert caught.value.errors()


@pytest.mark.parametrize(
    "contract_type,field_name",
    _nested_required_evidence_fields(),
    ids=lambda v: v.__name__ if isinstance(v, type) else str(v),
)
def test_nested_required_evidence_collection_rejects_empty(
    contract_type: type[BaseModel], field_name: str
) -> None:
    with pytest.raises(ValidationError) as caught:
        contract_type.model_validate({field_name: []})
    assert caught.value.errors()


@pytest.mark.parametrize("model_id,path,payload", _evidence_removal_probes())
def test_required_evidence_payload_cannot_be_removed_or_null(
    model_id: str, path: tuple[str, ...], payload: dict
) -> None:
    input_type = _registry()._models[model_id].input_type
    with pytest.raises(ValidationError) as caught:
        input_type.model_validate_json(json.dumps(payload, allow_nan=False))
    assert any("evidence" in ".".join(map(str, error["loc"])).lower() for error in caught.value.errors()), (
        path
    )


def test_evidence_removal_manifest_matches_dynamic_fixture_probes() -> None:
    manifest_path = Path(__file__).parent / "data" / "core_physics_evidence_removal_probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))["cases"]

    def value_at(payload: dict, path: tuple[str, ...]) -> object:
        value: object = payload
        for component in path:
            value = value[int(component)] if component.isdigit() else value[component]
        return value

    actual = []
    for model_id, path, payload in _evidence_removal_probes():
        if model_id not in set(_uncovered_model_ids()):
            continue
        replacement = value_at(payload, path)
        actual.append((model_id, list(path), "null" if replacement is None else "empty_collection"))
    recorded = [(row["model_id"], row["path"], row["mutation"]) for row in manifest]
    assert recorded == actual


@pytest.mark.parametrize(
    "model_id,payload",
    sorted(_example_inputs().items()),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_registered_valid_baseline_is_accepted_by_its_model_contract(
    model_id: str, payload: dict
) -> None:
    if model_id not in set(_uncovered_model_ids()):
        pytest.skip("baseline is outside the audited 116-model input scope")
    model = _registry()._models[model_id].input_type.model_validate_json(json.dumps(payload, allow_nan=False))
    assert isinstance(model, BaseModel)
