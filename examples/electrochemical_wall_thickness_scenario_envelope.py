"""Compose digest-pinned wall-thickness AssessmentResults into a finite envelope."""

from collections.abc import Iterable

from matintegrity import default_registry
from matintegrity.contracts import AssessmentResult, Evidence, RunContext, canonical_digest
from matintegrity.models.electrochemical_wall_thickness_scenario_envelope import (
    ElectrochemicalWallThicknessScenario,
    ElectrochemicalWallThicknessScenarioEnvelope,
)


def evaluate_wall_scenario_envelope(
    *,
    assessment_id: str,
    scenarios: Iterable[tuple[str, AssessmentResult]],
    asset_id: str,
    location_id: str,
    time_basis: str,
    physical_scope_id: str,
    material_condition_id: str,
    baseline_id: str,
    baseline_record_sha256: str,
    scenario_provider_id: str,
    scenario_provider_revision: str,
    scenario_manifest_citation: str,
    usage_rights_evidence: tuple[Evidence, ...],
    usage_license_id: str,
    complete_scenario_set_reviewed: bool,
    joint_scenario_dependence_reviewed: bool,
    baseline_and_scope_match_reviewed: bool,
    usage_rights_reviewed: bool,
    computational_use_authorized: bool,
    registry=None,
) -> AssessmentResult:
    """Evaluate supplied complete scenarios; the function assigns no weights."""
    scenario_rows = tuple(
        ElectrochemicalWallThicknessScenario(
            scenario_id=scenario_id,
            wall_result=wall_result,
            wall_result_sha256=canonical_digest(wall_result.model_dump(mode="json")),
        )
        for scenario_id, wall_result in scenarios
    )
    scenario_manifest_sha256 = canonical_digest(
        [row.model_dump(mode="json") for row in scenario_rows]
    )
    request = ElectrochemicalWallThicknessScenarioEnvelope(
        assessment_id=assessment_id,
        asset_id=asset_id,
        location_id=location_id,
        time_basis=time_basis,
        physical_scope_id=physical_scope_id,
        material_condition_id=material_condition_id,
        baseline_id=baseline_id,
        baseline_record_sha256=baseline_record_sha256,
        scenario_provider_id=scenario_provider_id,
        scenario_provider_revision=scenario_provider_revision,
        scenarios_sha256=scenario_manifest_sha256,
        scenarios=scenario_rows,
        scenario_evidence=(Evidence(
            source_id=scenario_provider_id,
            origin="user_declared",
            citation=scenario_manifest_citation,
            license_id=usage_license_id,
            sha256=scenario_manifest_sha256,
        ),),
        usage_rights_evidence=usage_rights_evidence,
        usage_license_id=usage_license_id,
        complete_scenario_set_reviewed=complete_scenario_set_reviewed,
        joint_scenario_dependence_reviewed=joint_scenario_dependence_reviewed,
        baseline_and_scope_match_reviewed=baseline_and_scope_match_reviewed,
        usage_rights_reviewed=usage_rights_reviewed,
        computational_use_authorized=computational_use_authorized,
    )
    active_registry = registry or default_registry()
    return active_registry.run(
        "integration.electrochemical_wall_thickness_scenario_envelope",
        request,
        RunContext(asset_id=asset_id, location_id=location_id, time_basis=time_basis),
    )
