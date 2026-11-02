"""Conserved total-component and phase state layout for coupled BDF stages.

No public solver is registered here. A stage chemistry/transport evaluator and
event-aware integration driver still have to bind this internal state layout.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class CoupledPhaseStateLayout:
    """Component-major totals followed by phase-major solid amounts, each by cell."""

    component_ids: tuple[str, ...]
    phase_ids: tuple[str, ...]
    cell_ids: tuple[str, ...]
    component_moles_per_phase_mole: tuple[tuple[float, ...], ...]

    def __post_init__(self):
        for identities in (self.component_ids, self.phase_ids, self.cell_ids):
            if (
                not identities
                or len(set(identities)) != len(identities)
                or any(not x.strip() for x in identities)
            ):
                raise ValueError("ordered component, phase and cell identities must be unique and nonblank")
        if len(self.component_moles_per_phase_mole) != len(self.component_ids) or any(
            len(row) != len(self.phase_ids) or any(not math.isfinite(x) for x in row)
            for row in self.component_moles_per_phase_mole
        ):
            raise ValueError("component-phase map must have the exact finite layout")

    @property
    def total_size(self):
        return (len(self.component_ids) + len(self.phase_ids)) * len(self.cell_ids)

    def _rows(self, rows, count, label, *, nonnegative):
        if len(rows) != count or any(len(row) != len(self.cell_ids) for row in rows):
            raise ValueError(f"{label} must preserve exact identity order and cell count")
        if any(not math.isfinite(x) or (nonnegative and x < 0) for row in rows for x in row):
            raise ValueError(f"{label} contains an unsupported inventory or rate")

    @staticmethod
    def _represent(value):
        try:
            result = float(value)
        except OverflowError as error:
            raise ArithmeticError("coupled inventory exceeds numeric support") from error
        if not math.isfinite(result) or (value and result == 0):
            raise ArithmeticError("coupled inventory is not representable")
        return result

    def pack_initial(self, dissolved_by_component, solid_by_phase):
        """Construct total inventories once; never add solids to totals twice."""
        self._rows(dissolved_by_component, len(self.component_ids), "dissolved", nonnegative=True)
        self._rows(solid_by_phase, len(self.phase_ids), "solid", nonnegative=True)
        totals = []
        for i, row in enumerate(dissolved_by_component):
            for cell, dissolved in enumerate(row):
                value = Fraction(dissolved) + sum(
                    (
                        Fraction(self.component_moles_per_phase_mole[i][j])
                        * Fraction(solid_by_phase[j][cell])
                        for j in range(len(self.phase_ids))
                    ),
                    Fraction(0),
                )
                totals.append(self._represent(value))
        state = tuple(totals) + tuple(x for row in solid_by_phase for x in row)
        recovered, _ = self.unpack_trial(state)
        if any(
            not math.isclose(actual, expected, rel_tol=2e-12, abs_tol=0.0)
            for row, original in zip(recovered, dissolved_by_component, strict=True)
            for actual, expected in zip(row, original, strict=True)
        ):
            raise ArithmeticError("total-state representation loses the initial dissolved inventory")
        return state

    def unpack_trial(self, state):
        """Derive dissolved amounts without clamping a negative BDF trial state."""
        if len(state) != self.total_size or any(not math.isfinite(x) for x in state):
            raise ValueError("coupled trial vector has an invalid layout or nonfinite entry")
        nc = len(self.cell_ids)
        split = len(self.component_ids) * nc
        solids = tuple(
            tuple(state[split + j * nc : split + (j + 1) * nc]) for j in range(len(self.phase_ids))
        )
        self._rows(solids, len(self.phase_ids), "solid trial", nonnegative=True)
        dissolved = []
        for i in range(len(self.component_ids)):
            row = []
            for cell in range(nc):
                value = Fraction(state[i * nc + cell]) - sum(
                    (
                        Fraction(self.component_moles_per_phase_mole[i][j]) * Fraction(solids[j][cell])
                        for j in range(len(self.phase_ids))
                    ),
                    Fraction(0),
                )
                if value < 0:
                    raise ArithmeticError("solid trial consumes more than the total component inventory")
                row.append(self._represent(value))
            dissolved.append(tuple(row))
        return tuple(dissolved), solids

    def derivative(self, transport_and_external_component_rates, phase_rates):
        """Internal phase transfer changes solid states, never total components."""
        self._rows(
            transport_and_external_component_rates,
            len(self.component_ids),
            "component rates",
            nonnegative=False,
        )
        self._rows(phase_rates, len(self.phase_ids), "phase rates", nonnegative=False)
        return tuple(x for row in transport_and_external_component_rates for x in row) + tuple(
            x for row in phase_rates for x in row
        )

    def component_balance(
        self,
        initial_state,
        final_state,
        integrated_external_by_component,
        *,
        absolute_tolerance_mol,
        relative_tolerance,
    ):
        """Audit component inventories against independently integrated net sources.

        The supplied integrals include transport across each cell boundary. Internal
        phase transfer belongs in neither source term. This audit does not estimate
        source integrals from endpoint rates or qualify a transport discretization.
        """
        for value in (absolute_tolerance_mol, relative_tolerance):
            if isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("balance tolerances must be finite and nonnegative")
        initial_dissolved, initial_solids = self.unpack_trial(initial_state)
        final_dissolved, final_solids = self.unpack_trial(final_state)
        self._rows(
            integrated_external_by_component,
            len(self.component_ids),
            "integrated net sources",
            nonnegative=False,
        )
        rows = []
        nc = len(self.cell_ids)
        for i, component_id in enumerate(self.component_ids):
            for c, cell_id in enumerate(self.cell_ids):
                start = Fraction(initial_state[i * nc + c])
                finish = Fraction(final_state[i * nc + c])
                source = Fraction(integrated_external_by_component[i][c])
                residual = finish - start - source
                scale = max(abs(start), abs(finish), abs(source))
                limit = Fraction(absolute_tolerance_mol) + Fraction(relative_tolerance) * scale
                solid_change = sum(
                    (
                        Fraction(self.component_moles_per_phase_mole[i][j])
                        * (Fraction(final_solids[j][c]) - Fraction(initial_solids[j][c]))
                        for j in range(len(self.phase_ids))
                    ),
                    Fraction(0),
                )
                rows.append(
                    dict(
                        component_id=component_id,
                        cell_id=cell_id,
                        dissolved_change_mol=self._represent(
                            Fraction(final_dissolved[i][c]) - Fraction(initial_dissolved[i][c])
                        ),
                        solid_component_change_mol=self._represent(solid_change),
                        integrated_net_source_mol=self._represent(source),
                        residual_mol=self._represent(residual),
                        tolerance_mol=self._represent(limit),
                        balanced=abs(residual) <= limit,
                    )
                )
        return dict(balanced=all(row["balanced"] for row in rows), cells=tuple(rows))
