"""Caller-calibrated erosion-corrosion loss-rate integration within provider support."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec


class ErosionCorrosionInterval(Contract):
    interval_id: str = Field(min_length=1)
    provider_support_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    flow_velocity_m_s: Nonnegative
    particle_loading: Nonnegative
    particle_loading_unit: str = Field(min_length=1)
    particle_size_descriptor: str = Field(min_length=1)
    fluid_chemistry_descriptor: str = Field(min_length=1)
    temperature_K: Positive
    calibrated_net_loss_rate_m_s: Nonnegative
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    provider_state_reviewed: bool
    rate_calibration_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("erosion-corrosion interval must have positive duration")
        return self


class ErosionCorrosionProviderSupport(Contract):
    provider_support_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_model_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_condition_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    minimum_flow_velocity_m_s: Nonnegative
    maximum_flow_velocity_m_s: Nonnegative
    particle_loading_unit: str = Field(min_length=1)
    minimum_particle_loading: Nonnegative
    maximum_particle_loading: Nonnegative
    supported_particle_size_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_fluid_chemistry_descriptors: tuple[str, ...] = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_calibrated_net_loss_rate_m_s: Nonnegative
    maximum_calibrated_net_loss_rate_m_s: Nonnegative
    maximum_cumulative_exposure_s: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        for lower, upper, name in (
            (self.minimum_flow_velocity_m_s, self.maximum_flow_velocity_m_s, "velocity"),
            (self.minimum_particle_loading, self.maximum_particle_loading, "particle loading"),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (
                self.minimum_calibrated_net_loss_rate_m_s,
                self.maximum_calibrated_net_loss_rate_m_s,
                "net loss rate",
            ),
        ):
            if upper < lower:
                raise ValueError(f"{name} provider-support bounds must be ordered")
        for values, name in (
            (self.supported_particle_size_descriptors, "particle size"),
            (self.supported_fluid_chemistry_descriptors, "fluid chemistry"),
        ):
            if len(values) != len(set(values)) or any(not value.strip() for value in values):
                raise ValueError(f"{name} descriptors must be unique and nonblank")
        return self


class ErosionCorrosionLoss(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    geometry_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    intervals: tuple[ErosionCorrosionInterval, ...] = Field(min_length=1)
    provider_support: ErosionCorrosionProviderSupport
    material_geometry_and_location_reviewed: bool
    interval_clock_and_units_reviewed: bool
    flow_particle_and_chemistry_records_reviewed: bool
    provider_identity_and_support_reviewed: bool
    net_loss_rates_reviewed: bool

    @model_validator(mode="after")
    def interval_clock(self):
        identifiers = [interval.interval_id for interval in self.intervals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("erosion-corrosion interval identifiers must be unique")
        for first, second in zip(self.intervals, self.intervals[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("erosion-corrosion intervals must be ordered and cannot overlap")
        return self


def erosion_corrosion_loss(x: ErosionCorrosionLoss) -> Calculation:
    support = x.provider_support
    missing_reviews = [
        name
        for name, reviewed in (
            (
                "material_geometry_and_location",
                x.material_geometry_and_location_reviewed,
            ),
            ("interval_clock_and_units", x.interval_clock_and_units_reviewed),
            (
                "flow_particle_and_chemistry_records",
                x.flow_particle_and_chemistry_records_reviewed,
            ),
            (
                "provider_identity_and_support",
                x.provider_identity_and_support_reviewed,
            ),
            ("net_loss_rates", x.net_loss_rates_reviewed),
        )
        if not reviewed
    ]
    identity_mismatches = []
    for field in ("material_condition_id", "geometry_id", "location_id"):
        if getattr(x, field) != getattr(support, field):
            identity_mismatches.append(field)
    invalid_intervals = [interval.interval_id for interval in x.intervals if not interval.record_valid]
    unreviewed_intervals = [
        interval.interval_id
        for interval in x.intervals
        if not interval.provider_state_reviewed or not interval.rate_calibration_reviewed
    ]
    provider_or_unit_mismatches = []
    for interval in x.intervals:
        fields = []
        if interval.provider_support_id != support.provider_support_id:
            fields.append("provider_support_id")
        if interval.particle_loading_unit != support.particle_loading_unit:
            fields.append("particle_loading_unit")
        if fields:
            provider_or_unit_mismatches.append({"interval_id": interval.interval_id, "fields": fields})
    if (
        missing_reviews
        or identity_mismatches
        or invalid_intervals
        or unreviewed_intervals
        or provider_or_unit_mismatches
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "invalid_interval_ids": invalid_intervals,
                "unreviewed_interval_ids": unreviewed_intervals,
                "provider_or_unit_mismatches": provider_or_unit_mismatches,
            },
            notes=(
                "Loss integration is withheld until interval identity, unit, provider and calibration reviews are complete.",
            ),
        )

    comparisons = []
    outside_ids = []
    cumulative_duration = 0.0
    for interval in x.intervals:
        duration = interval.end_time_s - interval.start_time_s
        cumulative_duration += duration
        unsupported = []
        if (
            not support.minimum_flow_velocity_m_s
            <= interval.flow_velocity_m_s
            <= support.maximum_flow_velocity_m_s
        ):
            unsupported.append("flow_velocity")
        if (
            not support.minimum_particle_loading
            <= interval.particle_loading
            <= support.maximum_particle_loading
        ):
            unsupported.append("particle_loading")
        if interval.particle_size_descriptor not in support.supported_particle_size_descriptors:
            unsupported.append("particle_size_descriptor")
        if interval.fluid_chemistry_descriptor not in support.supported_fluid_chemistry_descriptors:
            unsupported.append("fluid_chemistry_descriptor")
        if not support.minimum_temperature_K <= interval.temperature_K <= support.maximum_temperature_K:
            unsupported.append("temperature")
        if not (
            support.minimum_calibrated_net_loss_rate_m_s
            <= interval.calibrated_net_loss_rate_m_s
            <= support.maximum_calibrated_net_loss_rate_m_s
        ):
            unsupported.append("calibrated_net_loss_rate")
        if unsupported:
            outside_ids.append(interval.interval_id)
        comparisons.append(
            {
                "interval_id": interval.interval_id,
                "duration_s": duration,
                "unsupported_fields": unsupported,
                "within_provider_support": not unsupported,
            }
        )
    duration_supported = cumulative_duration <= support.maximum_cumulative_exposure_s
    base_values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "provider_id": support.provider_id,
        "provider_version": support.provider_version,
        "provider_model_digest": support.provider_model_digest,
        "interval_support_comparisons": comparisons,
        "cumulative_exposure_s": cumulative_duration,
        "cumulative_exposure_within_support": duration_supported,
        "outside_support_interval_ids": outside_ids,
        "provider_state_digests": [interval.provider_state_digest for interval in x.intervals],
    }
    if outside_ids or not duration_supported:
        return Calculation(
            status="out_of_scope",
            values=base_values,
            notes=(
                "At least one reviewed interval is outside provider support; no rate extrapolation or cumulative loss is reported.",
                "Mechanistic erosion-corrosion synergy, CFD wall shear, particle trajectories and geometry evolution are not calculated.",
            ),
        )

    interval_rows = []
    cumulative_loss = 0.0
    for interval in x.intervals:
        duration = interval.end_time_s - interval.start_time_s
        loss = interval.calibrated_net_loss_rate_m_s * duration
        cumulative_loss += loss
        interval_rows.append(
            {
                "interval_id": interval.interval_id,
                "net_loss_rate_m_s": interval.calibrated_net_loss_rate_m_s,
                "thickness_loss_m": loss,
                "cumulative_thickness_loss_m": cumulative_loss,
            }
        )
    base_values.update(
        {
            "interval_loss": interval_rows,
            "cumulative_thickness_loss_m": cumulative_loss,
        }
    )
    return Calculation(
        values=base_values,
        notes=(
            "Piecewise-constant caller-calibrated net loss rates are integrated exactly over recorded intervals.",
            "Mechanistic synergy, CFD wall shear, particle trajectories, local geometry evolution, lifetime and acceptance are not calculated.",
        ),
    )


class ErosionCorrosionRateRecord(Contract):
    """Evidence-linked thickness-loss rate on one declared interval and condition."""

    record_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    start_time_s: Nonnegative
    end_time_s: Positive
    material_condition_id: str = Field(min_length=1)
    fluid_condition_id: str = Field(min_length=1)
    geometry_condition_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    rate_m_s: Nonnegative
    lower_rate_bound_m_s: Nonnegative | None = None
    upper_rate_bound_m_s: Nonnegative | None = None
    rate_basis_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_matches_record(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("rate-record interval must have positive duration")
        if (self.provider_id, self.record_sha256) not in {
            (row.source_id, row.sha256) for row in self.evidence
        }:
            raise ValueError("component rate requires matching provider Evidence and record digest")
        if (self.lower_rate_bound_m_s is None) != (self.upper_rate_bound_m_s is None):
            raise ValueError("deterministic rate bounds must supply both lower and upper values")
        if self.lower_rate_bound_m_s is not None and not (
            self.lower_rate_bound_m_s <= self.rate_m_s <= self.upper_rate_bound_m_s
        ):
            raise ValueError("component point rate must lie inside its declared deterministic bounds")
        return self


class ErosionCorrosionSynergyInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    pure_erosion: ErosionCorrosionRateRecord
    pure_corrosion: ErosionCorrosionRateRecord
    combined_erosion_corrosion: ErosionCorrosionRateRecord
    corrosion_during_erosion: ErosionCorrosionRateRecord | None = None

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("synergy interval must have positive duration")
        return self


class ErosionCorrosionWallThicknessBaseline(Contract):
    """Digest-linked wall measurement and caller minimum-thickness limit."""

    baseline_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    geometry_condition_id: str = Field(min_length=1)
    baseline_time_s: Nonnegative
    measured_thickness_m: Positive
    required_thickness_m: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_matches_baseline(self):
        if (self.provider_id, self.record_sha256) not in {
            (row.source_id, row.sha256) for row in self.evidence
        }:
            raise ValueError("wall-thickness baseline requires matching provider Evidence and record digest")
        return self


class ErosionCorrosionSynergyAssessment(Contract):
    """Rate decomposition under a caller-declared component accounting convention."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    fluid_condition_id: str = Field(min_length=1)
    geometry_condition_id: str = Field(min_length=1)
    rate_basis_id: str = Field(min_length=1)
    intervals: tuple[ErosionCorrosionSynergyInterval, ...] = Field(min_length=1, max_length=100_000)
    wall_thickness_baseline: ErosionCorrosionWallThicknessBaseline | None = None
    matched_conditions_and_rate_basis_reviewed: bool
    component_definitions_and_accounting_convention_reviewed: bool
    interval_clock_and_measurements_reviewed: bool
    evidence_and_usage_rights_reviewed: bool
    computational_use_authorized: bool
    deterministic_rate_bounds_reviewed: bool = False
    wall_thickness_limit_state_reviewed: bool = False

    @model_validator(mode="after")
    def ordered_nonoverlapping_intervals(self):
        ids = [row.interval_id for row in self.intervals]
        if len(ids) != len(set(ids)):
            raise ValueError("synergy interval IDs must be unique")
        if any(right.start_time_s < left.end_time_s for left, right in zip(self.intervals, self.intervals[1:])):
            raise ValueError("synergy intervals must be ordered and nonoverlapping")
        records = [
            record
            for row in self.intervals
            for record in (
                row.pure_erosion,
                row.pure_corrosion,
                row.combined_erosion_corrosion,
                row.corrosion_during_erosion,
            )
            if record is not None
        ]
        if any(record.rate_basis_id != self.rate_basis_id for record in records):
            raise ValueError("component rates must use the declared common rate basis")
        return self


