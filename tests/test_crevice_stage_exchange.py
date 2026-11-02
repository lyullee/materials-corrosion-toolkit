import pytest

from matintegrity.crevice_aqueous_component_ledger import (
    ComponentSpeciesCoefficient,
    ConservedAqueousComponent,
)
from matintegrity.crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from matintegrity.crevice_stage_kinetic_rates import phase_component_exchange_mol_s, trial_saturation_ratio


def phase(name="salt", stoich=None, ksp=0.01):
    # Kernel fixture only; public phase evidence validation is not bypassed by a solver.
    return CreviceCompetingSolidPhase.model_construct(
        solid_species_id=name,
        aqueous_reactant_stoichiometry=stoich or {"cation": 1.0, "anion": 1.0},
        dimensionless_solubility_product=ksp,
    )


def components():
    return tuple(
        ConservedAqueousComponent(
            component_id=name,
            species_coefficients=(ComponentSpeciesCoefficient(species_id=name, coefficient=1.0),),
        )
        for name in ("cation", "anion")
    )


def test_saturation_uses_explicit_dimensionless_activity():
    assert trial_saturation_ratio(phase(), {"cation": 0.2, "anion": 0.2}) == pytest.approx(4.0)
    assert trial_saturation_ratio(phase(), {"cation": 0.0, "anion": 0.2}) == 0.0
    with pytest.raises(KeyError):
        trial_saturation_ratio(phase(), {"cation": 0.2})
    with pytest.raises(ValueError):
        trial_saturation_ratio(phase(), {"cation": 0.0, "anion": float("nan")})


@pytest.mark.parametrize("rate", [2.0, -2.0, 0.0])
def test_equal_opposite_component_exchange(rate):
    dissolved, solids = phase_component_exchange_mol_s(
        (phase(),), components(), {"salt": rate}, {"cation": 1, "anion": -1}
    )
    for key in dissolved:
        assert dissolved[key] == -rate
        assert solids["salt"][key] == rate


def test_competing_phase_cancellation_and_identity():
    phases = (phase("a"), phase("b"))
    dissolved, solids = phase_component_exchange_mol_s(
        phases, components(), {"a": 1e308, "b": -1e308}, {"cation": 1, "anion": -1}
    )
    assert dissolved == {"cation": 0.0, "anion": 0.0}
    assert solids["a"]["cation"] == 1e308
    with pytest.raises(ValueError, match="exactly"):
        phase_component_exchange_mol_s(phases, components(), {"a": 1.0}, {"cation": 1, "anion": -1})


def test_charge_nonconservation_rejected():
    with pytest.raises(ValueError, match="charge"):
        phase_component_exchange_mol_s(
            (phase(stoich={"cation": 2.0, "anion": 1.0}),),
            components(),
            {"salt": 1.0},
            {"cation": 1, "anion": -1},
        )


def test_unrepresentable_positive_saturation_not_zero():
    with pytest.raises(ArithmeticError, match="representable"):
        trial_saturation_ratio(phase(ksp=1e300), {"cation": 1e-300, "anion": 1e-300})
