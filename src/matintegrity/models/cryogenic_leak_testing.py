"""Cryogenic thermal-cycle and leak observations with caller-owned envelopes."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class CryogenicThermalCycle(Contract):
    cycle_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pressure_Pa: Nonnegative
    maximum_pressure_Pa: Nonnegative
    temperature_provider_id: str = Field(min_length=1)
    pressure_provider_id: str = Field(min_length=1)
    acquisition_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    thermal_stabilization_basis: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_cycle(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("cryogenic cycle must have positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("cryogenic temperature range must be ordered")
        if self.maximum_pressure_Pa < self.minimum_pressure_Pa:
            raise ValueError("cryogenic pressure range must be ordered")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid cryogenic cycle requires a basis")
        return self


class CryogenicLeakObservation(Contract):
    observation_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    observation_role: Literal["background", "control", "test"]
    method_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    reporting_status: Literal["quantified", "below_detection", "missing"]
    value: Nonnegative | None = None
    expanded_uncertainty: Nonnegative | None = None
    detection_limit: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_fields(self):
        if self.reporting_status == "quantified":
            if self.value is None or self.expanded_uncertainty is None or self.result_digest is None:
                raise ValueError("a quantified leak observation requires value, uncertainty and digest")
        elif self.reporting_status == "below_detection":
            if self.value is not None or self.detection_limit is None or self.result_digest is None:
                raise ValueError("a below-detection leak observation requires only a limit and digest")
        elif (
            self.value is not None
            or self.expanded_uncertainty is not None
            or self.detection_limit is not None
            or self.result_digest is not None
            or not self.missing_basis
        ):
            raise ValueError("a missing leak observation requires a basis and no result fields")
        return self


class DeclaredCryogenicLeakEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    test_medium_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge"]
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive
    minimum_supported_pressure_Pa: Nonnegative
    maximum_supported_pressure_Pa: Nonnegative
    supported_method_ids: tuple[str, ...] = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    maximum_conservative_value: Nonnegative
    minimum_valid_cycles: int = Field(ge=1)
    minimum_test_locations_per_cycle: int = Field(ge=1)
    envelope_provider_id: str = Field(min_length=1)
    envelope_provider_version: str = Field(min_length=1)
    envelope_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    authority_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_supported_temperature_K < self.minimum_supported_temperature_K:
            raise ValueError("cryogenic temperature support must be ordered")
        if self.maximum_supported_pressure_Pa < self.minimum_supported_pressure_Pa:
            raise ValueError("cryogenic pressure support must be ordered")
        if len(set(self.supported_method_ids)) != len(self.supported_method_ids):
            raise ValueError("supported cryogenic leak method IDs must be unique")
        return self


class CryogenicLeakTestAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    test_article_id: str = Field(min_length=1)
    test_medium_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute", "gauge"]
    clock_id: str = Field(min_length=1)
    cycles: tuple[CryogenicThermalCycle, ...] = Field(min_length=1)
    leak_observations: tuple[CryogenicLeakObservation, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DeclaredCryogenicLeakEnvelope, ...] = Field(min_length=1)
    article_and_medium_identity_reviewed: bool
    clock_and_cycle_alignment_reviewed: bool
    temperature_and_pressure_basis_reviewed: bool
    thermal_stabilization_reviewed: bool
    leak_methods_and_locations_reviewed: bool
    uncertainty_and_detection_limits_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_linked_records(self):
        cycle_ids = [row.cycle_id for row in self.cycles]
        observation_ids = [row.observation_id for row in self.leak_observations]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        for values, label in (
            (cycle_ids, "cryogenic cycle"),
            (observation_ids, "cryogenic leak observation"),
            (envelope_ids, "cryogenic leak envelope"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        if {row.cycle_id for row in self.leak_observations} - set(cycle_ids):
            raise ValueError("every cryogenic leak observation must reference a declared cycle")
        ordered = sorted(self.cycles, key=lambda row: row.start_time_s)
        if tuple(ordered) != self.cycles:
            raise ValueError("cryogenic cycles must be supplied in time order")
        if any(
            left.end_time_s > right.start_time_s for left, right in zip(ordered, ordered[1:], strict=False)
        ):
            raise ValueError("cryogenic cycles cannot overlap")
        return self


def cryogenic_leak_test_evidence(x: CryogenicLeakTestAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "article_and_medium_identity_reviewed",
            "clock_and_cycle_alignment_reviewed",
            "temperature_and_pressure_basis_reviewed",
            "thermal_stabilization_reviewed",
            "leak_methods_and_locations_reviewed",
            "uncertainty_and_detection_limits_reviewed",
            "provider_lineage_and_digests_reviewed",
            "envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_cycle_ids = [row.cycle_id for row in x.cycles if not row.record_valid]
    missing_observation_ids = [
        row.observation_id for row in x.leak_observations if row.reporting_status == "missing"
    ]
    identity_matches = [
        row
        for row in x.candidate_envelopes
        if row.test_medium_id == x.test_medium_id and row.pressure_basis == x.pressure_basis
    ]
    if missing_reviews or invalid_cycle_ids or missing_observation_ids or len(identity_matches) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in identity_matches],
                "invalid_cycle_ids": invalid_cycle_ids,
                "missing_observation_ids": missing_observation_ids,
                "missing_reviews": missing_reviews,
            },
            notes=(
                "A unique reviewed envelope and complete valid cycle and observation records are required.",
            ),
        )

    envelope = identity_matches[0]
    cycle_support = []
    outside_cycle_ids = []
    observations_by_cycle = {row.cycle_id: [] for row in x.cycles}
    for observation in x.leak_observations:
        observations_by_cycle[observation.cycle_id].append(observation)
    for cycle in x.cycles:
        within = (
            envelope.minimum_supported_temperature_K <= cycle.minimum_temperature_K
            and cycle.maximum_temperature_K <= envelope.maximum_supported_temperature_K
            and envelope.minimum_supported_pressure_Pa <= cycle.minimum_pressure_Pa
            and cycle.maximum_pressure_Pa <= envelope.maximum_supported_pressure_Pa
        )
        if not within:
            outside_cycle_ids.append(cycle.cycle_id)
        cycle_support.append({"cycle_id": cycle.cycle_id, "within_declared_support": within})

    comparison_rows = []
    definition_mismatch_ids = []
    outside_limit_ids = []
    test_locations_by_cycle: dict[str, set[str]] = {row.cycle_id: set() for row in x.cycles}
    for observation in x.leak_observations:
        exact = (
            observation.method_id in envelope.supported_method_ids
            and observation.metric_id == envelope.metric_id
            and observation.metric_definition == envelope.metric_definition
            and observation.unit_token == envelope.unit_token
        )
        if not exact:
            definition_mismatch_ids.append(observation.observation_id)
        if observation.observation_role == "test" and exact:
            test_locations_by_cycle[observation.cycle_id].add(observation.physical_location_id)
        conservative = (
            observation.value + observation.expanded_uncertainty
            if observation.reporting_status == "quantified"
            else observation.detection_limit
            if observation.reporting_status == "below_detection"
            else None
        )
        within_limit = (
            conservative <= envelope.maximum_conservative_value
            if exact and conservative is not None
            else None
        )
        if within_limit is False:
            outside_limit_ids.append(observation.observation_id)
        comparison_rows.append(
            {
                "observation_id": observation.observation_id,
                "cycle_id": observation.cycle_id,
                "physical_location_id": observation.physical_location_id,
                "observation_role": observation.observation_role,
                "reporting_status": observation.reporting_status,
                "exact_method_metric_and_unit_match": exact,
                "conservative_value": conservative,
                "within_caller_declared_maximum": within_limit,
            }
        )

    insufficient_cycle_ids = [
        cycle_id
        for cycle_id, locations in test_locations_by_cycle.items()
        if len(locations) < envelope.minimum_test_locations_per_cycle
    ]
    complete = (
        len(x.cycles) >= envelope.minimum_valid_cycles
        and not definition_mismatch_ids
        and not insufficient_cycle_ids
    )
    status = "out_of_scope" if outside_cycle_ids else "computed" if complete else "needs_data"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "test_article_id": x.test_article_id,
            "selected_envelope_id": envelope.envelope_id,
            "cycle_count": len(x.cycles),
            "cycle_support": cycle_support,
            "outside_support_cycle_ids": outside_cycle_ids,
            "leak_observation_comparisons": comparison_rows,
            "definition_mismatch_observation_ids": definition_mismatch_ids,
            "insufficient_test_location_cycle_ids": insufficient_cycle_ids,
            "outside_declared_maximum_observation_ids": outside_limit_ids,
            "all_exact_test_observations_within_declared_maximum": (
                not outside_limit_ids if status == "computed" else None
            ),
            "source_group_ids": sorted({row.source_group_id for row in x.leak_observations}),
            "missing_reviews": [],
        },
        notes=(
            "Below-detection observations use the caller-reviewed detection limit as a conservative upper comparison value and are never replaced by zero.",
            "Temperature, pressure, medium, method, metric and unit support are caller-owned and are not extrapolated.",
            "This evidence summary does not identify a leak source, predict service leakage or failure, establish POD, or declare acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("cryogenic leak assessment asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.cryogenic_leak_test_evidence",
            CryogenicLeakTestAssessment,
            cryogenic_leak_test_evidence,
            {
                "assessment_id": "1",
                "test_article_id": "1",
                "selected_envelope_id": "1",
                "cycle_count": "count",
                "cycle_support": "mixed",
                "outside_support_cycle_ids": "1",
                "leak_observation_comparisons": "mixed",
                "definition_mismatch_observation_ids": "1",
                "insufficient_test_location_cycle_ids": "1",
                "outside_declared_maximum_observation_ids": "1",
                "all_exact_test_observations_within_declared_maximum": "1",
                "source_group_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Cycle temperature and pressure extrema, medium identity and pressure basis are reviewed caller records.",
                "Leak method, metric, unit, uncertainty, detection limit and maximum comparison value are caller-owned.",
                "Background, control and test observations retain their declared roles and source groups.",
            ),
            ("reviewed_cryogenic_cycle_leak_evidence",),
            context_validator=same_identity,
        )
    ]
