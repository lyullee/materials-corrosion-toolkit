# Ordered elastic joint-load snapshots

`integration.elastic_joint_load_ordered_history` evaluates the existing two-spring elastic joint-load model independently at each strictly ordered caller snapshot. Every row carries an exact index, time and `ElasticJointLoad` input. The request also binds the series to one asset, location and time basis through `RunContext`.

The API reports each computed bolt/clamp-force result, finite-series extrema and the first supplied snapshot below a caller-defined minimum clamp force. It does not infer what happens between snapshots. If the bounded elastic model reports loss of closed-contact applicability at a knot, processing stops and returns the valid prefix.

```python
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

request = {
    "history_id": "joint-7-load-check",
    "asset_id": "exchanger-7",
    "location_id": "channel-cover",
    "time_basis": "s",
    "knots": ordered_load_snapshots,
    "minimum_clamp_force_N": 1.2e5,
    "ordered_time_basis_reviewed": True,
    "elastic_closed_contact_model_reviewed": True,
    "per_knot_preload_applicability_reviewed": True,
    "finite_snapshot_only_interpretation_reviewed": True,
}
result = default_registry().run(
    "integration.elastic_joint_load_ordered_history",
    request,
    RunContext(asset_id="exchanger-7", location_id="channel-cover", time_basis="s"),
)
```

This is a finite snapshot calculation for an elastic closed-contact load partition. It does not model gasket viscoelasticity, relaxation, contact opening between knots, leakage, seal acceptance, failure probability or material qualification. The caller threshold is not an acceptance criterion. No tests, numerical evaluations, example execution or package build were performed during implementation.
