"""Synthetic finite-plane feature handoff; no fatigue law or test data included."""

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.multiaxial_cycle_block_feature_handoff import (
    CycleBlockFeatureBinding,
    CycleBlockFeatureHandoffRequest,
    FiniteCyclePlane,
    TensorCycleBlockFeatureInput,
    bind_cycle_features_to_adaptive_request,
)
from matintegrity.models.multiaxial_work_life import ClosedTensorCycle
from matintegrity.registry import default_registry

provider_evidence = Evidence(
    source_id="synthetic-cycle-provider",
    origin="synthetic",
    citation="Project-authored synthetic example only; no experimental record.",
    sha256="0" * 64,
)
stress_evidence = Evidence(
    source_id="synthetic-stress-history",
    origin="synthetic",
    citation="Synthetic tensor path for API illustration only.",
    sha256="1" * 64,
)
strain_evidence = Evidence(
    source_id="synthetic-strain-history",
    origin="synthetic",
    citation="Synthetic tensor path for API illustration only.",
    sha256="2" * 64,
)
block_evidence = Evidence(
    source_id="synthetic-cycle-block-record",
    origin="synthetic",
    citation="Synthetic cycle-block record for API illustration only.",
    sha256="3" * 64,
)

cycle = ClosedTensorCycle(
    cycle_id="synthetic-representative-cycle",
    allocated_cycle_count=1.0,
    sample_ids=["start", "peak", "return"],
    stress_tensor_components_Pa=[
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [80e6, 10e6, 0.0, 5e6, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ],
    # Engineering-shear convention: xy component is gamma_xy.
    strain_tensor_components=[
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.001, 0.0002, 0.0, 0.002, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ],
)
block = TensorCycleBlockFeatureInput(
    block_id="synthetic-block-01",
    cycle_population_id="synthetic-population-01",
    loading_state_id="synthetic-loading-state-01",
    cycle_count=1000,
    source_record_id="synthetic-cycle-block-record",
    source_record_sha256="3" * 64,
    cycle=cycle,
    evidence=(block_evidence,),
)
request = CycleBlockFeatureHandoffRequest(
    assessment_id="synthetic-feature-handoff",
    physical_scope_id="synthetic-scope",
    material_condition_id="synthetic-material-condition",
    location_id="synthetic-location",
    cycle_count_basis_id="caller-counted-cycle-basis",
    history_provider_id="synthetic-cycle-provider",
    history_provider_revision="1",
    history_provider_configuration_sha256="4" * 64,
    history_provider_record_sha256="0" * 64,
    stress_history_source_id="synthetic-stress-history",
    stress_history_sha256="1" * 64,
    strain_history_source_id="synthetic-strain-history",
    strain_history_sha256="2" * 64,
    strain_shear_convention="engineering",
    maximum_stress_closure_error_Pa=1.0,
    maximum_strain_closure_error=1e-10,
    finite_planes=(FiniteCyclePlane(
        plane_id="x-normal-y-shear",
        normal=(1.0, 0.0, 0.0),
        engineering_shear_direction=(0.0, 1.0, 0.0),
    ),),
    blocks=(block,),
    parameter_bindings=(
        CycleBlockFeatureBinding(
            plane_id="x-normal-y-shear",
            feature_id="normal_stress_max_Pa",
            parameter_id="sigma_normal_max",
        ),
        CycleBlockFeatureBinding(
            plane_id="x-normal-y-shear",
            feature_id="engineering_shear_strain_amplitude",
            parameter_id="gamma_shear_amplitude",
        ),
    ),
    tensor_order_units_and_shear_convention_reviewed=True,
    closed_cycle_and_representative_repetition_reviewed=True,
    finite_plane_selection_and_feature_mapping_reviewed=True,
    feature_parameter_semantics_reviewed=True,
    source_evidence_and_usage_rights_reviewed=True,
    downstream_caller_law_remains_external_reviewed=True,
    computational_use_authorized=True,
    evidence=(provider_evidence, stress_evidence, strain_evidence),
)
context = RunContext(
    asset_id="synthetic-asset",
    location_id="synthetic-location",
    time_basis="caller_cycle_count",
    evidence=(provider_evidence, stress_evidence, strain_evidence, block_evidence),
)

handoff = default_registry().run(
    "integration.cycle_block_feature_handoff", request, context,
)

# Construct `adaptive_request` with the existing adaptive cycle-block API,
# caller-owned state/provider/calibration and matching block identity skeleton.
# The handoff replaces only the skeleton block parameter/source payload.
def bind_existing_request(adaptive_request):
    return bind_cycle_features_to_adaptive_request(adaptive_request, handoff)
