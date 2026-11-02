# Crevice cell transport to bulk composition summary

`integration.crevice_transport_volume_weighted_composition` summarizes the exact computed cell concentrations from a `CreviceGeometryTransportCampaign`. The request contains both the campaign input and a computed campaign result; the adapter checks the result digest, campaign identity, geometry identity, and source-input digest before reading the segment rows.

At each solver output knot it multiplies each cell concentration by its caller-defined cell volume, then reports the total inventory and volume-weighted bulk concentration. It retains the original cell concentration and inventory arrays. At a geometry remap, the pre-remap and post-remap states are represented as separate rows at the shared time so a volume change is not hidden behind one ambiguous value.

Before using a remapped concentration, the adapter checks the remap clock and its from/to geometry-state digests against that exact interval boundary.

```python
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

request = {
    "assessment_id": "crevice-run-2026-01",
    "campaign": campaign_request,
    "campaign_result": computed_campaign.values,
    "campaign_result_sha256": digest_of_canonical_result_values,
    "cell_volume_weighted_bulk_summary_reviewed": True,
    "local_cell_heterogeneity_must_be_preserved_reviewed": True,
    "no_automatic_equilibrium_or_kinetic_interpretation_reviewed": True,
}
summary = default_registry().run(
    "integration.crevice_transport_volume_weighted_composition",
    request,
    RunContext(asset_id="line-4", location_id="crevice-cell", time_basis="s"),
)
```

The digest must be computed from the same canonical JSON-compatible result value supplied in `campaign_result`. A generic `AssessmentResult` envelope is not substituted for that campaign payload; keep both the complete result and its source campaign request when handing it between modules.

This adapter does not solve speciation or equilibrium, infer reaction rates or phase transitions, or decide whether a bulk average is suitable for a chemistry model. Downstream users should use preserved local cell fields where spatial gradients affect reaction or transport. No test, numeric calculation, example execution, or scientific qualification was performed during implementation.
