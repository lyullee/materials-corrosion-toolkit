# Caller rate knots to a finite wall-thickness history

`corrosion.piecewise_linear_rate_thickness_history` maps a caller-owned, evidence-bearing corrosion-rate history to uniform area-average thickness loss. It complements constant-rate scenario APIs by accepting multiple strictly ordered time knots. The baseline time must be the first knot at elapsed time zero.

Between adjacent knots, the caller-reviewed corrosion rate is reconstructed as a straight line in time. For an interval from `t0` to `t1`, with rates `r0` and `r1`, the interval loss is the exact trapezoid integral:

```text
loss = (r0 + r1) * (t1 - t0) / 2
```

The API reports interval and cumulative loss, remaining thickness, required-thickness margin, both source-knot digests, and endpoint Evidence. If the required thickness is crossed within an interval, it bisects the integral of the same linear-rate reconstruction and returns a tight time bracket and a conditional midpoint estimate. If proposed cumulative loss exceeds the measured baseline, it rejects that interval and returns only the completed prefix.

## Python API

```python
from matintegrity.contracts import Evidence, RunContext
from matintegrity.corrosion_rate_history import (
    CorrosionRateHistoryKnot,
    CorrosionRateThicknessHistoryRequest,
)
from matintegrity.registry import default_registry

request = CorrosionRateThicknessHistoryRequest(
    history_id="loop-12-rate-history",
    asset_id="loop-12",
    location_id="elbow-4",
    material_id="carbon-steel",
    material_condition_id="reviewed-condition-1",
    physical_scope_id="uniform-area-average-wall",
    time_basis="s",
    knots=(
        CorrosionRateHistoryKnot(
            knot_index=0, time_s=0.0, corrosion_rate_m_s=1.0e-9,
            evidence=(Evidence(source_id="inspection-1", origin="measured",
                              citation="Caller-maintained inspection record", sha256="a" * 64),),
        ),
        CorrosionRateHistoryKnot(
            knot_index=1, time_s=1.0e7, corrosion_rate_m_s=1.4e-9,
            evidence=(Evidence(source_id="inspection-2", origin="measured",
                              citation="Caller-maintained inspection record", sha256="b" * 64),),
        ),
    ),
    baseline_thickness_m=0.012,
    baseline_evidence=Evidence(source_id="ultrasound-baseline", origin="measured",
                               citation="Caller thickness record", sha256="c" * 64),
    required_thickness_m=0.008,
    required_thickness_evidence=Evidence(source_id="design-limit", origin="user_declared",
                                         citation="Caller-approved thickness limit"),
    ordered_history_reviewed=True,
    rate_source_mapping_reviewed=True,
    piecewise_linear_rate_reconstruction_reviewed=True,
    uniform_area_average_loss_reviewed=True,
    material_condition_and_location_reviewed=True,
    finite_support_no_extrapolation_reviewed=True,
)
result = default_registry().run(
    "corrosion.piecewise_linear_rate_thickness_history",
    request,
    RunContext(asset_id="loop-12", location_id="elbow-4", time_basis="s"),
)
```

The values above illustrate contract wiring only; they are not an engineering recommendation. Each rate knot preserves its Evidence and canonical record digest. The API requires measured baseline Evidence, caller-declared or open-dataset Evidence for the thickness limit, matching `RunContext`, and explicit review gates.

## Interpretation boundary

This calculation does not infer rate between observations except for the explicitly reviewed linear reconstruction. It does not extrapolate outside the supplied knots, transfer rates across materials or locations, infer local pitting or corrosion morphology, assign weights or probability, decide acceptance, or qualify a life prediction. The crossing time is conditional on the supplied rate path and uniform-loss mapping. Tests, numerical evaluations, example execution, and package builds were not run during this implementation.
