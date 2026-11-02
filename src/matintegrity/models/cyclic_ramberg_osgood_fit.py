"""Weighted identification of stabilized cyclic Ramberg-Osgood coefficients."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class StabilizedCyclicObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_condition_id: str = Field(min_length=1)
    stress_amplitude: Positive
    stress_unit_token: str = Field(min_length=1)
    total_strain_amplitude: Positive
    strain_unit_token: Literal["1"] = "1"
    plastic_strain_definition: Literal["total_minus_elastic", "explicit_reported"]
    elastic_modulus: Positive | None = None
    elastic_modulus_unit_token: str | None = None
    reported_plastic_strain_amplitude: Positive | None = None
    weight: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def definition_fields(self):
        if self.plastic_strain_definition == "total_minus_elastic":
            if self.elastic_modulus is None or self.elastic_modulus_unit_token is None:
                raise ValueError("derived plastic strain requires elastic modulus and unit")
            if self.reported_plastic_strain_amplitude is not None:
                raise ValueError("derived plastic strain cannot also supply reported plastic strain")
        else:
            if self.reported_plastic_strain_amplitude is None:
                raise ValueError("explicit plastic strain definition requires a reported value")
            if self.elastic_modulus is not None or self.elastic_modulus_unit_token is not None:
                raise ValueError("explicit plastic strain does not use elastic modulus fields")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid cyclic observations require a basis")
        return self


class CyclicRambergOsgoodFit(Contract):
    fit_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    observations: tuple[StabilizedCyclicObservation, ...] = Field(min_length=4)
    minimum_calibration_specimen_count: int = Field(ge=2)
    minimum_calibration_source_group_count: int = Field(ge=2)
    minimum_holdout_specimen_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    material_and_stabilized_cycle_definition_reviewed: bool
    stress_strain_amplitudes_units_and_sign_reviewed: bool
    plastic_strain_definition_and_elastic_modulus_reviewed: bool
    specimen_source_independence_and_partitions_reviewed: bool
    weights_and_record_validity_reviewed: bool
    support_and_no_extrapolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identity_and_partition_contract(self):
        ids = [row.observation_id for row in self.observations]
        if len(set(ids)) != len(ids):
            raise ValueError("cyclic observation IDs must be unique")
        specimens = {}
        groups = {}
        for row in self.observations:
            if row.material_condition_id != self.material_condition_id:
                raise ValueError("all cyclic observations must share the fit material condition")
            for mapping, key, label in (
                (specimens, row.physical_specimen_id, "physical specimen"),
                (groups, row.source_group_id, "source group"),
                (groups, row.independence_group_id, "independence group"),
            ):
                prior = mapping.setdefault(key, row.partition)
                if prior != row.partition:
                    raise ValueError(f"{label} cannot cross calibration and holdout partitions")
        return self


def _plastic_strain(row: StabilizedCyclicObservation) -> float:
    if row.plastic_strain_definition == "explicit_reported":
        return row.reported_plastic_strain_amplitude
    return row.total_strain_amplitude - row.stress_amplitude / row.elastic_modulus


def cyclic_ramberg_osgood_fit(x: CyclicRambergOsgoodFit) -> Calculation:
    review_names = (
        "material_and_stabilized_cycle_definition_reviewed",
        "stress_strain_amplitudes_units_and_sign_reviewed",
        "plastic_strain_definition_and_elastic_modulus_reviewed",
        "specimen_source_independence_and_partitions_reviewed",
        "weights_and_record_validity_reviewed",
        "support_and_no_extrapolation_reviewed",
    )
    missing_reviews = [name for name in review_names if not getattr(x, name)]
    invalid_ids = [row.observation_id for row in x.observations if not row.record_valid]
    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    unit_pairs = {
        (row.stress_unit_token, row.elastic_modulus_unit_token)
        for row in x.observations
        if row.plastic_strain_definition == "total_minus_elastic"
    }
    stress_units = {row.stress_unit_token for row in x.observations}
    mismatched_elastic_unit_ids = [
        row.observation_id
        for row in x.observations
        if row.plastic_strain_definition == "total_minus_elastic"
        and row.elastic_modulus_unit_token != row.stress_unit_token
    ]
    nonpositive_plastic_ids = [row.observation_id for row in x.observations if _plastic_strain(row) <= 0]
    counts_ok = (
        len({r.physical_specimen_id for r in calibration}) >= x.minimum_calibration_specimen_count
        and len({r.source_group_id for r in calibration}) >= x.minimum_calibration_source_group_count
        and len({r.physical_specimen_id for r in holdout}) >= x.minimum_holdout_specimen_count
        and len({r.source_group_id for r in holdout}) >= x.minimum_holdout_source_group_count
    )
    if (
        missing_reviews
        or invalid_ids
        or len(stress_units) != 1
        or len(unit_pairs) > 1
        or mismatched_elastic_unit_ids
        or nonpositive_plastic_ids
        or not counts_ok
    ):
        return Calculation(
            status="needs_data",
            values={
                "fit_id": x.fit_id,
                "missing_reviews": missing_reviews,
                "invalid_observation_ids": invalid_ids,
                "stress_unit_tokens": sorted(stress_units),
                "elastic_modulus_unit_pairs": [list(v) for v in sorted(unit_pairs)],
                "mismatched_elastic_modulus_unit_observation_ids": mismatched_elastic_unit_ids,
                "nonpositive_plastic_strain_observation_ids": nonpositive_plastic_ids,
                "minimum_partition_counts_satisfied": counts_ok,
            },
            notes=(
                "Fit is withheld until definitions, units, partitions and positive plastic amplitudes are complete.",
            ),
        )
    xs = [math.log(_plastic_strain(r)) for r in calibration]
    ys = [math.log(r.stress_amplitude) for r in calibration]
    ws = [r.weight for r in calibration]
    sw = sum(ws)
    xm = sum(w * v for w, v in zip(ws, xs, strict=True)) / sw
    ym = sum(w * v for w, v in zip(ws, ys, strict=True)) / sw
    denominator = sum(w * (v - xm) ** 2 for w, v in zip(ws, xs, strict=True))
    if denominator <= 0:
        return Calculation(
            status="needs_data",
            values={"fit_id": x.fit_id, "reason": "zero calibration log-plastic-strain variance"},
            notes=("At least two distinct calibration plastic-strain amplitudes are required.",),
        )
    n_prime = sum(w * (a - xm) * (b - ym) for w, a, b in zip(ws, xs, ys, strict=True)) / denominator
    if n_prime <= 0:
        return Calculation(
            status="out_of_scope",
            values={"fit_id": x.fit_id, "fitted_cyclic_strain_hardening_exponent": n_prime},
            notes=("The supplied calibration data do not identify a positive Ramberg-Osgood exponent.",),
        )
    log_k = ym - n_prime * xm
    k_prime = math.exp(log_k)
    cmin, cmax = min(_plastic_strain(r) for r in calibration), max(_plastic_strain(r) for r in calibration)
    outside = [r.observation_id for r in holdout if not cmin <= _plastic_strain(r) <= cmax]
    values = {
        "fit_id": x.fit_id,
        "cyclic_strength_coefficient": k_prime,
        "cyclic_strain_hardening_exponent": n_prime,
        "stress_unit_token": next(iter(stress_units)),
        "calibration_plastic_strain_support": [cmin, cmax],
        "outside_support_holdout_observation_ids": outside,
        "calibration_observation_ids": [r.observation_id for r in calibration],
        "holdout_observation_ids": [r.observation_id for r in holdout],
    }
    notes = (
        "Only calibration rows identify K-prime and n-prime; holdout rows never influence the coefficients.",
        "Errors are evaluated in natural-log stress space with caller weights.",
        "No extrapolation, fatigue life, acceptance or failure probability is produced.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    errors = [
        math.log(r.stress_amplitude) - (log_k + n_prime * math.log(_plastic_strain(r))) for r in holdout
    ]
    hw = [r.weight for r in holdout]
    hsw = sum(hw)
    values["holdout_log_stress_bias"] = sum(w * e for w, e in zip(hw, errors, strict=True)) / hsw
    values["holdout_log_stress_rmse"] = math.sqrt(
        sum(w * e * e for w, e in zip(hw, errors, strict=True)) / hsw
    )
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("cyclic fit asset and location must match the run context")

    return [
        ModelSpec(
            "materials.cyclic_ramberg_osgood_fit",
            CyclicRambergOsgoodFit,
            cyclic_ramberg_osgood_fit,
            {
                "fit_id": "1",
                "cyclic_strength_coefficient": "caller_stress_unit",
                "cyclic_strain_hardening_exponent": "1",
                "stress_unit_token": "1",
                "calibration_plastic_strain_support": "1",
                "outside_support_holdout_observation_ids": "1",
                "calibration_observation_ids": "1",
                "holdout_observation_ids": "1",
                "holdout_log_stress_bias": "log(stress)",
                "holdout_log_stress_rmse": "log(stress)",
            },
            (
                "Weighted log-space fit of stabilized cyclic stress amplitude against positive plastic strain amplitude.",
                "Calibration and holdout specimens, source groups and independence groups are disjoint.",
                "The fitted coefficients are restricted to the calibration plastic-strain support.",
            ),
            ("weighted_stabilized_cyclic_ramberg_osgood_fit",),
            context_validator=same_identity,
        )
    ]
