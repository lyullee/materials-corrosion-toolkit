# Extension request: gasket transient scenario exposure provider

## Existing bounded interface

`integration.gasket_leakage_scenario_rate_interval` consumes two digest-pinned correlated leakage scenario envelopes with the same scenario IDs and calibration realization and integrates each scenario's total leakage rate using an explicitly reviewed linear-in-time rate reconstruction. Its output is amount in mol. It does not infer event probability, intermediate pressure/contact state or seal acceptability.

## Follow-on work for another session

1. Add a provider adapter that samples flange contact, gasket relaxation and differential pressure at caller-defined common time knots, then computes an envelope at every knot. Preserve common scenario identifiers only when their stochastic/deterministic realization semantics are genuinely traceable across all times.
2. Add adaptive knot refinement driven by a caller-declared rate reconstruction error criterion. The current two-endpoint trapezoid adapter does not estimate interpolation error or certify unsampled extrema.
3. Consume a fully time-resolved leakage amount as a source term in an external consequence module, keeping material composition, phase state and discharge thermodynamics as separately sourced inputs.
4. If an FTA/reliability module consumes the result, define the event threshold, demand frequency, detection/isolation behavior and time basis explicitly. Never treat scenario amounts as probabilities or map them into a Bernoulli event without a separate justified model.
5. Compare with an independent time-resolved sealing/leakage benchmark after provider data rights and experimental validation records are approved.

No follow-on transient provider, consequence or FTA adapter is implemented by this request.
