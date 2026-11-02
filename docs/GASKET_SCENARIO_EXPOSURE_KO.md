# Gasket scenario leakage exposure handoff

`integration.gasket_leakage_scenario_exposure` converts a digest-pinned, already-computed finite correlated gasket leakage-rate scenario set into an exposure amount over a caller-declared duration.

## Inputs and composition

The request takes the complete source `AssessmentResult` from `fabrication.gasket_correlated_scenario_envelope`, its canonical result digest, the matching snapshot time, an exposure duration, and explicit reviews of constant leakage state, time window, and computational use. The `RunContext` asset, location and time basis must exactly match the source result.

For each finite scenario it applies:

`exposure amount [mol] = snapshot leakage rate [mol/s] × declared duration [s]`

It preserves scenario IDs and source result/input/scenario digests and reports minimum/maximum witnesses. The output can be passed to caller-owned consequence or risk calculations as an amount basis.

## Limits

- The rate is held constant throughout the declared interval. Changes in contact pressure, differential pressure, area, calibration response, gasket relaxation, or leak path are not modeled.
- Minimum and maximum are over the finite supplied scenarios only. They are not probabilities, confidence intervals, or continuous uncertainty bounds.
- The API does not determine whether a leak is acceptable and does not replace transient flange-contact or leakage-history models when time-varying inputs exist.
- Scenario amounts are not FTA basic-event probabilities. A separate explicitly defined event mapping is required before reliability use.

This interface record does not imply testing, physical validation, or package builds.
