import copy
import json

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    GoverningThicknessRecipe,
    ThicknessDimension,
    ThicknessExpression,
    governing_thickness_recipe,
)
from matintegrity.registry import default_registry


def raw_values():
    evidence = {"source_id": "authored", "origin": "synthetic", "citation": "authored dimensions"}
    return {
        "component_id": "component",
        "joint_geometry_id": "joint",
        "material_condition_id": "condition",
        "purpose_id": "authored-thickness-selection",
        "selected_geometry_case_id": "authored-case",
        "dimensions": [
            {
                "dimension_id": name,
                "value_m": value,
                "definition": name,
                "record_digest": "a" * 64,
                "evidence": [evidence],
            }
            for name, value in [("left", 0.02), ("right", 0.03), ("throat", 0.01)]
        ],
        "expressions": [
            {"expression_id": "joined", "operation": "maximum", "references": ["left", "right"]},
            {"expression_id": "control", "operation": "minimum", "references": ["joined", "throat"]},
        ],
        "output_reference_id": "control",
    }


def bind(values):
    normalized = values | {
        "dimensions": tuple(
            ThicknessDimension.model_validate_json(json.dumps(row)) for row in values["dimensions"]
        ),
        "expressions": tuple(
            ThicknessExpression.model_validate_json(json.dumps(row)) for row in values["expressions"]
        ),
    }
    serialized = GoverningThicknessRecipe.model_construct(**normalized).model_dump(
        mode="json", exclude={"basis"}
    )
    digest = canonical_digest(serialized)
    basis = {
        "source_id": "authored",
        "revision": "1",
        "license_id": "authored-test",
        "record_sha256": digest,
        "applicability_and_units_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [
            {
                "source_id": "authored",
                "origin": "synthetic",
                "citation": "authored geometry recipe",
                "license_id": "authored-test",
                "sha256": digest,
            }
        ],
    }
    return GoverningThicknessRecipe.model_validate_json(json.dumps(values | {"basis": basis}))


def test_nested_selection_and_control_trace():
    result = governing_thickness_recipe(bind(raw_values()))
    assert result.values["governing_thickness_m"] == 0.01
    assert result.values["expression_trace"][0]["selected_reference_ids"] == ["right"]
    assert result.values["expression_trace"][1]["selected_reference_ids"] == ["throat"]


def test_sum_and_tied_controlling_dimensions_are_preserved():
    values = raw_values()
    values["dimensions"][1]["value_m"] = 0.02
    values["expressions"][1].update(operation="sum", references=["joined", "throat", "throat"])
    result = governing_thickness_recipe(bind(values))
    assert result.values["governing_thickness_m"] == pytest.approx(0.04)
    assert result.values["expression_trace"][0]["selected_reference_ids"] == ["left", "right"]


@pytest.mark.parametrize("mutation", ["forward", "shadow", "duplicate", "missing_output"])
def test_invalid_dependency_graph_is_rejected(mutation):
    values = raw_values()
    if mutation == "forward":
        values["expressions"][0]["references"] = ["control"]
    elif mutation == "shadow":
        values["expressions"][0]["expression_id"] = "left"
    elif mutation == "duplicate":
        values["dimensions"].append(copy.deepcopy(values["dimensions"][0]))
    else:
        values["output_reference_id"] = "absent"
    with pytest.raises(ValueError):
        bind(values)


def test_single_dimension_case_and_sum_overflow():
    values = raw_values()
    values.update(expressions=[], output_reference_id="throat")
    assert governing_thickness_recipe(bind(values)).values["governing_thickness_m"] == 0.01
    values = raw_values()
    values["dimensions"][0]["value_m"] = 1e308
    values["expressions"][1].update(operation="sum", references=["left", "left"])
    assert governing_thickness_recipe(bind(values)).status == "out_of_scope"


def test_digest_pins_case_selection_and_dimension_values():
    value = bind(raw_values()).model_dump(mode="json")
    value["selected_geometry_case_id"] = "other"
    with pytest.raises(ValueError, match="pin the complete"):
        GoverningThicknessRecipe.model_validate_json(json.dumps(value))


def test_default_registry_python_json_exchange():
    registry = default_registry()
    value = bind(raw_values())
    context = RunContext(asset_id="asset", location_id="joint", time_basis="synthetic")
    direct = registry.run("fabrication.governing_thickness_recipe", value, context)
    assert (
        direct.model_dump()
        == registry.run_json(
            "fabrication.governing_thickness_recipe", value.model_dump_json(), context
        ).model_dump()
    )
    assert direct.status == "computed"
