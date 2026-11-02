# Extension request: couple moving-volume continuity to hydraulic component BDF

## Existing contract

The current `integration.crevice_moving_volume_liquid_continuity` request consumes exact-knot per-cell aperture plus left/right boundary volumetric-flow histories. It calculates interval-mean face flow from cell-volume continuity and rejects a mismatched terminal boundary flow. `corrosion.crevice_moving_volume_hydraulic_history` now adds a caller-pressure-driven reduced series momentum ODE: cell-volume rates determine face-flow offsets and pressure forcing integrates the inlet-flow state. Both outputs are digest-bound to their source histories.

## Requested downstream extension

Extend the hydraulic/reactive crevice solver to accept either typed result only after recomputing it from its request and matching assessment, physical scope, ordered cell IDs, exact clock, geometry digest and pressure/boundary-flow digest. Preserve interval-mean face flows and the declared sign convention. If the downstream integrator needs stage flow, define and validate an explicit interval interpolation rule instead of silently treating interval means as instantaneous values. The reduced hydraulic result currently integrates only a common pressure-driven inlet-flow state; local chemistry and phase feedback remain outside it.

The coupled state should carry conserved aqueous component moles and solid phase inventories while cell liquid volume/aperture changes. At every solver stage it should enforce nonnegative liquid volume and minimum aperture, evaluate pressure/momentum from the same trial geometry and flow state, and include displaced/injected component amounts in left/right external-reservoir ledgers. Solid precipitation, wall exchange and electrochemical sources must close component, element, charge and phase inventories in the same interval.

## Acceptance evidence required

- Constant aperture and equal boundary flow reproduce the fixed-volume hydraulic path.
- Closed boundaries with nonzero net chamber shrinkage are rejected by total-volume closure.
- Prescribed volume decrease/increase with matched boundary displacement satisfies cellwise and system volume closure.
- Zero flow and zero volume change produce zero internal flow.
- Species/component transport with changing volume closes dissolved plus solid plus boundary inventories and does not create concentration by changing the concentration denominator alone.
- Independent numerical refinement and limiting-case comparison are completed before physical qualification.

This handoff does not prescribe a pressure-flow correlation, deposit morphology, kinetic parameter set, or qualification basis. Each must remain caller/provider sourced and independently reviewed.
