"""Coating qualification observations with isolated data partitions and caller limits."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative
from ..registry import ModelSpec


class CoatingQualificationSpecimen(Contract):
    specimen_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    coating_lot_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    exposure_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    evidence: list[Evidence] = Field(min_length=1)


class CoatingQualificationMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_kind: Literal["dry_film_thickness", "adhesion", "user_defined_performance"]
    value: Nonnegative | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    measurement_valid: bool
    missing_or_invalid_basis: str | None = None
    method_id: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def missingness(self):
        if self.value is None:
            if self.expanded_uncertainty is not None or not self.missing_or_invalid_basis:
                raise ValueError("a missing coating value requires a basis and no uncertainty")
        elif self.expanded_uncertainty is None:
            raise ValueError("a reported coating value requires expanded uncertainty")
        if not self.measurement_valid and not self.missing_or_invalid_basis:
            raise ValueError("an invalid coating measurement requires a basis")
        return self


class DeclaredCoatingRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    comparator: Literal["minimum", "maximum"]
    limit_value: Nonnegative
    unit_token: str = Field(min_length=1)
    applicability_description: str = Field(min_length=1)
    authority_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class CoatingQualificationAssessment(Contract):
    qualification_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    protocol_id: str = Field(min_length=1)
    protocol_revision: str = Field(min_length=1)
    specimens: list[CoatingQualificationSpecimen] = Field(min_length=2)
    measurements: list[CoatingQualificationMeasurement] = Field(min_length=1)
    declared_requirements: list[DeclaredCoatingRequirement] = Field(min_length=1)
    specimen_identity_reviewed: bool
    coating_lot_traceability_reviewed: bool
    exposure_identity_reviewed: bool
    measurement_methods_reviewed: bool
    uncertainty_basis_reviewed: bool
    partition_independence_reviewed: bool
    requirement_authority_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_partitions_and_units(self):
        specimen_ids = [item.specimen_id for item in self.specimens]
        measurement_ids = [item.measurement_id for item in self.measurements]
        requirement_ids = [item.requirement_id for item in self.declared_requirements]
        if len(set(specimen_ids)) != len(specimen_ids):
            raise ValueError("coating specimen IDs must be unique")
        if len(set(measurement_ids)) != len(measurement_ids):
            raise ValueError("coating measurement IDs must be unique")
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("coating requirement IDs must be unique")
        if any(item.coating_system_id != self.coating_system_id for item in self.specimens):
            raise ValueError("each specimen must reference the assessed coating system")
        known_specimens = set(specimen_ids)
        if {item.specimen_id for item in self.measurements} - known_specimens:
            raise ValueError("every coating measurement must reference a declared specimen")
        measurement_keys = [(item.specimen_id, item.metric_id) for item in self.measurements]
        if len(set(measurement_keys)) != len(measurement_keys):
            raise ValueError("declare at most one measurement for each specimen and metric")

        partitions_by_group = defaultdict(set)
        for item in self.specimens:
            partitions_by_group[item.source_group_id].add(item.partition)
        leaking = sorted(group for group, partitions in partitions_by_group.items() if len(partitions) > 1)
        if leaking:
            raise ValueError(f"source groups cannot cross calibration and holdout partitions: {leaking}")
        if {item.partition for item in self.specimens} != {"calibration", "holdout"}:
            raise ValueError("both calibration and holdout specimen partitions are required")

        requirement_units = defaultdict(set)
        for item in self.declared_requirements:
            requirement_units[item.metric_id].add(item.unit_token)
        if any(len(units) > 1 for units in requirement_units.values()):
            raise ValueError("requirements for one metric must share an exact unit token")
        for item in self.measurements:
            expected = requirement_units.get(item.metric_id)
            if expected and item.unit_token not in expected:
                raise ValueError("measurement and requirement units must match exactly")
        return self


def _partition_metric_summary(x: CoatingQualificationAssessment) -> dict:
    specimen_partition = {item.specimen_id: item.partition for item in x.specimens}
    grouped = defaultdict(list)
    for item in x.measurements:
        grouped[(specimen_partition[item.specimen_id], item.metric_id, item.unit_token)].append(item)
    summary = {"calibration": [], "holdout": []}
    for (partition, metric_id, unit_token), measurements in sorted(grouped.items()):
        valid = [item for item in measurements if item.measurement_valid and item.value is not None]
        values = [item.value for item in valid]
        summary[partition].append(
            {
                "metric_id": metric_id,
                "unit_token": unit_token,
                "record_count": len(measurements),
                "valid_value_count": len(values),
                "missing_or_invalid_measurement_ids": [
                    item.measurement_id
                    for item in measurements
                    if not item.measurement_valid or item.value is None
                ],
                "mean_valid_value": sum(values) / len(values) if values else None,
                "minimum_valid_value": min(values) if values else None,
                "maximum_valid_value": max(values) if values else None,
            }
        )
    return summary


def coating_qualification_assessment(x: CoatingQualificationAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_identity_reviewed",
            "coating_lot_traceability_reviewed",
            "exposure_identity_reviewed",
            "measurement_methods_reviewed",
            "uncertainty_basis_reviewed",
            "partition_independence_reviewed",
            "requirement_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    specimen_partition = {item.specimen_id: item.partition for item in x.specimens}
    rows = []
    incomplete = []
    for requirement in x.declared_requirements:
        for partition in ("calibration", "holdout"):
            relevant = [
                item
                for item in x.measurements
                if item.metric_id == requirement.metric_id
                and specimen_partition[item.specimen_id] == partition
            ]
            valid = [item for item in relevant if item.measurement_valid and item.value is not None]
            if len(valid) != len(relevant) or not valid:
                incomplete.append(f"{requirement.requirement_id}:{partition}")
            decisions = []
            conservative_values = []
            for item in valid:
                if requirement.comparator == "maximum":
                    conservative = item.value + item.expanded_uncertainty
                    decision = conservative <= requirement.limit_value
                else:
                    conservative = item.value - item.expanded_uncertainty
                    decision = conservative >= requirement.limit_value
                conservative_values.append(conservative)
                decisions.append(decision)
            rows.append(
                {
                    "requirement_id": requirement.requirement_id,
                    "partition": partition,
                    "metric_id": requirement.metric_id,
                    "comparator": requirement.comparator,
                    "limit_value": requirement.limit_value,
                    "unit_token": requirement.unit_token,
                    "valid_comparison_count": len(decisions),
                    "all_valid_measurements_satisfy_declared_requirement": (
                        all(decisions) if decisions and len(valid) == len(relevant) else None
                    ),
                    "governing_conservative_value": (
                        max(conservative_values)
                        if conservative_values and requirement.comparator == "maximum"
                        else min(conservative_values)
                        if conservative_values
                        else None
                    ),
                }
            )
    status = "needs_data" if missing_reviews or incomplete else "computed"
    return Calculation(
        status=status,
        values={
            "qualification_id": x.qualification_id,
            "coating_system_id": x.coating_system_id,
            "protocol_id": x.protocol_id,
            "protocol_revision": x.protocol_revision,
            "specimen_count_by_partition": {
                partition: sum(item.partition == partition for item in x.specimens)
                for partition in ("calibration", "holdout")
            },
            "coating_lot_ids": sorted({item.coating_lot_id for item in x.specimens}),
            "exposure_ids": sorted({item.exposure_id for item in x.specimens}),
            "partition_metric_summaries": _partition_metric_summary(x),
            "declared_requirement_rows": rows,
            "incomplete_requirement_partition_ids": sorted(set(incomplete)),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Calibration and holdout records remain separate; this summary does not fit, tune or select a model.",
            "Requirement limits and applicability are caller-owned and do not become embedded coating acceptance rules.",
            "Observed film thickness, adhesion or performance does not predict service life, field corrosion rate or failure probability.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "fabrication.coating_qualification_assessment",
            CoatingQualificationAssessment,
            coating_qualification_assessment,
            {
                "qualification_id": "1",
                "coating_system_id": "1",
                "protocol_id": "1",
                "protocol_revision": "1",
                "specimen_count_by_partition": "1",
                "coating_lot_ids": "1",
                "exposure_ids": "1",
                "partition_metric_summaries": "mixed",
                "declared_requirement_rows": "mixed",
                "incomplete_requirement_partition_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Specimens and source groups are assigned once to calibration or holdout and cannot cross partitions.",
                "Comparisons use exact unit-token agreement and the caller-provided expanded uncertainty.",
                "No transfer from laboratory exposure to field service is inferred.",
            ),
            ("partitioned_coating_observation_summary",),
        )
    ]
