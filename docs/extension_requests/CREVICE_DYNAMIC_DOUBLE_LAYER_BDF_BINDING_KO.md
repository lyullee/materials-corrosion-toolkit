# Downstream request: stage-resolved dynamic Cdl and Faradaic coupling

The current adapter recomputes a standalone lumped potential history and converts it into exact-knot BDF schedules. A simultaneous extension must place component moles, cell electrolyte potential, electrode potential, branch extents, double-layer charge and trial-stage aperture in one residual.

1. Re-evaluate signed branch kinetics and `Q(E,A)` at every BDF trial; include the active-area derivative in `dQ/dt`.
2. Solve ionic face-current continuity with no silent endpoint-only interpolation. Preserve external current boundaries as explicit inputs and ledgers.
3. Tie each branch to species/component/element/reservoir stoichiometry, electron number, current sign and licensed parameter evidence; reject charge, element or component imbalance.
4. If solid occupancy changes volume, include the same trial-stage geometry and volume-displacement flow in the transport residual.
5. Preserve solver-work budgets, provider support limits, atomic interval commits and exact input/result digests.

Do not advertise the operator-split adapter as a monolithic electrochemical solver or a qualified corrosion prediction.
