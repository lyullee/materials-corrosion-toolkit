import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.fatigue import (
    NeuberNotchStrainAmplitude,
    neuber_notch_strain_amplitude,
)
from matintegrity.registry import default_registry


def test_neuber_solution_satisfies_local_compatibility():
    result = neuber_notch_strain_amplitude(
        NeuberNotchStrainAmplitude(
            nominal_stress_amplitude_Pa=100e6,
            elastic_stress_concentration_factor=2.0,
            elastic_modulus_Pa=200e9,
            cyclic_strength_coefficient_Pa=1e9,
            cyclic_strain_hardening_exponent=0.2,
            all_inputs_reviewed=True,
        )
    )
    assert result.status == "computed"
    assert result.values["converged"] is True
    assert result.values["relative_neuber_residual"] <= 1e-11
    assert result.values["local_strain_amplitude"] == pytest.approx(
        result.values["elastic_strain_amplitude"] + result.values["plastic_strain_amplitude"]
    )


def test_linear_cyclic_limit_approaches_elastic_concentration():
    result = neuber_notch_strain_amplitude(
        NeuberNotchStrainAmplitude(
            nominal_stress_amplitude_Pa=1e6,
            elastic_stress_concentration_factor=2.0,
            elastic_modulus_Pa=200e9,
            cyclic_strength_coefficient_Pa=1e20,
            cyclic_strain_hardening_exponent=1.0,
            all_inputs_reviewed=True,
        )
    )
    assert result.values["local_stress_amplitude_Pa"] == pytest.approx(2e6, rel=1e-8)


def test_unreviewed_notch_inputs_require_review():
    result = neuber_notch_strain_amplitude(
        NeuberNotchStrainAmplitude(
            nominal_stress_amplitude_Pa=100e6,
            elastic_stress_concentration_factor=2.0,
            elastic_modulus_Pa=200e9,
            cyclic_strength_coefficient_Pa=1e9,
            cyclic_strain_hardening_exponent=0.2,
            all_inputs_reviewed=False,
        )
    )
    assert result.status == "needs_data"


def test_nonconverged_solution_is_not_a_usable_computed_result():
    result = neuber_notch_strain_amplitude(
        NeuberNotchStrainAmplitude(
            nominal_stress_amplitude_Pa=100e6,
            elastic_stress_concentration_factor=2.0,
            elastic_modulus_Pa=200e9,
            cyclic_strength_coefficient_Pa=1e9,
            cyclic_strain_hardening_exponent=0.2,
            all_inputs_reviewed=True,
            max_iterations=10,
        )
    )
    assert result.status == "out_of_scope"
    assert result.values["converged"] is False


def test_registered_chain_uses_notch_strain_as_strain_life_input():
    inputs = {
        "notch": {
            "nominal_stress_amplitude_Pa": 100e6,
            "elastic_stress_concentration_factor": 2.0,
            "elastic_modulus_Pa": 200e9,
            "cyclic_strength_coefficient_Pa": 1e9,
            "cyclic_strain_hardening_exponent": 0.2,
            "all_inputs_reviewed": True,
        },
        "fatigue_strength_coefficient_Pa": 1e9,
        "fatigue_strength_exponent": -0.1,
        "fatigue_ductility_coefficient": 0.5,
        "fatigue_ductility_exponent": -0.5,
        "minimum_valid_cycles": 1.0,
        "maximum_valid_cycles": 1e9,
    }
    result = default_registry().run(
        "fatigue.neuber_strain_life_chain",
        inputs,
        RunContext(asset_id="synthetic", location_id="notch", time_basis="constant-amplitude cycle"),
    )
    assert result.status == "computed"
    assert result.values["neuber_converged"] is True
    assert result.values["cycles_to_failure"] > 0
    assert result.values["strain_life_status"] == "computed"
    direct = default_registry().run(
        "fatigue.strain_life",
        {
            "strain_amplitude": result.values["local_strain_amplitude"],
            "elastic_modulus_Pa": 200e9,
            "fatigue_strength_coefficient_Pa": 1e9,
            "fatigue_strength_exponent": -0.1,
            "fatigue_ductility_coefficient": 0.5,
            "fatigue_ductility_exponent": -0.5,
            "minimum_valid_cycles": 1.0,
            "maximum_valid_cycles": 1e9,
        },
        RunContext(asset_id="synthetic", location_id="notch", time_basis="constant-amplitude cycle"),
    )
    assert result.values["cycles_to_failure"] == pytest.approx(direct.values["cycles_to_failure"])


def test_chain_stops_before_life_when_notch_inputs_are_unreviewed():
    import json
    from copy import deepcopy

    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "fatigue.neuber_strain_life_chain"
    ]
    inputs = deepcopy(inputs)
    inputs["notch"]["all_inputs_reviewed"] = False
    result = default_registry().run(
        "fatigue.neuber_strain_life_chain",
        inputs,
        RunContext(asset_id="synthetic", location_id="notch", time_basis="constant-amplitude cycle"),
    )
    assert result.status == "needs_data"
    assert result.values["strain_life_status"] == "not_evaluated"
    assert result.values["cycles_to_failure"] is None


def test_chain_preserves_notch_result_when_life_is_outside_calibration_interval():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "fatigue.neuber_strain_life_chain"
    ]
    inputs["minimum_valid_cycles"] = 1e10
    inputs["maximum_valid_cycles"] = 1e11
    result = default_registry().run(
        "fatigue.neuber_strain_life_chain",
        inputs,
        RunContext(asset_id="synthetic", location_id="notch", time_basis="constant-amplitude cycle"),
    )
    assert result.status == "out_of_scope"
    assert result.values["neuber_status"] == "computed"
    assert result.values["local_strain_amplitude"] > 0
    assert result.values["cycles_to_failure"] is None
