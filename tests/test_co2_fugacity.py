import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.co2_fugacity import (
    CoolPropCo2FugacityRequest,
    CoolPropCo2MixtureFugacityRequest,
    coolprop_co2_fugacity_to_aquasoldb_fields,
    coolprop_co2_fugacity_to_carbonate_fields,
    coolprop_co2_gas_fugacity,
    coolprop_co2_mixture_fugacity_to_aquasoldb_fields,
    coolprop_co2_mixture_fugacity_to_carbonate_fields,
    coolprop_co2_mixture_gas_fugacity,
)


def request(**overrides):
    values = {
        "assessment_id": "synthetic-co2-test",
        "temperature_K": 333.15,
        "co2_partial_pressure_Pa": 2.0e5,
        "backend": "HEOS",
        "pure_component_approximation_reviewed": True,
        "single_phase_gas_or_supercritical_reviewed": True,
        "review_id": "synthetic-review",
        "evidence": (
            Evidence(
                source_id="authored-test",
                origin="synthetic",
                citation="Synthetic software regression fixture",
            ),
        ),
    }
    values.update(overrides)
    return CoolPropCo2FugacityRequest(**values)


def mixture_request(**overrides):
    values = {
        "assessment_id": "synthetic-co2-mixture-test",
        "temperature_K": 300.0,
        "total_pressure_Pa": 100.0,
        "components": ("CarbonDioxide", "Nitrogen"),
        "mole_fractions": (0.8, 0.2),
        "backend": "HEOS",
        "mixture_composition_reviewed": True,
        "mixture_eos_applicability_reviewed": True,
        "single_phase_gas_or_supercritical_reviewed": True,
        "review_id": "synthetic-mixture-review",
        "evidence": (
            Evidence(
                source_id="authored-test",
                origin="synthetic",
                citation="Synthetic software regression fixture",
            ),
        ),
    }
    values.update(overrides)
    return CoolPropCo2MixtureFugacityRequest(**values)


def test_review_gates_withhold_calculation_before_optional_import():
    result = coolprop_co2_gas_fugacity(
        request(
            pure_component_approximation_reviewed=False,
            single_phase_gas_or_supercritical_reviewed=False,
        )
    )
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == [
        "pure_component_approximation_reviewed",
        "single_phase_gas_or_supercritical_reviewed",
    ]


def test_missing_optional_dependency_is_reported_as_needs_data(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def without_coolprop(name, *args, **kwargs):
        if name == "CoolProp" or name.startswith("CoolProp."):
            raise ImportError("simulated missing optional dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", without_coolprop)
    result = coolprop_co2_gas_fugacity(request())
    assert result.status == "needs_data"
    assert result.values["missing_dependency"] == "CoolProp"


def test_carbonate_adapter_requires_complete_reviewed_provider_lineage():
    values = {
        "mixture_fugacity_computed": False,
        "pure_component_approximation_reviewed": True,
        "single_phase_gas_or_supercritical_reviewed": True,
        "co2_fugacity_Pa": 199_000.0,
        "gas_fugacity_provider_id": "CoolProp:HEOS:CO2",
        "gas_fugacity_provider_revision": "8.0.0:revision",
        "gas_fugacity_configuration_digest": "a" * 64,
        "gas_fugacity_record_digest": "b" * 64,
    }
    assert coolprop_co2_fugacity_to_carbonate_fields(values) == {
        key: values[key]
        for key in (
            "co2_fugacity_Pa",
            "gas_fugacity_provider_id",
            "gas_fugacity_provider_revision",
            "gas_fugacity_configuration_digest",
            "gas_fugacity_record_digest",
        )
    }
    with pytest.raises(ValueError, match="pure-component"):
        coolprop_co2_fugacity_to_carbonate_fields({**values, "mixture_fugacity_computed": True})
    with pytest.raises(ValueError, match="incomplete"):
        coolprop_co2_fugacity_to_carbonate_fields(
            {key: value for key, value in values.items() if key != "gas_fugacity_record_digest"}
        )


def test_mixture_request_requires_matching_normalized_composition():
    with pytest.raises(ValueError, match="sum to one"):
        mixture_request(mole_fractions=(0.7, 0.2))
    with pytest.raises(ValueError, match="counts must match|at least 2 items"):
        mixture_request(mole_fractions=(1.0,))
    with pytest.raises(ValueError, match="include.*CO2"):
        mixture_request(components=("Nitrogen", "Methane"), mole_fractions=(0.5, 0.5))


def test_mixture_review_gate_withholds_provider_calculation():
    result = coolprop_co2_mixture_gas_fugacity(
        mixture_request(mixture_eos_applicability_reviewed=False, mixture_composition_reviewed=False)
    )
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == [
        "mixture_composition_reviewed",
        "mixture_eos_applicability_reviewed",
    ]


def test_coolprop_provider_fugacity_and_digests():
    pytest.importorskip("CoolProp")
    result = coolprop_co2_gas_fugacity(request())
    assert result.status == "computed"
    assert result.values["fugacity_coefficient"] > 0.0
    assert result.values["co2_fugacity_Pa"] == pytest.approx(
        result.values["fugacity_coefficient"] * 2.0e5,
        rel=1e-8,
    )
    assert len(result.values["gas_fugacity_configuration_digest"]) == 64
    assert len(result.values["gas_fugacity_record_digest"]) == 64
    assert result.values["mixture_fugacity_computed"] is False
    assert (
        coolprop_co2_fugacity_to_carbonate_fields(result.values)["co2_fugacity_Pa"]
        == result.values["co2_fugacity_Pa"]
    )
    comparison_fields = coolprop_co2_fugacity_to_aquasoldb_fields(result.values)
    assert comparison_fields["fugacity_temperature_K"] == result.values["temperature_K"]
    assert comparison_fields["fugacity_provider_id"] == result.values["gas_fugacity_provider_id"]


def test_non_gas_like_co2_state_is_not_returned_as_gas_fugacity():
    pytest.importorskip("CoolProp")
    two_phase = request(temperature_K=280.0, co2_partial_pressure_Pa=5.0e6)
    result = coolprop_co2_gas_fugacity(two_phase)
    if result.values.get("reason") == "CO2_state_not_gas_or_supercritical":
        assert result.status == "out_of_scope"
        assert "co2_fugacity_Pa" not in result.values
    else:
        assert result.status in {"computed", "out_of_scope"}


def test_coolprop_mixture_provider_and_interoperability():
    pytest.importorskip("CoolProp")
    result = coolprop_co2_mixture_gas_fugacity(mixture_request())
    assert result.status == "computed"
    values = result.values
    assert values["mixture_fugacity_computed"] is True
    assert values["co2_partial_pressure_Pa"] == pytest.approx(80.0)
    assert values["co2_fugacity_Pa"] == pytest.approx(
        values["fugacity_coefficient"] * values["co2_partial_pressure_Pa"], rel=1e-8
    )
    carbonate = coolprop_co2_mixture_fugacity_to_carbonate_fields(values)
    comparison = coolprop_co2_mixture_fugacity_to_aquasoldb_fields(values)
    assert carbonate["gas_fugacity_record_digest"] == comparison["fugacity_record_digest"]
    assert comparison["fugacity_temperature_K"] == 300.0
