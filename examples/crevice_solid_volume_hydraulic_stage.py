"""Python wiring for licensed crevice phase-volume to hydraulic-stage composition."""

from matintegrity.contracts import Calculation, Evidence, RunContext, canonical_digest
from matintegrity.crevice_solid_volume_hydraulic_stage import (
    CreviceSolidVolumeHydraulicStageRequest,
    MODEL_ID as COMPOSED_MODEL_ID,
)
from matintegrity.crevice_solid_volume_rate import (
    COMPOSED_STAGE_SOURCE_ID,
    composed_crevice_stage_geometry_digest,
)
from matintegrity.registry import default_registry


def run_phase_volume_hydraulic_stage(
    *,
    volume_rate_request: dict,
    hydraulic_stage_request: dict,
    context: RunContext,
    composition_license_id: str,
    composition_citation: str,
):
    """Run both registry APIs after caller has reviewed the derived-use permission."""
    registry = default_registry()
    volume = registry.run(
        "corrosion.crevice_solid_volume_rate", volume_rate_request, context
    )
    if volume.status != "computed":
        return volume

    volume_result = Calculation(
        status=volume.status,
        values=volume.values,
        notes=volume.notes,
    )
    hydraulic = registry.input_type(
        "corrosion.crevice_hydraulic_stage_rhs"
    ).model_validate(hydraulic_stage_request)
    authorization_digest = composed_crevice_stage_geometry_digest(
        hydraulic,
        volume.values["liquid_volume_rate_m3_s_by_cell"],
        volume_rate_result_sha256=canonical_digest(volume_result.model_dump(mode="json")),
    )
    authorization = Evidence(
        source_id=COMPOSED_STAGE_SOURCE_ID,
        origin="user_declared",
        citation=composition_citation,
        license_id=composition_license_id,
        sha256=authorization_digest,
    )
    composed_request = CreviceSolidVolumeHydraulicStageRequest(
        volume_rate_request=volume_rate_request,
        volume_rate_result=volume_result,
        hydraulic_stage_request=hydraulic,
        composition_authorization=authorization,
        composition_authorization_reviewed=True,
        computational_use_authorized=True,
    )
    return registry.run(COMPOSED_MODEL_ID, composed_request, context)
