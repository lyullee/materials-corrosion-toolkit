"""Caller-defined aqueous reaction providers evaluated on each guessed slit path."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, canonical_digest

SOURCE_ID = "caller_crevice_geometry_aware_aqueous_chemistry_provider"
MAX_SPECIES = 100
MAX_REACTIONS = 200
MAX_CELLS = 2000


def geometry_aware_chemistry_configuration_payload(
    *,
    provider_id: str,
    provider_revision: str,
    source_sha256: str,
    species: tuple["GeometryAwareAqueousSpecies", ...],
    reactions: tuple["GeometryAwareReactionDefinition", ...],
    valid_time_start_s: float,
    valid_time_end_s: float,
    minimum_aperture_m: float,
    maximum_aperture_m: float,
    maximum_concentration_mol_m3_by_species: tuple[float, ...],
    rate_basis: str = "net_reaction_extent_mol_m3_s",
) -> dict:
    return {
        "provider_id": provider_id,
        "provider_revision": provider_revision,
        "source_sha256": source_sha256,
        "species": [row.model_dump(mode="json") for row in species],
        "reactions": [row.model_dump(mode="json") for row in reactions],
        "valid_time_start_s": valid_time_start_s,
        "valid_time_end_s": valid_time_end_s,
        "minimum_aperture_m": minimum_aperture_m,
        "maximum_aperture_m": maximum_aperture_m,
        "maximum_concentration_mol_m3_by_species": list(maximum_concentration_mol_m3_by_species),
        "rate_basis": rate_basis,
    }


class GeometryAwareAqueousSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int
    elemental_composition: dict[str, int]

    @model_validator(mode="after")
    def validate_composition(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("each aqueous species requires nonnegative elemental counts")
        if not any(self.elemental_composition.values()):
            raise ValueError("aqueous elemental composition cannot be all zero")
        return self


class GeometryAwareReactionDefinition(Contract):
    reaction_id: str = Field(min_length=1)
    # Net stoichiometric coefficients in declared species order; products are positive.
    stoichiometric_coefficients: tuple[float, ...] = Field(min_length=1, max_length=MAX_SPECIES)


class CreviceGeometryAwareAqueousChemistryContract(Contract):
    """Serializable identity, support and conservation declaration for a caller law."""

    schema_version: Literal["matintegrity.crevice_geometry_aware_chemistry.v1"] = (
        "matintegrity.crevice_geometry_aware_chemistry.v1"
    )
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species: tuple[GeometryAwareAqueousSpecies, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    reactions: tuple[GeometryAwareReactionDefinition, ...] = Field(min_length=1, max_length=MAX_REACTIONS)
    valid_time_start_s: float = Field(ge=0)
    valid_time_end_s: float = Field(gt=0)
    minimum_aperture_m: float = Field(gt=0)
    maximum_aperture_m: float = Field(gt=0)
    maximum_concentration_mol_m3_by_species: tuple[float, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    rate_basis: Literal["net_reaction_extent_mol_m3_s"] = "net_reaction_extent_mol_m3_s"
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)
    geometry_dependence_and_path_reviewed: bool
    reaction_order_and_units_reviewed: bool
    element_and_charge_balance_reviewed: bool
    concentration_and_aperture_support_reviewed: bool
    deterministic_callback_reviewed: bool
    inventory_closure_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_provider_contract(self):
        ids = tuple(row.species_id for row in self.species)
        reaction_ids = tuple(row.reaction_id for row in self.reactions)
        if len(set(ids)) != len(ids) or len(set(reaction_ids)) != len(reaction_ids):
            raise ValueError("species and reaction identifiers must be unique")
        if len(self.maximum_concentration_mol_m3_by_species) != len(ids):
            raise ValueError("one concentration upper bound is required per species")
        if any(not math.isfinite(value) or value <= 0 for value in self.maximum_concentration_mol_m3_by_species):
            raise ValueError("concentration support limits must be finite and positive")
        if (
            not math.isfinite(self.valid_time_start_s)
            or not math.isfinite(self.valid_time_end_s)
            or self.valid_time_end_s <= self.valid_time_start_s
            or not math.isfinite(self.minimum_aperture_m)
            or not math.isfinite(self.maximum_aperture_m)
            or self.maximum_aperture_m <= self.minimum_aperture_m
        ):
            raise ValueError("provider time and aperture supports must be finite and ordered")
        for reaction in self.reactions:
            if len(reaction.stoichiometric_coefficients) != len(ids):
                raise ValueError("each reaction coefficient vector must follow the declared species order")
            if any(not math.isfinite(value) for value in reaction.stoichiometric_coefficients):
                raise ValueError("reaction stoichiometry must be finite")
            if not any(value != 0.0 for value in reaction.stoichiometric_coefficients):
                raise ValueError("reaction stoichiometry cannot be all zero")
            charge = math.fsum(
                coefficient * species.charge_number
                for coefficient, species in zip(reaction.stoichiometric_coefficients, self.species, strict=True)
            )
            if not math.isclose(charge, 0.0, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve charge")
            elements = set().union(*(row.elemental_composition for row in self.species))
            for element in elements:
                residual = math.fsum(
                    coefficient * species.elemental_composition.get(element, 0)
                    for coefficient, species in zip(reaction.stoichiometric_coefficients, self.species, strict=True)
                )
                if not math.isclose(residual, 0.0, rel_tol=0.0, abs_tol=1e-12):
                    raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve element {element!r}")
        if not any(
            row.source_id == self.provider_id and row.sha256 == self.source_sha256
            for row in self.evidence
        ):
            raise ValueError("provider source digest must be bound to matching Evidence")
        config = self.configuration_payload()
        if canonical_digest(config) != self.configuration_sha256:
            raise ValueError("provider configuration digest does not match the declared support and reaction basis")
        if not all((
            self.geometry_dependence_and_path_reviewed,
            self.reaction_order_and_units_reviewed,
            self.element_and_charge_balance_reviewed,
            self.concentration_and_aperture_support_reviewed,
            self.deterministic_callback_reviewed,
            self.inventory_closure_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("all provider, support, conservation, determinism and use reviews are required")
        return self

    def configuration_payload(self) -> dict:
        return geometry_aware_chemistry_configuration_payload(
            provider_id=self.provider_id,
            provider_revision=self.provider_revision,
            source_sha256=self.source_sha256,
            species=self.species,
            reactions=self.reactions,
            valid_time_start_s=self.valid_time_start_s,
            valid_time_end_s=self.valid_time_end_s,
            minimum_aperture_m=self.minimum_aperture_m,
            maximum_aperture_m=self.maximum_aperture_m,
            maximum_concentration_mol_m3_by_species=self.maximum_concentration_mol_m3_by_species,
            rate_basis=self.rate_basis,
        )


class GeometryAwareChemistryEvaluationError(ValueError):
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


class CreviceGeometryAwareAqueousChemistryProvider:
    """Bind a caller extent-rate evaluator to one guessed linear aperture segment."""

    def __init__(
        self,
        contract: CreviceGeometryAwareAqueousChemistryContract,
        evaluate_net_extent_rates: Callable[[float, np.ndarray, np.ndarray], np.ndarray],
    ):
        if not callable(evaluate_net_extent_rates):
            raise TypeError("a callable net-reaction extent-rate evaluator is required")
        self.contract = contract
        self.evaluate_net_extent_rates = evaluate_net_extent_rates
        self.provider_id = contract.provider_id
        self.provider_revision = contract.provider_revision
        self.source_sha256 = contract.source_sha256
        self.configuration_sha256 = contract.configuration_sha256
        self.species_ids = tuple(row.species_id for row in contract.species)
        self.source_request_sha256 = canonical_digest(contract.model_dump(mode="json"))
        self._stoichiometry = np.asarray(
            [row.stoichiometric_coefficients for row in contract.reactions], dtype=float
        ).T
        self.reaction_ids = tuple(row.reaction_id for row in contract.reactions)

    def bind_linear_aperture_path(
        self,
        start_time_s: float,
        end_time_s: float,
        start_aperture_m: np.ndarray,
        guessed_end_aperture_m: np.ndarray,
    ) -> Callable[[float, np.ndarray], np.ndarray]:
        contract = self.contract
        start_aperture = np.asarray(start_aperture_m, dtype=float).copy()
        end_aperture = np.asarray(guessed_end_aperture_m, dtype=float).copy()
        if (
            not math.isfinite(start_time_s) or not math.isfinite(end_time_s)
            or end_time_s <= start_time_s
            or start_time_s < contract.valid_time_start_s
            or end_time_s > contract.valid_time_end_s
            or start_aperture.ndim != 1
            or end_aperture.shape != start_aperture.shape
            or len(start_aperture) > MAX_CELLS
            or not np.isfinite(start_aperture).all()
            or not np.isfinite(end_aperture).all()
            or np.any(start_aperture < contract.minimum_aperture_m)
            or np.any(start_aperture > contract.maximum_aperture_m)
            or np.any(end_aperture < contract.minimum_aperture_m)
            or np.any(end_aperture > contract.maximum_aperture_m)
        ):
            raise GeometryAwareChemistryEvaluationError(
                provider_id=self.provider_id,
                elapsed_time_s=start_time_s,
                reason="segment time or guessed aperture path is outside provider support",
            )
        source_digest = self.source_sha256
        config_digest = canonical_digest({
            "provider_configuration_sha256": self.configuration_sha256,
            "start_time_s": start_time_s,
            "end_time_s": end_time_s,
            "start_aperture_m": start_aperture.tolist(),
            "guessed_end_aperture_m": end_aperture.tolist(),
        })

        def reaction(elapsed_time_s: float, concentrations_mol_m3: np.ndarray) -> np.ndarray:
            time_s: float | None = None
            try:
                time_s = float(elapsed_time_s)
                state = np.asarray(concentrations_mol_m3, dtype=float)
                if not math.isfinite(time_s) or time_s < start_time_s or time_s > end_time_s:
                    raise ValueError("reaction time is outside the declared segment/provider clock")
                if state.shape != (len(self.species_ids), len(start_aperture)) or not np.isfinite(state).all() or np.any(state < 0):
                    raise ValueError("concentration state must be finite, nonnegative, and match species/cell order")
                maxima = np.asarray(contract.maximum_concentration_mol_m3_by_species, dtype=float)[:, None]
                if np.any(state > maxima):
                    raise ValueError("concentration state is outside provider support")
                fraction = (time_s - start_time_s) / (end_time_s - start_time_s)
                aperture = start_aperture + fraction * (end_aperture - start_aperture)
                if np.any(aperture < contract.minimum_aperture_m) or np.any(aperture > contract.maximum_aperture_m):
                    raise ValueError("interpolated aperture is outside provider support")
                state.setflags(write=False)
                aperture.setflags(write=False)
                extent_rates = np.asarray(
                    self.evaluate_net_extent_rates(time_s, state, aperture), dtype=float
                )
                expected = (len(self.reaction_ids), len(start_aperture))
                if extent_rates.shape != expected or not np.isfinite(extent_rates).all():
                    raise ValueError("provider extent rates must be finite reaction-by-cell values")
                source = self._stoichiometry @ extent_rates
                if source.shape != state.shape or not np.isfinite(source).all():
                    raise ArithmeticError("stoichiometric aqueous source exceeded finite support")
                source.setflags(write=False)
                return source
            except GeometryAwareChemistryEvaluationError:
                raise
            except Exception as error:
                raise GeometryAwareChemistryEvaluationError(
                    provider_id=self.provider_id,
                    elapsed_time_s=time_s,
                    reason=f"caller chemistry evaluation failed: {type(error).__name__}",
                ) from error

        reaction.provider_id = self.provider_id
        reaction.provider_revision = self.provider_revision
        reaction.configuration_sha256 = config_digest
        reaction.source_request_sha256 = self.source_request_sha256
        reaction.source_sha256 = source_digest
        reaction.species_ids = self.species_ids
        reaction.reaction_ids = self.reaction_ids
        reaction.rate_units = "mol/(m3 s)"
        reaction.interpolation_method = "linear_aperture_path_per_fixed_point_trial"
        return reaction
