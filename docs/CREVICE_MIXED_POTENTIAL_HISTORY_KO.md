# Crevice mixed-potential knot history

`electrochemistry.crevice_mixed_potential_history` combines two or more caller-calculated, digest-pinned Nernst half-cell histories with separately calibrated Butler–Volmer reaction branches. At each aligned caller time knot it solves the shared metal-to-solution potential for zero signed net current. This is an operator-level composition for other integrity and risk modules; it is not itself a corrosion acceptance decision.

## Required inputs and review

Every branch carries its upstream computed Nernst `AssessmentResult`, full result SHA-256, reaction identity, standard-potential reference identity, exposed area, exchange-current density, electron number, transfer coefficients, calibrated overpotential range, signed species stoichiometry, calibration record identity and matching `Evidence`. All histories must use the same asset, location, physical scope, clock, reference electrode, exact time knots, temperatures and source-history lineage. The lineage can be a raw inventory assessment or an aqueous mass-action/B-dot activity history. Inventory, knot-history and upstream activity-result digests keep their distinct names; the API does not relabel an activity history as a raw inventory. Duplicate reaction IDs are rejected.

The request further requires caller signoff for a quasi-steady local balance, negligible solution ohmic drop, shared electronic potential, complete reaction set and area partition, and computational use. These gates identify assumptions; they do not independently validate them.

## Calculation and outputs

For branch `j`, its exposed area scales its exchange current onto the request's reference-area basis. The solver intersects all calibrated potential intervals, evaluates signed Butler–Volmer currents, and uses deterministic bracketed bisection to find a zero-current root. Each knot returns the mixed potential, residual net current, branch equilibrium potential and overpotential, anodic/cathodic partial currents and signed species flux on the reference-area basis. The computation is bounded to exact input knots; it does not interpolate, integrate charge, infer activity or kinetic parameters, calculate metal loss, or assess dynamic stability.

If zero current is not bracketed, the shared support is empty, or a branch leaves its calibrated range, the request is returned as unsupported instead of extrapolating. Missing reviews return `needs_data`.

## Limits and intended extension

The model assumes the caller's reaction list and area partition are complete and that all branches share one electronically connected surface potential. Spatial solution resistance, distributed surface potential, double-layer transients, changing area, kinetic fitting, uncertainty propagation and independent experimental qualification are not included. A downstream module can consume the per-branch flux history and its digest, then combine its own inventory, transport or risk method without treating this result as a corrosion-rate measurement.

## Python API

Use the registry model ID `electrochemistry.crevice_mixed_potential_history`, or call `evaluate_crevice_mixed_potential_history(request)` with a validated `CreviceMixedPotentialHistory`. Input contracts `CreviceMixedPotentialReaction` and `CreviceMixedPotentialHistory` are exported in the public schema set. The result preserves upstream assessment and kinetics calibration digests by reaction.

## Validation state

The implementation's contracts, catalog/schema links and source-scope trace are part of the code deliverable. Numerical solver tests, independent data validation, electrochemical experiments and HPC execution are deferred to the later batch validation stage. The B-dot adapter output can now enter this mixed-potential contract, provided every branch shares the exact upstream activity-history result and matching knot history.

## Synthetic end-to-end wiring

`examples/crevice_electrochemical_composition.py` shows the digest-preserving sequence from two caller Nernst profiles through mixed potential, interval species transfer and caller-volume composition. Its constants are synthetic wiring values and the example has intentionally not been executed; it is not calibration or validation evidence.
