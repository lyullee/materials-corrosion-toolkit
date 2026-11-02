import json

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    PipeBendWallAllowance,
    ThicknessRetentionFactor,
    ThicknessSoakDuration,
    pipe_bend_wall_allowance,
    thickness_soak_duration,
)
from matintegrity.registry import default_registry


def bind(contract, values):
    normalized = contract.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(normalized)
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
                "citation": "authored process recipe",
                "license_id": "authored-test",
                "sha256": digest,
            }
        ],
    }
    return contract.model_validate_json(json.dumps(normalized | {"basis": basis}))


def wall(**updates):
    return bind(
        PipeBendWallAllowance,
        {
            "component_id": "bend",
            "scenario_id": "authored-scenario",
            "nominal_wall_m": 0.01,
            "retention_factors": (
                ThicknessRetentionFactor(
                    factor_id="manufacturing",
                    retained_fraction=0.9,
                    interpretation="authored manufacturing allowance",
                ),
                ThicknessRetentionFactor(
                    factor_id="forming", retained_fraction=0.8, interpretation="authored forming allowance"
                ),
            ),
            "corrosion_allowance_m": 0.001,
            "required_pressure_wall_m": 0.005,
            "required_adjoining_wall_m": 0.006,
        }
        | updates,
    )


def soak(**updates):
    return bind(
        ThicknessSoakDuration,
        {
            "component_id": "bend",
            "procedure_id": "authored-procedure",
            "governing_thickness_m": 0.02,
            "proportional_soak_time_s_per_m": 100000.0,
            "minimum_soak_time_s": 2500.0,
        }
        | updates,
    )


def test_sequential_wall_retention_and_adjoining_requirement():
    result = pipe_bend_wall_allowance(wall())
    assert result.status == "computed"
    assert result.values["wall_after_retention_m"] == pytest.approx(0.0072)
    assert result.values["available_wall_after_allowance_m"] == pytest.approx(0.0062)
    assert result.values["required_wall_m"] == 0.006
    assert result.values["signed_wall_margin_m"] == pytest.approx(0.0002)


def test_negative_margin_is_not_clipped_or_relabelled_missing():
    result = pipe_bend_wall_allowance(wall(required_pressure_wall_m=0.008))
    assert result.status == "computed"
    assert result.values["signed_wall_margin_m"] == pytest.approx(-0.0018)


def test_exhausted_allowance_and_duplicate_retention_id():
    assert pipe_bend_wall_allowance(wall(corrosion_allowance_m=0.02)).status == "out_of_scope"
    factors = wall().retention_factors
    with pytest.raises(ValueError, match="unique"):
        wall(retention_factors=(factors[0], factors[0]))


@pytest.mark.parametrize(
    "thickness,required,controlling",
    [
        (0.01, 2500.0, ["minimum"]),
        (0.03, 3000.0, ["proportional"]),
        (0.025, 2500.0, ["proportional", "minimum"]),
    ],
)
def test_soak_floor_proportional_branch_and_tie(thickness, required, controlling):
    result = thickness_soak_duration(soak(governing_thickness_m=thickness))
    assert result.values["required_soak_time_s"] == pytest.approx(required)
    assert result.values["controlling_terms"] == controlling


@pytest.mark.parametrize(
    "updates",
    [
        {"governing_thickness_m": 1e308},
        {"governing_thickness_m": 1e-300, "proportional_soak_time_s_per_m": 1e-300},
    ],
)
def test_soak_numeric_range_is_explicit(updates):
    assert thickness_soak_duration(soak(**updates)).status == "out_of_scope"


@pytest.mark.parametrize(
    "model_id,factory",
    [("fabrication.pipe_bend_wall_allowance", wall), ("thermal.thickness_soak_duration", soak)],
)
def test_default_registry_python_json_exchange(model_id, factory):
    registry = default_registry()
    value = factory()
    context = RunContext(asset_id="asset", location_id="bend", time_basis="synthetic")
    direct = registry.run(model_id, value, context)
    assert direct.status == "computed"
    assert direct.model_dump() == registry.run_json(model_id, value.model_dump_json(), context).model_dump()