def erosion_corrosion_synergy_decomposition(x: ErosionCorrosionSynergyAssessment) -> Calculation:
    """Integrate pure and combined loss and preserve their signed residual interaction."""
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "material_condition_id": x.material_condition_id,
        "fluid_condition_id": x.fluid_condition_id,
        "geometry_condition_id": x.geometry_condition_id,
        "time_basis_id": x.time_basis_id,
        "rate_basis_id": x.rate_basis_id,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "accounting_convention": "combined = pure_erosion + pure_corrosion + residual_synergy",
    }
    missing = [
        name for name, reviewed in (
            ("matched_conditions_and_rate_basis_reviewed", x.matched_conditions_and_rate_basis_reviewed),
            ("component_definitions_and_accounting_convention_reviewed", x.component_definitions_and_accounting_convention_reviewed),
            ("interval_clock_and_measurements_reviewed", x.interval_clock_and_measurements_reviewed),
            ("evidence_and_usage_rights_reviewed", x.evidence_and_usage_rights_reviewed),
            ("computational_use_authorized", x.computational_use_authorized),
        ) if not reviewed
    ]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    identity_mismatches = []
    for interval in x.intervals:
        for record in (
            interval.pure_erosion,
            interval.pure_corrosion,
            interval.combined_erosion_corrosion,
            interval.corrosion_during_erosion,
        ):
            if record is None:
                continue
            fields = [
                field
                for field in (
                    "material_condition_id",
                    "fluid_condition_id",
                    "geometry_condition_id",
                    "physical_scope_id",
                    "location_id",
                )
                if getattr(record, field) != getattr(x, field)
            ]
            if fields:
                identity_mismatches.append({"interval_id": interval.interval_id, "record_id": record.record_id, "fields": fields})
            if (record.start_time_s, record.end_time_s) != (interval.start_time_s, interval.end_time_s):
                identity_mismatches.append({
                    "interval_id": interval.interval_id,
                    "record_id": record.record_id,
                    "fields": ["record_time_interval"],
                })
    if identity_mismatches:
        return Calculation(status="needs_data", values=base | {"component_identity_mismatches": identity_mismatches})

    wall_baseline = x.wall_thickness_baseline
    wall_limit_state_issues = []
    if wall_baseline is not None:
        if not x.wall_thickness_limit_state_reviewed:
            wall_limit_state_issues.append("wall_thickness_limit_state_reviewed")
        for field in (
            "asset_id",
            "location_id",
            "physical_scope_id",
            "material_condition_id",
            "geometry_condition_id",
        ):
            if getattr(wall_baseline, field) != getattr(x, field):
                wall_limit_state_issues.append(f"baseline_{field}_mismatch")
        if x.intervals[0].start_time_s != wall_baseline.baseline_time_s:
            wall_limit_state_issues.append("first_interval_does_not_start_at_thickness_baseline")
        gaps = [
            {"left_interval_id": left.interval_id, "right_interval_id": right.interval_id}
            for left, right in zip(x.intervals, x.intervals[1:])
            if right.start_time_s != left.end_time_s
        ]
        if gaps:
            wall_limit_state_issues.append("uncovered_time_between_loss_intervals")
    wall_limit_state_ready = wall_baseline is not None and not wall_limit_state_issues

    cumulative = {
        "pure_erosion_loss_m": 0.0,
        "pure_corrosion_loss_m": 0.0,
        "combined_loss_m": 0.0,
        "residual_synergy_loss_m": 0.0,
    }
    partitioned = all(row.corrosion_during_erosion is not None for row in x.intervals)
    accumulated_partition = {
        "corrosion_accelerated_erosion_loss_m": 0.0,
        "erosion_accelerated_corrosion_loss_m": 0.0,
    }
    rows = []
    bound_totals = {
        "pure_erosion_loss_lower_bound_m": 0.0,
        "pure_erosion_loss_upper_bound_m": 0.0,
        "pure_corrosion_loss_lower_bound_m": 0.0,
        "pure_corrosion_loss_upper_bound_m": 0.0,
        "combined_loss_lower_bound_m": 0.0,
        "combined_loss_upper_bound_m": 0.0,
        "residual_synergy_loss_lower_bound_m": 0.0,
        "residual_synergy_loss_upper_bound_m": 0.0,
    }
    all_residual_bounds_available = True
    first_point_limit_crossing = None
    first_possible_limit_crossing = None
    first_definite_limit_crossing = None
    for interval in x.intervals:
        duration = interval.end_time_s - interval.start_time_s
        e0 = interval.pure_erosion.rate_m_s
        c0 = interval.pure_corrosion.rate_m_s
        total = interval.combined_erosion_corrosion.rate_m_s
        residual = total - e0 - c0
        values = {
            "pure_erosion_loss_m": e0 * duration,
            "pure_corrosion_loss_m": c0 * duration,
            "combined_loss_m": total * duration,
            "residual_synergy_loss_m": residual * duration,
        }
        result_row = {
            "interval_id": interval.interval_id,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": duration,
            "pure_erosion_rate_m_s": e0,
            "pure_corrosion_rate_m_s": c0,
            "combined_rate_m_s": total,
            "residual_synergy_rate_m_s": residual,
            "component_lineage": {
                key: {
                    "record_id": record.record_id,
                    "provider_id": record.provider_id,
                    "provider_revision": record.provider_revision,
                    "record_sha256": record.record_sha256,
                    "material_condition_id": record.material_condition_id,
                    "fluid_condition_id": record.fluid_condition_id,
                    "geometry_condition_id": record.geometry_condition_id,
                    "physical_scope_id": record.physical_scope_id,
                    "location_id": record.location_id,
                }
                for key, record in (
                    ("pure_erosion", interval.pure_erosion),
                    ("pure_corrosion", interval.pure_corrosion),
                    ("combined", interval.combined_erosion_corrosion),
                )
            },
        }
        if wall_limit_state_ready:
            initial_margin = (
                wall_baseline.measured_thickness_m - wall_baseline.required_thickness_m
            )
            point_margin = (
                initial_margin
                - (cumulative["combined_loss_m"] + values["combined_loss_m"])
            )
            if not math.isfinite(point_margin):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "wall_thickness_limit_state_margin_exceeded_finite_numeric_support",
                    "interval_id": interval.interval_id,
                })
            result_row.update({
                "wall_thickness_baseline_id": wall_baseline.baseline_id,
                "wall_thickness_baseline_provider_id": wall_baseline.provider_id,
                "wall_thickness_baseline_record_sha256": wall_baseline.record_sha256,
                "initial_remaining_thickness_limit_state_margin_m": initial_margin,
                "initial_state_at_or_below_required_thickness": initial_margin <= 0.0,
                "remaining_thickness_limit_state_margin_m": point_margin,
                "point_margin_at_or_below_limit": point_margin <= 0.0,
            })
            if point_margin <= 0.0 and first_point_limit_crossing is None:
                first_point_limit_crossing = {
                    "interval_id": interval.interval_id,
                    "start_time_s": interval.start_time_s,
                    "end_time_s": interval.end_time_s,
                    "basis": "caller_point_rates",
                }
        core_records = (interval.pure_erosion, interval.pure_corrosion, interval.combined_erosion_corrosion)
        has_core_bounds = all(record.lower_rate_bound_m_s is not None for record in core_records)
        if has_core_bounds and x.deterministic_rate_bounds_reviewed:
            erosion_low = interval.pure_erosion.lower_rate_bound_m_s
            erosion_high = interval.pure_erosion.upper_rate_bound_m_s
            corrosion_low = interval.pure_corrosion.lower_rate_bound_m_s
            corrosion_high = interval.pure_corrosion.upper_rate_bound_m_s
            total_low = interval.combined_erosion_corrosion.lower_rate_bound_m_s
            total_high = interval.combined_erosion_corrosion.upper_rate_bound_m_s
            residual_low = total_low - erosion_high - corrosion_high
            residual_high = total_high - erosion_low - corrosion_low
            bound_values = {
                "pure_erosion_loss_lower_bound_m": erosion_low * duration,
                "pure_erosion_loss_upper_bound_m": erosion_high * duration,
                "pure_corrosion_loss_lower_bound_m": corrosion_low * duration,
                "pure_corrosion_loss_upper_bound_m": corrosion_high * duration,
                "combined_loss_lower_bound_m": total_low * duration,
                "combined_loss_upper_bound_m": total_high * duration,
                "residual_synergy_rate_lower_bound_m_s": residual_low,
                "residual_synergy_rate_upper_bound_m_s": residual_high,
                "residual_synergy_loss_lower_bound_m": residual_low * duration,
                "residual_synergy_loss_upper_bound_m": residual_high * duration,
            }
            if not all(math.isfinite(value) for value in bound_values.values()):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "deterministic_uncertainty_interval_exceeded_finite_numeric_support",
                    "interval_id": interval.interval_id,
                })
            result_row.update(bound_values)
            for key in bound_totals:
                bound_totals[key] += bound_values[key]
            if wall_limit_state_ready and all_residual_bounds_available:
                loss_lower = bound_totals["combined_loss_lower_bound_m"]
                loss_upper = bound_totals["combined_loss_upper_bound_m"]
                margin_lower = (
                    wall_baseline.measured_thickness_m
                    - wall_baseline.required_thickness_m
                    - loss_upper
                )
                margin_upper = (
                    wall_baseline.measured_thickness_m
                    - wall_baseline.required_thickness_m
                    - loss_lower
                )
                if not math.isfinite(margin_lower) or not math.isfinite(margin_upper):
                    return Calculation(status="out_of_scope", values=base | {
                        "reason": "wall_thickness_limit_state_bound_exceeded_finite_numeric_support",
                        "interval_id": interval.interval_id,
                    })
                if margin_lower <= 0.0 and first_possible_limit_crossing is None:
                    first_possible_limit_crossing = {
                        "interval_id": interval.interval_id,
                        "start_time_s": interval.start_time_s,
                        "end_time_s": interval.end_time_s,
                        "basis": "deterministic_margin_lower_bound_at_or_below_zero",
                    }
                if margin_upper <= 0.0 and first_definite_limit_crossing is None:
                    first_definite_limit_crossing = {
                        "interval_id": interval.interval_id,
                        "start_time_s": interval.start_time_s,
                        "end_time_s": interval.end_time_s,
                        "basis": "deterministic_margin_upper_bound_at_or_below_zero",
                    }
                result_row.update({
                    "remaining_thickness_margin_lower_bound_m": margin_lower,
                    "remaining_thickness_margin_upper_bound_m": margin_upper,
                    "deterministic_limit_state_classification": (
                        "entire_interval_at_or_below_limit"
                        if margin_upper <= 0.0
                        else "entire_interval_above_limit"
                        if margin_lower > 0.0
                        else "interval_overlaps_limit"
                    ),
                })
        else:
            all_residual_bounds_available = False
        if interval.corrosion_during_erosion is not None:
            cw = interval.corrosion_during_erosion.rate_m_s
            ew = total - cw
            if ew < 0.0:
                return Calculation(status="needs_data", values=base | {
                    "reason": "corrosion_during_erosion_rate_exceeds_combined_rate",
                    "interval_id": interval.interval_id,
                })
            ec = ew - e0
            ce = cw - c0
            values["corrosion_accelerated_erosion_loss_m"] = ec * duration
            values["erosion_accelerated_corrosion_loss_m"] = ce * duration
            result_row.update({
                "corrosion_during_erosion_rate_m_s": cw,
                "erosion_during_erosion_corrosion_rate_m_s": ew,
                "corrosion_accelerated_erosion_rate_m_s": ec,
                "erosion_accelerated_corrosion_rate_m_s": ce,
                "partitioned_synergy_rate_m_s": ec + ce,
                "corrosion_during_erosion_lineage": {
                    "record_id": interval.corrosion_during_erosion.record_id,
                    "provider_id": interval.corrosion_during_erosion.provider_id,
                    "provider_revision": interval.corrosion_during_erosion.provider_revision,
                    "record_sha256": interval.corrosion_during_erosion.record_sha256,
                    "material_condition_id": interval.corrosion_during_erosion.material_condition_id,
                    "fluid_condition_id": interval.corrosion_during_erosion.fluid_condition_id,
                    "geometry_condition_id": interval.corrosion_during_erosion.geometry_condition_id,
                    "physical_scope_id": interval.corrosion_during_erosion.physical_scope_id,
                    "location_id": interval.corrosion_during_erosion.location_id,
                },
            })
            partition_records = (*core_records, interval.corrosion_during_erosion)
            if x.deterministic_rate_bounds_reviewed and all(
                record.lower_rate_bound_m_s is not None for record in partition_records
            ):
                cw_record = interval.corrosion_during_erosion
                ce_low = cw_record.lower_rate_bound_m_s - interval.pure_corrosion.upper_rate_bound_m_s
                ce_high = cw_record.upper_rate_bound_m_s - interval.pure_corrosion.lower_rate_bound_m_s
                ec_low = (
                    interval.combined_erosion_corrosion.lower_rate_bound_m_s
                    - cw_record.upper_rate_bound_m_s
                    - interval.pure_erosion.upper_rate_bound_m_s
                )
                ec_high = (
                    interval.combined_erosion_corrosion.upper_rate_bound_m_s
                    - cw_record.lower_rate_bound_m_s
                    - interval.pure_erosion.lower_rate_bound_m_s
                )
                partition_bounds = {
                    "erosion_accelerated_corrosion_rate_lower_bound_m_s": ce_low,
                    "erosion_accelerated_corrosion_rate_upper_bound_m_s": ce_high,
                    "corrosion_accelerated_erosion_rate_lower_bound_m_s": ec_low,
                    "corrosion_accelerated_erosion_rate_upper_bound_m_s": ec_high,
                    "erosion_accelerated_corrosion_loss_lower_bound_m": ce_low * duration,
                    "erosion_accelerated_corrosion_loss_upper_bound_m": ce_high * duration,
                    "corrosion_accelerated_erosion_loss_lower_bound_m": ec_low * duration,
                    "corrosion_accelerated_erosion_loss_upper_bound_m": ec_high * duration,
                }
                if not all(math.isfinite(value) for value in partition_bounds.values()):
                    return Calculation(status="out_of_scope", values=base | {
                        "reason": "partitioned_uncertainty_interval_exceeded_finite_numeric_support",
                        "interval_id": interval.interval_id,
                    })
                result_row.update(partition_bounds)
            accumulated_partition["corrosion_accelerated_erosion_loss_m"] += values[
                "corrosion_accelerated_erosion_loss_m"
            ]
            accumulated_partition["erosion_accelerated_corrosion_loss_m"] += values[
                "erosion_accelerated_corrosion_loss_m"
            ]
        if any(not math.isfinite(value) for value in values.values()):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "integrated_component_loss_exceeded_finite_numeric_support",
                "interval_id": interval.interval_id,
            })
        for key in cumulative:
            cumulative[key] += values[key]
        if not all(math.isfinite(value) for value in (*cumulative.values(), *accumulated_partition.values())):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "cumulative_component_loss_exceeded_finite_numeric_support",
                "interval_id": interval.interval_id,
            })
        if has_core_bounds and x.deterministic_rate_bounds_reviewed and not all(
            math.isfinite(value) for value in bound_totals.values()
        ):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "cumulative_uncertainty_interval_exceeded_finite_numeric_support",
                "interval_id": interval.interval_id,
            })
        result_row.update(values)
        rows.append(result_row)

    return Calculation(values=base | {
        "interval_results": rows,
        "cumulative_component_losses": cumulative | (accumulated_partition if partitioned else {}),
        "partitioned_synergy_available_for_all_intervals": partitioned,
        "deterministic_rate_bounds_interpretation": (
            "Caller-declared finite endpoints propagated by interval arithmetic; not a probability or confidence interval."
        ),
        "deterministic_rate_bounds_status": (
            "computed"
            if all_residual_bounds_available and x.deterministic_rate_bounds_reviewed
            else "needs_data"
            if any(
                record.lower_rate_bound_m_s is not None
                for interval in x.intervals
                for record in (
                    interval.pure_erosion,
                    interval.pure_corrosion,
                    interval.combined_erosion_corrosion,
                    interval.corrosion_during_erosion,
                )
                if record is not None
            )
            else "not_supplied"
        ),
        "cumulative_deterministic_loss_bounds": (
            bound_totals if all_residual_bounds_available and x.deterministic_rate_bounds_reviewed else None
        ),
        "wall_thickness_limit_state": (
            {
                "status": "computed",
                "baseline_id": wall_baseline.baseline_id,
                "baseline_provider_id": wall_baseline.provider_id,
                "baseline_provider_revision": wall_baseline.provider_revision,
                "baseline_record_sha256": wall_baseline.record_sha256,
                "baseline_time_s": wall_baseline.baseline_time_s,
                "measured_thickness_m": wall_baseline.measured_thickness_m,
                "required_thickness_m": wall_baseline.required_thickness_m,
                "initial_remaining_thickness_limit_state_margin_m": (
                    wall_baseline.measured_thickness_m - wall_baseline.required_thickness_m
                ),
                "initial_state_at_or_below_required_thickness": (
                    wall_baseline.measured_thickness_m <= wall_baseline.required_thickness_m
                ),
                "bounds_status": (
                    "computed"
                    if all_residual_bounds_available and x.deterministic_rate_bounds_reviewed
                    else "not_available_for_complete_interval_history"
                ),
                "deterministic_bounds_complete_across_recorded_history": (
                    all_residual_bounds_available and x.deterministic_rate_bounds_reviewed
                ),
                "interpretation": "Deterministic margin to caller-required wall thickness; no failure probability, FTA event probability, code acceptance or remaining-life estimate is inferred.",
                "first_point_limit_crossing_interval": first_point_limit_crossing,
                "first_possible_limit_crossing_interval": first_possible_limit_crossing,
                "first_definite_limit_crossing_interval": first_definite_limit_crossing,
                "crossing_times_are_interval_brackets_not_interpolated_roots": True,
            }
            if wall_limit_state_ready
            else {
                "status": "not_requested" if wall_baseline is None else "needs_data",
                "issues": wall_limit_state_issues,
            }
        ),
        "rate_unit": "m/s",
        "loss_unit": "m",
        "interpretation": "Residual synergy is signed combined loss minus the two supplied pure-process losses; optional partition uses measured corrosion rate during erosion.",
    }, notes=(
        "Piecewise-constant caller-supplied component rates are integrated only on recorded intervals.",
        "Negative interaction is preserved; the decomposition does not infer mechanism or qualify a material.",
    ))


