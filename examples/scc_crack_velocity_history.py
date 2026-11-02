"""Illustrate the SCC time-growth API with synthetic values only."""

from __future__ import annotations

import json

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.models.chloride_scc import (
    SCC_CRACK_VELOCITY_SOURCE_ID,
    SCCCrackVelocityHistoryRequest,
    SCCCrackVelocityLaw,
    scc_crack_velocity_history,
)


def build_synthetic_request() -> SCCCrackVelocityHistoryRequest:
    curve_identities = {
        "curve_id": "synthetic-scc-curve",
        "source_group_id": "synthetic-example-source-group",
        "material_condition_id": "synthetic-material-condition",
        "metallurgy_id": "synthetic-metallurgy",
        "environment_id": "synthetic-environment",
        "loading_basis_id": "synthetic-fixed-loading",
        "threshold_K_I_Pa_sqrt_m": 10.0,
        "K_I_Pa_sqrt_m": [10.0, 30.0, 50.0],
        "crack_velocity_m_s": [0.0, 1.0e-9, 2.0e-9],
    }
    source_sha256 = canonical_digest({"synthetic_source_record": curve_identities})
    table_sha256 = canonical_digest(curve_identities)
    citation = "Synthetic instructional values in this example; not experimental evidence."
    law = SCCCrackVelocityLaw(
        **curve_identities,
        source_file_sha256=source_sha256,
        table_sha256=table_sha256,
        evidence=(Evidence(
            source_id=SCC_CRACK_VELOCITY_SOURCE_ID,
            origin="synthetic",
            citation=citation,
            license_id="MIT",
            sha256=source_sha256,
        ),),
        rights_boundary="local_only",
        applicability_review_id="synthetic-contract-example-only",
    )

    asset_id = "synthetic-asset"
    location_id = "synthetic-location"
    physical_scope_id = "synthetic-scope"
    specimen_id = "synthetic-specimen"
    clock_id = "synthetic-clock"
    time_s = (0.0, 10.0, 20.0)
    K_I = (20.0, 40.0, 50.0)
    history_record = {
        "asset_id": asset_id,
        "location_id": location_id,
        "physical_scope_id": physical_scope_id,
        "specimen_id": specimen_id,
        "clock_id": clock_id,
        "time_s": list(time_s),
        "K_I_Pa_sqrt_m": list(K_I),
    }
    history_sha256 = canonical_digest(history_record)
    return SCCCrackVelocityHistoryRequest(
        assessment_id="synthetic-scc-history-example",
        asset_id=asset_id,
        location_id=location_id,
        physical_scope_id=physical_scope_id,
        specimen_id=specimen_id,
        clock_id=clock_id,
        material_condition_id=law.material_condition_id,
        metallurgy_id=law.metallurgy_id,
        environment_id=law.environment_id,
        loading_basis_id=law.loading_basis_id,
        time_s=time_s,
        K_I_Pa_sqrt_m=K_I,
        K_I_history_sha256=history_sha256,
        history_evidence=(Evidence(
            source_id=SCC_CRACK_VELOCITY_SOURCE_ID,
            origin="synthetic",
            citation=citation,
            license_id="MIT",
            sha256=history_sha256,
        ),),
        law=law,
        stress_intensity_history_piecewise_linear_reviewed=True,
        interpolation_linear_in_K_I_and_velocity_reviewed=True,
        fixed_environment_and_loading_state_reviewed=True,
        crack_geometry_feedback_excluded_reviewed=True,
        maximum_operations=10_000,
        computation_budget_reviewed=True,
    )


if __name__ == "__main__":
    result = scc_crack_velocity_history(build_synthetic_request())
    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))
