"""Caller-supplied balanced solid extents for crevice aperture feedback."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, canonical_digest

SOURCE_ID = "caller_crevice_geometry_aware_solid_deposition_extent"
MAX_SPECIES = 100
MAX_SOLIDS = 64
MAX_REACTIONS = 200
MAX_CELLS = 2000


class SolidCoupledSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int
    elemental_composition: dict[str, int]

    @model_validator(mode="after")
    def valid_composition(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("species require explicit nonnegative elemental counts")
        if not any(self.elemental_composition.values()):
            raise ValueError("species elemental composition cannot be all zero")
        return self


class SolidPhaseInventoryBasis(Contract):
    phase_id: str = Field(min_length=1)
    charge_number: Literal[0] = 0
    elemental_composition: dict[str, int]
    initial_inventory_mol_m2_by_cell: tuple[float, ...] = Field(min_length=1, max_length=MAX_CELLS)
    initial_inventory_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    molar_volume_m3_mol: float = Field(gt=0)
    molar_volume_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def valid_solid(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("solid phase requires explicit nonnegative elemental counts")
        if not any(self.elemental_composition.values()):
            raise ValueError("solid phase elemental composition cannot be all zero")
        if any(not math.isfinite(value) or value < 0 for value in self.initial_inventory_mol_m2_by_cell):
            raise ValueError("initial solid inventory must be finite and nonnegative")
        if not math.isfinite(self.molar_volume_m3_mol) or self.molar_volume_m3_mol <= 0:
            raise ValueError("solid molar volume must be finite and positive")
        return self


class CallerSolidReactionExtent(Contract):
    reaction_id: str = Field(min_length=1)
    aqueous_stoichiometry: tuple[float, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    solid_stoichiometry: tuple[float, ...] = Field(min_length=1, max_length=MAX_SOLIDS)


def solid_deposition_configuration_payload(
    *, provider_id: str, provider_revision: str, provider_source_sha256: str,
    aqueous_species: tuple[SolidCoupledSpecies, ...],
    solid_phases: tuple[SolidPhaseInventoryBasis, ...],
    reactions: tuple[CallerSolidReactionExtent, ...],
    valid_time_start_s: float, valid_time_end_s: float,
    minimum_aperture_m: float, maximum_aperture_m: float,
    maximum_absolute_extent_mol_m3_by_reaction: tuple[float, ...],
    maximum_concentration_mol_m3_by_aqueous_species: tuple[float, ...],
    reference_area_m2: float, deposition_side_count: int,
    coverage_fraction_by_cell: tuple[float, ...],
) -> dict:
    return {
        "provider_id": provider_id,
        "provider_revision": provider_revision,
        "provider_source_sha256": provider_source_sha256,
        "aqueous_species": [row.model_dump(mode="json") for row in aqueous_species],
        "solid_phases": [row.model_dump(mode="json") for row in solid_phases],
        "reactions": [row.model_dump(mode="json") for row in reactions],
        "valid_time_start_s": valid_time_start_s,
        "valid_time_end_s": valid_time_end_s,
        "minimum_aperture_m": minimum_aperture_m,
        "maximum_aperture_m": maximum_aperture_m,
        "maximum_absolute_extent_mol_m3_by_reaction": list(maximum_absolute_extent_mol_m3_by_reaction),
        "maximum_concentration_mol_m3_by_aqueous_species": list(maximum_concentration_mol_m3_by_aqueous_species),
        "reference_area_m2": reference_area_m2,
        "deposition_side_count": deposition_side_count,
        "coverage_fraction_by_cell": list(coverage_fraction_by_cell),
    }


class CreviceGeometryAwareSolidDepositionContract(Contract):
    """Caller-defined endpoint extent law and complete solid inventory basis."""

    schema_version: Literal["matintegrity.crevice_geometry_aware_solid_deposition.v1"] = (
        "matintegrity.crevice_geometry_aware_solid_deposition.v1"
    )
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aqueous_species: tuple[SolidCoupledSpecies, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    solid_phases: tuple[SolidPhaseInventoryBasis, ...] = Field(min_length=1, max_length=MAX_SOLIDS)
    reactions: tuple[CallerSolidReactionExtent, ...] = Field(min_length=1, max_length=MAX_REACTIONS)
    valid_time_start_s: float = Field(ge=0)
    valid_time_end_s: float = Field(gt=0)
    minimum_aperture_m: float = Field(gt=0)
    maximum_aperture_m: float = Field(gt=0)
    maximum_absolute_extent_mol_m3_by_reaction: tuple[float, ...] = Field(min_length=1, max_length=MAX_REACTIONS)
    maximum_concentration_mol_m3_by_aqueous_species: tuple[float, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    reference_area_m2: float = Field(gt=0)
    deposition_side_count: Literal[1, 2]
    coverage_fraction_by_cell: tuple[float, ...] = Field(min_length=1, max_length=MAX_CELLS)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    endpoint_split_and_volume_basis_reviewed: bool
    reaction_extent_units_and_direction_reviewed: bool
    element_charge_and_phase_stoichiometry_reviewed: bool
    solid_inventory_and_dissolution_limits_reviewed: bool
    molar_volume_state_and_source_reviewed: bool
    deposition_face_coverage_mapping_reviewed: bool
    deterministic_re_evaluation_reviewed: bool
    reference_area_and_cell_volume_basis_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_extent_contract(self):
        aqueous_ids = tuple(row.species_id for row in self.aqueous_species)
        solid_ids = tuple(row.phase_id for row in self.solid_phases)
        reaction_ids = tuple(row.reaction_id for row in self.reactions)
        if any(len(set(rows)) != len(rows) for rows in (aqueous_ids, solid_ids, reaction_ids)):
            raise ValueError("aqueous species, solid phases and reaction IDs must be unique")
        cell_counts = {len(row.initial_inventory_mol_m2_by_cell) for row in self.solid_phases}
        if len(cell_counts) != 1 or not cell_counts or next(iter(cell_counts)) != len(self.coverage_fraction_by_cell):
            raise ValueError("all initial solid inventories and coverage rows must share one cell count")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in self.coverage_fraction_by_cell):
            raise ValueError("cell coverage fractions must lie in [0, 1]")
        if len(self.maximum_absolute_extent_mol_m3_by_reaction) != len(reaction_ids) or any(
            not math.isfinite(value) or value <= 0 for value in self.maximum_absolute_extent_mol_m3_by_reaction
        ):
            raise ValueError("one finite positive extent support bound is required per reaction")
        if len(self.maximum_concentration_mol_m3_by_aqueous_species) != len(aqueous_ids) or any(
            not math.isfinite(value) or value <= 0 for value in self.maximum_concentration_mol_m3_by_aqueous_species
        ):
            raise ValueError("one finite positive concentration support bound is required per aqueous species")
        if (
            not math.isfinite(self.valid_time_start_s) or not math.isfinite(self.valid_time_end_s)
            or self.valid_time_end_s <= self.valid_time_start_s
            or not math.isfinite(self.minimum_aperture_m) or not math.isfinite(self.maximum_aperture_m)
            or self.maximum_aperture_m <= self.minimum_aperture_m
            or not math.isfinite(self.reference_area_m2) or self.reference_area_m2 <= 0
        ):
            raise ValueError("provider time, aperture and reference-area supports must be finite and ordered")
        if set(aqueous_ids) & set(solid_ids):
            raise ValueError("aqueous and solid phase identifiers must be distinct")
        element_keys = set().union(
            *(row.elemental_composition for row in self.aqueous_species),
            *(row.elemental_composition for row in self.solid_phases),
        )
        for reaction in self.reactions:
            if len(reaction.aqueous_stoichiometry) != len(aqueous_ids) or len(reaction.solid_stoichiometry) != len(solid_ids):
                raise ValueError("reaction stoichiometry must follow the exact aqueous and solid ID orders")
            coefficients = (*reaction.aqueous_stoichiometry, *reaction.solid_stoichiometry)
            if any(not math.isfinite(value) for value in coefficients) or not any(value != 0.0 for value in coefficients):
                raise ValueError("reaction stoichiometry must be finite and nonzero")
            charge = math.fsum(
                value * species.charge_number
                for value, species in zip(reaction.aqueous_stoichiometry, self.aqueous_species, strict=True)
            )
            if not math.isclose(charge, 0.0, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve charge")
            for element in element_keys:
                residual = math.fsum(
                    value * species.elemental_composition.get(element, 0)
                    for value, species in zip(reaction.aqueous_stoichiometry, self.aqueous_species, strict=True)
                ) + math.fsum(
                    value * phase.elemental_composition.get(element, 0)
                    for value, phase in zip(reaction.solid_stoichiometry, self.solid_phases, strict=True)
                )
                if not math.isclose(residual, 0.0, rel_tol=0.0, abs_tol=1e-12):
                    raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve element {element!r}")
        expected_evidence = {
            (self.provider_id, self.provider_source_sha256),
            *((phase.phase_id, phase.molar_volume_source_sha256) for phase in self.solid_phases),
            *((f"{phase.phase_id}:initial_inventory", phase.initial_inventory_source_sha256) for phase in self.solid_phases),
        }
        received_evidence = {(row.source_id, row.sha256) for row in self.evidence}
        if len({row.source_id for row in self.evidence}) != len(self.evidence) or not expected_evidence <= received_evidence:
            raise ValueError("provider and each phase molar-volume source must be pinned by Evidence")
        if not all((
            self.endpoint_split_and_volume_basis_reviewed,
            self.reaction_extent_units_and_direction_reviewed,
            self.element_charge_and_phase_stoichiometry_reviewed,
            self.solid_inventory_and_dissolution_limits_reviewed,
            self.molar_volume_state_and_source_reviewed,
            self.deposition_face_coverage_mapping_reviewed,
            self.deterministic_re_evaluation_reviewed,
            self.reference_area_and_cell_volume_basis_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("all extent, inventory, geometry, source and deterministic-use reviews are required")
        if canonical_digest(self.configuration_payload()) != self.configuration_sha256:
            raise ValueError("solid-deposition provider configuration digest mismatch")
        return self

    def configuration_payload(self) -> dict:
        return solid_deposition_configuration_payload(
            provider_id=self.provider_id,
            provider_revision=self.provider_revision,
            provider_source_sha256=self.provider_source_sha256,
            aqueous_species=self.aqueous_species,
            solid_phases=self.solid_phases,
            reactions=self.reactions,
            valid_time_start_s=self.valid_time_start_s,
            valid_time_end_s=self.valid_time_end_s,
            minimum_aperture_m=self.minimum_aperture_m,
            maximum_aperture_m=self.maximum_aperture_m,
            maximum_absolute_extent_mol_m3_by_reaction=self.maximum_absolute_extent_mol_m3_by_reaction,
            maximum_concentration_mol_m3_by_aqueous_species=self.maximum_concentration_mol_m3_by_aqueous_species,
            reference_area_m2=self.reference_area_m2,
            deposition_side_count=self.deposition_side_count,
            coverage_fraction_by_cell=self.coverage_fraction_by_cell,
        )


class GeometryAwareSolidExtentEvaluationError(ValueError):
    def __init__(self, *, provider_id: str, elapsed_time_s: float | None, reason: str):
        super().__init__(reason)
        self.provider_id = provider_id
        self.elapsed_time_s = elapsed_time_s
        self.reason = reason

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "elapsed_time_s": self.elapsed_time_s,
            "failure_type": type(self).__name__,
            "reason": self.reason,
        }


class CreviceGeometryAwareSolidDepositionProvider:
    """Evaluate caller endpoint extents and close aqueous/solid inventories."""

    def __init__(
        self,
        contract: CreviceGeometryAwareSolidDepositionContract,
        evaluate_endpoint_extents: Callable[..., np.ndarray],
    ):
        if not callable(evaluate_endpoint_extents):
            raise TypeError("caller endpoint extent evaluator must be callable")
        self.contract = contract
        self.evaluate_endpoint_extents = evaluate_endpoint_extents
        self.provider_id = contract.provider_id
        self.provider_revision = contract.provider_revision
        self.source_sha256 = contract.provider_source_sha256
        self.configuration_sha256 = contract.configuration_sha256
        self.source_request_sha256 = canonical_digest(contract.model_dump(mode="json"))
        self.species_ids = tuple(row.species_id for row in contract.aqueous_species)
        self.solid_phase_ids = tuple(row.phase_id for row in contract.solid_phases)
        self.reaction_ids = tuple(row.reaction_id for row in contract.reactions)
        self._aqueous_stoichiometry = np.asarray(
            [row.aqueous_stoichiometry for row in contract.reactions], dtype=float
        ).T
        self._solid_stoichiometry = np.asarray(
            [row.solid_stoichiometry for row in contract.reactions], dtype=float
        ).T

    def evaluate_endpoint(
        self,
        *,
        start_time_s: float,
        end_time_s: float,
        transport_endpoint_concentration_mol_m3: np.ndarray,
        start_aperture_m: np.ndarray,
        guessed_end_aperture_m: np.ndarray,
        current_solid_inventory_mol_m2_by_phase: dict[str, np.ndarray],
        cell_volume_per_reference_area_m: np.ndarray,
        cell_width_m: np.ndarray,
        transverse_width_m: float,
        metal_recession_increment_m_by_cell: np.ndarray,
    ) -> dict:
        contract = self.contract
        provider_id = self.provider_id
        end_time = float(end_time_s)
        arrays = [
            np.asarray(transport_endpoint_concentration_mol_m3, dtype=float),
            np.asarray(start_aperture_m, dtype=float),
            np.asarray(guessed_end_aperture_m, dtype=float),
            np.asarray(cell_volume_per_reference_area_m, dtype=float),
            np.asarray(cell_width_m, dtype=float),
            np.asarray(metal_recession_increment_m_by_cell, dtype=float),
        ]
        concentration, start_aperture, end_aperture, volume_per_area, widths, recession = arrays
        try:
            cells = len(widths)
            if (
                not math.isfinite(start_time_s) or not math.isfinite(end_time)
                or end_time <= start_time_s
                or start_time_s < contract.valid_time_start_s or end_time > contract.valid_time_end_s
                or concentration.shape != (len(self.species_ids), cells)
                or start_aperture.shape != (cells,) or end_aperture.shape != (cells,)
                or volume_per_area.shape != (cells,) or recession.shape != (cells,)
                or any(not np.isfinite(row).all() for row in arrays)
                or np.any(concentration < 0) or np.any(volume_per_area <= 0) or np.any(widths <= 0)
                or not math.isfinite(transverse_width_m) or transverse_width_m <= 0
                or np.any(start_aperture < contract.minimum_aperture_m)
                or np.any(start_aperture > contract.maximum_aperture_m)
                or np.any(end_aperture < contract.minimum_aperture_m)
                or np.any(end_aperture > contract.maximum_aperture_m)
                or cells > MAX_CELLS
                or cells != len(contract.coverage_fraction_by_cell)
            ):
                raise ValueError("endpoint time, state, geometry or inventory grid is outside contract support")
            concentration_limits = np.asarray(contract.maximum_concentration_mol_m3_by_aqueous_species)[:, None]
            if np.any(concentration > concentration_limits):
                raise ValueError("endpoint concentration exceeds caller support")
            solid_start = np.asarray([
                current_solid_inventory_mol_m2_by_phase[phase_id] for phase_id in self.solid_phase_ids
            ], dtype=float)
            if solid_start.shape != (len(self.solid_phase_ids), cells) or not np.isfinite(solid_start).all() or np.any(solid_start < 0):
                raise ValueError("solid inventory state must be finite, nonnegative and phase/cell aligned")
            aperture_path_payload = {
                "start_time_s": float(start_time_s), "end_time_s": end_time,
                "start_aperture_m": start_aperture.tolist(), "guessed_end_aperture_m": end_aperture.tolist(),
                "endpoint_concentration_mol_m3": concentration.tolist(),
                "solid_inventory_mol_m2_by_phase": {
                    phase_id: solid_start[index].tolist() for index, phase_id in enumerate(self.solid_phase_ids)
                },
            }
            raw = np.asarray(self.evaluate_endpoint_extents(
                float(start_time_s), end_time, concentration.copy(), start_aperture.copy(), end_aperture.copy(),
                {phase_id: solid_start[index].copy() for index, phase_id in enumerate(self.solid_phase_ids)},
            ), dtype=float)
            repeated = np.asarray(self.evaluate_endpoint_extents(
                float(start_time_s), end_time, concentration.copy(), start_aperture.copy(), end_aperture.copy(),
                {phase_id: solid_start[index].copy() for index, phase_id in enumerate(self.solid_phase_ids)},
            ), dtype=float)
            if raw.shape != (len(self.reaction_ids), cells) or not np.isfinite(raw).all() or not np.array_equal(raw, repeated):
                raise ValueError("endpoint extents must be finite reaction-by-cell values and exactly repeatable")
            bounds = np.asarray(contract.maximum_absolute_extent_mol_m3_by_reaction)[:, None]
            if np.any(np.abs(raw) > bounds):
                raise ValueError("endpoint extent exceeds the declared reaction support")
            aqueous_delta = self._aqueous_stoichiometry @ raw
            if concentration.shape != aqueous_delta.shape:
                raise ArithmeticError("aqueous stoichiometric extent mapping exceeded shape support")
            reacted_concentration = concentration + aqueous_delta
            if (
                not np.isfinite(reacted_concentration).all()
                or np.any(reacted_concentration < 0)
                or np.any(reacted_concentration > concentration_limits)
            ):
                raise ValueError("endpoint reaction extent would make an aqueous inventory negative")
            solid_change = (self._solid_stoichiometry @ raw) * volume_per_area[None, :]
            solid_end = solid_start + solid_change
            if not np.isfinite(solid_end).all() or np.any(solid_end < -1e-12):
                raise ValueError("endpoint reaction extent exceeds available solid inventory")
            solid_end = np.maximum(solid_end, 0.0)
            solid_balance = solid_end - solid_start - solid_change
            if not np.isfinite(solid_balance).all() or np.any(np.abs(solid_balance) > 1e-12):
                raise ArithmeticError("solid phase inventory closure failed")
            source_mol_m2 = aqueous_delta * volume_per_area[None, :]
            if not np.isfinite(source_mol_m2).all():
                raise ArithmeticError("aqueous endpoint source exceeds finite inventory support")
            aqueous_balance_residual = source_mol_m2 - aqueous_delta * volume_per_area[None, :]
            if not np.isfinite(aqueous_balance_residual).all() or np.any(np.abs(aqueous_balance_residual) > 1e-12):
                raise ArithmeticError("aqueous species endpoint inventory mapping failed closure")
            charge_coefficients = np.asarray([
                math.fsum(value * species.charge_number for value, species in zip(
                    reaction.aqueous_stoichiometry, contract.aqueous_species, strict=True
                ))
                for reaction in contract.reactions
            ], dtype=float)
            charge_residual = charge_coefficients @ raw
            stoichiometric_limit = 1e-12 * np.maximum(1.0, np.max(np.abs(raw), axis=0))
            element_residuals = {}
            for element in set().union(
                *(row.elemental_composition for row in contract.aqueous_species),
                *(row.elemental_composition for row in contract.solid_phases),
            ):
                coefficients = np.asarray([
                    math.fsum(
                        coefficient * species.elemental_composition.get(element, 0)
                        for coefficient, species in zip(reaction.aqueous_stoichiometry, contract.aqueous_species, strict=True)
                    ) + math.fsum(
                        coefficient * phase.elemental_composition.get(element, 0)
                        for coefficient, phase in zip(reaction.solid_stoichiometry, contract.solid_phases, strict=True)
                    )
                    for reaction in contract.reactions
                ], dtype=float)
                element_residuals[element] = (coefficients @ raw).tolist()
            if (
                not np.isfinite(charge_residual).all()
                or np.any(np.abs(charge_residual) > stoichiometric_limit)
                or any(not np.isfinite(values).all() or np.any(np.abs(values) > stoichiometric_limit) for values in element_residuals.values())
            ):
                raise ArithmeticError("endpoint reaction extent failed element or charge closure")
            molar_volumes = np.asarray([row.molar_volume_m3_mol for row in contract.solid_phases])
            delta_volume_per_area = np.sum(solid_change * molar_volumes[:, None], axis=0)
            plan_area = widths * float(transverse_width_m)
            if not np.isfinite(delta_volume_per_area).all() or not np.isfinite(plan_area).all() or np.any(plan_area <= 0):
                raise ArithmeticError("solid volume or cell planform exceeds finite geometry support")
            mean_aperture_loss = delta_volume_per_area * contract.reference_area_m2 / plan_area
            coverage = np.asarray(contract.coverage_fraction_by_cell)
            covered_loss = np.zeros(cells, dtype=float)
            nonzero_coverage = coverage > 0
            if np.any((~nonzero_coverage) & (np.abs(delta_volume_per_area) > 1e-15)):
                raise ValueError("nonzero solid-volume change requires nonzero declared deposition coverage")
            covered_loss[nonzero_coverage] = (
                mean_aperture_loss[nonzero_coverage] / coverage[nonzero_coverage]
            )
            predicted_aperture = start_aperture + contract.deposition_side_count * recession - mean_aperture_loss
            covered_remaining = start_aperture + contract.deposition_side_count * recession - covered_loss
            if (
                not np.isfinite(predicted_aperture).all() or not np.isfinite(covered_remaining).all()
                or np.any(predicted_aperture < contract.minimum_aperture_m)
                or np.any(predicted_aperture > contract.maximum_aperture_m)
                or np.any(covered_remaining < 0)
            ):
                raise ValueError("combined recession/deposition geometry leaves declared gap support")
            endpoint_digest = canonical_digest({
                "provider_contract_sha256": canonical_digest(contract.model_dump(mode="json")),
                "aperture_path": aperture_path_payload,
                "extent_mol_m3_by_reaction_cell": raw.tolist(),
                "metal_recession_increment_m_by_cell": recession.tolist(),
            })
            return {
                "provider_id": provider_id,
                "provider_revision": self.provider_revision,
                "provider_source_sha256": self.source_sha256,
                "provider_configuration_sha256": self.configuration_sha256,
                "provider_contract_sha256": canonical_digest(contract.model_dump(mode="json")),
                "endpoint_evaluation_sha256": endpoint_digest,
                "start_time_s": float(start_time_s), "end_time_s": end_time,
                "reaction_ids": list(self.reaction_ids), "aqueous_species_ids": list(self.species_ids),
                "solid_phase_ids": list(self.solid_phase_ids),
                "extent_mol_m3_by_reaction_cell": raw.tolist(),
                "aqueous_concentration_delta_mol_m3_by_species_cell": aqueous_delta.tolist(),
                "aqueous_reaction_source_mol_m2_by_species_cell": source_mol_m2.tolist(),
                "solid_inventory_start_mol_m2_by_phase_cell": solid_start.tolist(),
                "solid_inventory_end_mol_m2_by_phase_cell": solid_end.tolist(),
                "solid_inventory_change_mol_m2_by_phase_cell": solid_change.tolist(),
                "aqueous_inventory_mapping_residual_mol_m2_by_species_cell": aqueous_balance_residual.tolist(),
                "element_balance_residual_mol_m3_by_element_cell": element_residuals,
                "charge_balance_residual_equiv_m3_by_cell": charge_residual.tolist(),
                "solid_volume_change_m3_m2_by_cell": delta_volume_per_area.tolist(),
                "equivalent_mean_aperture_loss_m_by_cell": mean_aperture_loss.tolist(),
                "covered_patch_aperture_loss_m_by_cell": covered_loss.tolist(),
                "predicted_end_aperture_m_by_cell": predicted_aperture.tolist(),
                "covered_patch_remaining_aperture_m_by_cell": covered_remaining.tolist(),
                "reaction_element_charge_balanced": True,
                "aqueous_inventory_source_basis": "endpoint_extent_mol_m3 multiplied by guessed end cell liquid volume per reference area",
                "geometry_interpretation": "cell mean solid volume maps to mean gap loss; coverage is used for a separate local covered-patch closure gate",
            }
        except GeometryAwareSolidExtentEvaluationError:
            raise
        except Exception as error:
            raise GeometryAwareSolidExtentEvaluationError(
                provider_id=provider_id,
                elapsed_time_s=end_time if math.isfinite(end_time) else None,
                reason=f"caller solid-extent evaluation failed: {type(error).__name__}",
            ) from error
