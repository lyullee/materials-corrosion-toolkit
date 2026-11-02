"""Synthetic input shape for the caller-owned saturation history event API."""

from matintegrity.contracts import canonical_digest
from matintegrity.saturation_history_events import (
    SaturationHistoryEventRequest,
    SaturationHistoryKnot,
    audit_saturation_history_events,
)

knots = (
    SaturationHistoryKnot(time_s=0.0, log10_saturation_ratio=-0.2),
    SaturationHistoryKnot(time_s=10.0, log10_saturation_ratio=0.2),
    SaturationHistoryKnot(time_s=20.0, log10_saturation_ratio=-0.1),
)
request = SaturationHistoryEventRequest(
    solid_id="phase-A",
    solution_scope_id="synthetic-run",
    provider_id="caller-equilibrium-model",
    provider_revision="revision-1",
    provider_configuration_sha256="a" * 64,
    input_history_sha256=canonical_digest([row.model_dump(mode="json") for row in knots]),
    knots=knots,
    consistent_solid_and_standard_state_reviewed=True,
    time_basis_and_order_reviewed=True,
    piecewise_linear_interpolation_reviewed=True,
    computational_use_authorized=True,
)
result = audit_saturation_history_events(request)
