"""Production hardness campaign evidence assessed only by caller-owned criteria."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class HardnessTestSubject(Contract):
    specimen_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    subject_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HardnessTestConfiguration(Contract):
    method_id: str = Field(min_length=1)
    scale_id: str = Field(min_length=1)
    hardness_unit_token: str = Field(min_length=1)
    applied_load: Positive
    applied_load_unit_token: str = Field(min_length=1)
    dwell_time_s: Positive
    indenter_id: str = Field(min_length=1)
    indenter_definition: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    instrument_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HardnessReferenceBlockEvidence(Contract):
    reference_block_id: str = Field(min_length=1)
    reference_block_condition_id: str = Field(min_length=1)
    scale_id: str = Field(min_length=1)
    certified_value: float
    certified_expanded_uncertainty: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    certificate_id: str = Field(min_length=1)
    certificate_revision: str = Field(min_length=1)
    certificate_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    verification_status: Literal["valid", "invalid", "missing"]
    verification_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def verification_basis(self):
        if self.verification_status != "valid" and not self.invalid_or_missing_basis:
            raise ValueError("invalid or missing hardness reference verification requires a basis")
        return self


class HardnessReading(Contract):
    reading_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    hardness_value: float
    expanded_hardness_uncertainty: Nonnegative
    hardness_unit_token: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    nearest_indent_spacing: Positive
    edge_distance: Positive
    local_thickness: Positive
    geometry_unit_token: str = Field(min_length=1)
    expanded_geometry_uncertainty: Nonnegative
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    caller_validity_status: Literal["valid", "invalid", "unknown"]
    caller_validity_basis: str = Field(min_length=1)
    reading_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HardnessCampaignCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    supported_component_ids: tuple[str, ...] = Field(min_length=1)
    supported_material_ids: tuple[str, ...] = Field(min_length=1)
    supported_material_condition_ids: tuple[str, ...] = Field(min_length=1)
    supported_heat_ids: tuple[str, ...] = Field(min_length=1)
    required_method_id: str = Field(min_length=1)
    required_scale_id: str = Field(min_length=1)
    required_hardness_unit_token: str = Field(min_length=1)
    required_applied_load: Positive
    required_applied_load_unit_token: str = Field(min_length=1)
    required_dwell_time_s: Positive
    dwell_time_tolerance_s: Nonnegative
    required_indenter_id: str = Field(min_length=1)
    required_instrument_id: str = Field(min_length=1)
    required_reference_block_id: str = Field(min_length=1)
    supported_surface_condition_ids: tuple[str, ...] = Field(min_length=1)
    geometry_unit_token: str = Field(min_length=1)
    minimum_indent_spacing: Positive
    minimum_edge_distance: Positive
    minimum_local_thickness: Positive
    minimum_hardness: float | None = None
    maximum_hardness: float | None = None
    minimum_valid_reading_count: int = Field(ge=1)
    minimum_independence_group_count: int = Field(ge=1)
    caller_validity_policy_id: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    built_in_standard_rules_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def profile_bounds(self):
        if self.minimum_hardness is None and self.maximum_hardness is None:
            raise ValueError("hardness campaign profile requires at least one caller hardness bound")
        if (
            self.minimum_hardness is not None
            and self.maximum_hardness is not None
            and self.minimum_hardness > self.maximum_hardness
        ):
            raise ValueError("caller hardness bounds must be ordered")
        return self


class HardnessTestingCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    subjects: tuple[HardnessTestSubject, ...] = Field(min_length=1)
    configuration: HardnessTestConfiguration
    reference_block: HardnessReferenceBlockEvidence
    readings: tuple[HardnessReading, ...] = Field(min_length=1)
    caller_profile: HardnessCampaignCallerProfile
    subject_component_location_material_and_heat_reviewed: bool
    method_scale_load_dwell_indenter_and_instrument_reviewed: bool
    calibration_and_reference_block_reviewed: bool
    surface_spacing_thickness_and_uncertainty_reviewed: bool
    replicate_source_and_independence_groups_reviewed: bool
    caller_validity_flags_and_profile_reviewed: bool
    provenance_and_record_digests_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        for values, label in (
            ([row.specimen_id for row in self.subjects], "subject"),
            ([row.reading_id for row in self.readings], "reading"),
            ([row.sequence_index for row in self.readings], "reading sequence"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"hardness campaign {label} identifiers must be unique")
        if {row.specimen_id for row in self.readings} - {row.specimen_id for row in self.subjects}:
            raise ValueError("hardness readings must reference declared subjects")
        return self


def hardness_testing_campaign(x: HardnessTestingCampaign) -> Calculation:
    profile = x.caller_profile
    missing_reviews = [
        name
        for name in (
            "subject_component_location_material_and_heat_reviewed",
            "method_scale_load_dwell_indenter_and_instrument_reviewed",
            "calibration_and_reference_block_reviewed",
            "surface_spacing_thickness_and_uncertainty_reviewed",
            "replicate_source_and_independence_groups_reviewed",
            "caller_validity_flags_and_profile_reviewed",
            "provenance_and_record_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    subject_mismatches = [
        row.specimen_id
        for row in x.subjects
        if row.component_id not in profile.supported_component_ids
        or row.material_id not in profile.supported_material_ids
        or row.material_condition_id not in profile.supported_material_condition_ids
        or row.heat_id not in profile.supported_heat_ids
        or row.location_id != x.location_id
    ]
    configuration = x.configuration
    configuration_mismatches = [
        name
        for name, actual, expected in (
            ("method_id", configuration.method_id, profile.required_method_id),
            ("scale_id", configuration.scale_id, profile.required_scale_id),
            ("hardness_unit_token", configuration.hardness_unit_token, profile.required_hardness_unit_token),
            ("applied_load", configuration.applied_load, profile.required_applied_load),
            (
                "applied_load_unit_token",
                configuration.applied_load_unit_token,
                profile.required_applied_load_unit_token,
            ),
            ("indenter_id", configuration.indenter_id, profile.required_indenter_id),
            ("instrument_id", configuration.instrument_id, profile.required_instrument_id),
        )
        if actual != expected
    ]
    if abs(configuration.dwell_time_s - profile.required_dwell_time_s) > profile.dwell_time_tolerance_s:
        configuration_mismatches.append("dwell_time_s")
    if (
        x.reference_block.scale_id != profile.required_scale_id
        or x.reference_block.hardness_unit_token != profile.required_hardness_unit_token
    ):
        configuration_mismatches.append("reference_block_scale_or_unit")
    if x.reference_block.reference_block_id != profile.required_reference_block_id:
        configuration_mismatches.append("reference_block_id")
    invalid_readings = [row.reading_id for row in x.readings if row.caller_validity_status != "valid"]
    if (
        missing_reviews
        or subject_mismatches
        or configuration_mismatches
        or x.reference_block.verification_status != "valid"
        or invalid_readings
    ):
        return _result(
            x,
            "insufficient_evidence",
            {
                "missing_reviews": missing_reviews,
                "subject_identity_mismatch_ids": subject_mismatches,
                "configuration_mismatch_fields": configuration_mismatches,
                "reference_block_verification_status": x.reference_block.verification_status,
                "invalid_or_unknown_reading_ids": invalid_readings,
            },
        )

    groups = {row.independence_group_id for row in x.readings}
    if (
        len(x.readings) < profile.minimum_valid_reading_count
        or len(groups) < profile.minimum_independence_group_count
    ):
        return _result(
            x,
            "insufficient_evidence",
            {"valid_reading_count": len(x.readings), "independence_group_count": len(groups)},
        )

    findings = []
    mismatch_ids = []
    for row in x.readings:
        if (
            row.hardness_unit_token != profile.required_hardness_unit_token
            or row.geometry_unit_token != profile.geometry_unit_token
        ):
            mismatch_ids.append(row.reading_id)
            continue
        if row.surface_condition_id not in profile.supported_surface_condition_ids:
            mismatch_ids.append(row.reading_id)
            continue
        for metric, value, uncertainty, minimum, maximum, unit in (
            (
                "hardness",
                row.hardness_value,
                row.expanded_hardness_uncertainty,
                profile.minimum_hardness,
                profile.maximum_hardness,
                row.hardness_unit_token,
            ),
            (
                "indent_spacing",
                row.nearest_indent_spacing,
                row.expanded_geometry_uncertainty,
                profile.minimum_indent_spacing,
                None,
                row.geometry_unit_token,
            ),
            (
                "edge_distance",
                row.edge_distance,
                row.expanded_geometry_uncertainty,
                profile.minimum_edge_distance,
                None,
                row.geometry_unit_token,
            ),
            (
                "local_thickness",
                row.local_thickness,
                row.expanded_geometry_uncertainty,
                profile.minimum_local_thickness,
                None,
                row.geometry_unit_token,
            ),
        ):
            findings.append(
                {
                    "reading_id": row.reading_id,
                    "metric": metric,
                    "value": value,
                    "uncertainty": uncertainty,
                    "unit": unit,
                    "outcome": _interval_outcome(value - uncertainty, value + uncertainty, minimum, maximum),
                }
            )
    if mismatch_ids:
        return _result(
            x,
            "insufficient_evidence",
            {"unit_or_surface_mismatch_reading_ids": mismatch_ids, "criterion_findings": findings},
        )
    outcomes = {row["outcome"] for row in findings}
    outcome = "reject" if "outside" in outcomes else "review" if "boundary_overlap" in outcomes else "accept"
    return _result(
        x,
        outcome,
        {
            "criterion_findings": findings,
            "reading_ids": [row.reading_id for row in x.readings],
            "specimen_ids": [row.specimen_id for row in x.subjects],
            "source_group_ids": sorted({row.source_group_id for row in x.readings}),
            "independence_group_ids": sorted(groups),
        },
    )


def _interval_outcome(lower, upper, minimum, maximum):
    within = (minimum is None or lower >= minimum) and (maximum is None or upper <= maximum)
    outside = (minimum is not None and upper < minimum) or (maximum is not None and lower > maximum)
    return "within" if within else "outside" if outside else "boundary_overlap"


def _result(x, quality_outcome, additions):
    body = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "quality_outcome": quality_outcome,
        "caller_profile_id": x.caller_profile.profile_id,
        "official_scale_conversion_applied": False,
        "standard_validity_rules_applied": False,
        "material_strength_inferred": False,
        "design_acceptance_claim": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        **additions,
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status="needs_data" if quality_outcome == "insufficient_evidence" else "computed",
        values=body,
        notes=(
            "Only exact-scale readings and caller validity flags and criteria are evaluated.",
            "No hardness conversion, bundled validity rule, material-strength inference, design allowable or qualification claim is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("hardness campaign asset and location must match run context")

    return [
        ModelSpec(
            "inspection.hardness_testing_campaign",
            HardnessTestingCampaign,
            hardness_testing_campaign,
            {
                "assessment_id": "1",
                "campaign_id": "1",
                "quality_outcome": "1",
                "caller_profile_id": "1",
                "criterion_findings": "mixed",
                "reading_ids": "1",
                "specimen_ids": "1",
                "source_group_ids": "1",
                "independence_group_ids": "1",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "Subject, material, heat, method, scale, load, dwell, indenter, reference block and instrument identities are exact caller inputs.",
                "Surface, spacing, thickness, readings, uncertainty, provenance and independence groups remain explicit evidence.",
                "Campaign outcomes use caller validity flags and bounds without conversion, strength inference or bundled acceptance rules.",
            ),
            ("authored_hardness_testing_campaign_evidence_audit",),
            context_validator=same_identity,
        )
    ]
