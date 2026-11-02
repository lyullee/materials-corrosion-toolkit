import math

import pytest

from matintegrity.crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from matintegrity.crevice_coupled_phase_rhs import CoupledPhaseRHS, CoupledPhaseTrialChemistry
from matintegrity.crevice_coupled_phase_state import CoupledPhaseStateLayout
from matintegrity.crevice_coupled_seed_bdf import integrate_coupled_seed_bdf
from matintegrity.crevice_nucleation_kinetic_history import CreviceMolarNucleationLaw
from matintegrity.multiphase_kinetic_ledger import SolidSaturationRateLaw


def evaluator(budget=1000):
    layout = CoupledPhaseStateLayout(("M",), ("solid",), ("cell",), ((1.0,),))
    # Authored internal-kernel fixtures, not public evidence-bearing requests.
    phase = CreviceCompetingSolidPhase.model_construct(
        solid_species_id="solid",
        aqueous_reactant_stoichiometry={"M": 1.0},
        dimensionless_solubility_product=1.0,
    )
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
        precipitation_rate_constant_mol_m3_s=3.0,
        precipitation_order=1.0,
        dissolution_rate_constant_mol_m3_s=3.0,
        dissolution_order=1.0,
        source_sha256="a" * 64,
    )
    seen = []

    def chemistry(time, dissolved):
        seen.append((time, dissolved))
        return CoupledPhaseTrialChemistry(({"M": dissolved[0][0]},), ((0.0,),))

    rhs = CoupledPhaseRHS(
        layout, ((phase,),), ((n,),), ((g,),), (1.0,), (300.0,), chemistry, maximum_evaluations=budget
    )
    return layout, rhs, seen


def test_chemistry_receives_each_trial_not_previous_stage():
    layout, rhs, seen = evaluator()
    assert rhs(0.0, layout.pack_initial(((3.0,),), ((1.0,),))) == pytest.approx((0.0, 6.0), rel=1e-14)
    assert rhs(0.0, (4.0, 2.0)) == pytest.approx((0.0, 3.0), rel=1e-14)
    assert seen == [(0.0, ((3.0,),)), (0.0, ((2.0,),))]


def test_bdf_internal_stage_feedback_matches_closed_form():
    scipy = pytest.importorskip("scipy.integrate")
    layout, rhs, _ = evaluator()
    result = scipy.solve_ivp(
        rhs,
        (0.0, 1.0),
        layout.pack_initial(((3.0,),), ((1.0,),)),
        method="BDF",
        rtol=1e-8,
        atol=1e-10,
        t_eval=(0.0, 0.5, 1.0),
    )
    assert result.success
    assert result.y[0] == pytest.approx([4.0] * 3, abs=1e-12)
    assert result.y[1] == pytest.approx([3.0 - 2.0 * math.exp(-3.0 * t) for t in result.t], rel=1e-7)


def test_stage_budget_and_invalid_trials_fail_without_stale_derivative():
    layout, rhs, seen = evaluator(budget=1)
    state = layout.pack_initial(((3.0,),), ((1.0,),))
    rhs(0.0, state)
    with pytest.raises(RuntimeError, match="budget"):
        rhs(0.1, state)
    assert len(seen) == 1
    _, rhs, seen = evaluator()
    with pytest.raises(ArithmeticError, match="consumes"):
        rhs(0.0, (1.0, 2.0))
    assert seen == []


def test_seed_event_bdf_restarts_at_threshold_with_same_trial_feedback():
    layout, rhs, _ = evaluator(budget=5000)
    initial = layout.pack_initial(((4.0,),), ((0.0,),))
    result = integrate_coupled_seed_bdf(
        rhs,
        initial,
        (0.0, 0.05, 0.5, 1.0),
        relative_tolerance=1e-8,
        absolute_tolerance_mol=1e-10,
        maximum_step_s=0.02,
        maximum_seed_events=4,
    )
    assert result["committed"], result
    event_time = -2.0 * math.log(0.95)
    assert len(result["seed_transitions"]) == 1
    assert result["seed_transitions"][0]["time_s"] == pytest.approx(event_time, abs=1e-7)
    expected = 3.0 - 2.9 * math.exp(-3.0 * (1.0 - event_time))
    assert result["state_by_time"][-1] == pytest.approx((4.0, expected), rel=1e-7)


def test_failed_seed_driver_has_no_committed_or_partial_trajectory():
    layout, rhs, _ = evaluator(budget=1)
    result = integrate_coupled_seed_bdf(
        rhs,
        layout.pack_initial(((4.0,),), ((0.0,),)),
        (0.0, 1.0),
        relative_tolerance=1e-8,
        absolute_tolerance_mol=1e-10,
        maximum_step_s=0.1,
        maximum_seed_events=4,
    )
    assert not result["committed"]
    assert "state_by_time" not in result