def _validate_synergy_context(x: ErosionCorrosionSynergyAssessment, context: RunContext) -> None:
    if (x.asset_id, x.location_id, x.time_basis_id) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("erosion-corrosion context must match the pinned asset, location and time basis")


def specifications():
    return [
        ModelSpec(
            "degradation.erosion_corrosion_loss",
            ErosionCorrosionLoss,
            erosion_corrosion_loss,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "provider_id": "1",
                "provider_version": "1",
                "provider_model_digest": "1",
                "interval_support_comparisons": "1",
                "cumulative_exposure_s": "s",
                "cumulative_exposure_within_support": "1",
                "outside_support_interval_ids": "1",
                "provider_state_digests": "1",
                "interval_loss": "1",
                "cumulative_thickness_loss_m": "m",
            },
            (
                "Net thickness-loss rates are externally calibrated, reviewed and constant within each interval.",
                "Material, geometry and physical location match one immutable provider support record.",
                "Flow, particles, chemistry and temperature are support coordinates, not mechanistic model inputs.",
            ),
            ("caller_calibrated_erosion_corrosion_loss_rate",),
        ),
        ModelSpec(
            "degradation.erosion_corrosion_synergy_decomposition",
            ErosionCorrosionSynergyAssessment,
            erosion_corrosion_synergy_decomposition,
            {
                "interval_results[].duration_s": "s",
                "interval_results[].pure_erosion_rate_m_s": "m/s",
                "interval_results[].pure_corrosion_rate_m_s": "m/s",
                "interval_results[].combined_rate_m_s": "m/s",
                "interval_results[].residual_synergy_rate_m_s": "m/s",
                "interval_results[].pure_erosion_loss_m": "m",
                "interval_results[].pure_corrosion_loss_m": "m",
                "interval_results[].combined_loss_m": "m",
                "interval_results[].residual_synergy_loss_m": "m",
                "interval_results[].residual_synergy_rate_lower_bound_m_s": "m/s",
                "interval_results[].residual_synergy_rate_upper_bound_m_s": "m/s",
                "interval_results[].pure_erosion_loss_lower_bound_m": "m",
                "interval_results[].pure_erosion_loss_upper_bound_m": "m",
                "interval_results[].pure_corrosion_loss_lower_bound_m": "m",
                "interval_results[].pure_corrosion_loss_upper_bound_m": "m",
                "interval_results[].combined_loss_lower_bound_m": "m",
                "interval_results[].combined_loss_upper_bound_m": "m",
                "interval_results[].residual_synergy_loss_lower_bound_m": "m",
                "interval_results[].residual_synergy_loss_upper_bound_m": "m",
                "interval_results[].erosion_accelerated_corrosion_rate_lower_bound_m_s": "m/s",
                "interval_results[].erosion_accelerated_corrosion_rate_upper_bound_m_s": "m/s",
                "interval_results[].corrosion_accelerated_erosion_rate_lower_bound_m_s": "m/s",
                "interval_results[].corrosion_accelerated_erosion_rate_upper_bound_m_s": "m/s",
                "interval_results[].erosion_accelerated_corrosion_loss_lower_bound_m": "m",
                "interval_results[].erosion_accelerated_corrosion_loss_upper_bound_m": "m",
                "interval_results[].corrosion_accelerated_erosion_loss_lower_bound_m": "m",
                "interval_results[].corrosion_accelerated_erosion_loss_upper_bound_m": "m",
                "interval_results[].remaining_thickness_limit_state_margin_m": "m",
                "interval_results[].remaining_thickness_margin_lower_bound_m": "m",
                "interval_results[].remaining_thickness_margin_upper_bound_m": "m",
                "wall_thickness_limit_state.measured_thickness_m": "m",
                "wall_thickness_limit_state.required_thickness_m": "m",
                "wall_thickness_limit_state.initial_remaining_thickness_limit_state_margin_m": "m",
                "wall_thickness_limit_state.baseline_time_s": "s",
                "wall_thickness_limit_state.first_point_limit_crossing_interval.start_time_s": "s",
                "wall_thickness_limit_state.first_point_limit_crossing_interval.end_time_s": "s",
                "wall_thickness_limit_state.first_possible_limit_crossing_interval.start_time_s": "s",
                "wall_thickness_limit_state.first_possible_limit_crossing_interval.end_time_s": "s",
                "wall_thickness_limit_state.first_definite_limit_crossing_interval.start_time_s": "s",
                "wall_thickness_limit_state.first_definite_limit_crossing_interval.end_time_s": "s",
                "cumulative_component_losses": "m",
                "cumulative_deterministic_loss_bounds": "m",
            },
            (
                "Pure erosion, pure corrosion and combined loss are caller-supplied matched observations; residual synergy is their signed arithmetic difference.",
                "Optional interaction partition requires a separately supplied corrosion rate measured during erosion; no mechanism, prediction, probability or acceptance is inferred.",
                "Optional rate endpoint propagation is deterministic interval arithmetic, not a confidence or probability interval.",
                "An optional digest-linked wall thickness limit state reports deterministic margins only, not failure probability or code acceptance.",
            ),
            (
                "caller_erosion_corrosion_component_accounting",
                "erosion_corrosion_1996_electrochemical_measurements",
                "erosion_corrosion_wall_limit_state_link",
            ),
            context_validator=_validate_synergy_context,
        ),
    ]
