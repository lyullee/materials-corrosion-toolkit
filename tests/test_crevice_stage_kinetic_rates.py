import pytest

from matintegrity.contracts import canonical_digest
from matintegrity.crevice_nucleation_kinetic_history import CreviceMolarNucleationLaw
from matintegrity.crevice_stage_kinetic_rates import trial_phase_rate_mol_s
from matintegrity.multiphase_kinetic_ledger import SolidSaturationRateLaw


def laws():
    raw = dict(
        solid_species_id="solid",
        critical_saturation_ratio=2.0,
        source_rate_constant_mol_m3_s=4.0,
        supersaturation_order=1.0,
        nucleated_inventory_threshold_mol_m3=0.1,
        maximum_rate_mol_m3_s=100.0,
    )
    digest = canonical_digest(raw)
    n = CreviceMolarNucleationLaw(
        **raw,
        source_sha256=digest,
        evidence=(
            dict(
                source_id="authored",
                origin="synthetic",
                citation="Authored kinetic case",
                license_id="authored-test",
                sha256=digest,
            ),
        ),
    )
    g = SolidSaturationRateLaw(
        solid_species_id="solid",
        precipitation_rate_constant_mol_m3_s=3.0,
        precipitation_order=1.0,
        dissolution_rate_constant_mol_m3_s=2.0,
        dissolution_order=1.0,
        source_sha256="a" * 64,
    )
    return n, g


@pytest.mark.parametrize(
    "solid,saturation,expected,mode",
    [
        (0.0, 4.0, 8.0, "nucleation_source"),
        (0.0, 1.5, 0.0, "nucleation_source"),
        (0.2, 4.0, 18.0, "seeded_growth"),
        (0.1, 0.5, -2.0, "dissolution"),
        (0.0, 0.5, 0.0, "no_solid_to_dissolve"),
    ],
)
def test_trial_branches(solid, saturation, expected, mode):
    n, g = laws()
    rate, state = trial_phase_rate_mol_s(
        solid_inventory_mol=solid,
        solution_volume_m3=2.0,
        saturation_ratio=saturation,
        temperature_K=300.0,
        nucleation_law=n,
        growth_law=g,
    )
    assert rate == expected
    assert state == mode


def test_bound_and_phase_identity():
    n, g = laws()
    raw = dict(
        solid_inventory_mol=0.0,
        solution_volume_m3=1.0,
        saturation_ratio=100.0,
        temperature_K=300.0,
        nucleation_law=n,
        growth_law=g,
    )
    with pytest.raises(ArithmeticError, match="bound"):
        trial_phase_rate_mol_s(**raw)
    raw["growth_law"] = g.model_copy(update={"solid_species_id": "other"})
    with pytest.raises(ValueError, match="identities"):
        trial_phase_rate_mol_s(**raw)
