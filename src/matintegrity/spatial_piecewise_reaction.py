"""Caller-specified interval mass-action sources for restricted spatial transport."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import numpy as np
from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

INTERFACE_ID = "integration.spatial_piecewise_mass_action"
SOURCE_ID = "caller_spatial_piecewise_mass_action"


class SpatialReactionInterval(Contract):
    """One contiguous, closed-at-right time interval in seconds."""

    start_time_s: Nonnegative
    end_time_s: Positive

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("reaction interval must have positive duration")
        return self


class SpatialMassActionReaction(Contract):
    """Fixed integer stoichiometry and caller-calibrated interval rate tables."""

    reaction_id: str = Field(min_length=1)
    reactants: dict[str, StrictInt]
    products: dict[str, StrictInt]
    forward_rate_constants: tuple[Nonnegative, ...] = Field(min_length=1)
    reverse_rate_constants: tuple[Nonnegative, ...] = Field(min_length=1)
    forward_rate_constant_unit: str = Field(min_length=1)
    reverse_rate_constant_unit: str = Field(min_length=1)
    calibration_record_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def stoichiometry_and_units(self):
        if (not self.reactants or not self.products or
                any(isinstance(n, bool) or n <= 0 for n in (*self.reactants.values(), *self.products.values()))):
            raise ValueError("reaction sides require positive integer stoichiometry")
        for side, unit in ((self.reactants, self.forward_rate_constant_unit),
                            (self.products, self.reverse_rate_constant_unit)):
            order = sum(side.values())
            expected = "1/s" if order == 1 else f"(mol/m3)^{1-order}/s"
            if unit != expected:
                raise ValueError(f"rate constant for declared concentration basis requires unit token {expected}")
        if not any(row.source_id == self.calibration_record_id and row.sha256 == self.calibration_sha256
                   for row in self.calibration_evidence):
            raise ValueError("calibration Evidence must match the declared record ID and digest")
        return self


class SpatialPiecewiseMassAction(Contract):
    """Reviewed piecewise-constant homogeneous chemistry for species-by-cell states."""

    schema_version: Literal["matintegrity.spatial_piecewise_mass_action.v1"] = "matintegrity.spatial_piecewise_mass_action.v1"
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    network_id: str = Field(min_length=1)
    species_ids: tuple[str, ...] = Field(min_length=1)
    charge_numbers: tuple[StrictInt, ...]
    elemental_composition: dict[str, dict[str, StrictInt]] | None = None
    intervals: tuple[SpatialReactionInterval, ...] = Field(min_length=1)
    reactions: tuple[SpatialMassActionReaction, ...] = Field(min_length=1, max_length=100)
    concentration_activity_approximation_reviewed: bool
    usage_license_id: str = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    computational_use_authorized: bool
    local_only_authorized: bool
    activity_provider_id: str | None = Field(default=None, min_length=1)
    activity_provider_revision: str | None = Field(default=None, min_length=1)
    activity_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_network(self):
        if not self.computational_use_authorized or not self.local_only_authorized:
            raise ValueError("explicit computational-use and local-only authorization are required")
        if not self.concentration_activity_approximation_reviewed:
            raise ValueError("caller review of the concentration/activity approximation is required")
        if len(set(self.species_ids)) != len(self.species_ids) or len(self.charge_numbers) != len(self.species_ids):
            raise ValueError("species IDs and charge numbers must align uniquely")
        if len({r.reaction_id for r in self.reactions}) != len(self.reactions):
            raise ValueError("reaction IDs must be unique")
        if any(len(r.forward_rate_constants) != len(self.intervals) or
               len(r.reverse_rate_constants) != len(self.intervals) for r in self.reactions):
            raise ValueError("each reaction rate table must have one value per interval")
        if any(right.start_time_s != left.end_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True)):
            raise ValueError("reaction intervals must be exactly contiguous; gaps and overlaps are unsupported")
        if (self.activity_provider_id is None) != (self.activity_provider_revision is None) or (
            self.activity_provider_id is None) != (self.activity_configuration_sha256 is None
        ):
            raise ValueError("activity provider identity, revision and configuration digest must be supplied together")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license")
        lookup = dict(zip(self.species_ids, self.charge_numbers, strict=True))
        if self.elemental_composition is not None:
            if set(self.elemental_composition) != set(self.species_ids):
                raise ValueError("elemental composition must cover every species")
            if any(isinstance(v, bool) or not isinstance(v, int) or v < 0
                   for row in self.elemental_composition.values() for v in row.values()):
                raise ValueError("element counts must be nonnegative integers")
        for reaction in self.reactions:
            involved = reaction.reactants.keys() | reaction.products.keys()
            if not involved <= set(lookup):
                raise ValueError("reaction references an undeclared species")
            charge_l = sum(lookup[s] * n for s, n in reaction.reactants.items())
            charge_r = sum(lookup[s] * n for s, n in reaction.products.items())
            if charge_l != charge_r:
                raise ValueError(f"reaction {reaction.reaction_id} does not conserve declared charge")
            if self.elemental_composition is not None:
                elements = set().union(*(self.elemental_composition[s] for s in involved))
                for element in elements:
                    lhs = sum(n * self.elemental_composition[s].get(element, 0) for s, n in reaction.reactants.items())
                    rhs = sum(n * self.elemental_composition[s].get(element, 0) for s, n in reaction.products.items())
                    if lhs != rhs:
                        raise ValueError(f"reaction {reaction.reaction_id} does not conserve declared element {element}")
        return self


def build_spatial_reaction_callback(
    model: SpatialPiecewiseMassAction,
    *,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
) -> Callable[[float, np.ndarray], np.ndarray]:
    """Build a source callback compatible with ``solve_restricted_transport``.

    Interval selection is left-closed/right-open except the final interval,
    whose right endpoint is included. No time extrapolation is performed.
    """
    if (activity_coefficients is None) != (model.activity_provider_id is None):
        raise ValueError("activity callback presence must match pinned activity-provider configuration")
    if activity_coefficients is not None:
        identity = (getattr(activity_coefficients, "provider_id", None),
                    getattr(activity_coefficients, "provider_revision", None),
                    getattr(activity_coefficients, "configuration_sha256", None))
        expected = (model.activity_provider_id, model.activity_provider_revision, model.activity_configuration_sha256)
        if identity != expected:
            raise ValueError("activity callback identity/configuration does not match model pins")
    indices = {name: i for i, name in enumerate(model.species_ids)}
    boundaries = tuple(row.end_time_s for row in model.intervals)

    def source(time_s: float, concentrations: np.ndarray) -> np.ndarray:
        if isinstance(time_s, bool) or not isinstance(time_s, (int, float, np.number)) or not math.isfinite(float(time_s)):
            raise ValueError("reaction callback time must be finite")
        time = float(time_s)
        if time < model.intervals[0].start_time_s or time > model.intervals[-1].end_time_s:
            raise ValueError("reaction callback time is outside declared interval support")
        interval_index = next((i for i, end in enumerate(boundaries) if time < end), len(boundaries) - 1)
        values = np.asarray(concentrations, dtype=float)
        if values.ndim != 2 or values.shape[0] != len(indices) or not np.isfinite(values).all() or np.any(values < 0):
            raise ValueError("concentrations must be finite nonnegative species-by-cell values")
        if activity_coefficients is not None:
            gamma = np.asarray(activity_coefficients(time, values), dtype=float)
            if gamma.shape != values.shape or not np.isfinite(gamma).all() or np.any(gamma <= 0):
                raise ValueError("activity callback must return finite positive coefficients per species and cell")
            values = values * gamma
            if not np.isfinite(values).all():
                raise ValueError("effective concentrations exceed finite numeric support")
        output = np.zeros_like(values)
        for reaction in model.reactions:
            extent_forward = np.full(values.shape[1], reaction.forward_rate_constants[interval_index], dtype=float)
            extent_reverse = np.full(values.shape[1], reaction.reverse_rate_constants[interval_index], dtype=float)
            for name, power in reaction.reactants.items():
                extent_forward *= values[indices[name]] ** power
            for name, power in reaction.products.items():
                extent_reverse *= values[indices[name]] ** power
            extent = extent_forward - extent_reverse
            for name in reaction.reactants.keys() | reaction.products.keys():
                output[indices[name]] += (reaction.products.get(name, 0) - reaction.reactants.get(name, 0)) * extent
        if not np.isfinite(output).all():
            raise ValueError("reaction source exceeds finite numeric support")
        return output

    source.configuration_sha256 = canonical_digest(model.model_dump(mode="json"))
    source.provider_id = model.provider_id
    source.provider_revision = model.provider_revision
    source.network_id = model.network_id
    source.species_ids = model.species_ids
    source.interval_support_s = (model.intervals[0].start_time_s, model.intervals[-1].end_time_s)
    source.activity_provider_id = model.activity_provider_id
    source.activity_provider_revision = model.activity_provider_revision
    source.activity_configuration_sha256 = model.activity_configuration_sha256
    return source


def _registered_evaluator(model: SpatialPiecewiseMassAction) -> Calculation:
    return Calculation(values={
        "model_id": INTERFACE_ID,
        "network_id": model.network_id,
        "provider_id": model.provider_id,
        "provider_revision": model.provider_revision,
        "configuration_sha256": canonical_digest(model.model_dump(mode="json")),
        "species_ids": list(model.species_ids),
        "interval_support_s": [model.intervals[0].start_time_s, model.intervals[-1].end_time_s],
        "interval_count": len(model.intervals),
        "reaction_count": len(model.reactions),
        "callback_signature": "(time_s, species_by_cell_concentration_mol_m3) -> species_by_cell_source_mol_m3_s",
        "callback_contract_ready": True,
        "activity_callback_required": model.activity_provider_id is not None,
        "exclusions": ["kinetics inference", "equilibrium inference", "corrosion or lifetime", "surface kinetics"],
    }, notes=("This contract creates a caller-calibrated callback for restricted spatial transport; it does not infer chemical parameters or material performance.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=INTERFACE_ID,
        input_type=SpatialPiecewiseMassAction,
        evaluator=_registered_evaluator,
        units={"interval_support_s": "s", "reaction_source": "mol/m3/s"},
        assumptions=("Rates, reaction directions, concentration/activity approximation and local-use rights are caller-supplied.", "Interval support is exact and contiguous; no time extrapolation is performed."),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