def two_cell_seed_run(second_threshold=0.1, event_budget=4, phase_major=False):
    _, single, _ = evaluator()
    layout = CoupledPhaseStateLayout(("M",), ("solid",), ("left", "right"), ((1.0,),))

    def chemistry(time, dissolved):
        return CoupledPhaseTrialChemistry(tuple({"M": value} for value in dissolved[0]), ((0.0, 0.0),))

    right = single.nucleation[0][0].model_copy(
        update={"nucleated_inventory_threshold_mol_m3": second_threshold}
    )
    rhs = CoupledPhaseRHS(
        layout,
        (single.phases[0], single.phases[0]),
        (single.nucleation[0], (right,)),
        (single.growth[0], single.growth[0]),
        (1.0, 1.0),
        (300.0, 300.0),
        chemistry,
        maximum_evaluations=5000,
    )
    if phase_major:
        phase_grid = tuple(
            tuple(rhs.nucleation[cell][phase] for cell in range(2))
            for phase in range(len(layout.phase_ids))
        )
        base_rhs = rhs

        class PhaseMajorAdapter:
            nucleation = phase_grid
            nucleation_phase_major = True
            layout = base_rhs.layout
            volumes = base_rhs.volumes

            def __getattr__(self, name):
                return getattr(base_rhs, name)

            def __call__(self, time_s, state):
                return base_rhs(time_s, state)

        rhs = PhaseMajorAdapter()
    return integrate_coupled_seed_bdf(
        rhs,
        layout.pack_initial(((4.0, 4.0),), ((0.0, 0.0),)),
        (0.0, 0.5),
        relative_tolerance=1e-8,
        absolute_tolerance_mol=1e-10,
        maximum_step_s=0.01,
        maximum_seed_events=event_budget,
    )


def test_simultaneous_cells_transition_once_at_same_boundary():
    result = two_cell_seed_run()
    assert result["committed"], result
    transitions = result["seed_transitions"]
    assert len(transitions) == 2
    assert [row["cell_id"] for row in transitions] == ["left", "right"]
    assert transitions[0]["time_s"] == transitions[1]["time_s"]
    final = result["state_by_time"][-1]
    assert final[2] == pytest.approx(final[3], rel=1e-12)


def test_phase_major_nucleation_law_grid_is_supported():
    result = two_cell_seed_run(phase_major=True)
    assert result["committed"], result
    assert [row["cell_id"] for row in result["seed_transitions"]] == ["left", "right"]


def test_nearby_seed_events_are_not_merged_using_ode_tolerance():
    result = two_cell_seed_run(second_threshold=0.1001)
    assert result["committed"], result
    transitions = result["seed_transitions"]
    assert len(transitions) == 2
    assert transitions[1]["time_s"] > transitions[0]["time_s"]


def test_simultaneous_group_budget_failure_does_not_commit_partial_group():
    result = two_cell_seed_run(event_budget=1)
    assert not result["committed"]
    assert result["seed_transitions"] == ()
    assert "state_by_time" not in result


def test_same_stage_source_integrals_survive_seed_restart():
    layout, rhs, _ = evaluator(budget=10000)

    def supplied_chemistry(time, dissolved):
        return CoupledPhaseTrialChemistry(({"M": dissolved[0][0]},), ((2.0 * time,),))

    rhs.stage_chemistry = supplied_chemistry
    result = integrate_coupled_seed_bdf(
        rhs,
        layout.pack_initial(((4.0,),), ((0.0,),)),
        (0.0, 0.5, 1.0),
        relative_tolerance=1e-8,
        absolute_tolerance_mol=1e-10,
        maximum_step_s=0.02,
        maximum_seed_events=4,
        integrate_component_sources=True,
    )
    assert result["committed"], result
    assert len(result["seed_transitions"]) == 1
    for time, state, sources, balance in zip(
        result["time_s"],
        result["state_by_time"],
        result["integrated_net_sources_by_time"],
        result["component_balance_by_time"],
        strict=True,
    ):
        assert len(state) == layout.total_size
        assert sources[0][0] == pytest.approx(time**2, abs=2e-8)
        assert state[0] == pytest.approx(4.0 + time**2, abs=2e-8)
        assert balance["balanced"]


def test_failed_augmented_driver_withholds_source_history():
    layout, rhs, _ = evaluator(budget=1)
    result = integrate_coupled_seed_bdf(
        rhs,
        layout.pack_initial(((4.0,),), ((0.0,),)),
        (0.0, 1.0),
        relative_tolerance=1e-8,
        absolute_tolerance_mol=1e-10,
        maximum_step_s=0.02,
        maximum_seed_events=4,
        integrate_component_sources=True,
    )
    assert not result["committed"]
    assert "integrated_net_sources_by_time" not in result
