# FAD history to FTA basic event adapter

## Scope

`matintegrity.fad_fta_binding` binds the exact deterministic result of
`structural.failure_assessment_history` to the existing `FaultTreeBasicEvent` and
`IntegrityEventBasis` contracts. Its only supported event condition is
`first_outside_pinned_fad_boundary_during_period`. The adapter never calculates,
calibrates or replaces the event probability supplied by the caller.

## Python API

First calculate an `FADAssessmentHistoryRequest` with
`evaluate_failure_assessment_history`. Then provide that exact request/result pair
and a separately assessed finite-period probability:

```python
from matintegrity.contracts import Evidence
from matintegrity.fad_fta_binding import (
    FADFaultTreeBindingRequest,
    FADFaultTreeProbabilityInput,
    bind_fad_history_probability_to_fta,
)
from matintegrity.fad_history import evaluate_failure_assessment_history

fad_result = evaluate_failure_assessment_history(fad_request)
binding = bind_fad_history_probability_to_fta(FADFaultTreeBindingRequest(
    fad_request=fad_request,
    fad_result=fad_result,
    probability_input=FADFaultTreeProbabilityInput(
        event_id="asset-crack-fad-boundary-event",
        failure_mode="caller-defined fracture-assessment boundary exceedance",
        event_condition="first_outside_pinned_fad_boundary_during_period",
        condition_id="fad-boundary-first-passage-v1",
        condition_statement=(
            "The reviewed FAD margin first becomes negative after period start."
        ),
        probability=0.02,  # independent caller assessment; never derived from FAD margins
        probability_meaning="conditional_first_failure_in_period",
        conditioning="Caller-defined initial flaw, load uncertainty and material state.",
        probability_scope_id="asset-period-probability-scope-v1",
        probability_evidence=(Evidence(
            source_id="caller_fad_event_probability_assessment",
            origin="user_declared",
            citation="Caller-maintained assessment and revision identifier",
            license_id=None,
            sha256=None,
        ),),
        rights_boundary="local_only",
        asset_id=fad_request.asset_id,
        location_id=fad_request.location_id,
        physical_scope_id=fad_request.physical_scope_id,
        clock_id=fad_request.clock_id,
        horizon_start_s=fad_request.knots[0].time_s,
        horizon_end_s=fad_request.knots[-1].time_s,
        material_condition_id=fad_request.material_condition_id,
        geometry_basis_id=fad_request.geometry_basis_id,
        load_history_id=fad_request.load_history_id,
    ),
))

if hasattr(binding, "basic_event"):
    basic_event = binding.basic_event
    lineage = binding.calculation
else:
    # needs_data / out_of_scope: never insert into the FTA.
    lineage = binding
```

The returned `basic_event` may be supplied to a `FaultTreeAssessment`. The FTA still
requires caller review of event scope, independence, common causes and cut sets.

Runnable synthetic-only end-to-end example: [`examples/fad_fta_binding.py`](../../examples/fad_fta_binding.py).
Its curve, provider receipts and probability are all illustrative synthetic inputs;
the probability is not derived from FAD margin and is not an asset risk estimate.

## Validation and crossing semantics

The adapter recomputes the entire FAD history request and compares the canonical
result digest. It checks source model identity, request digest, pinned curve digest,
exact knot times, asset/location/physical scope/clock/material/geometry/load identity,
and the probability's matching scope and positive horizon. All source provider
receipts have already been bound to each source knot by the FAD history request.

If the initial FAD margin is already negative at the first knot, the adapter returns
`out_of_scope`; this condition predates the period and is not a first-passage event
within it. When a later knot is the first negative-margin knot, the binding reports
the adjacent time/margin bracket but does not estimate an exact crossing time. If
no supplied knot is outside the boundary, the binding retains that nominal status;
the caller's probability remains an external uncertainty assessment and is neither
changed nor inferred by this adapter.

## Limits

- A caller independently supplies the probability, `conditional_first_failure_in_period`
  semantics, conditioning, shared scope ID, evidence and rights declaration.
- The adapter does not validate probability calibration or determine whether its
  uncertainty model is compatible with the deterministic nominal FAD history.
- The deterministic history samples only supplied knots. A transient excursion
  between knots can be missed.
- Provider result digests and Evidence are caller receipts; no provider data is
  fetched or independently verified.
- The adapter does not evaluate an FTA, infer dependence/common causes, estimate
  remaining life, establish code acceptance or qualify the FAD curve/mechanics.
- `caller_authorized_open_distribution` requires an authorization digest but is
  still a caller assertion, not a legal ruling.

No tests, numeric runs, packaging or HPC jobs were performed for this API.
