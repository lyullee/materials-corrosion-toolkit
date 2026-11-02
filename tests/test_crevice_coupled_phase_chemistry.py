import pytest

from matintegrity.crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from matintegrity.crevice_component_state_bdf import CellAqueousEquilibriumTemplate
from matintegrity.crevice_coupled_phase_chemistry import (
    CoupledPhaseDaviesChemistry,
    build_coupled_davies_phase_rhs,
)
from matintegrity.crevice_coupled_phase_state import CoupledPhaseStateLayout
from matintegrity.crevice_nucleation_kinetic_history import CreviceMolarNucleationLaw
from matintegrity.multiphase_kinetic_ledger import SolidSaturationRateLaw


def template():
    evidence = (
        {"source_id": "authored", "origin": "synthetic", "citation": "Authored dilute aqueous fixture"},
    )
    system = dict(
        assessment_id="trial",
        solution_id="cell",
        temperature_K=298.15,
        activity_standard_state="molarity_1_mol_L",
        species=tuple(
            dict(species_id=name, charge_number=charge, activity_coefficient=1.0, initial_activity=guess)
            for name, charge, guess in [("H", 1, 1e-11), ("OH", -1, 1e-3), ("Na", 1, 1e-3)]
        ),
        reactions=(
            dict(
                reaction_id="water",
                log10_equilibrium_constant=-14.0,
                terms=({"species_id": "H", "coefficient": 1.0}, {"species_id": "OH", "coefficient": 1.0}),
            ),
        ),
        constraints=(
            dict(
                constraint_id="sodium",
                target_mol_L=0.001,
                residual_scale_mol_L=0.001,
                terms=({"species_id": "Na", "coefficient": 1.0},),
            ),
            dict(
                constraint_id="charge",
                target_mol_L=0.0,
                residual_scale_mol_L=0.001,
                terms=(
                    {"species_id": "H", "coefficient": 1.0},
                    {"species_id": "Na", "coefficient": 1.0},
                    {"species_id": "OH", "coefficient": -1.0},
                ),
            ),
        ),
        evidence=evidence,
    )
    for prefix in ("activity", "equilibrium"):
        system.update(
            {
                f"{prefix}_provider_id": "authored",
                f"{prefix}_provider_revision": "1",
                f"{prefix}_configuration_digest": "a" * 64,
                f"{prefix}_record_digest": "a" * 64,
            }
        )
    for flag in (
        "complete_aqueous_species_inventory_reviewed",
        "reaction_stoichiometry_and_constant_reviewed",
        "balance_constraints_and_charge_scope_reviewed",
        "fixed_activity_coefficients_and_standard_state_reviewed",
        "temperature_and_provider_lineage_reviewed",
        "initial_activity_guess_and_solver_tolerance_reviewed",
        "single_liquid_phase_and_no_precipitation_reviewed",
    ):
        system[flag] = True
    activity = dict(
        system=system,
        water_mass_per_solution_volume_kg_L=1.0,
        davies_A_at_temperature=0.509,
        davies_A_provider_id="authored",
        davies_A_provider_revision="1",
        davies_A_configuration_digest="a" * 64,
        davies_A_record_digest="a" * 64,
        ionic_strength_limit_mol_kg=0.5,
        charge_balance_tolerance_mol_kg=1e-9,
        evidence=evidence,
    )
    for flag in (
        "water_mass_conversion_reviewed",
        "Davies_A_temperature_solvent_basis_reviewed",
        "molarity_to_molality_standard_state_mapping_reviewed",
        "complete_inventory_and_charge_scope_reviewed",
        "fixed_point_solver_settings_reviewed",
        "single_liquid_no_precipitation_scope_reviewed",
    ):
        activity[flag] = True
    return CellAqueousEquilibriumTemplate(
        cell_id="cell",
        solution_volume_L=1.0,
        aqueous_activity_request=activity,
        constraint_roles=(
            {"constraint_id": "sodium", "role": "conserved_component", "component_id": "Na"},
            {"constraint_id": "charge", "role": "charge_neutrality"},
        ),
        conserved_components=(
            {"component_id": "Na", "species_coefficients": ({"species_id": "Na", "coefficient": 1.0},)},
        ),
    )


def test_actual_davies_trial_updates_and_transport_callback():
    cell = template()
    layout = CoupledPhaseStateLayout(("Na",), ("solid",), ("cell",), ((1.0,),))
    seen = []

    def transport(time, rows):
        seen.append((time, rows))
        return ((0.0,),)

    adapter = CoupledPhaseDaviesChemistry(
        layout, (cell,), transport, maximum_equilibrium_calls=2, maximum_nested_iteration_work=100000
    )
    first = adapter(0.0, ((0.001,),))
    second = adapter(0.1, ((0.002,),))
    assert seen[0][1][0][2]["concentration_mol_L"] == pytest.approx(0.001, rel=1e-7)
    assert seen[1][1][0][2]["concentration_mol_L"] == pytest.approx(0.002, rel=1e-7)
    assert second.dimensionless_activity_by_cell[0]["Na"] > first.dimensionless_activity_by_cell[0]["Na"]
    assert cell.aqueous_activity_request.system.constraints[0].target_mol_L == 0.001
    assert len(adapter.lineage_sha256) == 64
    with pytest.raises(RuntimeError, match="budget"):
        adapter(0.2, ((0.001,),))


