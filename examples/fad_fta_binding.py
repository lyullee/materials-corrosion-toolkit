"""Synthetic-only example of binding a caller probability to a FAD history event."""

from __future__ import annotations

import json

from matintegrity.fad_fta_binding import (
    FADFaultTreeBindingRequest,
    FADFaultTreeProbabilityInput,
    bind_fad_history_probability_to_fta,
)
from fad_assessment_history import calculation, request, synthetic_evidence


if __name__ == "__main__":
    binding = bind_fad_history_probability_to_fta(FADFaultTreeBindingRequest(
        fad_request=request,
        fad_result=calculation,
        probability_input=FADFaultTreeProbabilityInput(
            event_id="synthetic-fad-boundary-event",
            failure_mode="Synthetic FAD boundary exceedance",
            event_condition="first_outside_pinned_fad_boundary_during_period",
            condition_id="synthetic-fad-first-passage-v1",
            condition_statement="A synthetic FAD margin first becomes negative after period start.",
            probability=0.03,
            probability_meaning="conditional_first_failure_in_period",
            conditioning="Synthetic illustration only; not a risk estimate.",
            probability_scope_id="synthetic-fad-period-scope",
            probability_evidence=(synthetic_evidence("caller-period-probability"),),
            rights_boundary="local_only",
            asset_id=request.asset_id,
            location_id=request.location_id,
            physical_scope_id=request.physical_scope_id,
            clock_id=request.clock_id,
            horizon_start_s=request.knots[0].time_s,
            horizon_end_s=request.knots[-1].time_s,
            material_condition_id=request.material_condition_id,
            geometry_basis_id=request.geometry_basis_id,
            load_history_id=request.load_history_id,
        ),
    ))
    if hasattr(binding, "basic_event"):
        output = {
            "basic_event": binding.basic_event.model_dump(mode="json"),
            "calculation": binding.calculation.model_dump(mode="json"),
        }
    else:
        output = binding.model_dump(mode="json")
    print(json.dumps(output, indent=2, ensure_ascii=False))
