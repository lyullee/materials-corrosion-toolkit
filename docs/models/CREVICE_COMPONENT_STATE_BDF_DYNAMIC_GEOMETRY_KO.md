# Crevice component-state BDF: opt-in solid-driven aperture feedback

## Scope

`crevice_component_state_bdf.v4` adds the opt-in `instantaneous_solid_aperture_feedback` mode. The default `fixed_volume` path remains unchanged. Dynamic geometry is accepted only with `instantaneous_solid_equilibrium`, caller-reviewed cell geometry and phase mappings, and the explicit stage-feedback review flag. Faradaic spatial stage coupling and hydraulic advection are rejected in this mode because their present operators assume fixed geometry.

This feature closes an aqueous/solid equilibrium stage with a bounded damped fixed-point iteration. It is an operator-split stage calculation, not a monolithic Newton solve in which chemical activities, solid amounts, aperture, and all transported states are solved simultaneously.

## Caller inputs and evidence

For each cell, `dynamic_solid_geometry_by_cell` declares:

- cell length and transverse width in m;
- initial and minimum aperture in m;
- one ordered phase mapping for every phase candidate in the matching cell phase set;
- solid molar volume in m^3/mol and whether that phase occupies the modeled gap;
- a source identifier, canonical SHA-256 digest, and evidence binding the complete geometry and phase map.

The existing cell `solution_volume_L` must equal `length * width * initial_aperture * 1000`. The phase map order and IDs must exactly match the declared candidate phase set. These are caller-supplied geometric assumptions; the code does not infer molar volumes, phase density, deposition location, or packing fraction.

## Stage calculation

For each trial component inventory and each cell, the solver starts at the initial liquid volume and calls the existing aqueous-plus-solid partition calculation. It sums `solid_mol * molar_volume_m3_mol` only for phases marked `occupies_gap`. The solid volume is divided by the cell plan area to obtain aperture reduction, then converted back to target solution volume. A damped update uses `alpha` from `dynamic_geometry_relaxation_factor`; the fixed-point residual is `abs(V_target - V_trial) / V_initial`.

When this residual reaches `dynamic_geometry_relative_tolerance`, the partition is repeated at the target volume and the mapping is checked once more. That final residual must also meet tolerance. The final cell area is `width * aperture`; area at each interior face is linearly interpolated between cell-center values using the supplied center distance and half-cell length. This stage face area is used both in the Nernst–Planck current-density conversion and in the integrated species/component face transfer.

The result reports exact-knot cell volume, aperture, cross-sectional area, residual, iteration history, aggregate maximum residual, and geometry work used/budget. `maximum_normalized_component_closure_residual` includes the maximum geometry residual divided by its requested tolerance. Any below-minimum aperture, nonfinite geometry, failed final closure, or exhausted per-cell/aggregate work budget returns `needs_data` with `committed=false`.

## Limits

- Solid inventory comes from the existing instantaneous equilibrium partition; phase kinetics, nucleation, deposition morphology, porosity, particle packing, mechanical gap deformation, and unlisted phases are not modeled.
- A phase marked as not occupying the gap still participates in chemistry but contributes no aperture reduction.
- The geometry map is static over the requested horizon. Only mapped solid occupancy changes the calculated volume and NP conductance.
- This is an inside-stage fixed-point closure around the existing partition solver. It is not a fully coupled monolithic chemistry/geometry/mechanics solver and does not establish uniqueness or physical validity of the caller's mapping.
- Existing fixed-volume schemas and behavior remain the default. v4 is required only when selecting dynamic geometry.

## API fields

Request: `moving_geometry_mode`, `dynamic_solid_geometry_by_cell`, `moving_geometry_stage_feedback_reviewed`, `dynamic_geometry_relative_tolerance`, `dynamic_geometry_relaxation_factor`, `maximum_dynamic_geometry_iterations_per_cell_stage`, and `maximum_total_dynamic_geometry_iterations`.

Geometry models: `CellDynamicSolidGeometry` and `SolidPhaseGeometryMap`.

No tests, package build, or HPC calculations are included in this implementation task.
