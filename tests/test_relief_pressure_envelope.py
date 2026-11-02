import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    ReliefPressureEnvelope,
    relief_pressure_envelope,
    specifications,
)
from matintegrity.registry import ModelRegistry


def inputs(**changes):
    values = (
        dict(
            equipment_allowable_gauge_pressure_Pa=1000.0,
            device_set_gauge_pressure_Pa=1000.0,
            peak_equipment_gauge_pressure_Pa=1125.0,
            gauge_reference_id="declared-ambient",
            maximum_set_pressure_multiplier=1.0,
            fractional_accumulation_allowance=0.125,
            absolute_accumulation_allowance_Pa=150.0,
            allowance_combination="larger_of",
            scenario_id="synthetic",
        )
        | changes
    )
    digest = canonical_digest(values)
    return ReliefPressureEnvelope(
        **values,
        basis=dict(
            source_id="synthetic-rule",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="synthetic-rule",
                    origin="synthetic",
                    citation="Authored pressure-envelope test, not a code rule",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize("mode,expected", [("larger_of", 1150.0), ("smaller_of", 1125.0), ("sum", 1275.0)])
def test_declared_combination_and_equality_boundary(mode, expected):
    result = relief_pressure_envelope(inputs(allowance_combination=mode))
    assert result.values["maximum_peak_gauge_pressure_Pa"] == expected
    assert result.values["set_pressure_margin_Pa"] == 0.0
    assert result.values["declared_rule_outcome"] == "within_declared_limits"


def test_exceedances_and_separate_set_limit():
    result = relief_pressure_envelope(
        inputs(device_set_gauge_pressure_Pa=1020.0, peak_equipment_gauge_pressure_Pa=1200.0)
    )
    assert result.values["set_pressure_margin_Pa"] == -20.0
    assert result.values["peak_pressure_margin_Pa"] == -50.0
    assert result.values["declared_rule_outcome"] == "exceeds_declared_limits"


def test_rule_identity_rejects_parameter_tampering():
    payload = inputs().model_dump()
    payload["fractional_accumulation_allowance"] = 0.25
    with pytest.raises(ValueError, match="pin the complete"):
        ReliefPressureEnvelope.model_validate(payload)


def test_public_python_json_contract():
    registry = ModelRegistry()
    registry.register(next(s for s in specifications() if s.model_id == "design.relief_pressure_envelope"))
    context = RunContext(asset_id="synthetic", location_id="device", time_basis="test")
    direct = registry.run("design.relief_pressure_envelope", inputs(), context)
    serialized = registry.run_json("design.relief_pressure_envelope", inputs().model_dump_json(), context)
    assert direct.model_dump() == serialized.model_dump()
