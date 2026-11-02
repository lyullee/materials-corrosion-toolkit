"""Caller-profile audit of reported tensile campaign results without curve recomputation."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

TensileMetric = Literal[
    "elastic_modulus",
    "offset_yield_strength",
    "ultimate_tensile_strength",
    "elongation",
    "reduction_of_area",
]


class TensileSpecimenIdentity(Contract):
    specimen_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    initial_gauge_length: Positive
    initial_cross_section_area: Positive
    geometry_unit_token: str = Field(min_length=1)
    area_unit_token: str = Field(min_length=1)
    specimen_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class TensileMachineConfiguration(Contract):
    machine_id: str = Field(min_length=1)
    machine_revision: str = Field(min_length=1)
    load_cell_id: str = Field(min_length=1)
    load_cell_revision: str = Field(min_length=1)
    extensometer_id: str = Field(min_length=1)
    extensometer_revision: str = Field(min_length=1)
    machine_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    load_cell_calibration_id: str = Field(min_length=1)
    load_cell_calibration_status: Literal["valid", "invalid", "missing"]
    load_cell_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    extensometer_calibration_id: str = Field(min_length=1)
    extensometer_calibration_status: Literal["valid", "invalid", "missing"]
    extensometer_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def calibration_basis(self):
        if (
            "valid" not in {self.load_cell_calibration_status, self.extensometer_calibration_status}
            or self.load_cell_calibration_status != "valid"
            or self.extensometer_calibration_status != "valid"
        ) and not self.invalid_or_missing_basis:
            raise ValueError("invalid or missing tensile calibration requires a basis")
        return self


class TensileReportedResult(Contract):
    result_id: str = Field(min_length=1)
    metric: TensileMetric
    metric_definition: str = Field(min_length=1)
    status: Literal["reported", "missing", "invalid"]
    value: Nonnegative | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    result_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_result(self):
        if self.status == "reported":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("reported tensile results require value and uncertainty")
        elif self.value is not None or self.expanded_uncertainty is not None:
            raise ValueError("missing or invalid tensile results cannot carry numeric values")
        elif not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid tensile results require a basis")
        return self


class TensileTestRecord(Contract):
    test_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    test_temperature_K: Positive
    expanded_temperature_uncertainty_K: Nonnegative
    strain_rate_per_s: Positive
    expanded_strain_rate_uncertainty_per_s: Nonnegative
    offset_definition_id: str = Field(min_length=1)
    offset_strain: Nonnegative
    offset_strain_unit_token: Literal["1"] = "1"
    raw_curve_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_set_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    results: tuple[TensileReportedResult, ...] = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    caller_validity_status: Literal["valid", "invalid", "unknown"]
    caller_validity_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_results(self):
        metrics = [row.metric for row in self.results]
        ids = [row.result_id for row in self.results]
        if len(set(metrics)) != len(metrics) or len(set(ids)) != len(ids):
            raise ValueError("tensile results must have unique metrics and identifiers per test")
        return self


class TensileMetricCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric: TensileMetric
    unit_token: str = Field(min_length=1)
    minimum_acceptable: Nonnegative | None = None
    maximum_acceptable: Nonnegative | None = None
    criterion_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_acceptable is None and self.maximum_acceptable is None:
            raise ValueError("tensile metric criterion requires at least one caller bound")
        if (
            self.minimum_acceptable is not None
            and self.maximum_acceptable is not None
            and self.minimum_acceptable > self.maximum_acceptable
        ):
            raise ValueError("tensile metric criterion bounds must be ordered")
        return self


class TensileCampaignCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    supported_orientation_ids: tuple[str, ...] = Field(min_length=1)
    supported_geometry_ids: tuple[str, ...] = Field(min_length=1)
    geometry_unit_token: str = Field(min_length=1)
    area_unit_token: str = Field(min_length=1)
    required_machine_id: str = Field(min_length=1)
    required_load_cell_id: str = Field(min_length=1)
    required_extensometer_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_strain_rate_per_s: Positive
    maximum_strain_rate_per_s: Positive
    required_offset_definition_id: str = Field(min_length=1)
    required_offset_strain: Nonnegative
    offset_strain_tolerance: Nonnegative
    required_metrics: tuple[TensileMetric, ...] = Field(min_length=1)
    metric_criteria: tuple[TensileMetricCriterion, ...] = Field(min_length=1)
    minimum_valid_test_count: int = Field(ge=1)
    minimum_independence_group_count: int = Field(ge=1)
    caller_validity_policy_id: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    built_in_standard_rules_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("tensile profile temperature support must be ordered")
        if self.maximum_strain_rate_per_s < self.minimum_strain_rate_per_s:
            raise ValueError("tensile profile strain-rate support must be ordered")
        criteria = [row.metric for row in self.metric_criteria]
        if len(set(self.required_metrics)) != len(self.required_metrics):
            raise ValueError("tensile required metrics must be unique")
        if len(set(criteria)) != len(criteria) or set(criteria) != set(self.required_metrics):
            raise ValueError("tensile profile requires exactly one criterion per required metric")
        return self


class TensileOffsetYieldCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    specimens: tuple[TensileSpecimenIdentity, ...] = Field(min_length=1)
    machine: TensileMachineConfiguration
    tests: tuple[TensileTestRecord, ...] = Field(min_length=1)
    caller_profile: TensileCampaignCallerProfile
    specimen_product_heat_orientation_and_geometry_reviewed: bool
    machine_load_cell_extensometer_and_calibration_reviewed: bool
    temperature_strain_rate_and_offset_definition_reviewed: bool
    raw_curve_and_reported_result_digests_reviewed: bool
    result_units_uncertainties_and_validity_flags_reviewed: bool
    replicate_source_and_independence_groups_reviewed: bool
    caller_profile_and_missing_evidence_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        for values, label in (
            ([row.specimen_id for row in self.specimens], "specimen"),
            ([row.test_id for row in self.tests], "test"),
            ([row.sequence_index for row in self.tests], "test sequence"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"tensile campaign {label} identifiers must be unique")
        if {row.specimen_id for row in self.tests} - {row.specimen_id for row in self.specimens}:
            raise ValueError("tensile tests must reference declared specimens")
        return self


def tensile_offset_yield_campaign(x: TensileOffsetYieldCampaign) -> Calculation:
    profile = x.caller_profile
    missing_reviews = [
        name
        for name in (
            "specimen_product_heat_orientation_and_geometry_reviewed",
            "machine_load_cell_extensometer_and_calibration_reviewed",
            "temperature_strain_rate_and_offset_definition_reviewed",
            "raw_curve_and_reported_result_digests_reviewed",
            "result_units_uncertainties_and_validity_flags_reviewed",
            "replicate_source_and_independence_groups_reviewed",
            "caller_profile_and_missing_evidence_policy_reviewed",
        )
        if not getattr(x, name)
    ]
    specimen_mismatches = [
        row.specimen_id
        for row in x.specimens
        if row.product_id != profile.product_id
        or row.heat_id != profile.heat_id
        or row.material_condition_id != profile.material_condition_id
        or row.orientation_id not in profile.supported_orientation_ids
        or row.geometry_id not in profile.supported_geometry_ids
        or row.geometry_unit_token != profile.geometry_unit_token
        or row.area_unit_token != profile.area_unit_token
    ]
    machine_mismatches = [
        name
        for name, actual, expected in (
            ("machine_id", x.machine.machine_id, profile.required_machine_id),
            ("load_cell_id", x.machine.load_cell_id, profile.required_load_cell_id),
            ("extensometer_id", x.machine.extensometer_id, profile.required_extensometer_id),
        )
        if actual != expected
    ]
    invalid_tests = [row.test_id for row in x.tests if row.caller_validity_status != "valid"]
    calibration_invalid = (
        x.machine.load_cell_calibration_status != "valid"
        or x.machine.extensometer_calibration_status != "valid"
    )
    if missing_reviews or specimen_mismatches or machine_mismatches or invalid_tests or calibration_invalid:
        return _result(
            x,
            "insufficient_evidence",
            {
                "missing_reviews": missing_reviews,
                "specimen_identity_mismatch_ids": specimen_mismatches,
                "machine_identity_mismatch_fields": machine_mismatches,
                "invalid_or_unknown_test_ids": invalid_tests,
                "calibration_evidence_valid": not calibration_invalid,
            },
        )
    groups = {row.independence_group_id for row in x.tests}
    if (
        len(x.tests) < profile.minimum_valid_test_count
        or len(groups) < profile.minimum_independence_group_count
    ):
        return _result(
            x,
            "insufficient_evidence",
            {"valid_test_count": len(x.tests), "independence_group_count": len(groups)},
        )

    criteria = {row.metric: row for row in profile.metric_criteria}
    findings, missing_or_mismatch = [], []
    for test in x.tests:
        for metric, value, uncertainty, minimum, maximum, unit in (
            (
                "test_temperature",
                test.test_temperature_K,
                test.expanded_temperature_uncertainty_K,
                profile.minimum_temperature_K,
                profile.maximum_temperature_K,
                "K",
            ),
            (
                "strain_rate",
                test.strain_rate_per_s,
                test.expanded_strain_rate_uncertainty_per_s,
                profile.minimum_strain_rate_per_s,
                profile.maximum_strain_rate_per_s,
                "1/s",
            ),
        ):
            findings.append(_finding(test.test_id, metric, value, uncertainty, unit, minimum, maximum))
        if (
            test.offset_definition_id != profile.required_offset_definition_id
            or abs(test.offset_strain - profile.required_offset_strain) > profile.offset_strain_tolerance
        ):
            missing_or_mismatch.append(f"{test.test_id}:offset_definition")
        results = {row.metric: row for row in test.results}
        for metric in profile.required_metrics:
            reported = results.get(metric)
            criterion = criteria[metric]
            if (
                reported is None
                or reported.status != "reported"
                or reported.unit_token != criterion.unit_token
            ):
                missing_or_mismatch.append(f"{test.test_id}:{metric}")
                continue
            findings.append(
                _finding(
                    test.test_id,
                    metric,
                    reported.value,
                    reported.expanded_uncertainty,
                    reported.unit_token,
                    criterion.minimum_acceptable,
                    criterion.maximum_acceptable,
                )
            )
    if missing_or_mismatch:
        return _result(
            x,
            "insufficient_evidence",
            {"missing_invalid_or_mismatch_results": missing_or_mismatch, "criterion_findings": findings},
        )
    outcomes = {row["outcome"] for row in findings}
    outcome = "reject" if "outside" in outcomes else "review" if "boundary_overlap" in outcomes else "accept"
    return _result(
        x,
        outcome,
        {
            "criterion_findings": findings,
            "test_ids": [row.test_id for row in x.tests],
            "specimen_ids": [row.specimen_id for row in x.specimens],
            "source_group_ids": sorted({row.source_group_id for row in x.tests}),
            "independence_group_ids": sorted(groups),
        },
    )


def _finding(test_id, metric, value, uncertainty, unit, minimum, maximum):
    lower, upper = value - uncertainty, value + uncertainty
    within = (minimum is None or lower >= minimum) and (maximum is None or upper <= maximum)
    outside = (minimum is not None and upper < minimum) or (maximum is not None and lower > maximum)
    return {
        "test_id": test_id,
        "metric": metric,
        "value": value,
        "uncertainty": uncertainty,
        "unit": unit,
        "outcome": "within" if within else "outside" if outside else "boundary_overlap",
    }


def _result(x, quality_outcome, additions):
    body = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "quality_outcome": quality_outcome,
        "caller_profile_id": x.caller_profile.profile_id,
        "raw_curve_recomputed": False,
        "offset_yield_automatically_calculated": False,
        "standard_validity_rules_applied": False,
        "design_acceptance_claim": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        **additions,
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status="needs_data" if quality_outcome == "insufficient_evidence" else "computed",
        values=body,
        notes=(
            "Reported tensile results and offset definition are preserved without curve recomputation.",
            "No automatic offset construction, bundled validity rule, design allowable or qualification claim is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("tensile campaign asset and location must match run context")

    return [
        ModelSpec(
            "inspection.tensile_offset_yield_campaign",
            TensileOffsetYieldCampaign,
            tensile_offset_yield_campaign,
            {
                "assessment_id": "1",
                "campaign_id": "1",
                "quality_outcome": "1",
                "caller_profile_id": "1",
                "criterion_findings": "mixed",
                "test_ids": "1",
                "specimen_ids": "1",
                "source_group_ids": "1",
                "independence_group_ids": "1",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "Specimen, product, heat, orientation, geometry, machine, load-cell and extensometer identities are exact caller inputs.",
                "Temperature, strain rate, raw/result digests, offset definition and reported result uncertainties remain explicit.",
                "Campaign outcomes use caller criteria without curve recomputation, automatic offset construction or bundled design rules.",
            ),
            ("authored_tensile_offset_yield_campaign_evidence_audit",),
            context_validator=same_identity,
        )
    ]