def test_cell_identity_and_insufficient_work_fail_before_transport():
    cell = template()
    layout = CoupledPhaseStateLayout(("Na",), ("solid",), ("cell",), ((1.0,),))
    adapter = CoupledPhaseDaviesChemistry(
        layout,
        (cell,),
        lambda *_: pytest.fail("transport invoked"),
        maximum_equilibrium_calls=2,
        maximum_nested_iteration_work=1,
    )
    with pytest.raises(RuntimeError, match="budget"):
        adapter(0.0, ((0.001,),))
    with pytest.raises(ValueError, match="identities"):
        CoupledPhaseDaviesChemistry(
            layout,
            (cell.model_copy(update={"cell_id": "other"}),),
            lambda *_: (),
            maximum_equilibrium_calls=1,
            maximum_nested_iteration_work=1,
        )


def bound_rhs(map_coefficient=1.0, phase_changes=None):
    cell = template()
    request = cell.aqueous_activity_request
    formulas = {"H": {"H": 1}, "OH": {"O": 1, "H": 1}, "Na": {"Na": 1}}
    species = tuple(
        row.model_copy(update={"elemental_composition": formulas[row.species_id]})
        for row in request.system.species
    )
    raw = cell.model_dump()
    system = raw["aqueous_activity_request"]["system"]
    system["species"] = tuple(row.model_dump() for row in species) + (
        dict(
            species_id="water",
            charge_number=0,
            activity_coefficient=1.0,
            initial_activity=1.0,
            elemental_composition={"H": 2, "O": 1},
        ),
    )
    reaction = system["reactions"][0]
    reaction["terms"] = reaction["terms"] + ({"species_id": "water", "coefficient": -1.0},)
    system["constraints"] = system["constraints"] + (
        dict(
            constraint_id="solvent",
            target_mol_L=1.0,
            residual_scale_mol_L=1.0,
            terms=({"species_id": "water", "coefficient": 1.0},),
        ),
    )
    system["elemental_formula_and_reaction_balance_reviewed"] = True
    raw["constraint_roles"] = raw["constraint_roles"] + (
        {"constraint_id": "solvent", "role": "fixed_target"},
    )
    cell = CellAqueousEquilibriumTemplate.model_validate(raw)
    phase = CreviceCompetingSolidPhase.model_construct(
        solid_species_id="solid",
        solid_elemental_composition={"Na": 1, "O": 1, "H": 1},
        aqueous_reactant_stoichiometry={"Na": 1.0, "OH": 1.0},
        dimensionless_solubility_product=0.01,
    )
    if phase_changes:
        phase = phase.model_copy(update=phase_changes)
    n = CreviceMolarNucleationLaw.model_construct(
        solid_species_id="solid",
        critical_saturation_ratio=2.0,
        source_rate_constant_mol_m3_s=1.0,
        supersaturation_order=1.0,
        nucleated_inventory_threshold_mol_m3=0.1,
        maximum_rate_mol_m3_s=100.0,
    )
    g = SolidSaturationRateLaw(
        solid_species_id="solid",
        precipitation_rate_constant_mol_m3_s=1.0,
        precipitation_order=1.0,
        dissolution_rate_constant_mol_m3_s=1.0,
        dissolution_order=1.0,
        source_sha256="a" * 64,
    )
    layout = CoupledPhaseStateLayout(("Na",), ("solid",), ("cell",), ((map_coefficient,),))
    rhs = build_coupled_davies_phase_rhs(
        layout,
        (cell,),
        ((phase,),),
        ((n,),),
        ((g,),),
        lambda *_: ((0.0,),),
        maximum_evaluations=5,
        maximum_equilibrium_calls=5,
        maximum_nested_iteration_work=100000,
    )
    return layout, rhs


def test_reaction_checked_binding_uses_template_volume_and_temperature():
    layout, rhs = bound_rhs()
    assert rhs.volumes == (0.001,)
    assert rhs.temperatures == (298.15,)
    derivative = rhs(0.0, layout.pack_initial(((0.001,),), ((1e-5,),)))
    assert derivative[0] == 0.0
    assert derivative[1] < 0.0


@pytest.mark.parametrize(
    "coefficient,changes,message",
    [
        (2.0, None, "component-phase map"),
        (1.0, {"aqueous_reactant_stoichiometry": {"Na": 1.0}}, "charge"),
        (1.0, {"solid_elemental_composition": {"Na": 2, "O": 1, "H": 1}}, "element"),
    ],
)
def test_inconsistent_reaction_binding_is_rejected(coefficient, changes, message):
    with pytest.raises(ValueError, match=message):
        bound_rhs(coefficient, changes)
