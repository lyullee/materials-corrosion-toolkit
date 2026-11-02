"""Internal adapter from coupled dissolved trial inventories to Davies chemistry."""

from __future__ import annotations

import math
from fractions import Fraction

from .contracts import canonical_digest
from .crevice_component_state_bdf import CellAqueousEquilibriumTemplate, _stage_system
from .crevice_coupled_phase_rhs import CoupledPhaseRHS, CoupledPhaseTrialChemistry
from .crevice_coupled_phase_state import CoupledPhaseStateLayout
from .models.aqueous_activity_iteration import aqueous_davies_self_consistent_speciation


class CoupledPhaseDaviesChemistry:
    """Solve every cell at the current trial, then evaluate transport on those rows.

    Transport is supplied explicitly as a callback; absent boundary fluxes are
    not invented. This adapter is internal and does not qualify a coupled solver.
    """

    def __init__(
        self,
        layout: CoupledPhaseStateLayout,
        cells: tuple[CellAqueousEquilibriumTemplate, ...],
        transport,
        *,
        maximum_equilibrium_calls: int,
        maximum_nested_iteration_work: int,
    ):
        if tuple(cell.cell_id for cell in cells) != layout.cell_ids:
            raise ValueError("chemistry templates must preserve exact cell identities and order")
        if any(
            tuple(row.component_id for row in cell.conserved_components) != layout.component_ids
            for cell in cells
        ):
            raise ValueError("chemistry component maps must preserve exact state identity order")
        for budget in (maximum_equilibrium_calls, maximum_nested_iteration_work):
            if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
                raise ValueError("positive integer chemistry work budgets are required")
        self.layout, self.cells, self.transport = layout, cells, transport
        self.maximum_equilibrium_calls = maximum_equilibrium_calls
        self.maximum_nested_iteration_work = maximum_nested_iteration_work
        self.equilibrium_calls = self.nested_iteration_work = 0
        self.lineage_sha256 = canonical_digest({"algorithm": "coupled-phase-davies-stage-v1"})

    def __call__(self, time_s, dissolved):
        if not math.isfinite(time_s):
            raise ValueError("chemistry stage time must be finite")
        self.layout._rows(dissolved, len(self.layout.component_ids), "dissolved trial", nonnegative=True)
        activities, species_rows = [], []
        for index, cell in enumerate(self.cells):
            work = cell.aqueous_activity_request.maximum_outer_iterations * (
                cell.aqueous_activity_request.system.maximum_iterations + 1
            )
            if (
                self.equilibrium_calls >= self.maximum_equilibrium_calls
                or self.nested_iteration_work + work > self.maximum_nested_iteration_work
            ):
                raise RuntimeError("coupled phase chemistry work budget exceeded")
            trial = _stage_system(
                cell, {key: dissolved[i][index] for i, key in enumerate(self.layout.component_ids)}
            )
            self.equilibrium_calls += 1
            self.nested_iteration_work += work
            result = aqueous_davies_self_consistent_speciation(trial)
            if result.status != "computed":
                raise RuntimeError(f"coupled phase cell chemistry failed:{cell.cell_id}:{result.status}")
            rows = result.values.get("species")
            expected = tuple(row.species_id for row in trial.system.species)
            if (
                not isinstance(rows, (list, tuple))
                or tuple(row.get("species_id") for row in rows) != expected
            ):
                raise RuntimeError("coupled phase chemistry species identity mismatch")
            activity = {row["species_id"]: float(row["dimensionless_activity"]) for row in rows}
            if any(not math.isfinite(value) or value <= 0 for value in activity.values()):
                raise ArithmeticError("coupled phase chemistry returned unsupported activity")
            activities.append(activity)
            species_rows.append(tuple(dict(row) for row in rows))
            self.lineage_sha256 = canonical_digest(
                {
                    "previous": self.lineage_sha256,
                    "time_s": float(time_s),
                    "cell_id": cell.cell_id,
                    "input_sha256": canonical_digest(trial.model_dump(mode="json")),
                    "result_sha256": canonical_digest(result.model_dump(mode="json")),
                }
            )
        rates = self.transport(time_s, tuple(species_rows))
        self.layout._rows(rates, len(self.layout.component_ids), "transport rates", nonnegative=False)
        return CoupledPhaseTrialChemistry(tuple(activities), tuple(tuple(row) for row in rates))


def build_coupled_davies_phase_rhs(
    layout,
    cells,
    phase_records_by_cell,
    nucleation_laws_by_cell,
    growth_laws_by_cell,
    transport,
    *,
    maximum_evaluations,
    maximum_equilibrium_calls,
    maximum_nested_iteration_work,
):
    """Bind actual cell chemistry after verifying the phase/component reaction map.

    This remains an internal constructor, not an event-aware integration API.
    Reaction balances are exact for the binary coefficients supplied by callers.
    """
    adapter = CoupledPhaseDaviesChemistry(
        layout,
        cells,
        transport,
        maximum_equilibrium_calls=maximum_equilibrium_calls,
        maximum_nested_iteration_work=maximum_nested_iteration_work,
    )
    if len(phase_records_by_cell) != len(cells):
        raise ValueError("phase records must preserve exact cell count")
    for cell, phases in zip(cells, phase_records_by_cell, strict=True):
        if tuple(phase.solid_species_id for phase in phases) != layout.phase_ids:
            raise ValueError("phase records must preserve exact phase order")
        species = {row.species_id: row for row in cell.aqueous_activity_request.system.species}
        for j, phase in enumerate(phases):
            stoich = phase.aqueous_reactant_stoichiometry
            if not set(stoich) <= set(species):
                raise ValueError("phase reaction refers to undeclared aqueous species")
            if any(species[key].elemental_composition is None for key in stoich):
                raise ValueError("phase reaction species require explicit elemental formulas")
            charge = sum(
                (Fraction(float(value)) * species[key].charge_number for key, value in stoich.items()),
                Fraction(0),
            )
            if charge:
                raise ValueError("neutral solid reaction must conserve charge")
            elements = set(phase.solid_elemental_composition)
            for key in stoich:
                elements.update(species[key].elemental_composition)
            for element in elements:
                amount = sum(
                    (
                        Fraction(float(value)) * species[key].elemental_composition.get(element, 0)
                        for key, value in stoich.items()
                    ),
                    Fraction(0),
                )
                if amount != phase.solid_elemental_composition.get(element, 0):
                    raise ValueError("solid reaction must conserve every declared element")
            for i, component in enumerate(cell.conserved_components):
                extent = sum(
                    (
                        Fraction(float(term.coefficient)) * Fraction(float(stoich.get(term.species_id, 0)))
                        for term in component.species_coefficients
                    ),
                    Fraction(0),
                )
                if extent != Fraction(layout.component_moles_per_phase_mole[i][j]):
                    raise ValueError("coupled state component-phase map differs from reaction stoichiometry")
    rhs = CoupledPhaseRHS(
        layout,
        phase_records_by_cell,
        nucleation_laws_by_cell,
        growth_laws_by_cell,
        tuple(float(cell.solution_volume_L) / 1000.0 for cell in cells),
        tuple(float(cell.aqueous_activity_request.system.temperature_K) for cell in cells),
        adapter,
        maximum_evaluations=maximum_evaluations,
    )
    return rhs
