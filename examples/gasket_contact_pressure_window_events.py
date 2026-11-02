"""Synthetic request template for a gasket contact-pressure window audit."""

from matintegrity.contracts import AssessmentResult, Evidence, RunContext, canonical_digest
from matintegrity.models.gasket_contact_window_events import GasketContactPressureWindowEvents

context = RunContext(asset_id="synthetic-asset", location_id="node-grid", time_basis="synthetic-seconds")
inputs = {"physical_scope_id": "synthetic-joint"}
history_values = {"time_history": [
    {"time_s": 0.0, "response_field": [{"node_id": "node-1", "mean_contact_pressure_Pa": 2.0e6}]},
    {"time_s": 10.0, "response_field": [{"node_id": "node-1", "mean_contact_pressure_Pa": 0.5e6}]},
    {"time_s": 20.0, "response_field": [{"node_id": "node-1", "mean_contact_pressure_Pa": 2.5e6}]},
]}
input_digest = canonical_digest({
    "model_id": "fabrication.flange_viscoelastic_contact_history",
    "model_version": "1.0.0",
    "inputs": inputs,
    "context": context.model_dump(mode="json"),
})
contact_history = AssessmentResult(
    model_id="fabrication.flange_viscoelastic_contact_history",
    model_version="1.0.0",
    status="computed",
    inputs=inputs,
    values=history_values,
    units={"time_history[].response_field[].mean_contact_pressure_Pa": "Pa"},
    assumptions=("Synthetic example only.",),
    notes=(),
    context=context,
    input_digest=input_digest,
    source_ids=("caller-synthetic-contact-history",),
    qualification="user_model",
    runtime={"matintegrity": "synthetic"},
)
criterion_basis = {
    "criterion_provider_id": "caller-criterion-provider",
    "criterion_provider_revision": "revision-1",
    "criterion_record_id": "synthetic-record",
    "physical_scope_id": "synthetic-joint",
    "node_id": "node-1",
    "minimum_contact_pressure_Pa": 1.0e6,
    "maximum_contact_pressure_Pa": 3.0e6,
}
criterion_sha256 = canonical_digest(criterion_basis)
request = GasketContactPressureWindowEvents(
    assessment_id="synthetic-window-review",
    physical_scope_id="synthetic-joint",
    contact_history=contact_history,
    contact_history_sha256=canonical_digest(contact_history.model_dump(mode="json")),
    node_id="node-1",
    minimum_contact_pressure_Pa=1.0e6,
    maximum_contact_pressure_Pa=3.0e6,
    criterion_provider_id="caller-criterion-provider",
    criterion_provider_revision="revision-1",
    criterion_record_id="synthetic-record",
    criterion_sha256=criterion_sha256,
    criterion_evidence=(Evidence(source_id="caller-criterion-provider", origin="synthetic", citation="Synthetic caller criterion", sha256=criterion_sha256),),
    usage_rights_evidence=(Evidence(source_id="caller-use-authorization", origin="user_declared", citation="Synthetic authorization", license_id="caller-authorized"),),
    usage_license_id="caller-authorized",
    physical_scope_and_time_basis_reviewed=True,
    criterion_applicability_reviewed=True,
    interpolation_basis_reviewed=True,
    pressure_basis_and_units_reviewed=True,
    usage_rights_reviewed=True,
    computational_use_authorized=True,
)
