"""Multi-record material certificate and caller-requirement reconciliation."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class CertificateRequirementRow(Contract):
    requirement_id: str = Field(min_length=1)
    quantity_kind: Literal["chemistry_mass_fraction", "property_si"]
    quantity_id: str = Field(min_length=1)
    unit_basis: Literal["mass_fraction", "SI"]
    unit_token: str = Field(min_length=1)
    minimum_allowed_value: float | None = None
    maximum_allowed_value: float | None = None
    comparison_policy: Literal["reported_uncertainty_interval_against_requirement"]
    requirement_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_requirement(self):
        if self.minimum_allowed_value is None and self.maximum_allowed_value is None:
            raise ValueError("a certificate requirement needs at least one bound")
        if (
            self.minimum_allowed_value is not None
            and self.maximum_allowed_value is not None
            and self.maximum_allowed_value < self.minimum_allowed_value
        ):
            raise ValueError("certificate requirement bounds must be ordered")
        if self.quantity_kind == "chemistry_mass_fraction":
            if self.unit_basis != "mass_fraction" or self.unit_token != "mass_fraction":
                raise ValueError("chemistry requirements require the exact mass_fraction unit")
            for value in (self.minimum_allowed_value, self.maximum_allowed_value):
                if value is not None and not 0 <= value <= 1:
                    raise ValueError("chemistry requirement bounds must be mass fractions")
        elif self.unit_basis != "SI":
            raise ValueError("property requirements require a caller-declared SI unit basis")
        return self


class CertificateMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    quantity_kind: Literal["chemistry_mass_fraction", "property_si"]
    quantity_id: str = Field(min_length=1)
    unit_basis: Literal["mass_fraction", "SI"]
    unit_token: str = Field(min_length=1)
    reported_value: float
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    method_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_measurement(self):
        if self.quantity_kind == "chemistry_mass_fraction":
            if self.unit_basis != "mass_fraction" or self.unit_token != "mass_fraction":
                raise ValueError("chemistry measurements require the exact mass_fraction unit")
            if not 0 <= self.reported_value <= 1:
                raise ValueError("reported chemistry values must be mass fractions")
        elif self.unit_basis != "SI":
            raise ValueError("property measurements require a caller-declared SI unit basis")
        return self


class MaterialCertificateRecord(Contract):
    record_id: str = Field(min_length=1)
    record_role: Literal["certificate", "independent_test", "supplemental_test"]
    heat_id: str = Field(min_length=1)
    lot_id: str = Field(min_length=1)
    reported_material_identity_id: str = Field(min_length=1)
    alias_resolution_status: Literal["exact", "resolved", "unresolved", "ambiguous"]
    resolved_material_condition_id: str | None = None
    alias_mapping_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    alias_resolution_basis: str = Field(min_length=1)
    physical_sample_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    measurements: tuple[CertificateMeasurement, ...] = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        measurement_ids = [row.measurement_id for row in self.measurements]
        if len(measurement_ids) != len(set(measurement_ids)):
            raise ValueError("certificate measurement identifiers must be unique within a record")
        if self.alias_resolution_status == "resolved":
            if self.resolved_material_condition_id is None or self.alias_mapping_digest is None:
                raise ValueError("resolved aliases require a canonical material condition and mapping digest")
        elif self.alias_resolution_status == "exact":
            if self.resolved_material_condition_id is None:
                raise ValueError("exact material identity requires a resolved material condition")
            if self.alias_mapping_digest is not None:
                raise ValueError("exact material identity cannot carry an alias mapping digest")
        elif self.resolved_material_condition_id is not None or self.alias_mapping_digest is not None:
            raise ValueError("unresolved or ambiguous material identity cannot carry a resolved mapping")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid material certificate record requires a basis")
        return self


class MaterialCertificateReconciliation(Contract):
    reconciliation_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    lot_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    requirement_set_id: str = Field(min_length=1)
    requirement_authority_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    requirements: tuple[CertificateRequirementRow, ...] = Field(min_length=1)
    records: tuple[MaterialCertificateRecord, ...] = Field(min_length=1)
    heat_lot_and_material_condition_reviewed: bool
    alias_resolution_status_and_mapping_reviewed: bool
    requirement_authority_and_bounds_reviewed: bool
    chemistry_mass_fraction_basis_reviewed: bool
    property_si_units_reviewed: bool
    physical_samples_and_source_groups_reviewed: bool
    methods_uncertainties_and_coverage_factors_reviewed: bool
    provider_lineage_and_result_digests_reviewed: bool
    duplicate_contradiction_and_missingness_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_records_and_requirements(self):
        requirement_ids = [row.requirement_id for row in self.requirements]
        requirement_keys = [(row.quantity_kind, row.quantity_id) for row in self.requirements]
        record_ids = [row.record_id for row in self.records]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("certificate requirement identifiers must be unique")
        if len(requirement_keys) != len(set(requirement_keys)):
            raise ValueError("certificate requirement quantity keys must be unique")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("material certificate record identifiers must be unique")
        return self


def _interval_outcome(lower: float, upper: float, requirement: CertificateRequirementRow) -> str:
    minimum = requirement.minimum_allowed_value
    maximum = requirement.maximum_allowed_value
    entirely_within = (minimum is None or lower >= minimum) and (maximum is None or upper <= maximum)
    entirely_outside = (minimum is not None and upper < minimum) or (maximum is not None and lower > maximum)
    if entirely_within:
        return "within_requirement"
    if entirely_outside:
        return "outside_requirement"
    return "uncertainty_overlap"


def certificate_reconciliation(x: MaterialCertificateReconciliation) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "heat_lot_and_material_condition_reviewed",
            "alias_resolution_status_and_mapping_reviewed",
            "requirement_authority_and_bounds_reviewed",
            "chemistry_mass_fraction_basis_reviewed",
            "property_si_units_reviewed",
            "physical_samples_and_source_groups_reviewed",
            "methods_uncertainties_and_coverage_factors_reviewed",
            "provider_lineage_and_result_digests_reviewed",
            "duplicate_contradiction_and_missingness_policy_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_record_ids = [row.record_id for row in x.records if not row.record_valid]
    identity_mismatch_record_ids = [
        row.record_id
        for row in x.records
        if row.heat_id != x.heat_id
        or row.lot_id != x.lot_id
        or row.resolved_material_condition_id != x.material_condition_id
    ]
    unresolved_or_ambiguous_record_ids = [
        row.record_id for row in x.records if row.alias_resolution_status in {"unresolved", "ambiguous"}
    ]
    if (
        missing_reviews
        or invalid_record_ids
        or identity_mismatch_record_ids
        or unresolved_or_ambiguous_record_ids
    ):
        return Calculation(
            status="needs_data",
            values={
                "reconciliation_id": x.reconciliation_id,
                "missing_reviews": missing_reviews,
                "invalid_record_ids": invalid_record_ids,
                "identity_mismatch_record_ids": identity_mismatch_record_ids,
                "unresolved_or_ambiguous_record_ids": unresolved_or_ambiguous_record_ids,
            },
            notes=("Exact heat, lot and reviewed material identity resolution are required.",),
        )

    measurements_by_key: dict[
        tuple[str, str], list[tuple[MaterialCertificateRecord, CertificateMeasurement]]
    ] = {}
    duplicate_rows = []
    for record in x.records:
        within_record: dict[tuple[str, str], list[str]] = {}
        for measurement in record.measurements:
            key = (measurement.quantity_kind, measurement.quantity_id)
            measurements_by_key.setdefault(key, []).append((record, measurement))
            within_record.setdefault(key, []).append(measurement.measurement_id)
        for key, measurement_ids in within_record.items():
            if len(measurement_ids) > 1:
                duplicate_rows.append(
                    {
                        "record_id": record.record_id,
                        "quantity_kind": key[0],
                        "quantity_id": key[1],
                        "measurement_ids": measurement_ids,
                    }
                )

    requirement_results = []
    missing_requirement_ids = []
    contradictory_requirement_ids = []
    unit_mismatch_measurement_ids = []
    outside_requirement_ids = []
    uncertainty_overlap_requirement_ids = []
    for requirement in x.requirements:
        key = (requirement.quantity_kind, requirement.quantity_id)
        linked = measurements_by_key.get(key, [])
        if not linked:
            missing_requirement_ids.append(requirement.requirement_id)
            requirement_results.append(
                {
                    "requirement_id": requirement.requirement_id,
                    "quantity_kind": requirement.quantity_kind,
                    "quantity_id": requirement.quantity_id,
                    "comparison_state": "missing",
                    "measurements": [],
                    "contradictory_measurement_pairs": [],
                }
            )
            continue
        comparisons = []
        comparable_intervals = []
        states = []
        for record, measurement in linked:
            unit_compatible = (
                measurement.unit_basis == requirement.unit_basis
                and measurement.unit_token == requirement.unit_token
            )
            state = "unit_mismatch"
            lower = measurement.reported_value - measurement.expanded_uncertainty
            upper = measurement.reported_value + measurement.expanded_uncertainty
            if unit_compatible:
                state = _interval_outcome(lower, upper, requirement)
                comparable_intervals.append((record.record_id, measurement.measurement_id, lower, upper))
                states.append(state)
            else:
                unit_mismatch_measurement_ids.append(measurement.measurement_id)
            comparisons.append(
                {
                    "record_id": record.record_id,
                    "record_role": record.record_role,
                    "physical_sample_id": record.physical_sample_id,
                    "source_group_id": record.source_group_id,
                    "measurement_id": measurement.measurement_id,
                    "reported_value": measurement.reported_value,
                    "expanded_uncertainty": measurement.expanded_uncertainty,
                    "uncertainty_coverage_factor": measurement.uncertainty_coverage_factor,
                    "unit_token": measurement.unit_token,
                    "uncertainty_interval": [lower, upper],
                    "comparison_state": state,
                }
            )
        contradictory_pairs = []
        for index, first in enumerate(comparable_intervals):
            for second in comparable_intervals[index + 1 :]:
                if first[3] < second[2] or second[3] < first[2]:
                    contradictory_pairs.append(
                        {
                            "first_record_id": first[0],
                            "first_measurement_id": first[1],
                            "second_record_id": second[0],
                            "second_measurement_id": second[1],
                        }
                    )
        if contradictory_pairs:
            comparison_state = "contradictory"
            contradictory_requirement_ids.append(requirement.requirement_id)
        elif any(row["comparison_state"] == "unit_mismatch" for row in comparisons):
            comparison_state = "unit_mismatch"
        elif "outside_requirement" in states:
            comparison_state = "outside_requirement"
            outside_requirement_ids.append(requirement.requirement_id)
        elif "uncertainty_overlap" in states:
            comparison_state = "uncertainty_overlap"
            uncertainty_overlap_requirement_ids.append(requirement.requirement_id)
        else:
            comparison_state = "within_requirement"
        requirement_results.append(
            {
                "requirement_id": requirement.requirement_id,
                "quantity_kind": requirement.quantity_kind,
                "quantity_id": requirement.quantity_id,
                "unit_basis": requirement.unit_basis,
                "unit_token": requirement.unit_token,
                "minimum_allowed_value": requirement.minimum_allowed_value,
                "maximum_allowed_value": requirement.maximum_allowed_value,
                "comparison_state": comparison_state,
                "measurements": comparisons,
                "contradictory_measurement_pairs": contradictory_pairs,
            }
        )
    if unit_mismatch_measurement_ids:
        return Calculation(
            status="needs_data",
            values={
                "reconciliation_id": x.reconciliation_id,
                "unit_mismatch_measurement_ids": sorted(set(unit_mismatch_measurement_ids)),
                "requirement_results": requirement_results,
                "duplicate_measurement_rows": duplicate_rows,
            },
            notes=(
                "Exact chemistry mass-fraction and property SI unit tokens are required; no conversion is inferred.",
            ),
        )

    declared_requirement_outcome = (
        "not_satisfied"
        if outside_requirement_ids
        else "unknown"
        if missing_requirement_ids or contradictory_requirement_ids or uncertainty_overlap_requirement_ids
        else "satisfied"
    )
    return Calculation(
        status="computed",
        values={
            "reconciliation_id": x.reconciliation_id,
            "physical_scope_id": x.physical_scope_id,
            "heat_id": x.heat_id,
            "lot_id": x.lot_id,
            "material_condition_id": x.material_condition_id,
            "requirement_set_id": x.requirement_set_id,
            "requirement_results": requirement_results,
            "duplicate_measurement_rows": duplicate_rows,
            "missing_requirement_ids": missing_requirement_ids,
            "contradictory_requirement_ids": contradictory_requirement_ids,
            "outside_requirement_ids": outside_requirement_ids,
            "uncertainty_overlap_requirement_ids": uncertainty_overlap_requirement_ids,
            "declared_requirement_outcome": declared_requirement_outcome,
        },
        notes=(
            "Duplicate, contradictory, missing and boundary-overlap evidence is preserved rather than collapsed or repaired.",
            "Only caller-supplied requirement rows are compared; no specification table or allowable value is embedded.",
            "The result does not select a material name, establish code acceptance or create failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("certificate reconciliation asset and location must match the run context")

    return [
        ModelSpec(
            "materials.multi_record_certificate_reconciliation",
            MaterialCertificateReconciliation,
            certificate_reconciliation,
            {
                "reconciliation_id": "1",
                "physical_scope_id": "1",
                "heat_id": "1",
                "lot_id": "1",
                "material_condition_id": "1",
                "requirement_set_id": "1",
                "requirement_results": "mixed",
                "duplicate_measurement_rows": "mixed",
                "missing_requirement_ids": "1",
                "contradictory_requirement_ids": "1",
                "outside_requirement_ids": "1",
                "uncertainty_overlap_requirement_ids": "1",
                "declared_requirement_outcome": "1",
            },
            (
                "One exact heat, lot and reviewed material-condition identity applies to every record.",
                "Chemistry mass fractions and property SI quantities remain separate exact unit domains.",
                "Reported expanded-uncertainty intervals are compared only with caller-supplied requirement bounds.",
            ),
            ("authored_multi_record_certificate_requirement_reconciliation",),
            context_validator=same_identity,
        )
    ]
