"""Caller-profile audit of impact-test campaign evidence without transition fitting."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ImpactMetric = Literal["absorbed_energy", "lateral_expansion", "shear_fracture"]


class ImpactSpecimenIdentity(Contract):
    specimen_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    notch_id: str = Field(min_length=1)
    notch_definition: str = Field(min_length=1)
    size_id: str = Field(min_length=1)
    thickness: Positive
    width: Positive
    length: Positive
    dimension_unit_token: str = Field(min_length=1)
    specimen_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ImpactMachineConfiguration(Contract):
    machine_id: str = Field(min_length=1)
    machine_revision: str = Field(min_length=1)
    striker_id: str = Field(min_length=1)
    striker_definition: str = Field(min_length=1)
    striker_radius: Positive
    striker_radius_unit_token: str = Field(min_length=1)
    machine_capacity: Positive
    machine_capacity_unit_token: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    calibration_revision: str = Field(min_length=1)
    calibration_status: Literal["valid", "invalid", "missing"]
    calibration_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def calibration_basis(self):
        if self.calibration_status != "valid" and not self.invalid_or_missing_basis:
            raise ValueError("invalid or missing impact-machine calibration requires a basis")
        return self


class ImpactReportedResult(Contract):
    result_id: str = Field(min_length=1)
    metric: ImpactMetric
    metric_definition: str = Field(min_length=1)
    status: Literal["reported", "missing", "invalid"]
    value: Nonnegative | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    result_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def result_status(self):
        if self.status == "reported":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("reported impact results require value and uncertainty")
        elif self.value is not None or self.expanded_uncertainty is not None:
            raise ValueError("missing or invalid impact results cannot carry numeric values")
        elif not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid impact results require a basis")
        return self


class ImpactTestRecord(Contract):
    test_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    test_temperature: Positive
    expanded_temperature_uncertainty: Nonnegative
    temperature_unit_token: Literal["K"] = "K"
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    results: tuple[ImpactReportedResult, ...] = Field(min_length=1)
    caller_validity_status: Literal["valid", "invalid", "unknown"]
    caller_validity_basis: str = Field(min_length=1)
    test_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_metrics(self):
        metrics = [row.metric for row in self.results]
        result_ids = [row.result_id for row in self.results]
        if len(set(metrics)) != len(metrics) or len(set(result_ids)) != len(result_ids):
            raise ValueError("impact results must have unique metrics and result identifiers per test")
        return self


class ImpactMetricCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric: ImpactMetric
    unit_token: str = Field(min_length=1)
    minimum_acceptable: Nonnegative | None = None
    maximum_acceptable: Nonnegative | None = None
    criterion_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.minimum_acceptable is None and self.maximum_acceptable is None:
            raise ValueError("impact metric criterion requires at least one caller bound")
        if (
            self.minimum_acceptable is not None
            and self.maximum_acceptable is not None
            and self.minimum_acceptable > self.maximum_acceptable
        ):
            raise ValueError("impact metric criterion bounds must be ordered")
        return self


class ImpactCampaignCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    notch_id: str = Field(min_length=1)
    size_id: str = Field(min_length=1)
    specimen_dimension_unit_token: str = Field(min_length=1)
    minimum_test_temperature_K: Positive
    maximum_test_temperature_K: Positive
    required_metrics: tuple[ImpactMetric, ...] = Field(min_length=1)
    metric_criteria: tuple[ImpactMetricCriterion, ...] = Field(min_length=1)
    minimum_valid_replicates_per_exact_temperature: int = Field(ge=1)
    minimum_independence_group_count: int = Field(ge=1)
    required_machine_id: str = Field(min_length=1)
    required_striker_id: str = Field(min_length=1)
    required_calibration_id: str = Field(min_length=1)
    caller_validity_policy_id: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    built_in_standard_criteria_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if self.maximum_test_temperature_K < self.minimum_test_temperature_K:
            raise ValueError("impact campaign temperature support must be ordered")
        if len(set(self.required_metrics)) != len(self.required_metrics):
            raise ValueError("impact campaign required metrics must be unique")
        criteria = [row.metric for row in self.metric_criteria]
        if len(set(criteria)) != len(criteria) or set(criteria) != set(self.required_metrics):
            raise ValueError("impact campaign requires exactly one criterion per required metric")
        return self


class ImpactTestingCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    specimens: tuple[ImpactSpecimenIdentity, ...] = Field(min_length=1)
    machine: ImpactMachineConfiguration
    tests: tuple[ImpactTestRecord, ...] = Field(min_length=1)
    caller_profile: ImpactCampaignCallerProfile
    specimen_product_heat_orientation_notch_and_size_reviewed: bool
    temperature_results_units_and_uncertainties_reviewed: bool
    machine_striker_and_calibration_reviewed: bool
    replicate_source_and_independence_groups_reviewed: bool
    caller_validity_flags_and_profile_reviewed: bool
    provenance_and_record_digests_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        for values, label in (
            ([row.specimen_id for row in self.specimens], "specimen"),
            ([row.test_id for row in self.tests], "test"),
            ([row.sequence_index for row in self.tests], "test sequence"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"impact campaign {label} identifiers must be unique")
        specimen_ids = {row.specimen_id for row in self.specimens}
        if {row.specimen_id for row in self.tests} - specimen_ids:
            raise ValueError("impact tests must reference declared specimens")
        tested_specimen_ids = [row.specimen_id for row in self.tests]
        if len(set(tested_specimen_ids)) != len(tested_specimen_ids):
            raise ValueError(
                "the campaign requires one impact test per physical specimen; combine metrics in one test record"
            )
        return self


def impact_testing_campaign(x: ImpactTestingCampaign) -> Calculation:
    profile = x.caller_profile
    missing_reviews = [
        name
        for name in (
            "specimen_product_heat_orientation_notch_and_size_reviewed",
            "temperature_results_units_and_uncertainties_reviewed",
            "machine_striker_and_calibration_reviewed",
            "replicate_source_and_independence_groups_reviewed",
            "caller_validity_flags_and_profile_reviewed",
            "provenance_and_record_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    specimen_mismatches = []
    for specimen in x.specimens:
        fields = [
            name
            for name in (
                "product_id",
                "heat_id",
                "material_condition_id",
                "orientation_id",
                "notch_id",
                "size_id",
            )
            if getattr(specimen, name) != getattr(profile, name)
        ]
        if specimen.dimension_unit_token != profile.specimen_dimension_unit_token:
            fields.append("dimension_unit_token")
        if fields:
            specimen_mismatches.append({"specimen_id": specimen.specimen_id, "fields": fields})
    machine_mismatch = [
        name
        for name, actual, required in (
            ("machine_id", x.machine.machine_id, profile.required_machine_id),
            ("striker_id", x.machine.striker_id, profile.required_striker_id),
            ("calibration_id", x.machine.calibration_id, profile.required_calibration_id),
        )
        if actual != required
    ]
    invalid_test_ids = [row.test_id for row in x.tests if row.caller_validity_status != "valid"]
    if (
        missing_reviews
        or specimen_mismatches
        or machine_mismatch
        or x.machine.calibration_status != "valid"
        or invalid_test_ids
    ):
        return _calculation(
            x,
            "insufficient_evidence",
            {
                "missing_reviews": missing_reviews,
                "specimen_identity_mismatches": specimen_mismatches,
                "machine_configuration_mismatches": machine_mismatch,
                "calibration_status": x.machine.calibration_status,
                "invalid_or_unknown_test_ids": invalid_test_ids,
            },
        )

    exact_temperature_counts = {}
    for row in x.tests:
        exact_temperature_counts[row.test_temperature] = (
            exact_temperature_counts.get(row.test_temperature, 0) + 1
        )
    insufficient_temperatures = [
        value
        for value, count in exact_temperature_counts.items()
        if count < profile.minimum_valid_replicates_per_exact_temperature
    ]
    independence_groups = {row.independence_group_id for row in x.tests}
    if insufficient_temperatures or len(independence_groups) < profile.minimum_independence_group_count:
        return _calculation(
            x,
            "insufficient_evidence",
            {
                "insufficient_replicate_temperatures_K": sorted(insufficient_temperatures),
                "independence_group_count": len(independence_groups),
            },
        )

    criteria = {row.metric: row for row in profile.metric_criteria}
    findings = []
    missing_or_invalid = []
    for test in x.tests:
        temp_outcome = _interval_outcome(
            test.test_temperature - test.expanded_temperature_uncertainty,
            test.test_temperature + test.expanded_temperature_uncertainty,
            profile.minimum_test_temperature_K,
            profile.maximum_test_temperature_K,
        )
        findings.append(
            {
                "test_id": test.test_id,
                "metric": "test_temperature",
                "value": test.test_temperature,
                "uncertainty": test.expanded_temperature_uncertainty,
                "unit": "K",
                "outcome": temp_outcome,
            }
        )
        results = {row.metric: row for row in test.results}
        for metric in profile.required_metrics:
            result = results.get(metric)
            criterion = criteria[metric]
            if result is None or result.status != "reported":
                missing_or_invalid.append(f"{test.test_id}:{metric}")
                continue
            if result.unit_token != criterion.unit_token:
                missing_or_invalid.append(f"{test.test_id}:{metric}:unit")
                continue
            outcome = _interval_outcome(
                result.value - result.expanded_uncertainty,
                result.value + result.expanded_uncertainty,
                criterion.minimum_acceptable,
                criterion.maximum_acceptable,
            )
            findings.append(
                {
                    "test_id": test.test_id,
                    "result_id": result.result_id,
                    "metric": metric,
                    "value": result.value,
                    "uncertainty": result.expanded_uncertainty,
                    "unit": result.unit_token,
                    "outcome": outcome,
                    "criterion_id": criterion.criterion_id,
                }
            )
    if missing_or_invalid:
        return _calculation(
            x,
            "insufficient_evidence",
            {"missing_invalid_or_unit_mismatch_results": missing_or_invalid, "criterion_findings": findings},
        )
    outcomes = {row["outcome"] for row in findings}
    outcome = "reject" if "outside" in outcomes else "review" if "boundary_overlap" in outcomes else "accept"
    return _calculation(
        x,
        outcome,
        {
            "criterion_findings": findings,
            "test_ids": [row.test_id for row in x.tests],
            "specimen_ids": [row.specimen_id for row in x.specimens],
            "source_group_ids": sorted({row.source_group_id for row in x.tests}),
            "independence_group_ids": sorted(independence_groups),
            "exact_temperature_replicate_counts": {
                str(key): exact_temperature_counts[key] for key in sorted(exact_temperature_counts)
            },
        },
    )


def _interval_outcome(lower, upper, minimum, maximum):
    within = (minimum is None or lower >= minimum) and (maximum is None or upper <= maximum)
    outside = (minimum is not None and upper < minimum) or (maximum is not None and lower > maximum)
    return "within" if within else "outside" if outside else "boundary_overlap"


def _calculation(x, quality_outcome, additions):
    body = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "quality_outcome": quality_outcome,
        "acceptance_profile_id": x.caller_profile.profile_id,
        "caller_acceptance_profile_only": True,
        "standard_validity_rules_applied": False,
        "temperature_correction_applied": False,
        "transition_fit_performed": False,
        "design_acceptance_claim": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        **additions,
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status="needs_data" if quality_outcome == "insufficient_evidence" else "computed",
        values=body,
        notes=(
            "Only caller-provided validity flags and criteria are applied to reported campaign evidence.",
            "No standard validity rule, temperature correction, transition fit, design allowable or qualification claim is generated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("impact campaign asset and location must match run context")

    return [
        ModelSpec(
            "inspection.impact_testing_campaign",
            ImpactTestingCampaign,
            impact_testing_campaign,
            {
                "assessment_id": "1",
                "campaign_id": "1",
                "quality_outcome": "1",
                "acceptance_profile_id": "1",
                "criterion_findings": "mixed",
                "test_ids": "1",
                "specimen_ids": "1",
                "source_group_ids": "1",
                "independence_group_ids": "1",
                "exact_temperature_replicate_counts": "count",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "Specimen, product, heat, orientation, notch, size, machine, striker and calibration identities are exact caller inputs.",
                "Reported energy, lateral expansion and shear-fracture evidence retains exact units, uncertainty and source independence.",
                "Campaign outcomes use caller validity flags and criteria without bundled standard rules or design acceptance.",
            ),
            ("authored_impact_testing_campaign_evidence_audit",),
            version="1.0.1",
            context_validator=same_identity,
        )
    ]
