# Ordered Findley life blocks with caller-reviewed linear damage

`integration.findley_miner_ordered_block_history` attaches one computed calibrated Findley life assessment to each caller-supplied cycle block. The model checks each assessment's canonical input digest, result state, model identity, and common asset, location, time basis, and material-condition identity before calculating.

The caller must affirm that block order is reviewed, the linear damage rule applies, and sequence interaction is omitted. Each upstream `AssessmentResult` must report `cycles_to_failure` in `cycle` units. For block *i*, the increment is `cycle_count_i / cycles_to_failure_i`; the increments are accumulated in the exact supplied order. A requested damage threshold is reported at the first integer cycle in the supplied finite sequence that reaches it. The API does not extend the history beyond those blocks.

## Python API

```python
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

# Each life assessment must already be computed through the registry and
# must match the same asset, location, time basis, and material condition.
blocks = [
    {"block_id": "startup", "cycle_count": 250, "life_result": startup_life},
    {"block_id": "steady", "cycle_count": 1200, "life_result": steady_life},
]
request = {
    "blocks": blocks,
    "damage_threshold": 1.0,
    "ordered_blocks_reviewed": True,
    "shared_asset_location_material_condition_reviewed": True,
    "linear_damage_rule_reviewed": True,
    "no_sequence_interaction_assumed": True,
}
result = default_registry().run(
    "integration.findley_miner_ordered_block_history",
    request,
    RunContext(asset_id="pump-17", location_id="elbow-A", time_basis="cycle"),
)
```

`startup_life` and `steady_life` are `AssessmentResult` instances returned by the registered calibrated Findley-life model. Callers should retain those results and their calibration evidence rather than copying only scalar lives. A noncomputed or mismatched result stops processing and returns the accepted prefix with a status explaining the boundary.

## Interpretation and verification status

The accumulated damage and first threshold crossing are conditional on the supplied calibrated life values and the caller's linear, sequence-independent rule. They are not a probability, failure frequency, service-life forecast, acceptance decision, or independent material qualification. No test, example execution, numeric evaluation, or HPC validation was performed during implementation; those checks remain queued for the shared parallel verification campaign.
