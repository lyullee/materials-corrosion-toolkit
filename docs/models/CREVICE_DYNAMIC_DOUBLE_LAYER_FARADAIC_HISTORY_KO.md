# Dynamic double-layer/Faradaic potential history

## Purpose

`integration.crevice_dynamic_double_layer_faradaic_history` advances an electrode potential history for independent lumped cells under a caller-supplied total-current schedule. It combines signed caller polarization tables with an Evidence-pinned differential-capacitance curve and integrates

`I_total(t) = sum_b I_F,b(E,t) + dQ(E,t)/dt`.

The stored charge is `Q = A(t) * integral[E_ref..E] C_d(V) dV`. The Cdl curve is piecewise linear and its charge integral is evaluated exactly by segment. Active area, imposed current and branch equilibrium potentials are linearly interpolated between caller knots; area variation contributes to `dQ/dt`. The potential ODE is integrated with SciPy BDF and returns exact requested knots.

## Required inputs

- Strictly increasing time knots starting at zero; stable cell ordering, initial/reference potential and active-area history.
- Per-cell total-current history with positive current defined into the electrode.
- One or more signed polarization tables with an overpotential support, one table per cell and equilibrium-potential history per knot. These may be derived from a caller-selected BV law or supplied empirical data; this module does not fit or assume a universal law.
- Differential capacitance versus potential, strictly positive on its declared support.
- SHA-256 digests and licensed Evidence matching the normalized records, plus explicit review of sign, interpolation, applicability, independent-cell scope and work limits.

All table lookups are bounded by the declared support. Extrapolation is rejected. Solver failures, nonfinite state, curve-support exits and work-budget exhaustion return an uncommitted result.

## Outputs

The result contains potential, stored charge, per-branch Faradaic current, capacitive current, imposed current and per-cell current-closure residual at every requested knot. It preserves input, area, current, capacitance and branch digests and reports BDF RHS work.

## Scope limits

Each cell is electrically independent. The API does not solve electrolyte ohmic potential, ionic Nernst–Planck transport, intercell current continuity, reaction stoichiometry, geometry evolution or area from material loss. Curves and active area remain caller-owned. A computed history is a user model, not a calibrated or procedure-qualified prediction. Spatial transport/Cdl integration must use a downstream adapter that preserves the simultaneous current balance.

## Python interface

Use `CreviceDynamicDoubleLayerFaradaicHistoryRequest`, `DynamicDoubleLayerPolarizationBranch`, and `solve_crevice_dynamic_double_layer_faradaic_history` from `matintegrity.crevice_dynamic_double_layer_faradaic_history`. The central `ModelRegistry` exposes the same model identifier. Schema and capability catalogs are generated from the registered contract.
