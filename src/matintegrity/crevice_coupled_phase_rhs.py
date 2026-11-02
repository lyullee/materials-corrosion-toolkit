"""Internal same-trial chemistry and phase RHS, not a qualified public solver."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from .crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from .crevice_coupled_phase_state import CoupledPhaseStateLayout
from .crevice_nucleation_kinetic_history import CreviceMolarNucleationLaw
from .crevice_stage_kinetic_rates import trial_phase_rate_mol_s, trial_saturation_ratio
from .multiphase_kinetic_ledger import SolidSaturationRateLaw


@dataclass(frozen=True)
class CoupledPhaseTrialChemistry:
    """Exact cell order activities and component-major transport/external rates."""

    dimensionless_activity_by_cell: tuple[dict[str, float], ...]
    component_transport_and_external_rates_mol_s: tuple[tuple[float, ...], ...]


class CoupledPhaseRHS:
    """Recompute saturation and phase rates from each supplied BDF trial state.

    The callback must solve local chemistry and transport at the supplied trial
    dissolved inventories. Seed/depletion event handling, the production model's
    evidence bindings and final integrated ledgers remain driver responsibilities.
    No mutable seed latch or previous-stage chemistry is cached here.
    """

    def __init__(
        self,
        layout: CoupledPhaseStateLayout,
        phase_records_by_cell: tuple[tuple[CreviceCompetingSolidPhase, ...], ...],
        nucleation_laws_by_cell: tuple[tuple[CreviceMolarNucleationLaw, ...], ...],
        growth_laws_by_cell: tuple[tuple[SolidSaturationRateLaw, ...], ...],
        solution_volume_m3_by_cell: tuple[float, ...],
        temperature_K_by_cell: tuple[float, ...],
        stage_chemistry: Callable[[float, tuple[tuple[float, ...], ...]], CoupledPhaseTrialChemistry],
        *,
        maximum_evaluations: int,
    ):
        nc = len(layout.cell_ids)
        for table in (phase_records_by_cell, nucleation_laws_by_cell, growth_laws_by_cell):
            if len(table) != nc or any(
                tuple(row.solid_species_id for row in cell) != layout.phase_ids for cell in table
            ):
                raise ValueError("phase and law tables must preserve exact cell and phase identity order")
        for values in (solution_volume_m3_by_cell, temperature_K_by_cell):
            if len(values) != nc or any(not math.isfinite(value) or value <= 0 for value in values):
                raise ValueError("cell volumes and temperatures must be finite positive exact layouts")
        if (
            isinstance(maximum_evaluations, bool)
            or not isinstance(maximum_evaluations, int)
            or maximum_evaluations < 1
        ):
            raise ValueError("an explicit positive integer stage evaluation budget is required")
        self.layout = layout
        self.phases = phase_records_by_cell
        self.nucleation = nucleation_laws_by_cell
        self.growth = growth_laws_by_cell
        self.volumes = solution_volume_m3_by_cell
        self.temperatures = temperature_K_by_cell
        self.stage_chemistry = stage_chemistry
        self.maximum_evaluations = maximum_evaluations
        self.evaluations = 0
        self.seeded_by_phase_cell = None

    def set_seed_modes_at_boundary(self, modes):
        """Driver-only accepted-boundary update; never call from a trial callback."""
        if len(modes) != len(self.layout.phase_ids) or any(
            len(row) != len(self.layout.cell_ids) or any(type(value) is not bool for value in row)
            for row in modes
        ):
            raise ValueError("seed modes must preserve exact phase/cell boolean layout")
        self.seeded_by_phase_cell = tuple(tuple(row) for row in modes)

    def __call__(self, time_s, state):
        if not math.isfinite(time_s):
            raise ValueError("stage time must be finite")
        self.evaluations += 1
        if self.evaluations > self.maximum_evaluations:
            raise RuntimeError("coupled phase stage evaluation budget exceeded")
        dissolved, solids = self.layout.unpack_trial(state)
        chemistry = self.stage_chemistry(time_s, dissolved)
        if len(chemistry.dimensionless_activity_by_cell) != len(self.layout.cell_ids):
            raise ValueError("stage activities must preserve exact cell layout")
        rates = [[] for _ in self.layout.phase_ids]
        for cell, phases in enumerate(self.phases):
            for phase_index, phase in enumerate(phases):
                saturation = trial_saturation_ratio(phase, chemistry.dimensionless_activity_by_cell[cell])
                rate, _ = trial_phase_rate_mol_s(
                    solid_inventory_mol=solids[phase_index][cell],
                    solution_volume_m3=self.volumes[cell],
                    saturation_ratio=saturation,
                    temperature_K=self.temperatures[cell],
                    nucleation_law=self.nucleation[cell][phase_index],
                    growth_law=self.growth[cell][phase_index],
                    seeded_override=None
                    if self.seeded_by_phase_cell is None
                    else self.seeded_by_phase_cell[phase_index][cell],
                )
                rates[phase_index].append(rate)
        return self.layout.derivative(
            chemistry.component_transport_and_external_rates_mol_s, tuple(tuple(row) for row in rates)
        )
