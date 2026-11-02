import math
from fractions import Fraction

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.materials import (
    DissolutionCharge,
    DuctilityComparison,
    TensilePoint,
    dissolution_charge,
    ductility_comparison,
    tensile_point,
)
from matintegrity.registry import default_registry


def test_charge_product_overflow_does_not_destroy_finite_outputs():
    request = DissolutionCharge(
        anodic_charge_C=1e308,
        equivalent_weight_kg_mol_electron=1e5,
        current_efficiency=1e-5,
        density_kg_m3=1e308,
    )
    result = dissolution_charge(request)
    assert result.status == "computed"
    mass = Fraction(1e308) * Fraction(1e5) * Fraction(1e-5) / Fraction(96485.33212331001)
    assert result.values["dissolved_mass_kg"] == float(mass)
    assert result.values["dissolved_volume_m3"] == float(mass / Fraction(1e308))


@pytest.mark.parametrize(
    "charge,equivalent,density", [(1e308, 1e308, 1.0), (1e-300, 1e-100, 1.0), (1.0, 1.0, 1e-320)]
)
def test_charge_unsupported_required_output_withholds_all(charge, equivalent, density):
    result = dissolution_charge(
        DissolutionCharge(
            anodic_charge_C=charge,
            equivalent_weight_kg_mol_electron=equivalent,
            current_efficiency=1,
            density_kg_m3=density,
        )
    )
    assert result.status == "out_of_scope"
    assert not result.values


@pytest.mark.parametrize("uniform", [True, False])
def test_tensile_explicit_zero_and_uniform_gate(uniform):
    result = tensile_point(
        TensilePoint(
            force_N=0,
            initial_area_m2=1,
            extension_m=0,
            gauge_length_m=1,
            uniform_deformation_declared=uniform,
        )
    )
    assert result.status == "computed"
    assert result.values["engineering_stress_Pa"] == 0
    assert ("true_stress_Pa" in result.values) == uniform


@pytest.mark.parametrize(
    "force,area,extension,length",
    [(1e308, 1e-308, 0, 1), (1e-308, 1e308, 0, 1), (1, 1, 1e308, 1e-308), (1, 1, 1e-308, 1e308)],
)
def test_tensile_unsupported_ratio_withholds_all(force, area, extension, length):
    result = tensile_point(
        TensilePoint(
            force_N=force,
            initial_area_m2=area,
            extension_m=extension,
            gauge_length_m=length,
            uniform_deformation_declared=True,
        )
    )
    assert result.status == "out_of_scope"
    assert not result.values


def test_ductility_signed_loss_matches_exact_inputs():
    baseline, exposed = 3.0, math.nextafter(3.0, math.inf)
    result = ductility_comparison(
        DuctilityComparison(baseline_elongation_fraction=baseline, exposed_elongation_fraction=exposed)
    )
    ratio = Fraction(exposed) / Fraction(baseline)
    assert result.values["relative_ductility_loss"] == float(1 - ratio)
    assert result.values["relative_ductility_loss"] < 0


@pytest.mark.parametrize("baseline,exposed", [(1e-308, 1e308), (1e308, 1e-308)])
def test_ductility_unsupported_ratio_withholds_all(baseline, exposed):
    result = ductility_comparison(
        DuctilityComparison(baseline_elongation_fraction=baseline, exposed_elongation_fraction=exposed)
    )
    assert result.status == "out_of_scope"
    assert not result.values


@pytest.mark.parametrize("model,inputs", [
    ("materials.tensile_point", TensilePoint(force_N=10, initial_area_m2=2,
        extension_m=0.1, gauge_length_m=1, uniform_deformation_declared=True)),
    ("materials.ductility_retention", DuctilityComparison(baseline_elongation_fraction=0.2,
        exposed_elongation_fraction=0.1)),
    ("corrosion.charge_to_loss", DissolutionCharge(anodic_charge_C=1e308,
        equivalent_weight_kg_mol_electron=1e5, current_efficiency=1e-5, density_kg_m3=1e308)),
])
def test_registry_exchange_preserves_repaired_values_and_version(model, inputs):
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="fixture", time_basis="synthetic")
    direct = registry.run(model, inputs.model_dump(), context)
    encoded = registry.run_json(model, inputs.model_dump_json(), context)
    assert direct.model_version == encoded.model_version == "1.0.1"
    assert direct.values == encoded.values
