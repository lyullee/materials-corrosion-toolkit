# SCC crack advance limit to FTA event binding

## Scope

`matintegrity.scc_fta_binding` maps the deterministic output of
`degradation.scc_crack_velocity_history` to the existing
`FaultTreeBasicEvent` and `IntegrityEventBasis` contracts. The event condition is a
caller-specified cumulative crack-advance limit reached within the supplied finite
history. This adapter does not calculate a probability from the crack-growth model.

The caller must provide an independently assessed probability with the exact meaning
`conditional_first_failure_in_period`, its conditioning statement, shared probability
scope, evidence and rights boundary. Point-in-time state probability, detection
probability, spatial exceedance and unscoped probabilities are not accepted by this
event mapping.

## Python API

First calculate the SCC history with the registered source API, then pass its typed
`Calculation` result and the exact request into the adapter:

```python
from matintegrity.contracts import Evidence
from matintegrity.models.chloride_scc import scc_crack_velocity_history
from matintegrity.scc_fta_binding import (
    SCCFaultTreeBindingRequest,
    SCCFaultTreeProbabilityInput,
    bind_scc_crack_advance_probability_to_fta,
)

scc_result = scc_crack_velocity_history(scc_request)
binding = bind_scc_crack_advance_probability_to_fta(
    SCCFaultTreeBindingRequest(
        scc_request=scc_request,
        scc_result=scc_result,
        crack_advance_limit_m=0.001,
        limit_evidence=Evidence(
            source_id="caller_crack_advance_limit",
            origin="user_declared",
            citation="Asset-specific crack-advance limit basis, revision 4",
            license_id=None,
            sha256=None,
        ),
        probability_input=SCCFaultTreeProbabilityInput(
            event_id="asset-17-scc-crack-limit",
            failure_mode="caller-defined SCC crack-advance limit event",
            condition_id="scc-advance-limit-v1",
            condition_statement=(
                "Cumulative SCC crack advance reaches the declared limit during the period."
            ),
            probability=0.03,  # independent caller assessment; never derived from scc_result
            probability_meaning="conditional_first_failure_in_period",
            conditioning="Caller-defined initial flaw, environment and operating state.",
            probability_scope_id="asset-17-scc-period-2026",
            probability_evidence=(Evidence(
                source_id="caller_probability_assessment",
                origin="user_declared",
                citation="Caller-maintained event-probability assessment, revision 2",
                license_id=None,
                sha256=None,
            ),),
            rights_boundary="local_only",
        ),
    )
)

if hasattr(binding, "basic_event"):
    basic_event = binding.basic_event
    provenance = binding.calculation
else:
    # `needs_data` or `out_of_scope`; do not insert it into a fault tree.
    provenance = binding
```

The returned `basic_event` can be supplied to a `FaultTreeAssessment`. The FTA still
requires caller review of event scope, independence, common causes and cut sets before
quantification.

Runnable synthetic-only wiring example: [`examples/scc_fta_binding.py`](../../examples/scc_fta_binding.py).
It reuses the synthetic request builder in `examples/scc_crack_velocity_history.py`;
the example probability and crack-advance limit are instructional values and are not
an asset risk estimate or an engineering acceptance criterion.

## Checks and lineage

The adapter verifies the source model ID and canonical request digest, recomputes the
complete SCC history calculation and compares its canonical digest with the supplied
result, then checks asset, location, physical scope, clock, material/environment
identity and exact time knots. A mismatched, incomplete or non-reproducible result is
withheld. The result digest, request digest, crack-advance limit evidence, caller
probability evidence, rights declaration and FTA event basis are retained in the
binding calculation.

The deterministic output reports whether the nominal knot history reaches the
caller limit by the end of the period. If reached, it reports the first adjacent time
interval whose left value is below the limit and whose right value reaches or exceeds
it. The model samples cumulative advance at the requested knots; the adapter does not
invent an exact crossing time. If the limit is already met at the first knot, the event
is rejected for this first-failure-in-period mapping because the condition predates
the interval.

## Limits

- The probability and its statistical basis are caller supplied and not verified by
  this deterministic bridge.
- The result is conditional on one caller-provided material, environment, loading
  state, crack-velocity curve and finite `K_I` history.
- The SCC source model uses its declared fixed-geometry assumptions. Crack-geometry
  feedback, initiation, other degradation mechanisms, acceptance, remaining life and
  SCC qualification are outside this adapter.
- The event binding does not evaluate an FTA, infer event dependence or common causes,
  or decide whether the caller probability is suitable for a safety decision.
- Open-distribution rights are caller declared; selecting that boundary requires an
  authorization digest and does not itself determine legal sufficiency.

No tests, numerical runs, packaging or HPC jobs were performed for this change.
