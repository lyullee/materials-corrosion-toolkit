# Caller-reviewed FAD time-history API

## Purpose

`structural.failure_assessment_history` evaluates a finite sequence of provider-supplied fracture-assessment coordinates against one caller-pinned FAD curve. It reports the normalized `Kr/Lr` values, vertical toughness-ratio margin, and a first outside-boundary knot interval bracket where one is present.

This API complements the static-point model `structural.failure_assessment_points`. The static model is unchanged. Neither API calculates stress intensity, reference stress, fracture resistance, normalizing strength, failure probability, remaining life, or code acceptance.

## Input contract

Build an `FADAssessmentHistoryRequest` from the `matintegrity.fad_history` module. Required identities are assessment, asset, location, physical scope, clock, material condition, geometry basis and load-history basis. `curve` is the existing `FailureAssessmentCurve`; `curve_sha256` must equal the canonical digest of that exact embedded curve contract. The existing curve contract requires licensed/entitled Evidence and a finite nonincreasing piecewise-linear boundary.

Each knot carries time, effective mode-I stress intensity, fracture resistance, reference stress, normalizing strength, and exactly one provider receipt for each quantity. A receipt records provider/result identity, the provider result SHA-256 and one or more Evidence records; every Evidence record must state a license or use entitlement. Each receipt also repeats asset, location, physical scope, clock, exact knot time, material condition, geometry basis and load-history identity. The request validator requires exact equality with its corresponding history knot and request scope. These are caller lineage statements: the history model does not fetch the records or verify their physical validity.

All six applicability review flags must be true before numeric evaluation. The finite knot cap and `maximum_curve_evaluations`/`maximum_output_knots` bound requested work and response rows. The `RunContext` asset, location and time basis must match the request asset, location and clock.

## Calculation and boundary handling

At each supplied time knot, the model computes:

- `Kr = effective_stress_intensity / fracture_resistance`
- `Lr = reference_stress / normalizing_strength`
- the allowable `Kr` by linear interpolation of the pinned curve in `Lr`
- vertical margin `allowable Kr − Kr`

Interpolation applies only to the caller's FAD boundary and only within its declared `Lr` support. If any history knot lies outside that support, the model returns `out_of_scope` without a partial knot history or extrapolation.

The first knot with a negative margin is reported. If it is after the first knot, the model reports the previous/current knot interval and margins. If the first knot is already outside the boundary, it reports `already_outside_at_horizon_start`; it does not call that a new first crossing during the period. When every knot is inside/on the boundary, the status says no outside knot was found in the supplied history. Equality is inside/on the declared boundary, matching the static FAD API.

No margin-versus-time interpolation is used to claim an exact crossing time. A transient excursion between supplied knots can be missed; choose a justified time grid or supply additional provider knots when the loading history requires them.

## Example outline

The complete synthetic-only example is [`examples/fad_assessment_history.py`](../../examples/fad_assessment_history.py). It is provided to illustrate the request/result shape and does not use measured or qualified data. The outline below shows the public API names; for a runnable input, use the linked example.

```python
from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.models.fad import FailureAssessmentCurve
from matintegrity.fad_history import (
    FADAssessmentHistoryKnot,
    FADAssessmentHistoryRequest,
    FADHistoryProviderReceipt,
    evaluate_failure_assessment_history,
)

# `curve` is a caller-reviewed FailureAssessmentCurve with licensed Evidence.
# Each provider result digest and value below must come from your own reviewed
# mechanics/material providers. The identifiers and numbers here are omitted.
request = FADAssessmentHistoryRequest(
    assessment_id="caller-assessment",
    asset_id="asset-id",
    location_id="location-id",
    physical_scope_id="scope-id",
    clock_id="operating-seconds-v1",
    material_condition_id="material-state-id",
    geometry_basis_id="geometry-basis-id",
    load_history_id="load-history-id",
    curve=curve,
    curve_sha256=canonical_digest(curve.model_dump(mode="json")),
    knots=(... exact ordered FADAssessmentHistoryKnot values ...),
    linear_elastic_k_solution_reviewed=True,
    reference_stress_solution_reviewed=True,
    toughness_and_strength_applicability_reviewed=True,
    load_history_and_combination_reviewed=True,
    geometry_and_material_scope_reviewed=True,
    curve_applicability_reviewed=True,
)
calculation = evaluate_failure_assessment_history(request)
```

The abbreviated outline is not itself a runnable dataset: a real request must supply each knot and all four digest/evidence receipts. Do not publish proprietary provider data or identifiers without redistribution permission.

## FTA boundary

This model does not produce an `IntegrityEventBasis` or `FaultTreeBasicEvent`. A downstream event adapter would need an explicit caller probability, `conditional_first_failure_in_period` semantics, conditioning and shared probability scope, plus digest verification of this exact history. Such a bridge must reject a history already outside at its first knot and must not derive probability or crossing time from this deterministic calculation.

## Reproducibility fields

The calculation includes the canonical `input_sha256`, pinned `curve_sha256`, physical scope identities, exact horizon, knot results and provider receipts. Save the validated JSON request together with the provider source records and curve rights basis to reproduce a screening result later.
