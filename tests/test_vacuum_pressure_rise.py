import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.vacuum_pressure_rise import (
    KnownVolumePressureRiseTest,
    known_volume_pressure_rise,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    def run(identifier, role, slope, group):
        times = [0.0, 10.0, 20.0, 30.0]
        return {
            "run_id": identifier,
            "role": role,
            "source_group_id": group,
            "clock_id": "clock-1",
            "elapsed_time_s": times,
            "absolute_pressure_Pa": [100.0 + slope * value for value in times],
            "pressure_standard_uncertainty_Pa": [1.0] * 4,
            "temperature_K": [300.0] * 4,
            "fit_window_start_s": 0.0,
            "fit_window_end_s": 30.0,
            "apparatus_state_digest": D,
            "run_data_digest": D,
            "provider_id": "provider-1",
            "provider_revision": "1",
            "record_valid": True,
            "evidence": [E],
        }

    value = {
        "assessment_id": "vacuum-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "apparatus_id": "apparatus-1",
        "rigid_volume_m3": 0.5,
        "pressure_basis": "absolute",
        "runs": [run("blank-1", "blank", 1.0, "source-blank"), run("test-1", "test", 3.0, "source-test")],
        "maximum_temperature_range_K": 1.0,
        "apparatus_volume_and_isolation_reviewed": True,
        "absolute_pressure_temperature_and_clock_reviewed": True,
        "blank_test_independence_reviewed": True,
        "fit_windows_weights_and_uncertainty_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "reference_comparison_reviewed": True,
        "evidence": [E],
    }
    value.update(updates)
    return KnownVolumePressureRiseTest.model_validate_json(json.dumps(value))


def test_blank_corrected_weighted_slopes():
    result = known_volume_pressure_rise(payload())
    assert result.status == "computed"
    assert result.values["blank_pressure_slope_Pa_s"] == pytest.approx(1.0)
    assert result.values["test_pressure_slope_Pa_s"] == pytest.approx(3.0)
    assert result.values["net_gas_throughput_Pa_m3_s"] == pytest.approx(1.0)


def test_molar_conversion_requires_reviewed_state():
    assert (
        known_volume_pressure_rise(
            payload(molar_conversion_requested=True, reference_temperature_K=300.0)
        ).status
        == "needs_data"
    )
    result = known_volume_pressure_rise(
        payload(
            molar_conversion_requested=True,
            molar_conversion_state_reviewed=True,
            reference_temperature_K=300.0,
        )
    )
    assert result.values["net_molar_flow_mol_s"] > 0


def test_temperature_outside_scope_and_clock_strict():
    base = payload()
    hot = base.runs[1].model_copy(update={"temperature_K": (300.0, 300.0, 303.0, 303.0)})
    assert (
        known_volume_pressure_rise(base.model_copy(update={"runs": (base.runs[0], hot)})).status
        == "out_of_scope"
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        base.runs[0].model_copy(update={"elapsed_time_s": (0.0, 10.0, 10.0, 30.0)}).model_validate(
            base.runs[0].model_copy(update={"elapsed_time_s": (0.0, 10.0, 10.0, 30.0)}).model_dump()
        )


def test_independence_and_context_are_strict():
    base = payload()
    duplicate = base.runs[1].model_copy(update={"source_group_id": "source-blank"})
    with pytest.raises(ValueError, match="independent source groups"):
        KnownVolumePressureRiseTest(**base.model_dump(exclude={"runs"}), runs=(base.runs[0], duplicate))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.known_volume_pressure_rise",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="clock-1"),
        )
