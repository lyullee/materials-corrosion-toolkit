"""Digest-bound one-cell phase and kinetic-law inputs for component BDF stages."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest
from .crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from .crevice_nucleation_kinetic_history import (
    CreviceMolarNucleationLaw,
    EvidenceBoundSaturationGrowthLaw,
)


class CreviceBDFInitialSolidInventory(Contract):
    """Initial solid amount paired with one ordered solid-phase identity."""

    solid_species_id: str = Field(min_length=1)
    initial_solid_moles_mol: Nonnegative


class CreviceBDFKineticPhaseSet(Contract):
    """One-cell, exact-clock phase set for same-stage kinetic BDF integration.

    Candidate phases, initial phase inventories, nucleation laws and growth
    laws use identical ordered solid species IDs. The phase-set digest binds
    every identity, clock, temperature, phase record, amount and kinetic law.
    """

    schema_version: Literal["matintegrity.crevice_bdf_kinetic_phase_set.v1"] = (
        "matintegrity.crevice_bdf_kinetic_phase_set.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    phase_set_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    valid_time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    temperature_K: Positive
    phase_candidates: tuple[CreviceCompetingSolidPhase, ...] = Field(min_length=1, max_length=12)
    initial_solid_inventory_by_phase: tuple[CreviceBDFInitialSolidInventory, ...] = Field(
        min_length=1, max_length=12
    )
    nucleation_laws: tuple[CreviceMolarNucleationLaw, ...] = Field(min_length=1, max_length=12)
    growth_laws: tuple[EvidenceBoundSaturationGrowthLaw, ...] = Field(min_length=1, max_length=12)
    phase_set_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_phase_set(self):
        if any(not math.isfinite(value) for value in self.valid_time_s):
            raise ValueError("kinetic BDF phase-set time knots must be finite")
        if any(right <= left for left, right in zip(self.valid_time_s, self.valid_time_s[1:])):
            raise ValueError("kinetic BDF phase-set time knots must be strictly increasing")

        phase_ids = tuple(row.solid_species_id for row in self.phase_candidates)
        inventory_ids = tuple(row.solid_species_id for row in self.initial_solid_inventory_by_phase)
        nucleation_ids = tuple(row.solid_species_id for row in self.nucleation_laws)
        growth_ids = tuple(row.law.solid_species_id for row in self.growth_laws)
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("kinetic BDF phase candidate IDs must be unique")
        if not (inventory_ids == nucleation_ids == growth_ids == phase_ids):
            raise ValueError(
                "initial solid amounts, nucleation laws and growth laws must match candidate phase IDs and order"
            )
        if any(
            not math.isfinite(float(row.initial_solid_moles_mol)) or row.initial_solid_moles_mol < 0.0
            for row in self.initial_solid_inventory_by_phase
        ):
            raise ValueError("initial solid amounts must be finite, nonnegative molar inventories")

        payload = self.model_dump(mode="json", exclude={"phase_set_sha256", "evidence"})
        if canonical_digest(payload) != self.phase_set_sha256:
            raise ValueError("kinetic BDF phase-set digest must bind all ordered phase, clock and law inputs")
        if not any(row.sha256 == self.phase_set_sha256 for row in self.evidence):
            raise ValueError("kinetic BDF phase-set Evidence must pin its exact digest")
        return self
