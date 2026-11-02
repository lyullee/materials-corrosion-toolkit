import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    ZenerHollomonParameter,
    zener_hollomon_parameter,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        material_condition_id="synthetic-condition",
        strain_rate_definition_id="declared-positive-equivalent-rate",
        activation_energy_basis_id="authored-Q",
        strain_rate_s_1=0.01,
        temperature_K=1000.0,
        activation_energy_J_mol=80000.0,
        gas_constant_J_mol_K=8.0,
    )
    raw.update(updates)
    digest = canonical_digest(raw)
    return ZenerHollomonParameter(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored arithmetic case.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_known_exponent_and_direct_value():
    result = zener_hollomon_parameter(request())
    assert result.status == "computed"
    assert result.values["temperature_compensation_exponent"] == 10.0
    assert result.values["ln_z_relative_to_1_s_1"] == pytest.approx(math.log(0.01) + 10.0)
    assert result.values["z_s_1"] == pytest.approx(0.01 * math.exp(10.0))


def test_zero_activation_retains_exact_supplied_rate():
    result = zener_hollomon_parameter(request(activation_energy_J_mol=0.0, strain_rate_s_1=5e-324))
    assert result.values["z_s_1"] == 5e-324


def test_unrepresentable_direct_value_keeps_logarithmic_descriptor():
    result = zener_hollomon_parameter(request(activation_energy_J_mol=8e6))
    assert result.status == "computed"
    assert result.values["z_s_1"] is None
    assert result.values["z_representable"] is False
    assert result.values["ln_z_relative_to_1_s_1"] == pytest.approx(math.log(0.01) + 1000.0)


def test_large_gas_constant_temperature_product_does_not_erase_compensation():
    result = zener_hollomon_parameter(
        request(
            activation_energy_J_mol=1e308,
            gas_constant_J_mol_K=1e308,
            temperature_K=100.0,
        )
    )
    assert result.values["temperature_compensation_exponent"] == pytest.approx(0.01)


@pytest.mark.parametrize(
    "updates",
    [
        dict(activation_energy_J_mol=1e308, gas_constant_J_mol_K=1e-300, temperature_K=1e-100),
        dict(activation_energy_J_mol=5e-324, gas_constant_J_mol_K=1e308, temperature_K=1e308),
    ],
)
def test_unrepresentable_activation_is_out_of_scope(updates):
    assert zener_hollomon_parameter(request(**updates)).status == "out_of_scope"


@pytest.mark.parametrize(
    "updates",
    [
        dict(strain_rate_s_1=0.0),
        dict(temperature_K=0.0),
        dict(activation_energy_J_mol=-1.0),
    ],
)
def test_invalid_physical_inputs(updates):
    with pytest.raises(ValueError):
        request(**updates)


def test_changed_parameter_breaks_digest():
    raw = request().model_dump()
    raw["activation_energy_J_mol"] = 1.0
    with pytest.raises(ValueError, match="pin the complete"):
        ZenerHollomonParameter.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="test", time_basis="instant")
    a = registry.run("creep.zener_hollomon_parameter", x, context)
    b = registry.run_json("creep.zener_hollomon_parameter", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
