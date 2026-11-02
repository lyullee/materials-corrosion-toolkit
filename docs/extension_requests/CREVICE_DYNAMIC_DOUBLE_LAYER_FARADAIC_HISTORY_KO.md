# Downstream request: spatially coupled dynamic double layer

The new lumped history API solves `I_total = I_F + dQ/dt` independently per cell. Extend `integration.crevice_component_state_bdf` only when a downstream solver can retain one simultaneous state for component moles, electrolyte potential, electrode potential and double-layer charge.

Required integration contract:

1. Bind the exact cell/time/area map, polarization branch identities and digests, Cdl curve digest, current sign convention, material/environment identity and Evidence lineage.
2. Solve electrolyte ohmic/ionic face-current continuity and per-cell Faradaic source terms in the same BDF residual as `dQ/dt`; do not endpoint-bind interval-mean current to a stage-resolved solution.
3. Include time-varying active area in `dQ/dt`; if area changes from solid occupancy, use the same trial-stage geometry and component inventory.
4. Preserve element, charge and external-reservoir closure, solver-work bounds, support rejection and all-or-nothing interval commits.
5. Reject mismatched cell order, clock, species/reaction stoichiometry, potential reference or evidence digest before integration.

The independent-cell result must not be represented as spatially coupled corrosion, a qualified BV law, or a validated material-life estimate.
