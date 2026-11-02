"""Bonded-layer observation reconciliation with caller-owned requirements and dispositions."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class BondedLayerRegion(Contract):
    region_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    target_area_m2: Positive
    examined_area_m2: Nonnegative
    unexamined_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def coverage(self):
        if self.examined_area_m2 > self.target_area_m2:
            raise ValueError("examined bonded-layer area cannot exceed target area")
        if self.examined_area_m2 < self.target_area_m2 and not self.unexamined_basis:
            raise ValueError("incomplete bonded-layer coverage requires a basis")
        return self


class BondedLayerObservation(Contract):
    observation_id: str = Field(min_length=1)
    region_id: str | None = None
    observation_kind: Literal["bond_strength", "interface_indication", "user_defined_metric"]
    metric_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    value: Nonnegative | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    measurement_valid: bool
    missing_invalid_or_unmapped_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def observation_state(self):
        if self.value is None:
            if self.expanded_uncertainty is not None or not self.missing_invalid_or_unmapped_basis:
                raise ValueError("a missing bonded-layer value requires a basis and no uncertainty")
        elif self.expanded_uncertainty is None:
            raise ValueError("a reported bonded-layer value requires expanded uncertainty")
        if (
            not self.measurement_valid or self.region_id is None
        ) and not self.missing_invalid_or_unmapped_basis:
            raise ValueError("invalid or unmapped bonded-layer observations require a basis")
        return self


class BondedLayerRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    comparator: Literal["minimum", "maximum"]
    limit_value: Nonnegative
    unit_token: str = Field(min_length=1)
    requirement_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class BondedLayerDisposition(Contract):
    requirement_id: str = Field(min_length=1)
    satisfied_disposition: str = Field(min_length=1)
    not_satisfied_disposition: str = Field(min_length=1)
    indeterminate_disposition: str = Field(min_length=1)
    disposition_authority_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class BondedLayerIntegrityAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    substrate_material_id: str = Field(min_length=1)
    substrate_lot_id: str = Field(min_length=1)
    bonded_layer_material_id: str = Field(min_length=1)
    bonded_layer_lot_id: str = Field(min_length=1)
    interface_system_id: str = Field(min_length=1)
    bonding_process_id: str = Field(min_length=1)
    bonding_process_revision: str = Field(min_length=1)
    regions: list[BondedLayerRegion] = Field(min_length=1)
    observations: list[BondedLayerObservation] = Field(min_length=1)
    declared_requirements: list[BondedLayerRequirement] = Field(min_length=1)
    declared_dispositions: list[BondedLayerDisposition]
    material_lot_and_process_identity_reviewed: bool
    regions_mutually_exclusive_reviewed: bool
    examination_coverage_reviewed: bool
    method_and_calibration_reviewed: bool
    uncertainty_basis_reviewed: bool
    observation_mapping_reviewed: bool
    requirement_and_disposition_authority_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_references_and_units(self):
        region_ids = [item.region_id for item in self.regions]
        observation_ids = [item.observation_id for item in self.observations]
        requirement_ids = [item.requirement_id for item in self.declared_requirements]
        disposition_ids = [item.requirement_id for item in self.declared_dispositions]
        if len(set(region_ids)) != len(region_ids):
            raise ValueError("bonded-layer region IDs must be unique")
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("bonded-layer observation IDs must be unique")
        if len(set(requirement_ids)) != len(requirement_ids):
            raise ValueError("bonded-layer requirement IDs must be unique")
        if len(set(disposition_ids)) != len(disposition_ids):
            raise ValueError("declare exactly one disposition row per requirement")
        known_regions = set(region_ids)
        if {item.region_id for item in self.observations if item.region_id is not None} - known_regions:
            raise ValueError("mapped observations must reference a declared bonded-layer region")
        if {item.region_id for item in self.declared_requirements} - known_regions:
            raise ValueError("requirements must reference a declared bonded-layer region")
        if set(disposition_ids) != set(requirement_ids):
            raise ValueError("each bonded-layer requirement requires one caller disposition row")
        requirement_units = {
            (item.region_id, item.metric_id): item.unit_token for item in self.declared_requirements
        }
        if len(requirement_units) != len(self.declared_requirements):
            raise ValueError("declare at most one requirement for each region and metric")
        for item in self.observations:
            if item.region_id is None:
                continue
            expected = requirement_units.get((item.region_id, item.metric_id))
            if expected is not None and item.unit_token != expected:
                raise ValueError("bonded-layer observation and requirement units must match exactly")
        return self


def bonded_layer_integrity_assessment(x: BondedLayerIntegrityAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_lot_and_process_identity_reviewed",
            "regions_mutually_exclusive_reviewed",
            "examination_coverage_reviewed",
            "method_and_calibration_reviewed",
            "uncertainty_basis_reviewed",
            "observation_mapping_reviewed",
            "requirement_and_disposition_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    dispositions = {item.requirement_id: item for item in x.declared_dispositions}
    unmapped = [item.observation_id for item in x.observations if item.region_id is None]
    invalid_or_missing = [
        item.observation_id for item in x.observations if not item.measurement_valid or item.value is None
    ]
    incomplete_requirements = []
    rows = []
    for requirement in x.declared_requirements:
        relevant = [
            item
            for item in x.observations
            if item.region_id == requirement.region_id and item.metric_id == requirement.metric_id
        ]
        valid = [item for item in relevant if item.measurement_valid and item.value is not None]
        complete = bool(valid) and len(valid) == len(relevant)
        if not complete:
            incomplete_requirements.append(requirement.requirement_id)
        conservative_values = []
        for item in valid:
            conservative_values.append(
                item.value + item.expanded_uncertainty
                if requirement.comparator == "maximum"
                else item.value - item.expanded_uncertainty
            )
        governing = (
            max(conservative_values)
            if conservative_values and requirement.comparator == "maximum"
            else min(conservative_values)
            if conservative_values
            else None
        )
        satisfied = (
            None
            if not complete
            else governing <= requirement.limit_value
            if requirement.comparator == "maximum"
            else governing >= requirement.limit_value
        )
        disposition = dispositions[requirement.requirement_id]
        selected_disposition = (
            disposition.indeterminate_disposition
            if satisfied is None
            else disposition.satisfied_disposition
            if satisfied
            else disposition.not_satisfied_disposition
        )
        rows.append(
            {
                "requirement_id": requirement.requirement_id,
                "region_id": requirement.region_id,
                "metric_id": requirement.metric_id,
                "comparator": requirement.comparator,
                "limit_value": requirement.limit_value,
                "unit_token": requirement.unit_token,
                "valid_observation_count": len(valid),
                "governing_conservative_value": governing,
                "declared_requirement_satisfied": satisfied,
                "caller_declared_disposition": selected_disposition,
            }
        )
    target_area = sum(item.target_area_m2 for item in x.regions)
    examined_area = sum(item.examined_area_m2 for item in x.regions)
    status = (
        "needs_data"
        if missing_reviews or unmapped or invalid_or_missing or incomplete_requirements
        else "computed"
    )
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "substrate_material_id": x.substrate_material_id,
            "bonded_layer_material_id": x.bonded_layer_material_id,
            "interface_system_id": x.interface_system_id,
            "target_area_m2": target_area,
            "examined_area_m2": examined_area,
            "coverage_fraction": examined_area / target_area,
            "requirement_rows": rows,
            "unmapped_observation_ids": unmapped,
            "invalid_or_missing_observation_ids": invalid_or_missing,
            "incomplete_requirement_ids": incomplete_requirements,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Requirement limits and disposition text are caller-owned and are preserved rather than treated as embedded code rules.",
            "The conservative comparison adds uncertainty for maximum limits and subtracts it for minimum limits.",
            "No delamination growth, residual stress, interface fracture, lifetime or failure probability is predicted.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.bonded_layer_integrity_assessment",
            BondedLayerIntegrityAssessment,
            bonded_layer_integrity_assessment,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "substrate_material_id": "1",
                "bonded_layer_material_id": "1",
                "interface_system_id": "1",
                "target_area_m2": "m^2",
                "examined_area_m2": "m^2",
                "coverage_fraction": "1",
                "requirement_rows": "mixed",
                "unmapped_observation_ids": "1",
                "invalid_or_missing_observation_ids": "1",
                "incomplete_requirement_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Substrate, layer, interface, lot and process identities are caller-reviewed and preserved.",
                "Numerical comparisons require exact observation and requirement unit tokens.",
                "Unmapped, invalid and missing observations are retained and prevent a complete assessment.",
            ),
            ("declared_bonded_layer_observation_disposition",),
        )
    ]
